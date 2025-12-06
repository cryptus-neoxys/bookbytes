"""Repository pattern package for BookBytes.

This module exports base repository classes and concrete repositories.
"""

from bookbytes.repositories.audio_book import AudioBookRepository
from bookbytes.repositories.base import BaseRepository, SoftDeleteRepository
from bookbytes.repositories.book_provider import BookProviderRepository
from bookbytes.repositories.chapter import ChapterRepository
from bookbytes.repositories.edition import EditionRepository
from bookbytes.repositories.work import WorkRepository

__all__ = [
    # Base
    "BaseRepository",
    "SoftDeleteRepository",
    # Phase 3: Audio Books Library
    "WorkRepository",
    "EditionRepository",
    "BookProviderRepository",
    "AudioBookRepository",
    "ChapterRepository",
]
