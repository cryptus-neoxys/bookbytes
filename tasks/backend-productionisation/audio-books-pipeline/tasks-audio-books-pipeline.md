# Tasks: Audio Books Pipeline

**PRD Reference:** [prd-audio-books-pipeline.md](./prd-audio-books-pipeline.md)  
**Design Doc:** [design-doc.md](./design-doc.md)  
**Parent:** [tasks-backend-productionisation.md](../tasks-backend-productionisation.md)

---

### Phase 0: Storage Service (Prerequisite)

> **Shared with:** [Phase 5 Storage Infrastructure](../tasks-backend-productionisation.md#phase-5-storage--external-services)

- `src/bookbytes/storage/base.py` - Abstract StorageBackend interface
- `src/bookbytes/storage/local.py` - Local filesystem implementation
- `src/bookbytes/storage/s3.py` - S3 implementation with presigned URLs
- `src/bookbytes/storage/__init__.py` - Factory function

### Phase 1: Processing API Endpoints

- `src/bookbytes/schemas/processing.py` - Request/response schemas
- `src/bookbytes/api/v1/processing.py` - Processing router
- `tests/unit/test_processing_endpoints.py` - Unit tests

### Phase 2: Job Infrastructure

- `src/bookbytes/models/job.py` - Job model with status enum
- `src/bookbytes/repositories/job.py` - Job repository
- `alembic/versions/xxx_add_jobs_table.py` - Migration

### Phase 3: LLM Service

- `src/bookbytes/services/llm.py` - LLMProvider protocol + InstructorProvider
- `tests/unit/test_llm_service.py` - Unit tests with mocked responses

### Phase 4: TTS Service

- `src/bookbytes/services/tts.py` - TTSProvider protocol + OpenAIProvider
- `tests/unit/test_tts_service.py` - Unit tests

### Phase 5: Processing Pipeline

- `src/bookbytes/services/processing.py` - ProcessingService orchestration
- `src/bookbytes/workers/settings.py` - ARQ worker settings
- `src/bookbytes/workers/tasks.py` - ARQ task definitions
- `tests/integration/test_processing_pipeline.py` - Integration tests

---

## Dependencies

- **Storage Service** (Phase 5 of backend-productionisation) - Required for storing audio files
- **AudioBook/Chapter models** (Phase 3.A of audio-books-library) - Already exist

---

## Tasks

### Phase 0: Storage Service (If not already implemented)

> Check if storage exists. If not, implement from [Phase 5 Storage tasks](../tasks-backend-productionisation.md).

- [ ] 0.1 Create `storage/base.py` with `StorageBackend` abstract class
  - [ ] `async save(key: str, data: bytes) -> str`
  - [ ] `async get_url(key: str) -> str`
  - [ ] `async delete(key: str) -> bool`
  - [ ] `async exists(key: str) -> bool`

- [ ] 0.2 Create `storage/local.py` with `LocalStorage`
  - [ ] Save to `LOCAL_STORAGE_PATH` config
  - [ ] Return file:// URLs for local dev
  - [ ] Use aiofiles for async I/O

- [ ] 0.3 Create `storage/s3.py` with `S3Storage`
  - [ ] Use aioboto3 for async S3 operations
  - [ ] Generate pre-signed URLs

- [ ] 0.4 Create `storage/__init__.py` factory
  - [ ] `get_storage_backend(settings) -> StorageBackend`

- [ ] 0.5 Add `get_storage()` dependency in `dependencies.py`

---

### Phase 1: Processing API Endpoints

- [ ] 1.1 Create `schemas/processing.py`
  - [ ] `ProcessRequest(edition_id: UUID | None, isbn: str | None)` with validator
  - [ ] `ProcessResponse(job_id, audio_book_id, status, message)`
  - [ ] `JobStatusResponse(id, status, progress, error_message, timestamps)`
  - [ ] `RefreshRequest(force: bool = False)`

- [ ] 1.2 Create `api/v1/processing.py` router
  - [ ] `POST /books/process` - Accept edition_id OR isbn, create job, return job_id
  - [ ] `POST /books/{audio_book_id}/refresh` - Regenerate audiobook
  - [ ] `GET /jobs/{job_id}` - Return job status with progress

- [ ] 1.3 Add processing router to v1 router
  - [ ] Include in `api/v1/router.py`

- [ ] 1.4 Unit tests for endpoints
  - [ ] Test process endpoint validation
  - [ ] Test job status endpoint
  - [ ] Test refresh endpoint

---

### Phase 2: Job Infrastructure

- [ ] 2.1 Create `models/job.py`
  - [ ] `JobStatus` enum (pending, processing, completed, failed)
  - [ ] `JobType` enum (audiobook_generation, audiobook_refresh)
  - [ ] `Job` model with FK to AudioBook, progress tracking

- [ ] 2.2 Generate Alembic migration
  - [ ] Run `alembic revision --autogenerate -m "add_jobs_table"`
  - [ ] Verify migration looks correct
  - [ ] Run migration

- [ ] 2.3 Create `repositories/job.py`
  - [ ] `JobRepository` with status-based queries
  - [ ] `get_by_status()`, `get_pending()`, `update_progress()`

- [ ] 2.4 Configure ARQ worker
  - [ ] Create `workers/settings.py` with `WorkerSettings`
  - [ ] Configure Redis connection from settings

---

### Phase 3: LLM Service

- [ ] 3.1 Add instructor dependency
  - [ ] Add `instructor>=1.0.0` to pyproject.toml
  - [ ] Run `uv sync`

- [ ] 3.2 Create domain models (no library imports)
  - [ ] `ChapterInfo(number, title, summary)` Pydantic model
  - [ ] `ChapterExtraction(chapters: list[ChapterInfo])` Pydantic model
  - [ ] `BookContext(title, author, num_chapters, language)` input model

- [ ] 3.3 Create `LLMProvider` Protocol
  - [ ] Define `extract_chapters(context: BookContext) -> ChapterExtraction`
  - [ ] Document interface contract

- [ ] 3.4 Implement `InstructorLLMProvider`
  - [ ] Initialize with OpenAI client
  - [ ] Use Instructor for structured output
  - [ ] Handle rate limits and retries

- [ ] 3.5 Create `LLMService` wrapper
  - [ ] Accept `LLMProvider` via DI
  - [ ] Provide convenience methods

- [ ] 3.6 Unit tests with mocked LLM responses
  - [ ] Test chapter extraction
  - [ ] Test error handling

---

### Phase 4: TTS Service

- [ ] 4.1 Create `TTSProvider` Protocol
  - [ ] `synthesize(text, voice) -> bytes`
  - [ ] `synthesize_stream(text, voice) -> AsyncIterator[bytes]`

- [ ] 4.2 Implement `OpenAITTSProvider`
  - [ ] Use `openai.audio.speech.create()`
  - [ ] Support voice selection (alloy, echo, fable, onyx, nova, shimmer)
  - [ ] Handle streaming response

- [ ] 4.3 Create `TTSService` wrapper
  - [ ] Accept `TTSProvider` via DI
  - [ ] Provide convenience methods

- [ ] 4.4 Unit tests
  - [ ] Test audio generation (mocked)
  - [ ] Test streaming (mocked)

---

### Phase 5: Processing Pipeline

- [ ] 5.1 Create `services/processing.py`
  - [ ] `ProcessingService` class
  - [ ] `start_processing(edition_id) -> (Job, AudioBook)`
  - [ ] `process_audiobook(job_id, audio_book_id)` - main pipeline
  - [ ] `refresh_audiobook(audio_book_id) -> (Job, AudioBook)`

- [ ] 5.2 Implement processing pipeline
  - [ ] Create AudioBook record (PENDING)
  - [ ] Create Job record
  - [ ] Extract chapters via LLMService
  - [ ] Generate audio for each chapter via TTSService
  - [ ] Store audio files via StorageService
  - [ ] Update Chapter records with audio paths
  - [ ] Update AudioBook status (COMPLETED)

- [ ] 5.3 Create ARQ tasks
  - [ ] `process_audiobook_task(ctx, job_id, audio_book_id)`
  - [ ] Progress updates at stages (20%, 50%, 80%, 100%)
  - [ ] Error handling with job failure status

- [ ] 5.4 Implement retry logic
  - [ ] Exponential backoff (3 attempts)
  - [ ] Partial failure handling (some chapters fail)

- [ ] 5.5 Integration tests
  - [ ] Full pipeline with mocked LLM/TTS
  - [ ] Job status progression
  - [ ] Error scenarios

---

### Phase 6: Dependency Injection Setup

- [ ] 6.1 Add provider factory functions
  - [ ] `get_llm_service()` - returns configured LLMService
  - [ ] `get_tts_service()` - returns configured TTSService
  - [ ] `get_processing_service()` - returns configured ProcessingService

- [ ] 6.2 Provider selection via config
  - [ ] `LLM_PROVIDER` env var (default: "instructor")
  - [ ] `TTS_PROVIDER` env var (default: "openai")

---

## Completion Checklist

- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] ARQ worker starts successfully
- [ ] Full E2E: POST /process → job complete → audio accessible
- [ ] Documentation updated
