"""Tests for search API endpoints.

Tests the /api/v1/books/search, /works, and /isbn endpoints.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from bookbytes.api.v1.search import get_openlibrary_service
from bookbytes.main import create_app
from bookbytes.services.cache import get_cache_service
from bookbytes.services.openlibrary import BookSearchResult, SearchResponse, WorkDetails

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_cache_service():
    """Create a mock CacheService."""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=(None, False))
    cache.set = AsyncMock(return_value=None)
    return cache


@pytest.fixture
def mock_openlibrary_service():
    """Create a mock OpenLibraryService."""
    service = MagicMock()
    service.search_books = AsyncMock()
    service.get_work_details = AsyncMock()
    service.close = AsyncMock()
    return service


@pytest.fixture
def sample_search_result() -> BookSearchResult:
    """Create a sample search result."""
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
        description="An epic fantasy novel.",
        subjects=["Fantasy", "Adventure"],
        first_publish_year=1954,
        cover_url="https://covers.openlibrary.org/b/id/258027-M.jpg",
        edition_count=120,
        isbn_list=["9780618640157"],
        external_work_key="/works/OL27448W",
    )


@pytest.fixture
def test_app(mock_cache_service, mock_openlibrary_service):
    """Create app with mocked dependencies."""
    app = create_app()

    # Override dependencies
    app.dependency_overrides[get_cache_service] = lambda: mock_cache_service
    app.dependency_overrides[get_openlibrary_service] = lambda: mock_openlibrary_service

    yield app

    # Cleanup
    app.dependency_overrides.clear()


# =============================================================================
# Search Endpoint Tests
# =============================================================================


class TestSearchBooksEndpoint:
    """Tests for POST /api/v1/books/search."""

    @pytest.mark.asyncio
    async def test_search_returns_results(
        self,
        test_app,
        mock_openlibrary_service: MagicMock,
        sample_search_result: BookSearchResult,
    ) -> None:
        """Test successful search returns results."""
        mock_openlibrary_service.search_books.return_value = SearchResponse(
            results=[sample_search_result],
            total_found=1,
            offset=0,
            limit=100,
        )

        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/v1/books/search",
                json={"title": "Lord of the Rings"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total_found"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["title"] == "The Lord of the Rings"
        assert data["results"][0]["authors"] == ["J. R. R. Tolkien"]

    @pytest.mark.asyncio
    async def test_search_with_pagination(
        self,
        test_app,
        mock_openlibrary_service: MagicMock,
        sample_search_result: BookSearchResult,
    ) -> None:
        """Test search with pagination parameters."""
        mock_openlibrary_service.search_books.return_value = SearchResponse(
            results=[sample_search_result] * 50,
            total_found=100,
            offset=0,
            limit=100,
        )

        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/v1/books/search?page=1&page_size=10",
                json={"title": "Test"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert len(data["results"]) <= 10
        assert data["has_more"] is True

    @pytest.mark.asyncio
    async def test_search_with_all_filters(
        self,
        test_app,
        mock_openlibrary_service: MagicMock,
        sample_search_result: BookSearchResult,
    ) -> None:
        """Test search with all filter parameters."""
        mock_openlibrary_service.search_books.return_value = SearchResponse(
            results=[sample_search_result],
            total_found=1,
            offset=0,
            limit=100,
        )

        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/v1/books/search",
                json={
                    "title": "Lord of the Rings",
                    "author": "Tolkien",
                    "publisher": "Houghton",
                    "language": "eng",
                },
            )

        assert response.status_code == 200
        # Verify service was called with filters
        mock_openlibrary_service.search_books.assert_called_once()
        call_kwargs = mock_openlibrary_service.search_books.call_args.kwargs
        assert call_kwargs["author"] == "Tolkien"
        assert call_kwargs["publisher"] == "Houghton"
        assert call_kwargs["language"] == "eng"

    @pytest.mark.asyncio
    async def test_search_empty_title_returns_422(
        self,
        test_app,
    ) -> None:
        """Test search with empty title returns validation error."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/v1/books/search",
                json={"title": ""},
            )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_search_no_results(
        self,
        test_app,
        mock_openlibrary_service: MagicMock,
    ) -> None:
        """Test search with no results."""
        mock_openlibrary_service.search_books.return_value = SearchResponse(
            results=[],
            total_found=0,
            offset=0,
            limit=100,
        )

        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/v1/books/search",
                json={"title": "nonexistentbook12345"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total_found"] == 0
        assert data["results"] == []


# =============================================================================
# Work Details Endpoint Tests
# =============================================================================


class TestGetWorkDetailsEndpoint:
    """Tests for GET /api/v1/books/works/{work_key}."""

    @pytest.mark.asyncio
    async def test_get_work_details_success(
        self,
        test_app,
        mock_openlibrary_service: MagicMock,
        sample_work_details: WorkDetails,
    ) -> None:
        """Test successful work details fetch."""
        mock_openlibrary_service.get_work_details.return_value = sample_work_details

        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/v1/books/works/works/OL27448W")

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "The Lord of the Rings"
        assert data["description"] == "An epic fantasy novel."
        assert data["external_work_key"] == "/works/OL27448W"


# =============================================================================
# ISBN Lookup Endpoint Tests
# =============================================================================


class TestLookupByISBNEndpoint:
    """Tests for GET /api/v1/books/isbn/{isbn}."""

    @pytest.mark.asyncio
    async def test_isbn_lookup_success(
        self,
        test_app,
        mock_openlibrary_service: MagicMock,
        sample_search_result: BookSearchResult,
        sample_work_details: WorkDetails,
    ) -> None:
        """Test successful ISBN lookup."""
        mock_openlibrary_service.search_books.return_value = SearchResponse(
            results=[sample_search_result],
            total_found=1,
            offset=0,
            limit=100,
        )
        mock_openlibrary_service.get_work_details.return_value = sample_work_details

        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/v1/books/isbn/9780618640157")

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "The Lord of the Rings"

    @pytest.mark.asyncio
    async def test_isbn_not_found_returns_404(
        self,
        test_app,
        mock_openlibrary_service: MagicMock,
    ) -> None:
        """Test ISBN not found returns 404."""
        mock_openlibrary_service.search_books.return_value = SearchResponse(
            results=[],
            total_found=0,
            offset=0,
            limit=100,
        )

        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/v1/books/isbn/0000000000000")

        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "BOOK_NOT_FOUND"
