"""Chapter model - audio content for a book chapter.

Chapters belong to an AudioBook and contain the generated summary
and audio file references.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bookbytes.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from bookbytes.models.audio_book import AudioBook


class Chapter(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A chapter within an audiobook.

    Contains the generated summary text and audio file references.

    Attributes:
        audio_book_id: Foreign key to parent AudioBook
        chapter_number: Sequential number within the book (1-indexed)
        title: Chapter title
        summary: Generated chapter summary text
        audio_file_path: Local/S3 path to audio file
        audio_url: Public URL for streaming
        word_count: Number of words in summary
        duration_seconds: Audio duration in seconds
    """

    __tablename__ = "chapters"

    audio_book_id: Mapped[UUID] = mapped_column(
        ForeignKey("audio_books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chapter_number: Mapped[int] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    audio_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    audio_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    word_count: Mapped[int | None] = mapped_column(nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(nullable=True)

    # Relationships
    audio_book: Mapped[AudioBook] = relationship("AudioBook", back_populates="chapters")

    __table_args__ = (
        # Each chapter number must be unique within an audiobook
        UniqueConstraint(
            "audio_book_id", "chapter_number", name="uq_chapter_audio_book_number"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Chapter(id={self.id}, audio_book_id={self.audio_book_id}, "
            f"number={self.chapter_number}, title='{self.title}')>"
        )
