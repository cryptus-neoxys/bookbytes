#!/usr/bin/env python3
"""
BookBytes - Audio Book Summarizer
Converts non-fiction books into chapter-wise audio summaries
"""

import os
import sys
import json
import sqlite3
import requests
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

# Third-party imports
from flask import Flask, request, jsonify, send_file
from gtts import gTTS
import openai
from openai import OpenAI

# Import custom logger
from logger import get_logger, setup_logging

# Configure logging
setup_logging(log_level=os.getenv('LOG_LEVEL', 'INFO'))
logger = get_logger(__name__)

@dataclass
class Book:
    isbn: str
    title: str
    author: str
    pages: Optional[int] = None
    publish_date: Optional[str] = None
    
@dataclass
class Chapter:
    book_isbn: str
    chapter_number: int
    title: str
    summary: str
    audio_file_path: Optional[str] = None
    word_count: Optional[int] = None

class BookBytesApp:
    def __init__(self, db_path: str = "bookbytes.db", audio_dir: str = "audio"):
        self.db_path = db_path
        self.audio_dir = Path(audio_dir)
        self.audio_dir.mkdir(exist_ok=True)
        
        # Initialize OpenAI client
        self.openai_client = None
        if os.getenv('OPENAI_API_KEY'):
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        logger.info(f"Initializing database at: {self.db_path}")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            logger.debug("Creating books table if not exists")
            # Books table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    isbn TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    pages INTEGER,
                    publish_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            logger.debug("Creating chapters table if not exists")
            # Chapters table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chapters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_isbn TEXT NOT NULL,
                    chapter_number INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    audio_file_path TEXT,
                    word_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (book_isbn) REFERENCES books (isbn),
                    UNIQUE(book_isbn, chapter_number)
                )
            """)
            
            conn.commit()
            logger.info("Database schema initialized successfully")
            
            # Check if tables were created successfully
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            logger.debug(f"Database tables: {[table[0] for table in tables]}")
            
            conn.close()
        except sqlite3.Error as e:
            logger.exception(f"Database initialization error: {e}")
            raise
    
    def fetch_book_details(self, isbn: str) -> Optional[Book]:
        """Fetch book details from Open Library API"""
        try:
            # Clean ISBN (remove hyphens, spaces)
            clean_isbn = isbn.replace('-', '').replace(' ', '')
            logger.info(f"Fetching book details for ISBN: {clean_isbn}")
            
            # Try Open Library API
            url = f"https://openlibrary.org/isbn/{clean_isbn}.json"
            logger.debug(f"Making API request to: {url}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"Received data from Open Library API: {json.dumps(data, indent=2)[:500]}...")
                
                # Extract book details
                title = data.get('title', 'Unknown Title')
                logger.info(f"Found book title: {title}")
                
                # Get authors
                authors = []
                if 'authors' in data:
                    logger.debug(f"Found {len(data['authors'])} authors, fetching details")
                    for author_ref in data['authors']:
                        author_key = author_ref['key']
                        author_url = f"https://openlibrary.org{author_key}.json"
                        logger.debug(f"Fetching author details from: {author_url}")
                        
                        author_response = requests.get(author_url, timeout=5)
                        if author_response.status_code == 200:
                            author_data = author_response.json()
                            author_name = author_data.get('name', 'Unknown Author')
                            authors.append(author_name)
                            logger.debug(f"Found author: {author_name}")
                        else:
                            logger.warning(f"Failed to fetch author details from {author_url}, status: {author_response.status_code}")
                
                author = ', '.join(authors) if authors else 'Unknown Author'
                pages = data.get('number_of_pages')
                publish_date = data.get('publish_date')
                
                book = Book(
                    isbn=clean_isbn,
                    title=title,
                    author=author,
                    pages=pages,
                    publish_date=publish_date
                )
                
                logger.info(f"Successfully retrieved book: {title} by {author}, {pages} pages, published {publish_date}")
                return book
            else:
                logger.warning(f"Book not found for ISBN: {isbn}, status code: {response.status_code}")
                if response.status_code != 404:
                    logger.debug(f"Response content: {response.text[:500]}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout while fetching book details for ISBN {isbn}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error while fetching book details for ISBN {isbn}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response for ISBN {isbn}: {e}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error fetching book details for ISBN {isbn}: {e}")
            return None
    
    def get_chapter_list(self, book: Book) -> List[Chapter]:
        """Get chapter list using OpenAI"""
        try:
            logger.info(f"Getting chapter list for book: '{book.title}' by {book.author}")
            
            if not os.getenv("OPENAI_API_KEY"):
                logger.error("OPENAI_API_KEY environment variable not set")
                return []
                
            # Prompt for chapter list
            prompt = f"""
            List the chapters for the book "{book.title}" by "{book.author}".
            """

            
            logger.debug(f"Sending prompt to OpenAI: {prompt[:100]}...")
            
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4.1-nano",
                  messages=[
                      {"role": "system", "content": [{"text": "You are a bookworm with exact detailed knowledge of popular non-fiction, non-educational books.\n\nList the chapters for the book \"<book_title>\" by \"<author_name>\" with each chapter clearly enumerated. Return only the chapter title, one per line, without chapter numbers or additional text. Return a response that strictly adheres to the described schema. \n<reposnse_schema>\n[CHAPTER_TITLE]\n</reposnse_schema>\n\n<sample_query>List the chapters for the book Atomic Habits by James Clear</sample_query>\n\n<sample_response>\nDeny Trauma\nAll Problems Are Interpersonal Relationship Problems\nDiscard Other People's Tasks\nWhere the Center of the World Is\nLive in Earnest in the Here and Now\nThe Courage to Be Happy\n</sample_response>","type": "text"}],},
                      {"role": "user", "content": prompt}
                  ],
                  response_format={
                    "type": "text"
                  },
                  temperature=0.2,
                  max_completion_tokens=400,
                  top_p=1,
                  frequency_penalty=0,
                  presence_penalty=0
                )
                logger.debug(f"Received response from OpenAI with {len(response.choices)} choices")
            except openai.APIConnectionError:
                logger.error("Failed to connect to OpenAI API")
                return []
            except openai.APIError as api_err:
                logger.error(f"OpenAI API error: {api_err}")
                return []
            except openai.RateLimitError:
                logger.error("OpenAI rate limit exceeded")
                return []

            # Parse the response
            content = response.choices[0].message.content.strip()
            logger.debug(f"Raw response content: {content[:200]}...")
            
            # Parse chapter titles
            chapters_data = [line.strip() for line in content.split('\n') if line.strip()]
            logger.info(f"Found {len(chapters_data)} chapters for {book.title}")
            
            # Create Chapter objects
            chapters: List[Chapter] = []
            for index, chapter in enumerate(chapters_data):
                chapter_num = index
                chapter_title = chapter
                logger.debug(f"Processing chapter {chapter_num}: {chapter_title}")

                chapters.append(Chapter(
                    book_isbn=book.isbn,
                    chapter_number=chapter_num,
                    title=chapter_title,
                    summary="",  # Will be filled later
                    audio_file_path="",  # Will be filled later
                ))

            logger.info(f"Successfully created {len(chapters_data)} chapter objects for '{book.title}'")
            return chapters
            
        except Exception as e:
            logger.exception(f"Unexpected error getting chapter list for book {book.title}: {e}")
            return []
    
    def get_chapter_summary(self, book: Book, chapter: Chapter) -> str:
        """Get chapter summary using OpenAI"""
        try:
            logger.info(f"Generating summary for Chapter {chapter.chapter_number}: {chapter.title} of '{book.title}'")
            
            if not os.getenv("OPENAI_API_KEY"):
                logger.error("OPENAI_API_KEY environment variable not set")
                return ""
            
            # Prompt for chapter summary
            prompt = f"""
            {chapter.title}, {book.title} by {book.author}
            """
            
            logger.debug(f"Sending summary prompt to OpenAI for chapter {chapter.chapter_number}: {prompt[:100]}...")
            
            try:
                response = self.openai_client.chat.completions.create(
                  model="gpt-4.1-nano",
                  messages=[
                      {"role": "system","content": [{"text": "You are a bookworm with exact, detailed knowledge of popular non-fiction, non-educational books.\n\nProvide a detailed and insightful summary strictly in about 450-500 words of [CHAPTER_TITLE], [BOOK_TITLE] by [AUTHOR]. Focus on core insights and key points, and stick to the precise chapter content to create an effective summary. Ensure that the summarisation of the chapter summary strictly falls between 450-500 words. If you don't know the exact content, provide a reasonable summary based on the book's topic and the chapter title. Return only the response that strictly adheres to the described schema. Do not add commentary, additional tags, or anything except the summary. !IMP & Non-Negotiable: 1. Proper 450-500 words summary, 2. output is just the summary as requested, 3. plain summary paragraphs in text output, nothing else.\n\n<input_format>\n[CHAPTER_TITLE], [BOOK_TITLE] by [AUTHOR]\n</input_format>\n\n<output_schema>\n[SUMMARY]\n</output_schema>\n\n<sample_input>\nAll Problems Are Interpersonal Relationship Problems, The Courage to Be Disliked by Ichiro Kishimi and Fumitake Koga\n</sample_input>\n\n<sample_output>\nChapter 2 of 'The Courage to Be Disliked' by Ichiro Kishimi and Fumitake Koga, titled 'All Problems Are Interpersonal Relationship Problems', delves into the foundational Adlerian psychological concept that every personal issue stems from complications in relationships with others ...\n</sample_output>","type": "text"}]},
                      {"role": "user", "content": prompt}
                  ],
                  response_format={
                    "type": "text"
                  },
                  temperature=0.8,
                  max_completion_tokens=1000,
                  top_p=1,
                  frequency_penalty=0,
                  presence_penalty=0
                )
                logger.debug(f"Received summary response from OpenAI with {len(response.choices)} choices")
            except openai.APIConnectionError:
                logger.error("Failed to connect to OpenAI API while generating summary")
                return ""
            except openai.APIError as api_err:
                logger.error(f"OpenAI API error while generating summary: {api_err}")
                return ""
            except openai.RateLimitError:
                logger.error("OpenAI rate limit exceeded while generating summary")
                return ""

            # Get the summary
            summary = response.choices[0].message.content.strip()
            
            # Log summary statistics
            word_count = len(summary.split())
            logger.info(f"Generated summary for Chapter {chapter.chapter_number} with {word_count} words")
            logger.debug(f"Summary preview: {summary[:150]}...")

            if summary.upper() == "UNKNOWN":
                logger.warning(f"LLM doesn't have knowledge of chapter: {chapter.title}")
                return ""
            if word_count < 100:
                logger.warning(f"Summary for Chapter {chapter.chapter_number} is unusually short ({word_count} words)")
            
            return summary
            
        except Exception as e:
            logger.exception(f"Unexpected error getting summary for chapter {chapter.chapter_number} of book {book.title}: {e}")
            return ""
    
    def text_to_speech(self, text: str, output_path: str, lang: str = 'en') -> bool:
        """Convert text to speech using gTTS"""
        try:
            logger.info(f"Converting text to speech, output path: {output_path}")
            
            # Log text statistics
            word_count = len(text.split())
            char_count = len(text)
            logger.debug(f"Text statistics: {word_count} words, {char_count} characters")
            
            if word_count == 0:
                logger.error("Cannot convert empty text to speech")
                return False
                
            # Check if output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                logger.debug(f"Creating output directory: {output_dir}")
                os.makedirs(output_dir, exist_ok=True)
            
            # Start timer for performance tracking
            start_time = datetime.now()
            logger.debug(f"Starting text-to-speech conversion at {start_time.isoformat()}")

            # Create gTTS object and save audio
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(output_path)
            
            # Calculate processing time
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Get file size
            file_size = os.path.getsize(output_path) / (1024 * 1024)  # Size in MB
            
            logger.info(f"Audio saved to: {output_path} ({file_size:.2f} MB)")
            logger.debug(f"Text-to-speech conversion completed in {duration:.2f} seconds")
            logger.debug(f"Conversion rate: {word_count/duration:.2f} words per second")
            
            return True
            
        except FileNotFoundError as e:
            logger.error(f"File path error during text-to-speech conversion: {e}")
            return False
        except PermissionError as e:
            logger.error(f"Permission error saving audio file: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error converting text to speech: {e}")
            return False
    
    def save_book(self, book: Book) -> bool:
        """Save book to database"""
        logger.info(f"Saving book to database: {book.title} (ISBN: {book.isbn})")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if book already exists
            cursor.execute("SELECT isbn FROM books WHERE isbn = ?", (book.isbn,))
            existing_book = cursor.fetchone()
            
            if existing_book:
                logger.debug(f"Book with ISBN {book.isbn} already exists, updating record")
                operation = "updated"
            else:
                logger.debug(f"Book with ISBN {book.isbn} is new, creating record")
                operation = "created"
            
            # Insert or replace book record
            cursor.execute("""
                INSERT OR REPLACE INTO books (isbn, title, author, pages, publish_date)
                VALUES (?, ?, ?, ?, ?)
            """, (book.isbn, book.title, book.author, book.pages, book.publish_date))
            
            # Get number of affected rows
            affected_rows = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.info(f"Book {operation} successfully: {book.title} (ISBN: {book.isbn})")
            logger.debug(f"Database operation affected {affected_rows} rows")
            
            return True
            
        except sqlite3.IntegrityError as e:
            logger.error(f"Database integrity error while saving book {book.isbn}: {e}")
            return False
        except sqlite3.OperationalError as e:
            logger.error(f"Database operational error while saving book {book.isbn}: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error saving book {book.isbn}: {e}")
            return False
    
    def save_chapter(self, chapter: Chapter) -> bool:
        """Save chapter to database"""
        logger.info(f"Saving chapter to database: Chapter {chapter.chapter_number}: {chapter.title} (ISBN: {chapter.book_isbn})")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if chapter already exists
            cursor.execute(
                "SELECT id FROM chapters WHERE book_isbn = ? AND chapter_number = ?", 
                (chapter.book_isbn, chapter.chapter_number)
            )
            existing_chapter = cursor.fetchone()
            
            if existing_chapter:
                logger.debug(f"Chapter {chapter.chapter_number} for book {chapter.book_isbn} already exists, updating record")
                operation = "updated"
            else:
                logger.debug(f"Chapter {chapter.chapter_number} for book {chapter.book_isbn} is new, creating record")
                operation = "created"
            
            # Calculate word count if not provided
            word_count = chapter.word_count
            if not word_count and chapter.summary:
                word_count = len(chapter.summary.split())
                logger.debug(f"Calculated word count for chapter: {word_count} words")
            
            # Insert or replace chapter record
            cursor.execute("""
                INSERT OR REPLACE INTO chapters 
                (book_isbn, chapter_number, title, summary, audio_file_path, word_count)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (chapter.book_isbn, chapter.chapter_number, chapter.title, 
                   chapter.summary, chapter.audio_file_path, word_count))
            
            # Get number of affected rows and last row ID
            affected_rows = cursor.rowcount
            last_row_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            logger.info(f"Chapter {operation} successfully: Chapter {chapter.chapter_number} (ID: {last_row_id})")
            logger.debug(f"Database operation affected {affected_rows} rows")
            
            # Log audio file information if available
            if chapter.audio_file_path and os.path.exists(chapter.audio_file_path):
                file_size = os.path.getsize(chapter.audio_file_path) / (1024 * 1024)  # Size in MB
                logger.debug(f"Associated audio file: {chapter.audio_file_path} ({file_size:.2f} MB)")
            
            return True
            
        except sqlite3.IntegrityError as e:
            logger.error(f"Database integrity error while saving chapter {chapter.chapter_number}: {e}")
            return False
        except sqlite3.OperationalError as e:
            logger.error(f"Database operational error while saving chapter {chapter.chapter_number}: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error saving chapter {chapter.chapter_number}: {e}")
            return False
    
    def process_book(self, isbn: str) -> Dict:
        """Main processing pipeline for a book"""
        result = {
            'success': False,
            'message': '',
            'book': None,
            'chapters_processed': 0
        }
        
        # Step 1: Fetch book details
        logger.info(f"Processing book with ISBN: {isbn}")
        book = self.fetch_book_details(isbn)
        
        if not book:
            result['message'] = f"Could not fetch book details for ISBN: {isbn}"
            return result
        
        result['book'] = {
            'isbn': book.isbn,
            'title': book.title,
            'author': book.author
        }
        
        # Save book to database
        if not self.save_book(book):
            result['message'] = "Failed to save book to database"
            return result
        
        # Step 2: Get chapters from LLM
        chapters = self.get_chapter_list(book)
        
        if not chapters:
            result['message'] = f"Could not retrieve chapters for book: {book.title}"
            return result
        
        # Step 3: Process each chapter
        processed_chapters = 0
        
        for i, chapter in enumerate(chapters, 1):
            chapter_title = chapter.title
            logger.info(f"Processing chapter {i}: {chapter_title}")
            
            # Generate summary
            summary = self.get_chapter_summary(book, chapter)
            
            if not summary:
                logger.warning(f"Skipping chapter {i} - no summary generated")
                continue
            
            # Create audio file
            audio_filename = f"{book.isbn}_chapter_{i:02d}.mp3"
            audio_path = self.audio_dir / audio_filename
            
            if self.text_to_speech(summary, str(audio_path)):
                # Save chapter to database
                chapter = Chapter(
                    book_isbn=book.isbn,
                    chapter_number=i,
                    title=chapter.title,
                    summary=summary,
                    audio_file_path=str(audio_path),
                    word_count=len(summary.split())
                )
                
                if self.save_chapter(chapter):
                    processed_chapters += 1
                    logger.info(f"Successfully processed chapter {i}")
                else:
                    logger.error(f"Failed to save chapter {i} to database")
            else:
                logger.error(f"Failed to generate audio for chapter {i}")
        
        result['success'] = processed_chapters > 0
        result['chapters_processed'] = processed_chapters
        result['message'] = f"Successfully processed {processed_chapters} out of {len(chapters)} chapters"
        
        return result
    
    def get_book(self, isbn: str) -> Optional[Dict]:
        """Get a single book from database"""
        logger.info(f"Retrieving book from database: {isbn}")
        start_time = datetime.now()
        
        # Validate and clean ISBN
        if not isbn or not isinstance(isbn, str):
            logger.warning(f"Invalid ISBN provided: {isbn}")
            return None
            
        clean_isbn = isbn.strip().replace('-', '').replace(' ', '')
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            logger.debug(f"Executing SQL query to retrieve book {clean_isbn}")
            cursor.execute("""
                SELECT b.isbn, b.title, b.author, b.pages, b.publish_date,
                       COUNT(c.id) as chapter_count
                FROM books b
                LEFT JOIN chapters c ON b.isbn = c.book_isbn
                WHERE b.isbn = ?
                GROUP BY b.isbn
            """, (clean_isbn,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                book = {
                    'isbn': row[0],
                    'title': row[1],
                    'author': row[2],
                    'pages': row[3],
                    'publish_date': row[4],
                    'chapter_count': row[5]
                }
                
                # Calculate processing time
                processing_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"Retrieved book {clean_isbn} in {processing_time:.2f} seconds")
                return book
            else:
                logger.warning(f"Book with ISBN {clean_isbn} not found")
                return None
            
        except sqlite3.Error as e:
            logger.error(f"SQLite error getting book {clean_isbn}: {e}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error getting book {clean_isbn}: {e}")
            return None

    def get_all_books(self) -> List[Dict]:
        """Get all books from database"""
        logger.info("Retrieving all books from database")
        start_time = datetime.now()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            logger.debug(f"Executing SQL query to retrieve books with chapter counts")
            cursor.execute("""
                SELECT b.isbn, b.title, b.author, b.pages, b.publish_date,
                       COUNT(c.id) as chapter_count
                FROM books b
                LEFT JOIN chapters c ON b.isbn = c.book_isbn
                GROUP BY b.isbn
                ORDER BY b.created_at DESC
            """)
            
            books = []
            for row in cursor.fetchall():
                books.append({
                    'isbn': row[0],
                    'title': row[1],
                    'author': row[2],
                    'pages': row[3],
                    'publish_date': row[4],
                    'chapter_count': row[5]
                })
            
            book_count = len(books)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Retrieved {book_count} books from database in {processing_time:.2f} seconds")
            
            if book_count > 0:
                logger.debug(f"Book ISBNs: {[book.get('isbn') for book in books]}")
            else:
                logger.debug("No books found in database")
            
            conn.close()
            return books
            
        except sqlite3.Error as e:
            logger.error(f"SQLite error getting books: {e}")
            return []
        except Exception as e:
            logger.exception(f"Unexpected error getting books: {e}")
            return []
    
    def get_book_chapters(self, isbn: str) -> List[Dict]:
        """Get all chapters for a specific book"""
        logger.info(f"Retrieving chapters for book ISBN: {isbn}")
        start_time = datetime.now()
        
        # Validate and clean ISBN
        if not isbn or not isinstance(isbn, str):
            logger.warning(f"Invalid ISBN provided: {isbn}")
            return []
            
        clean_isbn = isbn.strip().replace('-', '').replace(' ', '')
        if clean_isbn != isbn:
            logger.debug(f"Cleaned ISBN from '{isbn}' to '{clean_isbn}'")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # First check if the book exists
            cursor.execute("SELECT COUNT(*) FROM books WHERE isbn = ?", (clean_isbn,))
            book_exists = cursor.fetchone()[0] > 0
            
            if not book_exists:
                logger.warning(f"Book with ISBN {clean_isbn} not found in database")
                conn.close()
                return []
            
            logger.debug(f"Executing SQL query to retrieve chapters for ISBN {clean_isbn}")
            cursor.execute("""
                SELECT chapter_number, title, summary, audio_file_path, word_count,
                       CASE WHEN audio_file_path IS NOT NULL AND audio_file_path != '' 
                            THEN 1 ELSE 0 END as has_audio
                FROM chapters
                WHERE book_isbn = ? 
                ORDER BY chapter_number
            """, (clean_isbn,))
            
            chapters = []
            for row in cursor.fetchall():
                chapters.append({
                    'chapter_number': row[0],
                    'title': row[1],
                    'summary': row[2],
                    'audio_file_path': row[3],
                    'word_count': row[4],
                    'has_audio': row[5]
                })
            
            chapter_count = len(chapters)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            if chapter_count > 0:
                logger.info(f"Retrieved {chapter_count} chapters for book ISBN: {clean_isbn} in {processing_time:.2f} seconds")
                logger.debug(f"Chapter numbers: {[chapter.get('chapter_number') for chapter in chapters]}")
                
                # Log audio status
                chapters_with_audio = sum(1 for chapter in chapters if chapter.get('has_audio'))
                logger.debug(f"Chapters with audio: {chapters_with_audio}/{chapter_count}")
            else:
                logger.warning(f"No chapters found for book ISBN: {clean_isbn}")
            
            conn.close()
            return chapters
            
        except sqlite3.Error as e:
            logger.error(f"SQLite error getting chapters for book {clean_isbn}: {e}")
            return []
        except Exception as e:
            logger.exception(f"Unexpected error getting chapters for book {clean_isbn}: {e}")
            return []

# Flask API
app = Flask(__name__)
bookbytes = BookBytesApp()

@app.route('/api/process', methods=['POST'])
def process_book_api():
    """API endpoint to process a book by ISBN"""
    request_id = f"req_{datetime.now().strftime('%Y%m%d%H%M%S')}_{id(request)}"
    logger.info(f"[{request_id}] Received request to process book")
    
    try:
        data = request.get_json()
        logger.debug(f"[{request_id}] Request data: {data}")
        
        if not data or 'isbn' not in data:
            logger.warning(f"[{request_id}] Missing ISBN in request")
            return jsonify({'error': 'ISBN is required', 'request_id': request_id}), 400
        
        isbn = data['isbn'].strip()
        logger.info(f"[{request_id}] Processing book with ISBN: {isbn}")
        
        if not isbn:
            logger.warning(f"[{request_id}] Empty ISBN after stripping")
            return jsonify({'error': 'Invalid ISBN', 'request_id': request_id}), 400
        
        # Start timer for performance tracking
        start_time = datetime.now()
        
        # Process the book
        result = bookbytes.process_book(isbn)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"[{request_id}] Book processing completed in {processing_time:.2f} seconds")
        
        # Add request ID and processing time to response
        result['request_id'] = request_id
        result['processing_time'] = f"{processing_time:.2f}s"
        
        if result['success']:
            logger.info(f"[{request_id}] Successfully processed book: {result.get('book', {}).get('title', 'Unknown')}")
            return jsonify(result), 200
        else:
            logger.warning(f"[{request_id}] Failed to process book: {result.get('message', 'Unknown error')}")
            return jsonify(result), 400
            
    except json.JSONDecodeError:
        logger.error(f"[{request_id}] Invalid JSON in request body")
        return jsonify({'error': 'Invalid JSON in request body', 'request_id': request_id}), 400
    except Exception as e:
        logger.exception(f"[{request_id}] Unexpected error processing book request: {e}")
        return jsonify({'error': 'Internal server error', 'message': str(e), 'request_id': request_id}), 500

