"""
Celery tasks for background processing.
"""
import asyncio
from datetime import datetime, timedelta, timezone

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from indexer_api.core.config import settings
from indexer_api.core.logging import get_logger
from indexer_api.db.models import IndexJob, JobStatus
from indexer_api.services.indexer import IndexerService

logger = get_logger(__name__)


# Create a separate engine for Celery workers
worker_engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=True,
)
worker_session_maker = async_sessionmaker(
    worker_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def run_async(coro):
    """Run async code in Celery task."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@shared_task(
    bind=True,
    name="indexer_api.run_index_job",
    max_retries=3,
    default_retry_delay=60,
)
def run_index_job_task(self, job_id: str) -> dict:
    """
    Run an indexing job in the background.

    Args:
        job_id: The ID of the IndexJob to run

    Returns:
        dict with job results
    """
    logger.info("starting_index_job", job_id=job_id, celery_task_id=self.request.id)

    async def _run():
        async with worker_session_maker() as session:
            try:
                # Update job with Celery task ID
                result = await session.execute(
                    select(IndexJob).where(IndexJob.id == job_id)
                )
                job = result.scalar_one_or_none()

                if not job:
                    logger.error("job_not_found", job_id=job_id)
                    return {"status": "error", "message": "Job not found"}

                job.celery_task_id = self.request.id
                await session.commit()

                # Run the indexing
                service = IndexerService(session)
                await service.run_index_job(job_id)

                await session.commit()

                return {
                    "status": "completed",
                    "job_id": job_id,
                    "total_files": job.total_files,
                    "processed_files": job.processed_files,
                }

            except Exception as e:
                logger.error("job_failed", job_id=job_id, error=str(e))
                await session.rollback()

                # Update job status to failed
                result = await session.execute(
                    select(IndexJob).where(IndexJob.id == job_id)
                )
                job = result.scalar_one_or_none()
                if job:
                    job.status = JobStatus.FAILED
                    job.error_message = str(e)
                    job.completed_at = datetime.now(timezone.utc)
                    await session.commit()

                # Only retry if we haven't exhausted retries
                if self.request.retries < self.max_retries:
                    raise self.retry(exc=e)
                else:
                    # Max retries reached - return error instead of raising
                    return {"status": "failed", "job_id": job_id, "error": str(e)}

    return run_async(_run())


@shared_task(name="indexer_api.cleanup_old_jobs")
def cleanup_old_jobs_task(days: int = 30) -> dict:
    """
    Clean up completed jobs older than specified days.
    """
    from sqlalchemy import delete

    logger.info("cleaning_up_old_jobs", days=days)

    async def _cleanup():
        async with worker_session_maker() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            result = await session.execute(
                delete(IndexJob)
                .where(IndexJob.completed_at < cutoff)
                .where(IndexJob.status.in_([JobStatus.COMPLETED, JobStatus.FAILED]))
            )

            await session.commit()
            count = result.rowcount

            logger.info("cleaned_up_jobs", count=count)
            return {"deleted_count": count}

    return run_async(_cleanup())


@shared_task(name="indexer_api.update_usage_stats")
def update_usage_stats_task(org_id: str) -> dict:
    """
    Update organization usage statistics.
    """
    from sqlalchemy import func

    from indexer_api.db.models import FileIndex, Organization

    logger.info("updating_usage_stats", org_id=org_id)

    async def _update():
        async with worker_session_maker() as session:
            # Calculate total storage
            result = await session.execute(
                select(func.sum(FileIndex.total_size_bytes))
                .where(FileIndex.organization_id == org_id)
                .where(FileIndex.is_active == True)
            )
            total_bytes = result.scalar() or 0
            total_mb = total_bytes / (1024 * 1024)

            # Update organization
            result = await session.execute(
                select(Organization).where(Organization.id == org_id)
            )
            org = result.scalar_one_or_none()

            if org:
                org.current_storage_mb = total_mb
                await session.commit()

            return {"org_id": org_id, "storage_mb": total_mb}

    return run_async(_update())
