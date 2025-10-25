# Docker Setup Guide

This guide explains how to set up and run the Django PDF Vector Search project with Ollama and Qwen models using Docker.

## Prerequisites

- Docker and Docker Compose installed
- At least 8GB of RAM (16GB recommended for Qwen models)
- At least 20GB of free disk space

## Quick Start

1. **Clone and navigate to the project directory**
   ```bash
   cd django-pgvector-pdf
   ```

2. **Create the Ollama volume**
   ```bash
   docker volume create ollama_data
   ```

3. **Start all services**
   ```bash
   docker-compose up --build
   ```

## Services Overview

### 1. Database (PostgreSQL with pgvector)
- **Image**: `pgvector/pgvector:pg16`
- **Port**: 5432 (exposed as 5432)
- **Purpose**: Stores document embeddings and metadata

### 2. Django Web Application
- **Image**: Custom built from `Dockerfile`
- **Port**: 8000 (exposed as 8000)
- **Purpose**: Main web application for PDF processing and search
- **Features**:
  - PDF text extraction
  - Text embedding using all-MiniLM-L6-v2
  - Vector similarity search
  - Integration with Ollama for AI responses

### 3. Ollama Service
- **Image**: `ollama/ollama:latest`
- **Port**: 11434 (exposed as 11435)
- **Purpose**: Runs Qwen language models for AI responses
- **Models**: 
  - qwen2.5:7b (7 billion parameters)
  - qwen2.5:14b (14 billion parameters)

### 4. Nginx (Production)
- **Image**: `nginx:1.25-alpine`
- **Port**: 80 (exposed as 80)
- **Purpose**: Reverse proxy for production deployment

## Model Setup

### Sentence Transformer Model
The `all-MiniLM-L6-v2` model is mounted from the local directory:
- **Local path**: `./all-MiniLM-L6-v2_local_copy`
- **Container path**: `/model/all-MiniLM-L6-v2`
- **Purpose**: Generates embeddings for document text

### Qwen Models
Qwen models are automatically downloaded when the Ollama container starts:
- **qwen2.5:7b**: ~4GB download
- **qwen2.5:14b**: ~8GB download
- **Download time**: 10-30 minutes depending on internet speed

## Environment Variables

Key environment variables in `.env`:

```bash
# Database
POSTGRES_DB=mydb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Web server
WEB_PORT=8000

# Ollama
OLLAMA_PORT=11435

# Nginx
NGINX_PORT=80
```

## Testing the Setup

### 1. Test Ollama Connection
```bash
python test_ollama.py
```

### 2. Test Django Application
Visit `http://localhost:8000` in your browser

### 3. Test Nginx (Production)
Visit `http://localhost:80` in your browser

## Troubleshooting

### Common Issues

1. **"l" variable warning**
   - This is fixed by adding `l=` to the `.env` file

2. **Model not found error**
   - Ensure `all-MiniLM-L6-v2_local_copy` directory exists
   - Check volume mapping in `docker-compose.yml`

3. **Ollama connection issues**
   - Verify Ollama container is running: `docker-compose ps`
   - Check logs: `docker-compose logs ollama`
   - Ensure port 11435 is not in use

4. **Out of memory errors**
   - Reduce model size (use only qwen2.5:7b)
   - Increase Docker memory limit
   - Close other applications

### Useful Commands

```bash
# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f ollama

# Restart specific service
docker-compose restart ollama

# Stop all services
docker-compose down

# Remove all containers and volumes
docker-compose down -v

# Rebuild and start
docker-compose up --build
```

## Performance Optimization

1. **For Development**:
   - Use only qwen2.5:7b model
   - Reduce Docker memory usage

2. **For Production**:
   - Use both Qwen models for better responses
   - Increase Docker memory limit to 16GB+
   - Use GPU acceleration if available

## Security Notes

- Default database credentials are for development only
- Change passwords in production
- Use HTTPS in production
- Restrict network access as needed

## Next Steps

1. Upload PDF documents through the web interface
2. Test vector similarity search
3. Integrate with Qwen models for AI responses
4. Customize the application for your specific needs 