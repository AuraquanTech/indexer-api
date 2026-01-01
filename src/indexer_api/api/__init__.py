"""API module."""
from indexer_api.api.deps import (
    AuthContext,
    CurrentUser,
    DbSession,
    OptionalUser,
    get_auth_context,
    get_current_user,
    require_role,
    require_scope,
)
from indexer_api.api.routers import auth_router, health_router, indexes_router

__all__ = [
    # Dependencies
    "CurrentUser",
    "OptionalUser",
    "AuthContext",
    "DbSession",
    "get_current_user",
    "get_auth_context",
    "require_role",
    "require_scope",
    # Routers
    "auth_router",
    "health_router",
    "indexes_router",
]
