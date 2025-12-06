"""Tests for health check endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_liveness_probe(async_client: AsyncClient) -> None:
    """Test that liveness probe returns OK."""
    response = await async_client.get("/health/live")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_readiness_probe(async_client: AsyncClient) -> None:
    """Test that readiness probe returns OK with checks."""
    response = await async_client.get("/health/ready")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "checks" in data


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient) -> None:
    """Test that root endpoint returns service info."""
    response = await async_client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "BookBytes"
    assert "version" in data
    assert data["docs"] == "/docs"
    assert data["health"] == "/health/live"


@pytest.mark.asyncio
async def test_request_id_header(async_client: AsyncClient) -> None:
    """Test that response includes X-Request-ID header."""
    response = await async_client.get("/health/live")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers


@pytest.mark.asyncio
async def test_custom_request_id(async_client: AsyncClient) -> None:
    """Test that custom X-Request-ID is echoed back."""
    custom_id = "test-request-id-12345"
    response = await async_client.get(
        "/health/live", headers={"X-Request-ID": custom_id}
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id
