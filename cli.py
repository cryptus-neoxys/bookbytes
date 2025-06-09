#!/usr/bin/env python3
"""
BookBytes CLI - Command Line Interface
Provides easy command-line access to BookBytes functionality
"""

import argparse
import sys
import os
import json
from pathlib import Path

# Add the current directory to Python path to import our app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import BookBytesApp

def setup_environment():
    """Setup environment variables from .env file if it exists"""
    env_file = Path('.env')
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("✅ Loaded environment variables from .env file")
        except ImportError:
            print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
            print("   Or set environment variables manually")

def process_book_command(args):
    """Process a book by ISBN"""
    print(f"📚 Processing book with ISBN: {args.isbn}")
    
    app = BookBytesApp()
    result = app.process_book(args.isbn)
    
    if result['success']:
        print("\n✅ Book processing completed successfully!")
        print(f"   Title: {result['book']['title']}")
        print(f"   Author: {result['book']['author']}")
        print(f"   Chapters processed: {result['chapters_processed']}")
        
        if args.output_json:
            output_file = f"{result['book']['isbn']}_result.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"   Result saved to: {output_file}")
    else:
        print(f"\n❌ Book processing failed: {result['message']}")
        sys.exit(1)

def list_books_command(args):
    """List all processed books"""
    print("📖 Listing all processed books...\n")
    
    app = BookBytesApp()
    books = app.get_all_books()
    
    if not books:
        print("No books found. Process some books first using the 'process' command.")
        return
    
    for i, book in enumerate(books, 1):
        print(f"{i}. {book['title']} by {book['author']}")
        print(f"   ISBN: {book['isbn']}")
        print(f"   Chapters: {book['chapter_count']}")
        if book['pages']:
            print(f"   Pages: {book['pages']}")
        if book['publish_date']:
            print(f"   Published: {book['publish_date']}")
        print()
    
    if args.output_json:
        output_file = "books_list.json"
        with open(output_file, 'w') as f:
            json.dump({'books': books}, f, indent=2)
        print(f"📄 Book list saved to: {output_file}")

def chapters_command(args):
    """List chapters for a specific book"""
    print(f"📑 Listing chapters for ISBN: {args.isbn}\n")
    
    app = BookBytesApp()
    chapters = app.get_book_chapters(args.isbn)
    
    if not chapters:
        print(f"No chapters found for ISBN: {args.isbn}")
        print("Make sure the book has been processed first.")
        return
    
    total_words = sum(ch.get('word_count', 0) for ch in chapters)
    
    print(f"Found {len(chapters)} chapters (Total words: {total_words:,})\n")
    
    for chapter in chapters:
        print(f"Chapter {chapter['chapter_number']}: {chapter['title']}")
        print(f"   Words: {chapter.get('word_count', 0)}")
        print(f"   Audio: {'✅' if chapter.get('audio_file_path') else '❌'}")
        
        if args.show_summary:
            summary = chapter.get('summary', '')
            if summary:
                # Show first 100 characters of summary
                preview = summary[:100] + "..." if len(summary) > 100 else summary
                print(f"   Summary: {preview}")
        print()
    
    if args.output_json:
        output_file = f"{args.isbn}_chapters.json"
        with open(output_file, 'w') as f:
            json.dump({'chapters': chapters}, f, indent=2)
        print(f"📄 Chapters saved to: {output_file}")

