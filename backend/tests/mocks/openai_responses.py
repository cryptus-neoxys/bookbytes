"""Mock responses for OpenAI API calls.

These mocks allow testing without making real OpenAI API calls.
"""

from typing import Any

# =============================================================================
# Chapter Extraction Responses
# =============================================================================

CHAPTER_EXTRACTION_RESPONSE: dict[str, Any] = {
    "id": "chatcmpl-test123",
    "object": "chat.completion",
    "created": 1699000000,
    "model": "gpt-4o-mini",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": """[
                    {"number": 1, "title": "Introduction"},
                    {"number": 2, "title": "Getting Started"},
                    {"number": 3, "title": "Core Concepts"},
                    {"number": 4, "title": "Advanced Topics"},
                    {"number": 5, "title": "Best Practices"},
                    {"number": 6, "title": "Conclusion"}
                ]""",
            },
            "finish_reason": "stop",
        }
    ],
    "usage": {"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150},
}

CHAPTER_EXTRACTION_PARSED: list[dict[str, Any]] = [
    {"number": 1, "title": "Introduction"},
    {"number": 2, "title": "Getting Started"},
    {"number": 3, "title": "Core Concepts"},
    {"number": 4, "title": "Advanced Topics"},
    {"number": 5, "title": "Best Practices"},
    {"number": 6, "title": "Conclusion"},
]


# =============================================================================
# Summary Generation Responses
# =============================================================================

SUMMARY_GENERATION_RESPONSE: dict[str, Any] = {
    "id": "chatcmpl-test456",
    "object": "chat.completion",
    "created": 1699000001,
    "model": "gpt-4o-mini",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": (
                    "This chapter introduces the fundamental concepts of the book. "
                    "The author explains the motivation behind writing this guide and "
                    "outlines what readers can expect to learn. Key themes include "
                    "practical examples, best practices, and real-world applications. "
                    "The introduction sets the stage for deeper exploration in subsequent chapters."
                ),
            },
            "finish_reason": "stop",
        }
    ],
    "usage": {"prompt_tokens": 30, "completion_tokens": 80, "total_tokens": 110},
}

SAMPLE_SUMMARIES: dict[int, str] = {
    1: (
        "This chapter introduces the fundamental concepts of the book. "
        "The author explains the motivation and outlines what readers will learn."
    ),
    2: (
        "Getting Started covers the essential setup and configuration needed. "
        "Readers learn how to prepare their environment and install dependencies."
    ),
    3: (
        "Core Concepts dives deep into the main ideas that form the foundation. "
        "Key patterns and principles are explained with practical examples."
    ),
    4: (
        "Advanced Topics explores sophisticated techniques for experienced practitioners. "
        "Complex scenarios and edge cases are addressed with detailed solutions."
    ),
    5: (
        "Best Practices summarizes proven approaches and common pitfalls to avoid. "
        "The chapter provides actionable guidance for production environments."
    ),
    6: (
        "The Conclusion wraps up the key learnings and provides next steps. "
        "Resources for further learning and community engagement are shared."
    ),
}


# =============================================================================
# Error Responses
# =============================================================================

RATE_LIMIT_ERROR: dict[str, Any] = {
    "error": {
        "message": "Rate limit exceeded. Please retry after 20 seconds.",
        "type": "rate_limit_error",
        "code": "rate_limit_exceeded",
    }
}

INVALID_API_KEY_ERROR: dict[str, Any] = {
    "error": {
        "message": "Invalid API key provided.",
        "type": "invalid_request_error",
        "code": "invalid_api_key",
    }
}

CONTEXT_LENGTH_ERROR: dict[str, Any] = {
    "error": {
        "message": "This model's maximum context length is 16385 tokens.",
        "type": "invalid_request_error",
        "code": "context_length_exceeded",
    }
}
