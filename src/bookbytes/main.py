"""FastAPI application factory for BookBytes.

This module creates and configures the FastAPI application with:
- Lifespan management for startup/shutdown events
- Middleware configuration
- Exception handlers
- API routers
"""

import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from bookbytes.config import Settings, get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan events.

    Handles initialization and cleanup of:
    - Database connection pool
    - Redis connection
    - Any other resources that need lifecycle management

    Args:
        app: The FastAPI application instance

    Yields:
        None: Control back to the application
    """
    settings = get_settings()

    # ========================================
    # Startup
    # ========================================
    # TODO: Initialize database connection pool (Phase 2)
    # TODO: Initialize Redis connection (Phase 3)
    # TODO: Initialize structlog (Phase 7)

    # Store settings in app state for access in dependencies
    app.state.settings = settings

    # Log startup
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Environment: {settings.app_env.value}")
    print(f"Debug mode: {settings.debug}")

    yield

    # ========================================
    # Shutdown
    # ========================================
    # TODO: Close database connections gracefully (Phase 7)
    # TODO: Close Redis connections gracefully (Phase 7)
    # TODO: Wait for in-flight requests (Phase 7)

    print(f"Shutting down {settings.app_name}")


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

    # Request ID middleware
    @app.middleware("http")
    async def add_request_id(request: Request, call_next: Any) -> Any:
        """Add request ID to each request for tracing."""
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response


def configure_exception_handlers(app: FastAPI) -> None:
    """Configure global exception handlers.

    Args:
        app: The FastAPI application instance
    """

    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions with a consistent error response."""
        request_id = getattr(request.state, "request_id", None)

        # TODO: Replace with structlog in Phase 7
        print(f"Unhandled exception: {exc}")

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
        # TODO: Add actual health checks for DB and Redis in Phase 7
        return {
            "status": "ok",
            "checks": {
                "database": "ok",
                "redis": "ok",
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

    # TODO: Include API v1 router in Phase 4
    # from bookbytes.api.v1.router import router as v1_router
    # app.include_router(v1_router, prefix="/api/v1")


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
