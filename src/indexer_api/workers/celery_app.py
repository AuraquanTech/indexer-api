"""
Celery application configuration for background tasks.
"""
from celery import Celery

from indexer_api.core.config import settings

# Create Celery app
celery_app = Celery(
    "indexer_api",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,  # Fair task distribution
    task_acks_late=True,  # Acknowledge after completion
    task_reject_on_worker_lost=True,
    result_expires=86400,  # Results expire after 1 day
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["indexer_api.workers"])
