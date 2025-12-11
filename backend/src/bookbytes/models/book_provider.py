"""BookProvider model - maps internal entities to external provider IDs.

This is a polymorphic table that can link either Works or Editions to
external providers like OpenLibrary, Google Books, etc.

Benefits:
- Provider-agnostic core models (no openlibrary_key on Work/Edition)
- Easy to add new providers without migrations
- Same Work/Edition can have IDs from multiple providers
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import JSON, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bookbytes.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from bookbytes.models.edition import Edition
    from bookbytes.models.work import Work


class BookProviderType(str, Enum):
    """Supported external data providers."""

    OPENLIBRARY = "openlibrary"
    GOOGLE_BOOKS = "google_books"
    # Future: AMAZON, GOODREADS, etc.


class BookProvider(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Maps internal UUIDs to external provider IDs.

    This is a sparse/polymorphic table - either work_id OR edition_id is set,
    never both.

    Attributes:
        entity_type: "work" or "edition" - which table this maps to
        entity_id: The UUID of the Work or Edition
        provider: Provider name (e.g., "openlibrary")
        external_key: Provider's ID (e.g., "/works/OL27448W")
        provider_metadata: Optional JSON with extra provider-specific data
        work_id: FK to works table (nullable, set when entity_type="work")
        edition_id: FK to editions table (nullable, set when entity_type="edition")
    """

    __tablename__ = "book_providers"

    # Entity mapping
    entity_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # "work" or "edition"
    entity_id: Mapped[UUID] = mapped_column(nullable=False)

    # Provider info
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    external_key: Mapped[str] = mapped_column(String(200), nullable=False)

    # Optional provider-specific metadata
    provider_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships (nullable - only one will be set based on entity_type)
    work_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("works.id", ondelete="CASCADE"),
        nullable=True,
    )
    edition_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("editions.id", ondelete="CASCADE"),
        nullable=True,
    )

    work: Mapped[Work | None] = relationship(
        "Work",
        back_populates="book_providers",
        foreign_keys=[work_id],
    )
    edition: Mapped[Edition | None] = relationship(
        "Edition",
        back_populates="book_providers",
        foreign_keys=[edition_id],
    )

    __table_args__ = (
        # Each provider key should be unique globally
        UniqueConstraint("provider", "external_key", name="uq_provider_external_key"),
        # Index for looking up all providers for an entity
        Index("ix_book_providers_entity_lookup", "entity_type", "entity_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<BookProvider(provider='{self.provider}', "
            f"key='{self.external_key}', entity_type='{self.entity_type}')>"
        )
