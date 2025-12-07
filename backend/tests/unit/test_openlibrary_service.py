"""Tests for OpenLibraryService.

Tests the OpenLibrary API client with mocked HTTP responses.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from bookbytes.services.openlibrary import (
    BookSearchResult,
    OpenLibraryError,
    OpenLibraryRateLimitError,
    OpenLibraryService,
    SearchResponse,
    WorkDetails,
)

# =============================================================================
# Mock Response Data
# =============================================================================

MOCK_SEARCH_RESPONSE = {
    "numFound": 2,
    "start": 0,
    "docs": [
        {
            "key": "/works/OL27448W",
            "title": "The Lord of the Rings",
            "author_name": ["J. R. R. Tolkien"],
            "author_key": ["OL26320A"],
            "first_publish_year": 1954,
            "edition_count": 120,
            "cover_i": 258027,
            "isbn": ["9780618640157", "0618640150"],
            "language": ["eng", "spa"],
            "publisher": ["Houghton Mifflin"],
            "subject": ["Fantasy", "Epic"],
        },
        {
            "key": "/works/OL12345W",
            "title": "The Hobbit",
            "author_name": ["J. R. R. Tolkien"],
            "first_publish_year": 1937,
            "edition_count": 50,
            "cover_i": None,
            "isbn": ["9780618968633"],
            "subject": ["Fantasy"],
        },
    ],
}

MOCK_WORK_RESPONSE = {
    "key": "/works/OL27448W",
    "title": "The Lord of the Rings",
    "description": "An epic fantasy novel.",
    "subjects": ["Fantasy", "Adventure", "Epic"],
    "covers": [258027, 258028],
}


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_cache() -> MagicMock:
    """Create a mock CacheService."""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=(None, False))  # Cache miss by default
    cache.set = AsyncMock(return_value=None)
    return cache


@pytest.fixture
def openlibrary_service(mock_cache: MagicMock) -> OpenLibraryService:
    """Create OpenLibraryService with mock cache."""
    return OpenLibraryService(mock_cache)


# =============================================================================
# DTO Tests
# =============================================================================


class TestBookSearchResult:
    """Tests for BookSearchResult DTO."""

    def test_to_dict(self) -> None:
        """Test serialization to dict."""
        result = BookSearchResult(
            title="Test Book",
            authors=["Author One", "Author Two"],
            first_publish_year=2020,
            cover_url="https://example.com/cover.jpg",
            isbn_list=["9781234567890"],
            edition_count=5,
            subjects=["Fiction"],
            external_work_key="/works/OL12345W",
        )

        data = result.to_dict()

        assert data["title"] == "Test Book"
        assert data["authors"] == ["Author One", "Author Two"]
        assert data["first_publish_year"] == 2020
        assert data["cover_url"] == "https://example.com/cover.jpg"
        assert data["isbn_list"] == ["9781234567890"]
        assert data["edition_count"] == 5
        assert data["subjects"] == ["Fiction"]
        assert data["external_work_key"] == "/works/OL12345W"
        assert data["source_provider"] == "openlibrary"
        assert "fetched_at" in data

    def test_from_dict(self) -> None:
        """Test deserialization from dict."""
        data = {
            "title": "Test Book",
            "authors": ["Author"],
            "first_publish_year": 2020,
            "cover_url": None,
            "isbn_list": [],
            "edition_count": 1,
            "subjects": [],
            "external_work_key": "/works/OL12345W",
            "source_provider": "openlibrary",
            "fetched_at": "2024-01-01T00:00:00",
        }

        result = BookSearchResult.from_dict(data)

        assert result.title == "Test Book"
        assert result.authors == ["Author"]
        assert result.first_publish_year == 2020
        assert result.external_work_key == "/works/OL12345W"


class TestWorkDetails:
    """Tests for WorkDetails DTO."""

    def test_to_dict_and_from_dict_roundtrip(self) -> None:
        """Test serialization roundtrip."""
        original = WorkDetails(
            title="Epic Novel",
            authors=["Famous Author"],
            description="A great book.",
            subjects=["Fiction", "Drama"],
            first_publish_year=1990,
            cover_url="https://example.com/cover.jpg",
            edition_count=10,
            isbn_list=["9781234567890", "1234567890"],
            external_work_key="/works/OL99999W",
        )

        data = original.to_dict()
        restored = WorkDetails.from_dict(data)

        assert restored.title == original.title
        assert restored.authors == original.authors
        assert restored.description == original.description
        assert restored.subjects == original.subjects
        assert restored.external_work_key == original.external_work_key


class TestSearchResponse:
    """Tests for SearchResponse container."""

    def test_has_more_true(self) -> None:
        """Test has_more when more results exist."""
        response = SearchResponse(
            results=[],
            total_found=100,
            offset=0,
            limit=10,
        )
        # At offset 0 with 10 results, 100 total -> has more
        response.results = [MagicMock()] * 10
        assert response.has_more is True

    def test_has_more_false(self) -> None:
        """Test has_more when no more results."""
        response = SearchResponse(
            results=[MagicMock()] * 5,
            total_found=5,
            offset=0,
            limit=10,
        )
        assert response.has_more is False


# =============================================================================
# Search Tests
# =============================================================================


class TestSearchBooks:
    """Tests for search_books method."""

    @pytest.mark.asyncio
    async def test_search_cache_hit(
        self, openlibrary_service: OpenLibraryService, mock_cache: MagicMock
    ) -> None:
        """Test that cached results are returned without API call."""
        cached_data = {
            "results": [
                {
                    "title": "Cached Book",
                    "authors": ["Author"],
                    "first_publish_year": 2020,
                    "cover_url": None,
                    "isbn_list": [],
                    "edition_count": 1,
                    "subjects": [],
                    "external_work_key": "/works/OL123W",
                    "source_provider": "openlibrary",
                    "fetched_at": "2024-01-01",
                }
            ],
            "total_found": 1,
            "offset": 0,
            "limit": 100,
        }
        mock_cache.get.return_value = (cached_data, False)

        result = await openlibrary_service.search_books(title="Cached Book")

        assert len(result.results) == 1
        assert result.results[0].title == "Cached Book"
        mock_cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_cache_miss_calls_api(
        self, openlibrary_service: OpenLibraryService, mock_cache: MagicMock
    ) -> None:
        """Test that API is called on cache miss."""
        mock_cache.get.return_value = (None, False)

        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_SEARCH_RESPONSE
        mock_response.raise_for_status = MagicMock()

        with patch.object(openlibrary_service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await openlibrary_service.search_books(title="Lord of the Rings")

            assert result.total_found == 2
            assert len(result.results) == 2
            assert result.results[0].title == "The Lord of the Rings"
            assert result.results[0].authors == ["J. R. R. Tolkien"]
            mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_with_all_parameters(
        self, openlibrary_service: OpenLibraryService, mock_cache: MagicMock
    ) -> None:
        """Test search with all optional parameters."""
        mock_cache.get.return_value = (None, False)

        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_SEARCH_RESPONSE
        mock_response.raise_for_status = MagicMock()

        with patch.object(openlibrary_service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_get_client.return_value = mock_client

            await openlibrary_service.search_books(
                title="Test",
                author="Author",
                publisher="Publisher",
                language="eng",
            )

            # Verify all params were passed
            call_args = mock_client.get.call_args
            params = call_args[1]["params"]
            assert "author" in params
            assert "publisher" in params
            assert "language" in params


# =============================================================================
# Work Details Tests
# =============================================================================


class TestGetWorkDetails:
    """Tests for get_work_details method."""

    @pytest.mark.asyncio
    async def test_get_work_details_cache_hit(
        self, openlibrary_service: OpenLibraryService, mock_cache: MagicMock
    ) -> None:
        """Test cached work details are returned."""
        cached_data = {
            "title": "Cached Work",
            "authors": [],
            "description": "Cached description",
            "subjects": [],
            "first_publish_year": None,
            "cover_url": None,
            "edition_count": 0,
            "isbn_list": [],
            "external_work_key": "/works/OL123W",
            "source_provider": "openlibrary",
            "fetched_at": "2024-01-01",
        }
        mock_cache.get.return_value = (cached_data, False)

        result = await openlibrary_service.get_work_details("/works/OL123W")

        assert result.title == "Cached Work"
        assert result.description == "Cached description"

    @pytest.mark.asyncio
    async def test_get_work_details_api_call(
        self, openlibrary_service: OpenLibraryService, mock_cache: MagicMock
    ) -> None:
        """Test API is called for uncached work."""
        mock_cache.get.return_value = (None, False)

        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_WORK_RESPONSE
        mock_response.raise_for_status = MagicMock()

        with patch.object(openlibrary_service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await openlibrary_service.get_work_details("/works/OL27448W")

            assert result.title == "The Lord of the Rings"
            assert result.description == "An epic fantasy novel."
            assert "Fantasy" in result.subjects
            mock_cache.set.assert_called_once()


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_rate_limit_error(
        self, openlibrary_service: OpenLibraryService, mock_cache: MagicMock
    ) -> None:
        """Test rate limit error is raised properly."""
        mock_cache.get.return_value = (None, False)

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Rate limited",
            request=MagicMock(),
            response=mock_response,
        )

        with patch.object(openlibrary_service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_get_client.return_value = mock_client

            with pytest.raises(OpenLibraryRateLimitError):
                await openlibrary_service.search_books(title="Test")

    @pytest.mark.asyncio
    async def test_api_error(
        self, openlibrary_service: OpenLibraryService, mock_cache: MagicMock
    ) -> None:
        """Test generic API error is raised."""
        mock_cache.get.return_value = (None, False)

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error",
            request=MagicMock(),
            response=mock_response,
        )

        with patch.object(openlibrary_service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_get_client.return_value = mock_client

            with pytest.raises(OpenLibraryError):
                await openlibrary_service.search_books(title="Test")

    @pytest.mark.asyncio
    async def test_network_error(
        self, openlibrary_service: OpenLibraryService, mock_cache: MagicMock
    ) -> None:
        """Test network error is handled."""
        mock_cache.get.return_value = (None, False)

        with patch.object(openlibrary_service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.RequestError(
                "Connection failed", request=MagicMock()
            )
            mock_get_client.return_value = mock_client

            with pytest.raises(OpenLibraryError):
                await openlibrary_service.search_books(title="Test")


# =============================================================================
# Helper Method Tests
# =============================================================================


class TestHelperMethods:
    """Tests for helper methods."""

    @pytest.mark.asyncio
    async def test_get_all_isbns_for_work(
        self, openlibrary_service: OpenLibraryService, mock_cache: MagicMock
    ) -> None:
        """Test ISBN collection delegates to get_work_details."""
        cached_data = {
            "title": "Test",
            "authors": [],
            "description": None,
            "subjects": [],
            "first_publish_year": None,
            "cover_url": None,
            "edition_count": 5,
            "isbn_list": ["9781234567890", "1234567890"],
            "external_work_key": "/works/OL123W",
            "source_provider": "openlibrary",
            "fetched_at": "2024-01-01",
        }
        mock_cache.get.return_value = (cached_data, False)

        isbns = await openlibrary_service.get_all_isbns_for_work("/works/OL123W")

        assert isbns == ["9781234567890", "1234567890"]

    def test_user_agent_format(self, openlibrary_service: OpenLibraryService) -> None:
        """Test User-Agent header format."""
        ua = openlibrary_service._user_agent

        assert "BookBytes" in ua
        assert "contact" in ua.lower() or "@" in ua


# =============================================================================
# Response Parsing Tests
# =============================================================================


class TestResponseParsing:
    """Tests for API response parsing."""

    def test_parse_search_response_with_cover(
        self, openlibrary_service: OpenLibraryService
    ) -> None:
        """Test search response parsing generates cover URL."""
        response = openlibrary_service._parse_search_response(MOCK_SEARCH_RESPONSE)

        assert response.results[0].cover_url is not None
        assert "258027" in response.results[0].cover_url

    def test_parse_search_response_without_cover(
        self, openlibrary_service: OpenLibraryService
    ) -> None:
        """Test search response parsing handles missing cover."""
        response = openlibrary_service._parse_search_response(MOCK_SEARCH_RESPONSE)

        # Second result has no cover
        assert response.results[1].cover_url is None

    def test_parse_work_response_dict_description(
        self, openlibrary_service: OpenLibraryService
    ) -> None:
        """Test work parsing handles dict description format."""
        work_data = {
            "title": "Test",
            "description": {"value": "Description from dict"},
            "subjects": [],
            "covers": [],
        }

        result = openlibrary_service._parse_work_response(work_data, "/works/OL123W")

        assert result.description == "Description from dict"
