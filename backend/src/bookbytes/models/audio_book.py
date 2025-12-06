"""AudioBook model - our generated audiobook content.

AudioBook is the core output entity - it represents our generated audio
content for a specific Edition. Uses soft delete to preserve history.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bookbytes.models.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from bookbytes.models.chapter import Chapter
    from bookbytes.models.edition import Edition


class AudioBookStatus(str, Enum):
    """Processing status for audiobook generation."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AudioBook(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Generated audiobook for a specific edition.

    Created when a user requests audiobook generation for an Edition.
    Uses SoftDeleteMixin for soft delete support (preserves history).

    Attributes:
        edition_id: Foreign key to the Edition this audiobook is for
        status: Processing status (pending, processing, completed, failed)
        version: Version number (incremented on refresh/regeneration)
        error_message: Error details if status is "failed"
    """

    __tablename__ = "audio_books"

    edition_id: Mapped[UUID] = mapped_column(
        ForeignKey("editions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AudioBookStatus.PENDING.value,
        index=True,
    )
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Relationships
    edition: Mapped[Edition] = relationship("Edition", back_populates="audio_book")
    chapters: Mapped[list[Chapter]] = relationship(
        "Chapter",
        back_populates="audio_book",
        cascade="all, delete-orphan",
        order_by="Chapter.chapter_number",
    )

    def __repr__(self) -> str:
        return (
            f"<AudioBook(id={self.id}, edition_id={self.edition_id}, "
            f"status='{self.status}', version={self.version})>"
        )
