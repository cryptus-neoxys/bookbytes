"""AudioBookRepository for managing AudioBook entities.

Uses SoftDeleteRepository for soft delete support - audiobooks are never
permanently deleted to preserve history.
"""

from uuid import UUID

from sqlalchemy import select

from bookbytes.models.audio_book import AudioBook, AudioBookStatus
from bookbytes.repositories.base import SoftDeleteRepository


class AudioBookRepository(SoftDeleteRepository[AudioBook]):
    """Repository for AudioBook entities with soft delete support."""

    async def get_by_edition(
        self,
        edition_id: UUID,
        *,
        include_deleted: bool = False,
    ) -> AudioBook | None:
        """Find an audiobook for a specific edition.

        Args:
            edition_id: Edition UUID
            include_deleted: If True, include soft-deleted audiobooks

        Returns:
            AudioBook if found, None otherwise
        """
        query = select(AudioBook).where(AudioBook.edition_id == edition_id)

        if not include_deleted:
            query = query.where(AudioBook.deleted_at.is_(None))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_status(
        self,
        status: AudioBookStatus,
        *,
        offset: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
    ) -> list[AudioBook]:
        """Get audiobooks by processing status.

        Args:
            status: Processing status to filter by
            offset: Pagination offset
            limit: Maximum results
            include_deleted: If True, include soft-deleted audiobooks

        Returns:
            List of audiobooks with the given status
        """
        query = select(AudioBook).where(AudioBook.status == status.value)

        if not include_deleted:
            query = query.where(AudioBook.deleted_at.is_(None))

        result = await self.session.execute(query.offset(offset).limit(limit))
        return list(result.scalars().all())

    async def get_pending(self, *, limit: int = 100) -> list[AudioBook]:
        """Get audiobooks pending processing.

        Args:
            limit: Maximum results

        Returns:
            List of pending audiobooks
        """
        return await self.get_by_status(
            AudioBookStatus.PENDING,
            limit=limit,
        )

    async def get_processing(self, *, limit: int = 100) -> list[AudioBook]:
        """Get audiobooks currently being processed.

        Args:
            limit: Maximum results

        Returns:
            List of processing audiobooks
        """
        return await self.get_by_status(
            AudioBookStatus.PROCESSING,
            limit=limit,
        )

    async def mark_processing(self, audiobook: AudioBook) -> AudioBook:
        """Mark an audiobook as processing.

        Args:
            audiobook: AudioBook to update

        Returns:
            Updated audiobook
        """
        audiobook.status = AudioBookStatus.PROCESSING.value
        return await self.update(audiobook)

    async def mark_completed(self, audiobook: AudioBook) -> AudioBook:
        """Mark an audiobook as completed.

        Args:
            audiobook: AudioBook to update

        Returns:
            Updated audiobook
        """
        audiobook.status = AudioBookStatus.COMPLETED.value
        audiobook.error_message = None
        return await self.update(audiobook)

    async def mark_failed(
        self,
        audiobook: AudioBook,
        error_message: str,
    ) -> AudioBook:
        """Mark an audiobook as failed with error message.

        Args:
            audiobook: AudioBook to update
            error_message: Error details

        Returns:
            Updated audiobook
        """
        audiobook.status = AudioBookStatus.FAILED.value
        audiobook.error_message = error_message
        return await self.update(audiobook)

    async def increment_version(self, audiobook: AudioBook) -> AudioBook:
        """Increment audiobook version for refresh/regeneration.

        Args:
            audiobook: AudioBook to update

        Returns:
            Updated audiobook with incremented version
        """
        audiobook.version += 1
        audiobook.status = AudioBookStatus.PENDING.value
        audiobook.error_message = None
        return await self.update(audiobook)
