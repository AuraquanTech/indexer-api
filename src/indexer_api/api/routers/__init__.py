"""API routers."""
from indexer_api.api.routers.auth import router as auth_router
from indexer_api.api.routers.code import router as code_router
from indexer_api.api.routers.dam import router as dam_router
from indexer_api.api.routers.health import router as health_router
from indexer_api.api.routers.indexes import router as indexes_router

__all__ = [
    "auth_router",
    "code_router",
    "dam_router",
    "health_router",
    "indexes_router",
]
