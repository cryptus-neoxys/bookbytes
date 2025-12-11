"""Integration tests for search API endpoints.

These tests verify the endpoints work correctly with:
- Real database (SQLite in-memory for tests)
- Mocked OpenLibrary API (for predictable responses)

Run these tests with:
    pytest tests/integration/test_search_endpoints.py -v
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from bookbytes.api.v1.search import get_openlibrary_service
from bookbytes.services.cache import get_cache_service
from bookbytes.services.openlibrary import BookSearchResult, SearchResponse, WorkDetails

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_cache():
    """Create mock cache service."""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=(None, False))
    cache.set = AsyncMock(return_value=None)
    return cache


@pytest.fixture
def mock_openlibrary():
    """Create mock OpenLibrary service."""
    service = MagicMock()
    service.search_books = AsyncMock()
    service.get_work_details = AsyncMock()
    service.close = AsyncMock()
    return service


@pytest.fixture
def sample_search_result() -> BookSearchResult:
    """Create sample search result."""
    return BookSearchResult(
        title="The Lord of the Rings",
        authors=["J. R. R. Tolkien"],
        first_publish_year=1954,
        cover_url="https://covers.openlibrary.org/b/id/258027-M.jpg",
        isbn_list=["9780618640157", "0618640150"],
        edition_count=120,
        subjects=["Fantasy", "Epic"],
        external_work_key="/works/OL27448W",
    )


@pytest.fixture
def sample_work_details() -> WorkDetails:
    """Create sample work details."""
    return WorkDetails(
        title="The Lord of the Rings",
        authors=["J. R. R. Tolkien"],
        description="An epic fantasy novel about the quest to destroy the One Ring.",
        subjects=["Fantasy", "Adventure", "Epic"],
        first_publish_year=1954,
        cover_url="https://covers.openlibrary.org/b/id/258027-M.jpg",
        edition_count=120,
        isbn_list=["9780618640157"],
        external_work_key="/works/OL27448W",
    )


# =============================================================================
# Search Endpoint Integration Tests
# =============================================================================


class TestSearchEndpointIntegration:
    """Integration tests for POST /api/v1/books/search."""

    @pytest.mark.asyncio
    async def test_search_returns_200_with_results(
        self,
        app,
        async_client: AsyncClient,
        mock_cache,
        mock_openlibrary,
        sample_search_result: BookSearchResult,
    ) -> None:
        """Test search endpoint returns 200 with results."""
        mock_openlibrary.search_books.return_value = SearchResponse(
            results=[sample_search_result],
            total_found=1,
            offset=0,
            limit=100,
        )

        app.dependency_overrides[get_cache_service] = lambda: mock_cache
        app.dependency_overrides[get_openlibrary_service] = lambda: mock_openlibrary

        response = await async_client.post(
            "/api/v1/books/search",
            json={"title": "Lord of the Rings"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_found"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["title"] == "The Lord of the Rings"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_search_validates_request_body(
        self,
        app,
        async_client: AsyncClient,
        mock_cache,
        mock_openlibrary,
    ) -> None:
        """Test search validates request body."""
        app.dependency_overrides[get_cache_service] = lambda: mock_cache
        app.dependency_overrides[get_openlibrary_service] = lambda: mock_openlibrary

        # Missing title
        response = await async_client.post(
            "/api/v1/books/search",
            json={},
        )

        assert response.status_code == 422

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_search_with_pagination(
        self,
        app,
        async_client: AsyncClient,
        mock_cache,
        mock_openlibrary,
        sample_search_result: BookSearchResult,
    ) -> None:
        """Test search with pagination parameters."""
        mock_openlibrary.search_books.return_value = SearchResponse(
            results=[sample_search_result] * 30,
            total_found=100,
            offset=0,
            limit=100,
        )

        app.dependency_overrides[get_cache_service] = lambda: mock_cache
        app.dependency_overrides[get_openlibrary_service] = lambda: mock_openlibrary

        response = await async_client.post(
            "/api/v1/books/search?page=2&page_size=10",
            json={"title": "Test"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 10
        assert data["has_more"] is True

        app.dependency_overrides.clear()


# =============================================================================
# Work Details Endpoint Integration Tests
# =============================================================================


class TestWorkDetailsEndpointIntegration:
    """Integration tests for GET /api/v1/books/works/{work_key}."""

    @pytest.mark.asyncio
    async def test_get_work_returns_200(
        self,
        app,
        async_client: AsyncClient,
        mock_cache,
        mock_openlibrary,
        sample_work_details: WorkDetails,
    ) -> None:
        """Test get work details returns 200."""
        mock_openlibrary.get_work_details.return_value = sample_work_details

        app.dependency_overrides[get_cache_service] = lambda: mock_cache
        app.dependency_overrides[get_openlibrary_service] = lambda: mock_openlibrary

        response = await async_client.get("/api/v1/books/works/works/OL27448W")

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "The Lord of the Rings"
        assert data["description"] is not None
        assert any("Tolkien" in author for author in data["authors"])

        app.dependency_overrides.clear()


# =============================================================================
# ISBN Lookup Endpoint Integration Tests
# =============================================================================


class TestISBNLookupEndpointIntegration:
    """Integration tests for GET /api/v1/books/isbn/{isbn}."""

    @pytest.mark.asyncio
    async def test_isbn_lookup_returns_200(
        self,
        app,
        async_client: AsyncClient,
        mock_cache,
        mock_openlibrary,
        sample_search_result: BookSearchResult,
        sample_work_details: WorkDetails,
    ) -> None:
        """Test ISBN lookup returns 200 with book details."""
        mock_openlibrary.search_books.return_value = SearchResponse(
            results=[sample_search_result],
            total_found=1,
            offset=0,
            limit=100,
        )
        mock_openlibrary.get_work_details.return_value = sample_work_details

        app.dependency_overrides[get_cache_service] = lambda: mock_cache
        app.dependency_overrides[get_openlibrary_service] = lambda: mock_openlibrary

        response = await async_client.get("/api/v1/books/isbn/9780618640157")

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "The Lord of the Rings"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_isbn_lookup_not_found_returns_404(
        self,
        app,
        async_client: AsyncClient,
        mock_cache,
        mock_openlibrary,
    ) -> None:
        """Test ISBN not found returns 404."""
        mock_openlibrary.search_books.return_value = SearchResponse(
            results=[],
            total_found=0,
            offset=0,
            limit=100,
        )

        app.dependency_overrides[get_cache_service] = lambda: mock_cache
        app.dependency_overrides[get_openlibrary_service] = lambda: mock_openlibrary

        response = await async_client.get("/api/v1/books/isbn/0000000000000")

        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "BOOK_NOT_FOUND"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_isbn_with_dashes_is_handled(
        self,
        app,
        async_client: AsyncClient,
        mock_cache,
        mock_openlibrary,
        sample_search_result: BookSearchResult,
        sample_work_details: WorkDetails,
    ) -> None:
        """Test ISBN with dashes is normalized and handled."""
        mock_openlibrary.search_books.return_value = SearchResponse(
            results=[sample_search_result],
            total_found=1,
            offset=0,
            limit=100,
        )
        mock_openlibrary.get_work_details.return_value = sample_work_details

        app.dependency_overrides[get_cache_service] = lambda: mock_cache
        app.dependency_overrides[get_openlibrary_service] = lambda: mock_openlibrary

        response = await async_client.get("/api/v1/books/isbn/978-0-618-64015-7")

        assert response.status_code == 200

        app.dependency_overrides.clear()


# =============================================================================
# Request Headers Integration Tests
# =============================================================================


class TestRequestHeadersIntegration:
    """Integration tests for request headers."""

    @pytest.mark.asyncio
    async def test_request_id_header_returned(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test X-Request-ID header is returned in response."""
        response = await async_client.get("/health/live")

        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

    @pytest.mark.asyncio
    async def test_custom_request_id_preserved(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test custom X-Request-ID is preserved."""
        custom_id = "my-custom-request-id-123"

        response = await async_client.get(
            "/health/live",
            headers={"X-Request-ID": custom_id},
        )

        assert response.headers["X-Request-ID"] == custom_id
