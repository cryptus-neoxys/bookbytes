"""CacheService - Redis-only caching with TTL and stale-while-revalidate.

This service provides a simple, effective caching layer using Redis with:
- TTL-based expiration with jitter to prevent stampede
- Stale-while-revalidate for better UX
- Pattern-based invalidation

Redis is configured with AOF persistence (appendfsync everysec) for durability.
Search results are transient - if lost, users simply re-search. Important data
(processed books) is stored permanently in PostgreSQL Work/Edition tables.

Cache Key Types:
    - search:{hash} - Search results (24h TTL)
    - isbn:{isbn} - Book details by ISBN (7d TTL)
    - work:{identifier} - Work details (7d TTL)

Note: Using canonical data model approach - cache internal representations,
not raw API responses. Provider metadata stored in cached value, not key.
See: tasks/knowledge/multi-provider-integration-patterns.md
"""

import hashlib
import json
import random
from typing import Any

import structlog
from redis.asyncio import Redis

logger = structlog.get_logger(__name__)


class CacheService:
    """Redis-only caching with TTL and stale-while-revalidate.

    Configuration:
        Redis should be configured with:
        - appendonly yes
        - appendfsync everysec
        - maxmemory 256mb
        - maxmemory-policy allkeys-lru

    Usage with FastAPI:
        ```python
        from bookbytes.services.cache import CacheService, get_cache_service

        @router.get("/search")
        async def search(cache: CacheService = Depends(get_cache_service)):
            ...
        ```
    """

    # TTL constants (in seconds)
    TTL_SEARCH_RESULTS = 86400  # 24 hours
    TTL_WORK_DETAILS = 604800  # 7 days
    TTL_ISBN_DETAILS = 604800  # 7 days

    # Stale-while-revalidate threshold
    REVALIDATE_THRESHOLD = 0.2  # Trigger refresh at 20% TTL remaining

    def __init__(self, redis: Redis) -> None:
        """Initialize the cache service.

        Args:
            redis: Async Redis client
        """
        self.redis = redis

    async def get(self, cache_key: str) -> tuple[dict | None, bool]:
        """Get from cache with stale-while-revalidate support.

        Returns:
            Tuple of (data, needs_revalidation).
            - data: Cached data or None if not found
            - needs_revalidation: True if data is stale and should be refreshed
        """
        try:
            result = await self.redis.get(cache_key)
            if not result:
                return None, False

            ttl = await self.redis.ttl(cache_key)
            original_ttl = self._get_original_ttl(cache_key)

            # Check if near expiry (stale-while-revalidate)
            if ttl > 0 and original_ttl > 0:
                needs_revalidation = (ttl / original_ttl) < self.REVALIDATE_THRESHOLD
            else:
                needs_revalidation = False

            data = json.loads(result)
            return data, needs_revalidation

        except Exception as e:
            logger.warning("cache_get_failed", cache_key=cache_key, error=str(e))
            return None, False

    async def set(
        self,
        cache_key: str,
        data: dict[str, Any],
        base_ttl: int | None = None,
    ) -> None:
        """Store in Redis with jittered TTL.

        Args:
            cache_key: Cache key
            data: Data to cache (must be JSON-serializable)
            base_ttl: Base TTL in seconds (auto-detected from key prefix if None)
        """
        try:
            if base_ttl is None:
                base_ttl = self._get_original_ttl(cache_key)

            ttl = self._jitter_ttl(base_ttl)
            await self.redis.setex(cache_key, ttl, json.dumps(data))
            logger.debug("cache_set", cache_key=cache_key, ttl=ttl)

        except Exception as e:
            logger.warning("cache_set_failed", cache_key=cache_key, error=str(e))

    async def invalidate(self, cache_key: str) -> None:
        """Delete a specific cache key.

        Args:
            cache_key: Key to delete
        """
        try:
            await self.redis.delete(cache_key)
            logger.debug("cache_invalidated", cache_key=cache_key)
        except Exception as e:
            logger.warning("cache_invalidate_failed", cache_key=cache_key, error=str(e))

    async def invalidate_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern.

        Args:
            pattern: Redis glob pattern (e.g., "search:*")

        Returns:
            Number of keys deleted
        """
        try:
            count = 0
            async for key in self.redis.scan_iter(match=pattern):
                await self.redis.delete(key)
                count += 1
            logger.debug("cache_pattern_invalidated", pattern=pattern, count=count)
            return count
        except Exception as e:
            logger.warning(
                "cache_pattern_invalidate_failed", pattern=pattern, error=str(e)
            )
            return 0

    def _jitter_ttl(self, base_ttl: int) -> int:
        """Add ±10% random jitter to prevent cache stampede.

        Args:
            base_ttl: Base TTL in seconds

        Returns:
            Jittered TTL
        """
        jitter = random.uniform(-0.1, 0.1)
        return max(1, int(base_ttl * (1 + jitter)))

    def _get_original_ttl(self, cache_key: str) -> int:
        """Get original TTL based on key prefix.

        Args:
            cache_key: Cache key

        Returns:
            Original TTL in seconds
        """
        ttl_map = {
            "search": self.TTL_SEARCH_RESULTS,
            "work": self.TTL_WORK_DETAILS,
            "isbn": self.TTL_ISBN_DETAILS,
        }

        prefix = cache_key.split(":", 1)[0] if ":" in cache_key else cache_key
        return ttl_map.get(prefix, self.TTL_SEARCH_RESULTS)

    # -------------------------------------------------------------------------
    # Cache Key Generators
    # -------------------------------------------------------------------------

    @staticmethod
    def search_key(
        *,
        title: str,
        author: str | None = None,
        publisher: str | None = None,
        language: str | None = None,
    ) -> str:
        """Generate a deterministic cache key for search parameters.

        Same search parameters = same key = cache hit.
        Normalizes input (lowercase, strip, sorted keys).

        Args:
            title: Search title
            author: Optional author
            publisher: Optional publisher
            language: Optional language code

        Returns:
            Cache key (e.g., "search:a3f2b1c4d5e6f7a8")
        """
        # Normalize: lowercase, strip whitespace
        normalized = {
            "title": title.lower().strip(),
        }
        if author:
            normalized["author"] = author.lower().strip()
        if publisher:
            normalized["publisher"] = publisher.lower().strip()
        if language:
            normalized["language"] = language.lower().strip()

        # Create deterministic string (sorted keys)
        key_parts = sorted(f"{k}={v}" for k, v in normalized.items() if v)
        key_string = "&".join(key_parts)

        # Hash for storage efficiency
        hash_digest = hashlib.sha256(key_string.encode()).hexdigest()[:16]
        return f"search:{hash_digest}"

    @staticmethod
    def isbn_key(isbn: str) -> str:
        """Generate cache key for ISBN-based lookup.

        Args:
            isbn: ISBN (10 or 13 digits)

        Returns:
            Cache key (e.g., "isbn:9780618640157")
        """
        return f"isbn:{isbn}"

    @staticmethod
    def work_key(identifier: str) -> str:
        """Generate cache key for work details.

        Args:
            identifier: Work identifier (ISBN or internal ID)

        Returns:
            Cache key (e.g., "work:9780618640157")
        """
        return f"work:{identifier}"


# Global Redis client (set during app startup)
_redis_client: Redis | None = None


def set_redis_client(redis: Redis) -> None:
    """Set the global Redis client during app startup.

    Call this in your FastAPI lifespan:
        ```python
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            redis = Redis.from_url(settings.redis_url)
            set_redis_client(redis)
            yield
            await redis.close()
        ```
    """
    global _redis_client
    _redis_client = redis


def get_cache_service() -> CacheService:
    """FastAPI dependency for CacheService.

    Usage:
        ```python
        @router.get("/search")
        async def search(cache: CacheService = Depends(get_cache_service)):
            data, stale = await cache.get("search:abc123")
        ```
    """
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized. Call set_redis_client first.")
    return CacheService(_redis_client)
