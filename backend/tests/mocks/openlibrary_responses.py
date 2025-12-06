"""Mock responses for Open Library API calls.

These mocks allow testing without making real Open Library API calls.
"""

from typing import Any

# =============================================================================
# Successful Book Lookups
# =============================================================================

# ISBN: 9780134685991 - Effective Python
EFFECTIVE_PYTHON_RESPONSE: dict[str, Any] = {
    "ISBN:9780134685991": {
        "url": "https://openlibrary.org/books/OL27258011M",
        "key": "/books/OL27258011M",
        "title": "Effective Python: 90 Specific Ways to Write Better Python",
        "authors": [{"url": "/authors/OL7373539A", "name": "Brett Slatkin"}],
        "publishers": [{"name": "Addison-Wesley Professional"}],
        "publish_date": "2019",
        "number_of_pages": 480,
        "cover": {
            "small": "https://covers.openlibrary.org/b/isbn/9780134685991-S.jpg",
            "medium": "https://covers.openlibrary.org/b/isbn/9780134685991-M.jpg",
            "large": "https://covers.openlibrary.org/b/isbn/9780134685991-L.jpg",
        },
        "identifiers": {
            "isbn_10": ["0134853989"],
            "isbn_13": ["9780134685991"],
            "openlibrary": ["OL27258011M"],
        },
        "subjects": [
            {"name": "Python (Computer program language)"},
            {"name": "Computer programming"},
        ],
    }
}

# ISBN: 9780596517984 - The Ruby Programming Language
RUBY_BOOK_RESPONSE: dict[str, Any] = {
    "ISBN:9780596517984": {
        "url": "https://openlibrary.org/books/OL23177938M",
        "key": "/books/OL23177938M",
        "title": "The Ruby Programming Language",
        "authors": [
            {"url": "/authors/OL2734036A", "name": "David Flanagan"},
            {"url": "/authors/OL2734037A", "name": "Yukihiro Matsumoto"},
        ],
        "publishers": [{"name": "O'Reilly Media"}],
        "publish_date": "2008",
        "number_of_pages": 446,
        "cover": {
            "small": "https://covers.openlibrary.org/b/isbn/9780596517984-S.jpg",
            "medium": "https://covers.openlibrary.org/b/isbn/9780596517984-M.jpg",
            "large": "https://covers.openlibrary.org/b/isbn/9780596517984-L.jpg",
        },
        "identifiers": {
            "isbn_10": ["0596516177"],
            "isbn_13": ["9780596517984"],
        },
    }
}


# =============================================================================
# Parsed Book Metadata
# =============================================================================

EFFECTIVE_PYTHON_METADATA: dict[str, Any] = {
    "title": "Effective Python: 90 Specific Ways to Write Better Python",
    "author": "Brett Slatkin",
    "publisher": "Addison-Wesley Professional",
    "publish_date": "2019",
    "pages": 480,
    "cover_url": "https://covers.openlibrary.org/b/isbn/9780134685991-L.jpg",
    "language": "en",
    "isbns": [
        {"isbn": "0134853989", "type": "isbn10"},
        {"isbn": "9780134685991", "type": "isbn13"},
    ],
}

RUBY_BOOK_METADATA: dict[str, Any] = {
    "title": "The Ruby Programming Language",
    "author": "David Flanagan, Yukihiro Matsumoto",
    "publisher": "O'Reilly Media",
    "publish_date": "2008",
    "pages": 446,
    "cover_url": "https://covers.openlibrary.org/b/isbn/9780596517984-L.jpg",
    "language": "en",
    "isbns": [
        {"isbn": "0596516177", "type": "isbn10"},
        {"isbn": "9780596517984", "type": "isbn13"},
    ],
}


# =============================================================================
# Not Found Responses
# =============================================================================

NOT_FOUND_RESPONSE: dict[str, Any] = {}

INVALID_ISBN_RESPONSE: dict[str, Any] = {}


# =============================================================================
# Error Responses
# =============================================================================

SERVICE_UNAVAILABLE_RESPONSE = {
    "error": "Service temporarily unavailable",
    "status": 503,
}

RATE_LIMITED_RESPONSE = {
    "error": "Rate limit exceeded",
    "status": 429,
}


# =============================================================================
# Helper Functions
# =============================================================================


def get_mock_response(isbn: str) -> dict[str, Any]:
    """Get a mock response for a given ISBN.

    Args:
        isbn: The ISBN to look up

    Returns:
        Mock API response or empty dict if not found
    """
    responses = {
        "9780134685991": EFFECTIVE_PYTHON_RESPONSE,
        "0134853989": EFFECTIVE_PYTHON_RESPONSE,
        "9780596517984": RUBY_BOOK_RESPONSE,
        "0596516177": RUBY_BOOK_RESPONSE,
    }
    return responses.get(isbn, {})


def get_mock_metadata(isbn: str) -> dict[str, Any] | None:
    """Get parsed metadata for a given ISBN.

    Args:
        isbn: The ISBN to look up

    Returns:
        Parsed metadata dict or None if not found
    """
    metadata = {
        "9780134685991": EFFECTIVE_PYTHON_METADATA,
        "0134853989": EFFECTIVE_PYTHON_METADATA,
        "9780596517984": RUBY_BOOK_METADATA,
        "0596516177": RUBY_BOOK_METADATA,
    }
    return metadata.get(isbn)
