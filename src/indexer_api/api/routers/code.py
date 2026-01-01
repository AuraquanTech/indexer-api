"""
Code Discovery router.
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

from indexer_api.api.deps import AuthContext, DbSession
from indexer_api.schemas.base import PaginatedResponse
from indexer_api.schemas.code import (
    CodeAnalysisJob,
    CodeFileDetail,
    CodeFileResponse,
    CodeMetadata,
    CodeSearch,
    MVPReadiness,
    ProjectDependencies,
    ProjectStats,
)
from indexer_api.services.code_discovery import CodeDiscoveryService

router = APIRouter(prefix="/indexes/{index_id}/code", tags=["Code Discovery"])


# ============================================================================
# Code Analysis
# ============================================================================


@router.post(
    "/analyze",
    response_model=CodeAnalysisJob,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start code analysis",
)
async def start_code_analysis(
    index_id: str,
    auth: AuthContext,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> CodeAnalysisJob:
    """
    Start a code analysis job to extract metrics from source files.

    This analyzes code files to determine language, line counts, complexity,
    function/class counts, and import dependencies.
    """
    org_id, user_id = auth

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API keys cannot start analysis. Use JWT authentication.",
        )

    service = CodeDiscoveryService(db)

    try:
        job = await service.analyze_index(org_id, index_id, user_id)
        await db.commit()
        await db.refresh(job)

        # Add background task
        async def run_analysis(job_id: str):
            import asyncio
            await asyncio.sleep(0.1)
            from indexer_api.db.base import get_db_context
            async with get_db_context() as new_session:
                new_service = CodeDiscoveryService(new_session)
                await new_service.run_analysis_job(job_id)

        background_tasks.add_task(run_analysis, job.id)

        status_val = job.status.value if hasattr(job.status, 'value') else job.status
        return CodeAnalysisJob(
            job_id=job.id,
            index_id=index_id,
            status=status_val,
            total_files_to_analyze=job.total_files,
            message=f"Code analysis started. Analyzing {job.total_files} code files.",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================================
# Code File Browsing
# ============================================================================


@router.get(
    "/files",
    response_model=PaginatedResponse[CodeFileResponse],
    summary="List/search code files",
)
async def list_code_files(
    index_id: str,
    auth: AuthContext,
    db: DbSession,
    language: str | None = None,
    min_lines: int | None = Query(None, ge=0),
    max_lines: int | None = None,
    min_complexity: float | None = Query(None, ge=0),
    max_complexity: float | None = None,
    has_type_hints: bool | None = None,
    has_docstrings: bool | None = None,
    path_prefix: str | None = None,
    order_by: str = Query("path", pattern=r"^(path|filename|size_bytes|lines_total|complexity|functions|classes)$"),
    order_desc: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> PaginatedResponse[CodeFileResponse]:
    """
    List and search code files with analysis metadata.

    Supports filtering by language, line count, complexity, and more.
    """
    org_id, _ = auth
    service = CodeDiscoveryService(db)

    search = CodeSearch(
        language=language,
        min_lines=min_lines,
        max_lines=max_lines,
        min_complexity=min_complexity,
        max_complexity=max_complexity,
        has_type_hints=has_type_hints,
        has_docstrings=has_docstrings,
        path_prefix=path_prefix,
        order_by=order_by,
        order_desc=order_desc,
    )

    try:
        files, total = await service.search_code(
            org_id=org_id,
            index_id=index_id,
            search=search,
            page=page,
            page_size=page_size,
        )

        items = []
        for f in files:
            code_data = f.extra_metadata.get("code") if f.extra_metadata else None
            items.append(CodeFileResponse(
                id=f.id,
                index_id=f.index_id,
                path=f.path,
                filename=f.filename,
                extension=f.extension,
                size_bytes=f.size_bytes,
                modified_time=f.modified_time,
                indexed_at=f.indexed_at,
                code=CodeMetadata(**code_data) if code_data else None,
            ))

        return PaginatedResponse.create(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/files/{file_id}",
    response_model=CodeFileDetail,
    summary="Get code file details",
)
async def get_code_file(
    index_id: str,
    file_id: str,
    auth: AuthContext,
    db: DbSession,
) -> CodeFileDetail:
    """Get detailed analysis information about a specific code file."""
    from sqlalchemy import select
    from indexer_api.db.models import FileIndex, IndexedFile

    org_id, _ = auth

    # Get file with index verification
    result = await db.execute(
        select(IndexedFile)
        .join(FileIndex)
        .where(IndexedFile.id == file_id)
        .where(IndexedFile.index_id == index_id)
        .where(FileIndex.organization_id == org_id)
    )
    file = result.scalar_one_or_none()

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Code file not found",
        )

    code_data = file.extra_metadata.get("code") if file.extra_metadata else None

    return CodeFileDetail(
        id=file.id,
        index_id=file.index_id,
        path=file.path,
        filename=file.filename,
        extension=file.extension,
        size_bytes=file.size_bytes,
        modified_time=file.modified_time,
        indexed_at=file.indexed_at,
        md5_hash=file.md5_hash,
        quality_score=file.quality_score,
        complexity_score=file.complexity_score,
        code=CodeMetadata(**code_data) if code_data else None,
    )


# ============================================================================
# Project Statistics
# ============================================================================


@router.get(
    "/stats",
    response_model=ProjectStats,
    summary="Get project code statistics",
)
async def get_project_stats(
    index_id: str,
    auth: AuthContext,
    db: DbSession,
) -> ProjectStats:
    """
    Get aggregate statistics for code files in the index.

    Includes language breakdown, line counts, complexity metrics, and more.
    """
    org_id, _ = auth
    service = CodeDiscoveryService(db)

    stats = await service.get_project_stats(org_id, index_id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Index not found",
        )

    return stats


@router.get(
    "/dependencies",
    response_model=ProjectDependencies,
    summary="Get project dependencies",
)
async def get_dependencies(
    index_id: str,
    auth: AuthContext,
    db: DbSession,
) -> ProjectDependencies:
    """
    Analyze and return project dependencies.

    Categorizes imports into standard library, third-party, and local imports.
    """
    org_id, _ = auth
    service = CodeDiscoveryService(db)

    deps = await service.get_dependencies(org_id, index_id)
    if not deps:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Index not found",
        )

    return deps


# ============================================================================
# MVP Readiness
# ============================================================================


@router.get(
    "/mvp-score",
    response_model=MVPReadiness,
    summary="Get MVP readiness score",
)
async def get_mvp_readiness(
    index_id: str,
    auth: AuthContext,
    db: DbSession,
) -> MVPReadiness:
    """
    Calculate MVP readiness score for the project.

    Evaluates:
    - Documentation (README, code comments)
    - Testing (test files, coverage)
    - Project setup (license, gitignore, CI/CD)
    - Code quality (complexity, type hints)

    Returns a score from 0-100 with grade (A-F) and recommendations.
    """
    org_id, _ = auth
    service = CodeDiscoveryService(db)

    readiness = await service.calculate_mvp_readiness(org_id, index_id)
    if not readiness:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Index not found",
        )

    return readiness
