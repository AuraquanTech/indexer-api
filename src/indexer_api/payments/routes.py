"""
Payment API Routes
Handles checkout, webhooks, product management, and order tracking
"""
from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime
import logging

from .models import (
    ProductCreate, Product, ProductResponse,
    OrderStatus, CheckoutSessionResponse, RevenueMetrics
)
from .stripe_service import get_stripe_service, StripeService
from .license_service import get_license_service, LicenseService
from .email_service import get_email_service, EmailService

logger = logging.getLogger(__name__)

payment_router = APIRouter(prefix="/payments", tags=["payments"])

# In-memory storage for demo (replace with Supabase in production)
_products: dict = {}
_orders: dict = {}
_customers: dict = {}


def get_services():
    """Dependency to get all payment services"""
    return {
        "stripe": get_stripe_service(),
        "license": get_license_service(),
        "email": get_email_service()
    }


# ============== Health & Status ==============

@payment_router.get("/status")
async def payment_status():
    """Check payment system status"""
    stripe_svc = get_stripe_service()
    email_svc = get_email_service()

    return {
        "status": "operational",
        "stripe_configured": stripe_svc.is_configured,
        "email_configured": email_svc.is_configured,
        "products_count": len(_products),
        "orders_count": len(_orders)
    }


# ============== Products ==============

@payment_router.post("/products", response_model=Product)
async def create_product(product: ProductCreate):
    """Create a new product for sale"""
    stripe_svc = get_stripe_service()

    product_id = uuid4()

    # Create in Stripe if configured
    stripe_product_id = None
    stripe_price_id = None

    if stripe_svc.is_configured:
        try:
            stripe_result = await stripe_svc.create_product(
                name=product.name,
                description=product.description,
                price_cents=product.price_cents,
                metadata={"product_id": str(product_id)}
            )
            stripe_product_id = stripe_result["product_id"]
            stripe_price_id = stripe_result["price_id"]
        except Exception as e:
            logger.error(f"Failed to create Stripe product: {e}")

    # Create product record
    new_product = Product(
        id=product_id,
        name=product.name,
        description=product.description,
        price_cents=product.price_cents,
        product_type=product.product_type,
        project_id=product.project_id,
        stripe_product_id=stripe_product_id,
        stripe_price_id=stripe_price_id or product.stripe_price_id,
        download_url=product.download_url,
        features=product.features,
        metadata=product.metadata,
        status="active" if stripe_price_id else "draft"
    )

    _products[str(product_id)] = new_product.model_dump()

    return new_product


@payment_router.get("/products", response_model=List[Product])
async def list_products(status: Optional[str] = None):
    """List all products"""
    products = list(_products.values())
    if status:
        products = [p for p in products if p.get("status") == status]
    return [Product(**p) for p in products]


@payment_router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: UUID):
    """Get a single product with checkout URL"""
    product_data = _products.get(str(product_id))
    if not product_data:
        raise HTTPException(status_code=404, detail="Product not found")

    product = Product(**product_data)
    checkout_url = None

    # Generate checkout URL if Stripe is configured
    stripe_svc = get_stripe_service()
    if stripe_svc.is_configured and product.stripe_price_id:
        try:
            result = await stripe_svc.create_checkout_session(
                price_id=product.stripe_price_id,
                success_url=f"http://localhost:3000/checkout/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"http://localhost:3000/checkout/cancel",
                metadata={"product_id": str(product_id)}
            )
            checkout_url = result["checkout_url"]
        except Exception as e:
            logger.error(f"Failed to create checkout URL: {e}")

    return ProductResponse(product=product, checkout_url=checkout_url)


# ============== Checkout ==============

@payment_router.post("/checkout/{product_id}", response_model=CheckoutSessionResponse)
async def create_checkout(
    product_id: UUID,
    customer_email: Optional[str] = None,
    success_url: Optional[str] = None,
    cancel_url: Optional[str] = None
):
    """Create a checkout session for a product"""
    stripe_svc = get_stripe_service()

    if not stripe_svc.is_configured:
        raise HTTPException(status_code=503, detail="Payment system not configured")

    product_data = _products.get(str(product_id))
    if not product_data:
        raise HTTPException(status_code=404, detail="Product not found")

    product = Product(**product_data)
    if not product.stripe_price_id:
        raise HTTPException(status_code=400, detail="Product not set up for payments")

    # Create order record
    order_id = uuid4()
    _orders[str(order_id)] = {
        "id": str(order_id),
        "product_id": str(product_id),
        "customer_email": customer_email,
        "status": "pending",
        "amount_cents": product.price_cents,
        "created_at": datetime.utcnow().isoformat()
    }

    try:
        result = await stripe_svc.create_checkout_session(
            price_id=product.stripe_price_id,
            success_url=success_url or f"http://localhost:3000/checkout/success?session_id={{CHECKOUT_SESSION_ID}}&order_id={order_id}",
            cancel_url=cancel_url or f"http://localhost:3000/checkout/cancel?order_id={order_id}",
            customer_email=customer_email,
            metadata={
                "product_id": str(product_id),
                "order_id": str(order_id),
                "product_name": product.name
            }
        )

        # Update order with session ID
        _orders[str(order_id)]["stripe_session_id"] = result["session_id"]

        return CheckoutSessionResponse(
            checkout_url=result["checkout_url"],
            session_id=result["session_id"]
        )

    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@payment_router.get("/checkout/session/{session_id}")
