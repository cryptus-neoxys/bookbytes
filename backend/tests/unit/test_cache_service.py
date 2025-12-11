"""Tests for CacheService.

Tests the Redis caching layer with TTL jitter, stale-while-revalidate,
and cache key generation.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from bookbytes.services.cache import CacheService

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_redis() -> MagicMock:
    """Create a mock Redis client."""
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.ttl = AsyncMock(return_value=3600)
    redis.scan_iter = MagicMock(return_value=iter([]))
    return redis


@pytest.fixture
def cache_service(mock_redis: MagicMock) -> CacheService:
    """Create CacheService with mock Redis."""
    return CacheService(mock_redis)


# =============================================================================
# Cache Key Generation Tests
# =============================================================================


class TestCacheKeyGeneration:
    """Tests for static cache key generation methods."""

    def test_search_key_basic(self) -> None:
        """Test basic search key generation."""
        key = CacheService.search_key(title="Lord of the Rings")
        assert key.startswith("search:")
        assert len(key) == len("search:") + 16  # 16-char hash

    def test_search_key_normalized(self) -> None:
        """Test that search keys are normalized (lowercase, trimmed)."""
        key1 = CacheService.search_key(title="Lord of the Rings")
        key2 = CacheService.search_key(title="  LORD OF THE RINGS  ")
        assert key1 == key2

    def test_search_key_with_author(self) -> None:
        """Test search key with author."""
        key1 = CacheService.search_key(title="Lord of the Rings")
        key2 = CacheService.search_key(title="Lord of the Rings", author="Tolkien")
        assert key1 != key2

    def test_search_key_deterministic(self) -> None:
        """Test that same inputs always produce same key."""
        key1 = CacheService.search_key(
            title="Test", author="Author", publisher="Pub", language="eng"
        )
        key2 = CacheService.search_key(
            title="Test", author="Author", publisher="Pub", language="eng"
        )
        assert key1 == key2

    def test_isbn_key(self) -> None:
        """Test ISBN key generation."""
        key = CacheService.isbn_key("9780618640157")
        assert key == "isbn:9780618640157"

    def test_work_key(self) -> None:
        """Test work key generation."""
        key = CacheService.work_key("/works/OL27448W")
        assert key == "work:/works/OL27448W"


# =============================================================================
# TTL Tests
# =============================================================================


class TestTTLHandling:
    """Tests for TTL jitter and original TTL detection."""

    def test_jitter_ttl_within_range(self, cache_service: CacheService) -> None:
        """Test that jittered TTL is within ±10% of base."""
        base_ttl = 86400  # 24 hours

        # Run multiple times to test randomness
        for _ in range(100):
            jittered = cache_service._jitter_ttl(base_ttl)
            # Should be within ±10%
            assert base_ttl * 0.89 <= jittered <= base_ttl * 1.11

    def test_jitter_ttl_minimum(self, cache_service: CacheService) -> None:
        """Test that jittered TTL is at least 1."""
        jittered = cache_service._jitter_ttl(1)
        assert jittered >= 1

    def test_get_original_ttl_search(self, cache_service: CacheService) -> None:
        """Test TTL detection for search keys."""
        ttl = cache_service._get_original_ttl("search:abc123")
        assert ttl == CacheService.TTL_SEARCH_RESULTS

    def test_get_original_ttl_work(self, cache_service: CacheService) -> None:
        """Test TTL detection for work keys."""
        ttl = cache_service._get_original_ttl("work:/works/OL27448W")
        assert ttl == CacheService.TTL_WORK_DETAILS

    def test_get_original_ttl_isbn(self, cache_service: CacheService) -> None:
        """Test TTL detection for ISBN keys."""
        ttl = cache_service._get_original_ttl("isbn:9780618640157")
        assert ttl == CacheService.TTL_ISBN_DETAILS

    def test_get_original_ttl_unknown_defaults(
        self, cache_service: CacheService
    ) -> None:
        """Test that unknown keys default to search TTL."""
        ttl = cache_service._get_original_ttl("unknown:key")
        assert ttl == CacheService.TTL_SEARCH_RESULTS


# =============================================================================
# Cache Get Tests
# =============================================================================


class TestCacheGet:
    """Tests for cache get operation."""

    @pytest.mark.asyncio
    async def test_get_miss_returns_none(
        self, cache_service: CacheService, mock_redis: MagicMock
    ) -> None:
        """Test cache miss returns (None, False)."""
        mock_redis.get.return_value = None

        data, needs_revalidation = await cache_service.get("search:abc123")

        assert data is None
        assert needs_revalidation is False
        mock_redis.get.assert_called_once_with("search:abc123")

    @pytest.mark.asyncio
    async def test_get_hit_returns_data(
        self, cache_service: CacheService, mock_redis: MagicMock
    ) -> None:
        """Test cache hit returns parsed data."""
        cached_data = {"title": "Test Book", "authors": ["Author"]}
        mock_redis.get.return_value = json.dumps(cached_data)
        mock_redis.ttl.return_value = 50000  # Lots of TTL remaining

        data, needs_revalidation = await cache_service.get("search:abc123")

        assert data == cached_data
        assert needs_revalidation is False

    @pytest.mark.asyncio
    async def test_get_stale_needs_revalidation(
        self, cache_service: CacheService, mock_redis: MagicMock
    ) -> None:
        """Test that near-expiry data triggers revalidation flag."""
        cached_data = {"title": "Test Book"}
        mock_redis.get.return_value = json.dumps(cached_data)
        # TTL is 10% of original (below 20% threshold)
        mock_redis.ttl.return_value = int(CacheService.TTL_SEARCH_RESULTS * 0.1)

        data, needs_revalidation = await cache_service.get("search:abc123")

        assert data == cached_data
        assert needs_revalidation is True

    @pytest.mark.asyncio
    async def test_get_handles_redis_error(
        self, cache_service: CacheService, mock_redis: MagicMock
    ) -> None:
        """Test that Redis errors return None without raising."""
        mock_redis.get.side_effect = Exception("Redis connection error")

        data, needs_revalidation = await cache_service.get("search:abc123")

        assert data is None
        assert needs_revalidation is False


# =============================================================================
# Cache Set Tests
# =============================================================================


class TestCacheSet:
    """Tests for cache set operation."""

    @pytest.mark.asyncio
    async def test_set_stores_data(
        self, cache_service: CacheService, mock_redis: MagicMock
    ) -> None:
        """Test that set stores JSON-serialized data."""
        data = {"title": "Test Book", "authors": ["Author"]}

        await cache_service.set("search:abc123", data)

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "search:abc123"
        assert json.loads(call_args[0][2]) == data

    @pytest.mark.asyncio
    async def test_set_with_custom_ttl(
        self, cache_service: CacheService, mock_redis: MagicMock
    ) -> None:
        """Test that custom TTL is applied with jitter."""
        await cache_service.set("search:abc123", {"data": "test"}, base_ttl=3600)

        call_args = mock_redis.setex.call_args
        ttl_used = call_args[0][1]
        # Should be within ±10% of 3600
        assert 3600 * 0.89 <= ttl_used <= 3600 * 1.11

    @pytest.mark.asyncio
    async def test_set_handles_redis_error(
        self, cache_service: CacheService, mock_redis: MagicMock
    ) -> None:
        """Test that Redis errors don't raise."""
        mock_redis.setex.side_effect = Exception("Redis error")

        # Should not raise
        await cache_service.set("search:abc123", {"data": "test"})


