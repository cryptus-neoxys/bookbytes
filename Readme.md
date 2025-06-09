# BookBytes 📚🎧

BookBytes is a Python application that converts non-fiction books into chapter-wise audio summaries for faster and more convenient knowledge consumption. Transform a 200-page book into 15-20 digestible 5-minute audio bites!

## 🎯 Problem Statement

- **Problem**: Long books, no time to read
- **Solution**: Short, condensed audio bytes for simpler consumption
- **Value**: 200-page book → 15-20 chapters → 5 mins audio bites each → 1.5-2hrs total

## 🚀 Features

- **ISBN-based book lookup**: Enter any book's ISBN to get started
- **Automatic chapter detection**: Uses LLM to identify book chapters
- **AI-powered summaries**: Generates concise, informative chapter summaries
- **Text-to-speech conversion**: Converts summaries to high-quality audio
- **RESTful API**: Easy-to-use API for integration
- **Database storage**: Persistent storage for books, chapters, and audio files

## 🛠️ Technology Stack

- **Backend**: Python, Flask
- **Database**: SQLite
- **AI/LLM**: OpenAI GPT-3.5-turbo
- **Text-to-Speech**: Google Text-to-Speech (gTTS)
- **Book Data**: Open Library API

## 📋 Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Internet connection (for API calls)

## 🔧 Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd bookbytes
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   ```
   
   Or create a `.env` file:
   ```
   OPENAI_API_KEY=your-openai-api-key-here
   ```

## 🚀 Usage

### Starting the Server

```bash
python app.py
```

The server will start on `http://localhost:5000`

### API Endpoints

#### 1. Process a Book
**POST** `/api/process`

```bash
curl -X POST http://localhost:5000/api/process \
  -H "Content-Type: application/json" \
  -d '{"isbn": "9780307887894"}'
```

**Response**:
```json
{
  "success": true,
  "message": "Successfully processed 12 out of 12 chapters",
  "book": {
    "isbn": "9780307887894",
    "title": "The Power of Habit",
    "author": "Charles Duhigg"
  },
  "chapters_processed": 12
}
```

#### 2. List All Books
**GET** `/api/books`

```bash
curl http://localhost:5000/api/books
```

**Response**:
```json
{
  "books": [
    {
      "isbn": "9780307887894",
      "title": "The Power of Habit",
      "author": "Charles Duhigg",
      "pages": 371,
      "publish_date": "2012",
      "chapter_count": 12
    }
  ]
}
```

#### 3. Get Book Chapters
**GET** `/api/books/{isbn}/chapters`

```bash
curl http://localhost:5000/api/books/9780307887894/chapters
```

**Response**:
```json
{
  "chapters": [
    {
      "chapter_number": 1,
      "title": "The Habit Loop",
      "summary": "This chapter introduces the concept of the habit loop...",
      "audio_file_path": "audio/9780307887894_chapter_01.mp3",
      "word_count": 142
    }
  ]
}
```

#### 4. Get Chapter Audio
**GET** `/api/audio/{isbn}/{chapter_number}`

```bash
curl http://localhost:5000/api/audio/9780307887894/1 --output chapter1.mp3
```

#### 5. Health Check
**GET** `/health`

```bash
curl http://localhost:5000/health
```

## 📁 Project Structure

```
bookbytes/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .env                  # Environment variables (create this)
├── bookbytes.db          # SQLite database (auto-created)
├── audio/                # Generated audio files (auto-created)
│   ├── {isbn}_chapter_01.mp3
│   ├── {isbn}_chapter_02.mp3
│   └── ...
├── knowledge/
│   └── docs.md           # Project documentation
└── samples/              # Sample audio files
    └── ...
```

## 🔄 Processing Flow

1. **User Input**: Provide book ISBN
2. **Book Lookup**: Fetch book details from Open Library API
3. **Chapter Detection**: Use LLM to identify book chapters
4. **Summary Generation**: Generate concise summaries for each chapter
5. **Audio Conversion**: Convert text summaries to audio using TTS
6. **Storage**: Save book, chapters, and audio files to database
7. **API Access**: Serve content through RESTful API

## 🎵 Audio Quality

- **Format**: MP3
- **Quality**: Standard quality suitable for speech
- **Duration**: Typically 3-7 minutes per chapter
- **Language**: English (configurable)

## 🔒 Legal Considerations

- **Fair Use**: Generates transformative summaries for educational purposes
- **Copyright Compliance**: Does not reproduce substantial portions of original works
- **Educational Purpose**: Designed for knowledge consumption and learning

## 🚧 Limitations

- **LLM Knowledge**: Limited to books in the training data
- **Chapter Detection**: May not work for all books
- **Summary Quality**: Depends on LLM's knowledge of the specific book
- **API Costs**: OpenAI API usage incurs costs

## 🔮 Future Enhancements (v0.1.0+)

- Chapter-wise audio storage with metadata
- Timestamp tracking for audio navigation
- Support for book titles instead of ISBN
- Multiple TTS voice options
- Batch processing capabilities
- Web interface for easier interaction

## 🐛 Troubleshooting

### Common Issues

1. **"OpenAI API key not configured"**
   - Ensure `OPENAI_API_KEY` environment variable is set
   - Check that the API key is valid and has sufficient credits

2. **"Book not found for ISBN"**
   - Verify the ISBN is correct (10 or 13 digits)
   - Try removing hyphens from the ISBN
   - Check if the book exists in Open Library

3. **"Could not retrieve chapters"**
   - The book might not be in the LLM's training data
   - Try a more popular or well-known book

4. **Audio generation fails**
   - Check internet connection (gTTS requires internet)
   - Ensure the `audio/` directory is writable

### Debug Mode

Run the application in debug mode for more detailed logs:

```bash
FLASK_DEBUG=1 python app.py
```

## 📊 Example Books to Try

- **The Power of Habit** - ISBN: 9780307887894
- **Atomic Habits** - ISBN: 9780735211292
- **Thinking, Fast and Slow** - ISBN: 9780374533557
- **The 7 Habits of Highly Effective People** - ISBN: 9780743269513

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Open Library for book metadata
- OpenAI for LLM capabilities
- Google for Text-to-Speech services
- Flask community for the web framework

---

**Happy Learning! 🎓📚**