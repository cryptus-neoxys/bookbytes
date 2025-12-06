# Tasks: Audio Books Library

**Design Reference:** [design-doc.md](./design-doc.md)  
**Parent:** [tasks-backend-productionisation.md](../tasks-backend-productionisation.md)  
**Branch:** `feat/productionise-and-saasify`

---

## Overview

This module implements the enhanced book search flow with:

- OpenLibrary API integration
- Two-tier caching (Redis L1 + PostgreSQL L2)
- Provider-agnostic data models
- Background job processing for audiobook generation

---

## Relevant Files

### Models

- `src/bookbytes/models/work.py` - Work model (provider-agnostic)
- `src/bookbytes/models/edition.py` - Edition model with ISBN
- `src/bookbytes/models/book_provider.py` - Provider mapping (polymorphic)
- `src/bookbytes/models/audio_book.py` - AudioBook model
- `src/bookbytes/models/chapter.py` - Chapter model
- `src/bookbytes/models/api_cache.py` - API cache for raw responses

### Repositories

- `src/bookbytes/repositories/work.py` - WorkRepository
- `src/bookbytes/repositories/edition.py` - EditionRepository
- `src/bookbytes/repositories/book_provider.py` - BookProviderRepository
- `src/bookbytes/repositories/audio_book.py` - AudioBookRepository
- `src/bookbytes/repositories/chapter.py` - ChapterRepository (update existing)

### Services

- `src/bookbytes/services/cache.py` - Two-tier cache service
- `src/bookbytes/services/openlibrary.py` - OpenLibrary API client
- `src/bookbytes/services/library.py` - Library management service

### API

- `src/bookbytes/api/v1/search.py` - Book search endpoints

### Workers

- `src/bookbytes/workers/tasks.py` - Background job tasks

---

## Tasks

### Phase 3.0: UUIDv7 Foundation

> **Prerequisite:** Before creating new models, set up UUIDv7 infrastructure.

- [ ] 3.0.1 Add `uuid6` library to `pyproject.toml`

  - RFC 9562 compliant backport for Python <3.14
  - Will switch to stdlib `uuid.uuid7()` when on Python 3.14

- [ ] 3.0.2 Install `pg_idkit` PostgreSQL extension

  - Supports UUIDv7 generation in database
  - Create migration to install extension: `CREATE EXTENSION IF NOT EXISTS pg_idkit`

- [ ] 3.0.3 Update `models/base.py` `UUIDPrimaryKeyMixin`
  - Change from `uuid.uuid4` to `uuid6.uuid7`
  - Keep PostgreSQL default as app-generated (no DB function)

```python
# Before
from uuid import uuid4
default=uuid4

# After
from uuid6 import uuid7
default=uuid7
```

- [ ] 3.0.4 Verify UUIDv7 sorting works in PostgreSQL
  - UUIDv7 is time-sortable when stored as native UUID type

---

### Phase 3.A: Data Models & Migrations

- [ ] 3.A.1 Create `models/work.py` with `Work` model

  - UUID primary key (v7), title, authors (JSON), first_publish_year, subjects (JSON), cover_url
  - Relationship to `editions` and `book_providers`
  - No provider-specific fields

- [ ] 3.A.2 Create `models/edition.py` with `Edition` model

  - work_id FK, isbn (unique, indexed), isbn_type, title, publisher, publish_year, language, pages
  - Relationship to `work`, `audio_book`, `book_providers`

- [ ] 3.A.3 Create `models/book_provider.py` with `BookProvider` model

  - entity_type ("work" | "edition"), entity_id, provider, external_key
  - Nullable FKs: work_id, edition_id (polymorphic pattern)
  - Unique constraint on (provider, external_key)
  - Index on (entity_type, entity_id)

- [ ] 3.A.4 Create `models/audio_book.py` with `AudioBook` model

  - edition_id FK, status enum, version
  - Uses SoftDeleteMixin

- [ ] 3.A.5 Update `models/chapter.py` to reference AudioBook

  - audio_book_id FK, chapter_number, title, summary, audio paths, word_count, duration

