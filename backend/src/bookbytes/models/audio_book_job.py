"""AudioBookJob relation - links jobs to audiobooks.

This relation table maintains the link between generic jobs
and audiobook domain entities, keeping the Job model pure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bookbytes.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from bookbytes.models.audio_book import AudioBook
    from bookbytes.models.job import Job


class AudioBookJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Relation between Job and AudioBook.

    Links a generic job to an audiobook. One job can be associated
    with one audiobook (1:1 via unique constraint on job_id).

    Using CASCADE delete on both FKs:
    - If job is deleted, this link is deleted
    - If audiobook is deleted, this link is deleted

    Attributes:
        job_id: Foreign key to the generic job
        audio_book_id: Foreign key to the audiobook being processed
    """

    __tablename__ = "audio_book_jobs"

    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # 1 job : 1 audiobook
        index=True,
    )
    audio_book_id: Mapped[UUID] = mapped_column(
        ForeignKey("audio_books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    job: Mapped[Job] = relationship("Job", lazy="joined")
    audio_book: Mapped[AudioBook] = relationship("AudioBook", lazy="joined")

    def __repr__(self) -> str:
        return (
            f"<AudioBookJob(job_id={self.job_id}, audio_book_id={self.audio_book_id})>"
        )
