# BookBytes AI Coding Instructions

## 🧠 Project Overview

BookBytes converts physical books (via ISBN) into chapter-wise audio summaries.

- **Core Logic**: `BookBytesApp` class in `app.py` orchestrates the entire pipeline.
- **Stack**: Python 3.8+, Flask, SQLite, OpenAI GPT-3.5, gTTS.
- **Data Flow**: ISBN -> Open Library API (Metadata) -> OpenAI (Chapter extraction & Summaries) -> gTTS (Audio) -> SQLite (Persistence).

## 🏗 Architecture & Patterns

- **Service Layer**: `BookBytesApp` encapsulates all business logic. Do not put logic in Flask routes or CLI commands; they should only call `BookBytesApp` methods.
- **Data Models**: Use `@dataclass` for entities (`Book`, `Chapter`) defined in `app.py`.
- **Database**: SQLite with raw SQL queries in `BookBytesApp`. Tables: `books`, `chapters`.
- **Logging**: MUST use `logger.py`. Import with `from logger import get_logger`.
  ```python
  logger = get_logger(__name__)
  logger.info("Message", extra={"context": "value"})
  ```
- **Path Handling**: Always use `pathlib.Path` instead of `os.path`.

## 🛠 Workflows & Commands

- **Run API**: `python app.py` (Starts Flask server on port 5000).
- **Run CLI**: `python cli.py [command]` (e.g., `process --isbn <isbn>`).
- **Docker**: `docker-compose up -d` (Runs app + persists data in `bookbytes-data` volume).
- **Testing**:
  - `test_app.py` is a standalone integration test script, NOT a pytest suite.
  - Run against a running server: `python test_app.py`.
  - Ensure `OPENAI_API_KEY` is set in `.env` before running.

## 📦 Dependencies & Integrations

- **External APIs**:
  - Open Library (Book metadata).
  - OpenAI API (Summarization, Chapter detection).
- **Audio**: `gTTS` (Google Text-to-Speech) saves files to `audio/` directory.
- **Environment**: Load vars using `python-dotenv` (handled in `cli.py` and `app.py`).

## 🚨 Critical Conventions

- **Error Handling**: Catch exceptions in `BookBytesApp` methods and return a result dict (`{'success': False, 'message': ...}`) rather than raising exceptions to the caller.
- **File Structure**:
  - `app.py`: Monolithic core (API + Logic + Models).
  - `cli.py`: CLI wrapper around `BookBytesApp`.
  - `knowledge/`: Documentation storage.
