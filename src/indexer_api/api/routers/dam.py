"""
Digital Asset Management (DAM) router.
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

from indexer_api.api.deps import AuthContext, DbSession
from indexer_api.db.models import AssetType
from indexer_api.schemas.base import PaginatedResponse
from indexer_api.schemas.dam import (
    DAMAnalysisJob,
    DAMAssetDetail,
    DAMAssetResponse,
    DAMMetadata,
    DAMSearch,
    DAMStats,
)
from indexer_api.services.dam import DAMService

router = APIRouter(prefix="/indexes/{index_id}/dam", tags=["Digital Asset Management"])


# ============================================================================
# DAM Analysis
# ============================================================================


@router.post(
    "/analyze",
    response_model=DAMAnalysisJob,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start DAM analysis",
)
async def start_dam_analysis(
    index_id: str,
    auth: AuthContext,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> DAMAnalysisJob:
    """
    Start a DAM analysis job to extract metadata from media files.

    This analyzes images, videos, audio files, and documents in the index,
    extracting EXIF data, dimensions, duration, and other metadata.
    """
    org_id, user_id = auth

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API keys cannot start analysis. Use JWT authentication.",
        )

    service = DAMService(db)

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
                new_service = DAMService(new_session)
                await new_service.run_analysis_job(job_id)

        background_tasks.add_task(run_analysis, job.id)

        status_val = job.status.value if hasattr(job.status, 'value') else job.status
        return DAMAnalysisJob(
            job_id=job.id,
            index_id=index_id,
            status=status_val,
            total_files_to_analyze=job.total_files,
            message=f"DAM analysis started. Analyzing {job.total_files} media files.",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================================
# Asset Browsing
# ============================================================================


@router.get(
    "/assets",
    response_model=PaginatedResponse[DAMAssetResponse],
    summary="List/search media assets",
)
async def list_assets(
    index_id: str,
    auth: AuthContext,
    db: DbSession,
    asset_type: AssetType | None = None,
    min_width: int | None = Query(None, ge=0),
    max_width: int | None = None,
    min_height: int | None = Query(None, ge=0),
    max_height: int | None = None,
    min_duration: float | None = Query(None, ge=0),
    max_duration: float | None = None,
    format: str | None = None,
    has_exif: bool | None = None,
    has_gps: bool | None = None,
    order_by: str = Query("filename", pattern=r"^(filename|size_bytes|modified_time|width|height|duration_seconds)$"),
    order_desc: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> PaginatedResponse[DAMAssetResponse]:
    """
    List and search media assets with DAM metadata.

    Supports filtering by asset type, dimensions, duration, and format.
    """
    org_id, _ = auth
    service = DAMService(db)

    search = DAMSearch(
        asset_type=asset_type,
        min_width=min_width,
        max_width=max_width,
        min_height=min_height,
        max_height=max_height,
        min_duration=min_duration,
        max_duration=max_duration,
        format=format,
        has_exif=has_exif,
        has_gps=has_gps,
        order_by=order_by,
        order_desc=order_desc,
    )

    try:
        files, total = await service.search_assets(
            org_id=org_id,
            index_id=index_id,
            search=search,
            page=page,
            page_size=page_size,
        )

        items = []
        for f in files:
            dam_data = f.extra_metadata.get("dam") if f.extra_metadata else None
            items.append(DAMAssetResponse(
                id=f.id,
                index_id=f.index_id,
                path=f.path,
                filename=f.filename,
                extension=f.extension,
                size_bytes=f.size_bytes,
                created_time=f.created_time,
                modified_time=f.modified_time,
                mime_type=f.mime_type,
                indexed_at=f.indexed_at,
                dam=DAMMetadata(**dam_data) if dam_data else None,
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
    "/assets/{file_id}",
    response_model=DAMAssetDetail,
    summary="Get asset details",
)
async def get_asset(
    index_id: str,
    file_id: str,
    auth: AuthContext,
    db: DbSession,
) -> DAMAssetDetail:
    """Get detailed information about a specific media asset."""
    org_id, _ = auth
    service = DAMService(db)

    file = await service.get_asset(org_id, index_id, file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )

    dam_data = file.extra_metadata.get("dam") if file.extra_metadata else None

    return DAMAssetDetail(
        id=file.id,
        index_id=file.index_id,
        path=file.path,
        filename=file.filename,
        extension=file.extension,
        size_bytes=file.size_bytes,
        created_time=file.created_time,
        modified_time=file.modified_time,
        mime_type=file.mime_type,
        indexed_at=file.indexed_at,
        md5_hash=file.md5_hash,
        sha256_hash=file.sha256_hash,
        quality_score=file.quality_score,
        dam=DAMMetadata(**dam_data) if dam_data else None,
    )


# ============================================================================
# DAM Statistics
# ============================================================================


@router.get(
    "/stats",
    response_model=DAMStats,
    summary="Get DAM statistics",
)
async def get_dam_stats(
    index_id: str,
    auth: AuthContext,
    db: DbSession,
) -> DAMStats:
    """
    Get aggregate statistics for media assets in the index.

    Includes counts by type, size breakdown, format distribution, and more.
    """
    org_id, _ = auth
    service = DAMService(db)

    stats = await service.get_stats(org_id, index_id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Index not found",
        )

    return stats
