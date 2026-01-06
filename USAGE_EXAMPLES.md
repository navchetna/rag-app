# RAG Backend - Usage Examples

This document provides practical examples of how to use the RAG Backend API.

## Prerequisites

- Server running on `http://localhost:8080`
- Groq API key configured
- All microservices running
- Qdrant vector database running

## 1. Health Check

Verify the server is running:

```bash
curl http://localhost:8080/health
```

Response:
```json
{
  "status": "healthy",
  "message": "RAG Backend is running",
  "version": "1.0.0"
}
```

## 2. Document Ingestion

### Upload a single PDF

```bash
curl -X POST \
  -F "files=@document.pdf" \
  -F "user_id=user123" \
  http://localhost:8080/ingest
```

Response:
```json
{
  "batch_job_id": "ALI-1767681208.8422334",
  "batch_job_file_ids": ["ALI-1767681208.8422334:document.pdf"],
  "message": "Successfully submitted 1 file(s) for processing",
  "status": "queued"
}
```

### Upload multiple PDFs

```bash
curl -X POST \
  -F "files=@document1.pdf" \
  -F "files=@document2.pdf" \
  -F "files=@document3.pdf" \
  -F "user_id=user123" \
  http://localhost:8080/ingest
```

Response:
```json
{
  "batch_job_id": "ALI-1767681208.8422334",
  "batch_job_file_ids": [
    "ALI-1767681208.8422334:document1.pdf",
    "ALI-1767681208.8422334:document2.pdf",
    "ALI-1767681208.8422334:document3.pdf"
  ],
  "message": "Successfully submitted 3 file(s) for processing",
  "status": "queued"
}
```

## 3. Check Ingestion Status

### Check by batch_job_id

```bash
curl "http://localhost:8080/status?batch_job_id=ALI-1767681208.8422334"
```

Response (while processing):
```json
{
  "batch_job_id": "ALI-1767681208.8422334",
  "user_id": "user123",
  "status": "processing",
  "total_files": 3,
  "files": [
    {
      "batch_job_file_id": "ALI-1767681208.8422334:document1.pdf",
      "filename": "document1.pdf",
      "status": "parsing",
      "parsing_status": "in_progress",
      "dataprep_status": "pending",
      "error_message": null,
      "created_at": "2026-01-06T10:30:00",
      "updated_at": "2026-01-06T10:31:00"
    },
    {
      "batch_job_file_id": "ALI-1767681208.8422334:document2.pdf",
      "filename": "document2.pdf",
      "status": "completed",
      "parsing_status": "completed",
      "dataprep_status": "completed",
      "error_message": null,
      "created_at": "2026-01-06T10:30:00",
      "updated_at": "2026-01-06T10:32:30"
    },
    {
      "batch_job_file_id": "ALI-1767681208.8422334:document3.pdf",
      "filename": "document3.pdf",
      "status": "queued",
      "parsing_status": "pending",
      "dataprep_status": "pending",
      "error_message": null,
      "created_at": "2026-01-06T10:30:00",
      "updated_at": "2026-01-06T10:30:00"
    }
  ],
  "created_at": "2026-01-06T10:30:00",
  "updated_at": "2026-01-06T10:32:30",
  "error_message": null
}
```

Response (after completion):
```json
{
  "batch_job_id": "ALI-1767681208.8422334",
  "user_id": "user123",
  "status": "completed",
  "total_files": 3,
  "files": [
    {
      "batch_job_file_id": "ALI-1767681208.8422334:document1.pdf",
      "filename": "document1.pdf",
      "status": "completed",
      "parsing_status": "completed",
      "dataprep_status": "completed",
      "error_message": null,
      "created_at": "2026-01-06T10:30:00",
      "updated_at": "2026-01-06T10:35:00"
    },
    {
      "batch_job_file_id": "ALI-1767681208.8422334:document2.pdf",
      "filename": "document2.pdf",
      "status": "completed",
      "parsing_status": "completed",
      "dataprep_status": "completed",
      "error_message": null,
      "created_at": "2026-01-06T10:30:00",
      "updated_at": "2026-01-06T10:33:00"
    },
    {
      "batch_job_file_id": "ALI-1767681208.8422334:document3.pdf",
      "filename": "document3.pdf",
      "status": "completed",
      "parsing_status": "completed",
      "dataprep_status": "completed",
      "error_message": null,
      "created_at": "2026-01-06T10:30:00",
      "updated_at": "2026-01-06T10:34:15"
    }
  ],
  "created_at": "2026-01-06T10:30:00",
  "updated_at": "2026-01-06T10:35:00",
  "error_message": null
}
```

### Check by batch_job_file_id

```bash
curl "http://localhost:8080/status?batch_job_file_id=ALI-1767681208.8422334:document1.pdf"
```

Returns the same format as above, but filtered for the batch containing that file.

## 4. Query the RAG System

### Basic query with context

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What was the budget for 2024?",
    "user_id": "user123",
    "use_context": true
  }' \
  http://localhost:8080/query
```

Response (with context found):
```json
{
  "query": "What was the budget for 2024?",
  "response": "Based on the documents provided, the budget for 2024 was $5 million with a focus on infrastructure development and research initiatives.",
  "used_rag": true,
  "context": "[Document 1] The 2024 annual budget has been allocated as follows: $5 million for infrastructure development, $2 million for research initiatives, and $1 million for administrative costs.",
  "created_at": "2026-01-06T10:40:00"
}
```

Response (no context found, using LLM knowledge):
```json
{
  "query": "What is the capital of France?",
  "response": "The capital of France is Paris, a major cultural and historical center located in the north-central part of the country.",
  "used_rag": false,
  "context": null,
  "created_at": "2026-01-06T10:41:00"
}
```

### Query without context (knowledge only)

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain quantum computing",
    "user_id": "user123",
    "use_context": false
  }' \
  http://localhost:8080/query
```