def audio_command(args):
    """Generate or check audio files"""
    print(f"🎵 Audio operations for ISBN: {args.isbn}")
    
    app = BookBytesApp()
    chapters = app.get_book_chapters(args.isbn)
    
    if not chapters:
        print(f"No chapters found for ISBN: {args.isbn}")
        return
    
    audio_files = []
    missing_audio = []
    
    for chapter in chapters:
        audio_path = chapter.get('audio_file_path')
        if audio_path and os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            audio_files.append({
                'chapter': chapter['chapter_number'],
                'title': chapter['title'],
                'path': audio_path,
                'size': file_size
            })
        else:
            missing_audio.append(chapter)
    
    print(f"\n📊 Audio Status:")
    print(f"   Available: {len(audio_files)} files")
    print(f"   Missing: {len(missing_audio)} files")
    
    if audio_files:
        total_size = sum(f['size'] for f in audio_files)
        print(f"   Total size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
        
        if args.list_files:
            print("\n🎵 Available audio files:")
            for audio in audio_files:
                print(f"   Chapter {audio['chapter']}: {audio['title']}")
                print(f"     File: {audio['path']}")
                print(f"     Size: {audio['size']:,} bytes")
    
    if missing_audio:
        print(f"\n⚠️  Missing audio for {len(missing_audio)} chapters:")
        for chapter in missing_audio:
            print(f"   Chapter {chapter['chapter_number']}: {chapter['title']}")

def server_command(args):
    """Start the Flask server"""
    print("🚀 Starting BookBytes API server...")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Debug: {args.debug}")
    print("\n📡 Available endpoints:")
    print("   POST /api/process - Process a book by ISBN")
    print("   GET /api/books - List all processed books")
    print("   GET /api/books/<isbn>/chapters - Get chapters for a book")
    print("   GET /api/audio/<isbn>/<chapter_number> - Get audio for a chapter")
    print("   GET /health - Health check")
    print("\nPress Ctrl+C to stop the server\n")
    
    # Import and run the Flask app
    from app import app
    app.run(debug=args.debug, host=args.host, port=args.port)

def status_command(args):
    """Show system status and configuration"""
    print("🔍 BookBytes System Status\n")
    
    # Check environment
    openai_key = os.getenv('OPENAI_API_KEY')
    print(f"OpenAI API Key: {'✅ Set' if openai_key else '❌ Not set'}")
    
    # Check database
    db_path = "bookbytes.db"
    print(f"Database: {'✅ Exists' if os.path.exists(db_path) else '❌ Not found'} ({db_path})")
    
    # Check audio directory
    audio_dir = Path("audio")
    print(f"Audio directory: {'✅ Exists' if audio_dir.exists() else '❌ Not found'} ({audio_dir})")
    
    if audio_dir.exists():
        audio_files = list(audio_dir.glob("*.mp3"))
        print(f"Audio files: {len(audio_files)} found")
    
    # Check books in database
    if os.path.exists(db_path):
        app = BookBytesApp()
        books = app.get_all_books()
        print(f"Processed books: {len(books)}")
        
        if books:
            total_chapters = sum(book['chapter_count'] for book in books)
            print(f"Total chapters: {total_chapters}")
    
    print("\n📋 Configuration:")
    print(f"   Python: {sys.version.split()[0]}")
    print(f"   Working directory: {os.getcwd()}")
    
    # Check dependencies
    try:
        import flask
        print(f"   Flask: {flask.__version__}")
    except ImportError:
        print("   Flask: ❌ Not installed")
    
    try:
        import openai
        print(f"   OpenAI: {openai.__version__}")
    except ImportError:
        print("   OpenAI: ❌ Not installed")
    
    try:
        import gtts
        print("   gTTS: ✅ Available")
    except ImportError:
        print("   gTTS: ❌ Not installed")

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="BookBytes CLI - Convert books to audio summaries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s process 9780307887894                    # Process a book
  %(prog)s list                                     # List all books
  %(prog)s chapters 9780307887894                   # Show chapters
  %(prog)s audio 9780307887894 --list-files         # Check audio files
  %(prog)s server --port 8000                       # Start server on port 8000
  %(prog)s status                                   # Show system status
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process a book by ISBN')
    process_parser.add_argument('isbn', help='Book ISBN (10 or 13 digits)')
    process_parser.add_argument('--output-json', action='store_true', help='Save result as JSON')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all processed books')
    list_parser.add_argument('--output-json', action='store_true', help='Save list as JSON')
    
    # Chapters command
    chapters_parser = subparsers.add_parser('chapters', help='List chapters for a book')
    chapters_parser.add_argument('isbn', help='Book ISBN')
    chapters_parser.add_argument('--show-summary', action='store_true', help='Show summary preview')
    chapters_parser.add_argument('--output-json', action='store_true', help='Save chapters as JSON')
    
    # Audio command
    audio_parser = subparsers.add_parser('audio', help='Check audio files for a book')
    audio_parser.add_argument('isbn', help='Book ISBN')
    audio_parser.add_argument('--list-files', action='store_true', help='List all audio files')
    
    # Server command
    server_parser = subparsers.add_parser('server', help='Start the API server')
    server_parser.add_argument('--host', default='0.0.0.0', help='Server host (default: 0.0.0.0)')
    server_parser.add_argument('--port', type=int, default=5000, help='Server port (default: 5000)')
    server_parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Setup environment
    setup_environment()
    
    # Route to appropriate command
    if args.command == 'process':
        process_book_command(args)
    elif args.command == 'list':
        list_books_command(args)
    elif args.command == 'chapters':
        chapters_command(args)
    elif args.command == 'audio':
        audio_command(args)
    elif args.command == 'server':
        server_command(args)
    elif args.command == 'status':
        status_command(args)

if __name__ == '__main__':
    main()