"""BookProviderRepository for managing provider mappings.

Provides CRUD operations and specialized queries for BookProvider entities.
This is a polymorphic table that maps our internal UUIDs to external provider IDs.
"""

from uuid import UUID

from sqlalchemy import select

from bookbytes.models.book_provider import BookProvider
from bookbytes.repositories.base import BaseRepository


class BookProviderRepository(BaseRepository[BookProvider]):
    """Repository for BookProvider (external ID mapping) entities."""

    async def get_by_provider_key(
        self,
        provider: str,
        external_key: str,
    ) -> BookProvider | None:
        """Find a mapping by provider and external key.

        Args:
            provider: Provider name (e.g., "openlibrary")
            external_key: External ID (e.g., "/works/OL27448W")

        Returns:
            BookProvider mapping if found, None otherwise
        """
        result = await self.session.execute(
            select(BookProvider)
            .where(BookProvider.provider == provider)
            .where(BookProvider.external_key == external_key)
        )
        return result.scalar_one_or_none()

    async def get_for_work(self, work_id: UUID) -> list[BookProvider]:
        """Get all provider mappings for a work.

        Args:
            work_id: Work UUID

        Returns:
            List of provider mappings
        """
        result = await self.session.execute(
            select(BookProvider)
            .where(BookProvider.entity_type == "work")
            .where(BookProvider.work_id == work_id)
        )
        return list(result.scalars().all())

    async def get_for_edition(self, edition_id: UUID) -> list[BookProvider]:
        """Get all provider mappings for an edition.

        Args:
            edition_id: Edition UUID

        Returns:
            List of provider mappings
        """
        result = await self.session.execute(
            select(BookProvider)
            .where(BookProvider.entity_type == "edition")
            .where(BookProvider.edition_id == edition_id)
        )
        return list(result.scalars().all())

    async def create_work_mapping(
        self,
        work_id: UUID,
        provider: str,
        external_key: str,
        provider_metadata: dict | None = None,
    ) -> BookProvider:
        """Create a provider mapping for a work.

        Args:
            work_id: Work UUID
            provider: Provider name
            external_key: External ID
            provider_metadata: Optional extra provider data

        Returns:
            Created BookProvider mapping
        """
        mapping = BookProvider(
            entity_type="work",
            entity_id=work_id,
            work_id=work_id,
            edition_id=None,
            provider=provider,
            external_key=external_key,
            provider_metadata=provider_metadata,
        )
        return await self.create(mapping)

    async def create_edition_mapping(
        self,
        edition_id: UUID,
        provider: str,
        external_key: str,
        provider_metadata: dict | None = None,
    ) -> BookProvider:
        """Create a provider mapping for an edition.

        Args:
            edition_id: Edition UUID
            provider: Provider name
            external_key: External ID
            provider_metadata: Optional extra provider data

        Returns:
            Created BookProvider mapping
        """
        mapping = BookProvider(
            entity_type="edition",
            entity_id=edition_id,
            work_id=None,
            edition_id=edition_id,
            provider=provider,
            external_key=external_key,
            provider_metadata=provider_metadata,
        )
        return await self.create(mapping)

    async def provider_key_exists(
        self,
        provider: str,
        external_key: str,
    ) -> bool:
        """Check if a provider key already exists.

        Args:
            provider: Provider name
            external_key: External ID

        Returns:
            True if exists
        """
        result = await self.session.execute(
            select(BookProvider.id)
            .where(BookProvider.provider == provider)
            .where(BookProvider.external_key == external_key)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None
