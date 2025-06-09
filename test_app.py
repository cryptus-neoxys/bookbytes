#!/usr/bin/env python3
"""
Test script for BookBytes application
Demonstrates basic functionality and API usage
"""

import requests
import json
import time
import os
from pathlib import Path

class BookBytesTest:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_health_check(self):
        """Test the health check endpoint"""
        print("\n🔍 Testing health check...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ Health check passed")
                print(f"   Response: {response.json()}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def test_process_book(self, isbn):
        """Test processing a book by ISBN"""
        print(f"\n📚 Testing book processing for ISBN: {isbn}")
        try:
            payload = {"isbn": isbn}
            response = self.session.post(
                f"{self.base_url}/api/process",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Book processing successful")
                print(f"   Title: {result.get('book', {}).get('title', 'Unknown')}")
                print(f"   Author: {result.get('book', {}).get('author', 'Unknown')}")
                print(f"   Chapters processed: {result.get('chapters_processed', 0)}")
                print(f"   Message: {result.get('message', '')}")
                return True, result
            else:
                print(f"❌ Book processing failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('message', 'Unknown error')}")
                except:
                    print(f"   Error: {response.text}")
                return False, None
        except Exception as e:
            print(f"❌ Book processing error: {e}")
            return False, None
    
    def test_list_books(self):
        """Test listing all books"""
        print("\n📖 Testing book listing...")
        try:
            response = self.session.get(f"{self.base_url}/api/books")
            if response.status_code == 200:
                result = response.json()
                books = result.get('books', [])
                print(f"✅ Found {len(books)} books")
                for book in books:
                    print(f"   - {book.get('title', 'Unknown')} by {book.get('author', 'Unknown')}")
                    print(f"     ISBN: {book.get('isbn', 'Unknown')}, Chapters: {book.get('chapter_count', 0)}")
                return True, books
            else:
                print(f"❌ Book listing failed: {response.status_code}")
                return False, []
        except Exception as e:
            print(f"❌ Book listing error: {e}")
            return False, []
    
    def test_get_chapters(self, isbn):
        """Test getting chapters for a specific book"""
        print(f"\n📑 Testing chapter retrieval for ISBN: {isbn}")
        try:
            response = self.session.get(f"{self.base_url}/api/books/{isbn}/chapters")
            if response.status_code == 200:
                result = response.json()
                chapters = result.get('chapters', [])
                print(f"✅ Found {len(chapters)} chapters")
                for chapter in chapters[:3]:  # Show first 3 chapters
                    print(f"   Chapter {chapter.get('chapter_number', 0)}: {chapter.get('title', 'Unknown')}")
                    print(f"     Words: {chapter.get('word_count', 0)}, Audio: {bool(chapter.get('audio_file_path'))}")
                if len(chapters) > 3:
                    print(f"   ... and {len(chapters) - 3} more chapters")
                return True, chapters
            else:
                print(f"❌ Chapter retrieval failed: {response.status_code}")
                return False, []
        except Exception as e:
            print(f"❌ Chapter retrieval error: {e}")
            return False, []
    
    def test_download_audio(self, isbn, chapter_number, output_dir="test_audio"):
        """Test downloading audio for a specific chapter"""
        print(f"\n🎵 Testing audio download for ISBN: {isbn}, Chapter: {chapter_number}")
        try:
            # Create output directory
            Path(output_dir).mkdir(exist_ok=True)
            
            response = self.session.get(f"{self.base_url}/api/audio/{isbn}/{chapter_number}")
            if response.status_code == 200:
                filename = f"{output_dir}/{isbn}_chapter_{chapter_number:02d}.mp3"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                
                file_size = os.path.getsize(filename)
                print(f"✅ Audio downloaded successfully")
                print(f"   File: {filename}")
                print(f"   Size: {file_size:,} bytes")
                return True, filename
            else:
                print(f"❌ Audio download failed: {response.status_code}")
                return False, None
        except Exception as e:
            print(f"❌ Audio download error: {e}")
            return False, None
    
    def run_full_test(self, test_isbn="9780307887894"):
        """Run a complete test suite"""
        print("🚀 Starting BookBytes Test Suite")
        print("=" * 50)
        
        # Test 1: Health check
        if not self.test_health_check():
            print("\n❌ Health check failed. Make sure the server is running.")
            return False
        
        # Test 2: Process a book
        success, book_data = self.test_process_book(test_isbn)
        if not success:
            print("\n❌ Book processing failed. Check your OpenAI API key and internet connection.")
            return False
        
        # Wait a moment for processing to complete
        time.sleep(2)
        
        # Test 3: List books
        success, books = self.test_list_books()
        if not success:
            print("\n❌ Book listing failed.")
            return False
        
        # Test 4: Get chapters
        success, chapters = self.test_get_chapters(test_isbn)
        if not success or not chapters:
            print("\n❌ Chapter retrieval failed.")
            return False
        
        # Test 5: Download audio for first chapter
        success, audio_file = self.test_download_audio(test_isbn, 1)
        if not success:
            print("\n❌ Audio download failed.")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed successfully!")
        print("\n📊 Test Summary:")
        print(f"   ✅ Health check: OK")
        print(f"   ✅ Book processing: OK")
        print(f"   ✅ Book listing: OK")
        print(f"   ✅ Chapter retrieval: OK")
        print(f"   ✅ Audio download: OK")
        
        if audio_file:
            print(f"\n🎵 Sample audio file created: {audio_file}")
            print("   You can play this file to test the audio quality.")
        
        return True

def main():
    """Main test function"""
    print("BookBytes Test Script")
    print("====================\n")
    
    # Check if server is likely running
    tester = BookBytesTest()
    
    # Test with a well-known book
    test_isbns = [
        "9780307887894",  # The Power of Habit
        "9780735211292",  # Atomic Habits
        "9780374533557",  # Thinking, Fast and Slow
    ]
    
    print("Available test ISBNs:")
    for i, isbn in enumerate(test_isbns, 1):
        print(f"  {i}. {isbn}")
    
    # Use the first ISBN for testing
    test_isbn = test_isbns[0]
    print(f"\nUsing ISBN: {test_isbn} for testing")
    
    # Run the full test suite
    success = tester.run_full_test(test_isbn)
    
    if success:
        print("\n🎯 Next steps:")
        print("   1. Try processing other books with different ISBNs")
        print("   2. Listen to the generated audio files")
        print("   3. Integrate the API into your own applications")
        print("   4. Explore the database to see stored data")
    else:
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure the server is running: python app.py")
        print("   2. Check your OpenAI API key is set: export OPENAI_API_KEY='your-key'")
        print("   3. Ensure you have internet connectivity")
        print("   4. Check the server logs for detailed error messages")

if __name__ == "__main__":
    main()