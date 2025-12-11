# BookBytes AI Coding Instructions

## Project Overview

BookBytes converts physical books (via ISBN) into chapter-wise audio summaries. Currently being refactored from Flask monolith to production FastAPI.

- **Stack**: Python 3.13+, FastAPI, PostgreSQL (async), Redis, ARQ workers, OpenAI, gTTS
- **Data Flow**: ISBN → Open Library API → OpenAI (chapters + summaries) → gTTS → Storage (local/S3)

## Architecture (`src/bookbytes/`)

```
main.py          # FastAPI app factory with lifespan, middleware, exception handlers
config.py        # Pydantic Settings with env validation (Settings class, enums)
dependencies.py  # FastAPI Depends() injection container
core/
  exceptions.py  # Exception hierarchy (BookBytesError base, domain-specific subclasses)
  logging.py     # Structlog config with correlation ID support
api/v1/          # Versioned API routers
services/        # Business logic (call from routes, not vice versa)
repositories/    # Database access layer (SQLAlchemy async)
schemas/         # Pydantic request/response models (BaseSchema in common.py)
models/          # SQLAlchemy ORM models
storage/         # Pluggable storage (local dev, S3 prod)
workers/         # ARQ background job handlers
```

## Logging (MUST use structlog)

```python
from bookbytes.core.logging import get_logger
logger = get_logger(__name__)
logger.info("Processing book", isbn="123", user_id="abc")  # Key-value pairs, not f-strings
```

Correlation IDs are auto-injected via middleware. Use `set_correlation_id()` for background jobs.

## Exceptions Pattern

Raise domain exceptions from `core/exceptions.py`, never raw `Exception`. Global handlers convert to JSON:

```python
from bookbytes.core.exceptions import BookNotFoundError
raise BookNotFoundError(isbn="123")  # Returns {"error": {"code": "BOOK_NOT_FOUND", ...}}
```

## Configuration

All config via `Settings` class in `config.py`. Access with `get_settings()` (cached) or `SettingsDep` in routes:

```python
from bookbytes.config import get_settings
settings = get_settings()
if settings.is_development: ...
```

## Commands

- **Run API**: `uv run python -m bookbytes.main` or `uv run uvicorn bookbytes.main:app --reload`
- **Tests**: `uv run pytest tests/` (async fixtures in `tests/conftest.py`)
- **Lint**: `uv run ruff check src/ tests/` | **Format**: `uv run ruff format src/ tests/`
- **Type check**: `uv run mypy src/`

## Testing Conventions

- Use fixtures from `tests/conftest.py`: `async_client`, `authenticated_client`, `test_settings`
- Mock external services (OpenAI, Open Library) using `tests/mocks/`

## Key Conventions

- **Async everywhere**: All DB/HTTP ops must use `async/await`
- **Pydantic schemas**: Inherit from `BaseSchema` in `schemas/common.py` (auto ORM conversion)
- **Enums for options**: Use `str, Enum` pattern (e.g., `Environment`, `StorageBackend`) for type-safe configs
- **Path handling**: Use `pathlib.Path`, never `os.path`
- **Auth modes**: `API_KEY` for dev (header `X-API-Key`), `JWT` for prod

## Legacy Code (root-level)

`app.py`, `cli.py`, `test_app.py` are the original Flask implementation—reference for business logic only.
