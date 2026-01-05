"""
Payment System Database Models
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class ProductType(str, Enum):
    SOFTWARE = "software"
    TEMPLATE = "template"
    API = "api"
    COURSE = "course"
    SERVICE = "service"


class ProductStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class OrderStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class LicenseType(str, Enum):
    PERPETUAL = "perpetual"
    SUBSCRIPTION = "subscription"
    TRIAL = "trial"


# Pydantic Models for API
class ProductCreate(BaseModel):
    name: str
    description: str
    price_cents: int  # Price in cents (e.g., 4999 = $49.99)
    product_type: ProductType = ProductType.SOFTWARE
    project_id: Optional[UUID] = None  # Link to indexed project
    stripe_price_id: Optional[str] = None
    download_url: Optional[str] = None
    features: List[str] = []
    metadata: dict = {}


class Product(ProductCreate):
    id: UUID = Field(default_factory=uuid4)
    status: ProductStatus = ProductStatus.DRAFT
    stripe_product_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    total_sales: int = 0
    total_revenue_cents: int = 0


class CustomerCreate(BaseModel):
    email: str
    name: Optional[str] = None
    stripe_customer_id: Optional[str] = None


class Customer(CustomerCreate):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    total_spent_cents: int = 0
    order_count: int = 0


class OrderCreate(BaseModel):
    customer_id: UUID
    product_id: UUID
    amount_cents: int
    stripe_payment_intent_id: Optional[str] = None
    stripe_checkout_session_id: Optional[str] = None


class Order(OrderCreate):
    id: UUID = Field(default_factory=uuid4)
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    license_key: Optional[str] = None
    download_url: Optional[str] = None
    metadata: dict = {}


class LicenseCreate(BaseModel):
    order_id: UUID
    product_id: UUID
    customer_id: UUID
    license_type: LicenseType = LicenseType.PERPETUAL


class License(LicenseCreate):
    id: UUID = Field(default_factory=uuid4)
    license_key: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    is_active: bool = True
    activations: int = 0
    max_activations: int = 3


# API Response Models
class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str


class ProductResponse(BaseModel):
    product: Product
    checkout_url: Optional[str] = None


class RevenueMetrics(BaseModel):
    total_revenue_cents: int
    mrr_cents: int  # Monthly Recurring Revenue
    total_customers: int
    total_orders: int
    avg_order_value_cents: int
    top_products: List[dict]
    recent_orders: List[dict]
    revenue_by_day: List[dict]
