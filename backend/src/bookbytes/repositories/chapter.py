"""ChapterRepository for managing Chapter entities.

Provides CRUD operations and specialized queries for Chapter entities.
"""

from uuid import UUID

from sqlalchemy import select

from bookbytes.models.chapter import Chapter
from bookbytes.repositories.base import BaseRepository


class ChapterRepository(BaseRepository[Chapter]):
    """Repository for Chapter entities."""

    async def get_by_audio_book(
        self,
        audio_book_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Chapter]:
        """Get all chapters for an audiobook, ordered by chapter number.

        Args:
            audio_book_id: AudioBook UUID
            offset: Pagination offset
            limit: Maximum results

        Returns:
            List of chapters ordered by chapter_number
        """
        result = await self.session.execute(
            select(Chapter)
            .where(Chapter.audio_book_id == audio_book_id)
            .order_by(Chapter.chapter_number)
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_number(
        self,
        audio_book_id: UUID,
        chapter_number: int,
    ) -> Chapter | None:
        """Get a specific chapter by audiobook and chapter number.

        Args:
            audio_book_id: AudioBook UUID
            chapter_number: Chapter number (1-indexed)

        Returns:
            Chapter if found, None otherwise
        """
        result = await self.session.execute(
            select(Chapter)
            .where(Chapter.audio_book_id == audio_book_id)
            .where(Chapter.chapter_number == chapter_number)
        )
        return result.scalar_one_or_none()

    async def count_by_audio_book(self, audio_book_id: UUID) -> int:
        """Count chapters for an audiobook.

        Args:
            audio_book_id: AudioBook UUID

        Returns:
            Number of chapters
        """
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.count())
            .select_from(Chapter)
            .where(Chapter.audio_book_id == audio_book_id)
        )
        return result.scalar_one()

    async def get_total_duration(self, audio_book_id: UUID) -> int:
        """Get total duration of all chapters in seconds.

        Args:
            audio_book_id: AudioBook UUID

        Returns:
            Total duration in seconds
        """
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.coalesce(func.sum(Chapter.duration_seconds), 0)).where(
                Chapter.audio_book_id == audio_book_id
            )
        )
        return result.scalar_one()

    async def delete_all_for_audio_book(self, audio_book_id: UUID) -> int:
        """Delete all chapters for an audiobook (for regeneration).

        Args:
            audio_book_id: AudioBook UUID

        Returns:
            Number of chapters deleted
        """
        from sqlalchemy import delete

        result = await self.session.execute(
            delete(Chapter).where(Chapter.audio_book_id == audio_book_id)
        )
        await self.session.flush()
        return result.rowcount