@app.route('/api/books', methods=['GET'])
def get_books_api():
    """API endpoint to get all processed books"""
    request_id = f"req_{datetime.now().strftime('%Y%m%d%H%M%S')}_{id(request)}"
    logger.info(f"[{request_id}] Received request to list all books")
    
    try:
        # Start timer for performance tracking
        start_time = datetime.now()
        
        books = bookbytes.get_all_books()
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"[{request_id}] Retrieved {len(books)} books in {processing_time:.2f} seconds")
        logger.debug(f"[{request_id}] Book ISBNs: {[book.get('isbn') for book in books]}")
        
        response = {
            'books': books,
            'count': len(books),
            'request_id': request_id,
            'processing_time': f"{processing_time:.2f}s"
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.exception(f"[{request_id}] Error retrieving books: {e}")
        return jsonify({
            'error': 'Internal server error', 
            'message': str(e),
            'request_id': request_id
        }), 500

@app.route('/api/books/<isbn>', methods=['GET'])
def get_book_api(isbn):
    """API endpoint to get a specific book"""
    request_id = f"req_{datetime.now().strftime('%Y%m%d%H%M%S')}_{id(request)}"
    logger.info(f"[{request_id}] Received request to get book details for ISBN: {isbn}")
    
    try:
        # Start timer for performance tracking
        start_time = datetime.now()
        
        book = bookbytes.get_book(isbn)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        if book:
            logger.info(f"[{request_id}] Retrieved book details for {isbn} in {processing_time:.2f} seconds")
            
            response = {
                'book': book,
                'request_id': request_id,
                'processing_time': f"{processing_time:.2f}s"
            }
            return jsonify(response)
        else:
            logger.warning(f"[{request_id}] Book not found: {isbn}")
            return jsonify({
                'error': 'Book not found',
                'request_id': request_id
            }), 404
        
    except Exception as e:
        logger.exception(f"[{request_id}] Error retrieving book {isbn}: {e}")
        return jsonify({
            'error': 'Internal server error', 
            'message': str(e),
            'request_id': request_id
        }), 500

@app.route('/api/books/<isbn>/chapters', methods=['GET'])
def get_chapters_api(isbn):
    """API endpoint to get chapters for a specific book"""
    request_id = f"req_{datetime.now().strftime('%Y%m%d%H%M%S')}_{id(request)}"
    logger.info(f"[{request_id}] Received request to list chapters for book ISBN: {isbn}")
    
    try:
        # Start timer for performance tracking
        start_time = datetime.now()
        
        # Validate ISBN
        if not isbn or not isbn.strip():
            logger.warning(f"[{request_id}] Invalid ISBN provided: {isbn}")
            return jsonify({
                'error': 'Invalid ISBN',
                'request_id': request_id
            }), 400
        
        # Clean ISBN
        clean_isbn = isbn.strip().replace('-', '').replace(' ', '')
        if clean_isbn != isbn:
            logger.debug(f"[{request_id}] Cleaned ISBN from '{isbn}' to '{clean_isbn}'")
        
        chapters = bookbytes.get_book_chapters(clean_isbn)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        if chapters:
            logger.info(f"[{request_id}] Retrieved {len(chapters)} chapters for book ISBN: {clean_isbn} in {processing_time:.2f} seconds")
            logger.debug(f"[{request_id}] Chapter numbers: {[chapter.get('chapter_number') for chapter in chapters]}")
        else:
            logger.warning(f"[{request_id}] No chapters found for book ISBN: {clean_isbn}")
        
        response = {
            'chapters': chapters,
            'count': len(chapters),
            'isbn': clean_isbn,
            'request_id': request_id,
            'processing_time': f"{processing_time:.2f}s"
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.exception(f"[{request_id}] Error retrieving chapters for ISBN {isbn}: {e}")
        return jsonify({
            'error': 'Internal server error', 
            'message': str(e),
            'request_id': request_id
        }), 500

@app.route('/api/audio/<isbn>/<int:chapter_number>', methods=['GET'])
def get_audio_api(isbn, chapter_number):
    """API endpoint to serve audio files"""
    request_id = f"req_{datetime.now().strftime('%Y%m%d%H%M%S')}_{id(request)}"
    logger.info(f"[{request_id}] Received request for audio file - ISBN: {isbn}, Chapter: {chapter_number}")
    
    try:
        # Start timer for performance tracking
        start_time = datetime.now()
        
        # Validate ISBN
        if not isbn or not isbn.strip():
            logger.warning(f"[{request_id}] Invalid ISBN provided: {isbn}")
            return jsonify({
                'error': 'Invalid ISBN',
                'request_id': request_id
            }), 400
        
        # Clean ISBN
        clean_isbn = isbn.strip().replace('-', '').replace(' ', '')
        
        # Validate chapter number
        if chapter_number <= 0:
            logger.warning(f"[{request_id}] Invalid chapter number: {chapter_number}")
            return jsonify({
                'error': 'Invalid chapter number',
                'request_id': request_id
            }), 400
        
        logger.debug(f"[{request_id}] Looking up audio file path in database")
        conn = sqlite3.connect(bookbytes.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT audio_file_path, title FROM chapters
            WHERE book_isbn = ? AND chapter_number = ?
        """, (clean_isbn, chapter_number))
        
        result = cursor.fetchone()
        conn.close()
        
        # Calculate database lookup time
        db_lookup_time = (datetime.now() - start_time).total_seconds()
        logger.debug(f"[{request_id}] Database lookup completed in {db_lookup_time:.2f} seconds")
        
        if result and result[0] and os.path.exists(result[0]):
            audio_path = result[0]
            chapter_title = result[1]
            
            # Get file size
            file_size = os.path.getsize(audio_path) / (1024 * 1024)  # Size in MB
            logger.info(f"[{request_id}] Serving audio file: {audio_path} ({file_size:.2f} MB)")
            logger.debug(f"[{request_id}] Chapter title: {chapter_title}")
            
            # Set response headers for better download experience
            response = send_file(
                audio_path, 
                mimetype='audio/mpeg',
                as_attachment=request.args.get('download') == 'true',
                download_name=f"{clean_isbn}_chapter_{chapter_number}.mp3" if request.args.get('download') == 'true' else None
            )
            
            # Add custom headers
            response.headers['X-Request-ID'] = request_id
            response.headers['X-Chapter-Title'] = chapter_title
            response.headers['X-File-Size'] = f"{file_size:.2f} MB"
            
            return response
        else:
            logger.warning(f"[{request_id}] Audio file not found for ISBN: {clean_isbn}, Chapter: {chapter_number}")
            if result:
                logger.debug(f"[{request_id}] Database returned path: {result[0]}, but file does not exist")
            
            return jsonify({
                'error': 'Audio file not found',
                'request_id': request_id
            }), 404
            
    except sqlite3.Error as e:
        logger.error(f"[{request_id}] Database error while serving audio: {e}")
        return jsonify({
            'error': 'Database error',
            'message': str(e),
            'request_id': request_id
        }), 500
    except Exception as e:
        logger.exception(f"[{request_id}] Unexpected error serving audio: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e),
            'request_id': request_id
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    request_id = f"req_{datetime.now().strftime('%Y%m%d%H%M%S')}_{id(request)}"
    logger.debug(f"[{request_id}] Health check request received")
    
    try:
        # Check database connection
        db_status = "healthy"
        db_error = None
        try:
            conn = sqlite3.connect(bookbytes.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            conn.close()
        except Exception as e:
            db_status = "unhealthy"
            db_error = str(e)
            logger.error(f"[{request_id}] Database health check failed: {e}")
        
        # Check audio directory
        audio_dir_status = "healthy" if os.path.exists(bookbytes.audio_dir) and os.access(bookbytes.audio_dir, os.W_OK) else "unhealthy"
        if audio_dir_status == "unhealthy":
            logger.warning(f"[{request_id}] Audio directory health check failed: {bookbytes.audio_dir}")
        
        # Check OpenAI API key
        openai_status = "healthy" if os.getenv("OPENAI_API_KEY") else "missing"
        if openai_status != "healthy":
            logger.warning(f"[{request_id}] OpenAI API key not configured")
        
        response = {
            'status': 'healthy' if db_status == "healthy" and audio_dir_status == "healthy" else 'degraded',
            'timestamp': datetime.now().isoformat(),
            'request_id': request_id,
            'components': {
                'database': {
                    'status': db_status,
                    'error': db_error
                },
                'audio_directory': {
                    'status': audio_dir_status,
                    'path': str(bookbytes.audio_dir)
                },
                'openai_api': {
                    'status': openai_status
                }
            },
            'version': '0.0.0'
        }
        
        logger.debug(f"[{request_id}] Health check completed with status: {response['status']}")
        return jsonify(response)
        
    except Exception as e:
        logger.exception(f"[{request_id}] Error during health check: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e),
            'request_id': request_id
        }), 500

if __name__ == '__main__':
    startup_time = datetime.now()
    logger.info(f"Starting BookBytes application at {startup_time.isoformat()}")
    
    # Log environment configuration
    port = int(os.getenv('PORT', 5000))
    db_path = os.getenv('DB_PATH', 'bookbytes.db')
    audio_dir = os.getenv('AUDIO_DIR', 'audio')
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() in ('true', '1', 't')
    
    logger.info(f"Configuration: PORT={port}, DB_PATH={db_path}, AUDIO_DIR={audio_dir}, DEBUG={debug_mode}")
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY environment variable not set. AI-powered features will not work.")
        logger.warning("Please set the OPENAI_API_KEY environment variable to enable all features.")
    else:
        logger.info("OpenAI API key detected")
    
    # Initialize the BookBytes application
    try:
        logger.info("Initializing BookBytes application...")
        bookbytes = BookBytesApp(db_path=db_path, audio_dir=audio_dir)
        logger.info("BookBytes application initialized successfully")
        
        # Log database and audio directory status
        logger.info(f"Database path: {bookbytes.db_path}")
        logger.info(f"Audio directory: {bookbytes.audio_dir}")
        
        # Check if audio directory exists and is writable
        if not os.path.exists(bookbytes.audio_dir):
            logger.warning(f"Audio directory does not exist: {bookbytes.audio_dir}")
            logger.info("Creating audio directory...")
            try:
                os.makedirs(bookbytes.audio_dir, exist_ok=True)
                logger.info(f"Created audio directory: {bookbytes.audio_dir}")
            except Exception as e:
                logger.error(f"Failed to create audio directory: {e}")
        elif not os.access(bookbytes.audio_dir, os.W_OK):
            logger.error(f"Audio directory is not writable: {bookbytes.audio_dir}")
        
        # Run the Flask app
        logger.info(f"Starting Flask server on host='0.0.0.0', port={port}, debug={debug_mode}")
        app.run(debug=debug_mode, host='0.0.0.0', port=port)
        
    except Exception as e:
        logger.exception(f"Failed to initialize BookBytes application: {e}")
        sys.exit(1)