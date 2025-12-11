"""FastAPI application factory for BookBytes.

This module creates and configures the FastAPI application with:
- Lifespan management for startup/shutdown events
- Middleware configuration (CORS, request ID, logging)
- Exception handlers
- API routers
"""

import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from bookbytes.config import Settings, get_settings
from bookbytes.core.exceptions import BookBytesError
from bookbytes.core.logging import (
    clear_correlation_id,
    configure_logging,
    get_logger,
    set_correlation_id,
)

# Initialize logger for this module
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan events.

    Handles initialization and cleanup of:
    - Logging configuration
    - Database connection pool
    - Redis connection
    - Any other resources that need lifecycle management

    Args:
        app: The FastAPI application instance

    Yields:
        None: Control back to the application
    """
    from bookbytes.core.database import close_db, init_db

    settings = get_settings()

    # ========================================
    # Startup
    # ========================================
    # Configure logging first
    configure_logging(settings)

    # Re-get logger after configuration
    startup_logger = get_logger(__name__)

    # Initialize database connection pool
    await init_db(settings)

    # TODO: Initialize Redis connection (Phase 3)

    # Store settings in app state for access in dependencies
    app.state.settings = settings

    # Log startup
    startup_logger.info(
        "Application starting",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env.value,
        debug=settings.debug,
    )

    yield

    # ========================================
    # Shutdown
    # ========================================
    # Close database connections
    await close_db()

    # TODO: Close Redis connections (Phase 3)
    # TODO: Wait for in-flight requests (Phase 7)

    startup_logger.info("Application shutting down", app_name=settings.app_name)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    This is the application factory function that creates a fully configured
    FastAPI instance with all middleware, routes, and exception handlers.

    Args:
        settings: Optional settings override for testing

    Returns:
        FastAPI: Configured application instance
    """
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description=(
            "AI-powered book summarization and audio generation service. "
            "Upload a book ISBN and get chapter summaries with audio narration."
        ),
        version=settings.app_version,
        docs_url="/docs" if settings.is_development else "/docs",
        redoc_url="/redoc" if settings.is_development else "/redoc",
        openapi_url="/openapi.json" if settings.is_development else "/openapi.json",
        lifespan=lifespan,
    )

    # ========================================
    # Middleware
    # ========================================
    configure_middleware(app, settings)

    # ========================================
    # Exception Handlers
    # ========================================
    configure_exception_handlers(app)

    # ========================================
    # Routes
    # ========================================
    configure_routes(app)

    return app


def configure_middleware(app: FastAPI, settings: Settings) -> None:
    """Configure application middleware.

    Args:
        app: The FastAPI application instance
        settings: Application settings
    """
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.is_development else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging middleware
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next: Any) -> Any:
        """Log requests and responses with correlation ID."""
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        # Set correlation ID for all logs in this request context
        set_correlation_id(request_id)

        # Log request start
        request_logger = get_logger("bookbytes.request")
        start_time = time.perf_counter()

        request_logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            query=str(request.query_params) if request.query_params else None,
        )

        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log request completion
            request_logger.info(
                "Request completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            request_logger.error(
                "Request failed",
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration_ms, 2),
                error=str(exc),
            )
            raise

        finally:
            # Clear correlation ID
            clear_correlation_id()


def configure_exception_handlers(app: FastAPI) -> None:
    """Configure global exception handlers.

    Args:
        app: The FastAPI application instance
    """
    exception_logger = get_logger("bookbytes.exceptions")

    @app.exception_handler(BookBytesError)
    async def bookbytes_exception_handler(
        request: Request, exc: BookBytesError
    ) -> JSONResponse:
        """Handle BookBytes custom exceptions with structured error response."""
        request_id = getattr(request.state, "request_id", None)

        # Log at appropriate level based on status code
        if exc.status_code >= 500:
            exception_logger.error(
                "Application error",
                error_code=exc.code,
                error_message=exc.message,
                status_code=exc.status_code,
                path=request.url.path,
            )
        else:
            exception_logger.warning(
                "Client error",
                error_code=exc.code,
                error_message=exc.message,
                status_code=exc.status_code,
                path=request.url.path,
            )

        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(request_id=request_id),
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions with a consistent error response."""
        request_id = getattr(request.state, "request_id", None)

        exception_logger.exception(
            "Unhandled exception",
            error_type=type(exc).__name__,
            error_message=str(exc),
            path=request.url.path,
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "request_id": request_id,
                }
            },
        )


def configure_routes(app: FastAPI) -> None:
    """Configure application routes.

    Args:
        app: The FastAPI application instance
    """

    # Placeholder health check endpoint
    @app.get(
        "/health/live",
        tags=["Health"],
        summary="Liveness probe",
        description="Returns OK if the service is running",
    )
    async def liveness() -> dict[str, str]:
        """Liveness probe for container orchestration."""
        return {"status": "ok"}

    @app.get(
        "/health/ready",
        tags=["Health"],
        summary="Readiness probe",
        description="Returns OK if the service is ready to accept requests",
    )
    async def readiness() -> dict[str, Any]:
        """Readiness probe checking dependent services."""
        from bookbytes.core.database import check_db_connection

        # Check database connectivity
        db_ok = await check_db_connection()

        # TODO: Check Redis connectivity (Phase 3)
        redis_ok = True  # Placeholder

        overall_status = "ok" if (db_ok and redis_ok) else "error"

        return {
            "status": overall_status,
            "checks": {
                "database": "ok" if db_ok else "error",
                "redis": "ok" if redis_ok else "error",
            },
        }

    # Root endpoint
    @app.get(
        "/",
        tags=["Root"],
        summary="API root",
        description="Returns API information",
    )
    async def root() -> dict[str, str]:
        """API root endpoint with service information."""
        settings = get_settings()
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/health/live",
        }

    # Include API v1 router
    from bookbytes.api.v1.router import router as v1_router

    app.include_router(v1_router, prefix="/api/v1")


# Create the application instance
app = create_app()


def cli() -> None:
    """CLI entry point for running the application."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "bookbytes.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        log_level=settings.log_level.value.lower(),
    )


if __name__ == "__main__":
    cli()
