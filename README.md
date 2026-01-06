# RAG App built On Navchetna/AIComps Microservices

A comprehensive backend service for Retrieval Augmented Generation (RAG) systems that orchestrates document ingestion, vector database operations, and LLM-powered query answering.

## Architecture Overview

This backend acts as a unified gateway for multiple microservices:

```
┌─────────────────────┐
│   RAG Backend       │
│   (FastAPI)         │
└──────────┬──────────┘
           │
     ┌─────┼─────┬─────────────┐
     │     │     │             │
     ▼     ▼     ▼             ▼
┌──────┐ ┌───┐ ┌──────┐  ┌──────────┐
│PDF   │ │LLM│ │Ret   │  │Chat      │
│Parser│ │   │ │iever │  │Memory    │
└──────┘ └───┘ └──────┘  └──────────┘
     │     │     │
     ▼     ▼     ▼
  Qdrant Vector Database
```

## Features

### 📄 Document Ingestion
- Accepts single or multiple PDF files
- Asynchronous processing pipeline
- Tracks ingestion status per file
- Automatic parsing and vectorization

### 🔍 Intelligent Retrieval
- Vector similarity search using Qdrant
- MPN‌et-base-v2 embeddings (768-dimensional) for semantic understanding
- Context-aware document retrieval
- Configurable similarity thresholds

### 🤖 LLM Integration
- Groq API integration for fast inference
- Context-aware prompt engineering
- RAG flag indicating whether context was used
- Streaming-ready response format

### 💬 Conversation Memory
- SQLite-based chat history tracking
- User-specific conversation context
- Automatic conversation persistence
- Multi-turn conversation support

### 📊 Status Tracking
- Queryable by batch_job_id or batch_job_file_id
- Per-file parsing and preparation status
- Detailed error messages
- Timestamp tracking

## Prerequisites

- Python 3.10+
- Running microservices:
  - PDF Parser (localhost:8000)
  - DataPrep (localhost:5000)
  - Retriever (localhost:7000)
- Qdrant vector database (localhost:6333)
- Groq API key

## Installation

### 1. Clone and Setup

```bash
git clone <your-repo-url> rag-backend
cd rag-backend
python setup.py setup
```

### 2. Configure Environment

Edit `.env` with your configuration:

```bash
cp .env.example .env
# Edit .env with your values:
# - GROQ_API_KEY: Your Groq API key
# - Microservice endpoints if different from defaults
# - Database location (defaults to SQLite)
```

### 3. Run the Server

**Development Mode (with auto-reload):**
```bash
python setup.py run --debug
```

**Production Mode:**
```bash
python setup.py run
```

Or directly with uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port 8080
```

The API will be available at `http://localhost:8080`

## API Endpoints

### Health Check
```bash
GET /health
```
Returns server status and version.

### Ingest Documents
```bash
POST /ingest
Content-Type: multipart/form-data

Parameters:
- files: PDF file(s) to ingest (required)
- user_id: User identifier (optional, defaults to "default")

Response:
{
  "batch_job_id": "batch_123456789.1234567890",
  "batch_job_file_ids": ["batch_123456789.1234567890:document.pdf"],
  "message": "Successfully submitted 1 file(s) for processing",
  "status": "queued"
}
```

**Example:**
```bash
curl -X POST \
  -F "files=@document.pdf" \
  -F "user_id=default" \
  http://localhost:8080/ingest
```

### Check Ingestion Status
```bash
GET /status?batch_job_id=batch_123456789.1234567890
# OR
GET /status?batch_job_file_id=batch_123456789.1234567890:document.pdf

Response:
{
  "batch_job_id": "batch_123456789.1234567890",
  "user_id": "default",
  "status": "completed",  // queued, processing, completed, failed
  "total_files": 1,
  "files": [
    {
      "batch_job_file_id": "batch_123456789.1234567890:document.pdf",
      "filename": "document.pdf",
      "status": "completed",
      "parsing_status": "completed",
      "dataprep_status": "completed",
      "error_message": null,
      "created_at": "2026-01-06T10:30:00",
      "updated_at": "2026-01-06T10:35:00"
    }
  ],
  "created_at": "2026-01-06T10:30:00",
  "updated_at": "2026-01-06T10:35:00",
  "error_message": null
}
```

**Example:**
```bash
curl "http://localhost:8080/status?batch_job_id=batch_123456789.1234567890"
```

### Query the RAG System
```bash
POST /query
Content-Type: application/json

{
  "query": "What is the main topic covered in the documents?",
  "user_id": "default",
  "use_context": true
}

Response:
{
  "query": "What is the main topic covered in the documents?",
  "response": "Based on the provided documents, the main topics include...",
  "used_rag": true,
  "context": "[Document 1 - document.pdf]\nThe document discusses...",
  "created_at": "2026-01-06T10:40:00Z"
}
```

