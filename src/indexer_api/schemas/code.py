"""
Code Discovery schemas.
"""
from datetime import datetime
from typing import Any

from pydantic import Field

from indexer_api.schemas.base import BaseSchema


# ============================================================================
# Code Metadata Schemas
# ============================================================================


class CodeMetadata(BaseSchema):
    """Code file metadata stored in extra_metadata."""

    language: str
    lines_total: int = 0
    lines_code: int = 0
    lines_comment: int = 0
    lines_blank: int = 0
    complexity: float | None = None
    maintainability_index: float | None = None
    functions: int = 0
    classes: int = 0
    imports: list[str] = Field(default_factory=list)
    has_docstrings: bool = False
    has_type_hints: bool = False


class CodeFileResponse(BaseSchema):
    """Extended file response with code metadata."""

    id: str
    index_id: str
    path: str
    filename: str
    extension: str | None
    size_bytes: int
    modified_time: datetime | None
    indexed_at: datetime
    code: CodeMetadata | None = None


class CodeFileDetail(CodeFileResponse):
    """Detailed code file response."""

    md5_hash: str | None = None
    quality_score: float | None = None
    complexity_score: float | None = None


# ============================================================================
# Code Search Schemas
# ============================================================================


class CodeSearch(BaseSchema):
    """Search/filter parameters for code files."""

    language: str | None = None
    languages: list[str] | None = None
    min_lines: int | None = Field(None, ge=0)
    max_lines: int | None = None
    min_complexity: float | None = Field(None, ge=0)
    max_complexity: float | None = None
    min_functions: int | None = Field(None, ge=0)
    min_classes: int | None = Field(None, ge=0)
    has_type_hints: bool | None = None
    has_docstrings: bool | None = None
    import_contains: str | None = None
    path_prefix: str | None = None
    order_by: str = Field(
        default="path",
        pattern=r"^(path|filename|size_bytes|lines_total|complexity|functions|classes)$"
    )
    order_desc: bool = False


# ============================================================================
# Project Statistics Schemas
# ============================================================================


class LanguageStats(BaseSchema):
    """Statistics for a single language."""

    language: str
    file_count: int
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    total_size_bytes: int
    avg_complexity: float | None = None
    total_functions: int = 0
    total_classes: int = 0


class ProjectStats(BaseSchema):
    """Aggregate project statistics."""

    index_id: str
    total_code_files: int
    total_lines: int
    total_code_lines: int
    total_comment_lines: int
    total_blank_lines: int
    total_size_bytes: int
    languages: list[LanguageStats]
    language_breakdown: dict[str, int]
    avg_complexity: float | None = None
    avg_file_size: float
    largest_files: list[dict[str, Any]]
    most_complex_files: list[dict[str, Any]]


class DependencyInfo(BaseSchema):
    """Dependency information."""

    name: str
    import_count: int
    files_using: list[str]
    is_stdlib: bool = False


class ProjectDependencies(BaseSchema):
    """Project dependencies analysis."""

    index_id: str
    total_unique_imports: int
    stdlib_imports: list[DependencyInfo]
    third_party_imports: list[DependencyInfo]
    local_imports: list[DependencyInfo]


# ============================================================================
# MVP Readiness Schemas
# ============================================================================


class MVPCheckResult(BaseSchema):
    """Result of a single MVP check."""

    name: str
    passed: bool
    score: float
    max_score: float
    description: str
    details: str | None = None


class MVPReadiness(BaseSchema):
    """MVP readiness score and breakdown."""

    index_id: str
    score: float = Field(ge=0, le=100)
    grade: str  # A, B, C, D, F

    # Presence checks
    has_readme: bool = False
    has_license: bool = False
    has_gitignore: bool = False
    has_tests: bool = False
    has_ci: bool = False
    has_requirements: bool = False
    has_setup_config: bool = False

    # Quality metrics
    documentation_ratio: float = 0.0
    test_ratio: float = 0.0
    avg_complexity: float | None = None
    type_hint_ratio: float = 0.0

    # Breakdown by category
    checks: list[MVPCheckResult]

    # Actionable recommendations
    recommendations: list[str]


class CodeAnalysisJob(BaseSchema):
    """Response for starting a code analysis job."""

    job_id: str
    index_id: str
    status: str
    total_files_to_analyze: int
    message: str
