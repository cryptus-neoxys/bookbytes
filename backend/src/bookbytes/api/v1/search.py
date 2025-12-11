"""Book search and lookup endpoints.

Provides endpoints for searching books via OpenLibrary,
fetching work details, and ISBN lookups.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from bookbytes.core.exceptions import BookNotFoundError, ExternalServiceError
from bookbytes.core.logging import get_logger
from bookbytes.schemas.common import ErrorResponse
from bookbytes.schemas.search import (
    BookSearchRequest,
    BookSearchResponse,
    BookSearchResultItem,
    WorkResponse,
)
from bookbytes.services.cache import CacheService, get_cache_service
from bookbytes.services.openlibrary import (
    OpenLibraryError,
    OpenLibraryService,
)

logger = get_logger(__name__)

router = APIRouter()


# =============================================================================
# Dependencies
# =============================================================================


def get_openlibrary_service(
    cache: Annotated[CacheService, Depends(get_cache_service)],
) -> OpenLibraryService:
    """Create OpenLibraryService with injected cache."""
    return OpenLibraryService(cache)


# =============================================================================
# Search Endpoints
# =============================================================================


@router.post(
    "/search",
    response_model=BookSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search for books",
    description="Search books via OpenLibrary by title, author, publisher, or language.",
    responses={
        200: {"description": "Search results"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        502: {"model": ErrorResponse, "description": "External service error"},
    },
)
async def search_books(
    request: BookSearchRequest,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Results per page")] = 20,
    openlibrary: Annotated[OpenLibraryService, Depends(get_openlibrary_service)] = None,
) -> BookSearchResponse:
    """Search for books by title, author, etc.

    Uses OpenLibrary API with caching. Results are paginated from
    a larger cached result set (100 per API call).
    """
    logger.info(
        "search_books_request",
        title=request.title,
        author=request.author,
        page=page,
        page_size=page_size,
    )

    try:
        # Calculate offset for API call
        # We fetch 100 results max, then slice for pagination
        api_offset = ((page - 1) // 5) * 100  # Fetch next batch every 5 pages

        result = await openlibrary.search_books(
            title=request.title,
            author=request.author,
            publisher=request.publisher,
            language=request.language,
            offset=api_offset,
        )

        # Calculate slice for requested page
        # Within our 100-result batch, find the right slice
        batch_start = (page - 1) % 5 * page_size
        batch_end = batch_start + page_size
        page_results = result.results[batch_start:batch_end]

        # Convert to response format
        items = [
            BookSearchResultItem(
                title=r.title,
                authors=r.authors,
                first_publish_year=r.first_publish_year,
                cover_url=r.cover_url,
                isbn_list=r.isbn_list,
                edition_count=r.edition_count,
                subjects=r.subjects,
                external_work_key=r.external_work_key,
            )
            for r in page_results
        ]

        logger.info(
            "search_books_success",
            total_found=result.total_found,
            results_returned=len(items),
        )

        return BookSearchResponse(
            results=items,
            total_found=result.total_found,
            page=page,
            page_size=page_size,
            has_more=(page * page_size) < result.total_found,
        )

    except OpenLibraryError as e:
        logger.error("search_books_failed", error=str(e))
        raise ExternalServiceError(
            message="Failed to search books",
            details={"provider": "openlibrary", "error": str(e)},
        ) from e
    finally:
        await openlibrary.close()


@router.get(
    "/works/{work_key:path}",
    response_model=WorkResponse,
    status_code=status.HTTP_200_OK,
    summary="Get work details",
    description="Fetch detailed information about a work by its OpenLibrary key.",
    responses={
        200: {"description": "Work details"},
        404: {"model": ErrorResponse, "description": "Work not found"},
        502: {"model": ErrorResponse, "description": "External service error"},
    },
)
async def get_work_details(
    work_key: str,
    openlibrary: Annotated[OpenLibraryService, Depends(get_openlibrary_service)] = None,
) -> WorkResponse:
    """Get detailed information about a work.

    Args:
        work_key: OpenLibrary work key (e.g., "works/OL27448W")
    """
    # Normalize work key
    if not work_key.startswith("/"):
        work_key = f"/{work_key}"

    logger.info("get_work_details_request", work_key=work_key)

    try:
        work = await openlibrary.get_work_details(work_key)

        logger.info("get_work_details_success", work_key=work_key, title=work.title)

        return WorkResponse(
            id=None,  # Not yet in our library
            title=work.title,
            authors=work.authors,
            description=work.description,
            subjects=work.subjects,
            first_publish_year=work.first_publish_year,
            cover_url=work.cover_url,
            edition_count=work.edition_count,
            external_work_key=work.external_work_key,
            editions=[],  # Editions fetched separately
        )

    except OpenLibraryError as e:
        logger.error("get_work_details_failed", work_key=work_key, error=str(e))
        raise ExternalServiceError(
            message="Failed to fetch work details",
            details={"work_key": work_key, "error": str(e)},
        ) from e
    finally:
        await openlibrary.close()


@router.get(
    "/isbn/{isbn}",
    response_model=WorkResponse,
    status_code=status.HTTP_200_OK,
    summary="Lookup by ISBN",
    description="Find a book by ISBN. Checks library first, then queries OpenLibrary.",
    responses={
        200: {"description": "Book details"},
        404: {"model": ErrorResponse, "description": "ISBN not found"},
        502: {"model": ErrorResponse, "description": "External service error"},
    },
)
async def lookup_by_isbn(
    isbn: str,
    openlibrary: Annotated[OpenLibraryService, Depends(get_openlibrary_service)] = None,
) -> WorkResponse:
    """Lookup a book by ISBN.

    First checks if the ISBN exists in our library.
    If not, queries OpenLibrary and optionally stores the result.

    Args:
        isbn: ISBN-10 or ISBN-13
    """
    # Normalize ISBN (remove dashes/spaces)
    clean_isbn = isbn.replace("-", "").replace(" ", "")

    logger.info("lookup_isbn_request", isbn=clean_isbn)

    # TODO: Check library first (EditionRepository)
    # For now, search OpenLibrary directly

    try:
        # Search by ISBN
        result = await openlibrary.search_books(title=clean_isbn)

        if not result.results:
            logger.warning("lookup_isbn_not_found", isbn=clean_isbn)
            raise BookNotFoundError(isbn=clean_isbn)

        # Get the first match and fetch full work details
        first_match = result.results[0]
        work = await openlibrary.get_work_details(first_match.external_work_key)

        logger.info(
            "lookup_isbn_success",
            isbn=clean_isbn,
            work_key=work.external_work_key,
            title=work.title,
        )

        return WorkResponse(
            id=None,
            title=work.title,
            authors=work.authors,
            description=work.description,
            subjects=work.subjects,
            first_publish_year=work.first_publish_year,
            cover_url=work.cover_url,
            edition_count=work.edition_count,
            external_work_key=work.external_work_key,
            editions=[],
        )

    except BookNotFoundError:
        raise
    except OpenLibraryError as e:
        logger.error("lookup_isbn_failed", isbn=clean_isbn, error=str(e))
        raise ExternalServiceError(
            message="Failed to lookup ISBN",
            details={"isbn": clean_isbn, "error": str(e)},
        ) from e
    finally:
        await openlibrary.close()
