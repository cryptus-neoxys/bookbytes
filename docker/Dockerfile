# BookBytes Multi-Stage Dockerfile
# Stage 1: Builder - installs dependencies
# Stage 2: Runtime - minimal production image

# Stage 1: Builder
FROM python:3.13-slim AS builder

# Install uv for fast package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Create virtual environment and install dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code and README (needed for hatchling build)
COPY src/ src/
COPY Readme.md ./

# Install the project itself
RUN uv sync --frozen --no-dev


# Stage 2: Runtime
FROM python:3.13-slim AS runtime

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd --gid 1000 bookbytes \
    && useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home bookbytes

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy source code
COPY --from=builder /app/src /app/src

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # App defaults
    APP_ENV=production \
    HOST=0.0.0.0 \
    PORT=8000

# Create data directories
RUN mkdir -p /app/data/audio && chown -R bookbytes:bookbytes /app

# Switch to non-root user
USER bookbytes

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health/live || exit 1

# Default command (can be overridden in docker-compose)
# Use shell form to interpolate PORT env var
CMD uvicorn bookbytes.main:app --host 0.0.0.0 --port ${PORT}
