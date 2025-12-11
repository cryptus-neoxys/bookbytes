"""Unit tests for processing endpoints.

Tests the processing API endpoints including request validation,
job creation, and status checking.
"""

import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from bookbytes.schemas.processing import (
    JobStatusResponse,
    ProcessRequest,
    RefreshRequest,
)

# =============================================================================
# Schema Validation Tests
# =============================================================================


class TestProcessRequestValidation:
    """Test ProcessRequest schema validation."""

    def test_valid_edition_id(self) -> None:
        """Edition ID only is valid."""
        request = ProcessRequest(
            edition_id="01234567-89ab-cdef-0123-456789abcdef",
        )
        assert request.edition_id is not None
        assert request.isbn is None

    def test_valid_isbn(self) -> None:
        """ISBN only is valid."""
        request = ProcessRequest(isbn="978-0-13-468599-1")
        assert request.isbn == "978-0-13-468599-1"
        assert request.edition_id is None

    def test_isbn_without_hyphens(self) -> None:
        """ISBN without hyphens is valid."""
        request = ProcessRequest(isbn="9780134685991")
        assert request.isbn == "9780134685991"

    def test_neither_provided_raises_error(self) -> None:
        """Neither edition_id nor isbn raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ProcessRequest()

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "edition_id or isbn" in str(errors[0]["msg"]).lower()

    def test_both_provided_raises_error(self) -> None:
        """Both edition_id and isbn raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ProcessRequest(
                edition_id="01234567-89ab-cdef-0123-456789abcdef",
                isbn="978-0-13-468599-1",
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "only one" in str(errors[0]["msg"]).lower()

    def test_invalid_uuid_raises_error(self) -> None:
        """Invalid UUID format raises validation error."""
        with pytest.raises(ValidationError):
            ProcessRequest(edition_id="not-a-uuid")

    def test_isbn_too_short_raises_error(self) -> None:
        """ISBN shorter than 10 chars raises validation error."""
        with pytest.raises(ValidationError):
            ProcessRequest(isbn="123456789")  # 9 chars

    def test_isbn_too_long_raises_error(self) -> None:
        """ISBN longer than 17 chars raises validation error."""
        with pytest.raises(ValidationError):
            ProcessRequest(isbn="978-0-13-468599-1-2-3")  # too long


class TestRefreshRequestValidation:
    """Test RefreshRequest schema validation."""

    def test_default_force_is_false(self) -> None:
        """Default force value is False."""
        request = RefreshRequest()
        assert request.force is False

    def test_force_true(self) -> None:
        """Force can be set to True."""
        request = RefreshRequest(force=True)
        assert request.force is True


class TestJobStatusResponse:
    """Test JobStatusResponse schema."""

    def test_from_attributes_enabled(self) -> None:
        """Can create from ORM model."""
        assert JobStatusResponse.model_config.get("from_attributes") is True


# =============================================================================
# Endpoint Integration Tests
# =============================================================================


@pytest.mark.integration
class TestProcessEndpoint:
    """Test POST /books/process endpoint."""

    async def test_process_returns_501_not_implemented(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Process returns 501 until service is implemented."""
        response = await async_client.post(
            "/api/v1/books/process",
            json={"isbn": "9780134685991"},
        )
        assert response.status_code == 501
        assert "not yet implemented" in response.json()["detail"].lower()

    async def test_process_validates_request_body(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Process validates request body."""
        response = await async_client.post(
            "/api/v1/books/process",
            json={},  # Empty body - neither edition_id nor isbn
        )
        assert response.status_code == 422


@pytest.mark.integration
class TestRefreshEndpoint:
    """Test POST /books/{audio_book_id}/refresh endpoint."""

    async def test_refresh_returns_501_not_implemented(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Refresh returns 501 until service is implemented."""
        response = await async_client.post(
            "/api/v1/books/01234567-89ab-cdef-0123-456789abcdef/refresh",
            json={},
        )
        assert response.status_code == 501
        assert "not yet implemented" in response.json()["detail"].lower()


@pytest.mark.integration
class TestJobStatusEndpoint:
    """Test GET /books/jobs/{job_id} endpoint."""

    async def test_job_status_returns_501_not_implemented(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Job status returns 501 until repository is implemented."""
        response = await async_client.get(
            "/api/v1/books/jobs/01234567-89ab-cdef-0123-456789abcdef",
        )
        assert response.status_code == 501
        assert "not yet implemented" in response.json()["detail"].lower()

    async def test_job_status_invalid_uuid_returns_422(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Invalid UUID returns 422."""
        response = await async_client.get(
            "/api/v1/books/jobs/not-a-uuid",
        )
        assert response.status_code == 422
