### Dependencies (pyproject.toml)

```toml
[project]
dependencies = [
    # Core
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "python-multipart>=0.0.6",

    # Async
    "httpx>=0.26.0",
    "anyio>=4.2.0",

    # Database
    "sqlalchemy[asyncio]>=2.0.25",
    "asyncpg>=0.29.0",
    "aiosqlite>=0.19.0",
    "alembic>=1.13.0",

    # Background Jobs
    "arq>=0.25.0",
    "redis>=5.0.0",

    # Configuration
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "python-dotenv>=1.0.0",

    # Auth (JWT)
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",

    # Storage
    "boto3>=1.34.0",
    "aioboto3>=12.0.0",

    # External APIs
    "openai>=1.0.0",
    "gtts>=2.5.0",

    # Resilience
    "tenacity>=8.2.0",

    # Observability
    "structlog>=24.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "respx>=0.20.0",
    "fakeredis>=2.20.0",
    "ruff>=0.1.0",
]
```

### Folder Structure

```
bookbytes/
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
├── src/
│   └── bookbytes/
│       ├── __init__.py
│       ├── main.py                 # FastAPI app factory
│       ├── config.py               # Pydantic settings
│       ├── dependencies.py         # DI container
│       │
│       ├── api/
│       │   ├── __init__.py
│       │   └── v1/
│       │       ├── __init__.py
│       │       ├── router.py       # Main v1 router
│       │       ├── auth.py         # Auth endpoints (register, login, me)
│       │       ├── books.py        # Book endpoints
│       │       ├── chapters.py     # Chapter endpoints
│       │       ├── jobs.py         # Job status endpoints
│       │       └── health.py       # Health checks
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── base.py             # Base model, mixins
│       │   ├── user.py             # User model
│       │   ├── book.py             # Book + BookIsbn models
│       │   ├── chapter.py
│       │   └── job.py
│       │
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── common.py           # Shared schemas
│       │   ├── auth.py             # Auth request/response schemas
│       │   ├── book.py
│       │   ├── chapter.py
│       │   └── job.py
│       │
│       ├── repositories/
│       │   ├── __init__.py
│       │   ├── base.py             # Generic repository
│       │   ├── user.py             # User repository
│       │   ├── book.py             # Book + BookIsbn repositories
│       │   ├── chapter.py
│       │   └── job.py
│       │
│       ├── services/
│       │   ├── __init__.py
│       │   ├── book_service.py     # Book processing orchestration
│       │   ├── openai_service.py   # OpenAI API wrapper
│       │   ├── tts_service.py      # gTTS wrapper
│       │   └── metadata_service.py # Open Library API
│       │
│       ├── workers/
│       │   ├── __init__.py
│       │   ├── settings.py         # ARQ worker config
│       │   └── tasks.py            # Job definitions
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── database.py         # Async engine & sessions
│       │   ├── exceptions.py       # Exception hierarchy
│       │   ├── logging.py          # Structured logging
│       │   └── security.py         # JWT utilities
│       │
│       └── storage/
│           ├── __init__.py
│           ├── base.py             # Abstract interface
│           ├── local.py            # Local filesystem
│           └── s3.py               # S3 implementation
│
├── tests/
│   ├── conftest.py
│   ├── integration/
│   │   ├── test_books_api.py
│   │   └── test_jobs_api.py
│   └── mocks/
│       ├── openai_responses.py
│       └── openlibrary_responses.py
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── alembic.ini
├── pyproject.toml
├── .env.example
└── README.md
```

### Database Schema

