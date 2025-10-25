# Docker Deployment Guide

This guide explains how to deploy your application using Docker.

## Prerequisites

- Docker and Docker Compose installed on your server
- Git to clone the repository

## Deployment Steps

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd <your-project-directory>
```

### 2. Configure Environment Variables

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Edit the `.env` file and set appropriate values:
- Set `DJANGO_SECRET_KEY` to a secure random string
- Set `DJANGO_DEBUG=False` for production
- Update `DJANGO_ALLOWED_HOSTS` with your domain
- Configure database credentials if needed
- Adjust other settings as necessary

### 3. Build and Start the Containers

Build and start all containers in detached mode:

```bash
docker-compose up -d
```

This will:
1. Build the Django application image
2. Start the PostgreSQL database
3. Start the Ollama service
4. Start the Nginx web server
5. Run migrations and collect static files automatically

### 4. Verify the Deployment

Check if all containers are running:

```bash
docker-compose ps
```

Access your application at:
- http://your-domain.com (or http://server-ip if testing locally)

### 5. Maintenance Tasks

#### View Logs

```bash
# View logs from all containers
docker-compose logs

# View logs from a specific container
docker-compose logs web
```

#### Execute Django Management Commands

```bash
# Create a superuser
docker-compose exec web python manage.py createsuperuser

# Run other Django commands
docker-compose exec web python manage.py <command>
```

#### Database Backup

```bash
docker-compose exec db pg_dump -U postgres mydb > backup_$(date +%Y-%m-%d_%H-%M-%S).sql
```

#### Update the Application

```bash
# Pull latest changes
git pull

# Rebuild and restart containers
docker-compose down
docker-compose up -d --build
```

## Production Considerations

1. **SSL/TLS**: For HTTPS, you should either:
   - Configure Nginx with SSL certificates
   - Use a reverse proxy like Traefik or Caddy
   - Put Cloudflare or another CDN in front

2. **Backups**: Set up regular database backups

3. **Monitoring**: Consider adding monitoring with Prometheus/Grafana

4. **Scaling**: For higher traffic, consider:
   - Increasing Gunicorn workers
   - Using a managed database service
   - Implementing load balancing