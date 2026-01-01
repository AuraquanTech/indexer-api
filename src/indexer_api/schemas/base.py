"""
Base Pydantic schemas and utilities.
"""
from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        json_encoders={datetime: lambda v: v.isoformat()},
    )


class TimestampMixin(BaseModel):
    """Mixin for created_at/updated_at fields."""

    created_at: datetime
    updated_at: datetime | None = None


class PaginatedResponse(BaseSchema, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total_pages: int

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """Create a paginated response."""
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class ErrorResponse(BaseSchema):
    """Standard error response."""

    error: str
    message: str
    details: dict[str, Any] | None = None
    request_id: str | None = None


class SuccessResponse(BaseSchema):
    """Standard success response."""

    success: bool = True
    message: str


class HealthResponse(BaseSchema):
    """Health check response."""

    status: str = "healthy"
    version: str
    database: str = "connected"
    redis: str = "connected"
