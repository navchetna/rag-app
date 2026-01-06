# RAG Backend - Getting Started Guide

Complete step-by-step instructions to run the RAG Backend system.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Detailed Setup](#detailed-setup)
3. [Running the Application](#running-the-application)
4. [Testing the API](#testing-the-api)
5. [Troubleshooting](#troubleshooting)

## Quick Start

For experienced users, here's the TL;DR:

```bash
# 1. Setup
python setup.py setup

# 2. Configure
cp .env.example .env
# Edit .env and set GROQ_API_KEY

# 3. Run
python setup.py run --debug
```

The API will be available at `http://localhost:8080/docs` (Swagger UI).

---

## Detailed Setup

### Step 1: Prerequisites Check

Ensure you have:
- Python 3.10 or higher
- All microservices running:
  - PDF Parser (port 8000)
  - DataPrep (port 5000)
  - Retriever (port 7000)
- Qdrant vector database (port 6333)
- Groq API key (get from https://console.groq.com)

Check Python version:
```bash
python3 --version
```

Should output: `Python 3.10.x` or higher

### Step 2: Clone/Navigate to Project

```bash
cd /home/alimohammad/rag-backend
```

### Step 3: Create Environment File

```bash
# Copy the example environment file
cp .env.example .env

# Edit it with your configuration
nano .env  # or use your favorite editor
```

**Required Settings:**
- `GROQ_API_KEY`: Your Groq API key
  
**Optional (if microservices on different hosts):**
- `PDF_PARSER_HOST` and `PDF_PARSER_PORT`
- `DATAPREP_HOST` and `DATAPREP_PORT`
- `RETRIEVER_HOST` and `RETRIEVER_PORT`
- `QDRANT_HOST` and `QDRANT_PORT`

Example `.env` file:
```
APP_NAME="RAG Backend"
DEBUG=False
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx
PDF_PARSER_HOST=localhost
PDF_PARSER_PORT=8000
DATAPREP_HOST=localhost
DATAPREP_PORT=5000
RETRIEVER_HOST=localhost
RETRIEVER_PORT=7000
QDRANT_HOST=localhost
QDRANT_PORT=6333
DATABASE_URL=sqlite:///./rag_backend.db
```

### Step 4: Install Dependencies

```bash
python setup.py setup
```

This will:
1. Create the `.env` file if it doesn't exist
2. Install all Python packages from `requirements.txt`
3. Show a success message

Alternatively, manually install:
```bash
pip install -r requirements.txt
```

---

## Running the Application

### Option 1: Using Setup Script (Recommended)

**Development Mode (with auto-reload):**
```bash
python setup.py run --debug
```

**Production Mode:**
```bash
python setup.py run
```

### Option 2: Direct with Uvicorn

```bash
# Development
uvicorn main:app --reload --host 0.0.0.0 --port 8080

# Production
uvicorn main:app --host 0.0.0.0 --port 8080 --workers 4
```

### Option 3: Using Gunicorn (Production)

```bash
pip install gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080
```

### Option 4: Docker Compose

```bash
docker-compose up -d
```

---

## Testing the API

### Check if Server is Running

```bash
curl http://localhost:8080/health
```

Expected response:
```json
{
  "status": "healthy",
  "message": "RAG Backend is running",
  "version": "1.0.0"
}
```

### View Interactive API Documentation

Open in your browser:
```
http://localhost:8080/docs
```

This provides a Swagger UI where you can test all endpoints interactively.

### Test Upload Documents

Create a test PDF or use an existing one:

```bash
curl -X POST \
  -F "files=@/path/to/document.pdf" \
  -F "user_id=test_user" \
  http://localhost:8080/ingest
```

Save the `batch_job_id` from the response.

### Check Upload Status

```bash
curl "http://localhost:8080/status?batch_job_id=YOUR_BATCH_JOB_ID"
```

Wait for `status` to be `"completed"`.

### Query the System

Once documents are processed:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is in the document?",
    "user_id": "test_user",
    "use_context": true
  }' \
  http://localhost:8080/query
```

---

## Troubleshooting

### Issue: "Connection refused" when trying to upload

**Solution:**
1. Verify PDF Parser is running on port 8000:
   ```bash
   curl http://localhost:8000/health
   ```
2. Check `.env` file for correct `PDF_PARSER_HOST` and `PDF_PARSER_PORT`

### Issue: "GROQ_API_KEY not set"

**Solution:**
1. Add to `.env`:
   ```
   GROQ_API_KEY=your-actual-api-key
   ```
2. Restart the server

### Issue: Embeddings taking very long to generate

**Normal behavior!** First run downloads the MiniLM model (~130MB). Subsequent requests are fast.

To pre-download:
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded successfully")
```

### Issue: "Port 8080 already in use"

**Solution:**
Either stop the other service using port 8080, or run on a different port:

```bash
uvicorn main:app --port 8081 --host 0.0.0.0
```

Then access at `http://localhost:8081`

### Issue: Database is locked

**Solution:**
SQLite has limitations with concurrent writes. For production:

1. Stop all running instances
2. Delete the database: `rm rag_backend.db`
3. Update `.env` to use PostgreSQL:
   ```
   DATABASE_URL=postgresql://user:password@localhost/rag_backend
   ```
4. Restart the server

### Issue: Ingestion fails with "Parsing failed"

**Solution:**
1. Check PDF Parser is running:
   ```bash
   curl http://localhost:8000/health
   ```
2. Check logs for detailed error message
3. Ensure PDF file is valid and not corrupted

### Issue: Query returns "No context found"

**Normal behavior** if:
1. Documents haven't finished processing yet
2. The query doesn't match document content

Check ingestion status first, then try a different query.

### Issue: LLM returns generic response instead of context-based

**Check:**
1. Is `used_rag` flag `true` in the response?
2. Is `context` field populated?
3. Try a more specific query matching document content

---

## Environment Variables Reference

### Application
| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | RAG Backend | Application name |
| `APP_VERSION` | 1.0.0 | Application version |
| `DEBUG` | False | Enable debug mode (don't use in production) |
| `DATABASE_URL` | sqlite:///./rag_backend.db | Database connection string |

### Microservices
| Variable | Default | Description |
|----------|---------|-------------|
| `PDF_PARSER_HOST` | localhost | PDF Parser service host |
| `PDF_PARSER_PORT` | 8000 | PDF Parser service port |
| `PDF_PARSER_TIMEOUT` | 300 | PDF Parser timeout (seconds) |
| `DATAPREP_HOST` | localhost | DataPrep service host |
| `DATAPREP_PORT` | 5000 | DataPrep service port |
| `DATAPREP_TIMEOUT` | 300 | DataPrep timeout (seconds) |
| `RETRIEVER_HOST` | localhost | Retriever service host |
| `RETRIEVER_PORT` | 7000 | Retriever service port |
| `RETRIEVER_TIMEOUT` | 30 | Retriever timeout (seconds) |

### Vector Database
| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT_HOST` | localhost | Qdrant database host |
| `QDRANT_PORT` | 6333 | Qdrant database port |
| `QDRANT_COLLECTION_NAME` | rag-qdrant | Collection name in Qdrant |

### LLM & Embeddings
| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | (required) | Groq API authentication key |
| `GROQ_MODEL` | llama-2-70b-chat | Groq model to use |
| `LLM_TIMEOUT` | 30 | LLM request timeout (seconds) |
| `EMBEDDING_MODEL` | all-MiniLM-L6-v2 | SentenceTransformer model |

---

## File Structure

```
rag-backend/
├── main.py                    # FastAPI application entry point
├── config.py                  # Configuration management
├── setup.py                   # Setup utilities
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker image definition
├── docker-compose.yml         # Docker Compose orchestration
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
├── README.md                 # Main documentation
├── GETTING_STARTED.md        # This file
├── USAGE_EXAMPLES.md         # API usage examples
├── DOCKER.md                 # Docker deployment guide
└── app/
    ├── database.py            # Database session management
    ├── models.py              # SQLAlchemy ORM models
    ├── schemas.py             # Pydantic request/response models
    ├── background_tasks.py    # Async task processing
    ├── services/              # Business logic
    │   ├── llm_service.py              # Groq LLM integration
    │   ├── embedding_service.py        # Embedding generation
    │   ├── pdf_parser_service.py       # PDF Parser API client
    │   ├── dataprep_service.py         # DataPrep API client
    │   └── retriever_service.py        # Vector retrieval client
    └── routes/                # API endpoints
        ├── ingest.py          # Document ingestion endpoint
        ├── status.py          # Status checking endpoint
        └── query.py           # RAG query endpoint
```

---

## Next Steps

1. **Test the API**: Use the examples in `USAGE_EXAMPLES.md`
2. **Integrate with your application**: Use curl, Python, or any HTTP client
3. **Monitor performance**: Check logs and database
4. **Deploy to production**: Use Docker Compose or Kubernetes
5. **Scale**: Add load balancing and multiple workers as needed

---

## Support & Documentation

- **API Documentation**: `http://localhost:8080/docs` (Swagger UI)
- **Examples**: See `USAGE_EXAMPLES.md`
- **Deployment**: See `DOCKER.md` for containerization
- **Code Documentation**: Inline comments throughout source code

---

## Quick Command Reference

```bash
# Setup
python setup.py setup

# Run (development)
python setup.py run --debug

# Run (production)
python setup.py run

# Docker
docker-compose up -d
docker-compose down

# Test API
curl http://localhost:8080/health

# View logs
docker-compose logs -f rag-backend

# Database reset
rm rag_backend.db
```

---

## Common Workflows

### Workflow 1: Upload & Query Document

```bash
# 1. Upload
RESPONSE=$(curl -s -X POST -F "files=@doc.pdf" http://localhost:8080/ingest)
BATCH_ID=$(echo $RESPONSE | grep -o '"batch_job_id":"[^"]*' | cut -d'"' -f4)

# 2. Wait for processing
while true; do
  STATUS=$(curl -s "http://localhost:8080/status?batch_job_id=$BATCH_ID" | grep -o '"status":"[^"]*' | cut -d'"' -f4)
  if [ "$STATUS" = "completed" ]; then
    echo "✓ Processing complete"
    break
  fi
  echo "⏳ Status: $STATUS"
  sleep 2
done

# 3. Query
curl -X POST -H "Content-Type: application/json" \
  -d '{"query":"What is in the document?"}' \
  http://localhost:8080/query
```

### Workflow 2: Batch Processing Multiple Documents

```bash
# Upload multiple files
curl -X POST \
  -F "files=@doc1.pdf" \
  -F "files=@doc2.pdf" \
  -F "files=@doc3.pdf" \
  -F "user_id=batch_user" \
  http://localhost:8080/ingest
```

---

## Final Checklist

Before going to production:

- [ ] All microservices running and tested
- [ ] `.env` configured with real API keys
- [ ] GROQ_API_KEY verified and valid
- [ ] Database backup strategy in place
- [ ] Logging configured
- [ ] Resource limits set
- [ ] Load testing completed
- [ ] Error handling verified
- [ ] Documentation updated
- [ ] Team trained on operations

---

Good luck with your RAG system! 🚀
