"""
File index and search schemas.
"""
from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from indexer_api.db.models import JobStatus, JobType
from indexer_api.schemas.base import BaseSchema, TimestampMixin


# ============================================================================
# File Index Schemas
# ============================================================================


class FileIndexCreate(BaseSchema):
    """Schema for creating a new file index."""

    name: str = Field(max_length=255)
    description: str | None = Field(None, max_length=1000)
    root_path: str = Field(max_length=1000)
    include_patterns: list[str] = Field(default_factory=lambda: ["*"])
    exclude_patterns: list[str] = Field(
        default_factory=lambda: ["*.git*", "*node_modules*", "*__pycache__*", "*.env*"]
    )
    max_depth: int | None = Field(None, ge=1, le=100)
    compute_hashes: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class FileIndexUpdate(BaseSchema):
    """Schema for updating a file index."""

    name: str | None = Field(None, max_length=255)
    description: str | None = Field(None, max_length=1000)
    include_patterns: list[str] | None = None
    exclude_patterns: list[str] | None = None
    max_depth: int | None = None
    compute_hashes: bool | None = None
    is_active: bool | None = None


class FileIndexResponse(BaseSchema, TimestampMixin):
    """File index response schema."""

    id: str
    name: str
    description: str | None
    organization_id: str
    root_path: str
    include_patterns: list[str]
    exclude_patterns: list[str]
    max_depth: int | None
    compute_hashes: bool
    total_files: int
    total_directories: int
    total_size_bytes: int
    last_indexed_at: datetime | None
    is_active: bool


class FileIndexStats(BaseSchema):
    """Statistics for a file index."""

    index_id: str
    total_files: int
    total_directories: int
    total_size_bytes: int
    total_size_human: str
    extensions_breakdown: dict[str, int]
    size_distribution: dict[str, int]
    last_indexed_at: datetime | None
    avg_file_size: float
    largest_file: dict[str, Any] | None


# ============================================================================
# Indexed File Schemas
# ============================================================================


class IndexedFileResponse(BaseSchema):
    """Response for a single indexed file."""

    id: str
    index_id: str
    path: str
    filename: str
    extension: str | None
    size_bytes: int
    created_time: datetime | None
    modified_time: datetime | None
    md5_hash: str | None
    sha256_hash: str | None
    mime_type: str | None
    is_directory: bool
    depth: int
    quality_score: float | None
    complexity_score: float | None
    importance_score: float | None
    extra_metadata: dict[str, Any] | None
    indexed_at: datetime


class IndexedFileSearch(BaseSchema):
    """Search/filter parameters for indexed files."""

    query: str | None = Field(None, max_length=500, description="Search in filename and path")
    extension: str | None = Field(None, max_length=50)
    extensions: list[str] | None = None
    min_size: int | None = Field(None, ge=0)
    max_size: int | None = None
    min_quality_score: float | None = Field(None, ge=0, le=1)
    modified_after: datetime | None = None
    modified_before: datetime | None = None
    is_directory: bool | None = None
    path_prefix: str | None = Field(None, max_length=1000)
    order_by: str = Field(default="path", pattern=r"^(path|filename|size_bytes|modified_time|quality_score)$")
    order_desc: bool = False


class DuplicateFilesResponse(BaseSchema):
    """Response for duplicate file detection."""

    hash: str
    file_count: int
    total_size_bytes: int
    files: list[IndexedFileResponse]


# ============================================================================
# Index Job Schemas
# ============================================================================


class IndexJobCreate(BaseSchema):
    """Schema for creating an index job."""

    job_type: JobType = JobType.FULL_SCAN
    priority: int = Field(default=5, ge=1, le=10)


class IndexJobResponse(BaseSchema):
    """Index job response schema."""

    id: str
    index_id: str
    created_by_id: str
    job_type: JobType
    status: JobStatus
    priority: int
    total_files: int
    processed_files: int
    failed_files: int
    progress_percent: float
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    celery_task_id: str | None
    created_at: datetime


class IndexJobProgress(BaseSchema):
    """Real-time job progress update."""

    job_id: str
    status: JobStatus
    progress_percent: float
    processed_files: int
    total_files: int
    failed_files: int
    current_file: str | None = None
    eta_seconds: int | None = None


# ============================================================================
# Search Result Schemas
# ============================================================================


class SearchResult(BaseSchema):
    """A single search result."""

    file: IndexedFileResponse
    score: float = Field(ge=0, le=1)
    highlights: list[str] = Field(default_factory=list)


class SearchResponse(BaseSchema):
    """Search response with results."""

    query: str
    total_results: int
    results: list[SearchResult]
    took_ms: float
    filters_applied: dict[str, Any]
