# OneLab Backend - Docker Deployment

This document describes how to deploy the OneLab backend using Docker and Docker Compose.

## Architecture

The OneLab backend consists of the following services:

- **Django Web Application**: Main API server
- **PostgreSQL**: Primary database
- **Redis**: Caching and message broker for Celery
- **Celery Worker**: Background task processing
- **Celery Beat**: Task scheduler
- **Celery Flower**: Task monitoring and management

## Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)
- At least 4GB RAM available for containers

## Quick Start

1. **Clone and navigate to the backend directory:**
   ```bash
   cd OneLab0803/backend
   ```

2. **Create environment file:**
   ```bash
   cp env.docker .env
   ```

3. **Edit the .env file with your configuration:**
   ```bash
   # Update these values for your environment
   SECRET_KEY=your-super-secret-key-change-this-in-production
   DB_PASSWORD=your-secure-password
   ```

4. **Build and start all services:**
   ```bash
   docker-compose up --build
   ```

5. **Create a superuser (in a new terminal):**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

6. **Access the application:**
   - API: http://localhost:8000
   - Admin: http://localhost:8000/admin
   - Flower (Celery monitoring): http://localhost:5555

## Services

### Web Application (Django)
- **Port**: 8000
- **Health Check**: http://localhost:8000/api/health/
- **Description**: Main API server with REST endpoints

### Database (PostgreSQL)
- **Port**: 5432
- **Database**: onelab_db
- **User**: postgres
- **Description**: Primary database for the application

### Redis
- **Port**: 6379
- **Description**: Caching layer and message broker for Celery

### Celery Worker
- **Description**: Processes background tasks
- **Concurrency**: 4 workers
- **Logs**: Available in container logs

### Celery Beat
- **Description**: Scheduler for periodic tasks
- **Tasks**: Health checks, log cleanup, database backups

### Celery Flower
- **Port**: 5555
- **Description**: Web-based monitoring for Celery tasks

## Environment Variables

### Required Variables
- `SECRET_KEY`: Django secret key
- `DB_PASSWORD`: PostgreSQL password

### Optional Variables
- `DEBUG`: Set to False for production
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `CORS_ALLOWED_ORIGINS`: Comma-separated list of CORS origins

## Development

### Running in Development Mode
```bash
# Set DEBUG=True in .env file
DEBUG=True

# Start services
docker-compose up
```

### Running Tests
```bash
docker-compose exec web python manage.py test
```

### Database Migrations
```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

### Collecting Static Files
```bash
docker-compose exec web python manage.py collectstatic
```

## Production Deployment

### Security Considerations
1. Change all default passwords
2. Use strong SECRET_KEY
3. Set DEBUG=False
4. Configure proper ALLOWED_HOSTS
5. Use HTTPS in production
6. Set up proper logging

### Scaling
```bash
# Scale web workers
docker-compose up --scale web=3

# Scale celery workers
docker-compose up --scale celery=2
```

### Backup and Restore

#### Database Backup
```bash
docker-compose exec db pg_dump -U postgres onelab_db > backup.sql
```

#### Database Restore
```bash
docker-compose exec -T db psql -U postgres onelab_db < backup.sql
```

## Monitoring

### Health Checks
- Web: http://localhost:8000/api/health/
- Database: Automatic health checks
- Redis: Automatic health checks

### Logs
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs web
docker-compose logs celery
docker-compose logs db
```

### Celery Monitoring
- Access Flower at http://localhost:5555
- Monitor task queues and workers
- View task history and statistics

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change ports in docker-compose.yml
2. **Memory issues**: Increase Docker memory allocation
3. **Database connection**: Check DB_HOST and credentials
4. **Redis connection**: Verify REDIS_URL format

### Debugging
```bash
# Access container shell
docker-compose exec web bash

# Check Django settings
docker-compose exec web python manage.py check

# View database
docker-compose exec db psql -U postgres onelab_db
```

## API Endpoints

### Authentication
- `POST /api/token/`: Obtain JWT token
- `POST /api/token/refresh/`: Refresh JWT token
- `POST /api/token/verify/`: Verify JWT token

### Health Check
- `GET /api/health/`: Application health status

### Users
- `GET /api/users/`: List users
- `POST /api/users/`: Create user
- `GET /api/users/{id}/`: Get user details

### Monitoring
- `GET /api/monitoring/`: System monitoring data

### Maintenance
- `GET /api/maintenance/`: Maintenance tasks

### AI Assistant
- `GET /api/ai/`: AI assistant endpoints

## File Structure

```
backend/
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Multi-service orchestration
├── requirements.txt        # Python dependencies
├── manage.py              # Django management script
├── .env                   # Environment variables
├── .dockerignore          # Docker build exclusions
├── init.sql              # Database initialization
├── onelab/               # Django project settings
├── users/                # User management app
├── monitoring/           # System monitoring app
├── maintenance/          # Maintenance management app
└── ai_assistant/        # AI assistant app
```

## Performance Optimization

1. **Database**: Use connection pooling
2. **Redis**: Configure proper memory limits
3. **Celery**: Adjust worker concurrency
4. **Static files**: Use CDN in production
5. **Caching**: Implement Redis caching strategies

## Security Best Practices

1. **Secrets**: Use Docker secrets or external secret management
2. **Network**: Use custom Docker networks
3. **Updates**: Regularly update base images
4. **Scans**: Run security scans on images
5. **Access**: Limit container access to host resources 