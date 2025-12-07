"""Library service for managing books in the database.

This service orchestrates Work, Edition, and BookProvider repositories
to persist data fetched from external providers like OpenLibrary.
"""

from uuid import UUID

import structlog

from bookbytes.models.edition import Edition
from bookbytes.models.work import Work
from bookbytes.repositories.book_provider import BookProviderRepository
from bookbytes.repositories.edition import EditionRepository
from bookbytes.repositories.work import WorkRepository
from bookbytes.services.openlibrary import BookSearchResult, WorkDetails

logger = structlog.get_logger(__name__)


class LibraryService:
    """Service for managing library persistence.

    Handles the creation and retrieval of Works and Editions,
    including their mappings to external providers.

    Usage:
        ```python
        service = LibraryService(work_repo, edition_repo, provider_repo)
        work = await service.get_or_create_work(search_result)
        ```
    """

    PROVIDER_OPENLIBRARY = "openlibrary"

    def __init__(
        self,
        work_repo: WorkRepository,
        edition_repo: EditionRepository,
        provider_repo: BookProviderRepository,
    ) -> None:
        """Initialize the service with repositories.

        Args:
            work_repo: Repository for Work entities
            edition_repo: Repository for Edition entities
            provider_repo: Repository for BookProvider mappings
        """
        self.work_repo = work_repo
        self.edition_repo = edition_repo
        self.provider_repo = provider_repo

    # -------------------------------------------------------------------------
    # Work Operations
    # -------------------------------------------------------------------------

    async def find_work_by_provider(
        self,
        provider: str,
        external_key: str,
    ) -> Work | None:
        """Find a work by its external provider key.

        Args:
            provider: Provider name (e.g., "openlibrary")
            external_key: External identifier (e.g., "/works/OL27448W")

        Returns:
            Work if found, None otherwise
        """
        mapping = await self.provider_repo.get_by_provider_key(provider, external_key)

        if mapping and mapping.work_id:
            logger.debug(
                "found_work_by_provider",
                provider=provider,
                external_key=external_key,
                work_id=str(mapping.work_id),
            )
            return await self.work_repo.get(mapping.work_id)

        return None

    async def get_or_create_work(
        self,
        search_result: BookSearchResult,
    ) -> Work:
        """Get existing work or create new one from search result.

        If the work already exists (via provider mapping), returns it.
        Otherwise, creates a new Work and links it to the provider.

        Args:
            search_result: BookSearchResult from OpenLibrary

        Returns:
            Existing or newly created Work
        """
        # Check if work already exists via provider mapping
        existing = await self.find_work_by_provider(
            provider=self.PROVIDER_OPENLIBRARY,
            external_key=search_result.external_work_key,
        )

        if existing:
            logger.info(
                "work_already_exists",
                work_id=str(existing.id),
                title=existing.title,
            )
            return existing

        # Create new work
        work = Work(
            title=search_result.title,
            authors=search_result.authors,
            subjects=search_result.subjects,
            first_publish_year=search_result.first_publish_year,
        )
        created_work = await self.work_repo.create(work)

        # Create provider mapping
        await self.provider_repo.create_work_mapping(
            work_id=created_work.id,
            provider=self.PROVIDER_OPENLIBRARY,
            external_key=search_result.external_work_key,
            provider_metadata={
                "fetched_at": search_result.fetched_at,
                "edition_count": search_result.edition_count,
            },
        )

        logger.info(
            "work_created",
            work_id=str(created_work.id),
            title=created_work.title,
            external_key=search_result.external_work_key,
        )

        return created_work

    async def get_or_create_work_from_details(
        self,
        work_details: WorkDetails,
    ) -> Work:
        """Get existing work or create new one from work details.

        Args:
            work_details: WorkDetails from OpenLibrary

        Returns:
            Existing or newly created Work
        """
        # Check if work already exists
        existing = await self.find_work_by_provider(
            provider=self.PROVIDER_OPENLIBRARY,
            external_key=work_details.external_work_key,
        )

        if existing:
            return existing

        # Create new work
        work = Work(
            title=work_details.title,
            authors=work_details.authors,
            subjects=work_details.subjects,
            first_publish_year=work_details.first_publish_year,
        )
        created_work = await self.work_repo.create(work)

        # Create provider mapping
        await self.provider_repo.create_work_mapping(
            work_id=created_work.id,
            provider=self.PROVIDER_OPENLIBRARY,
            external_key=work_details.external_work_key,
        )

        logger.info(
            "work_created_from_details",
            work_id=str(created_work.id),
            title=created_work.title,
        )

        return created_work

    # -------------------------------------------------------------------------
    # Edition Operations
    # -------------------------------------------------------------------------

    async def find_by_isbn(self, isbn: str) -> Edition | None:
        """Find an edition by ISBN.

        Args:
            isbn: ISBN-10 or ISBN-13 (normalized, no dashes)

        Returns:
            Edition if found, None otherwise
        """
        clean_isbn = isbn.replace("-", "").replace(" ", "")
        return await self.edition_repo.get_by_isbn(clean_isbn)

    async def find_latest_edition(
        self,
        work_id: UUID,
        language: str = "eng",
    ) -> Edition | None:
        """Find the latest edition of a work.

        Args:
            work_id: Work UUID
            language: ISO 639-2/B language code (default: "eng")

        Returns:
            Latest edition or None
        """
        return await self.edition_repo.get_latest_by_work(work_id, language)

    async def store_edition(
        self,
        work: Work,
        isbn: str,
        *,
        title: str | None = None,
        publisher: str | None = None,
        publish_year: int | None = None,
        language: str = "eng",
        pages: int | None = None,
        external_key: str | None = None,
    ) -> Edition:
        """Store a single edition for a work.

        Args:
            work: Parent Work entity
            isbn: ISBN-10 or ISBN-13
            title: Edition-specific title (defaults to work title)
            publisher: Publisher name
            publish_year: Publication year
            language: ISO 639-2/B language code
            pages: Page count
            external_key: External provider key for edition

        Returns:
            Created Edition
        """
        clean_isbn = isbn.replace("-", "").replace(" ", "")

        # Check if already exists
        existing = await self.edition_repo.get_by_isbn(clean_isbn)
        if existing:
            logger.debug("edition_already_exists", isbn=clean_isbn)
            return existing

        # Determine ISBN type
        isbn_type = "isbn13" if len(clean_isbn) == 13 else "isbn10"

        # Create edition
        edition = Edition(
            work_id=work.id,
            isbn=clean_isbn,
            isbn_type=isbn_type,
            title=title or work.title,
            publisher=publisher,
            publish_year=publish_year,
            language=language,
            pages=pages,
        )
        created_edition = await self.edition_repo.create(edition)

        # Create provider mapping if external key provided
        if external_key:
            await self.provider_repo.create_edition_mapping(
                edition_id=created_edition.id,
                provider=self.PROVIDER_OPENLIBRARY,
                external_key=external_key,
            )

        logger.info(
            "edition_created",
            edition_id=str(created_edition.id),
            isbn=clean_isbn,
            work_id=str(work.id),
        )

        return created_edition

    async def isbn_exists(self, isbn: str) -> bool:
        """Check if an ISBN exists in the library.

        Args:
            isbn: ISBN to check

        Returns:
            True if exists
        """
        clean_isbn = isbn.replace("-", "").replace(" ", "")
        return await self.edition_repo.isbn_exists(clean_isbn)


# -----------------------------------------------------------------------------
# FastAPI Dependency Injection
# -----------------------------------------------------------------------------

_library_service: LibraryService | None = None


def set_library_service(service: LibraryService) -> None:
    """Set the global library service during app startup."""
    global _library_service
    _library_service = service


def get_library_service() -> LibraryService:
    """FastAPI dependency for LibraryService."""
    if _library_service is None:
        raise RuntimeError(
            "Library service not initialized. Call set_library_service first."
        )
    return _library_service
