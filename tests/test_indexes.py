"""
Tests for file indexing endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_index(client: AsyncClient, auth_headers, tmp_path):
    """Test creating a new file index."""
    response = await client.post(
        "/api/v1/indexes",
        headers=auth_headers,
        json={
            "name": "Test Index",
            "description": "A test index",
            "root_path": str(tmp_path),
            "include_patterns": ["*"],
            "exclude_patterns": ["*.git*"],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Index"
    assert data["root_path"] == str(tmp_path)


@pytest.mark.asyncio
async def test_list_indexes(client: AsyncClient, auth_headers, tmp_path):
    """Test listing indexes."""
    # Create an index first
    await client.post(
        "/api/v1/indexes",
        headers=auth_headers,
        json={"name": "List Test", "root_path": str(tmp_path)},
    )

    response = await client.get("/api/v1/indexes", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_index(client: AsyncClient, auth_headers, tmp_path):
    """Test getting a specific index."""
    # Create an index
    create_response = await client.post(
        "/api/v1/indexes",
        headers=auth_headers,
        json={"name": "Get Test", "root_path": str(tmp_path)},
    )
    index_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/indexes/{index_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == index_id
    assert data["name"] == "Get Test"


@pytest.mark.asyncio
async def test_get_nonexistent_index(client: AsyncClient, auth_headers):
    """Test getting a non-existent index returns 404."""
    response = await client.get(
        "/api/v1/indexes/nonexistent-id",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_index(client: AsyncClient, auth_headers, tmp_path):
    """Test deleting an index."""
    # Create an index
    create_response = await client.post(
        "/api/v1/indexes",
        headers=auth_headers,
        json={"name": "Delete Test", "root_path": str(tmp_path)},
    )
    index_id = create_response.json()["id"]

    # Delete it
    response = await client.delete(f"/api/v1/indexes/{index_id}", headers=auth_headers)
    assert response.status_code == 200

    # Verify it's gone
    get_response = await client.get(f"/api/v1/indexes/{index_id}", headers=auth_headers)
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_search_files(client: AsyncClient, auth_headers, tmp_path):
    """Test searching files in an index."""
    # Create some test files
    (tmp_path / "test.py").write_text("print('hello')")
    (tmp_path / "data.json").write_text("{}")

    # Create an index
    create_response = await client.post(
        "/api/v1/indexes",
        headers=auth_headers,
        json={"name": "Search Test", "root_path": str(tmp_path)},
    )
    index_id = create_response.json()["id"]

    # Search (note: files won't be there until indexing runs)
    response = await client.get(
        f"/api/v1/indexes/{index_id}/files",
        headers=auth_headers,
        params={"query": "test", "page": 1, "page_size": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_start_scan_job(client: AsyncClient, auth_headers, tmp_path):
    """Test starting an indexing scan job."""
    # Create an index
    create_response = await client.post(
        "/api/v1/indexes",
        headers=auth_headers,
        json={"name": "Scan Test", "root_path": str(tmp_path)},
    )
    index_id = create_response.json()["id"]

    # Start a scan
    response = await client.post(
        f"/api/v1/indexes/{index_id}/scan",
        headers=auth_headers,
        json={"job_type": "full_scan"},
    )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] in ["pending", "running"]
    assert data["index_id"] == index_id


@pytest.mark.asyncio
async def test_list_jobs(client: AsyncClient, auth_headers, tmp_path):
    """Test listing indexing jobs."""
    # Create an index and start a job
    create_response = await client.post(
        "/api/v1/indexes",
        headers=auth_headers,
        json={"name": "Jobs Test", "root_path": str(tmp_path)},
    )
    index_id = create_response.json()["id"]

    await client.post(
        f"/api/v1/indexes/{index_id}/scan",
        headers=auth_headers,
        json={"job_type": "full_scan"},
    )

    # List jobs
    response = await client.get(
        f"/api/v1/indexes/{index_id}/jobs",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
