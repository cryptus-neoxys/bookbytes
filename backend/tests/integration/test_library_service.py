"""Integration tests for LibraryService.

These tests verify the LibraryService logic with mocked repositories.
For true database integration tests, the test_db_session fixture needs
to be properly implemented (marked as TODO in conftest.py).

Run these tests with:
    pytest tests/integration/test_library_service.py -v
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from bookbytes.models.edition import Edition
from bookbytes.models.work import Work
from bookbytes.services.library import LibraryService
from bookbytes.services.openlibrary import BookSearchResult, WorkDetails

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_work_repo():
    """Create a mock WorkRepository with realistic behavior."""
    repo = MagicMock()
    repo.get = AsyncMock()
    repo.create = AsyncMock()
    return repo


@pytest.fixture
def mock_edition_repo():
    """Create a mock EditionRepository with realistic behavior."""
    repo = MagicMock()
    repo.get_by_isbn = AsyncMock(return_value=None)
    repo.get_latest_by_work = AsyncMock(return_value=None)
    repo.isbn_exists = AsyncMock(return_value=False)
    repo.create = AsyncMock()
    return repo


@pytest.fixture
def mock_provider_repo():
    """Create a mock BookProviderRepository with realistic behavior."""
    repo = MagicMock()
    repo.get_by_provider_key = AsyncMock(return_value=None)
    repo.create_work_mapping = AsyncMock()
    repo.create_edition_mapping = AsyncMock()
    repo.get_for_edition = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def library_service(mock_work_repo, mock_edition_repo, mock_provider_repo):
    """Create LibraryService with mocked repositories."""
    return LibraryService(
        work_repo=mock_work_repo,
        edition_repo=mock_edition_repo,
        provider_repo=mock_provider_repo,
    )


@pytest.fixture
def sample_search_result() -> BookSearchResult:
    """Create a sample BookSearchResult."""
    return BookSearchResult(
        title="The Lord of the Rings",
        authors=["J. R. R. Tolkien"],
        first_publish_year=1954,
        cover_url="https://covers.openlibrary.org/b/id/258027-M.jpg",
        isbn_list=["9780618640157"],
        edition_count=120,
        subjects=["Fantasy", "Epic"],
        external_work_key="/works/OL27448W",
    )


@pytest.fixture
def sample_work_details() -> WorkDetails:
    """Create sample work details."""
    return WorkDetails(
        title="1984",
        authors=["George Orwell"],
        description="A dystopian novel.",
        subjects=["Dystopia", "Politics"],
        first_publish_year=1949,
        cover_url=None,
        edition_count=200,
        isbn_list=["9780451524935"],
        external_work_key="/works/OL1168083W",
    )


@pytest.fixture
def sample_work() -> Work:
    """Create a sample Work instance."""
    work = Work(
        title="The Lord of the Rings",
        authors=["J. R. R. Tolkien"],
        subjects=["Fantasy"],
        first_publish_year=1954,
    )
    work.id = UUID("01234567-89ab-cdef-0123-456789abcdef")
    return work


@pytest.fixture
def sample_edition(sample_work: Work) -> Edition:
    """Create a sample Edition instance."""
    edition = Edition(
        work_id=sample_work.id,
        isbn="9780618640157",
        isbn_type="isbn13",
        title="The Lord of the Rings",
        language="eng",
    )
    edition.id = UUID("fedcba98-7654-3210-fedc-ba9876543210")
    return edition


# =============================================================================
# Work Persistence Tests
# =============================================================================


class TestLibraryServiceWorkPersistence:
    """Integration tests for Work persistence."""

    @pytest.mark.asyncio
    async def test_create_work_creates_provider_mapping(
        self,
        library_service: LibraryService,
        mock_work_repo: MagicMock,
        mock_provider_repo: MagicMock,
        sample_search_result: BookSearchResult,
        sample_work: Work,
    ) -> None:
        """Test that provider mapping is created when work is created."""
        mock_work_repo.create.return_value = sample_work

        await library_service.get_or_create_work(sample_search_result)

        # Verify provider mapping was created
        mock_provider_repo.create_work_mapping.assert_called_once()
        call_kwargs = mock_provider_repo.create_work_mapping.call_args.kwargs
        assert call_kwargs["provider"] == "openlibrary"
        assert call_kwargs["external_key"] == "/works/OL27448W"

    @pytest.mark.asyncio
    async def test_get_or_create_work_returns_existing(
        self,
        library_service: LibraryService,
        mock_work_repo: MagicMock,
        mock_provider_repo: MagicMock,
        sample_search_result: BookSearchResult,
        sample_work: Work,
    ) -> None:
        """Test that existing work is returned, not duplicated."""
        # Setup: work exists via provider mapping
        mock_mapping = MagicMock()
        mock_mapping.work_id = sample_work.id
        mock_provider_repo.get_by_provider_key.return_value = mock_mapping
        mock_work_repo.get.return_value = sample_work

        result = await library_service.get_or_create_work(sample_search_result)

        assert result == sample_work
        mock_work_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_work_from_details(
        self,
        library_service: LibraryService,
        mock_work_repo: MagicMock,
        sample_work_details: WorkDetails,
        sample_work: Work,
    ) -> None:
        """Test creating work from WorkDetails."""
        mock_work_repo.create.return_value = sample_work

        result = await library_service.get_or_create_work_from_details(
            sample_work_details
        )

        assert result.id is not None
        mock_work_repo.create.assert_called_once()


# =============================================================================
# Edition Persistence Tests
# =============================================================================


class TestLibraryServiceEditionPersistence:
    """Integration tests for Edition persistence."""

    @pytest.mark.asyncio
    async def test_store_edition_creates_new(
        self,
        library_service: LibraryService,
        mock_edition_repo: MagicMock,
        sample_work: Work,
        sample_edition: Edition,
    ) -> None:
        """Test that store_edition creates a new edition."""
        mock_edition_repo.get_by_isbn.return_value = None
        mock_edition_repo.create.return_value = sample_edition

        result = await library_service.store_edition(
            work=sample_work,
            isbn="9780618640157",
            title="50th Anniversary Edition",
            publisher="Houghton Mifflin",
            publish_year=2004,
        )

        assert result == sample_edition
        mock_edition_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_edition_normalizes_isbn(
        self,
        library_service: LibraryService,
        mock_edition_repo: MagicMock,
        sample_work: Work,
        sample_edition: Edition,
    ) -> None:
        """Test that ISBN is normalized before storing."""
        mock_edition_repo.get_by_isbn.return_value = None
        mock_edition_repo.create.return_value = sample_edition

        await library_service.store_edition(
            work=sample_work,
            isbn="978-0-618-64015-7",
        )

        # Check that get_by_isbn was called with normalized ISBN
        mock_edition_repo.get_by_isbn.assert_called_with("9780618640157")

    @pytest.mark.asyncio
    async def test_store_edition_returns_existing(
        self,
        library_service: LibraryService,
        mock_edition_repo: MagicMock,
        sample_work: Work,
        sample_edition: Edition,
    ) -> None:
        """Test that existing edition is returned, not duplicated."""
        mock_edition_repo.get_by_isbn.return_value = sample_edition

        result = await library_service.store_edition(
            work=sample_work, isbn="9780618640157"
        )

        assert result == sample_edition
        mock_edition_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_find_by_isbn_normalizes_input(
        self,
        library_service: LibraryService,
        mock_edition_repo: MagicMock,
    ) -> None:
        """Test that ISBN is normalized in find_by_isbn."""
        await library_service.find_by_isbn("978-0-618-64015-7")

        mock_edition_repo.get_by_isbn.assert_called_with("9780618640157")

    @pytest.mark.asyncio
    async def test_isbn_exists_returns_correct_value(
        self,
        library_service: LibraryService,
        mock_edition_repo: MagicMock,
    ) -> None:
        """Test isbn_exists returns correct boolean."""
        mock_edition_repo.isbn_exists.return_value = True

        result = await library_service.isbn_exists("9780618640157")

        assert result is True


# =============================================================================
# Provider Mapping Tests
# =============================================================================


class TestLibraryServiceProviderMapping:
    """Integration tests for provider mappings."""

    @pytest.mark.asyncio
    async def test_edition_provider_mapping_created(
        self,
        library_service: LibraryService,
        mock_edition_repo: MagicMock,
        mock_provider_repo: MagicMock,
        sample_work: Work,
        sample_edition: Edition,
    ) -> None:
        """Test that edition can have provider mapping."""
        mock_edition_repo.get_by_isbn.return_value = None
        mock_edition_repo.create.return_value = sample_edition

        await library_service.store_edition(
            work=sample_work,
            isbn="9780618640157",
            external_key="/books/OL12345M",
        )

        mock_provider_repo.create_edition_mapping.assert_called_once()
        call_kwargs = mock_provider_repo.create_edition_mapping.call_args.kwargs
        assert call_kwargs["external_key"] == "/books/OL12345M"

    @pytest.mark.asyncio
    async def test_find_work_by_nonexistent_provider(
        self,
        library_service: LibraryService,
        mock_provider_repo: MagicMock,
    ) -> None:
        """Test finding work by provider that doesn't exist."""
        mock_provider_repo.get_by_provider_key.return_value = None

        result = await library_service.find_work_by_provider(
            provider="openlibrary",
            external_key="/works/NONEXISTENT",
        )

        assert result is None
