"""WorkRepository for managing Work entities.

Provides CRUD operations and specialized queries for Work entities.
"""

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from bookbytes.models.work import Work
from bookbytes.repositories.base import BaseRepository


class WorkRepository(BaseRepository[Work]):
    """Repository for Work entities."""

    async def get_by_title_author(
        self,
        title: str,
        authors: list[str],
    ) -> Work | None:
        """Find a work by title and author combination.

        Args:
            title: Work title (case-insensitive partial match)
            authors: List of author names

        Returns:
            Work if found, None otherwise
        """
        # Case-insensitive title match with author overlap
        result = await self.session.execute(
            select(Work)
            .where(Work.title.ilike(f"%{title}%"))
            .where(Work.authors.contains(authors))
        )
        return result.scalar_one_or_none()

    async def get_with_editions(self, work_id: Work) -> Work | None:
        """Get a work with its editions eagerly loaded.

        Args:
            work_id: Work UUID

        Returns:
            Work with editions loaded, or None
        """
        result = await self.session.execute(
            select(Work).options(selectinload(Work.editions)).where(Work.id == work_id)
        )
        return result.scalar_one_or_none()

    async def search_by_title(
        self,
        title: str,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Work]:
        """Search works by title (case-insensitive partial match).

        Args:
            title: Search term
            offset: Pagination offset
            limit: Maximum results

        Returns:
            List of matching works
        """
        result = await self.session.execute(
            select(Work)
            .where(Work.title.ilike(f"%{title}%"))
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
