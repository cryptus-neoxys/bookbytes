"""FastAPI dependency injection container.

This module provides dependency injection functions for use with FastAPI's
Depends() pattern. Dependencies are organized by functionality and can be
easily mocked for testing.
"""

from collections.abc import AsyncGenerator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from bookbytes.config import Settings, get_settings

# Type alias for common dependency patterns
SettingsDep = Annotated[Settings, Depends(get_settings)]


# ========================================
# Settings Dependencies
# ========================================
def get_settings_from_request(request: Request) -> Settings:
    """Get settings from request state (set during lifespan).

    This is useful when you need settings that were potentially
    modified during startup.

    Args:
        request: The current request

    Returns:
        Settings: Application settings
    """
    return request.app.state.settings


# ========================================
# Database Dependencies
# ========================================
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session.

    Yields a database session that automatically handles
    commit on success and rollback on exception.

    Yields:
        AsyncSession: Database session
    """

    from bookbytes.core.database import get_async_session

    async for session in get_async_session():
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ========================================
# Redis Dependencies
# ========================================
# TODO: Implement in Phase 3
async def get_redis() -> AsyncGenerator[None, None]:
    """Get a Redis connection.

    Yields a Redis connection from the connection pool.

    Yields:
        Redis: Redis connection
    """
    # Placeholder - will be implemented in Phase 3
    # redis = await aioredis.from_url(settings.redis_url)
    # try:
    #     yield redis
    # finally:
    #     await redis.close()
    yield None  # type: ignore


# ========================================
# Storage Dependencies
# ========================================
# TODO: Implement in Phase 5
@lru_cache
def get_storage() -> None:
    """Get the configured storage backend.

    Returns the appropriate storage backend (Local or S3) based on
    the STORAGE_BACKEND configuration.

    Returns:
        StorageBackend: Configured storage backend
    """
    # Placeholder - will be implemented in Phase 5
    # settings = get_settings()
    # from bookbytes.storage import get_storage_backend
    # return get_storage_backend(settings)
    return None


# ========================================
# Service Dependencies
# ========================================
# TODO: Implement in Phase 5
def get_metadata_service() -> None:
    """Get the book metadata service.

    Returns:
        BookMetadataService: Metadata service instance
    """
    # Placeholder - will be implemented in Phase 5
    return None


def get_openai_service() -> None:
    """Get the OpenAI service.

    Returns:
        OpenAIService: OpenAI service instance
    """
    # Placeholder - will be implemented in Phase 5
    return None


def get_tts_service() -> None:
    """Get the TTS (Text-to-Speech) service.

    Returns:
        TTSService: TTS service instance
    """
    # Placeholder - will be implemented in Phase 5
    return None


def get_book_service() -> None:
    """Get the book processing service.

    Returns:
        BookService: Book service instance
    """
    # Placeholder - will be implemented in Phase 5
    return None


# ========================================
# Auth Dependencies
# ========================================
# TODO: Implement in Phase 6
async def get_current_user() -> None:
    """Get the current authenticated user.

    Decodes the JWT token from the Authorization header,
    validates it, and returns the user from the database.

    Raises:
        HTTPException: 401 if token is invalid or user not found

    Returns:
        User: Current authenticated user
    """
    # Placeholder - will be implemented in Phase 6
    return None


async def get_current_user_optional() -> None:
    """Get the current user if authenticated, otherwise None.

    Useful for endpoints that work with or without authentication.

    Returns:
        User | None: Current user or None if not authenticated
    """
    # Placeholder - will be implemented in Phase 6
    return None
