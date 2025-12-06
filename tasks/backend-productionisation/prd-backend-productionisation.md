# PRD: Backend Productionisation

**Document Version:** 1.1  
**Created:** 4 December 2025  
**Last Updated:** 4 December 2025  
**Status:** Approved for Implementation  
**Timeline:** 1-2 days (aggressive)

---

## 1. Introduction/Overview

BookBytes is an application that converts physical books (via ISBN) into chapter-wise audio summaries. The current implementation is a working prototype with a monolithic architecture (`app.py` ~700 lines), synchronous processing, SQLite database, and Flask-based API.

This PRD outlines the transformation of the backend from a junior-developer prototype into a production-ready, senior-engineer-quality SaaS backend. The focus is on **technical excellence** with JWT authentication included in this phase (OAuth deferred).

### Problem Statement

The current codebase has several production blockers:

- **Monolithic architecture** makes testing and maintenance difficult
- **Synchronous processing** blocks API responses during long OpenAI/gTTS operations
- **SQLite** doesn't scale and lacks proper connection management
- **No async runtime** limits concurrency and throughput
- **Mixed error handling** leads to inconsistent API responses
- **No job tracking** means clients can't monitor long-running operations
- **Tight coupling** to external services makes testing difficult

### Solution

Restructure the backend using FastAPI with async patterns, PostgreSQL with SQLAlchemy 2.0 async, ARQ for background jobs, and a clean modular architecture following repository/service patterns.

---

## 2. Goals

| #   | Goal                      | Success Criteria                                                                              |
| --- | ------------------------- | --------------------------------------------------------------------------------------------- |
| G1  | **Modular Architecture**  | Codebase split into api/, models/, services/, repositories/ with clear separation of concerns |
| G2  | **Async Runtime**         | All database and HTTP operations use async/await                                              |
| G3  | **Background Processing** | Book processing happens in worker mode with job status tracking                               |
| G4  | **Production Database**   | PostgreSQL with async driver, migrations, and connection pooling                              |
| G5  | **Consistent API**        | Versioned endpoints, Pydantic validation, standardized error responses                        |
| G6  | **Storage Abstraction**   | Pluggable storage (local dev / S3 prod) without code changes                                  |
| G7  | **Observability**         | Structured JSON logging, health checks, graceful shutdown                                     |
| G8  | **Testability**           | Integration tests with mocked external services                                               |
| G9  | **Containerization**      | Docker Compose stack with API, Worker, Postgres, Redis                                        |
| G10 | **JWT Authentication**    | Protected endpoints with JWT tokens; API key mode for local development                       |

---

## 3. User Stories

### API Consumer Stories

| ID  | Story                                                                                                                    | Acceptance Criteria                                                 |
| --- | ------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------- |
| US1 | As an API consumer, I want to submit a book for processing and receive a job ID, so I can track progress without waiting | POST `/api/v1/books/process` returns `{job_id, status}` immediately |
| US2 | As an API consumer, I want to poll job status, so I know when processing is complete                                     | GET `/api/v1/jobs/{job_id}` returns current status and progress     |
| US3 | As an API consumer, I want consistent error responses, so I can handle failures programmatically                         | All errors return `{error: {code, message}}` format                 |
| US4 | As an API consumer, I want to retrieve audio files via URL, so I can stream them directly                                | Audio endpoints return pre-signed URLs (S3) or direct paths (local) |

### Developer Stories

| ID  | Story                                                                       | Acceptance Criteria                                     |
| --- | --------------------------------------------------------------------------- | ------------------------------------------------------- |
| DS1 | As a developer, I want to run the full stack locally with one command       | `docker-compose up` starts API, Worker, Postgres, Redis |
| DS2 | As a developer, I want to run tests with mocked external services           | `pytest` runs without OpenAI/gTTS API calls             |
| DS3 | As a developer, I want to add new features without touching unrelated code  | Each module has single responsibility                   |
| DS4 | As a developer, I want database migrations, so schema changes are versioned | Alembic migrations track all schema changes             |

### Operations Stories

