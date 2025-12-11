"""Services package for BookBytes.

This module exports service classes for business logic.
"""

from bookbytes.services.cache import (
    CacheService,
    get_cache_service,
    set_redis_client,
)
from bookbytes.services.openlibrary import (
    BookSearchResult,
    OpenLibraryError,
    OpenLibraryRateLimitError,
    OpenLibraryService,
    SearchResponse,
    WorkDetails,
    get_openlibrary_service,
    set_openlibrary_service,
)

__all__ = [
    # Cache
    "CacheService",
    "get_cache_service",
    "set_redis_client",
    # OpenLibrary
    "BookSearchResult",
    "OpenLibraryError",
    "OpenLibraryRateLimitError",
    "OpenLibraryService",
    "SearchResponse",
    "WorkDetails",
    "get_openlibrary_service",
    "set_openlibrary_service",
]
