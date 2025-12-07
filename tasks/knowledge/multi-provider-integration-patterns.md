# Multi-Provider Data Integration Patterns

> **Status:** Research document for future multi-provider phase
> **Created:** 2024-12-07
> **Context:** BookBytes Audio Books Library - caching strategy for external book APIs

---

## Summary

When integrating multiple external data sources (OpenLibrary, Google Books, Goodreads), use:

1. **Canonical Data Model (CDM)** - unified internal representation
2. **Anti-Corruption Layer (ACL)** - adapter per provider

---

## Industry Patterns

### Canonical Data Model (CDM)

A standardized, application-agnostic data representation that acts as a "universal translator."

**Key Benefits:**

- `2n` mappings instead of `n²` (each provider to canonical, canonical to consumer)
- Data consistency across providers
- Easy to add new providers (just add adapter)
- Cache layer stays provider-agnostic

```
OpenLibrary API ──▶ ┌──────────────────┐ ◀── Google Books
                    │ Canonical Model  │
                    │ (BookSearchResult│
                    │  Edition, Work)  │
                    └────────┬─────────┘
                             ▼
                    ┌──────────────────┐
                    │   Redis Cache    │
                    │ (Canonical JSON) │
                    └──────────────────┘
```

### Anti-Corruption Layer (ACL)

From Domain-Driven Design (DDD) - translation layer protecting domain from external system quirks.

```python
class OpenLibraryAdapter:
    """Transforms OpenLibrary responses to canonical models."""

    def to_search_result(self, raw: dict) -> BookSearchResult:
        return BookSearchResult(
            title=raw["title"],
            authors=self._extract_authors(raw),
            source_provider="openlibrary",
            ...
        )
```

---

## Cache Key Strategy

### Current (Phase 1 - Single Provider)

Provider-agnostic keys:
| Key | Description |
|-----|-------------|
| `search:{hash}` | Search results |
| `isbn:{isbn}` | Book by ISBN |
| `work:{identifier}` | Work details |

### Future (Multi-Provider Phase)

Same keys, but cached data includes metadata:

```python
{
    "data": { ... },  # Canonical model
    "metadata": {
        "source_provider": "openlibrary",
        "fetched_at": "2024-12-07T...",
    }
}
```

---

## Trade-offs Analysis

| Trade-off           | Decision                                  | Rationale                                 |
| ------------------- | ----------------------------------------- | ----------------------------------------- |
| First provider wins | ✅ Accepted                               | Book metadata is similar across providers |
| Transform overhead  | ✅ Accepted                               | Happens once at fetch time                |
| Provider debugging  | Include `source_provider` in cached value |
| Schema evolution    | Version canonical models carefully        |

---

## Deferred to Multi-Provider Phase

- [ ] Provider-specific adapters (ACL)
- [ ] Provider rotation/selection strategy
- [ ] Provider-specific rate limiting
- [ ] Provider health checks and failover
- [ ] Provider-specific cache invalidation patterns

---

## References

- Eric Evans, Domain-Driven Design (Anti-Corruption Layer)
- Enterprise Integration Patterns (Canonical Data Model)
- Microsoft Azure Architecture: [Anti-Corruption Layer](https://learn.microsoft.com/en-us/azure/architecture/patterns/anti-corruption-layer)
