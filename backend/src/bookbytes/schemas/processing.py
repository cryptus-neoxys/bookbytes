"""Schemas for audiobook processing endpoints.

Request and response models for the processing pipeline including
job creation, status tracking, and audiobook refresh.
"""

from __future__ import annotations

from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProcessRequest(BaseModel):
    """Request to start audiobook processing.

    Must provide either edition_id or isbn, not both or neither.
    """

    edition_id: UUID | None = Field(
        default=None,
        description="UUID of the edition to process",
    )
    isbn: str | None = Field(
        default=None,
        description="ISBN to lookup and process (will find/create edition)",
        min_length=10,
        max_length=17,  # ISBN-13 with hyphens
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"edition_id": "01234567-89ab-cdef-0123-456789abcdef"},
                {"isbn": "978-0-13-468599-1"},
            ]
        }
    )

    @model_validator(mode="after")
    def require_exactly_one(self) -> Self:
        """Validate that exactly one of edition_id or isbn is provided."""
        has_edition = self.edition_id is not None
        has_isbn = self.isbn is not None

        if not has_edition and not has_isbn:
            msg = "Must provide either edition_id or isbn"
            raise ValueError(msg)

        if has_edition and has_isbn:
            msg = "Provide only one of edition_id or isbn, not both"
            raise ValueError(msg)

        return self


class RefreshRequest(BaseModel):
    """Request to refresh/regenerate an audiobook."""

    force: bool = Field(
        default=False,
        description="Force regeneration even if audiobook is up-to-date",
    )


class ProcessResponse(BaseModel):
    """Response after starting audiobook processing."""

    job_id: UUID = Field(description="ID of the processing job")
    audio_book_id: UUID = Field(description="ID of the audiobook being processed")
    status: str = Field(description="Initial status (typically 'pending')")
    message: str = Field(description="Human-readable status message")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "01234567-89ab-cdef-0123-456789abcdef",
                "audio_book_id": "fedcba98-7654-3210-fedc-ba9876543210",
                "status": "pending",
                "message": "Audiobook processing started",
            }
        }
    )


class JobStatusResponse(BaseModel):
    """Response for job status query."""

    id: UUID = Field(description="Job ID")
    job_type: str = Field(description="Type of job (e.g., 'audiobook_generation')")
    status: str = Field(
        description="Current status: pending, processing, completed, failed"
    )
    audio_book_id: UUID | None = Field(
        default=None,
        description="Associated audiobook ID (if applicable)",
    )
    progress: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Progress percentage (0-100)",
    )
    error_message: str | None = Field(
        default=None,
        description="Error details if status is 'failed'",
    )
    created_at: datetime = Field(description="When the job was created")
    updated_at: datetime = Field(description="When the job was last updated")
    started_at: datetime | None = Field(
        default=None,
        description="When processing started",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="When processing completed (success or failure)",
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "01234567-89ab-cdef-0123-456789abcdef",
                "job_type": "audiobook_generation",
                "status": "processing",
                "audio_book_id": "fedcba98-7654-3210-fedc-ba9876543210",
                "progress": 45,
                "error_message": None,
                "created_at": "2024-12-11T12:00:00Z",
                "updated_at": "2024-12-11T12:05:00Z",
                "started_at": "2024-12-11T12:01:00Z",
                "completed_at": None,
            }
        },
    )
