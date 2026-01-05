"""
Catalog API router.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from indexer_api.api.deps import AuthContext, DbSession
from indexer_api.catalog.models import CatalogJob, CatalogJobRun, CatalogProject
from indexer_api.catalog.schemas import (
    CatalogProjectCreate,
    CatalogProjectOut,
    CatalogProjectUpdate,
    HealthReportOut,
    JobRunOut,
    JobStatusOut,
    ProjectListOut,
    ProjectSearchOut,
    ProjectSearchResult,
    ScanRequest,
    ScanResponse,
)
from indexer_api.catalog.llm_routes import llm_router

router = APIRouter(prefix="/catalog", tags=["Catalog"])

# Include LLM-powered routes
router.include_router(llm_router)

# ============================================================================
# Project CRUD
# ============================================================================


@router.get("/projects", response_model=ProjectListOut)
async def list_projects(
    auth: AuthContext,
    db: DbSession,
    lifecycle: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    project_type: Optional[str] = Query(None, alias="type"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
):
    """List all cataloged projects with filtering."""
    org_id, _ = auth

    query = select(CatalogProject).where(CatalogProject.organization_id == org_id)

    if lifecycle:
        query = query.where(CatalogProject.lifecycle == lifecycle)
    if project_type:
        query = query.where(CatalogProject.type == project_type)
    # Language filter requires JSON contains check
    if language:
        query = query.where(CatalogProject.languages.contains([language]))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Paginate
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    projects = result.scalars().all()

    return ProjectListOut(
        items=[CatalogProjectOut.model_validate(p) for p in projects],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/projects/{project_id}", response_model=CatalogProjectOut)
async def get_project(
    project_id: str,
    auth: AuthContext,
    db: DbSession,
):
    """Get a specific project by ID."""
    org_id, _ = auth

    result = await db.execute(
        select(CatalogProject).where(
            CatalogProject.id == project_id,
            CatalogProject.organization_id == org_id,
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return CatalogProjectOut.model_validate(project)


@router.post("/projects", response_model=CatalogProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: CatalogProjectCreate,
    auth: AuthContext,
    db: DbSession,
):
    """Create a new project in the catalog."""
    org_id, _ = auth

    # Check for duplicates
    existing = await db.execute(
        select(CatalogProject).where(
            CatalogProject.organization_id == org_id,
            CatalogProject.name == project_data.name,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Project with this name already exists")

    project = CatalogProject(
        organization_id=org_id,
        **project_data.model_dump(),
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    return CatalogProjectOut.model_validate(project)


@router.patch("/projects/{project_id}", response_model=CatalogProjectOut)
async def update_project(
    project_id: str,
    project_data: CatalogProjectUpdate,
    auth: AuthContext,
    db: DbSession,
):
    """Update a project."""
    org_id, _ = auth

    result = await db.execute(
        select(CatalogProject).where(
            CatalogProject.id == project_id,
            CatalogProject.organization_id == org_id,
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = project_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)

    await db.commit()
    await db.refresh(project)

    return CatalogProjectOut.model_validate(project)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    auth: AuthContext,
    db: DbSession,
):
    """Delete a project from the catalog."""
    org_id, _ = auth

    result = await db.execute(
        select(CatalogProject).where(
            CatalogProject.id == project_id,
            CatalogProject.organization_id == org_id,
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.delete(project)
    await db.commit()


# ============================================================================
# Search
# ============================================================================


@router.get("/search", response_model=ProjectSearchOut)
async def search_projects(
    auth: AuthContext,
    db: DbSession,
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
):
    """Full-text search across projects."""
    org_id, _ = auth

    # Simple LIKE search for now (upgrade to full-text search later)
    search_term = f"%{q}%"

    result = await db.execute(
        select(CatalogProject)
        .where(
            CatalogProject.organization_id == org_id,
            (
                CatalogProject.name.ilike(search_term) |
                CatalogProject.title.ilike(search_term) |
                CatalogProject.description.ilike(search_term) |
                CatalogProject.path.ilike(search_term)
            ),
        )
        .limit(limit)
    )
    projects = result.scalars().all()

    return ProjectSearchOut(
        results=[
            ProjectSearchResult(
                id=p.id,
                name=p.name,
                title=p.title,
                description=p.description,
                path=p.path,
                type=p.type,
                lifecycle=p.lifecycle,
                languages=p.languages or [],
                frameworks=p.frameworks or [],
                health_score=p.health_score,
                relevance_score=1.0,
            )
            for p in projects
        ],
        total=len(projects),
        query=q,
    )


# ============================================================================
# Job Status
# ============================================================================


@router.get("/jobs/{job_id}", response_model=JobStatusOut)
async def get_job_status(
    job_id: str,
    auth: AuthContext,
    db: DbSession,
):
    """Get job status and execution history."""
    org_id, _ = auth

    result = await db.execute(
        select(CatalogJob).where(
            CatalogJob.id == job_id,
            CatalogJob.organization_id == org_id,
        )
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get runs
    runs_result = await db.execute(
        select(CatalogJobRun)
        .where(CatalogJobRun.job_id == job.id)
        .order_by(CatalogJobRun.started_at.desc())
        .limit(10)
    )
    runs = [
        JobRunOut(
            started_at=r.started_at,
            finished_at=r.finished_at,
            status=r.status,
            result=r.result,
            error=r.error,
        )
        for r in runs_result.scalars().all()
    ]

    return JobStatusOut(
        job_id=job.id,
        job_type=job.job_type,
        status=job.status,
        priority=job.priority,
        attempts=job.attempts,
        max_attempts=job.max_attempts,
        created_at=job.created_at,
        updated_at=job.updated_at,
        run_after=job.run_after,
        last_error=job.last_error,
        runs=runs,
    )


# ============================================================================
# Health Report
# ============================================================================


@router.get("/health-report", response_model=HealthReportOut)
async def health_report(
    auth: AuthContext,
    db: DbSession,
):
    """Get aggregate portfolio health metrics."""
    org_id, _ = auth
    now = datetime.now(timezone.utc)

    # Total projects
    total_result = await db.execute(
        select(func.count()).select_from(CatalogProject).where(
            CatalogProject.organization_id == org_id
        )
    )
    total = total_result.scalar_one()

    # By lifecycle
    lifecycle_result = await db.execute(
        select(CatalogProject.lifecycle, func.count())
        .where(CatalogProject.organization_id == org_id)
        .group_by(CatalogProject.lifecycle)
    )
    by_lifecycle = {row[0]: row[1] for row in lifecycle_result.all()}

    # By type
    type_result = await db.execute(
        select(CatalogProject.type, func.count())
        .where(CatalogProject.organization_id == org_id)
        .group_by(CatalogProject.type)
    )
    by_type = {row[0]: row[1] for row in type_result.all()}

    # By language (aggregate from JSON)
    all_projects = await db.execute(
        select(CatalogProject.languages).where(
            CatalogProject.organization_id == org_id
        )
    )
    lang_counts: dict[str, int] = {}
    for (langs,) in all_projects.all():
        for lang in (langs or []):
            lang_counts[lang] = lang_counts.get(lang, 0) + 1

    # Avg health score
    avg_result = await db.execute(
        select(func.avg(CatalogProject.health_score))
        .where(
            CatalogProject.organization_id == org_id,
            CatalogProject.health_score.isnot(None),
        )
    )
    avg_health = avg_result.scalar_one()

    # Total LOC
    loc_result = await db.execute(
        select(func.sum(CatalogProject.loc_total))
        .where(CatalogProject.organization_id == org_id)
    )
    total_loc = loc_result.scalar_one()

    # Stale: no sync in 30+ days
    stale_cutoff = now - timedelta(days=30)
    stale_result = await db.execute(
        select(func.count())
        .select_from(CatalogProject)
        .where(
            CatalogProject.organization_id == org_id,
            (
                (CatalogProject.last_synced_at < stale_cutoff) |
                (CatalogProject.last_synced_at.is_(None))
            ),
        )
    )
    stale_count = stale_result.scalar_one()

    # Recently updated (7 days)
    recent_cutoff = now - timedelta(days=7)
    recent_result = await db.execute(
        select(func.count())
        .select_from(CatalogProject)
        .where(
            CatalogProject.organization_id == org_id,
            CatalogProject.updated_at >= recent_cutoff,
        )
    )
    recently_updated = recent_result.scalar_one()

    return HealthReportOut(
        total_projects=total,
        by_lifecycle=by_lifecycle,
        by_language=lang_counts,
        by_type=by_type,
        avg_health_score=round(avg_health, 2) if avg_health else None,
        stale_count=stale_count,
        recently_updated=recently_updated,
        total_loc=total_loc,
        generated_at=now,
    )


# ============================================================================
# Scan
# ============================================================================


@router.post("/scan", response_model=ScanResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_scan(
    scan_data: ScanRequest,
    auth: AuthContext,
    db: DbSession,
):
    """Trigger a filesystem scan for new/changed projects."""
    org_id, user_id = auth

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API keys cannot trigger scans. Use JWT authentication.",
        )

    # Create job
    job = CatalogJob(
        organization_id=org_id,
        job_type="scan",
        status="pending",
        result={"paths": scan_data.paths, "max_depth": scan_data.max_depth},
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # TODO: Enqueue actual scan task via Celery or background task

    return ScanResponse(
        job_id=job.id,
        status="pending",
        message=f"Scan job enqueued for {len(scan_data.paths)} paths",
    )
