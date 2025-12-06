"""EditionRepository for managing Edition entities.

Provides CRUD operations and specialized queries for Edition entities.
"""

from uuid import UUID

from sqlalchemy import select

from bookbytes.models.edition import Edition
from bookbytes.repositories.base import BaseRepository


class EditionRepository(BaseRepository[Edition]):
    """Repository for Edition entities."""

    async def get_by_isbn(self, isbn: str) -> Edition | None:
        """Find an edition by its normalized ISBN.

        Args:
            isbn: Normalized ISBN (10 or 13 digits, no dashes)

        Returns:
            Edition if found, None otherwise
        """
        result = await self.session.execute(select(Edition).where(Edition.isbn == isbn))
        return result.scalar_one_or_none()

    async def get_by_work_id(
        self,
        work_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Edition]:
        """Get all editions for a work.

        Args:
            work_id: Work UUID
            offset: Pagination offset
            limit: Maximum results

        Returns:
            List of editions
        """
        result = await self.session.execute(
            select(Edition)
            .where(Edition.work_id == work_id)
            .order_by(Edition.publish_year.desc().nulls_last())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_latest_by_work(
        self,
        work_id: UUID,
        language: str = "eng",
    ) -> Edition | None:
        """Get the latest edition of a work by publish year.

        Args:
            work_id: Work UUID
            language: ISO 639-2/B language code (default: "eng")

        Returns:
            Latest edition or None
        """
        result = await self.session.execute(
            select(Edition)
            .where(Edition.work_id == work_id)
            .where(Edition.language == language)
            .order_by(Edition.publish_year.desc().nulls_last())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def isbn_exists(self, isbn: str) -> bool:
        """Check if an ISBN already exists in the library.

        Args:
            isbn: Normalized ISBN

        Returns:
            True if exists
        """
        result = await self.session.execute(
            select(Edition.id).where(Edition.isbn == isbn).limit(1)
        )
        return result.scalar_one_or_none() is not None
