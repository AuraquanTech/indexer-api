"""
Pytest fixtures and configuration.
"""
import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from indexer_api.db.base import Base, get_db
from indexer_api.main import app

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user."""
    from indexer_api.schemas.auth import UserCreate
    from indexer_api.services.auth import AuthService

    auth_service = AuthService(db_session)
    user_data = UserCreate(
        email="test@example.com",
        password="Test1234!",
        organization_name="Test Org",
        full_name="Test User",
    )
    user = await auth_service.create_user(user_data)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def auth_headers(db_session: AsyncSession, test_user) -> dict:
    """Get authentication headers for test user."""
    from indexer_api.services.auth import AuthService

    auth_service = AuthService(db_session)
    tokens = await auth_service.create_tokens(test_user)

    return {"Authorization": f"Bearer {tokens.access_token}"}
