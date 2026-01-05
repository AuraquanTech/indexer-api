"""
Catalog schemas for project management.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProjectLifecycle(str, Enum):
    """Project lifecycle stages."""
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ProductionReadiness(str, Enum):
    """Production readiness levels."""
    UNKNOWN = "unknown"  # Not assessed
    PROTOTYPE = "prototype"  # Experimental/proof of concept
    ALPHA = "alpha"  # Early development, unstable
    BETA = "beta"  # Feature complete, needs testing
    PRODUCTION = "production"  # Production ready
    MATURE = "mature"  # Battle-tested, stable
    LEGACY = "legacy"  # Old but still works
    DEPRECATED = "deprecated"  # Should not be used


class ProjectType(str, Enum):
    """Project type classification."""
    API = "api"
    LIBRARY = "library"
    CLI = "cli"
    WEB = "web"  # Web project (generic)
    WEB_APP = "web_app"
    MOBILE_APP = "mobile_app"
    SERVICE = "service"
    MONOREPO = "monorepo"
    APPLICATION = "application"  # General application
    TOOL = "tool"  # Development tool
    FRAMEWORK = "framework"  # Framework/boilerplate
    PLUGIN = "plugin"  # Plugin/extension
    EXTENSION = "extension"  # Browser/IDE extension
    SCRIPT = "script"  # Script collection
    CONFIG = "config"  # Configuration/dotfiles
    DOCS = "docs"  # Documentation
    BOT = "bot"  # Bot/automation
    GAME = "game"  # Game
    DATA = "data"  # Data/ML project
    TEMPLATE = "template"  # Template/starter
    OTHER = "other"


# ============================================================================
# Project Schemas
# ============================================================================


class CatalogProjectBase(BaseModel):
    """Base project schema."""
    name: str = Field(..., min_length=1, max_length=100)
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    path: str = Field(..., description="Absolute filesystem path")
    repository_url: Optional[str] = None
    type: ProjectType = ProjectType.OTHER
    lifecycle: ProjectLifecycle = ProjectLifecycle.ACTIVE
    languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    license_spdx: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class CatalogProjectCreate(CatalogProjectBase):
    """Schema for creating a project."""
    pass


class CatalogProjectUpdate(BaseModel):
    """Schema for updating a project."""
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[ProjectType] = None
    lifecycle: Optional[ProjectLifecycle] = None
    languages: Optional[List[str]] = None
    frameworks: Optional[List[str]] = None
    license_spdx: Optional[str] = None
    tags: Optional[List[str]] = None


class QualityIndicators(BaseModel):
    """Quality indicator flags."""
    has_readme: bool = False
    has_license: bool = False
    has_tests: bool = False
    has_ci_cd: bool = False
    has_documentation: bool = False
    has_changelog: bool = False
    has_contributing: bool = False
    has_security_policy: bool = False
    has_package_json: bool = False
    has_docker: bool = False
    has_linting: bool = False
    has_type_hints: bool = False


class QualityAssessment(BaseModel):
    """Detailed quality assessment."""
    code_quality_score: int = Field(0, ge=0, le=100)
    documentation_score: int = Field(0, ge=0, le=100)
    test_score: int = Field(0, ge=0, le=100)
    security_score: int = Field(0, ge=0, le=100)
    maintainability_score: int = Field(0, ge=0, le=100)
    key_features: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    production_blockers: List[str] = Field(default_factory=list)
    recommended_improvements: List[str] = Field(default_factory=list)
    technology_stack: List[str] = Field(default_factory=list)
    use_cases: List[str] = Field(default_factory=list)


class CatalogProjectOut(BaseModel):
    """Project output schema - accepts any type value from DB."""
    id: str
    organization_id: str
    name: str
    title: Optional[str] = None
    description: Optional[str] = None
    path: str
    repository_url: Optional[str] = None
    type: str = "other"  # Accept any string, not just enum values
    lifecycle: str = "active"  # Accept any string
    languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    license_spdx: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    health_score: Optional[float] = None
    loc_total: Optional[int] = None
    file_count: Optional[int] = None
    last_synced_at: Optional[datetime] = None
    github_stars: Optional[int] = None
    github_forks: Optional[int] = None
    open_issues: Optional[int] = None
    # Quality fields
    production_readiness: str = "unknown"
    quality_score: Optional[float] = None
    quality_assessment: Optional[Dict[str, Any]] = None
    quality_indicators: Optional[Dict[str, Any]] = None
    last_quality_check_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectSearchResult(BaseModel):
    """Search result item."""
    id: str
    name: str
    title: Optional[str] = None
    description: Optional[str] = None
    path: str
    type: str
    lifecycle: str
    languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    health_score: Optional[float] = None
    production_readiness: str = "unknown"
    quality_score: Optional[float] = None
    relevance_score: float = 1.0

    class Config:
        from_attributes = True


class ProjectListOut(BaseModel):
    """Paginated project list."""
    items: List[CatalogProjectOut]
    total: int
    page: int
    per_page: int


class ProjectSearchOut(BaseModel):
    """Search results."""
    results: List[ProjectSearchResult]
    total: int
    query: str


# ============================================================================
# Job & Run Schemas
# ============================================================================


class JobRunOut(BaseModel):
    """Job execution run output."""
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class JobStatusOut(BaseModel):
    """Job status output."""
    job_id: str
    job_type: str
    status: str
    priority: int
    attempts: int = 0
    max_attempts: int = 3
    created_at: datetime
    updated_at: datetime
    run_after: Optional[datetime] = None
    last_error: Optional[Dict[str, Any]] = None
    runs: List[JobRunOut] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ============================================================================
# Health Report Schemas
# ============================================================================


class HealthReportOut(BaseModel):
    """Portfolio health report."""
    total_projects: int
    by_lifecycle: Dict[str, int]
    by_language: Dict[str, int]
    by_type: Dict[str, int] = Field(default_factory=dict)
    avg_health_score: Optional[float] = None
    stale_count: int  # no sync in 30+ days
    recently_updated: int  # updated in last 7 days
    total_loc: Optional[int] = None
    generated_at: datetime


# ============================================================================
# Scan Schemas
# ============================================================================


class ScanRequest(BaseModel):
    """Request to scan filesystem for projects."""
    paths: List[str] = Field(default_factory=list, description="Paths to scan")
    max_depth: int = Field(default=5, ge=1, le=20)
    recursive: bool = True
    include_hidden: bool = False


class ScanResponse(BaseModel):
    """Scan job response."""
    job_id: str
    status: str
    message: str


# ============================================================================
# Quality Report Schemas
# ============================================================================


class QualityReportProject(BaseModel):
    """Project summary for quality report."""
    id: str
    name: str
    path: str
    type: str
    production_readiness: str
    quality_score: Optional[float] = None
    languages: List[str] = Field(default_factory=list)
    key_issues: List[str] = Field(default_factory=list)


class QualityReportOut(BaseModel):
    """Comprehensive quality report for all projects."""
    total_projects: int
    assessed_projects: int
    by_production_readiness: Dict[str, int]
    by_quality_tier: Dict[str, int]  # excellent, good, fair, poor, unknown
    avg_quality_score: Optional[float] = None
    production_ready_count: int
    needs_attention: List[QualityReportProject]  # Low quality or blockers
    top_quality: List[QualityReportProject]  # Best quality projects
    common_issues: Dict[str, int]  # Issue -> count
    technology_distribution: Dict[str, int]
    generated_at: datetime


class QualityAssessmentRequest(BaseModel):
    """Request to run quality assessment."""
    project_ids: Optional[List[str]] = None  # Specific projects, or all if None
    force_refresh: bool = False  # Re-assess even if already done
    deep_scan: bool = True  # Include file analysis


class QualityAssessmentResponse(BaseModel):
    """Quality assessment job response."""
    job_id: str
    status: str
    message: str
    projects_to_assess: int
