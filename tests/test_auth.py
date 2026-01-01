"""
Tests for authentication endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "organization_name": "New Org",
            "full_name": "New User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["organization"]["name"] == "New Org"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user):
    """Test registration with duplicate email fails."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",  # Already exists
            "password": "SecurePass123!",
            "organization_name": "Another Org",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user):
    """Test successful login."""
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "test@example.com",
            "password": "Test1234!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user):
    """Test login with wrong password."""
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "test@example.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, auth_headers):
    """Test getting current user profile."""
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_create_api_key(client: AsyncClient, auth_headers):
    """Test creating an API key."""
    response = await client.post(
        "/api/v1/auth/api-keys",
        headers=auth_headers,
        json={
            "name": "Test Key",
            "scopes": ["read", "write"],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "key" in data
    assert data["name"] == "Test Key"
    assert data["key"].startswith("idx_")


@pytest.mark.asyncio
async def test_list_api_keys(client: AsyncClient, auth_headers):
    """Test listing API keys."""
    # Create a key first
    await client.post(
        "/api/v1/auth/api-keys",
        headers=auth_headers,
        json={"name": "Test Key", "scopes": ["read"]},
    )

    response = await client.get("/api/v1/auth/api-keys", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