```sql
-- ============================================
-- USERS (for JWT auth)
-- ============================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

-- ============================================
-- BOOKS (UUID primary key, grouped by language)
-- ============================================
CREATE TABLE books (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    author VARCHAR(500) NOT NULL,
    language VARCHAR(10) NOT NULL DEFAULT 'en',  -- ISO 639-1 code
    edition VARCHAR(100),                         -- e.g., "1st", "Revised"
    publisher VARCHAR(255),
    pages INTEGER,
    publish_date VARCHAR(50),
    cover_url VARCHAR(1000),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_books_language ON books(language);
CREATE INDEX idx_books_title ON books(title);

-- ============================================
-- BOOK_ISBNS (normalized 1:N relationship)
-- ============================================
CREATE TYPE isbn_type AS ENUM ('isbn10', 'isbn13');

CREATE TABLE book_isbns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    isbn VARCHAR(13) NOT NULL UNIQUE,
    isbn_type isbn_type NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_book_isbns_isbn ON book_isbns(isbn);
CREATE INDEX idx_book_isbns_book_id ON book_isbns(book_id);

-- ============================================
-- CHAPTERS (references Book by UUID)
-- ============================================
CREATE TABLE chapters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    chapter_number INTEGER NOT NULL,
    title VARCHAR(500) NOT NULL,
    summary TEXT NOT NULL,
    audio_file_path VARCHAR(1000),
    audio_url VARCHAR(1000),
    word_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(book_id, chapter_number)
);

CREATE INDEX idx_chapters_book_id ON chapters(book_id);

-- ============================================
-- JOBS (background processing)
-- ============================================
CREATE TYPE job_status AS ENUM ('pending', 'processing', 'completed', 'failed');
CREATE TYPE job_type AS ENUM ('process_book');

CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,  -- nullable for system jobs
    type job_type NOT NULL,
    status job_status NOT NULL DEFAULT 'pending',
    book_id UUID REFERENCES books(id) ON DELETE SET NULL,  -- reference to book being processed
    isbn VARCHAR(13),                                       -- input ISBN used for processing
    error TEXT,
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    current_step VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_user_id ON jobs(user_id);
CREATE INDEX idx_jobs_book_id ON jobs(book_id);
```

### API Endpoints

#### Auth Endpoints (Public)

| Method | Endpoint                | Description       | Request             | Response                     |
| ------ | ----------------------- | ----------------- | ------------------- | ---------------------------- |
| POST   | `/api/v1/auth/register` | Register new user | `{email, password}` | `{user: {...}}`              |
| POST   | `/api/v1/auth/login`    | Login user        | `{email, password}` | `{access_token, token_type}` |
| GET    | `/api/v1/auth/me`       | Get current user  | -                   | `{user: {...}}`              |

#### Protected Endpoints (Require JWT or API Key)

| Method | Endpoint                           | Description           | Request          | Response                                       |
| ------ | ---------------------------------- | --------------------- | ---------------- | ---------------------------------------------- |
| POST   | `/api/v1/books/process`            | Start book processing | `{isbn: string}` | `{job_id, status}`                             |
| GET    | `/api/v1/books`                    | List all books        | -                | `{books: [...]}`                               |
| GET    | `/api/v1/books/{book_id}`          | Get book by UUID      | -                | `{book: {...}, isbns: [...], chapters: [...]}` |
| GET    | `/api/v1/books/isbn/{isbn}`        | Get book by ISBN      | -                | `{book: {...}}`                                |
| GET    | `/api/v1/books/{book_id}/chapters` | Get book chapters     | -                | `{chapters: [...]}`                            |
| GET    | `/api/v1/chapters/{id}`            | Get chapter details   | -                | `{chapter: {...}}`                             |
| GET    | `/api/v1/chapters/{id}/audio`      | Get audio URL         | -                | `{url: string}` or redirect                    |
| GET    | `/api/v1/jobs`                     | List user's jobs      | -                | `{jobs: [...]}`                                |
| GET    | `/api/v1/jobs/{job_id}`            | Get job status        | -                | `{job: {...}}`                                 |

#### Health Endpoints (Public)

| Method | Endpoint        | Description     | Request | Response                        |
| ------ | --------------- | --------------- | ------- | ------------------------------- |
| GET    | `/health/live`  | Liveness probe  | -       | `{status: "ok"}`                |
| GET    | `/health/ready` | Readiness probe | -       | `{status: "ok", checks: {...}}` |

### Error Response Format

```json
{
  "error": {
    "code": "BOOK_NOT_FOUND",
    "message": "Book with ISBN 1234567890 not found",
    "request_id": "abc-123-def"
  }
}
```

### Environment Variables