# =============================================================================
# Cache Invalidation Tests
# =============================================================================


class TestCacheInvalidation:
    """Tests for cache invalidation."""

    @pytest.mark.asyncio
    async def test_invalidate_single_key(
        self, cache_service: CacheService, mock_redis: MagicMock
    ) -> None:
        """Test single key invalidation."""
        await cache_service.invalidate("search:abc123")

        mock_redis.delete.assert_called_once_with("search:abc123")

    @pytest.mark.asyncio
    async def test_invalidate_pattern(
        self, cache_service: CacheService, mock_redis: MagicMock
    ) -> None:
        """Test pattern-based invalidation."""
        # Mock scan_iter to return some keys
        mock_keys = [b"search:key1", b"search:key2", b"search:key3"]

        async def mock_scan_iter(match: str):
            for key in mock_keys:
                yield key

        mock_redis.scan_iter = mock_scan_iter

        count = await cache_service.invalidate_pattern("search:*")

        assert count == 3
        assert mock_redis.delete.call_count == 3

    @pytest.mark.asyncio
    async def test_invalidate_handles_error(
        self, cache_service: CacheService, mock_redis: MagicMock
    ) -> None:
        """Test that invalidation errors don't raise."""
        mock_redis.delete.side_effect = Exception("Redis error")

        # Should not raise
        await cache_service.invalidate("search:abc123")
