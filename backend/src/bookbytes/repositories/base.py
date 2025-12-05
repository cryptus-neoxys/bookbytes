"""Generic base repository with async CRUD operations and soft delete support.

This module provides a generic repository pattern for SQLAlchemy models:
- BaseRepository[T]: Generic class for standard CRUD operations
- SoftDeleteRepository[T]: Repository with soft delete support
- All methods are async and use SQLAlchemy 2.0 style

Usage:
    from bookbytes.repositories.base import BaseRepository, SoftDeleteRepository
    from bookbytes.models.book import Book

    # For models without soft delete
    class JobRepository(BaseRepository[Job]):
        pass

    # For models with SoftDeleteMixin
    class BookRepository(SoftDeleteRepository[Book]):
        pass

    # Usage
    repo = BookRepository(session)
    book = await repo.get_by_id(book_id)
    books = await repo.get_all(offset=0, limit=10)
    await repo.soft_delete(book)  # Sets deleted_at instead of removing
"""

from datetime import UTC, datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bookbytes.models.base import Base, SoftDeleteMixin

# Type variable for model classes
T = TypeVar("T", bound=Base)

# Type variable for soft-deletable models
S = TypeVar("S", bound=SoftDeleteMixin)


class BaseRepository(Generic[T]):
    """Generic repository providing async CRUD operations.

    This base class provides standard database operations that can be
    inherited by specific repositories. It uses SQLAlchemy 2.0 style
    async queries.

    Type Parameters:
        T: The SQLAlchemy model class

    Attributes:
        session: The async database session
        model_class: The model class for this repository
    """

    model_class: type[T]

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session: Async database session
        """
        self.session = session

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Extract model class from Generic type parameter."""
        super().__init_subclass__(**kwargs)
        # Get the model class from the type parameter
        for base in cls.__orig_bases__:  # type: ignore[attr-defined]
            if hasattr(base, "__args__"):
                cls.model_class = base.__args__[0]
                break

    async def get_by_id(self, id: UUID) -> T | None:
        """Get a single entity by its UUID.

        Args:
            id: The entity's UUID

        Returns:
            The entity if found, None otherwise
        """
        result = await self.session.execute(
            select(self.model_class).where(self.model_class.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[T]:
        """Get all entities with pagination.

        Args:
            offset: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of entities
        """
        result = await self.session.execute(
            select(self.model_class).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        """Count total entities.

        Returns:
            Total count
        """
        result = await self.session.execute(
            select(func.count()).select_from(self.model_class)
        )
        return result.scalar_one()

    async def create(self, entity: T) -> T:
        """Create a new entity.

        Args:
            entity: The entity to create

        Returns:
            The created entity with generated fields (id, timestamps)
        """
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def create_many(self, entities: list[T]) -> list[T]:
        """Create multiple entities in bulk.

        Args:
            entities: List of entities to create

        Returns:
            List of created entities
        """
        self.session.add_all(entities)
        await self.session.flush()
        for entity in entities:
            await self.session.refresh(entity)
        return entities

    async def update(self, entity: T) -> T:
        """Update an existing entity.

        Args:
            entity: The entity with updated fields

        Returns:
            The updated entity
        """
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def hard_delete(self, entity: T) -> None:
        """Permanently delete an entity from the database.

        WARNING: This is a hard delete. For soft delete, use SoftDeleteRepository.

        Args:
            entity: The entity to permanently delete
        """
        await self.session.delete(entity)
        await self.session.flush()

    async def hard_delete_by_id(self, id: UUID) -> bool:
        """Permanently delete an entity by its UUID.

        WARNING: This is a hard delete. For soft delete, use SoftDeleteRepository.

        Args:
            id: The entity's UUID

        Returns:
            True if entity was deleted, False if not found
        """
        entity = await self.get_by_id(id)
        if entity is None:
            return False
        await self.hard_delete(entity)
        return True

    async def exists(self, id: UUID) -> bool:
        """Check if an entity exists.

        Args:
            id: The entity's UUID

        Returns:
            True if exists, False otherwise
        """
        result = await self.session.execute(
            select(func.count())
            .select_from(self.model_class)
            .where(self.model_class.id == id)
        )
        return result.scalar_one() > 0


class SoftDeleteRepository(BaseRepository[T], Generic[T]):
    """Repository with soft delete support.

    This repository is for models that include SoftDeleteMixin.
    Instead of permanently deleting records, it sets the deleted_at timestamp.
    By default, queries exclude soft-deleted records.

    Type Parameters:
        T: The SQLAlchemy model class (must include SoftDeleteMixin)
    """

    async def get_by_id(self, id: UUID, *, include_deleted: bool = False) -> T | None:
        """Get a single entity by its UUID.

        Args:
            id: The entity's UUID
            include_deleted: If True, include soft-deleted entities

        Returns:
            The entity if found, None otherwise
        """
        query = select(self.model_class).where(self.model_class.id == id)

        if not include_deleted:
            query = query.where(self.model_class.deleted_at.is_(None))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
    ) -> list[T]:
        """Get all entities with pagination.

        Args:
            offset: Number of records to skip
            limit: Maximum records to return
            include_deleted: If True, include soft-deleted entities

        Returns:
            List of entities
        """
        query = select(self.model_class)

        if not include_deleted:
            query = query.where(self.model_class.deleted_at.is_(None))

        result = await self.session.execute(query.offset(offset).limit(limit))
        return list(result.scalars().all())

    async def count(self, *, include_deleted: bool = False) -> int:
        """Count total entities.

        Args:
            include_deleted: If True, include soft-deleted entities

        Returns:
            Total count
        """
        query = select(func.count()).select_from(self.model_class)

        if not include_deleted:
            query = query.where(self.model_class.deleted_at.is_(None))

        result = await self.session.execute(query)
        return result.scalar_one()

    async def soft_delete(self, entity: T) -> T:
        """Soft delete an entity by setting deleted_at timestamp.

        Args:
            entity: The entity to soft delete

        Returns:
            The soft-deleted entity
        """
        entity.deleted_at = datetime.now(UTC)  # type: ignore[attr-defined]
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def soft_delete_by_id(self, id: UUID) -> bool:
        """Soft delete an entity by its UUID.

        Args:
            id: The entity's UUID

        Returns:
            True if entity was soft-deleted, False if not found
        """
        entity = await self.get_by_id(id, include_deleted=False)
        if entity is None:
            return False
        await self.soft_delete(entity)
        return True

    async def restore(self, entity: T) -> T:
        """Restore a soft-deleted entity.

        Args:
            entity: The entity to restore

        Returns:
            The restored entity
        """
        entity.deleted_at = None  # type: ignore[attr-defined]
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def restore_by_id(self, id: UUID) -> bool:
        """Restore a soft-deleted entity by its UUID.

        Args:
            id: The entity's UUID

        Returns:
            True if entity was restored, False if not found
        """
        entity = await self.get_by_id(id, include_deleted=True)
        if entity is None or entity.deleted_at is None:  # type: ignore[attr-defined]
            return False
        await self.restore(entity)
        return True

    async def exists(self, id: UUID, *, include_deleted: bool = False) -> bool:
        """Check if an entity exists.

        Args:
            id: The entity's UUID
            include_deleted: If True, include soft-deleted entities

        Returns:
            True if exists, False otherwise
        """
        query = (
            select(func.count())
            .select_from(self.model_class)
            .where(self.model_class.id == id)
        )

        if not include_deleted:
            query = query.where(self.model_class.deleted_at.is_(None))

        result = await self.session.execute(query)
        return result.scalar_one() > 0

    # Alias for backwards compatibility and explicit naming
    async def delete(self, entity: T) -> T:
        """Soft delete an entity (alias for soft_delete).

        Args:
            entity: The entity to soft delete

        Returns:
            The soft-deleted entity
        """
        return await self.soft_delete(entity)

    async def delete_by_id(self, id: UUID) -> bool:
        """Soft delete an entity by ID (alias for soft_delete_by_id).

        Args:
            id: The entity's UUID

        Returns:
            True if soft-deleted, False if not found
        """
        return await self.soft_delete_by_id(id)
