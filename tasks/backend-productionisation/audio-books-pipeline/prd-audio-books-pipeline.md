# PRD: Audio Books Pipeline

**Document Version:** 1.0  
**Created:** 11 December 2025  
**Status:** Draft  
**Timeline:** Urgent (hours, target completion in 1-2 days)

---

## 1. Introduction/Overview

The Audio Books Pipeline transforms book editions into chapter-wise audio summaries using LLM and TTS services. This is the core value-delivery component of BookBytes - converting a 250-page book into 15-20 audio summaries of ~5 minutes each.

### Problem Statement

Users want to consume books faster without losing key insights. Reading full books is time-consuming, and existing audiobooks are just narrations of the full text.

### Solution

An automated pipeline that:
1. Uses LLM to extract chapter summaries from book metadata
2. Converts summaries to natural-sounding audio via TTS
3. Stores and serves audio files to users

---

## 2. Goals

| #   | Goal                         | Success Criteria                                                    |
| --- | ---------------------------- | ------------------------------------------------------------------- |
| G1  | **Production Architecture**  | Provider-agnostic design allowing LLM/TTS switching without code changes |
| G2  | **Revenue Enablement**       | Working pipeline that processes books end-to-end                    |
| G3  | **Quality Output**           | Structured summaries with clear, natural audio                      |
| G4  | **Reliability**              | Retry logic, partial success handling, job progress tracking        |
| G5  | **Observability**            | Full job status visibility, error diagnostics                       |

---

## 3. User Stories

### API Consumer Stories

| ID  | Story                                                                                      | Acceptance Criteria                                      |
| --- | ------------------------------------------------------------------------------------------ | -------------------------------------------------------- |
| US1 | As a user, I want to submit a book for processing and get a job ID                        | `POST /books/process` returns `{job_id, status}` immediately |
| US2 | As a user, I want to poll job status to know when my audiobook is ready                   | `GET /jobs/{id}` shows progress 0-100%                   |
| US3 | As a user, I want to listen to generated chapter summaries                                 | Chapter audio files are accessible via URL               |
| US4 | As a user, I want to refresh an audiobook when I want updated summaries                    | `POST /books/{id}/refresh` creates new version           |

### Developer Stories

| ID  | Story                                                                                      | Acceptance Criteria                                      |
| --- | ------------------------------------------------------------------------------------------ | -------------------------------------------------------- |
| DS1 | As a developer, I want to switch LLM providers without changing business logic             | Provider configured via DI, Protocol interface           |
| DS2 | As a developer, I want to switch TTS providers without changing business logic             | Provider configured via DI, Protocol interface           |
| DS3 | As a developer, I want failed jobs to retry automatically                                  | ARQ retry logic with exponential backoff                 |
| DS4 | As a developer, I want to test the pipeline without calling real APIs                      | Mocked providers work in tests                           |

---

## 4. Functional Requirements

### Phase 1: API Endpoints

| #      | Requirement                                                                |
| ------ | -------------------------------------------------------------------------- |
| FR1.1  | Create `POST /api/v1/books/process` endpoint accepting `edition_id` or `isbn` |
| FR1.2  | Return `job_id` and `audio_book_id` immediately (async processing)        |
| FR1.3  | Create `GET /api/v1/jobs/{job_id}` endpoint for status polling            |
| FR1.4  | Job status includes: `pending`, `processing`, `completed`, `failed`       |
| FR1.5  | Job response includes `progress` (0-100) and `error_message` if failed    |
| FR1.6  | Create `POST /api/v1/books/{audio_book_id}/refresh` for regeneration      |
| FR1.7  | Refresh increments audiobook `version` and creates new job                |

### Phase 2: Job Infrastructure

| #      | Requirement                                                                |
| ------ | -------------------------------------------------------------------------- |
| FR2.1  | Create `Job` model with `job_type`, `status`, `progress`, `audio_book_id` |
| FR2.2  | Create Alembic migration for `jobs` table                                 |
| FR2.3  | Create `JobRepository` with async CRUD                                    |
| FR2.4  | Configure ARQ worker settings in `workers/settings.py`                    |

