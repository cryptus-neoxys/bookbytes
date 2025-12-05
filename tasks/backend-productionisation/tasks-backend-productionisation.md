# Tasks: Backend Productionisation

**PRD Reference:** [prd-backend-productionisation.md](./prd-backend-productionisation.md)  
**Technical Reference:** [technical-considerations-backend-productionisation.md](./technical-considerations-backend-productionisation.md)  
**Branch:** `feat/productionise-and-saasify`

---

## Relevant Files

### Phase 1: Project Structure & Configuration

- `pyproject.toml` - Modern Python packaging with all dependencies
- `src/bookbytes/__init__.py` - Package initialization
- `src/bookbytes/main.py` - FastAPI application factory with lifespan events
- `src/bookbytes/config.py` - Pydantic Settings class for environment validation
- `src/bookbytes/dependencies.py` - FastAPI dependency injection container
- `.env.example` - Documented environment variables template

### Incremental Phase (2): Database Layer

- `src/bookbytes/core/__init__.py` - Core module initialization
- `src/bookbytes/core/database.py` - Async engine, session factory, connection pooling
- `src/bookbytes/models/__init__.py` - Models package with exports
- `src/bookbytes/models/base.py` - SQLAlchemy base model with common mixins
- `src/bookbytes/models/user.py` - User model for authentication
- `src/bookbytes/models/book.py` - Book and BookIsbn models
- `src/bookbytes/models/chapter.py` - Chapter model
- `src/bookbytes/models/job.py` - Job model with status enum
- `src/bookbytes/repositories/__init__.py` - Repositories package
- `src/bookbytes/repositories/base.py` - Generic async repository base class
- `src/bookbytes/repositories/user.py` - User repository
- `src/bookbytes/repositories/book.py` - Book and BookIsbn repositories
- `src/bookbytes/repositories/chapter.py` - Chapter repository
- `src/bookbytes/repositories/job.py` - Job repository
- `alembic.ini` - Alembic configuration
- `alembic/env.py` - Async migration environment
- `alembic/script.py.mako` - Migration template
- `alembic/versions/001_initial_schema.py` - Initial database migration

### Phase 3: Background Job Queue

- `src/bookbytes/workers/__init__.py` - Workers package
- `src/bookbytes/workers/settings.py` - ARQ worker configuration
- `src/bookbytes/workers/tasks.py` - Job task definitions (process_book_task)
- `src/bookbytes/api/v1/jobs.py` - Job status API endpoints

### Phase 4: API Layer & Error Handling

- `src/bookbytes/core/exceptions.py` - Custom exception hierarchy
- `src/bookbytes/api/__init__.py` - API package
- `src/bookbytes/api/v1/__init__.py` - V1 API package
- `src/bookbytes/api/v1/router.py` - Main v1 router combining all endpoints
- `src/bookbytes/api/v1/books.py` - Book endpoints (process, list, get, chapters)
- `src/bookbytes/api/v1/chapters.py` - Chapter endpoints (get, audio)
- `src/bookbytes/api/v1/health.py` - Health check endpoints
- `src/bookbytes/schemas/__init__.py` - Schemas package
- `src/bookbytes/schemas/common.py` - Shared schemas (ErrorResponse, PaginatedResponse)
- `src/bookbytes/schemas/book.py` - Book request/response schemas
- `src/bookbytes/schemas/chapter.py` - Chapter schemas
- `src/bookbytes/schemas/job.py` - Job schemas

### Phase 5: Storage & External Services

- `src/bookbytes/storage/__init__.py` - Storage package
- `src/bookbytes/storage/base.py` - Abstract StorageBackend interface
- `src/bookbytes/storage/local.py` - LocalStorage implementation
- `src/bookbytes/storage/s3.py` - S3Storage implementation with pre-signed URLs
- `src/bookbytes/services/__init__.py` - Services package
- `src/bookbytes/services/book_service.py` - Book processing orchestration
- `src/bookbytes/services/metadata_service.py` - Open Library API client
- `src/bookbytes/services/openai_service.py` - OpenAI API wrapper with retries
- `src/bookbytes/services/tts_service.py` - gTTS wrapper with retries

### Phase 6: JWT Authentication

