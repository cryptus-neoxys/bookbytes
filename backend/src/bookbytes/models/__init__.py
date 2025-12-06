"""Models package for BookBytes.

This module exports the Base class and all model classes.
Models are added incrementally as each phase is implemented.
"""

from bookbytes.models.api_cache import APICache
from bookbytes.models.audio_book import AudioBook, AudioBookStatus
from bookbytes.models.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from bookbytes.models.book_provider import BookProvider, BookProviderType
from bookbytes.models.chapter import Chapter
from bookbytes.models.edition import Edition
from bookbytes.models.work import Work

__all__ = [
    # Base and Mixins
    "Base",
    "UUIDPrimaryKeyMixin",
    "TimestampMixin",
    "SoftDeleteMixin",
    # Phase 3: Audio Books Library
    "Work",
    "Edition",
    "BookProvider",
    "BookProviderType",
    "AudioBook",
    "AudioBookStatus",
    "Chapter",
    "APICache",
    # Future phases will add:
    # Phase 3.F: Job (background processing)
    # Phase 6: User (authentication)
]
