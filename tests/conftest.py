"""Pytest configuration and fixtures for BookBytes tests.

This module provides reusable fixtures for:
- Async test client
- Test database session (in-memory SQLite)
- Mocked external services
- Settings overrides
- Authentication helpers
"""

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from bookbytes.config import Settings
from bookbytes.main import create_app


# =============================================================================
# Settings Fixtures
# =============================================================================


@pytest.fixture
def test_settings() -> Settings:
    """Create test-specific settings.

    Overrides production settings with test-appropriate values.
    """
    return Settings(
        app_env="development",  # type: ignore[arg-type]
        debug=True,
        log_level="DEBUG",  # type: ignore[arg-type]
        log_format="console",  # type: ignore[arg-type]
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/15",  # Use DB 15 for tests
        storage_backend="local",  # type: ignore[arg-type]
        local_storage_path="/tmp/bookbytes-test-audio",
        auth_mode="api_key",  # type: ignore[arg-type]
        api_key="test-api-key",  # type: ignore[arg-type]
        jwt_secret_key="test-jwt-secret-key",  # type: ignore[arg-type]
        openai_api_key="sk-test-key",  # type: ignore[arg-type]
    )


# =============================================================================
# Application Fixtures
# =============================================================================


@pytest.fixture
def app(test_settings: Settings) -> FastAPI:
    """Create a test FastAPI application with test settings."""
    return create_app(settings=test_settings)


@pytest.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing.

    This client makes requests to the test app without starting a server.

    Usage:
        async def test_endpoint(async_client: AsyncClient):
            response = await async_client.get("/health/live")
            assert response.status_code == 200
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
async def authenticated_client(
    app: FastAPI, test_settings: Settings
) -> AsyncGenerator[AsyncClient, None]:
    """Create an authenticated async client using API key.

    This client automatically includes the X-API-Key header.

    Usage:
        async def test_protected_endpoint(authenticated_client: AsyncClient):
            response = await authenticated_client.get("/api/v1/books")
            assert response.status_code == 200
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"X-API-Key": test_settings.api_key.get_secret_value()},
    ) as client:
        yield client


# =============================================================================
# Database Fixtures
# =============================================================================
# TODO: Implement in Phase 2 when database layer is ready


@pytest.fixture
async def test_db_session() -> AsyncGenerator[Any, None]:
    """Create an isolated test database session.

    This fixture will be implemented in Phase 2 when the database layer is ready.
    It will:
    - Create in-memory SQLite database
    - Run migrations
    - Yield a session
    - Rollback after test

    Usage:
        async def test_create_book(test_db_session: AsyncSession):
            book = Book(title="Test", author="Author")
            test_db_session.add(book)
            await test_db_session.commit()
    """
    # Placeholder - will be implemented in Phase 2
    yield None


# =============================================================================
# Mock Service Fixtures
# =============================================================================


@pytest.fixture
def mock_openai_service() -> MagicMock:
    """Create a mock OpenAI service.

    Use this to avoid making real API calls in tests.

    Usage:
        async def test_chapter_extraction(mock_openai_service: MagicMock):
            mock_openai_service.extract_chapters.return_value = [
                {"number": 1, "title": "Introduction"},
            ]
    """
    mock = MagicMock()
    mock.extract_chapters = AsyncMock(
        return_value=[
            {"number": 1, "title": "Introduction"},
            {"number": 2, "title": "Getting Started"},
        ]
    )
    mock.generate_summary = AsyncMock(
        return_value="This chapter introduces the main concepts."
    )
    return mock


@pytest.fixture
def mock_tts_service() -> MagicMock:
    """Create a mock TTS service.

    Use this to avoid generating real audio in tests.

    Usage:
        async def test_audio_generation(mock_tts_service: MagicMock):
            mock_tts_service.generate_audio.return_value = "/path/to/audio.mp3"
    """
    mock = MagicMock()
    mock.generate_audio = AsyncMock(return_value="/tmp/test-audio.mp3")
    return mock


@pytest.fixture
def mock_metadata_service() -> MagicMock:
    """Create a mock book metadata service.

    Use this to avoid making real Open Library API calls.
    """
    mock = MagicMock()
    mock.fetch_by_isbn = AsyncMock(
        return_value={
            "title": "Test Book",
            "author": "Test Author",
            "publisher": "Test Publisher",
            "publish_date": "2024",
            "pages": 200,
            "cover_url": "https://example.com/cover.jpg",
        }
    )
    return mock


@pytest.fixture
def mock_storage() -> MagicMock:
    """Create a mock storage backend.

    Use this to avoid file system or S3 operations in tests.
    """
    mock = MagicMock()
    mock.save = AsyncMock(return_value="test-audio-key")
    mock.get_url = AsyncMock(return_value="https://storage.example.com/test-audio.mp3")
    mock.delete = AsyncMock(return_value=True)
    mock.exists = AsyncMock(return_value=True)
    return mock


# =============================================================================
# Helper Fixtures
# =============================================================================


@pytest.fixture
def sample_isbn() -> str:
    """Return a sample ISBN for testing."""
    return "9780134685991"


@pytest.fixture
def sample_book_data() -> dict[str, Any]:
    """Return sample book data for testing."""
    return {
        "title": "Effective Python",
        "author": "Brett Slatkin",
        "language": "en",
        "publisher": "Addison-Wesley",
        "pages": 480,
        "publish_date": "2019",
        "cover_url": "https://covers.openlibrary.org/b/isbn/9780134685991-L.jpg",
    }


@pytest.fixture
def sample_chapter_data() -> list[dict[str, Any]]:
    """Return sample chapter data for testing."""
    return [
        {
            "chapter_number": 1,
            "title": "Pythonic Thinking",
            "summary": "This chapter covers Python idioms and best practices.",
            "word_count": 150,
        },
        {
            "chapter_number": 2,
            "title": "Lists and Dictionaries",
            "summary": "This chapter explores Python's built-in data structures.",
            "word_count": 180,
        },
    ]