async def get_checkout_status(session_id: str):
    """Get the status of a checkout session"""
    stripe_svc = get_stripe_service()

    if not stripe_svc.is_configured:
        raise HTTPException(status_code=503, detail="Payment system not configured")

    try:
        return await stripe_svc.get_checkout_session(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== Webhooks ==============

@payment_router.post("/webhook/stripe")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle Stripe webhook events"""
    stripe_svc = get_stripe_service()
    license_svc = get_license_service()
    email_svc = get_email_service()

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe_svc.verify_webhook_signature(payload, sig_header)
    except Exception as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    data = event["data"]["object"]

    logger.info(f"Received Stripe webhook: {event_type}")

    if event_type == "checkout.session.completed":
        # Payment successful - fulfill the order
        session_id = data["id"]
        metadata = data.get("metadata", {})
        customer_email = data.get("customer_details", {}).get("email")

        order_id = metadata.get("order_id")
        product_id = metadata.get("product_id")
        product_name = metadata.get("product_name", "Product")

        if order_id and product_id:
            # Generate license key
            license_key = license_svc.generate_license_key(
                product_id=UUID(product_id),
                customer_id=uuid4(),  # Would be real customer ID
                order_id=UUID(order_id)
            )

            # Update order
            if order_id in _orders:
                _orders[order_id].update({
                    "status": "completed",
                    "license_key": license_key,
                    "completed_at": datetime.utcnow().isoformat(),
                    "customer_email": customer_email
                })

            # Update product sales
            if product_id in _products:
                _products[product_id]["total_sales"] = _products[product_id].get("total_sales", 0) + 1
                _products[product_id]["total_revenue_cents"] = _products[product_id].get("total_revenue_cents", 0) + data.get("amount_total", 0)

            # Send receipt email in background
            if customer_email and email_svc.is_configured:
                download_url = _products.get(product_id, {}).get("download_url", "https://example.com/download")
                background_tasks.add_task(
                    email_svc.send_purchase_receipt,
                    customer_email=customer_email,
                    customer_name=data.get("customer_details", {}).get("name", "Customer"),
                    product_name=product_name,
                    amount_cents=data.get("amount_total", 0),
                    license_key=license_key,
                    download_url=download_url,
                    order_id=order_id
                )

    elif event_type == "payment_intent.payment_failed":
        # Payment failed
        metadata = data.get("metadata", {})
        order_id = metadata.get("order_id")
        if order_id and order_id in _orders:
            _orders[order_id]["status"] = "failed"

    return {"received": True}


# ============== Orders ==============

@payment_router.get("/orders")
async def list_orders(status: Optional[str] = None, limit: int = 50):
    """List all orders"""
    orders = list(_orders.values())
    if status:
        orders = [o for o in orders if o.get("status") == status]
    return orders[:limit]


@payment_router.get("/orders/{order_id}")
async def get_order(order_id: UUID):
    """Get a single order"""
    order = _orders.get(str(order_id))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


# ============== Revenue Metrics ==============

@payment_router.get("/metrics", response_model=RevenueMetrics)
async def get_revenue_metrics(days: int = 30):
    """Get revenue metrics and analytics"""
    stripe_svc = get_stripe_service()

    # Get metrics from Stripe if configured
    stripe_metrics = await stripe_svc.get_revenue_metrics(days)

    # Calculate from local data as fallback/supplement
    completed_orders = [o for o in _orders.values() if o.get("status") == "completed"]
    total_revenue = sum(o.get("amount_cents", 0) for o in completed_orders)

    # Get top products
    product_sales = {}
    for order in completed_orders:
        pid = order.get("product_id")
        if pid:
            product_sales[pid] = product_sales.get(pid, 0) + 1

    top_products = []
    for pid, count in sorted(product_sales.items(), key=lambda x: -x[1])[:5]:
        product = _products.get(pid, {})
        top_products.append({
            "product_id": pid,
            "name": product.get("name", "Unknown"),
            "sales_count": count,
            "revenue_cents": product.get("total_revenue_cents", 0)
        })

    return RevenueMetrics(
        total_revenue_cents=stripe_metrics.get("total_revenue", total_revenue),
        mrr_cents=0,  # Would calculate from subscriptions
        total_customers=len(set(o.get("customer_email") for o in completed_orders if o.get("customer_email"))),
        total_orders=len(completed_orders),
        avg_order_value_cents=total_revenue // len(completed_orders) if completed_orders else 0,
        top_products=top_products,
        recent_orders=completed_orders[-10:],
        revenue_by_day=[]  # Would aggregate by day
    )


# ============== License Validation ==============

@payment_router.post("/licenses/validate")
async def validate_license(license_key: str, machine_id: Optional[str] = None):
    """Validate a license key"""
    license_svc = get_license_service()

    # Check format
    if not license_svc.validate_license_format(license_key):
        return {"valid": False, "error": "Invalid license format"}

    # Look up in orders
    for order in _orders.values():
        if order.get("license_key") == license_key:
            return {
                "valid": True,
                "product_id": order.get("product_id"),
                "order_id": order.get("id"),
                "activated_at": datetime.utcnow().isoformat()
            }

    return {"valid": False, "error": "License not found"}


# ============== Quick Payment Links ==============

@payment_router.post("/payment-link/{product_id}")
async def create_payment_link(product_id: UUID):
    """Create a reusable payment link for a product"""
    stripe_svc = get_stripe_service()

    if not stripe_svc.is_configured:
        raise HTTPException(status_code=503, detail="Payment system not configured")

    product_data = _products.get(str(product_id))
    if not product_data:
        raise HTTPException(status_code=404, detail="Product not found")

    product = Product(**product_data)
    if not product.stripe_price_id:
        raise HTTPException(status_code=400, detail="Product not set up for payments")

    try:
        link = await stripe_svc.create_payment_link(
            price_id=product.stripe_price_id,
            metadata={
                "product_id": str(product_id),
                "product_name": product.name,
                "success_url": "http://localhost:3000/checkout/success"
            }
        )
        return {"payment_link": link}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
