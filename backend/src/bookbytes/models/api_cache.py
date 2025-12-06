"""APICache model - L2 cache for raw API responses.

This table serves as the PostgreSQL layer of our two-tier cache:
- L1: Redis (fast, volatile)
- L2: PostgreSQL (persistent, survives restarts)

The CacheService manages this table directly (no repository needed).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from bookbytes.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class APICache(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persistent cache for API responses (L2 layer).

    Stores raw API responses from external providers like OpenLibrary.
    Used to repopulate Redis cache after restarts.

    Attributes:
        cache_key: Unique key for this cache entry (hash of params)
        source: API source identifier (e.g., "openlibrary", "google_books")
        response_json: Raw JSON response from API
        total_results: Number of results in response (for pagination info)
        expires_at: When this cache entry expires
        original_ttl: Original TTL in seconds (for revalidation calculation)
        hit_count: Number of cache hits (for analytics)
    """

    __tablename__ = "api_cache"

    cache_key: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="openlibrary",
        index=True,
    )
    response_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    total_results: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    original_ttl: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )  # TTL in seconds for stale-while-revalidate calculation
    hit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        # Index for cleanup queries (expired entries)
        Index("ix_api_cache_expires_at_source", "expires_at", "source"),
    )

    def __repr__(self) -> str:
        return (
            f"<APICache(key='{self.cache_key}', source='{self.source}', "
            f"expires_at={self.expires_at}, hits={self.hit_count})>"
        )