- `src/bookbytes/core/security.py` - JWT encode/decode, password hashing
- `src/bookbytes/api/v1/auth.py` - Auth endpoints (register, login, me)
- `src/bookbytes/schemas/auth.py` - Auth request/response schemas

### Phase 7: Observability & Deployment

- `src/bookbytes/core/logging.py` - Structlog configuration with correlation IDs
- `docker/Dockerfile` - Multi-stage production Dockerfile
- `docker/docker-compose.yml` - Full stack: api, worker, postgres, redis

### Tests

- `tests/__init__.py` - Tests package
- `tests/conftest.py` - Pytest fixtures (async client, mock services, test DB)
- `tests/mocks/__init__.py` - Mock responses package
- `tests/mocks/openai_responses.py` - OpenAI API mock responses
- `tests/mocks/openlibrary_responses.py` - Open Library mock responses
- `tests/integration/__init__.py` - Integration tests package
- `tests/integration/test_auth_api.py` - Auth endpoint tests
- `tests/integration/test_books_api.py` - Books endpoint tests
- `tests/integration/test_jobs_api.py` - Jobs endpoint tests

### Notes

- This task list follows the 7-phase structure defined in the PRD
- All source code lives under `src/bookbytes/` for proper Python packaging
- Tests use pytest-asyncio for async test support
- Use `pytest tests/` to run all tests, or `pytest tests/integration/test_books_api.py` for specific tests
- Use `alembic upgrade head` to run migrations
- Use `docker-compose -f docker/docker-compose.yml up` to start the full stack
- Environment variables are validated at startup via Pydantic Settings

---

## Instructions for Completing Tasks

**IMPORTANT:** As you complete each task, you must check it off in this markdown file by changing `- [ ]` to `- [x]`. This helps track progress and ensures you don't skip any steps.

Example:

- `- [ ] 1.1 Read file` → `- [x] 1.1 Read file` (after completing)

Update the file after completing each sub-task, not just after completing an entire parent task.

---

## Tasks

- [x] 1.0 **Phase 1: Project Structure & Configuration**

  - [x] 1.1 Create the new folder structure: `src/bookbytes/` with subdirectories `api/`, `api/v1/`, `models/`, `schemas/`, `repositories/`, `services/`, `workers/`, `core/`, `storage/`
  - [x] 1.2 Create `__init__.py` files in each package directory to make them proper Python packages
  - [x] 1.3 Create `pyproject.toml` with project metadata, all dependencies from technical-considerations doc, and optional dev dependencies (pytest, ruff, etc.)
  - [x] 1.4 Create `src/bookbytes/config.py` with Pydantic `Settings` class that validates all environment variables: `APP_ENV`, `DEBUG`, `LOG_LEVEL`, `DATABASE_URL`, `REDIS_URL`, `STORAGE_BACKEND`, `AUTH_MODE`, `JWT_SECRET_KEY`, `OPENAI_API_KEY`, etc.
  - [x] 1.5 Create `src/bookbytes/main.py` with FastAPI application factory using `@asynccontextmanager` lifespan for startup/shutdown events (initialize DB, Redis connections)
  - [x] 1.6 Create `src/bookbytes/dependencies.py` with dependency injection functions: `get_settings()`, `get_db_session()`, `get_redis()` using FastAPI's `Depends()` pattern
  - [x] 1.7 Create `.env.example` with all environment variables documented with comments explaining each one
  - [x] 1.8 Verify the app starts: `uvicorn src.bookbytes.main:app --reload` should show FastAPI running (even with placeholder routes)

- [x] 2.0 **Phase 2: Database Foundation**

  - [x] 2.1 Create `src/bookbytes/core/database.py` with async SQLAlchemy engine using `create_async_engine()`, `async_sessionmaker`, and connection pool settings (pool_size=2, max_overflow=8)
  - [x] 2.2 Create `src/bookbytes/models/base.py` with `Base = declarative_base()` and a `TimestampMixin` class that adds `created_at` and `updated_at` columns with auto-update triggers
  - [x] 2.3 Create `src/bookbytes/models/__init__.py` that exports Base (will be extended as models are added in subsequent phases)
  - [x] 2.4 Initialize Alembic: Run `alembic init alembic` and configure `alembic.ini` with async driver support
  - [x] 2.5 Update `alembic/env.py` to use async migrations with `run_async_migrations()` function, import Base from models, use `target_metadata = Base.metadata`
  - [x] 2.6 Create `src/bookbytes/repositories/base.py` with generic `BaseRepository[T]` class providing async `get_by_id()`, `get_all()`, `create()`, `update()`, `delete()` methods
  - [x] 2.7 Add database session dependency to `dependencies.py`: async generator `get_db_session()` that yields session and handles commit/rollback
  - [x] 2.8 Update `main.py` lifespan to initialize and close database connection
  - [x] 2.9 Update `/health/ready` to check database connectivity with `SELECT 1`
  - [x] 2.10 Create `tests/integration/test_database.py` to verify database connection and session lifecycle
  - [ ] 2.11 Test database setup: Start postgres via docker-compose, verify connection works

