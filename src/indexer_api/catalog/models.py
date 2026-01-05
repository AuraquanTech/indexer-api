"""
Catalog database models.
"""
from datetime import datetime, timezone
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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from indexer_api.db.base import Base


def utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid4())


class CatalogProject(Base):
    """A project in the catalog."""

    __tablename__ = "catalog_projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False
    )

    # Core info
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    path: Mapped[str] = mapped_column(Text, nullable=False)

    # Classification
    type: Mapped[str] = mapped_column(String(20), default="other")
    lifecycle: Mapped[str] = mapped_column(String(20), default="active")

    # Tech stack (JSON arrays)
    languages: Mapped[list[str] | None] = mapped_column(JSON, default=list)
    frameworks: Mapped[list[str] | None] = mapped_column(JSON, default=list)
    tags: Mapped[list[str] | None] = mapped_column(JSON, default=list)

    # Repository info
    repository_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    default_branch: Mapped[str | None] = mapped_column(String(100), nullable=True)
    license_spdx: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # GitHub metrics
    github_stars: Mapped[int | None] = mapped_column(Integer, nullable=True)
    github_forks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    github_watchers: Mapped[int | None] = mapped_column(Integer, nullable=True)
    open_issues: Mapped[int | None] = mapped_column(Integer, nullable=True)
    open_prs: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Code metrics
    loc_total: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    file_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_complexity: Mapped[float | None] = mapped_column(Float, nullable=True)
    test_coverage: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Health score (0-100)
    health_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Quality Assessment
    production_readiness: Mapped[str] = mapped_column(String(20), default="unknown")
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_assessment: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    quality_indicators: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    last_quality_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Sync tracking
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_commit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_commit_sha: Mapped[str | None] = mapped_column(String(40), nullable=True)

    # Extra metadata
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_catalog_org_name"),
        UniqueConstraint("organization_id", "path", name="uq_catalog_org_path"),
        Index("ix_catalog_projects_lifecycle", "lifecycle"),
        Index("ix_catalog_projects_type", "type"),
        Index("ix_catalog_projects_org", "organization_id"),
    )


class CatalogJob(Base):
    """A catalog-related job (scan, refresh, etc.)."""

    __tablename__ = "catalog_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False
    )
    project_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("catalog_projects.id"), nullable=True
    )

    job_type: Mapped[str] = mapped_column(String(30), nullable=False)  # scan, refresh, health_check
    status: Mapped[str] = mapped_column(String(20), default="pending")
    priority: Mapped[int] = mapped_column(Integer, default=5)

    # Execution tracking
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    run_after: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Results
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    last_error: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        Index("ix_catalog_jobs_status", "status"),
        Index("ix_catalog_jobs_run_after", "run_after"),
    )


class CatalogJobRun(Base):
    """An execution run of a catalog job."""

    __tablename__ = "catalog_job_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("catalog_jobs.id", ondelete="CASCADE"), nullable=False
    )

    status: Mapped[str] = mapped_column(String(20), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_catalog_job_runs_job", "job_id"),
    )
