"""Work model - represents a book across all editions.

This is the top-level entity in our library hierarchy:
Work -> Edition -> AudioBook -> Chapter

Works are provider-agnostic - external provider IDs are stored
in the BookProvider table for decoupling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bookbytes.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from bookbytes.models.book_provider import BookProvider
    from bookbytes.models.edition import Edition


class Work(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A book work spanning all editions.

    Example: "The Lord of the Rings" is one Work, but may have many Editions
    (hardcover 1954, paperback 1965, anniversary edition 2004, etc.).

    Attributes:
        title: Primary title of the work
        authors: List of author names (JSON array)
        first_publish_year: Year of first publication (if known)
        subjects: Topic/genre classifications (JSON array)
        cover_url: URL to cover image (if available)
    """

    __tablename__ = "works"

    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    authors: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    first_publish_year: Mapped[int | None] = mapped_column(nullable=True)
    subjects: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Relationships
    editions: Mapped[list[Edition]] = relationship(
        "Edition",
        back_populates="work",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    book_providers: Mapped[list[BookProvider]] = relationship(
        "BookProvider",
        back_populates="work",
        cascade="all, delete-orphan",
        foreign_keys="BookProvider.work_id",
    )

    def __repr__(self) -> str:
        return f"<Work(id={self.id}, title='{self.title}', authors={self.authors})>"
