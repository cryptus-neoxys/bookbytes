"""Search and book-related API schemas.

This module defines Pydantic models for book search, work details,
and audiobook processing endpoints.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from bookbytes.schemas.common import BaseSchema

# =============================================================================
# Search Request/Response
# =============================================================================


class BookSearchRequest(BaseSchema):
    """Request body for book search.

    Attributes:
        title: Book title to search (required)
        author: Optional author name filter
        publisher: Optional publisher filter
        language: Optional language code (e.g., "eng")
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Book title to search",
        json_schema_extra={"example": "Lord of the Rings"},
    )
    author: str | None = Field(
        None,
        max_length=200,
        description="Filter by author name",
        json_schema_extra={"example": "J.R.R. Tolkien"},
    )
    publisher: str | None = Field(
        None,
        max_length=200,
        description="Filter by publisher",
    )
    language: str | None = Field(
        None,
        min_length=2,
        max_length=10,
        description="Language code (e.g., 'eng', 'spa')",
        json_schema_extra={"example": "eng"},
    )


class BookSearchResultItem(BaseModel):
    """Single search result item.

    Represents a book work from search results with key metadata.
    """

    model_config = ConfigDict(from_attributes=True)

    title: str = Field(..., description="Book title")
    authors: list[str] = Field(default_factory=list, description="Author names")
    first_publish_year: int | None = Field(None, description="First publication year")
    cover_url: str | None = Field(None, description="Cover image URL")
    isbn_list: list[str] = Field(
        default_factory=list, description="Available ISBNs (limited)"
    )
    edition_count: int = Field(0, description="Number of editions")
    subjects: list[str] = Field(default_factory=list, description="Subject categories")
    external_work_key: str = Field(..., description="OpenLibrary work key")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "The Lord of the Rings",
                "authors": ["J. R. R. Tolkien"],
                "first_publish_year": 1954,
                "cover_url": "https://covers.openlibrary.org/b/id/258027-M.jpg",
                "isbn_list": ["9780618640157", "0618640150"],
                "edition_count": 120,
                "subjects": ["Fantasy", "Epic"],
                "external_work_key": "/works/OL27448W",
            }
        }
    )


class BookSearchResponse(BaseModel):
    """Search response with pagination info.

    Contains search results and metadata about the total results.
    """

    results: list[BookSearchResultItem] = Field(..., description="Search result items")
    total_found: int = Field(..., ge=0, description="Total matching results")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Results per page")
    has_more: bool = Field(..., description="More results available")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "results": [
                    {
                        "title": "The Lord of the Rings",
                        "authors": ["J. R. R. Tolkien"],
                        "first_publish_year": 1954,
                        "cover_url": "https://covers.openlibrary.org/b/id/258027-M.jpg",
                        "isbn_list": ["9780618640157"],
                        "edition_count": 120,
                        "subjects": ["Fantasy"],
                        "external_work_key": "/works/OL27448W",
                    }
                ],
                "total_found": 629,
                "page": 1,
                "page_size": 20,
                "has_more": True,
            }
        }
    )


# =============================================================================
# Work Details
# =============================================================================


class EditionResponse(BaseSchema):
    """Edition details response.

    Represents a specific edition of a work (ISBN-based).
    """

    id: UUID | None = Field(None, description="Internal edition ID (if stored)")
    isbn: str = Field(..., description="ISBN (10 or 13)")
    isbn_type: str = Field(..., description="ISBN type: 'isbn10' or 'isbn13'")
    title: str = Field(..., description="Edition-specific title")
    publisher: str | None = Field(None, description="Publisher name")
    publish_year: int | None = Field(None, description="Publication year")
    language: str = Field("eng", description="Language code")
    cover_url: str | None = Field(None, description="Cover image URL")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "01234567-89ab-cdef-0123-456789abcdef",
                "isbn": "9780618640157",
                "isbn_type": "isbn13",
                "title": "The Lord of the Rings: 50th Anniversary Edition",
                "publisher": "Houghton Mifflin",
                "publish_year": 2004,
                "language": "eng",
                "cover_url": "https://covers.openlibrary.org/b/isbn/9780618640157-M.jpg",
            }
        }
    )


class WorkResponse(BaseSchema):
    """Work details response.

    Contains full work metadata including all editions.
    """

    id: UUID | None = Field(None, description="Internal work ID (if stored)")
    title: str = Field(..., description="Work title")
    authors: list[str] = Field(default_factory=list, description="Author names")
    description: str | None = Field(None, description="Work description")
    subjects: list[str] = Field(default_factory=list, description="Subject categories")
    first_publish_year: int | None = Field(None, description="First publication year")
    cover_url: str | None = Field(None, description="Cover image URL")
    edition_count: int = Field(0, description="Total edition count")
    external_work_key: str = Field(..., description="OpenLibrary work key")
    editions: list[EditionResponse] = Field(
        default_factory=list, description="Available editions"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": None,
                "title": "The Lord of the Rings",
                "authors": ["J. R. R. Tolkien"],
                "description": "An epic fantasy novel...",
                "subjects": ["Fantasy", "Adventure"],
                "first_publish_year": 1954,
                "cover_url": "https://covers.openlibrary.org/b/id/258027-M.jpg",
                "edition_count": 120,
                "external_work_key": "/works/OL27448W",
                "editions": [],
            }
        }
    )


# =============================================================================
# Processing Requests
# =============================================================================


class ProcessBookRequest(BaseSchema):
    """Request to process a book into an audiobook.

    Either edition_id OR isbn must be provided (not both).
    """

    edition_id: UUID | None = Field(
        None, description="Internal edition UUID (if already in library)"
    )
    isbn: str | None = Field(
        None,
        min_length=10,
        max_length=17,
        description="ISBN to process (10 or 13 digits)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"isbn": "9780618640157"},
        }
    )


class JobResponse(BaseSchema):
    """Job creation response.

    Returned when a background job is queued.
    """

    job_id: str = Field(..., description="Background job ID")
    status: str = Field(..., description="Job status")
    message: str = Field(..., description="Status message")
    edition_id: UUID | None = Field(None, description="Edition being processed")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "arq:job:abc123",
                "status": "queued",
                "message": "Audiobook generation queued",
                "edition_id": "01234567-89ab-cdef-0123-456789abcdef",
            }
        }
    )


class RefreshBookRequest(BaseSchema):
    """Request to refresh an audiobook.

    Optionally specify a new edition to use.
    """

    new_edition_id: UUID | None = Field(
        None, description="New edition to use (optional)"
    )
    force: bool = Field(False, description="Force refresh even if no changes detected")


# =============================================================================
# AudioBook Response (for GET operations)
# =============================================================================


class ChapterSummary(BaseSchema):
    """Chapter summary in audiobook response."""

    chapter_number: int = Field(..., ge=1, description="Chapter order")
    title: str = Field(..., description="Chapter title")
    summary: str | None = Field(None, description="Chapter summary")
    audio_url: str | None = Field(None, description="Audio file URL")
    duration_seconds: int | None = Field(None, description="Audio duration")


class AudioBookResponse(BaseSchema):
    """AudioBook details response."""

    id: UUID = Field(..., description="AudioBook ID")
    edition_id: UUID = Field(..., description="Source edition ID")
    status: str = Field(..., description="Processing status")
    voice_id: str | None = Field(None, description="TTS voice used")
    total_duration_seconds: int | None = Field(None, description="Total duration")
    chapters: list[ChapterSummary] = Field(
        default_factory=list, description="Chapter list"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
