"""Async database engine and session management.

This module provides the core database infrastructure:
- Async SQLAlchemy engine with connection pooling
- Async session factory for request-scoped sessions
- Database lifecycle management (init/close)

Usage:
    from bookbytes.core.database import init_db, close_db, get_async_session

    # At startup
    await init_db(settings)

    # In request handlers (via dependency injection)
    async with get_async_session() as session:
        ...

    # At shutdown
    await close_db()
"""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from bookbytes.config import Settings
from bookbytes.core.logging import get_logger

logger = get_logger(__name__)

# Global engine and session factory (initialized at startup)
_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Get the database engine.

    Raises:
        RuntimeError: If database is not initialized
    """
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get the session factory.

    Raises:
        RuntimeError: If database is not initialized
    """
    if _async_session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _async_session_factory


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session.

    This is designed to be used as a FastAPI dependency or in any async context.
    The session is automatically closed when the context exits.

    Yields:
        AsyncSession: Database session for the current context
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_db(settings: Settings) -> None:
    """Initialize the database engine and session factory.

    This should be called once at application startup.

    Args:
        settings: Application settings containing database configuration
    """
    global _engine, _async_session_factory

    logger.info(
        "Initializing database",
        database_url=_mask_password(settings.database_url),
    )

    # Determine pool settings based on database type
    is_sqlite = settings.database_url.startswith("sqlite")

    engine_kwargs: dict[str, Any] = {
        "echo": settings.debug,
    }

    if is_sqlite:
        # SQLite doesn't support connection pooling the same way
        engine_kwargs["poolclass"] = NullPool
        # Required for SQLite async
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    else:
        # PostgreSQL connection pool settings
        engine_kwargs["pool_size"] = settings.database_pool_min
        engine_kwargs["max_overflow"] = (
            settings.database_pool_max - settings.database_pool_min
        )
        engine_kwargs["pool_pre_ping"] = True  # Verify connections before use

    _engine = create_async_engine(
        settings.database_url,
        **engine_kwargs,
    )

    _async_session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    logger.info("Database initialized successfully")


async def close_db() -> None:
    """Close the database engine and all connections.

    This should be called at application shutdown.
    """
    global _engine, _async_session_factory

    if _engine is not None:
        logger.info("Closing database connections")
        await _engine.dispose()
        _engine = None
        _async_session_factory = None
        logger.info("Database connections closed")


async def check_db_connection() -> bool:
    """Check if the database connection is working.

    Returns:
        True if connection is healthy, False otherwise
    """
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return False


def _mask_password(url: str) -> str:
    """Mask password in database URL for logging.

    Args:
        url: Database URL

    Returns:
        URL with password masked
    """
    # Simple masking - replace password between :// and @
    if "://" in url and "@" in url:
        prefix = url.split("://")[0] + "://"
        rest = url.split("://")[1]
        if "@" in rest:
            creds, host = rest.split("@", 1)
            if ":" in creds:
                user = creds.split(":")[0]
                return f"{prefix}{user}:****@{host}"
    return url
