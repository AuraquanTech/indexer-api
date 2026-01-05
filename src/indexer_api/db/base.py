"""
Database base configuration and session management.
"""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from indexer_api.core.config import settings

# Naming convention for constraints (PostgreSQL best practice)
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class for all database models."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=True,
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database sessions."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions (for background tasks)."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    from sqlalchemy import text

    async with engine.begin() as conn:
        # Enable WAL mode for SQLite (better concurrency)
        if "sqlite" in settings.database_url:
            await conn.execute(text("PRAGMA journal_mode=WAL"))
            await conn.execute(text("PRAGMA busy_timeout=30000"))

        # Get existing indexes to avoid conflicts
        def create_tables_safe(sync_conn):
            from sqlalchemy import inspect as sa_inspect
            inspector = sa_inspect(sync_conn)

            # Get all existing indexes across all tables
            existing_indexes = set()
            for table_name in inspector.get_table_names():
                for idx in inspector.get_indexes(table_name):
                    existing_indexes.add(idx['name'])

            # Create tables first (without indexes)
            for table in Base.metadata.sorted_tables:
                if not inspector.has_table(table.name):
                    # Create table without indexes
                    table.create(sync_conn, checkfirst=True)

            # Now create indexes that don't exist
            for table in Base.metadata.sorted_tables:
                for index in table.indexes:
                    if index.name not in existing_indexes:
                        try:
                            index.create(sync_conn)
                        except Exception:
                            pass  # Index might already exist

        await conn.run_sync(create_tables_safe)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