- [ ] 3.A.6 Create `models/api_cache.py` with `APICache` model

  - cache_key (unique, indexed), source, response_json, total_results, expires_at (indexed), original_ttl, hit_count

- [ ] 3.A.7 Update `models/__init__.py` with new model exports

- [ ] 3.A.8 Generate migration: `alembic revision --autogenerate -m "add_audio_books_library_models"`

- [ ] 3.A.9 Run migration: `alembic upgrade head`

---

### Phase 3.A-R: Repositories

> **Note:** No APICacheRepository - CacheService handles all cache operations directly.

- [ ] 3.A-R.1 Create `repositories/work.py` with `WorkRepository`

  - `get_by_title_author()` - find by title and author combination
  - `get_with_editions()` - eager load editions

- [ ] 3.A-R.2 Create `repositories/edition.py` with `EditionRepository`

  - `get_by_isbn()` - find by normalized ISBN
  - `get_by_work_id()` - all editions for a work
  - `get_latest_by_work()` - latest by publish_year

- [ ] 3.A-R.3 Create `repositories/book_provider.py` with `BookProviderRepository`

  - `get_by_provider_key()` - find by (provider, external_key)
  - `get_for_entity()` - all providers for a work/edition
  - `create_mapping()` - link entity to provider

- [ ] 3.A-R.4 Create `repositories/audio_book.py` with `AudioBookRepository`

  - Extends `SoftDeleteRepository` for soft delete support
  - `get_by_edition()` - find audiobook for edition
  - `get_by_status()` - filter by processing status

- [ ] 3.A-R.5 Update `repositories/chapter.py` with `ChapterRepository`

  - `get_by_audio_book()` - all chapters for audiobook
  - `get_by_number()` - specific chapter

- [ ] 3.A-R.6 Update `repositories/__init__.py` with new exports

---

### Phase 3.B: Cache Service

- [ ] 3.B.1 Create `services/cache.py` with `CacheService` class

  - Two-tier: Redis (L1) + PostgreSQL (L2)
  - Inject Redis client and DB session
  - Directly manages APICache table (no repository needed)

- [ ] 3.B.2 Implement `get()` method

  - Check Redis first, then PostgreSQL on miss
  - Return (data, needs_revalidation) tuple
  - Track remaining TTL for stale-while-revalidate

- [ ] 3.B.3 Implement `set()` method with TTL jitter

  - Store in both Redis and PostgreSQL
  - Add ±10% random jitter to prevent stampede

- [ ] 3.B.4 Implement `invalidate()` and `invalidate_pattern()`

  - Delete from both tiers
  - Pattern support for search cache invalidation

- [ ] 3.B.5 Implement stale-while-revalidate logic

  - Return stale data at <20% TTL remaining
  - Trigger background refresh

- [ ] 3.B.6 Add async storage method for fire-and-forget caching

  - Used when returning OpenLibrary response immediately

- [ ] 3.B.7 Add cache key generation helper
  - Normalize params (lowercase, trim, sort)
  - SHA256 hash for storage efficiency

---

### Phase 3.C: OpenLibrary Service

- [ ] 3.C.1 Create `services/openlibrary.py` with `OpenLibraryService` class

  - BASE_URL, PAGE_SIZE=100
  - Use httpx async client

- [ ] 3.C.2 Add User-Agent header

  - Include app name and contact for API compliance

- [ ] 3.C.3 Implement `search_books()` method

  - Accept title, author, publisher, language
  - Check cache first (via CacheService)
  - Query API on miss, cache result async

- [ ] 3.C.4 Implement `get_work_details()` method

  - Fetch work by OpenLibrary key
  - Cache with 7-day TTL

- [ ] 3.C.5 Implement `get_all_isbns_for_work()` method

  - Collect ISBNs from all editions

- [ ] 3.C.6 Map API responses to provider-agnostic schemas
  - Create DTOs for search results, work details

---

### Phase 3.D: Library Service

