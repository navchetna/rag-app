# Docker Build and Deployment Guide

## Building the Docker Image

```bash
docker build -t rag-backend:latest .
```

## Running with Docker Compose

The `docker-compose.yml` includes both the RAG Backend and Qdrant vector database.

### Prerequisites
1. Ensure other microservices (PDF Parser, DataPrep, Retriever) are running
2. Create a `.env` file with your configuration:

```bash
cp .env.example .env
# Edit .env with your values
```

### Start Services

```bash
docker-compose up -d
```

This will:
- Build the RAG Backend image
- Start the RAG Backend on port 8080
- Start Qdrant on port 6333
- Create a persistent database volume

### View Logs

```bash
docker-compose logs -f rag-backend
docker-compose logs -f qdrant
```

### Stop Services

```bash
docker-compose down
```

### Stop and Remove Volumes

```bash
docker-compose down -v
```

## Running Individual Container

```bash
docker run -d \
  --name rag-backend \
  -p 8080:8080 \
  -e GROQ_API_KEY=your-key-here \
  -e PDF_PARSER_HOST=pdf-parser-host \
  -e DATAPREP_HOST=dataprep-host \
  -e RETRIEVER_HOST=retriever-host \
  -e QDRANT_HOST=qdrant-host \
  -v rag-backend-db:/app \
  rag-backend:latest
```

## Network Configuration

The `docker-compose.yml` creates a custom network `rag-network` that allows:
- RAG Backend to communicate with Qdrant
- Easy service-to-service communication using service names as hostnames

If PDF Parser, DataPrep, and Retriever services should also be in the network, update their configuration or add them to the compose file.

## Production Considerations

1. **Use Named Volumes**: Already configured in docker-compose.yml
2. **Set Resources Limits**: Add to docker-compose.yml:
   ```yaml
   services:
     rag-backend:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 4G
   ```

3. **Enable Restart Policy**: Already set to `unless-stopped`

4. **Use Environment Variables**: Pass via `.env` file

5. **Logging**:
   ```yaml
   logging:
     driver: "json-file"
     options:
       max-size: "10m"
       max-file: "3"
   ```

## Troubleshooting

### Container fails to start
```bash
docker-compose logs rag-backend
```

### Qdrant connection issues
```bash
# Check if Qdrant is running
docker-compose ps

# Test Qdrant connectivity
curl http://localhost:6333/health
```

### Database issues
```bash
# Remove database volume and restart
docker-compose down -v
docker-compose up -d
```

## Scaling

For production with multiple instances:
1. Use load balancer (nginx, HAProxy)
2. Share database volume or use remote PostgreSQL
3. Configure Redis for shared cache (optional)
4. Use Docker Swarm or Kubernetes for orchestration