Response:
```json
{
  "query": "Explain quantum computing",
  "response": "Quantum computing is a type of computation that uses quantum bits (qubits) instead of classical bits. Qubits can exist in superposition, meaning they can be both 0 and 1 simultaneously, which allows quantum computers to process information in fundamentally different ways than classical computers...",
  "used_rag": false,
  "context": null,
  "created_at": "2026-01-06T10:42:00"
}
```

## 5. Multi-turn Conversations

The system automatically maintains conversation context. Each query is stored with its response.

### First message

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the company annual revenue?",
    "user_id": "user123"
  }' \
  http://localhost:8080/query
```

Response:
```json
{
  "query": "What is the company annual revenue?",
  "response": "According to the financial documents, the company's annual revenue for 2024 is $150 million.",
  "used_rag": true,
  "context": "[Document 1] Annual Revenue Report: The company achieved $150 million in total revenue...",
  "created_at": "2026-01-06T10:43:00"
}
```

### Follow-up question (system includes previous context)

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What was the growth compared to last year?",
    "user_id": "user123"
  }' \
  http://localhost:8080/query
```

Response (LLM receives conversation history):
```json
{
  "query": "What was the growth compared to last year?",
  "response": "Based on the financial records, this represents a 15% increase from the previous year's revenue of $130 million.",
  "used_rag": true,
  "context": "[Document 1] Year-over-year comparison shows growth from $130M (2023) to $150M (2024)...",
  "created_at": "2026-01-06T10:44:00"
}
```

## 6. Error Handling Examples

### No files provided

```bash
curl -X POST \
  -F "user_id=user123" \
  http://localhost:8080/ingest
```

Response:
```json
{
  "detail": "No files provided"
}
```

### Invalid file type

```bash
curl -X POST \
  -F "files=@document.txt" \
  -F "user_id=user123" \
  http://localhost:8080/ingest
```

Response:
```json
{
  "detail": "File document.txt is not a PDF"
}
```

### Ingestion job not found

```bash
curl "http://localhost:8080/status?batch_job_id=INVALID_ID"
```

Response:
```json
{
  "detail": "Ingestion job INVALID_ID not found"
}
```

### Empty query

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"query": ""}' \
  http://localhost:8080/query
```

Response:
```json
{
  "detail": "Query cannot be empty"
}
```

## 7. Integration Example (Python)

```python
import requests
import json
import time

BASE_URL = "http://localhost:8080"

# 1. Upload documents
print("Uploading documents...")
with open("document.pdf", "rb") as f:
    files = {"files": f}
    data = {"user_id": "user123"}
    response = requests.post(f"{BASE_URL}/ingest", files=files, data=data)
    result = response.json()
    batch_job_id = result["batch_job_id"]
    print(f"Batch Job ID: {batch_job_id}")

# 2. Wait for processing
print("Waiting for processing...")
while True:
    response = requests.get(f"{BASE_URL}/status?batch_job_id={batch_job_id}")
    status = response.json()
    
    if status["status"] == "completed":
        print("✓ Processing complete")
        break
    elif status["status"] == "failed":
        print("✗ Processing failed")
        break
    else:
        print(f"  Status: {status['status']}")
        time.sleep(2)

# 3. Query the system
print("Querying system...")
query_data = {
    "query": "What is the main topic of the document?",
    "user_id": "user123",
    "use_context": True
}
response = requests.post(f"{BASE_URL}/query", json=query_data)
answer = response.json()
print(f"Q: {answer['query']}")
print(f"A: {answer['response']}")
print(f"RAG Used: {answer['used_rag']}")
```

## 8. Status Values Explained

### Overall Status
- `queued`: Batch submitted, waiting to be processed
- `processing`: Files are being parsed or prepared
- `completed`: All files successfully processed
- `failed`: One or more files failed

### Per-File Status
- `queued`: Waiting for processing
- `parsing`: PDF is being parsed
- `parsed`: Parsing complete, ready for dataprep
- `preparing`: Being prepared for vector database
- `completed`: Successfully ingested into vector DB
- `failed`: Processing failed

### Parsing Status
- `pending`: Not started
- `in_progress`: Currently parsing
- `completed`: Successfully parsed
- `failed`: Parsing failed

### DataPrep Status
- `pending`: Not started
- `in_progress`: Being processed
- `completed`: Successfully ingested to Qdrant
- `failed`: Ingestion failed

## 9. Best Practices

1. **Poll Status Appropriately**
   - For large files, wait longer between status checks
   - Don't poll more frequently than every 2 seconds
   - For production, consider webhooks or long-polling

2. **Handle Errors Gracefully**
   - Check HTTP status codes
   - Implement retry logic with exponential backoff
   - Log all API interactions for debugging

3. **User ID Management**
   - Use consistent user IDs for conversation tracking
   - Different user IDs have separate conversation histories
   - Use "default" for anonymous users

4. **Context Usage**
   - Set `use_context=true` for document-based questions
   - Set `use_context=false` for general knowledge questions
   - Check `used_rag` flag in response to verify context was used

5. **File Naming**
   - Use descriptive, URL-safe filenames
   - Avoid special characters in PDF filenames
   - Keep filenames under 255 characters

## 10. Monitoring & Debugging

View real-time logs:
```bash
# In another terminal while server is running
tail -f rag_backend.db  # Database activity
# Or check the console where server is running
```

Check FastAPI documentation:
```
http://localhost:8080/docs
```

This provides an interactive Swagger UI where you can test all endpoints.