**Example:**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the main topic?",
    "user_id": "default",
    "use_context": true
  }' \
  http://localhost:8080/query
```

## Project Structure

```
rag-backend/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── setup.py              # Setup and utility scripts
├── .env.example          # Environment variables template
├── rag_backend.db        # SQLite database (auto-created)
└── app/
    ├── __init__.py
    ├── database.py       # Database session management
    ├── models.py         # SQLAlchemy ORM models
    ├── schemas.py        # Pydantic request/response schemas
    ├── background_tasks.py  # Async task processing
    ├── services/         # Business logic services
    │   ├── llm_service.py       # Groq LLM integration
    │   ├── embedding_service.py # MiniLM embeddings
    │   ├── pdf_parser_service.py   # PDF Parser API client
    │   ├── dataprep_service.py     # DataPrep API client
    │   └── retriever_service.py    # Vector retriever client
    └── routes/          # API endpoints
        ├── ingest.py    # Document ingestion
        ├── status.py    # Status checking
        └── query.py     # RAG queries
```

## Configuration

All configuration is managed via environment variables in `.env`:

### Application
- `APP_NAME`: Application name
- `APP_VERSION`: Application version
- `DEBUG`: Debug mode flag
- `DATABASE_URL`: SQLite database path

### Microservices
- `PDF_PARSER_HOST/PORT`: PDF Parser service location
- `DATAPREP_HOST/PORT`: DataPrep service location
- `RETRIEVER_HOST/PORT`: Retriever service location
- `QDRANT_HOST/PORT`: Vector database location

### LLM & Embeddings
- `GROQ_API_KEY`: Groq API authentication
- `GROQ_MODEL`: Model name (default: llama-2-70b-chat)
- `EMBEDDING_MODEL`: Embedding model (default: all-MiniLM-L6-v2)

See `.env.example` for all available options.

## Ingestion Pipeline Flow

1. **User uploads PDF(s)** → `/ingest` endpoint
2. **Immediate response** with `batch_job_id` and file IDs
3. **Background task spawned**:
   - Monitors PDF Parser status
   - When parsing completes, calls DataPrep
   - DataPrep vectorizes and stores in Qdrant
4. **Status tracking** via `/status` endpoint

## Query Pipeline Flow

1. **User submits query** → `/query` endpoint
2. **Embedding generation** using MiniLM
3. **Vector similarity search** in Qdrant
4. **LLM processing**:
   - Formats context if found
   - Sends to Groq LLM
   - Includes chat history if available
5. **Response returned** with `usedRAG` flag
6. **Conversation saved** to chat history

## Error Handling

- Failed ingestions tracked with error messages
- Graceful degradation when context unavailable
- Detailed logging for debugging
- Proper HTTP status codes for API errors

## Performance Considerations

- Async background tasks for non-blocking ingestion
- Connection pooling for API calls
- SQLite with proper indexing for fast status checks
- Embeddings cached in memory during session
- Configurable timeouts for microservice calls

## Development

### Running Tests
```bash
# Add pytest to requirements.txt and create test files
pytest tests/
```

### Monitoring
Check logs during operation:
```bash
# Logs are printed to console with timestamps
# Each module has its own logger for granular control
```

### Database Management
```bash
# Database is auto-created at startup
# To reset: delete rag_backend.db and restart the server
```

## Troubleshooting

### Microservice Connection Errors
- Verify microservices are running on configured ports
- Check `.env` for correct host/port settings
- Look for timeout errors in logs

### Embedding Generation Fails
- Ensure sentence-transformers is installed
- First embedding download takes time (model cache)
- Check available disk space

### Groq API Errors
- Verify `GROQ_API_KEY` is set in `.env`
- Check API key validity
- Monitor rate limits

### Database Lock
- SQLite locks on concurrent writes (by design)
- Use PostgreSQL for high concurrency (update DATABASE_URL)

## Production Deployment

### Recommendations
1. Use PostgreSQL instead of SQLite for production
2. Run with Gunicorn + multiple workers:
   ```bash
   gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
   ```
3. Use nginx as reverse proxy
4. Enable HTTPS/TLS
5. Set `DEBUG=False` in `.env`
6. Use proper secret management for API keys
7. Set up monitoring and alerting

### Docker Support
Can be containerized using FastAPI Docker best practices.

## License

MIT

## Support

For issues or questions, check the logs and ensure all microservices are running properly.