### Phase 3: LLM Service

| #      | Requirement                                                                |
| ------ | -------------------------------------------------------------------------- |
| FR3.1  | Define `LLMProvider` Protocol with `extract_chapters()` method            |
| FR3.2  | Create `BookContext` and `ChapterExtraction` Pydantic models              |
| FR3.3  | Implement `InstructorLLMProvider` using Instructor library                |
| FR3.4  | Create `LLMService` thin wrapper that delegates to provider               |
| FR3.5  | Extract chapter number, title, and summary for each chapter               |
| FR3.6  | Provider selection via dependency injection                               |

### Phase 4: TTS Service

| #      | Requirement                                                                |
| ------ | -------------------------------------------------------------------------- |
| FR4.1  | Define `TTSProvider` Protocol with `synthesize()` and `synthesize_stream()` |
| FR4.2  | Implement `OpenAITTSProvider` using OpenAI TTS API                        |
| FR4.3  | Create `TTSService` wrapper that delegates to provider                    |
| FR4.4  | Support voice selection (default: "alloy")                                |
| FR4.5  | Return audio as bytes or async stream                                     |

### Phase 5: Processing Pipeline

| #      | Requirement                                                                |
| ------ | -------------------------------------------------------------------------- |
| FR5.1  | Create `ProcessingService` orchestrating LLM → TTS → Storage              |
| FR5.2  | Create ARQ task `process_audiobook_task` in `workers/tasks.py`            |
| FR5.3  | Update job progress at each stage (20%, 50%, 80%, 100%)                   |
| FR5.4  | Handle partial failures (some chapters fail, others succeed)              |
| FR5.5  | Implement retry logic with exponential backoff (3 attempts)               |
| FR5.6  | Store audio files via StorageService (local dev / S3 prod)                |
| FR5.7  | Update `AudioBook` status on completion/failure                           |
| FR5.8  | Store chapter audio paths/URLs in `Chapter` records                       |

---

## 5. Non-Goals (Out of Scope)

- **Multiple TTS providers implemented** - Architecture ready, only OpenAI initially
- **Multiple LLM providers implemented** - Architecture ready, only OpenAI/Instructor initially
- **User notifications** - No push notifications on job completion (polling only)
- **Audio file management UI** - API only, no admin interface
- **Voice customization per user** - Single voice initially
- **Real-time streaming to client** - Files generated then served, no live streaming

---

## 6. Technical Considerations

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ProcessingService                         │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐          ┌──────────────────┐        │
│  │   LLMService     │          │   TTSService     │        │
│  │  (Protocol-based)│          │  (Protocol-based)│        │
│  └────────┬─────────┘          └────────┬─────────┘        │
│           │                              │                  │
│  ┌────────▼─────────┐          ┌────────▼─────────┐        │
│  │InstructorProvider│          │ OpenAITTSProvider│        │
│  └──────────────────┘          └──────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Dependencies

```toml
instructor = ">=1.0.0"  # New - for structured LLM output
# openai, arq already present
```

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Job queue | ARQ | Already in deps, native async |
| LLM library | Instructor (behind Protocol) | Structured output, but decoupled |
| TTS provider | OpenAI | Quality/cost balance |
| Provider abstraction | Protocol pattern | Enables switching without code changes |

---

## 7. Success Metrics

| Metric | Target |
|--------|--------|
| Processing success rate | >95% of jobs complete successfully |
| Average processing time | <5 minutes per book (15-20 chapters) |
| Audio quality | No user complaints about clarity |
| Provider switch time | <30 minutes to add new provider |

---

## 8. Open Questions

1. **Chapter count estimation** - How do we know how many chapters a book has? (Use metadata or ask LLM?)
2. **Summary length** - Target word count per chapter summary? (Affects audio duration)
3. **Voice selection** - Stick with one voice or offer options?
4. **Rate limiting** - How to handle OpenAI rate limits during batch processing?
