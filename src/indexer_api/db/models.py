"""
SQLAlchemy database models.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from indexer_api.db.base import Base


def utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid4())


# ============================================================================
# Enums
# ============================================================================


class UserRole(str, Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class SubscriptionTier(str, Enum):
    """Subscription tiers."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class JobStatus(str, Enum):
    """Index job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Index job types."""
    FULL_SCAN = "full_scan"
    INCREMENTAL = "incremental"
    QUICK_SCAN = "quick_scan"
    DAM_ANALYSIS = "dam_analysis"
    CODE_ANALYSIS = "code_analysis"


class AssetType(str, Enum):
    """Asset types for DAM categorization."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    CODE = "code"
    OTHER = "other"


# ============================================================================
# User & Organization Models
# ============================================================================


class Organization(Base):
    """Organization/tenant for multi-tenancy."""

    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        String(20), default=SubscriptionTier.FREE
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Limits based on tier
    max_indexes: Mapped[int] = mapped_column(Integer, default=3)
    max_files_per_index: Mapped[int] = mapped_column(Integer, default=10000)
    max_storage_mb: Mapped[int] = mapped_column(Integer, default=1000)

    # Usage tracking
    current_storage_mb: Mapped[float] = mapped_column(Float, default=0.0)
    api_calls_this_month: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="organization")
    indexes: Mapped[list["FileIndex"]] = relationship("FileIndex", back_populates="organization")
    api_keys: Mapped[list["APIKey"]] = relationship("APIKey", back_populates="organization")


class User(Base):
    """User model with authentication."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(String(20), default=UserRole.USER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False
    )

    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    # Relationships
    organization: Mapped[Organization] = relationship("Organization", back_populates="users")
    jobs: Mapped[list["IndexJob"]] = relationship("IndexJob", back_populates="created_by_user")


class APIKey(Base):
    """API keys for programmatic access."""

    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    key_prefix: Mapped[str] = mapped_column(String(10), nullable=False)  # For display: "idx_abc..."

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False
    )
    created_by_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )

    scopes: Mapped[list[str]] = mapped_column(JSON, default=list)  # ["read", "write", "admin"]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationships
    organization: Mapped[Organization] = relationship("Organization", back_populates="api_keys")

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_api_key_org_name"),
    )


# ============================================================================
# Index & File Models
# ============================================================================


class FileIndex(Base):
    """A file index belonging to an organization."""

    __tablename__ = "file_indexes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False
    )

    # Index configuration
    root_path: Mapped[str] = mapped_column(Text, nullable=False)
    include_patterns: Mapped[list[str]] = mapped_column(JSON, default=list)
    exclude_patterns: Mapped[list[str]] = mapped_column(JSON, default=list)
    max_depth: Mapped[int | None] = mapped_column(Integer, nullable=True)
    compute_hashes: Mapped[bool] = mapped_column(Boolean, default=True)

    # Statistics
    total_files: Mapped[int] = mapped_column(Integer, default=0)
    total_directories: Mapped[int] = mapped_column(Integer, default=0)
    total_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    last_indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    # Relationships
    organization: Mapped[Organization] = relationship("Organization", back_populates="indexes")
    files: Mapped[list["IndexedFile"]] = relationship(
        "IndexedFile", back_populates="index", cascade="all, delete-orphan"
    )
    jobs: Mapped[list["IndexJob"]] = relationship(
        "IndexJob", back_populates="index", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_index_org_name"),
        Index("ix_file_indexes_org_active", "organization_id", "is_active"),
    )


class IndexedFile(Base):
    """A file entry within an index."""

    __tablename__ = "indexed_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    index_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("file_indexes.id", ondelete="CASCADE"), nullable=False
    )

    # File information
    path: Mapped[str] = mapped_column(Text, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    extension: Mapped[str] = mapped_column(String(50), nullable=True, index=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)

    # Timestamps
    created_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    modified_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accessed_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Hashes
    md5_hash: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    sha256_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Metadata
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_directory: Mapped[bool] = mapped_column(Boolean, default=False)
    depth: Mapped[int] = mapped_column(Integer, default=0)

    # Quality scores (from ultimate_indexer)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    complexity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    importance_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Extra metadata
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    indexed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationships
    index: Mapped[FileIndex] = relationship("FileIndex", back_populates="files")

    __table_args__ = (
        Index("ix_indexed_files_index_path", "index_id", "path"),
        Index("ix_indexed_files_index_ext", "index_id", "extension"),
        Index("ix_indexed_files_size", "size_bytes"),
    )


# ============================================================================
# Job & Task Models
# ============================================================================


class IndexJob(Base):
    """An indexing job/task."""

    __tablename__ = "index_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    index_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("file_indexes.id", ondelete="CASCADE"), nullable=False
    )
    created_by_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )

    job_type: Mapped[JobType] = mapped_column(String(20), default=JobType.FULL_SCAN)
    status: Mapped[JobStatus] = mapped_column(String(20), default=JobStatus.PENDING, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=5)  # 1=highest, 10=lowest

    # Progress tracking
    total_files: Mapped[int] = mapped_column(Integer, default=0)
    processed_files: Mapped[int] = mapped_column(Integer, default=0)
    failed_files: Mapped[int] = mapped_column(Integer, default=0)
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0)

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Celery task ID
    celery_task_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationships
    index: Mapped[FileIndex] = relationship("FileIndex", back_populates="jobs")
    created_by_user: Mapped[User] = relationship("User", back_populates="jobs")

    __table_args__ = (
        Index("ix_index_jobs_status_created", "status", "created_at"),
    )


# ============================================================================
# Usage & Billing Models
# ============================================================================


class UsageRecord(Base):
    """API usage tracking for billing."""

    __tablename__ = "usage_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False
    )

    # What was used
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)  # api_call, storage, compute
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Quantities
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit: Mapped[str] = mapped_column(String(20), default="count")  # count, bytes, seconds

    # Billing period
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Metadata
    extra_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index("ix_usage_org_period", "organization_id", "period_start", "period_end"),
    )