- [ ] 3.0 **Phase 3: Background Job Queue**

  - [ ] 3.1 Create `src/bookbytes/models/job.py` with `Job` model: `id` (UUID, PK), `user_id` (FK, nullable), `type` (Enum: process_book), `status` (Enum: pending, processing, completed, failed), `book_id` (FK, nullable), `isbn`, `error`, `progress` (0-100), `current_step`, timestamps including `started_at`, `completed_at`
  - [ ] 3.2 Create `src/bookbytes/repositories/job.py` with `JobRepository` adding `get_by_user_id()`, `get_pending_jobs()`, `update_status()`, `update_progress()`
  - [ ] 3.3 Generate migration for Job model: `alembic revision --autogenerate -m "add_job_model"`
  - [ ] 3.4 Create `src/bookbytes/workers/settings.py` with ARQ `WorkerSettings` class: define `redis_settings` from config, `functions` list, `max_jobs=5` (from `WORKER_MAX_JOBS` env var), `job_timeout=600` (10 min for book processing)
  - [ ] 3.5 Create `src/bookbytes/workers/tasks.py` with `process_book_task(ctx, job_id: str, isbn: str)` async function that will orchestrate the pipeline (placeholder implementation for now)
  - [ ] 3.6 Implement job lifecycle in `process_book_task`: update job status to `processing` at start, update `progress` and `current_step` during execution, set `completed` or `failed` at end
  - [ ] 3.7 Define processing steps as constants: `STEP_FETCHING_METADATA = "fetching_metadata"`, `STEP_EXTRACTING_CHAPTERS = "extracting_chapters"`, `STEP_GENERATING_SUMMARIES = "generating_summaries"`, `STEP_CREATING_AUDIO = "creating_audio"`
  - [ ] 3.8 Add startup hook in `workers/settings.py` to initialize database session factory for use within worker tasks
  - [ ] 3.9 Create `src/bookbytes/schemas/job.py` with Pydantic schemas: `JobCreate(isbn: str)`, `JobResponse(id, type, status, progress, current_step, created_at, ...)`, `JobListResponse(jobs: list[JobResponse])`
  - [ ] 3.10 Create `src/bookbytes/api/v1/jobs.py` with endpoints: `GET /jobs` (list user's jobs), `GET /jobs/{job_id}` (get job status with progress)
  - [ ] 3.11 Add job enqueueing logic: Create helper function `enqueue_book_processing(redis, job_id, isbn)` that uses ARQ's `enqueue_job()`
  - [ ] 3.12 Test worker starts: Run `arq src.bookbytes.workers.settings.WorkerSettings` and verify it connects to Redis and waits for jobs
  - [ ] 3.13 Create `tests/integration/test_jobs_api.py` with tests: list jobs for user, get job status, verify job progress updates

- [ ] 4.0 **Phase 4: API Layer & Error Handling**

  - [x] 4.1 Create `src/bookbytes/core/exceptions.py` with exception hierarchy: `BookBytesError(Exception)` base class with `code` and `message` attributes, then `BookNotFoundError`, `ChapterNotFoundError`, `JobNotFoundError`, `ISBNNotFoundError`, `AuthenticationError`, `AuthorizationError` _(DONE - moved to auxiliary foundation)_
  - [x] 4.2 Create `src/bookbytes/schemas/common.py` with shared schemas: `ErrorDetail(code: str, message: str, request_id: str | None)`, `ErrorResponse(error: ErrorDetail)`, `PaginatedResponse[T](items: list[T], total: int, page: int, size: int)` _(DONE - moved to auxiliary foundation)_
  - [x] 4.3 Add global exception handlers in `main.py`: register handlers for `BookBytesError` (return 400 with ErrorResponse), `HTTPException` (pass through), `Exception` (log and return 500) _(DONE - integrated with 4.1)_
  - [x] 4.4 Create request ID middleware in `main.py`: Use `starlette.middleware` to add `X-Request-ID` header (generate UUID if not present), store in request state for logging _(DONE - completed in Phase 1 and logging setup)_
  - [ ] 4.5 Create `src/bookbytes/models/book.py` with `Book` model: `id` (UUID, PK), `title`, `author`, `language` (default 'en'), `edition`, `publisher`, `pages`, `publish_date`, `cover_url`, timestamps. Add relationship to `BookIsbn` and `Chapter`
  - [ ] 4.6 Create `src/bookbytes/models/book.py` with `BookIsbn` model in same file: `id` (UUID, PK), `book_id` (FK to books), `isbn` (unique), `isbn_type` (Enum: isbn10, isbn13), `created_at`. Add index on `isbn`
  - [ ] 4.7 Create `src/bookbytes/models/chapter.py` with `Chapter` model: `id` (UUID, PK), `book_id` (FK), `chapter_number`, `title`, `summary`, `audio_file_path`, `audio_url`, `word_count`, timestamps. Add unique constraint on `(book_id, chapter_number)`
  - [ ] 4.8 Create `src/bookbytes/repositories/book.py` with `BookRepository` (add `get_by_language()`, `get_latest_by_title_language()`) and `BookIsbnRepository` (add `get_by_isbn()`, `get_isbns_for_book()`)
  - [ ] 4.9 Create `src/bookbytes/repositories/chapter.py` with `ChapterRepository` adding `get_by_book_id()`, `get_by_book_and_number()`
  - [ ] 4.10 Generate migration for Book, BookIsbn, Chapter models: `alembic revision --autogenerate -m "add_book_chapter_models"`
  - [ ] 4.11 Create `src/bookbytes/schemas/book.py` with schemas: `BookCreate(isbn: str)`, `BookIsbnResponse(isbn, isbn_type)`, `BookResponse(id, title, author, language, ..., isbns: list[BookIsbnResponse])`, `BookListResponse(books: list[BookResponse])`, `ProcessBookRequest(isbn: str)`, `ProcessBookResponse(job_id, status)`
  - [ ] 4.12 Create `src/bookbytes/api/v1/books.py` with endpoints: `POST /books/process` (enqueue processing, return job_id), `GET /books` (list all books), `GET /books/{book_id}` (get by UUID), `GET /books/isbn/{isbn}` (get by ISBN), `GET /books/{book_id}/chapters` (list chapters)
  - [ ] 4.13 Create `src/bookbytes/api/v1/chapters.py` with endpoints: `GET /chapters/{chapter_id}` (get chapter details), `GET /chapters/{chapter_id}/audio` (return audio URL or redirect)
  - [ ] 4.14 Create `src/bookbytes/api/v1/health.py` with endpoints: `GET /health/live` (always returns 200 `{"status": "ok"}`), `GET /health/ready` (checks DB and Redis, returns checks object)
  - [ ] 4.15 Create `src/bookbytes/api/v1/router.py` that combines all routers using `APIRouter()` and `include_router()` with appropriate prefixes and tags
  - [ ] 4.16 Include v1 router in `main.py` under `/api/v1` prefix
  - [ ] 4.17 Configure OpenAPI in `main.py`: Set title, description, version, add example responses to endpoints using `responses` parameter
  - [ ] 4.18 Verify API documentation: Access `/docs` and `/redoc` endpoints, ensure all endpoints are documented with request/response examples
  - [ ] 4.19 Create `tests/integration/test_books_api.py` with tests: process book (returns job_id), list books, get book by id, get book by isbn (404 for unknown), get chapters for book

- [ ] 5.0 **Phase 5: Storage & External Services**

  - [ ] 5.1 Create `src/bookbytes/storage/base.py` with abstract `StorageBackend` class defining interface: `async save(key: str, data: bytes) -> str`, `async get_url(key: str) -> str`, `async delete(key: str) -> bool`, `async exists(key: str) -> bool`
  - [ ] 5.2 Create `src/bookbytes/storage/local.py` with `LocalStorage(StorageBackend)` implementation: saves files to `LOCAL_STORAGE_PATH`, returns file:// URLs for local dev, uses aiofiles for async I/O
  - [ ] 5.3 Create `src/bookbytes/storage/s3.py` with `S3Storage(StorageBackend)` implementation: uses aioboto3 for async S3 operations, generates pre-signed URLs with configurable expiry (default: no expiry), handles bucket operations
  - [ ] 5.4 Create `src/bookbytes/storage/__init__.py` with factory function `get_storage_backend(settings) -> StorageBackend` that returns LocalStorage or S3Storage based on `STORAGE_BACKEND` config
  - [ ] 5.5 Add storage backend dependency in `dependencies.py`: `get_storage()` that uses the factory function
  - [ ] 5.6 Create `src/bookbytes/services/metadata_service.py` with `BookMetadataService` class: async `fetch_by_isbn(isbn: str) -> BookMetadata` using httpx to call Open Library API, parse response into dataclass, handle not found
  - [ ] 5.7 Add retry logic to `BookMetadataService` using tenacity: `@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))`, log retries
  - [ ] 5.8 Create `src/bookbytes/services/openai_service.py` with `OpenAIService` class: async methods `extract_chapters(book_title, author) -> list[ChapterInfo]`, `generate_summary(book_title, chapter_title) -> str` using OpenAI async client
  - [ ] 5.9 Add retry logic to `OpenAIService` methods using tenacity with exponential backoff, handle rate limits and API errors gracefully
  - [ ] 5.10 Create `src/bookbytes/services/tts_service.py` with `TTSService` class: method `generate_audio(text: str, output_key: str) -> str` that uses gTTS (runs in thread executor since gTTS is sync), saves to storage backend, returns URL
  - [ ] 5.11 Add retry logic to `TTSService` using tenacity: 3 retries with exponential backoff for transient failures
  - [ ] 5.12 Create `src/bookbytes/services/book_service.py` with `BookService` class that orchestrates the full pipeline: `async process_book(isbn: str, job_id: str)` that coordinates MetadataService → OpenAIService → TTSService, updates job progress
  - [ ] 5.13 Add configurable timeouts to all HTTP clients: Set `timeout=httpx.Timeout(30.0)` in httpx clients, `request_timeout=30` in OpenAI client
  - [ ] 5.14 Wire up `BookService` in `process_book_task`: Instantiate services, call `book_service.process_book()`, handle exceptions and update job status accordingly
  - [ ] 5.15 Add service dependencies in `dependencies.py`: `get_metadata_service()`, `get_openai_service()`, `get_tts_service()`, `get_book_service()`

- [ ] 6.0 **Phase 6: JWT Authentication**

  - [ ] 6.1 Create `src/bookbytes/models/user.py` with `User` model: `id` (UUID, PK), `email` (unique), `hashed_password`, `is_active` (default True), timestamps
  - [ ] 6.2 Create `src/bookbytes/repositories/user.py` with `UserRepository` extending base, adding `get_by_email()` method
  - [ ] 6.3 Generate migration for User model: `alembic revision --autogenerate -m "add_user_model"`
  - [ ] 6.4 Create `src/bookbytes/core/security.py` with password utilities: `hash_password(password: str) -> str` using passlib bcrypt, `verify_password(plain: str, hashed: str) -> bool`
  - [ ] 6.2 Add JWT utilities in `security.py`: `create_access_token(data: dict, expires_delta: timedelta | None) -> str` using python-jose, `decode_access_token(token: str) -> dict` with validation
  - [ ] 6.3 Define JWT payload structure in `security.py`: `TokenPayload` dataclass with `sub` (user_id), `exp`, `iat`, `scope` (default: "access")
  - [ ] 6.4 Create `src/bookbytes/schemas/auth.py` with schemas: `UserCreate(email: EmailStr, password: str)`, `UserLogin(email: EmailStr, password: str)`, `UserResponse(id, email, is_active, created_at)`, `TokenResponse(access_token: str, token_type: str = "bearer")`
  - [ ] 6.5 Create `src/bookbytes/api/v1/auth.py` with endpoints: `POST /auth/register` (create user, return UserResponse), `POST /auth/login` (validate credentials, return TokenResponse), `GET /auth/me` (return current user)
  - [ ] 6.6 Create auth dependency in `dependencies.py`: `get_current_user(token: str = Depends(oauth2_scheme))` that decodes JWT, fetches user from DB, raises 401 if invalid
  - [ ] 6.7 Create optional auth dependency: `get_current_user_optional()` that returns None if no token, for endpoints that work with or without auth
  - [ ] 6.8 Implement API key bypass for local dev: In `get_current_user()`, if `AUTH_MODE=api_key`, check `X-API-Key` header against `API_KEY` config, return a mock/system user
  - [ ] 6.9 Add `oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")` in dependencies for Swagger UI integration
  - [ ] 6.10 Protect book and job endpoints: Add `current_user: User = Depends(get_current_user)` to all endpoints in `books.py` and `jobs.py`
  - [ ] 6.11 Filter jobs by user: Update `GET /jobs` to only return jobs where `job.user_id == current_user.id`
  - [ ] 6.12 Include auth router in v1 router with `/auth` prefix
  - [ ] 6.13 Test auth flow: Verify register → login → access protected endpoint with token works; verify 401 without token
  - [ ] 6.14 Create `tests/integration/test_auth_api.py` with tests: register new user, login with valid credentials, login with invalid credentials (401), access /me with token, access /me without token (401)

- [ ] 7.0 **Phase 7: Observability & Deployment**
  - [x] 7.1 Create `src/bookbytes/core/logging.py` with structlog configuration: Configure `structlog.configure()` with processors for JSON output (prod) or console (dev), add timestamp, log level, logger name _(DONE - moved to auxiliary foundation)_
  - [x] 7.2 Add correlation ID processor in logging: Extract `request_id` from context, add to all log entries _(DONE - moved to auxiliary foundation)_
  - [x] 7.3 Create logging middleware in `main.py`: Log request start (method, path, request*id), log request end (status_code, duration_ms), bind request_id to structlog context *(DONE - moved to auxiliary foundation)\_
  - [x] ~~7.4 Replace all `print()` and basic logging calls throughout codebase with structlog~~ _(OBSOLETE - logging established from start, no print statements to replace)_
  - [ ] 7.5 Add structured logging to worker tasks: Log job start, each step transition, completion/failure with job_id context
  - [ ] 7.6 Enhance health endpoints: `/health/ready` should check DB connection (`SELECT 1`), Redis ping, return `{"status": "ok", "checks": {"database": "ok", "redis": "ok"}}` or appropriate error status
  - [ ] 7.7 Implement graceful shutdown in `main.py` lifespan: On shutdown, wait for in-flight requests (30s timeout), close DB connections, close Redis connections
  - [ ] 7.8 Add graceful shutdown to worker: Configure ARQ's `on_shutdown` hook to wait for current job completion before exiting
  - [x] 7.9 Create `docker/Dockerfile` with multi-stage build: Stage 1 (builder) installs dependencies, Stage 2 (runtime) copies only needed files, uses slim Python image, runs as non-root user _(DONE - moved to auxiliary foundation)_
  - [x] 7.10 Create `docker/docker-compose.yml` with services: `api` (uvicorn), `worker` (arq), `postgres` (postgres:16-alpine), `redis` (redis:7-alpine) with health checks, volumes, and proper depends*on conditions *(DONE - moved to auxiliary foundation)\_
  - [x] 7.11 Add volume mounts in docker-compose: `postgres-data` for database persistence, `redis-data` for Redis persistence, `audio-data` for local audio file storage _(DONE - moved to auxiliary foundation)_
  - [x] 7.12 Configure environment variables in docker-compose: Use `${VAR:-default}` syntax for secrets, set development defaults for local use _(DONE - moved to auxiliary foundation)_
  - [ ] 7.13 Test full stack: Run `docker-compose up --build`, verify all services start, health checks pass, can register user and process book
  - [x] 7.14 Create `tests/conftest.py` with pytest fixtures: `async_client` (TestClient with async support), `test_db_session` (isolated test database), `mock_openai_service`, `mock_tts_service`, `authenticated_client` (client with valid JWT) _(DONE - moved to auxiliary foundation)_
  - [ ] 7.15 Verify all tests pass: Run `pytest tests/ -v` and ensure all tests pass with mocked external services
