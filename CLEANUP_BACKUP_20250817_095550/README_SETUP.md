# OneLab Backend Setup Guide

## One-Time Setup (Build Images)

**Only run this ONCE** to build the Docker image with all dependencies:

```bash
./build-images.sh
```

This creates the `onelab-backend:latest` image with:
- Python 3.11
- Django and all dependencies
- pgvector pre-installed
- All AI/ML packages (sentence-transformers, torch, etc.)

## Daily Usage (No Rebuild Required)

After the one-time setup, use these commands:

### Start the System
```bash
./start-system.sh
```

### Stop the System
```bash
./stop-system.sh
```

### View Logs
```bash
docker compose logs -f
```

## Only Rebuild When Needed

Rebuild ONLY when you:
- Change code significantly
- Update dependencies in `requirements.txt`
- Need to update the base image

```bash
./rebuild-images.sh
```

## System URLs

Once started:
- **Backend API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin  
- **Flower (Celery Monitor)**: http://localhost:5555
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Troubleshooting

If services fail to start:
```bash
docker compose logs web
docker compose logs celery
```

## Architecture

- **Database**: PostgreSQL with pgvector extension
- **Cache**: Redis
- **Task Queue**: Celery
- **AI Models**: Ollama (running locally on host)
- **Embeddings**: sentence-transformers (in containers)
