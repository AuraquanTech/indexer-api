"""
Authentication and user schemas.
"""
from datetime import datetime

from pydantic import EmailStr, Field, field_validator

from indexer_api.db.models import SubscriptionTier, UserRole
from indexer_api.schemas.base import BaseSchema, TimestampMixin


# ============================================================================
# Token Schemas
# ============================================================================


class Token(BaseSchema):
    """JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token expiry in seconds")


class TokenPayload(BaseSchema):
    """JWT token payload."""

    sub: str
    exp: datetime
    iat: datetime
    type: str = "access"


class RefreshTokenRequest(BaseSchema):
    """Request to refresh tokens."""

    refresh_token: str


# ============================================================================
# User Schemas
# ============================================================================


class UserCreate(BaseSchema):
    """Schema for creating a new user."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    full_name: str | None = Field(None, max_length=255)
    organization_name: str = Field(max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseSchema):
    """Schema for user login."""

    email: EmailStr
    password: str


class UserUpdate(BaseSchema):
    """Schema for updating a user."""

    full_name: str | None = Field(None, max_length=255)
    email: EmailStr | None = None


class UserResponse(BaseSchema, TimestampMixin):
    """User response schema."""

    id: str
    email: str
    full_name: str | None
    role: UserRole
    is_active: bool
    is_verified: bool
    organization_id: str
    last_login: datetime | None


class UserWithOrganization(UserResponse):
    """User response with organization details."""

    organization: "OrganizationResponse"


# ============================================================================
# Organization Schemas
# ============================================================================


class OrganizationCreate(BaseSchema):
    """Schema for creating an organization."""

    name: str = Field(max_length=255)
    slug: str | None = Field(None, max_length=100, pattern=r"^[a-z0-9-]+$")


class OrganizationUpdate(BaseSchema):
    """Schema for updating an organization."""

    name: str | None = Field(None, max_length=255)


class OrganizationResponse(BaseSchema, TimestampMixin):
    """Organization response schema."""

    id: str
    name: str
    slug: str
    subscription_tier: SubscriptionTier
    max_indexes: int
    max_files_per_index: int
    max_storage_mb: int
    current_storage_mb: float
    api_calls_this_month: int


class OrganizationUsage(BaseSchema):
    """Organization usage summary."""

    organization_id: str
    total_indexes: int
    total_files: int
    total_storage_mb: float
    api_calls_this_month: int
    limits: dict[str, int]


# ============================================================================
# API Key Schemas
# ============================================================================


class APIKeyCreate(BaseSchema):
    """Schema for creating an API key."""

    name: str = Field(max_length=100)
    scopes: list[str] = Field(default_factory=lambda: ["read"])
    expires_in_days: int | None = Field(None, ge=1, le=365)


class APIKeyResponse(BaseSchema):
    """API key response (without the actual key)."""

    id: str
    name: str
    key_prefix: str
    scopes: list[str]
    is_active: bool
    expires_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime


class APIKeyCreated(APIKeyResponse):
    """API key response after creation (includes the actual key)."""

    key: str = Field(description="The full API key - only shown once!")


# Update forward refs
UserWithOrganization.model_rebuild()
