"""Models package for BookBytes.

This module exports the Base class and all model classes.
Models are added incrementally as each phase is implemented.
"""

from bookbytes.models.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

__all__ = [
    "Base",
    "UUIDPrimaryKeyMixin",
    "TimestampMixin",
    "SoftDeleteMixin",
    # Models will be added here as phases are implemented:
    # Phase 3: Job
    # Phase 4: Book, BookIsbn, Chapter
    # Phase 6: User
]
