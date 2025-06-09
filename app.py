#!/usr/bin/env python3
"""
BookBytes - Audio Book Summarizer
Converts non-fiction books into chapter-wise audio summaries
"""

import os
import json
import sqlite3
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging
from datetime import datetime

# Third-party imports
from flask import Flask, request, jsonify, send_file
from gtts import gTTS
import openai
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
        conn.close()
    
    def fetch_book_details(self, isbn: str) -> Optional[Book]:
        """Fetch book details from Open Library API"""
        try:
            # Clean ISBN (remove hyphens, spaces)
            clean_isbn = isbn.replace('-', '').replace(' ', '')
            
            # Try Open Library API
            url = f"https://openlibrary.org/isbn/{clean_isbn}.json"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract book details
                title = data.get('title', 'Unknown Title')
                
                # Get authors
                authors = []
                if 'authors' in data:
                    for author_ref in data['authors']:
                        author_key = author_ref['key']
                        author_response = requests.get(f"https://openlibrary.org{author_key}.json", timeout=5)
                        if author_response.status_code == 200:
                            author_data = author_response.json()
                            authors.append(author_data.get('name', 'Unknown Author'))
                
                author = ', '.join(authors) if authors else 'Unknown Author'
                pages = data.get('number_of_pages')
                publish_date = data.get('publish_date')
                
                return Book(
                    isbn=clean_isbn,
                    title=title,
                    author=author,
                    pages=pages,
                    publish_date=publish_date
                )
            else:
                logger.warning(f"Book not found for ISBN: {isbn}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching book details for ISBN {isbn}: {e}")
            return None
    
    def get_chapters_from_llm(self, book: Book) -> List[str]:
        """Get list of chapters from LLM"""
        if not self.openai_client:
            logger.error("OpenAI API key not configured")
            return []
        
        try:
            prompt = f"""
            List the chapters for the book "{book.title}" by "{book.author}".
            """
            
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
            
            content = response.choices[0].message.content.strip()
            
            if content.upper() == "UNKNOWN":
                logger.warning(f"LLM doesn't have knowledge of chapters for: {book.title}")
                return []
            
            # Parse chapter titles
            chapters = [line.strip() for line in content.split('\n') if line.strip()]
            logger.info(f"Found {len(chapters)} chapters for {book.title}")
            return chapters
            
        except Exception as e:
            logger.error(f"Error getting chapters from LLM: {e}")
            return []
    
    def generate_chapter_summary(self, book: Book, chapter_title: str) -> Optional[str]:
        """Generate summary for a specific chapter"""
        if not self.openai_client:
            logger.error("OpenAI API key not configured")
            return None
        
        try:
            prompt = f"""
            {chapter_title}, {book.title} by {book.author}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {"role": "system","content": [{"text": "You are a bookworm with exact, detailed knowledge of popular non-fiction, non-educational books.\n\nProvide a detailed and insightful summary strictly in about 450-500 words of [CHAPTER_TITLE], [BOOK_TITLE] by [AUTHOR]. Focus on core insights and key points, and stick to the precise chapter content to create an effective summary. Ensure that the summarisation of the chapter summary strictly falls between 450-500 words. Return only the response that strictly adheres to the described schema. Do not add commentary, additional tags, or anything except the summary. !IMP & Non-Negotiable: 1. Proper 450-500 words summary, 2. output is just the summary as requested, 3. plain summary paragraphs in text output, nothing else.\n\n<input_format>\n[CHAPTER_TITLE], [BOOK_TITLE] by [AUTHOR]\n</input_format>\n\n<output_schema>\n[SUMMARY]\n</output_schema>\n\n<sample_input>\nAll Problems Are Interpersonal Relationship Problems, The Courage to Be Disliked by Ichiro Kishimi and Fumitake Koga\n</sample_input>\n\n<sample_output>\nChapter 2 of 'The Courage to Be Disliked' by Ichiro Kishimi and Fumitake Koga, titled 'All Problems Are Interpersonal Relationship Problems', delves into the foundational Adlerian psychological concept that every personal issue stems from complications in relationships with others ...\n</sample_output>","type": "text"}]},
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
            
            content = response.choices[0].message.content.strip()
            logger.info(f"Summary for {chapter_title}: {content}")
            
            if content.upper() == "UNKNOWN":
                logger.warning(f"LLM doesn't have knowledge of chapter: {chapter_title}")
                return None
            
            return content
            
        except Exception as e:
            logger.error(f"Error generating summary for chapter {chapter_title}: {e}")
            return None
    
    def text_to_speech(self, text: str, output_path: str, lang: str = 'en') -> bool:
        """Convert text to speech using gTTS"""
        try:
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(output_path)
            logger.info(f"Audio saved to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error converting text to speech: {e}")
            return False
    
    def save_book(self, book: Book) -> bool:
        """Save book to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO books (isbn, title, author, pages, publish_date)
                VALUES (?, ?, ?, ?, ?)
            """, (book.isbn, book.title, book.author, book.pages, book.publish_date))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving book: {e}")
            return False
    
    def save_chapter(self, chapter: Chapter) -> bool:
        """Save chapter to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO chapters 
                (book_isbn, chapter_number, title, summary, audio_file_path, word_count)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (chapter.book_isbn, chapter.chapter_number, chapter.title, 
                   chapter.summary, chapter.audio_file_path, chapter.word_count))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving chapter: {e}")
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
        chapter_titles = self.get_chapters_from_llm(book)
        
        if not chapter_titles:
            result['message'] = f"Could not retrieve chapters for book: {book.title}"
            return result
        
        # Step 3: Process each chapter
        processed_chapters = 0
        
        for i, chapter_title in enumerate(chapter_titles, 1):
            logger.info(f"Processing chapter {i}: {chapter_title}")
            
            # Generate summary
            summary = self.generate_chapter_summary(book, chapter_title)
            
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
                    title=chapter_title,
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
        result['message'] = f"Successfully processed {processed_chapters} out of {len(chapter_titles)} chapters"
        
        return result
    
    def get_all_books(self) -> List[Dict]:
        """Get all books from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
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
            
            conn.close()
            return books
        except Exception as e:
            logger.error(f"Error fetching books: {e}")
            return []
    
    def get_book_chapters(self, isbn: str) -> List[Dict]:
        """Get all chapters for a specific book"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT chapter_number, title, summary, audio_file_path, word_count
                FROM chapters
                WHERE book_isbn = ?
                ORDER BY chapter_number
            """, (isbn,))
            
            chapters = []
            for row in cursor.fetchall():
                chapters.append({
                    'chapter_number': row[0],
                    'title': row[1],
                    'summary': row[2],
                    'audio_file_path': row[3],
                    'word_count': row[4]
                })
            
            conn.close()
            return chapters
        except Exception as e:
            logger.error(f"Error fetching chapters for ISBN {isbn}: {e}")
            return []

# Flask API
app = Flask(__name__)
bookbytes = BookBytesApp()

@app.route('/api/process', methods=['POST'])
def process_book_api():
    """API endpoint to process a book by ISBN"""
    data = request.get_json()
    
    if not data or 'isbn' not in data:
        return jsonify({'error': 'ISBN is required'}), 400
    
    isbn = data['isbn'].strip()
    
    if not isbn:
        return jsonify({'error': 'Invalid ISBN'}), 400
    
    result = bookbytes.process_book(isbn)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@app.route('/api/books', methods=['GET'])
def get_books_api():
    """API endpoint to get all processed books"""
    books = bookbytes.get_all_books()
    return jsonify({'books': books})

@app.route('/api/books/<isbn>/chapters', methods=['GET'])
def get_chapters_api(isbn):
    """API endpoint to get chapters for a specific book"""
    chapters = bookbytes.get_book_chapters(isbn)
    return jsonify({'chapters': chapters})

@app.route('/api/audio/<isbn>/<int:chapter_number>', methods=['GET'])
def get_audio_api(isbn, chapter_number):
    """API endpoint to serve audio files"""
    try:
        conn = sqlite3.connect(bookbytes.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT audio_file_path FROM chapters
            WHERE book_isbn = ? AND chapter_number = ?
        """, (isbn, chapter_number))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] and os.path.exists(result[0]):
            return send_file(result[0], mimetype='audio/mpeg')
        else:
            return jsonify({'error': 'Audio file not found'}), 404
            
    except Exception as e:
        logger.error(f"Error serving audio: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    # Check for required environment variables
    if not os.getenv('OPENAI_API_KEY'):
        print("Warning: OPENAI_API_KEY environment variable not set")
        print("Set it with: export OPENAI_API_KEY='your-api-key-here'")
    
    print("Starting BookBytes API server...")
    print("Available endpoints:")
    print("  POST /api/process - Process a book by ISBN")
    print("  GET /api/books - List all processed books")
    print("  GET /api/books/<isbn>/chapters - Get chapters for a book")
    print("  GET /api/audio/<isbn>/<chapter_number> - Get audio for a chapter")
    print("  GET /health - Health check")
    
    app.run(debug=True, host='0.0.0.0', port=5000)