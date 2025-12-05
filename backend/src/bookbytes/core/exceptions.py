"""Custom exception hierarchy for BookBytes.

This module defines a consistent exception hierarchy that enables:
- Structured error responses with error codes
- Consistent HTTP status code mapping
- Machine-readable error handling for API consumers

Usage:
    from bookbytes.core.exceptions import BookNotFoundError

    raise BookNotFoundError(isbn="1234567890")
"""

from typing import Any


class BookBytesError(Exception):
    """Base exception for all BookBytes errors.

    All custom exceptions should inherit from this class to enable
    consistent error handling and response formatting.

    Attributes:
        code: Machine-readable error code (e.g., "BOOK_NOT_FOUND")
        message: Human-readable error message
        status_code: HTTP status code to return
        details: Additional error details (optional)
    """

    code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred"
    status_code: int = 500

    def __init__(
        self,
        message: str | None = None,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Override default message
            code: Override default error code
            details: Additional error details
        """
        if message:
            self.message = message
        if code:
            self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self, request_id: str | None = None) -> dict[str, Any]:
        """Convert exception to API error response format.

        Args:
            request_id: Request correlation ID

        Returns:
            Error response dictionary
        """
        error: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
        }
        if request_id:
            error["request_id"] = request_id
        if self.details:
            error["details"] = self.details
        return {"error": error}


# =============================================================================
# Resource Not Found Errors (404)
# =============================================================================


class NotFoundError(BookBytesError):
    """Base class for resource not found errors."""

    status_code: int = 404


class BookNotFoundError(NotFoundError):
    """Raised when a book cannot be found."""

    code: str = "BOOK_NOT_FOUND"
    message: str = "Book not found"

    def __init__(
        self,
        book_id: str | None = None,
        isbn: str | None = None,
        message: str | None = None,
    ) -> None:
        """Initialize with optional identifiers.

        Args:
            book_id: UUID of the book
            isbn: ISBN of the book
            message: Override default message
        """
        details: dict[str, Any] = {}
        if book_id:
            details["book_id"] = book_id
        if isbn:
            details["isbn"] = isbn

        if not message:
            if isbn:
                message = f"Book with ISBN {isbn} not found"
            elif book_id:
                message = f"Book with ID {book_id} not found"

        super().__init__(message=message, details=details if details else None)


class ChapterNotFoundError(NotFoundError):
    """Raised when a chapter cannot be found."""

    code: str = "CHAPTER_NOT_FOUND"
    message: str = "Chapter not found"

    def __init__(
        self,
        chapter_id: str | None = None,
        book_id: str | None = None,
        chapter_number: int | None = None,
        message: str | None = None,
    ) -> None:
        """Initialize with optional identifiers."""
        details: dict[str, Any] = {}
        if chapter_id:
            details["chapter_id"] = chapter_id
        if book_id:
            details["book_id"] = book_id
        if chapter_number is not None:
            details["chapter_number"] = chapter_number

        if not message and chapter_number is not None and book_id:
            message = f"Chapter {chapter_number} not found for book {book_id}"

        super().__init__(message=message, details=details if details else None)


class JobNotFoundError(NotFoundError):
    """Raised when a job cannot be found."""

    code: str = "JOB_NOT_FOUND"
    message: str = "Job not found"

    def __init__(self, job_id: str | None = None, message: str | None = None) -> None:
        """Initialize with optional job ID."""
        details: dict[str, Any] = {}
        if job_id:
            details["job_id"] = job_id
            if not message:
                message = f"Job with ID {job_id} not found"

        super().__init__(message=message, details=details if details else None)


class UserNotFoundError(NotFoundError):
    """Raised when a user cannot be found."""

    code: str = "USER_NOT_FOUND"
    message: str = "User not found"

    def __init__(
        self,
        user_id: str | None = None,
        email: str | None = None,
        message: str | None = None,
    ) -> None:
        """Initialize with optional identifiers."""
        details: dict[str, Any] = {}
        if user_id:
            details["user_id"] = user_id
        if email:
            details["email"] = email

        super().__init__(message=message, details=details if details else None)


class ISBNNotFoundError(NotFoundError):
    """Raised when an ISBN lookup fails (from external API)."""

    code: str = "ISBN_NOT_FOUND"
    message: str = "ISBN not found in metadata service"

    def __init__(self, isbn: str | None = None, message: str | None = None) -> None:
        """Initialize with optional ISBN."""
        details: dict[str, Any] = {}
        if isbn:
            details["isbn"] = isbn
            if not message:
                message = f"ISBN {isbn} not found in Open Library"

        super().__init__(message=message, details=details if details else None)


# =============================================================================
# Authentication & Authorization Errors (401, 403)
# =============================================================================


class AuthenticationError(BookBytesError):
    """Raised when authentication fails."""

    code: str = "AUTHENTICATION_FAILED"
    message: str = "Authentication failed"
    status_code: int = 401


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid."""

    code: str = "INVALID_CREDENTIALS"
    message: str = "Invalid email or password"


class InvalidTokenError(AuthenticationError):
    """Raised when JWT token is invalid or expired."""

    code: str = "INVALID_TOKEN"
    message: str = "Invalid or expired token"


class AuthorizationError(BookBytesError):
    """Raised when user lacks permission for an action."""

    code: str = "AUTHORIZATION_FAILED"
    message: str = "You do not have permission to perform this action"
    status_code: int = 403


# =============================================================================
# Validation Errors (400)
# =============================================================================


class ValidationError(BookBytesError):
    """Raised when input validation fails."""

    code: str = "VALIDATION_ERROR"
    message: str = "Validation error"
    status_code: int = 400

    def __init__(
        self,
        message: str | None = None,
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize with optional field information."""
        if details is None:
            details = {}
        if field:
            details["field"] = field
        super().__init__(message=message, details=details if details else None)


class InvalidISBNError(ValidationError):
    """Raised when ISBN format is invalid."""

    code: str = "INVALID_ISBN"
    message: str = "Invalid ISBN format"

    def __init__(self, isbn: str | None = None, message: str | None = None) -> None:
        """Initialize with optional ISBN."""
        details: dict[str, Any] = {}
        if isbn:
            details["isbn"] = isbn
        super().__init__(message=message, field="isbn", details=details)


class DuplicateEmailError(ValidationError):
    """Raised when email is already registered."""

    code: str = "DUPLICATE_EMAIL"
    message: str = "Email is already registered"


# =============================================================================
# External Service Errors (502, 503)
# =============================================================================


class ExternalServiceError(BookBytesError):
    """Base class for external service errors."""

    code: str = "EXTERNAL_SERVICE_ERROR"
    message: str = "External service error"
    status_code: int = 502


class OpenAIServiceError(ExternalServiceError):
    """Raised when OpenAI API call fails."""

    code: str = "OPENAI_SERVICE_ERROR"
    message: str = "Failed to communicate with OpenAI"


class TTSServiceError(ExternalServiceError):
    """Raised when TTS service fails."""

    code: str = "TTS_SERVICE_ERROR"
    message: str = "Failed to generate audio"


class MetadataServiceError(ExternalServiceError):
    """Raised when book metadata service fails."""

    code: str = "METADATA_SERVICE_ERROR"
    message: str = "Failed to fetch book metadata"


class StorageServiceError(ExternalServiceError):
    """Raised when storage operations fail."""

    code: str = "STORAGE_SERVICE_ERROR"
    message: str = "Failed to store or retrieve file"


# =============================================================================
# Job Processing Errors (409, 500)
# =============================================================================


class JobError(BookBytesError):
    """Base class for job processing errors."""

    code: str = "JOB_ERROR"
    message: str = "Job processing error"


class JobAlreadyExistsError(JobError):
    """Raised when trying to create a duplicate job for a book."""

    code: str = "JOB_ALREADY_EXISTS"
    message: str = "A job for this book is already in progress"
    status_code: int = 409

    def __init__(
        self,
        book_id: str | None = None,
        job_id: str | None = None,
        message: str | None = None,
    ) -> None:
        """Initialize with optional identifiers.

        Args:
            book_id: UUID of the book being processed
            job_id: ID of the existing job
            message: Override default message
        """
        details: dict[str, Any] = {}
        if book_id:
            details["book_id"] = book_id
        if job_id:
            details["existing_job_id"] = job_id

        if not message and book_id:
            message = f"A job for book {book_id} is already in progress"

        super().__init__(message=message, details=details if details else None)


class JobProcessingError(JobError):
    """Raised when job processing fails."""

    code: str = "JOB_PROCESSING_FAILED"
    message: str = "Job processing failed"
    status_code: int = 500

    def __init__(
        self,
        job_id: str | None = None,
        step: str | None = None,
        error: str | None = None,
    ) -> None:
        """Initialize with optional job details."""
        details: dict[str, Any] = {}
        if job_id:
            details["job_id"] = job_id
        if step:
            details["failed_step"] = step
        if error:
            details["error"] = error
        super().__init__(details=details if details else None)
