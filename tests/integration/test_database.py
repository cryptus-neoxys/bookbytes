"""Tests for database infrastructure."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_ready_checks_database(async_client: AsyncClient) -> None:
    """Test that /health/ready checks database connectivity."""
    response = await async_client.get("/health/ready")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "database" in data["checks"]


@pytest.mark.asyncio
async def test_database_session_lifecycle() -> None:
    """Test that database session can be created and closed."""
    from bookbytes.config import Settings
    from bookbytes.core.database import close_db, get_async_session, init_db

    # Create test settings with SQLite
    settings = Settings(
        app_env="development",  # type: ignore[arg-type]
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/15",
        storage_backend="local",  # type: ignore[arg-type]
        local_storage_path="/tmp/test",
        auth_mode="api_key",  # type: ignore[arg-type]
        api_key="test-key",  # type: ignore[arg-type]
        jwt_secret_key="test-secret",  # type: ignore[arg-type]
        openai_api_key="sk-test",  # type: ignore[arg-type]
    )

    # Initialize database
    await init_db(settings)

    # Get a session and verify it works
    from sqlalchemy import text

    async for session in get_async_session():
        assert session is not None
        # Simple query to verify connection
        result = await session.execute(text("SELECT 1"))
        value = result.scalar()
        assert value == 1

    # Close database
    await close_db()


@pytest.mark.asyncio
async def test_base_model_has_expected_mixins() -> None:
    """Test that Base and mixins are properly defined."""
    from bookbytes.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

    # Verify Base exists
    assert Base is not None

    # Verify mixins have expected attributes
    assert hasattr(UUIDPrimaryKeyMixin, "id")
    assert hasattr(TimestampMixin, "created_at")
    assert hasattr(TimestampMixin, "updated_at")
