"""Job model - generic background job tracking.

Job is a fully generic table with no domain-specific columns.
Domain entities link to jobs via relation tables (e.g., audio_book_jobs).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from bookbytes.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class JobStatus(str, Enum):
    """Processing status for background jobs."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobType(str, Enum):
    """Types of background jobs.

    Extend this enum as new job types are added.
    """

    AUDIOBOOK_GENERATION = "audiobook_generation"
    AUDIOBOOK_REFRESH = "audiobook_refresh"


class Job(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Generic background job tracking.

    This model is intentionally domain-agnostic. Domain entities
    (e.g., AudioBook) link to jobs via relation tables.

    State Machine:
        pending → processing → completed
                           ↘ failed → pending (retry)

    Attributes:
        job_type: Type of job (e.g., audiobook_generation)
        status: Current status (pending, processing, completed, failed)
        progress: Completion percentage (0-100)
        current_step: Human-readable current step description
        error_message: Error details if status is failed
        error_code: Machine-readable error code
        version: Optimistic lock for concurrent access
        worker_id: Identifier of worker processing this job
        retry_count: Number of retry attempts
        max_retries: Maximum allowed retries
        started_at: When processing started
        completed_at: When processing finished (success or failure)
    """

    __tablename__ = "jobs"

    # === Core (Generic) ===
    job_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=JobStatus.PENDING.value,
        index=True,
    )

    # === Progress Tracking ===
    progress: Mapped[int] = mapped_column(nullable=False, default=0)
    current_step: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # === Error Handling ===
    error_message: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # === Concurrency Control ===
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    worker_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # === Retry Tracking ===
    retry_count: Mapped[int] = mapped_column(nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(nullable=False, default=3)

    # === Timestamps ===
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return (
            f"<Job(id={self.id}, type='{self.job_type}', "
            f"status='{self.status}', progress={self.progress}%)>"
        )

    @property
    def is_terminal(self) -> bool:
        """Check if job is in a terminal state (completed or failed)."""
        return self.status in (JobStatus.COMPLETED.value, JobStatus.FAILED.value)

    @property
    def can_retry(self) -> bool:
        """Check if job can be retried."""
        return (
            self.status == JobStatus.FAILED.value
            and self.retry_count < self.max_retries
        )
