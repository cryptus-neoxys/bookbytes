"""Structured logging configuration using Python's standard logging.

This module configures logging with:
- JSON output for production (machine-readable)
- Console output for development (human-readable)
- Correlation ID support for request tracing
- Structlog integration for structured log entries

Usage:
    from bookbytes.core.logging import configure_logging, get_logger

    # Configure at app startup
    configure_logging(log_level="INFO", json_format=True)

    # Get a logger in any module
    logger = get_logger(__name__)
    logger.info("Processing book", isbn="1234567890", user_id="abc-123")
"""

import logging
import sys
from contextvars import ContextVar
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from bookbytes.config import Settings

# Context variable for correlation/request ID
correlation_id_ctx: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> str | None:
    """Get the current correlation ID from context."""
    return correlation_id_ctx.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID in context."""
    correlation_id_ctx.set(correlation_id)


def clear_correlation_id() -> None:
    """Clear the correlation ID from context."""
    correlation_id_ctx.set(None)


def add_correlation_id(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Structlog processor to add correlation ID to log entries."""
    correlation_id = get_correlation_id()
    if correlation_id:
        event_dict["correlation_id"] = correlation_id
    return event_dict


def add_app_context(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add application context to log entries."""
    event_dict["service"] = "bookbytes"
    return event_dict


def configure_logging(settings: Settings | None = None) -> None:
    """Configure structured logging for the application.

    Args:
        settings: Application settings. If None, uses default settings.
    """
    if settings is None:
        from bookbytes.config import get_settings

        settings = get_settings()

    # Determine log level
    log_level = getattr(logging, settings.log_level.value, logging.INFO)

    # Shared processors for all environments
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        add_correlation_id,
        add_app_context,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.use_json_logs:
        # Production: JSON format for log aggregation
        processors: list[Processor] = [
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
            foreign_pre_chain=shared_processors,
        )
    else:
        # Development: Pretty console output
        processors = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(colors=True),
        ]
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(colors=True),
            foreign_pre_chain=shared_processors,
        )

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add new handler with structlog formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    root_logger.addHandler(handler)

    # Quiet noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        A bound structlog logger that outputs structured logs.

    Example:
        logger = get_logger(__name__)
        logger.info("Processing started", book_id="123", chapter=1)
        logger.error("Processing failed", book_id="123", error=str(e))
    """
    return structlog.get_logger(name)


def log_context(**kwargs: Any) -> structlog.contextvars.bound_contextvars:
    """Context manager to bind values to all logs within the context.

    Example:
        with log_context(request_id="abc-123", user_id="user-456"):
            logger.info("Processing")  # Includes request_id and user_id
    """
    return structlog.contextvars.bound_contextvars(**kwargs)
