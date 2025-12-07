"""Tests for LibraryService.

Tests the library persistence layer with mocked repositories.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from bookbytes.models.edition import Edition
from bookbytes.models.work import Work
from bookbytes.services.library import LibraryService
from bookbytes.services.openlibrary import BookSearchResult

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_work_repo():
    """Create a mock WorkRepository."""
    repo = MagicMock()
    repo.get = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    return repo


@pytest.fixture
def mock_edition_repo():
    """Create a mock EditionRepository."""
    repo = MagicMock()
    repo.get_by_isbn = AsyncMock(return_value=None)
    repo.get_latest_by_work = AsyncMock(return_value=None)
    repo.isbn_exists = AsyncMock(return_value=False)
    repo.create = AsyncMock()
    return repo


@pytest.fixture
def mock_provider_repo():
    """Create a mock BookProviderRepository."""
    repo = MagicMock()
    repo.get_by_provider_key = AsyncMock(return_value=None)
    repo.create_work_mapping = AsyncMock()
    repo.create_edition_mapping = AsyncMock()
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
def sample_work() -> Work:
    """Create a sample Work."""
    work = Work(
        title="The Lord of the Rings",
        authors=["J. R. R. Tolkien"],
        subjects=["Fantasy"],
        first_publish_year=1954,
    )
    # Mock the ID
    work.id = UUID("01234567-89ab-cdef-0123-456789abcdef")
    return work


@pytest.fixture
def sample_edition() -> Edition:
    """Create a sample Edition."""
    edition = Edition(
        work_id=UUID("01234567-89ab-cdef-0123-456789abcdef"),
        isbn="9780618640157",
        isbn_type="isbn13",
        title="The Lord of the Rings",
        language="eng",
    )
    edition.id = UUID("fedcba98-7654-3210-fedc-ba9876543210")
    return edition


# =============================================================================
# Work Operations Tests
# =============================================================================


class TestFindWorkByProvider:
    """Tests for find_work_by_provider method."""

    @pytest.mark.asyncio
    async def test_find_work_returns_none_when_not_found(
        self,
        library_service: LibraryService,
        mock_provider_repo: MagicMock,
    ) -> None:
        """Test returns None when no mapping exists."""
        mock_provider_repo.get_by_provider_key.return_value = None

        result = await library_service.find_work_by_provider(
            "openlibrary", "/works/OL12345W"
        )

        assert result is None
        mock_provider_repo.get_by_provider_key.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_work_returns_work_when_found(
        self,
        library_service: LibraryService,
        mock_provider_repo: MagicMock,
        mock_work_repo: MagicMock,
        sample_work: Work,
    ) -> None:
        """Test returns Work when mapping exists."""
        mock_mapping = MagicMock()
        mock_mapping.work_id = sample_work.id
        mock_provider_repo.get_by_provider_key.return_value = mock_mapping
        mock_work_repo.get.return_value = sample_work

        result = await library_service.find_work_by_provider(
            "openlibrary", "/works/OL27448W"
        )

        assert result == sample_work
        mock_work_repo.get.assert_called_once_with(sample_work.id)


class TestGetOrCreateWork:
    """Tests for get_or_create_work method."""

    @pytest.mark.asyncio
    async def test_returns_existing_work(
        self,
        library_service: LibraryService,
        mock_provider_repo: MagicMock,
        mock_work_repo: MagicMock,
        sample_search_result: BookSearchResult,
        sample_work: Work,
    ) -> None:
        """Test returns existing work if already in library."""
        mock_mapping = MagicMock()
        mock_mapping.work_id = sample_work.id
        mock_provider_repo.get_by_provider_key.return_value = mock_mapping
        mock_work_repo.get.return_value = sample_work

        result = await library_service.get_or_create_work(sample_search_result)

        assert result == sample_work
        mock_work_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_creates_new_work(
        self,
        library_service: LibraryService,
        mock_provider_repo: MagicMock,
        mock_work_repo: MagicMock,
        sample_search_result: BookSearchResult,
        sample_work: Work,
    ) -> None:
        """Test creates new work if not in library."""
        mock_provider_repo.get_by_provider_key.return_value = None
        mock_work_repo.create.return_value = sample_work

        result = await library_service.get_or_create_work(sample_search_result)

        assert result == sample_work
        mock_work_repo.create.assert_called_once()
        mock_provider_repo.create_work_mapping.assert_called_once()


# =============================================================================
# Edition Operations Tests
# =============================================================================


class TestFindByISBN:
    """Tests for find_by_isbn method."""

    @pytest.mark.asyncio
    async def test_find_by_isbn_normalizes_input(
        self,
        library_service: LibraryService,
        mock_edition_repo: MagicMock,
    ) -> None:
        """Test ISBN is normalized before lookup."""
        await library_service.find_by_isbn("978-0-618-64015-7")

        # Should be called with normalized ISBN
        mock_edition_repo.get_by_isbn.assert_called_once_with("9780618640157")

    @pytest.mark.asyncio
    async def test_find_by_isbn_returns_edition(
        self,
        library_service: LibraryService,
        mock_edition_repo: MagicMock,
        sample_edition: Edition,
    ) -> None:
        """Test returns edition when found."""
        mock_edition_repo.get_by_isbn.return_value = sample_edition

        result = await library_service.find_by_isbn("9780618640157")

        assert result == sample_edition


class TestStoreEdition:
    """Tests for store_edition method."""

    @pytest.mark.asyncio
    async def test_store_edition_returns_existing(
        self,
        library_service: LibraryService,
        mock_edition_repo: MagicMock,
        sample_work: Work,
        sample_edition: Edition,
    ) -> None:
        """Test returns existing edition if ISBN already exists."""
        mock_edition_repo.get_by_isbn.return_value = sample_edition

        result = await library_service.store_edition(
            work=sample_work,
            isbn="9780618640157",
        )

        assert result == sample_edition
        mock_edition_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_store_edition_creates_new(
        self,
        library_service: LibraryService,
        mock_edition_repo: MagicMock,
        sample_work: Work,
        sample_edition: Edition,
    ) -> None:
        """Test creates new edition if not exists."""
        mock_edition_repo.get_by_isbn.return_value = None
        mock_edition_repo.create.return_value = sample_edition

        result = await library_service.store_edition(
            work=sample_work,
            isbn="9780618640157",
            title="Special Edition",
            publisher="Houghton Mifflin",
            publish_year=2004,
        )

        assert result == sample_edition
        mock_edition_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_edition_with_provider_mapping(
        self,
        library_service: LibraryService,
        mock_edition_repo: MagicMock,
        mock_provider_repo: MagicMock,
        sample_work: Work,
        sample_edition: Edition,
    ) -> None:
        """Test creates provider mapping when external_key provided."""
        mock_edition_repo.get_by_isbn.return_value = None
        mock_edition_repo.create.return_value = sample_edition

        await library_service.store_edition(
            work=sample_work,
            isbn="9780618640157",
            external_key="/books/OL12345M",
        )

        mock_provider_repo.create_edition_mapping.assert_called_once()


class TestISBNExists:
    """Tests for isbn_exists method."""

    @pytest.mark.asyncio
    async def test_isbn_exists_true(
        self,
        library_service: LibraryService,
        mock_edition_repo: MagicMock,
    ) -> None:
        """Test returns True when ISBN exists."""
        mock_edition_repo.isbn_exists.return_value = True

        result = await library_service.isbn_exists("9780618640157")

        assert result is True

    @pytest.mark.asyncio
    async def test_isbn_exists_false(
        self,
        library_service: LibraryService,
        mock_edition_repo: MagicMock,
    ) -> None:
        """Test returns False when ISBN doesn't exist."""
        mock_edition_repo.isbn_exists.return_value = False

        result = await library_service.isbn_exists("0000000000000")

        assert result is False
