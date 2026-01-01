"""
FastAPI application entry point.
"""
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from indexer_api.api.routers import auth_router, code_router, dam_router, health_router, indexes_router
from indexer_api.core.config import settings
from indexer_api.core.logging import get_logger, setup_logging
from indexer_api.db.base import close_db, init_db

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""

    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Get client identifier (IP or API key)
        client_id = request.headers.get("X-API-Key") or request.client.host or "unknown"
        now = time.time()
        window_start = now - 60  # 1 minute window

        # Clean old requests
        self.requests[client_id] = [
            ts for ts in self.requests[client_id] if ts > window_start
        ]

        # Check rate limit
        if len(self.requests[client_id]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit of {self.requests_per_minute} requests/minute exceeded",
                    "retry_after": 60,
                },
                headers={"Retry-After": "60"},
            )

        # Record request
        self.requests[client_id].append(now)

        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan - startup and shutdown."""
    # Startup
    setup_logging()
    logger.info(
        "starting_application",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )

    await init_db()
    logger.info("database_initialized")

    yield

    # Shutdown
    await close_db()
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="""
# IndexerAPI - Enterprise File Indexing Service

Fast, scalable file indexing as a service.

## Features

- **File System Indexing**: High-performance directory scanning
- **Search & Queries**: Find files by name, extension, size, and more
- **Duplicate Detection**: Identify duplicate files by content hash
- **Multi-tenant**: Organizations with user management
- **API Keys**: Programmatic access with scoped permissions

## Authentication

Two authentication methods are supported:

1. **JWT Tokens**: Use `/auth/login` to get tokens, include in `Authorization: Bearer <token>` header
2. **API Keys**: Create via `/auth/api-keys`, include in `X-API-Key` header

## Rate Limits

| Tier | Requests/minute |
|------|-----------------|
| Free | 100 |
| Pro | 1000 |
| Enterprise | Unlimited |
        """,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Rate limiting middleware (must be added first to process last)
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=settings.rate_limit_requests,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "validation_error", "message": str(exc)},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_error",
                "message": "An unexpected error occurred",
            },
        )

    # Include routers
    app.include_router(health_router)
    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(indexes_router, prefix=settings.api_prefix)
    app.include_router(dam_router, prefix=settings.api_prefix)
    app.include_router(code_router, prefix=settings.api_prefix)

    return app


# Create app instance
app = create_app()
