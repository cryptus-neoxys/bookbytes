"""OpenLibrary API client service.

This service provides async access to the OpenLibrary API for book search
and metadata retrieval. Uses canonical internal DTOs for all responses.

See: https://openlibrary.org/dev/docs/api/search
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import httpx
import structlog

from bookbytes.config import get_settings
from bookbytes.services.cache import CacheService

logger = structlog.get_logger(__name__)


# -----------------------------------------------------------------------------
# DTOs (Canonical Internal Models - Anti-Corruption Layer)
# -----------------------------------------------------------------------------


@dataclass
class BookSearchResult:
    """Canonical search result - provider agnostic.

    Maps OpenLibrary (and future provider) responses to internal format.
    """

    title: str
    authors: list[str]
    first_publish_year: int | None
    cover_url: str | None
    isbn_list: list[str]
    edition_count: int
    subjects: list[str]

    # Metadata (stored in cache, not used for key)
    external_work_key: str  # e.g., "/works/OL27448W"
    source_provider: str = "openlibrary"
    fetched_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict for caching."""
        return {
            "title": self.title,
            "authors": self.authors,
            "first_publish_year": self.first_publish_year,
            "cover_url": self.cover_url,
            "isbn_list": self.isbn_list,
            "edition_count": self.edition_count,
            "subjects": self.subjects,
            "external_work_key": self.external_work_key,
            "source_provider": self.source_provider,
            "fetched_at": self.fetched_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BookSearchResult":
        """Create from cached dict."""
        return cls(
            title=data["title"],
            authors=data["authors"],
            first_publish_year=data.get("first_publish_year"),
            cover_url=data.get("cover_url"),
            isbn_list=data.get("isbn_list", []),
            edition_count=data.get("edition_count", 0),
            subjects=data.get("subjects", []),
            external_work_key=data["external_work_key"],
            source_provider=data.get("source_provider", "openlibrary"),
            fetched_at=data.get("fetched_at", ""),
        )


@dataclass
class WorkDetails:
    """Canonical work details - provider agnostic."""

    title: str
    authors: list[str]
    description: str | None
    subjects: list[str]
    first_publish_year: int | None
    cover_url: str | None
    edition_count: int
    isbn_list: list[str]

    # Metadata
    external_work_key: str
    source_provider: str = "openlibrary"
    fetched_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "title": self.title,
            "authors": self.authors,
            "description": self.description,
            "subjects": self.subjects,
            "first_publish_year": self.first_publish_year,
            "cover_url": self.cover_url,
            "edition_count": self.edition_count,
            "isbn_list": self.isbn_list,
            "external_work_key": self.external_work_key,
            "source_provider": self.source_provider,
            "fetched_at": self.fetched_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkDetails":
        """Create from cached dict."""
        return cls(
            title=data["title"],
            authors=data["authors"],
            description=data.get("description"),
            subjects=data.get("subjects", []),
            first_publish_year=data.get("first_publish_year"),
            cover_url=data.get("cover_url"),
            edition_count=data.get("edition_count", 0),
            isbn_list=data.get("isbn_list", []),
            external_work_key=data["external_work_key"],
            source_provider=data.get("source_provider", "openlibrary"),
            fetched_at=data.get("fetched_at", ""),
        )


@dataclass
class SearchResponse:
    """Container for search results with pagination info."""

    results: list[BookSearchResult]
    total_found: int
    offset: int
    limit: int

    @property
    def has_more(self) -> bool:
        """Check if there are more results to fetch."""
        return self.offset + len(self.results) < self.total_found


# -----------------------------------------------------------------------------
# OpenLibrary Service
# -----------------------------------------------------------------------------


class OpenLibraryError(Exception):
    """Base exception for OpenLibrary API errors."""

    pass


class OpenLibraryRateLimitError(OpenLibraryError):
    """Rate limit exceeded."""

    pass


class OpenLibraryService:
    """Async client for OpenLibrary API.

    Uses httpx for async HTTP requests and integrates with CacheService
    for caching responses. All responses are converted to canonical DTOs.

    Usage:
        ```python
        service = OpenLibraryService(cache_service)
        results = await service.search_books(title="Lord of the Rings")
        ```
    """

    COVER_BASE_URL = "https://covers.openlibrary.org/b"

    def __init__(self, cache: CacheService) -> None:
        """Initialize the service.

        Args:
            cache: CacheService instance for caching responses
        """
        self.cache = cache
        self._settings = get_settings()
        self._client: httpx.AsyncClient | None = None

    @property
    def _user_agent(self) -> str:
        """User-Agent header for API compliance."""
        return f"{self._settings.app_name}/{self._settings.app_version} (contact@bookbytes.app)"

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._settings.openlibrary_base_url,
                timeout=self._settings.openlibrary_timeout,
                headers={"User-Agent": self._user_agent},
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def search_books(
        self,
        *,
        title: str,
        author: str | None = None,
        publisher: str | None = None,
        language: str | None = None,
        offset: int = 0,
    ) -> SearchResponse:
        """Search for books by title, author, etc.

        Args:
            title: Book title to search
            author: Optional author name
            publisher: Optional publisher name
            language: Optional language code (e.g., "eng")
            offset: Pagination offset

        Returns:
            SearchResponse with matching books

        Raises:
            OpenLibraryError: On API errors
        """
        # Check cache first
        cache_key = CacheService.search_key(
            title=title,
            author=author,
            publisher=publisher,
            language=language,
        )

        cached_data, needs_revalidation = await self.cache.get(cache_key)
        if cached_data and not needs_revalidation:
            logger.debug("search_cache_hit", cache_key=cache_key)
            return self._parse_cached_search(cached_data)

        # Cache miss or stale - fetch from API
        logger.debug("search_cache_miss", cache_key=cache_key)
        response = await self._fetch_search(
            title=title,
            author=author,
            publisher=publisher,
            language=language,
            offset=offset,
        )

        # Cache the response (fire and forget for now)
        await self.cache.set(cache_key, self._serialize_search(response))

        return response

    async def get_work_details(self, work_key: str) -> WorkDetails:
        """Get detailed information about a work.

        Args:
            work_key: OpenLibrary work key (e.g., "/works/OL27448W")

        Returns:
            WorkDetails with full metadata

        Raises:
            OpenLibraryError: On API errors
        """
        # Use ISBN or work key for cache
        cache_key = CacheService.work_key(work_key)

        cached_data, needs_revalidation = await self.cache.get(cache_key)
        if cached_data and not needs_revalidation:
            logger.debug("work_cache_hit", cache_key=cache_key)
            return WorkDetails.from_dict(cached_data)

        # Fetch from API
        logger.debug("work_cache_miss", cache_key=cache_key)
        work = await self._fetch_work(work_key)

        # Cache the response
        await self.cache.set(cache_key, work.to_dict())

        return work

    async def get_all_isbns_for_work(self, work_key: str) -> list[str]:
        """Get all ISBNs associated with a work.

        Args:
            work_key: OpenLibrary work key

        Returns:
            List of ISBNs (both ISBN-10 and ISBN-13)
        """
        work = await self.get_work_details(work_key)
        return work.isbn_list

    # -------------------------------------------------------------------------
    # Private Methods - API Fetching
    # -------------------------------------------------------------------------

    async def _fetch_search(
        self,
        *,
        title: str,
        author: str | None = None,
        publisher: str | None = None,
        language: str | None = None,
        offset: int = 0,
    ) -> SearchResponse:
        """Fetch search results from OpenLibrary API."""
        client = await self._get_client()

        params: dict[str, Any] = {
            "title": title,
            "limit": self._settings.openlibrary_page_size,
            "offset": offset,
            "fields": "key,title,author_name,author_key,first_publish_year,"
            "edition_count,cover_i,isbn,language,publisher,subject",
        }

        if author:
            params["author"] = author
        if publisher:
            params["publisher"] = publisher
        if language:
            params["language"] = language

        try:
            response = await client.get("/search.json", params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise OpenLibraryRateLimitError("Rate limit exceeded") from e
            logger.error(
                "openlibrary_search_failed",
                status_code=e.response.status_code,
                title=title,
            )
            raise OpenLibraryError(
                f"API request failed: {e.response.status_code}"
            ) from e
        except httpx.RequestError as e:
            logger.error("openlibrary_request_error", error=str(e), title=title)
            raise OpenLibraryError(f"Request failed: {e}") from e

        data = response.json()
        return self._parse_search_response(data)

    async def _fetch_work(self, work_key: str) -> WorkDetails:
        """Fetch work details from OpenLibrary API."""
        client = await self._get_client()

        # Normalize work key (remove leading slash if present)
        work_id = work_key.lstrip("/")

        try:
            response = await client.get(f"/{work_id}.json")
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(
                "openlibrary_work_fetch_failed",
                status_code=e.response.status_code,
                work_key=work_key,
            )
            raise OpenLibraryError(
                f"API request failed: {e.response.status_code}"
            ) from e
        except httpx.RequestError as e:
            logger.error("openlibrary_request_error", error=str(e), work_key=work_key)
            raise OpenLibraryError(f"Request failed: {e}") from e

        data = response.json()
        return self._parse_work_response(data, work_key)

    # -------------------------------------------------------------------------
    # Private Methods - Response Parsing (Anti-Corruption Layer)
    # -------------------------------------------------------------------------

    def _parse_search_response(self, data: dict[str, Any]) -> SearchResponse:
        """Parse OpenLibrary search response to canonical format."""
        results = []

        for doc in data.get("docs", []):
            # Build cover URL
            cover_id = doc.get("cover_i")
            cover_url = (
                f"{self.COVER_BASE_URL}/id/{cover_id}-M.jpg" if cover_id else None
            )

            result = BookSearchResult(
                title=doc.get("title", "Unknown"),
                authors=doc.get("author_name", []),
                first_publish_year=doc.get("first_publish_year"),
                cover_url=cover_url,
                isbn_list=doc.get("isbn", [])[:20],  # Limit ISBNs
                edition_count=doc.get("edition_count", 0),
                subjects=doc.get("subject", [])[:10],  # Limit subjects
                external_work_key=doc.get("key", ""),
            )
            results.append(result)

        return SearchResponse(
            results=results,
            total_found=data.get("numFound", 0),
            offset=data.get("start", 0),
            limit=self._settings.openlibrary_page_size,
        )

    def _parse_work_response(self, data: dict[str, Any], work_key: str) -> WorkDetails:
        """Parse OpenLibrary work response to canonical format."""
        # Handle description (can be string or dict)
        description = data.get("description")
        if isinstance(description, dict):
            description = description.get("value", "")

        # Extract cover from covers array
        covers = data.get("covers", [])
        cover_url = f"{self.COVER_BASE_URL}/id/{covers[0]}-M.jpg" if covers else None

        # Get subjects
        subjects = data.get("subjects", [])
        if isinstance(subjects, list) and subjects and isinstance(subjects[0], dict):
            subjects = [s.get("name", "") for s in subjects]

        return WorkDetails(
            title=data.get("title", "Unknown"),
            authors=[],  # Need separate author fetch - simplified for now
            description=description,
            subjects=subjects[:20] if subjects else [],
            first_publish_year=None,  # Need editions data
            cover_url=cover_url,
            edition_count=0,  # Need separate query
            isbn_list=[],  # Need editions query
            external_work_key=work_key,
        )

    def _parse_cached_search(self, data: dict[str, Any]) -> SearchResponse:
        """Parse cached search data back to SearchResponse."""
        return SearchResponse(
            results=[BookSearchResult.from_dict(r) for r in data.get("results", [])],
            total_found=data.get("total_found", 0),
            offset=data.get("offset", 0),
            limit=data.get("limit", self._settings.openlibrary_page_size),
        )

    def _serialize_search(self, response: SearchResponse) -> dict[str, Any]:
        """Serialize SearchResponse for caching."""
        return {
            "results": [r.to_dict() for r in response.results],
            "total_found": response.total_found,
            "offset": response.offset,
            "limit": response.limit,
        }


# -----------------------------------------------------------------------------
# FastAPI Dependency Injection
# -----------------------------------------------------------------------------

_openlibrary_service: OpenLibraryService | None = None


def set_openlibrary_service(service: OpenLibraryService) -> None:
    """Set the global OpenLibrary service during app startup."""
    global _openlibrary_service
    _openlibrary_service = service


def get_openlibrary_service() -> OpenLibraryService:
    """FastAPI dependency for OpenLibraryService."""
    if _openlibrary_service is None:
        raise RuntimeError(
            "OpenLibrary service not initialized. Call set_openlibrary_service first."
        )
    return _openlibrary_service
