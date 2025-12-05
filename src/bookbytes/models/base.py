"""SQLAlchemy Base model and common mixins.

This module provides:
- Base: Declarative base for all models
- UUIDPrimaryKeyMixin: UUID primary key for all entities
- TimestampMixin: created_at and updated_at columns

Usage:
    from bookbytes.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin

    class MyModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
        __tablename__ = "my_table"
        name: Mapped[str]
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    All models should inherit from this class to be included in migrations.
    """

    pass


class UUIDPrimaryKeyMixin:
    """Mixin that adds a UUID primary key column.

    All entities should use UUID as primary key for:
    - Security (not guessable)
    - Distributed ID generation (no central sequence)
    - URL-safe identifiers
    """

    @declared_attr
    def id(cls) -> Mapped[uuid.UUID]:
        return mapped_column(
            primary_key=True,
            default=uuid.uuid4,
            nullable=False,
        )


class TimestampMixin:
    """Mixin that adds created_at and updated_at columns.

    - created_at: Set automatically on insert
    - updated_at: Set automatically on insert and update
    """

    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        )

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        )


class SoftDeleteMixin:
    """Mixin that adds soft delete support via deleted_at timestamp.

    Instead of permanently deleting records, this marks them with a timestamp.
    Queries should filter out soft-deleted records by default.

    - deleted_at: Nullable timestamp, NULL means not deleted
    """

    @declared_attr
    def deleted_at(cls) -> Mapped[datetime | None]:
        return mapped_column(
            DateTime(timezone=True),
            nullable=True,
            default=None,
            index=True,  # Index for efficient filtering
        )

    @property
    def is_deleted(self) -> bool:
        """Check if this entity has been soft-deleted."""
        return self.deleted_at is not None

    def mark_deleted(self) -> None:
        """Mark this entity as soft-deleted."""
        from datetime import UTC, datetime

        self.deleted_at = datetime.now(UTC)

    def restore(self) -> None:
        """Restore a soft-deleted entity."""
        self.deleted_at = None
