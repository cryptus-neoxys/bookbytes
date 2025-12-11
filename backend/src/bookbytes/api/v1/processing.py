"""Audiobook processing endpoints.

Provides endpoints for starting audiobook processing,
checking job status, and refreshing audiobooks.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from bookbytes.core.database import get_async_session
from bookbytes.core.logging import get_logger
from bookbytes.schemas.common import ErrorResponse
from bookbytes.schemas.processing import (
    JobStatusResponse,
    ProcessRequest,
    ProcessResponse,
    RefreshRequest,
)

logger = get_logger(__name__)

router = APIRouter()


# =============================================================================
# Dependencies (will be implemented in later phases)
# =============================================================================


# async def get_processing_service(...) -> ProcessingService:
#     """Get the processing service with injected dependencies."""
#     ...


# =============================================================================
# Processing Endpoints
# =============================================================================


@router.post(
    "/process",
    response_model=ProcessResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start audiobook processing",
    description="Start processing an audiobook from an edition or ISBN. Returns a job ID for tracking progress.",
    responses={
        202: {"description": "Processing started"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Edition/ISBN not found"},
        409: {"model": ErrorResponse, "description": "Audiobook already exists"},
    },
)
async def start_processing(
    request: ProcessRequest,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> ProcessResponse:
    """Start audiobook processing for an edition.

    Accepts either an edition_id (UUID) or an ISBN string.
    Creates an AudioBook record in PENDING status and queues
    a background job for processing.

    Returns immediately with a job_id for status polling.
    """
    logger.info(
        "start_processing_request",
        edition_id=str(request.edition_id) if request.edition_id else None,
        isbn=request.isbn,
    )

    # TODO: Implement in Phase 5 (ProcessingService)
    # 1. Resolve edition_id or look up by ISBN
    # 2. Check if audiobook already exists for this edition
    # 3. Create AudioBook record (status=PENDING)
    # 4. Create Job record
    # 5. Enqueue ARQ task
    # 6. Return job_id

    # Placeholder - will be replaced with actual implementation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Processing service not yet implemented. See Phase 3.1.5 tasks.",
    )


@router.post(
    "/{audio_book_id}/refresh",
    response_model=ProcessResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Refresh audiobook",
    description="Regenerate an audiobook with a new version. Useful when summary quality improves.",
    responses={
        202: {"description": "Refresh started"},
        404: {"model": ErrorResponse, "description": "Audiobook not found"},
    },
)
async def refresh_audiobook(
    audio_book_id: UUID,
    request: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> ProcessResponse:
    """Refresh an existing audiobook.

    Creates a new version by incrementing the version number
    and reprocessing all chapters.

    Args:
        audio_book_id: UUID of the audiobook to refresh
        request: Refresh options (force flag)
    """
    logger.info(
        "refresh_audiobook_request",
        audio_book_id=str(audio_book_id),
        force=request.force,
    )

    # TODO: Implement in Phase 5 (ProcessingService)
    # 1. Look up AudioBook by ID
    # 2. Increment version
    # 3. Reset status to PENDING
    # 4. Create Job record
    # 5. Enqueue ARQ task
    # 6. Return job_id

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh service not yet implemented. See Phase 3.1.5 tasks.",
    )


# =============================================================================
# Job Status Endpoints
# =============================================================================


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get job status",
    description="Get the current status and progress of a processing job.",
    responses={
        200: {"description": "Job status"},
        404: {"model": ErrorResponse, "description": "Job not found"},
    },
)
async def get_job_status(
    job_id: UUID,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> JobStatusResponse:
    """Get the status of a processing job.

    Returns progress percentage, current status, and any error details.

    Args:
        job_id: UUID of the job to check
    """
    logger.info("get_job_status_request", job_id=str(job_id))

    # TODO: Implement when Job model exists (Phase 2)
    # 1. Query Job by ID
    # 2. Return JobStatusResponse

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Job repository not yet implemented. See Phase 3.1.2 tasks.",
    )