| ID  | Story                                                                                  | Acceptance Criteria                                |
| --- | -------------------------------------------------------------------------------------- | -------------------------------------------------- |
| OS1 | As an operator, I want health check endpoints, so I can configure load balancer probes | `/health/live` and `/health/ready` endpoints exist |
| OS2 | As an operator, I want structured logs, so I can aggregate and search them             | All logs output as JSON with correlation IDs       |
| OS3 | As an operator, I want graceful shutdown, so in-flight requests complete               | SIGTERM allows 30s for cleanup                     |

---

## 4. Functional Requirements

### Phase 1: Project Structure & Configuration

| #     | Requirement                                                                                                                                                   |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| FR1.1 | Create new folder structure under `src/bookbytes/` with modules: `api/`, `models/`, `schemas/`, `repositories/`, `services/`, `workers/`, `core/`, `storage/` |
| FR1.2 | Implement Pydantic Settings class in `config.py` with validation for all environment variables                                                                |
| FR1.3 | Configure FastAPI application factory in `main.py` with lifespan events                                                                                       |
| FR1.4 | Set up dependency injection using FastAPI's `Depends()` pattern                                                                                               |
| FR1.5 | Create `pyproject.toml` for modern Python packaging with all dependencies                                                                                     |
| FR1.6 | Create `.env.example` with all required environment variables documented                                                                                      |

### Phase 2: Database Layer

| #     | Requirement                                                                  |
| ----- | ---------------------------------------------------------------------------- |
| FR2.1 | Create SQLAlchemy 2.0 async models for `Book`, `BookIsbn`, `Chapter`, `Job`, `User` in `models/` |
| FR2.2 | **Book model**: UUID primary key (not ISBN). Group editions by language, keep latest edition per language. Fields: `id` (UUID PK), `title`, `author`, `language` (ISO 639-1), `edition`, `publisher`, `pages`, `publish_date`, `cover_url`, `created_at`, `updated_at` |
| FR2.3 | **BookIsbn model**: Normalized ISBN storage (1:N with Book). Fields: `id` (UUID PK), `book_id` (FK), `isbn` (VARCHAR 13, unique), `isbn_type` (enum: isbn10, isbn13), `created_at`. Index on `isbn` for fast lookups |
| FR2.4 | **Chapter model**: Reference Book by UUID. Fields: `id` (UUID PK), `book_id` (FK), `chapter_number`, `title`, `summary`, `audio_file_path`, `audio_url`, `word_count`, `created_at`, `updated_at`. Unique constraint on `(book_id, chapter_number)` |
| FR2.5 | Implement async database engine and session factory in `core/database.py`    |
| FR2.6 | Configure Alembic for async migrations with `alembic/` directory             |
| FR2.7 | Create initial migration with new schema (fresh start, no SQLite migration)  |
| FR2.8 | Implement repository classes with async CRUD operations                      |
| FR2.9 | Add connection pooling configuration (min 2, max 10 connections)             |
| FR2.10 | Support SQLite (aiosqlite) for local development via config flag            |

### Phase 3: Background Job Queue

| #     | Requirement                                                                            |
| ----- | -------------------------------------------------------------------------------------- |
| FR3.1 | Set up ARQ with Redis connection in `workers/settings.py`                              |
| FR3.2 | Create `process_book_task` that orchestrates the full pipeline                         |
| FR3.3 | Implement `Job` model with status enum: `pending`, `processing`, `completed`, `failed` |
| FR3.4 | Add job progress tracking (percentage, current step)                                   |
| FR3.5 | Create job status API endpoint: GET `/api/v1/jobs/{job_id}`                            |
| FR3.6 | Implement job result storage (success data or error details)                           |
| FR3.7 | Add worker entry point: `arq src.bookbytes.workers.settings.WorkerSettings`            |

### Phase 4: API Layer & Error Handling

