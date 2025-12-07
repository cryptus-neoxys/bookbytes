# BookBytes Backend 📚🎧

> Transform lengthy non-fiction books into concise, chapter-wise audio summaries.

## Overview

BookBytes converts books into digestible 5-minute audio bytes. A 250-page book becomes 15-20 short audio chapters totaling 1.5-2 hours.

**Tech Stack:** Python 3.13+, FastAPI, PostgreSQL, Redis, SQLAlchemy 2.0, httpx

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    BookBytes Library                          │
├──────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐   │
│  │   Works     │───▶│  Editions   │───▶│   AudioBooks    │   │
│  │ (our data)  │    │ (ISBNs)     │    │ (our content)   │   │
│  └──────┬──────┘    └─────────────┘    └─────────────────┘   │
│         │                                                     │
│         ▼                                                     │
│  ┌─────────────┐                                             │
│  │BookProviders│  ← Maps our IDs to provider IDs (OL, Google)│
│  └─────────────┘                                             │
│         │                                                     │
│         ▼                                                     │
│  ┌─────────────┐                                             │
│  │  Redis Cache│  ← Raw API responses (TTL-based)            │
│  └─────────────┘                                             │
└──────────────────────────────────────────────────────────────┘
```

### Data Model Hierarchy

```
Work (canonical book)
  ├── Edition (specific ISBN/format)
  │     └── AudioBook (generated audio)
  │           └── Chapter (individual segments)
  └── BookProvider (external ID mappings)
```

### Book Search Flow

```mermaid
flowchart TD
    A[User Search] --> B{Search Type?}

    %% ISBN Search Path
    B -->|By ISBN| C[Check Library DB]
    C -->|Found| E[Return Existing Book]
    C -->|Not Found| F1[Check Cache]
    F1 -->|Hit| G{Latest Edition?}
    F1 -->|Miss| F[Query OpenLibrary API]
    F --> G
    G -->|Yes| H[Store in Library]
    G -->|No| I[Find Latest Edition]
    I --> H

    %% Title/Author Search Path
    B -->|By Title/Author| D1[Check Search Cache]
    D1 -->|Hit| K[Display Results]
    D1 -->|Miss| D4[Query OpenLibrary API]
    D4 --> K

    %% Selection & Processing
    K --> L[User Selects Book]
    L --> M[Store Work + Editions]
    M --> N[Process AudioBook]
```

## Project Structure

```
backend/
├── src/bookbytes/
│   ├── api/v1/           # FastAPI routers
│   │   ├── router.py     # Main v1 router
│   │   └── search.py     # Book search endpoints
│   ├── core/             # Config, database, logging
│   ├── models/           # SQLAlchemy models
│   │   ├── work.py       # Work entity
│   │   ├── edition.py    # Edition entity
│   │   ├── audio_book.py # AudioBook entity
│   │   └── book_provider.py
│   ├── repositories/     # Database access layer
│   ├── schemas/          # Pydantic schemas
│   └── services/         # Business logic
│       ├── cache.py      # Redis cache service
│       ├── library.py    # Work/Edition persistence
│       └── openlibrary.py # OpenLibrary API client
├── tests/
│   ├── unit/             # Unit tests (mocked deps)
│   └── integration/      # Integration tests
└── pyproject.toml
```

## Local Development Setup

### Prerequisites

- Python 3.13+
- Redis (for caching)
- PostgreSQL (or use SQLite for development)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd bookbytes/backend
```

### 2. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e ".[dev]"
```

### 3. Environment Configuration

Create a `.env` file:

```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./bookbytes.db
# For PostgreSQL:
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost/bookbytes

# Redis
REDIS_URL=redis://localhost:6379/0

# API Keys
OPENAI_API_KEY=sk-...

# App Config
APP_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG
LOG_FORMAT=console
```

### 4. Start Redis

```bash
# Using Docker
docker run -d -p 6379:6379 redis:alpine

# Or install locally
brew install redis && redis-server
```

### 5. Run the Server

```bash
# Development server with auto-reload
uv run uvicorn bookbytes.main:app --reload --port 8000

# Or using make
make dev
```

### 6. Run Tests

```bash
# All unit tests
make test

# Integration tests (requires Redis)
make test-integration

# Coverage report
make test-cov
```

## API Endpoints

| Method | Endpoint                         | Description                  |
| ------ | -------------------------------- | ---------------------------- |
| `POST` | `/api/v1/books/search`           | Search books by title/author |
| `GET`  | `/api/v1/books/works/{work_key}` | Get work details             |
| `GET`  | `/api/v1/books/isbn/{isbn}`      | Lookup by ISBN               |
| `GET`  | `/health/live`                   | Liveness probe               |
| `GET`  | `/health/ready`                  | Readiness probe              |

### Example: Search Books

```bash
curl -X POST http://localhost:8000/api/v1/books/search \
  -H "Content-Type: application/json" \
  -d '{"title": "Atomic Habits"}'
```

## Testing Strategy

| Layer       | Location                                       | Coverage                             |
| ----------- | ---------------------------------------------- | ------------------------------------ |
| Unit        | `tests/unit/`                                  | Services, endpoints with mocked deps |
| Integration | `tests/integration/`                           | API + database + mocked externals    |
| External    | `tests/integration/` (`@pytest.mark.external`) | Real API calls                       |

Run with markers:

```bash
# Skip external API tests (for CI)
pytest -m "not external"

# Only run external tests
pytest -m external
```

## Configuration

All settings via environment variables or `.env`:

| Variable         | Default       | Description          |
| ---------------- | ------------- | -------------------- |
| `APP_ENV`        | `development` | Environment mode     |
| `DATABASE_URL`   | Required      | SQLAlchemy async URL |
| `REDIS_URL`      | Required      | Redis connection URL |
| `OPENAI_API_KEY` | Required      | OpenAI API key       |
| `LOG_LEVEL`      | `INFO`        | Logging level        |
| `LOG_FORMAT`     | `json`        | `json` or `console`  |

## License

Not licensed yet.
