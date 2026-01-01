"""
Indexes router - file indexing and search endpoints.
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

from indexer_api.api.deps import AuthContext, DbSession
from indexer_api.db.models import JobStatus, JobType
from indexer_api.schemas.base import PaginatedResponse, SuccessResponse
from indexer_api.schemas.index import (
    DuplicateFilesResponse,
    FileIndexCreate,
    FileIndexResponse,
    FileIndexStats,
    FileIndexUpdate,
    IndexedFileResponse,
    IndexedFileSearch,
    IndexJobCreate,
    IndexJobResponse,
)
from indexer_api.services.indexer import IndexerService

router = APIRouter(prefix="/indexes", tags=["Indexes"])


# ============================================================================
# Index CRUD
# ============================================================================


@router.post(
    "",
    response_model=FileIndexResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new file index",
)
async def create_index(
    index_data: FileIndexCreate,
    auth: AuthContext,
    db: DbSession,
) -> FileIndexResponse:
    """
    Create a new file index.

    Specify the root path and patterns for files to include/exclude.
    """
    org_id, user_id = auth
    service = IndexerService(db)

    try:
        index = await service.create_index(org_id, index_data)
        return FileIndexResponse.model_validate(index)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "",
    response_model=list[FileIndexResponse],
    summary="List all indexes",
)
async def list_indexes(
    auth: AuthContext,
    db: DbSession,
) -> list[FileIndexResponse]:
    """List all file indexes for the organization."""
    org_id, _ = auth
    service = IndexerService(db)

    indexes = await service.list_indexes(org_id)
    return [FileIndexResponse.model_validate(idx) for idx in indexes]


@router.get(
    "/{index_id}",
    response_model=FileIndexResponse,
    summary="Get index details",
)
async def get_index(
    index_id: str,
    auth: AuthContext,
    db: DbSession,
) -> FileIndexResponse:
    """Get details of a specific index."""
    org_id, _ = auth
    service = IndexerService(db)

    index = await service.get_index(org_id, index_id)
    if not index:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Index not found",
        )

    return FileIndexResponse.model_validate(index)


@router.patch(
    "/{index_id}",
    response_model=FileIndexResponse,
    summary="Update an index",
)
async def update_index(
    index_id: str,
    update_data: FileIndexUpdate,
    auth: AuthContext,
    db: DbSession,
) -> FileIndexResponse:
    """Update an existing file index."""
    from sqlalchemy import select
    from indexer_api.db.models import FileIndex

    org_id, _ = auth
    service = IndexerService(db)

    index = await service.get_index(org_id, index_id)
    if not index:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Index not found",
        )

    # Apply updates
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(index, field, value)

    await db.flush()
    await db.refresh(index)

    return FileIndexResponse.model_validate(index)


@router.delete(
    "/{index_id}",
    response_model=SuccessResponse,
    summary="Delete an index",
)
async def delete_index(
    index_id: str,
    auth: AuthContext,
    db: DbSession,
) -> SuccessResponse:
    """Delete an index and all its indexed files."""
    org_id, _ = auth
    service = IndexerService(db)

    success = await service.delete_index(org_id, index_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Index not found",
        )

    return SuccessResponse(message="Index deleted")


@router.get(
    "/{index_id}/stats",
    response_model=FileIndexStats,
    summary="Get index statistics",
)
async def get_index_stats(
    index_id: str,
    auth: AuthContext,
    db: DbSession,
) -> FileIndexStats:
    """Get detailed statistics for an index."""
    org_id, _ = auth
    service = IndexerService(db)

    stats = await service.get_index_stats(org_id, index_id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Index not found",
        )

    return stats


# ============================================================================
# Index Jobs
# ============================================================================


@router.post(
    "/{index_id}/scan",
    response_model=IndexJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start an indexing scan",
)
async def start_index_scan(
    index_id: str,
    job_data: IndexJobCreate,
    auth: AuthContext,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> IndexJobResponse:
    """
    Start a new indexing scan job.

    The scan runs in the background. Use the jobs endpoint to track progress.
    """
    org_id, user_id = auth
    service = IndexerService(db)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API keys cannot start scans. Use JWT authentication.",
        )

    try:
        job = await service.start_index_job(
            org_id=org_id,
            index_id=index_id,
            user_id=user_id,
            job_type=job_data.job_type,
        )

        # Commit job to database before background task starts
        await db.commit()
        await db.refresh(job)

        # Add background task with its own session
        async def run_job(job_id: str):
            import asyncio
            # Small delay to ensure transaction is fully committed
            await asyncio.sleep(0.1)
            from indexer_api.db.base import get_db_context
            async with get_db_context() as new_session:
                new_service = IndexerService(new_session)
                await new_service.run_index_job(job_id)

        background_tasks.add_task(run_job, job.id)

        return IndexJobResponse.model_validate(job)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{index_id}/jobs",
    response_model=list[IndexJobResponse],
    summary="List indexing jobs",
)
async def list_index_jobs(
    index_id: str,
    auth: AuthContext,
    db: DbSession,
    status_filter: JobStatus | None = Query(None, alias="status"),
    limit: int = Query(10, ge=1, le=100),
) -> list[IndexJobResponse]:
    """List indexing jobs for an index."""
    from sqlalchemy import select

    from indexer_api.db.models import FileIndex, IndexJob

    org_id, _ = auth

    # Verify access
    service = IndexerService(db)
    index = await service.get_index(org_id, index_id)
    if not index:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Index not found",
        )

    # Query jobs
    query = (
        select(IndexJob)
        .where(IndexJob.index_id == index_id)
        .order_by(IndexJob.created_at.desc())
        .limit(limit)
    )

    if status_filter:
        query = query.where(IndexJob.status == status_filter)

    result = await db.execute(query)
    jobs = result.scalars().all()

    return [IndexJobResponse.model_validate(job) for job in jobs]


@router.get(
    "/{index_id}/jobs/{job_id}",
    response_model=IndexJobResponse,
    summary="Get job details",
)
async def get_job(
    index_id: str,
    job_id: str,
    auth: AuthContext,
    db: DbSession,
) -> IndexJobResponse:
    """Get details of a specific job."""
    from sqlalchemy import select

    from indexer_api.db.models import IndexJob

    org_id, _ = auth

    # Verify access
    service = IndexerService(db)
    index = await service.get_index(org_id, index_id)
    if not index:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Index not found",
        )

    result = await db.execute(
        select(IndexJob)
        .where(IndexJob.id == job_id)
        .where(IndexJob.index_id == index_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    return IndexJobResponse.model_validate(job)


# ============================================================================
# File Search & Queries
# ============================================================================


@router.get(
    "/{index_id}/files",
    response_model=PaginatedResponse[IndexedFileResponse],
    summary="Search indexed files",
)
async def search_files(
    index_id: str,
    auth: AuthContext,
    db: DbSession,
    query: str | None = Query(None, max_length=500),
    extension: str | None = None,
    min_size: int | None = Query(None, ge=0),
    max_size: int | None = None,
    path_prefix: str | None = None,
    order_by: str = Query("path", pattern=r"^(path|filename|size_bytes|modified_time|quality_score)$"),
    order_desc: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> PaginatedResponse[IndexedFileResponse]:
    """
    Search for files in an index.

    Supports filtering by:
    - Text query (filename/path)
    - File extension
    - Size range
    - Path prefix
    """
    org_id, _ = auth
    service = IndexerService(db)

    search = IndexedFileSearch(
        query=query,
        extension=extension,
        min_size=min_size,
        max_size=max_size,
        path_prefix=path_prefix,
        order_by=order_by,
        order_desc=order_desc,
    )

    files, total = await service.search_files(
        org_id=org_id,
        index_id=index_id,
        search=search,
        page=page,
        page_size=page_size,
    )

    return PaginatedResponse.create(
        items=[IndexedFileResponse.model_validate(f) for f in files],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{index_id}/duplicates",
    response_model=list[DuplicateFilesResponse],
    summary="Find duplicate files",
)
async def find_duplicates(
    index_id: str,
    auth: AuthContext,
    db: DbSession,
) -> list[DuplicateFilesResponse]:
    """Find duplicate files by content hash."""
    org_id, _ = auth
    service = IndexerService(db)

    duplicates = await service.find_duplicates(org_id, index_id)

    return [
        DuplicateFilesResponse(
            hash=d["hash"],
            file_count=d["file_count"],
            total_size_bytes=d["total_size_bytes"],
            files=[IndexedFileResponse.model_validate(f) for f in d["files"]],
        )
        for d in duplicates
    ]