| #     | Requirement                                                   |
| ----- | ------------------------------------------------------------- |
| FR4.1 | Create versioned router structure: `/api/v1/`                 |
| FR4.2 | Migrate all Flask endpoints to FastAPI with async handlers    |
| FR4.3 | Implement Pydantic request/response schemas for all endpoints |
| FR4.4 | Create custom exception hierarchy in `core/exceptions.py`     |
| FR4.5 | Add global exception handlers for consistent error responses  |
| FR4.6 | Configure OpenAPI documentation with examples                 |
| FR4.7 | Add request ID middleware for correlation                     |

### Phase 5: Storage & External Services

| #     | Requirement                                                                  |
| ----- | ---------------------------------------------------------------------------- | --- |
| FR5.1 | Create abstract `StorageBackend` interface in `storage/base.py`              |
| FR5.2 | Implement `LocalStorage` for development (saves to `data/audio/`)            |
| FR5.3 | Implement `S3Storage` for production with pre-signed URLs                    |
| FR5.4 | Add storage backend selection via config: `STORAGE_BACKEND=local             | s3` |
| FR5.5 | Wrap OpenAI calls with retry logic (3 retries, exponential backoff)          |
| FR5.6 | Wrap gTTS calls with retry logic (3 retries)                                 |
| FR5.7 | Add configurable timeouts for all external HTTP calls (30s default)          |
| FR5.8 | Create service classes: `OpenAIService`, `TTSService`, `BookMetadataService` |

### Phase 6: JWT Authentication

| #     | Requirement                                                         |
| ----- | ------------------------------------------------------------------- |
| FR6.1 | Implement JWT token structure with `sub`, `exp`, `iat`, `scope` claims |
| FR6.2 | Create `core/security.py` with JWT encode/decode utilities, password hashing |
| FR6.3 | Create `User` model with fields: `id` (UUID), `email`, `hashed_password`, `is_active`, `created_at` |
| FR6.4 | Implement auth middleware with `get_current_user` dependency        |
| FR6.5 | Create auth endpoints: POST `/api/v1/auth/register`, POST `/api/v1/auth/login`, GET `/api/v1/auth/me` |
| FR6.6 | Add `AUTH_MODE` config: `jwt` (production) or `api_key` (local dev bypass) |
| FR6.7 | For `api_key` mode: Accept `X-API-Key` header with configurable static key for local development |
| FR6.8 | Protect all `/api/v1/books/*` and `/api/v1/jobs/*` endpoints with auth |
| FR6.9 | Document OAuth integration points for future implementation (design only) |

### Phase 7: Observability & Deployment

| #     | Requirement                                                             |
| ----- | ----------------------------------------------------------------------- |
| FR7.1 | Configure structlog for JSON logging in `core/logging.py`               |
| FR7.2 | Add proper logging to the codebase                                      |
| FR7.3 | Add correlation ID to all log entries                                   |
| FR7.4 | Create `/health/live` endpoint (always returns 200 if app is running)   |
| FR7.5 | Create `/health/ready` endpoint (checks DB and Redis connectivity)      |
| FR7.6 | Implement graceful shutdown with 30s timeout                            |
| FR7.7 | Create multi-stage `Dockerfile` for optimized image                     |
| FR7.8 | Create `docker-compose.yml` with services: api, worker, postgres, redis |
| FR7.9 | Add volume mounts for local development data persistence                |

---

## 5. Non-Goals (Out of Scope)

| #   | Excluded Item                       | Reason                                         |
| --- | ----------------------------------- | ---------------------------------------------- |
| NG1 | OAuth/Social login                  | Deferred to future phase; JWT auth only for now |
| NG2 | Billing and subscription management | Deferred to future phase                       |
| NG3 | CDN configuration                   | S3 storage only; CDN is infrastructure concern |
| NG4 | Kubernetes deployment               | Docker Compose is target                       |
| NG5 | Load testing                        | This is at internal release stage              |
| NG6 | CLI tool updates                    | Deferred to later                              |
| NG7 | Frontend changes                    | Backend-only scope                             |
| NG8 | Rate limiting implementation        | Design only; implement later                   |
| NG9 | User management UI                  | API-only; auth endpoints only                  |
| NG10 | Email verification flow            | Deferred; users active by default              |
| NG11 | Password reset flow                | Deferred to future phase                       |

