# RAG Backend - Quick Reference

## 🚀 Get Started in 3 Steps

```bash
# 1. Setup
python setup.py setup

# 2. Configure (add GROQ_API_KEY to .env)
nano .env

# 3. Run
python setup.py run --debug
```

Visit: **http://localhost:8080/docs**

---

## 📝 API Quick Reference

### Health Check
```bash
curl http://localhost:8080/health
```

### Upload Document
```bash
curl -X POST \
  -F "files=@document.pdf" \
  -F "user_id=user123" \
  http://localhost:8080/ingest
```

**Response:**
```json
{
  "batch_job_id": "ALI-1234567890",
  "batch_job_file_ids": ["ALI-1234567890:document.pdf"],
  "status": "queued"
}
```

### Check Status
```bash
curl "http://localhost:8080/status?batch_job_id=ALI-1234567890"
```

### Query with RAG
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is in the document?",
    "user_id": "user123",
    "use_context": true
  }' \
  http://localhost:8080/query
```

**Response:**
```json
{
  "query": "What is in the document?",
  "response": "Based on the document...",
  "used_rag": true,
  "context": "[Document 1] Content..."
}
```

---

## 🔧 Environment Setup

### Create `.env` file
```bash
cp .env.example .env
```

### Essential Configuration
```env
GROQ_API_KEY=your-api-key-here
PDF_PARSER_HOST=localhost
PDF_PARSER_PORT=8000
DATAPREP_HOST=localhost
DATAPREP_PORT=5000
RETRIEVER_HOST=localhost
RETRIEVER_PORT=7000
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

---

## 📊 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/` | GET | API info |
| `/ingest` | POST | Upload PDFs |
| `/status` | GET | Check status |
| `/query` | POST | Ask questions |
| `/docs` | GET | API docs |

---

## 🐳 Docker Quick Start

```bash
# Start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f rag-backend

# Stop
docker-compose down
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Full documentation |
| `GETTING_STARTED.md` | Setup & troubleshooting |
| `USAGE_EXAMPLES.md` | Code examples |
| `DOCKER.md` | Docker guide |
| `PROJECT_SUMMARY.md` | Project overview |

---

## 🔍 Status Values

### Overall Status
- `queued` - Waiting to process
- `processing` - Currently processing
- `completed` - Finished successfully
- `failed` - Error occurred

### File Status
- `queued` - Waiting
- `parsing` - Parsing PDF
- `parsed` - Parse complete
- `preparing` - Preparing for DB
- `completed` - Done
- `failed` - Error

---

## 🛠️ Common Commands

```bash
# Setup
python setup.py setup

# Run (development)
python setup.py run --debug

# Run (production)
python setup.py run

# View Swagger UI
open http://localhost:8080/docs

# Direct uvicorn
uvicorn main:app --reload

# Check if running
curl http://localhost:8080/health

# Docker
docker-compose up -d
docker-compose logs -f
docker-compose down
```

---

## 📦 Project Structure

```
app/
  ├── database.py          # DB setup
  ├── models.py            # Data models
  ├── schemas.py           # Validation
  ├── background_tasks.py  # Async tasks
  ├── services/            # Microservice clients
  │   ├── llm_service.py
  │   ├── embedding_service.py
  │   ├── pdf_parser_service.py
  │   ├── dataprep_service.py
  │   └── retriever_service.py
  └── routes/              # API endpoints
      ├── ingest.py
      ├── status.py
      └── query.py
```

---

## 🔐 Environment Variables

### Required
- `GROQ_API_KEY` - LLM API key

### Microservices (defaults shown)
- `PDF_PARSER_HOST=localhost`
- `PDF_PARSER_PORT=8000`
- `DATAPREP_HOST=localhost`
- `DATAPREP_PORT=5000`
- `RETRIEVER_HOST=localhost`
- `RETRIEVER_PORT=7000`

### Database
- `QDRANT_HOST=localhost`
- `QDRANT_PORT=6333`
- `DATABASE_URL=sqlite:///./rag_backend.db`

### Application
- `APP_NAME=RAG Backend`
- `DEBUG=False`

---

## 💡 Usage Tips

1. **First time using embeddings?** First query takes 30s (model download)
2. **Polling status?** Wait 2-5 seconds between checks
3. **Multiple PDFs?** Use batch upload in one request
4. **Chat context?** Same user_id maintains conversation memory
5. **No context?** Set `use_context=false` for general knowledge

---

## 🐛 Troubleshooting

### "Connection refused"
- Check microservices are running
- Verify `.env` has correct hosts/ports

### "GROQ_API_KEY not set"
- Add to `.env`: `GROQ_API_KEY=your-key`
- Restart server

### First embedding slow
- Normal! Model downloads (~130MB)
- Subsequent requests are fast

### Port already in use
- Use different port: `uvicorn main:app --port 8081`

### Database locked
- SQLite limitation
- Use PostgreSQL for production

---

## 📈 Performance Notes

- First embedding: ~30 seconds
- Subsequent embeddings: <100ms
- Status queries: <10ms
- PDF parsing: 10-60s (depends on size)
- LLM response: 1-5 seconds

---

## 🎯 Typical Workflow

```bash
# 1. Upload
curl -F "files=@doc.pdf" http://localhost:8080/ingest
# Save batch_job_id

# 2. Wait for completion
while sleep 2; do
  curl "http://localhost:8080/status?batch_job_id=..."
done

# 3. Ask questions
curl -X POST -H "Content-Type: application/json" \
  -d '{"query":"..."}' http://localhost:8080/query

# 4. Follow-up questions (context maintained)
curl -X POST -H "Content-Type: application/json" \
  -d '{"query":"..."}' http://localhost:8080/query
```

---

## 📞 Quick Help

- **API Docs**: http://localhost:8080/docs
- **Examples**: See `USAGE_EXAMPLES.md`
- **Setup Help**: See `GETTING_STARTED.md`
- **Docker**: See `DOCKER.md`
- **Full Details**: See `README.md`

---

**Ready to start?** → `python setup.py setup`
