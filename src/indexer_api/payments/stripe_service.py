"""
Stripe Integration Service
Handles all Stripe API operations for checkout, products, and payments

Security Features (from Knowledge Base):
- HMAC-SHA256 signature validation for webhooks
- Timestamp replay attack prevention (5-minute tolerance)
- PII masking in logs
"""
import os
import time
import stripe
from typing import Optional, Dict, Any, Tuple
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

# Webhook timestamp tolerance (5 minutes to prevent replay attacks)
WEBHOOK_TOLERANCE_SECONDS = 300


class StripeService:
    """Service for Stripe payment operations"""

    def __init__(self):
        # Load from environment or credentials file
        self.secret_key = os.getenv("STRIPE_SECRET_KEY")
        self.publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

        # Try loading from .ai-credentials if not in env
        if not self.secret_key:
            self._load_from_credentials()

        if self.secret_key:
            stripe.api_key = self.secret_key
            logger.info("Stripe initialized successfully")
        else:
            logger.warning("Stripe not configured - payment features disabled")

    def _load_from_credentials(self):
        """Load credentials from .ai-credentials file"""
        creds_path = os.path.expanduser("~/.ai-credentials/api-keys.env")
        if os.path.exists(creds_path):
            try:
                with open(creds_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            if key == "STRIPE_SECRET_KEY":
                                self.secret_key = value
                            elif key == "STRIPE_PUBLISHABLE_KEY":
                                self.publishable_key = value
                            elif key == "STRIPE_WEBHOOK_SECRET":
                                self.webhook_secret = value
            except Exception as e:
                logger.error(f"Error loading credentials: {e}")

    @property
    def is_configured(self) -> bool:
        """Check if Stripe is properly configured"""
        return bool(self.secret_key and self.secret_key.startswith('sk_'))

    async def create_product(
        self,
        name: str,
        description: str,
        price_cents: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Create a Stripe product and price"""
        if not self.is_configured:
            raise ValueError("Stripe not configured")

        try:
            # Create product
            product = stripe.Product.create(
                name=name,
                description=description,
                metadata=metadata or {}
            )

            # Create price
            price = stripe.Price.create(
                product=product.id,
                unit_amount=price_cents,
                currency="usd"
            )

            return {
                "product_id": product.id,
                "price_id": price.id
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating product: {e}")
            raise

    async def create_checkout_session(
        self,
        price_id: str,
        success_url: str,
        cancel_url: str,
        customer_email: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Create a Stripe Checkout session"""
        if not self.is_configured:
            raise ValueError("Stripe not configured")

        try:
            session_params = {
                "mode": "payment",
                "line_items": [{"price": price_id, "quantity": 1}],
                "success_url": success_url,
                "cancel_url": cancel_url,
                "metadata": metadata or {},
                "payment_intent_data": {
                    "metadata": metadata or {}
                }
            }

            if customer_email:
                session_params["customer_email"] = customer_email

            session = stripe.checkout.Session.create(**session_params)

            return {
                "session_id": session.id,
                "checkout_url": session.url
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout: {e}")
            raise

    async def create_payment_link(
        self,
        price_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a reusable payment link"""
        if not self.is_configured:
            raise ValueError("Stripe not configured")

        try:
            link = stripe.PaymentLink.create(
                line_items=[{"price": price_id, "quantity": 1}],
                metadata=metadata or {},
                after_completion={
                    "type": "redirect",
                    "redirect": {
                        "url": metadata.get("success_url", "https://example.com/success")
                    }
                }
            )
            return link.url
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment link: {e}")
            raise

    async def get_checkout_session(self, session_id: str) -> Dict[str, Any]:
        """Retrieve checkout session details"""
        if not self.is_configured:
            raise ValueError("Stripe not configured")

        try:
            session = stripe.checkout.Session.retrieve(
                session_id,
                expand=["customer", "payment_intent"]
            )
            return {
                "id": session.id,
                "status": session.status,
                "payment_status": session.payment_status,
                "customer_email": session.customer_details.email if session.customer_details else None,
                "amount_total": session.amount_total,
                "metadata": session.metadata
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving session: {e}")
            raise

    def verify_webhook_signature(
        self,
        payload: bytes,
        sig_header: str,
        tolerance: int = WEBHOOK_TOLERANCE_SECONDS
    ) -> Tuple[Dict[str, Any], bool]:
        """
        Verify and parse webhook payload with replay attack prevention.

        Security features:
        - HMAC-SHA256 signature validation (Stripe built-in)
        - Timestamp tolerance check to prevent replay attacks

        Args:
            payload: Raw webhook body bytes
            sig_header: Stripe-Signature header value
            tolerance: Max age of webhook in seconds (default 5 minutes)

        Returns:
            Tuple of (event dict, is_replay_safe bool)

        Raises:
            ValueError: If webhook secret not configured
            SignatureVerificationError: If signature invalid
        """
        if not self.webhook_secret:
            raise ValueError("Webhook secret not configured")

        try:
            # Stripe's construct_event already validates signature with HMAC-SHA256
            # and checks timestamp within tolerance
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret, tolerance=tolerance
            )

            # Additional timestamp validation for logging/monitoring
            timestamp = self._extract_webhook_timestamp(sig_header)
            is_recent = self._validate_timestamp_freshness(timestamp, tolerance)

            if not is_recent:
                logger.warning(
                    "webhook_timestamp_warning",
                    event_id=event.get("id"),
                    timestamp=timestamp,
                    tolerance=tolerance
                )

            return event, is_recent

        except stripe.error.SignatureVerificationError as e:
            logger.error(
                "webhook_signature_failed",
                error=str(e),
                # Don't log full sig_header to avoid leaking secrets
                sig_prefix=sig_header[:20] if sig_header else None
            )
            raise

    def _extract_webhook_timestamp(self, sig_header: str) -> Optional[int]:
        """Extract timestamp from Stripe signature header."""
        try:
            parts = sig_header.split(",")
            for part in parts:
                if part.startswith("t="):
                    return int(part[2:])
        except (ValueError, AttributeError):
            pass
        return None

    def _validate_timestamp_freshness(
        self,
        timestamp: Optional[int],
        tolerance: int
    ) -> bool:
        """Check if webhook timestamp is within acceptable range."""
        if timestamp is None:
            return False
        current_time = int(time.time())
        age = current_time - timestamp
        return 0 <= age <= tolerance

    async def get_revenue_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get revenue metrics from Stripe"""
        if not self.is_configured:
            return {
                "total_revenue": 0,
                "payment_count": 0,
                "avg_payment": 0,
                "configured": False
            }

        try:
            import time
            from datetime import datetime, timedelta

            start_date = datetime.utcnow() - timedelta(days=days)
            start_timestamp = int(start_date.timestamp())

            # Get successful payments
            payments = stripe.PaymentIntent.list(
                created={"gte": start_timestamp},
                limit=100
            )

            successful = [p for p in payments.data if p.status == "succeeded"]
            total_revenue = sum(p.amount for p in successful)

            return {
                "total_revenue": total_revenue,
                "payment_count": len(successful),
                "avg_payment": total_revenue // len(successful) if successful else 0,
                "configured": True
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error getting metrics: {e}")
            return {
                "total_revenue": 0,
                "payment_count": 0,
                "avg_payment": 0,
                "error": str(e)
            }


# Singleton instance
_stripe_service: Optional[StripeService] = None


def get_stripe_service() -> StripeService:
    """Get or create Stripe service singleton"""
    global _stripe_service
    if _stripe_service is None:
        _stripe_service = StripeService()
    return _stripe_service