---

## 6. Technical Considerations

### Technology Stack

| Component     | Technology           | Rationale                                        |
| ------------- | -------------------- | ------------------------------------------------ |
| Web Framework | FastAPI 0.109+       | Async-native, auto OpenAPI, Pydantic integration |
| Async Runtime | uvicorn + uvloop     | High-performance ASGI server                     |
| Database      | PostgreSQL 16        | Production-grade, async support                  |
| ORM           | SQLAlchemy 2.0 async | Modern async patterns, type hints                |
| Migrations    | Alembic              | SQLAlchemy-native, versioned migrations          |
| Job Queue     | ARQ                  | Async-native, Redis-based, simple                |
| Validation    | Pydantic v2          | FastAPI integration, performance                 |
| HTTP Client   | httpx                | Async HTTP client                                |
| Logging       | structlog            | Structured JSON logging                          |
| Storage       | boto3/aioboto3       | S3-compatible storage                            |

---

## 7. Success Metrics

| Metric                  | Target                     | Measurement               |
| ----------------------- | -------------------------- | ------------------------- |
| API Response Time (p95) | < 200ms for sync endpoints | Logs / APM                |
| Job Processing Time     | < 5min per book            | Job completion timestamps |
| Test Coverage           | > 70% on critical paths    | pytest-cov                |
| Error Rate              | < 1%                       | Log aggregation           |
| Build Time              | < 2min                     | CI/CD pipeline            |
| Container Image Size    | < 500MB                    | Docker                    |

---

## 8. Open Questions

| #   | Question                                                    | Status  | Decision                                  |
| --- | ----------------------------------------------------------- | ------- | ----------------------------------------- |
| Q1  | Should we keep backward compatibility with Flask endpoints? | Decided | No - clean break with v1 API              |
| Q2  | How to handle in-flight jobs during deployment?             | Decided | Graceful shutdown with proper status tracking; worker waits for current job before terminating |
| Q3  | Should audio files have expiring URLs?                      | Decided | No - audio files managed via Books/Chapters lifecycle; no URL expiration |
| Q4  | Max concurrent jobs per worker?                             | Decided | 5 concurrent jobs (configurable via `WORKER_MAX_JOBS` env var) |
| Q5  | How to handle Book identity across editions?                | Decided | UUID primary key; ISBNs stored as array; group by language; keep latest edition per language |

---

## 9. Implementation Phases

### Phase 1: Project Structure & Configuration

**Duration:** 2-3 hours  
**Files:** `pyproject.toml`, `src/bookbytes/config.py`, `src/bookbytes/main.py`, folder structure  
**Deliverable:** Runnable FastAPI app with config system

### Phase 2: Database Layer

**Duration:** 2-3 hours  
**Files:** `models/`, `repositories/`, `core/database.py`, `alembic/`  
**Deliverable:** Async database with migrations

### Phase 3: Background Job Queue

**Duration:** 2-3 hours  
**Files:** `workers/`, `models/job.py`, `api/v1/jobs.py`  
**Deliverable:** ARQ worker processing books asynchronously

### Phase 4: API Layer & Error Handling

**Duration:** 2-3 hours  
**Files:** `api/v1/`, `schemas/`, `core/exceptions.py`  
**Deliverable:** Full API with validation and error handling

### Phase 5: Storage & External Services

**Duration:** 1-2 hours  
**Files:** `storage/`, `services/`  
**Deliverable:** Pluggable storage and resilient external calls

### Phase 6: JWT Authentication

**Duration:** 1-2 hours  
**Files:** `core/security.py`, `models/user.py`, `api/v1/auth.py`, `schemas/auth.py`  
**Deliverable:** Working JWT auth with user registration/login; API key bypass for local dev

### Phase 7: Observability & Deployment

**Duration:** 1-2 hours  
**Files:** `core/logging.py`, `docker/`, health endpoints  
**Deliverable:** Production-ready Docker stack

---

_This PRD will be used to generate detailed task lists for each phase._
