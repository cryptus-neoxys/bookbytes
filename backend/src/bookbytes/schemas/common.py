"""Common Pydantic schemas used across the API.

This module provides shared schemas for:
- Error responses (consistent error format)
- Pagination (standardized list responses)
- Common fields and mixins
"""

from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# Generic type for paginated responses
T = TypeVar("T")


# =============================================================================
# Base Configuration
# =============================================================================


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,  # Allow ORM model conversion
        populate_by_name=True,  # Allow both alias and field name
        str_strip_whitespace=True,  # Strip whitespace from strings
    )


# =============================================================================
# Error Schemas
# =============================================================================


class ErrorDetail(BaseModel):
    """Details of an error response.

    Follows RFC 7807 Problem Details style.

    Attributes:
        code: Machine-readable error code (e.g., "BOOK_NOT_FOUND")
        message: Human-readable error description
        request_id: Correlation ID for tracing (optional)
        details: Additional error context (optional)
    """

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    request_id: str | None = Field(
        None, description="Request correlation ID for tracing"
    )
    details: dict[str, str | int | bool | None] | None = Field(
        None, description="Additional error context"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "BOOK_NOT_FOUND",
                "message": "Book with ISBN 1234567890 not found",
                "request_id": "abc-123-def-456",
            }
        }
    )


class ErrorResponse(BaseModel):
    """Standard error response wrapper.

    All API errors should return this format for consistency.

    Attributes:
        error: The error details
    """

    error: ErrorDetail

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": {
                    "code": "BOOK_NOT_FOUND",
                    "message": "Book with ISBN 1234567890 not found",
                    "request_id": "abc-123-def-456",
                }
            }
        }
    )


# =============================================================================
# Pagination Schemas
# =============================================================================


class PaginationParams(BaseModel):
    """Query parameters for pagination.

    Attributes:
        page: Page number (1-indexed)
        size: Number of items per page
    """

    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    size: int = Field(20, ge=1, le=100, description="Items per page (max 100)")

    @property
    def offset(self) -> int:
        """Calculate the offset for database queries."""
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        """Get the limit for database queries."""
        return self.size


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper.

    Use this for any list endpoint that supports pagination.

    Attributes:
        items: List of items for the current page
        total: Total number of items across all pages
        page: Current page number
        size: Number of items per page
        pages: Total number of pages
    """

    items: list[T] = Field(..., description="List of items for current page")
    total: int = Field(..., ge=0, description="Total items across all pages")
    page: int = Field(..., ge=1, description="Current page number")
    size: int = Field(..., ge=1, description="Items per page")
    pages: int = Field(..., ge=0, description="Total number of pages")

    @classmethod
    def create(
        cls, items: list[T], total: int, page: int, size: int
    ) -> "PaginatedResponse[T]":
        """Factory method to create a paginated response.

        Args:
            items: Items for the current page
            total: Total number of items
            page: Current page number
            size: Page size

        Returns:
            Paginated response with calculated pages
        """
        pages = (total + size - 1) // size if total > 0 else 0
        return cls(items=items, total=total, page=page, size=size, pages=pages)


# =============================================================================
# Common Field Types
# =============================================================================


class UUIDMixin(BaseModel):
    """Mixin for models with UUID primary key."""

    id: UUID = Field(..., description="Unique identifier")


class TimestampMixin(BaseModel):
    """Mixin for models with timestamp fields."""

    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class UUIDTimestampMixin(UUIDMixin, TimestampMixin):
    """Combined mixin for UUID and timestamps."""

    pass


# =============================================================================
# Health Check Schemas
# =============================================================================


class HealthStatus(BaseModel):
    """Individual health check status.

    Attributes:
        status: Health status ("ok" or "error")
        message: Optional status message
    """

    status: str = Field(..., pattern="^(ok|error)$")
    message: str | None = None


class HealthCheckResponse(BaseModel):
    """Health check endpoint response.

    Attributes:
        status: Overall health status
        checks: Individual service health checks
    """

    status: str = Field(..., pattern="^(ok|degraded|error)$")
    checks: dict[str, HealthStatus | str] = Field(
        default_factory=dict, description="Individual service checks"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ok",
                "checks": {
                    "database": "ok",
                    "redis": "ok",
                },
            }
        }
    )


# =============================================================================
# Message Response Schemas
# =============================================================================


class MessageResponse(BaseModel):
    """Simple message response.

    Useful for operations that just need to confirm success.
    """

    message: str = Field(..., description="Response message")

    model_config = ConfigDict(
        json_schema_extra={"example": {"message": "Operation completed successfully"}}
    )
