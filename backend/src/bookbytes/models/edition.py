"""Edition model - represents a specific ISBN/format of a Work.

A Work can have many Editions (hardcover, paperback, different years, languages).
Each Edition has a unique ISBN and can have one AudioBook generated for it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bookbytes.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from bookbytes.models.audio_book import AudioBook
    from bookbytes.models.book_provider import BookProvider
    from bookbytes.models.work import Work


class Edition(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A specific edition of a book work.

    Example: "The Lord of the Rings" hardcover 1954 edition with ISBN 0-618-00222-7.

    Attributes:
        work_id: Foreign key to parent Work
        isbn: Normalized ISBN (10 or 13 digits, no dashes)
        isbn_type: "isbn10" or "isbn13"
        title: Edition-specific title (may differ from Work title)
        publisher: Publisher name
        publish_year: Year this edition was published
        language: ISO 639-2 language code (default: "eng")
        pages: Page count
    """

    __tablename__ = "editions"

    work_id: Mapped[UUID] = mapped_column(
        ForeignKey("works.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    isbn: Mapped[str] = mapped_column(
        String(13),
        unique=True,
        nullable=False,
        index=True,
    )
    isbn_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )  # "isbn10" or "isbn13"
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    publisher: Mapped[str | None] = mapped_column(String(200), nullable=True)
    publish_year: Mapped[int | None] = mapped_column(nullable=True, index=True)
    language: Mapped[str] = mapped_column(
        String(7), nullable=False, default="eng"
    )  # ISO 639-2/B (bibliographic) code - standard for MARC/ONIX publishing
    pages: Mapped[int | None] = mapped_column(nullable=True)

    # Relationships
    work: Mapped[Work] = relationship("Work", back_populates="editions")
    audio_book: Mapped[AudioBook | None] = relationship(
        "AudioBook",
        back_populates="edition",
        uselist=False,
        cascade="all, delete-orphan",
    )
    book_providers: Mapped[list[BookProvider]] = relationship(
        "BookProvider",
        back_populates="edition",
        cascade="all, delete-orphan",
        foreign_keys="BookProvider.edition_id",
    )

    def __repr__(self) -> str:
        return f"<Edition(id={self.id}, isbn='{self.isbn}', title='{self.title}')>"