```bash
# Application
APP_ENV=development|staging|production
DEBUG=true|false
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR
LOG_FORMAT=json|console

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/bookbytes
DATABASE_POOL_MIN=2
DATABASE_POOL_MAX=10

# Redis
REDIS_URL=redis://localhost:6379/0

# Storage
STORAGE_BACKEND=local|s3
LOCAL_STORAGE_PATH=./data/audio
S3_BUCKET=bookbytes-audio
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

# External APIs
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TIMEOUT=30

# Auth
AUTH_MODE=jwt|api_key           # jwt for production, api_key for local dev
JWT_SECRET_KEY=...              # Required for jwt mode
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
API_KEY=dev-api-key-12345       # Only used when AUTH_MODE=api_key

# Worker
WORKER_MAX_JOBS=5               # Max concurrent jobs per worker
```

---

## Appendix A: Migration from Current Codebase

### Mapping: Old → New

| Old Location                               | New Location                                     |
| ------------------------------------------ | ------------------------------------------------ |
| `app.py:Book` dataclass                    | `src/bookbytes/models/book.py` (Book + BookIsbn) |
| `app.py:Chapter` dataclass                 | `src/bookbytes/models/chapter.py`                |
| `app.py:BookBytesApp._init_database()`     | `alembic/versions/001_initial.py`                |
| `app.py:BookBytesApp.fetch_book_details()` | `src/bookbytes/services/metadata_service.py`     |
| `app.py:BookBytesApp.get_chapter_list()`   | `src/bookbytes/services/openai_service.py`       |
| `app.py:BookBytesApp.text_to_speech()`     | `src/bookbytes/services/tts_service.py`          |
| `app.py:BookBytesApp.save_book()`          | `src/bookbytes/repositories/book.py`             |
| `app.py:process_book_api()`                | `src/bookbytes/api/v1/books.py`                  |
| `logger.py`                                | `src/bookbytes/core/logging.py`                  |
| N/A (new)                                  | `src/bookbytes/models/user.py`                   |
| N/A (new)                                  | `src/bookbytes/api/v1/auth.py`                   |
| N/A (new)                                  | `src/bookbytes/core/security.py`                 |

### Preserved Functionality

All existing functionality will be preserved:

- Book metadata fetching from Open Library
- Chapter extraction via OpenAI
- Summary generation via OpenAI
- Audio generation via gTTS
- Book/Chapter CRUD operations

### New Functionality

- JWT authentication with user registration/login
- API key mode for local development bypass
- Background job processing with status tracking
- Multiple ISBNs per book (normalized)
- Book grouping by language

### Breaking Changes

- API endpoints move to `/api/v1/` prefix
- Book identified by UUID, not ISBN (ISBNs are now secondary lookup)
- Processing returns job ID instead of blocking
- Audio served via URL instead of direct file serving
- All protected endpoints require authentication (JWT or API key)
- Response format standardized

---

## Appendix B: Docker Compose Reference

```yaml
version: "3.8"

services:
  api:
    build:
      context: .
      dockerfile: docker/Dockerfile
    command: uvicorn src.bookbytes.main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=development
      - DATABASE_URL=postgresql+asyncpg://bookbytes:bookbytes@postgres:5432/bookbytes
      - REDIS_URL=redis://redis:6379/0
      - STORAGE_BACKEND=local
      - LOCAL_STORAGE_PATH=/data/audio
      - AUTH_MODE=api_key
      - API_KEY=dev-api-key-12345
      - JWT_SECRET_KEY=${JWT_SECRET_KEY:-dev-secret-key-change-in-prod}
    volumes:
      - audio-data:/data/audio
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/live"]
      interval: 10s
      timeout: 5s
      retries: 3

  worker:
    build:
      context: .
      dockerfile: docker/Dockerfile
    command: arq src.bookbytes.workers.settings.WorkerSettings
    environment:
      - APP_ENV=development
      - DATABASE_URL=postgresql+asyncpg://bookbytes:bookbytes@postgres:5432/bookbytes
      - REDIS_URL=redis://redis:6379/0
      - STORAGE_BACKEND=local
      - LOCAL_STORAGE_PATH=/data/audio
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - WORKER_MAX_JOBS=5
    volumes:
      - audio-data:/data/audio
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started

  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=bookbytes
      - POSTGRES_PASSWORD=bookbytes
      - POSTGRES_DB=bookbytes
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U bookbytes"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres-data:
  redis-data:
  audio-data:
```
