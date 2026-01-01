"""Database module - models and session management."""
from indexer_api.db.base import (
    Base,
    async_session_maker,
    close_db,
    engine,
    get_db,
    get_db_context,
    init_db,
)
from indexer_api.db.models import (
    APIKey,
    FileIndex,
    IndexedFile,
    IndexJob,
    JobStatus,
    JobType,
    Organization,
    SubscriptionTier,
    UsageRecord,
    User,
    UserRole,
)

__all__ = [
    # Base
    "Base",
    "engine",
    "async_session_maker",
    "get_db",
    "get_db_context",
    "init_db",
    "close_db",
    # Models
    "Organization",
    "User",
    "UserRole",
    "SubscriptionTier",
    "APIKey",
    "FileIndex",
    "IndexedFile",
    "IndexJob",
    "JobStatus",
    "JobType",
    "UsageRecord",
]
