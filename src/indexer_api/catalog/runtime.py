"""
Catalog runtime - watcher and job worker management.

Manages the background services for the catalog module.

This module is designed with production-grade reliability:
- Isolated database sessions per job execution
- Proper cleanup on shutdown
- Graceful error handling with exponential backoff
- Clear separation between job discovery and execution
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Set

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from indexer_api.catalog.job_handlers import execute_job
from indexer_api.catalog.models import CatalogJob, CatalogJobRun
from indexer_api.catalog.watcher import WatcherDaemon
from indexer_api.core.logging import get_logger
from indexer_api.db.base import get_db_context

logger = get_logger(__name__)

# Global runtime state
_watcher: Optional[WatcherDaemon] = None
_worker_task: Optional[asyncio.Task] = None
_running = False


async def start_catalog_runtime() -> None:
    """
    Start the catalog runtime (watcher + job worker).

    Initializes:
    - File system watcher for configured paths
    - Background job worker for processing queued jobs
    """
    global _watcher, _worker_task, _running

    if _running:
        logger.warning("catalog_runtime_already_running")
        return

    _running = True

    # Get watch paths from environment
    watch_paths_str = os.environ.get("CATALOG_WATCH_PATHS", "")
    watch_paths = [p.strip() for p in watch_paths_str.split(",") if p.strip()]

    if watch_paths:
        _watcher = WatcherDaemon(
            watch_paths=watch_paths,
            on_refresh=_enqueue_refresh_job,
            debounce_seconds=float(os.environ.get("CATALOG_DEBOUNCE_SECONDS", "5.0")),
            max_wait_seconds=float(os.environ.get("CATALOG_MAX_WAIT_SECONDS", "30.0")),
        )
        await _watcher.start()

    # Start job worker
    _worker_task = asyncio.create_task(_run_job_worker())

    logger.info(
        "catalog_runtime_started",
        watch_paths=watch_paths,
        worker="enabled",
    )


async def stop_catalog_runtime() -> None:
    """
    Stop the catalog runtime gracefully.

    Waits for active jobs to complete before shutting down.
    """
    global _watcher, _worker_task, _running

    _running = False

    if _watcher:
        await _watcher.stop()
        _watcher = None

    if _worker_task:
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass
        _worker_task = None

    logger.info("catalog_runtime_stopped")


async def _enqueue_refresh_job(project_path: Path) -> None:
    """
    Enqueue a refresh job for a project (called by watcher).

    Creates a new refresh job in the database for the project
    at the specified path.
    """
    from indexer_api.catalog.models import CatalogProject

    async with get_db_context() as db:
        # Find the project by path
        result = await db.execute(
            select(CatalogProject).where(CatalogProject.path == str(project_path))
        )
        project = result.scalar_one_or_none()

        if not project:
            logger.debug("refresh_job_skip_unknown_path", path=str(project_path))
            return

        # Check if there's already a pending refresh job for this project
        existing = await db.execute(
            select(CatalogJob).where(
                CatalogJob.project_id == project.id,
                CatalogJob.job_type == "refresh",
                CatalogJob.status.in_(["pending", "running"]),
            )
        )
        if existing.scalar_one_or_none():
            logger.debug("refresh_job_already_pending", project=project.name)
            return

        # Create new refresh job
        job = CatalogJob(
            organization_id=project.organization_id,
            job_type="refresh",
            project_id=project.id,
            priority=5,  # Medium priority
        )
        db.add(job)
        await db.commit()

        logger.info("refresh_job_enqueued", project=project.name)


async def _run_job_worker() -> None:
    """
    Background job worker loop.

    Polls for pending jobs and executes them with proper isolation.
    Each job gets its own database session to prevent state corruption.
    """
    poll_interval = float(os.environ.get("CATALOG_WORKER_POLL_INTERVAL", "5.0"))
    max_concurrent = int(os.environ.get("CATALOG_WORKER_MAX_CONCURRENT", "3"))

    logger.info(
        "job_worker_started",
        poll_interval=poll_interval,
        max_concurrent=max_concurrent,
    )

    active_jobs: Set[str] = set()

    while _running:
        try:
            # Use a dedicated session for job discovery
            async with get_db_context() as db:
                now = datetime.now(timezone.utc)

                # Find pending jobs that aren't already being processed
                result = await db.execute(
                    select(CatalogJob)
                    .where(
                        CatalogJob.status == "pending",
                        CatalogJob.run_after <= now,
                        CatalogJob.id.notin_(active_jobs) if active_jobs else True,
                    )
                    .order_by(CatalogJob.priority, CatalogJob.created_at)
                    .limit(max_concurrent - len(active_jobs))
                )
                jobs = result.scalars().all()

                for job in jobs:
                    if len(active_jobs) >= max_concurrent:
                        break

                    # Mark as running in the discovery session
                    job.status = "running"
                    job.attempts += 1
                    job.started_at = now
                    await db.commit()

                    active_jobs.add(job.id)

                    # Execute in separate task with its own session
                    asyncio.create_task(
                        _execute_job_isolated(job.id, active_jobs)
                    )

        except Exception as e:
            logger.error("job_worker_poll_error", error=str(e))

        await asyncio.sleep(poll_interval)


async def _execute_job_isolated(job_id: str, active_jobs: Set[str]) -> None:
    """
    Execute a job with an isolated database session.

    This ensures that each job execution has its own clean session,
    preventing state corruption between concurrent jobs.

    Args:
        job_id: ID of the job to execute
        active_jobs: Set of active job IDs (for cleanup on completion)
    """
    try:
        # Create a fresh session for this job execution
        async with get_db_context() as db:
            # Re-fetch the job in this session
            result = await db.execute(
                select(CatalogJob).where(CatalogJob.id == job_id)
            )
            job = result.scalar_one_or_none()

            if not job:
                logger.warning("job_not_found", job_id=job_id)
                return

            # Create job run record
            run = CatalogJobRun(
                job_id=job.id,
                status="running",
            )
            db.add(run)
            await db.commit()

            try:
                # Execute the job with this isolated session
                result_data = await execute_job(job, db)

                # Determine final status
                if result_data.get("status") == "error":
                    final_status = "failed"
                elif result_data.get("status") == "skipped":
                    final_status = "completed"  # Skipped is still "completed"
                else:
                    final_status = "completed"

                # Update job status
                job.status = final_status
                job.completed_at = datetime.now(timezone.utc)
                job.result = result_data

                # Update run record
                run.status = "succeeded" if final_status == "completed" else "failed"
                run.finished_at = datetime.now(timezone.utc)
                run.result = result_data

                await db.commit()

                logger.info(
                    "job_completed",
                    job_id=job_id,
                    job_type=job.job_type,
                    status=final_status,
                    result=result_data.get("status"),
                )

            except Exception as e:
                # Job execution failed
                error_data = {
                    "message": str(e),
                    "type": type(e).__name__,
                }

                # Update run record
                run.status = "failed"
                run.finished_at = datetime.now(timezone.utc)
                run.error = error_data

                # Re-fetch job to ensure we have the latest state
                await db.refresh(job)

                job.last_error = error_data

                # Check if we should retry
                if job.attempts < job.max_attempts:
                    # Exponential backoff: 5s, 10s, 20s, 40s, ... up to 5 minutes
                    backoff_seconds = min(300, (2 ** job.attempts) * 5)
                    job.status = "pending"
                    job.run_after = datetime.now(timezone.utc) + timedelta(
                        seconds=backoff_seconds
                    )
                    logger.warning(
                        "job_retry_scheduled",
                        job_id=job_id,
                        attempt=job.attempts,
                        max_attempts=job.max_attempts,
                        backoff_seconds=backoff_seconds,
                        error=str(e),
                    )
                else:
                    # Max attempts exceeded, move to failed
                    job.status = "failed"
                    job.completed_at = datetime.now(timezone.utc)
                    logger.error(
                        "job_failed_permanently",
                        job_id=job_id,
                        attempts=job.attempts,
                        error=str(e),
                    )

                await db.commit()

    except Exception as e:
        # Critical error in job execution wrapper
        logger.error(
            "job_execution_critical_error",
            job_id=job_id,
            error=str(e),
            exc_info=True,
        )

        # Try to mark job as failed
        try:
            async with get_db_context() as db:
                await db.execute(
                    update(CatalogJob)
                    .where(CatalogJob.id == job_id)
                    .values(
                        status="failed",
                        completed_at=datetime.now(timezone.utc),
                        last_error={"message": str(e), "type": "CriticalError"},
                    )
                )
                await db.commit()
        except Exception:
            pass  # Best effort

    finally:
        # Always remove from active jobs set
        active_jobs.discard(job_id)


def get_watcher() -> Optional[WatcherDaemon]:
    """Get the global watcher instance."""
    return _watcher


def is_running() -> bool:
    """Check if the catalog runtime is running."""
    return _running