- [ ] 3.D.1 Create `services/library.py` with `LibraryService` class

  - Inject: WorkRepository, EditionRepository, BookProviderRepository

- [ ] 3.D.2 Implement `find_work_by_provider()`

  - Query BookProvider by (provider, external_key)
  - Return associated Work

- [ ] 3.D.3 Implement `get_or_create_work()`

  - Check if work exists via provider lookup
  - Create new Work if not found
  - Link to provider

- [ ] 3.D.4 Implement `link_to_provider()`

  - Create BookProvider mapping for Work or Edition

- [ ] 3.D.5 Implement `find_by_isbn()`

  - Query Edition by normalized ISBN

- [ ] 3.D.6 Implement `find_latest_edition()`

  - Order by publish_year descending
  - Filter by language

- [ ] 3.D.7 Implement `store_editions()`
  - Bulk insert editions for a work
  - Create BookProvider mappings

---

### Phase 3.E: API Endpoints

- [ ] 3.E.1 Create `api/v1/search.py` with router

- [ ] 3.E.2 Create `POST /books/search` endpoint

  - Accept BookSearchRequest (title, author?, publisher?, language?)
  - Return paginated results with page, page_size params

- [ ] 3.E.3 Create `GET /books/works/{work_id}` endpoint

  - Return work details with all editions

- [ ] 3.E.4 Create `GET /books/isbn/{isbn}` endpoint

  - Check library first, query API if not found
  - Store in library on fetch

- [ ] 3.E.5 Create `POST /books/process` endpoint

  - Accept edition_id OR isbn
  - Create Job, enqueue background task
  - Return job_id

- [ ] 3.E.6 Create `POST /books/{audio_book_id}/refresh` endpoint

  - Regenerate audiobook for new edition
  - Invalidate related caches

- [ ] 3.E.7 Create schemas in `schemas/search.py`

  - BookSearchRequest, BookSearchResponse, WorkResponse, EditionResponse

- [ ] 3.E.8 Include search router in v1 router

---

### Phase 3.F: Background Jobs

- [ ] 3.F.1 Create/update Job model for audiobook processing

  - Add audio_book_id FK

- [ ] 3.F.2 Update `workers/tasks.py` with audiobook processing

  - Fetch work details
  - Collect all ISBNs
  - Generate audio (existing pipeline)

- [ ] 3.F.3 Implement cache invalidation on job completion
  - Invalidate search caches containing this work

---

### Phase 3.G: Testing

- [ ] 3.G.1 Create `tests/unit/test_cache_service.py`

  - Test two-tier cache flow
  - Test TTL jitter
  - Test stale-while-revalidate

- [ ] 3.G.2 Create `tests/unit/test_openlibrary_service.py`

  - Mock HTTP responses
  - Test search, work details, ISBN collection

- [ ] 3.G.3 Create `tests/unit/test_library_service.py`

  - Test provider lookups
  - Test work/edition storage

- [ ] 3.G.4 Create `tests/unit/test_repositories.py`

  - Test Work, Edition, BookProvider, AudioBook repositories

- [ ] 3.G.5 Create `tests/integration/test_search_api.py`

  - Test full search flow with mocked OpenLibrary
  - Test caching behavior
  - Test pagination

- [ ] 3.G.6 Add OpenLibrary mock responses to `tests/mocks/`

---

## Notes

- **UUIDv7:** Using `uuid6` library (RFC 9562 compliant) until Python 3.14
- **PostgreSQL:** `pg_idkit` extension for UUIDv7 generation capability
- All models use `UUIDPrimaryKeyMixin` (now v7) and `TimestampMixin`
- AudioBook uses `SoftDeleteMixin` for soft deletion
- AudioBookRepository extends `SoftDeleteRepository`
- BookProvider is a sparse/polymorphic table (see design doc for query patterns)
- **No APICacheRepository:** CacheService manages APICache directly
- Redis memory policy: `allkeys-lru` with 256mb limit
- OpenLibrary requires User-Agent header to avoid rate limiting
