"""AudioBookJob repository for job-audiobook relations.

Provides operations to link jobs to audiobooks and query jobs
for a specific audiobook.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from bookbytes.models.audio_book_job import AudioBookJob
from bookbytes.models.job import Job
from bookbytes.repositories.base import BaseRepository


class AudioBookJobRepository(BaseRepository[AudioBookJob]):
    """Repository for AudioBookJob relation model.

    Manages the link between generic jobs and audiobooks.
    """

    async def create_link(
        self,
        job_id: UUID,
        audio_book_id: UUID,
    ) -> AudioBookJob:
        """Create a link between a job and an audiobook.

        Args:
            job_id: The job's UUID
            audio_book_id: The audiobook's UUID

        Returns:
            The created AudioBookJob link
        """
        link = AudioBookJob(job_id=job_id, audio_book_id=audio_book_id)
        self.session.add(link)
        await self.session.commit()
        await self.session.refresh(link)
        return link

    async def get_by_job_id(self, job_id: UUID) -> AudioBookJob | None:
        """Get the link for a specific job.

        Args:
            job_id: The job's UUID

        Returns:
            The link if found, None otherwise
        """
        query = (
            select(AudioBookJob)
            .where(AudioBookJob.job_id == job_id)
            .options(joinedload(AudioBookJob.audio_book))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_jobs_for_audiobook(
        self,
        audio_book_id: UUID,
        limit: int = 50,
    ) -> list[Job]:
        """Get all jobs associated with an audiobook.

        Args:
            audio_book_id: The audiobook's UUID
            limit: Maximum number of results

        Returns:
            List of jobs for this audiobook, newest first
        """
        query = (
            select(Job)
            .join(AudioBookJob, AudioBookJob.job_id == Job.id)
            .where(AudioBookJob.audio_book_id == audio_book_id)
            .order_by(Job.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_latest_job_for_audiobook(
        self,
        audio_book_id: UUID,
    ) -> Job | None:
        """Get the most recent job for an audiobook.

        Args:
            audio_book_id: The audiobook's UUID

        Returns:
            The latest job, or None if no jobs exist
        """
        query = (
            select(Job)
            .join(AudioBookJob, AudioBookJob.job_id == Job.id)
            .where(AudioBookJob.audio_book_id == audio_book_id)
            .order_by(Job.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
