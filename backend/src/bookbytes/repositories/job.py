"""Job repository with worker-safe operations.

Provides CRUD operations for jobs with atomic claim, progress updates,
and status transitions. Uses optimistic locking for concurrency control.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update

from bookbytes.models.job import Job, JobStatus, JobType
from bookbytes.repositories.base import BaseRepository


class JobRepository(BaseRepository[Job]):
    """Repository for Job model with worker-safe operations.

    Provides atomic operations for job claiming and status updates
    to ensure safe concurrent access from multiple workers.
    """

    async def claim_next(
        self,
        worker_id: str,
        job_type: str | None = None,
    ) -> Job | None:
        """Atomically claim the next pending job.

        Uses optimistic locking via version column to prevent
        race conditions when multiple workers try to claim jobs.

        Args:
            worker_id: Identifier of the claiming worker
            job_type: Optional filter by job type

        Returns:
            The claimed job, or None if no jobs available
        """
        # Find oldest pending job
        query = (
            select(Job)
            .where(Job.status == JobStatus.PENDING.value)
            .order_by(Job.created_at)
            .limit(1)
        )

        if job_type:
            query = query.where(Job.job_type == job_type)

        result = await self.session.execute(query)
        job = result.scalar_one_or_none()

        if not job:
            return None

        # Atomically claim with optimistic lock
        stmt = (
            update(Job)
            .where(Job.id == job.id)
            .where(Job.version == job.version)  # Optimistic lock
            .values(
                status=JobStatus.PROCESSING.value,
                worker_id=worker_id,
                started_at=datetime.now(UTC),
                version=job.version + 1,
            )
            .returning(Job)
        )

        result = await self.session.execute(stmt)
        claimed = result.scalar_one_or_none()

        if claimed:
            await self.session.commit()

        return claimed

    async def update_progress(
        self,
        job_id: UUID,
        progress: int,
        current_step: str | None = None,
    ) -> bool:
        """Update job progress.

        Args:
            job_id: The job's UUID
            progress: Progress percentage (0-100)
            current_step: Optional human-readable step description

        Returns:
            True if update succeeded, False if job not found
        """
        values: dict[str, int | str | None] = {"progress": min(100, max(0, progress))}
        if current_step is not None:
            values["current_step"] = current_step

        stmt = update(Job).where(Job.id == job_id).values(**values)
        result = await self.session.execute(stmt)
        await self.session.commit()

        return result.rowcount > 0

    async def mark_completed(self, job_id: UUID) -> bool:
        """Mark job as completed.

        Args:
            job_id: The job's UUID

        Returns:
            True if update succeeded
        """
        stmt = (
            update(Job)
            .where(Job.id == job_id)
            .values(
                status=JobStatus.COMPLETED.value,
                progress=100,
                completed_at=datetime.now(UTC),
            )
        )
        result = await self.session.execute(stmt)
        await self.session.commit()

        return result.rowcount > 0

    async def mark_failed(
        self,
        job_id: UUID,
        error_message: str,
        error_code: str | None = None,
    ) -> bool:
        """Mark job as failed with error details.

        Args:
            job_id: The job's UUID
            error_message: Human-readable error message
            error_code: Optional machine-readable error code

        Returns:
            True if update succeeded
        """
        stmt = (
            update(Job)
            .where(Job.id == job_id)
            .values(
                status=JobStatus.FAILED.value,
                error_message=error_message[:2000],  # Truncate to fit
                error_code=error_code[:50] if error_code else None,
                completed_at=datetime.now(UTC),
            )
        )
        result = await self.session.execute(stmt)
        await self.session.commit()

        return result.rowcount > 0

    async def schedule_retry(self, job_id: UUID) -> bool:
        """Schedule a failed job for retry.

        Increments retry_count and sets status back to pending.

        Args:
            job_id: The job's UUID

        Returns:
            True if retry scheduled, False if max retries exceeded
        """
        # Get current job state
        job = await self.get_by_id(job_id)
        if not job or not job.can_retry:
            return False

        stmt = (
            update(Job)
            .where(Job.id == job_id)
            .values(
                status=JobStatus.PENDING.value,
                retry_count=job.retry_count + 1,
                worker_id=None,
                started_at=None,
                completed_at=None,
                error_message=None,
                error_code=None,
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()

        return True

    async def get_by_status(
        self,
        status: JobStatus,
        limit: int = 100,
    ) -> list[Job]:
        """Get jobs by status.

        Args:
            status: The status to filter by
            limit: Maximum number of results

        Returns:
            List of jobs with the given status
        """
        query = (
            select(Job)
            .where(Job.status == status.value)
            .order_by(Job.created_at)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_count(self) -> int:
        """Get count of pending jobs (for monitoring).

        Returns:
            Number of pending jobs
        """
        query = (
            select(func.count())
            .select_from(Job)
            .where(Job.status == JobStatus.PENDING.value)
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_by_job_type(
        self,
        job_type: JobType,
        limit: int = 100,
    ) -> list[Job]:
        """Get jobs by type.

        Args:
            job_type: The job type to filter by
            limit: Maximum number of results

        Returns:
            List of jobs of the given type
        """
        query = (
            select(Job)
            .where(Job.job_type == job_type.value)
            .order_by(Job.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
