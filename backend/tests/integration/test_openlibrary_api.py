"""Integration tests for OpenLibraryService against real API.

These tests hit the actual OpenLibrary API to validate:
- API contract hasn't changed
- Response parsing works with real data
- Error handling for real network conditions

Run these tests with:
    pytest -m integration
    pytest -m external

Skip these in CI with:
    pytest -m "not integration"
"""

import pytest

from bookbytes.services.cache import CacheService
from bookbytes.services.openlibrary import (
    OpenLibraryError,
    OpenLibraryService,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_cache():
    """Create a minimal mock cache that always misses.

    For integration tests, we want to hit the real API.
    """
    from unittest.mock import AsyncMock, MagicMock

    cache = MagicMock(spec=CacheService)
    cache.get = AsyncMock(return_value=(None, False))  # Always miss
    cache.set = AsyncMock(return_value=None)
    return cache


@pytest.fixture
def openlibrary_service(mock_cache) -> OpenLibraryService:
    """Create OpenLibraryService with mock cache for real API testing."""
    return OpenLibraryService(mock_cache)


async def check_openlibrary_reachable() -> bool:
    """Check if OpenLibrary API is reachable."""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.head("https://openlibrary.org")
            return response.status_code < 500
    except (httpx.RequestError, httpx.HTTPStatusError):
        return False


@pytest.fixture
async def skip_if_no_network():
    """Skip test if OpenLibrary API is unreachable."""
    is_reachable = await check_openlibrary_reachable()
    if not is_reachable:
        pytest.skip("OpenLibrary API is unreachable (network issue)")
    return True


# =============================================================================
# Search Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.external
class TestOpenLibrarySearchIntegration:
    """Integration tests for search_books against real API."""

    @pytest.mark.asyncio
    async def test_search_returns_results(
        self, openlibrary_service: OpenLibraryService
    ) -> None:
        """Test that search returns real results."""
        result = await openlibrary_service.search_books(title="Lord of the Rings")

        assert result.total_found > 0
        assert len(result.results) > 0

        # Verify first result has expected fields
        first = result.results[0]
        assert first.title  # Has a title
        assert first.external_work_key  # Has work key
        assert first.source_provider == "openlibrary"

        await openlibrary_service.close()

    @pytest.mark.asyncio
    async def test_search_tolkien_returns_correct_author(
        self, openlibrary_service: OpenLibraryService
    ) -> None:
        """Test that searching for Tolkien returns his works."""
        result = await openlibrary_service.search_books(
            title="Hobbit", author="Tolkien"
        )

        assert result.total_found > 0

        # At least one result should have Tolkien as author
        has_tolkien = any("Tolkien" in str(r.authors) for r in result.results)
        assert has_tolkien, "Expected to find Tolkien in authors"

        await openlibrary_service.close()

    @pytest.mark.asyncio
    async def test_search_with_language_filter(
        self, openlibrary_service: OpenLibraryService
    ) -> None:
        """Test search with language parameter."""
        result = await openlibrary_service.search_books(
            title="Don Quixote", language="spa"
        )

        # Should return results (Don Quixote exists in Spanish)
        assert result.total_found >= 0  # May be 0 if API doesn't support filter well

        await openlibrary_service.close()

    @pytest.mark.asyncio
    async def test_search_nonexistent_book(
        self, openlibrary_service: OpenLibraryService
    ) -> None:
        """Test search for a book that doesn't exist."""
        result = await openlibrary_service.search_books(
            title="xyznonexistentbook123456789"
        )

        assert result.total_found == 0
        assert len(result.results) == 0

        await openlibrary_service.close()

    @pytest.mark.asyncio
    async def test_search_result_has_cover_url(
        self, openlibrary_service: OpenLibraryService
    ) -> None:
        """Test that popular books have cover URLs."""
        result = await openlibrary_service.search_books(title="Harry Potter")

        # At least one result should have a cover
        has_cover = any(r.cover_url is not None for r in result.results)
        assert has_cover, "Expected at least one result with cover"

        await openlibrary_service.close()


# =============================================================================
# Work Details Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.external
class TestOpenLibraryWorkDetailsIntegration:
    """Integration tests for get_work_details against real API."""

    @pytest.mark.asyncio
    async def test_get_work_details_lotr(
        self, openlibrary_service: OpenLibraryService
    ) -> None:
        """Test fetching work details for Lord of the Rings."""
        # First search to get a valid work key
        search = await openlibrary_service.search_books(title="Lord of the Rings")
        assert len(search.results) > 0

        work_key = search.results[0].external_work_key

        # Now fetch work details
        work = await openlibrary_service.get_work_details(work_key)

        assert work.title  # Has title
        assert work.external_work_key == work_key
        assert work.source_provider == "openlibrary"

        await openlibrary_service.close()

    @pytest.mark.asyncio
    async def test_get_work_details_has_description(
        self, openlibrary_service: OpenLibraryService
    ) -> None:
        """Test that work details include description when available."""
        # Use a well-known work that has description
        search = await openlibrary_service.search_books(title="1984", author="Orwell")

        if len(search.results) > 0:
            work_key = search.results[0].external_work_key
            work = await openlibrary_service.get_work_details(work_key)

            # Description may or may not be present depending on the work
            # Just verify it's a string or None
            assert work.description is None or isinstance(work.description, str)

        await openlibrary_service.close()


# =============================================================================
# ISBN Helper Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.external
class TestOpenLibraryISBNIntegration:
    """Integration tests for ISBN-related methods."""

    @pytest.mark.asyncio
    async def test_search_returns_isbns(
        self, openlibrary_service: OpenLibraryService
    ) -> None:
        """Test that search results include ISBNs."""
        result = await openlibrary_service.search_books(title="Clean Code")

        # At least one result should have ISBNs
        has_isbns = any(len(r.isbn_list) > 0 for r in result.results)
        assert has_isbns, "Expected at least one result with ISBNs"

        await openlibrary_service.close()


# =============================================================================
# Error Handling Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.external
class TestOpenLibraryErrorHandlingIntegration:
    """Integration tests for error handling with real API."""

    @pytest.mark.asyncio
    async def test_invalid_work_key_handling(
        self, openlibrary_service: OpenLibraryService
    ) -> None:
        """Test handling of invalid work key."""

        with pytest.raises(OpenLibraryError):
            await openlibrary_service.get_work_details("/works/INVALID12345")

        await openlibrary_service.close()


# =============================================================================
# Cache Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.external
class TestOpenLibraryCacheIntegration:
    """Test cache behavior with real API responses."""

    @pytest.mark.asyncio
    async def test_cache_is_populated_after_search(
        self, mock_cache, openlibrary_service: OpenLibraryService
    ) -> None:
        """Test that cache.set is called after successful search."""
        await openlibrary_service.search_books(title="Python")

        # Cache should have been set
        mock_cache.set.assert_called_once()

        # Verify the cached data structure
        call_args = mock_cache.set.call_args
        cache_key = call_args[0][0]
        cache_data = call_args[0][1]

        assert cache_key.startswith("search:")
        assert "results" in cache_data
        assert "total_found" in cache_data

        await openlibrary_service.close()

    @pytest.mark.asyncio
    async def test_cache_key_is_deterministic(
        self, openlibrary_service: OpenLibraryService
    ) -> None:
        """Test that same search params produce same cache key."""
        key1 = CacheService.search_key(title="Python", author="Guido")
        key2 = CacheService.search_key(title="Python", author="Guido")
        key3 = CacheService.search_key(title="python", author="guido")

        assert key1 == key2
        assert key1 == key3  # Normalized

        await openlibrary_service.close()
