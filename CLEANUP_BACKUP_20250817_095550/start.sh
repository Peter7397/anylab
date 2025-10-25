#!/bin/bash

# OneLab Backend Docker Startup Script

set -e

echo "🚀 Starting OneLab Backend with Docker..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.docker .env
    echo "⚠️  Please edit .env file with your configuration before continuing"
    echo "   Key variables to update:"
    echo "   - SECRET_KEY"
    echo "   - DB_PASSWORD"
    echo "   - JWT_SECRET_KEY"
    read -p "Press Enter to continue after editing .env file..."
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install it and try again."
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo "🛑 Stopping containers..."
    docker-compose down
    echo "✅ Cleanup complete"
}

# Set trap to cleanup on script exit
trap cleanup EXIT

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if web service is healthy
echo "🏥 Checking service health..."
if docker-compose exec -T web python manage.py check > /dev/null 2>&1; then
    echo "✅ Services are healthy!"
else
    echo "⚠️  Services may still be starting up..."
fi

echo ""
echo "🎉 OneLab Backend is starting up!"
echo ""
echo "📊 Service URLs:"
echo "   - API: http://localhost:8000"
echo "   - Admin: http://localhost:8000/admin"
echo "   - Health Check: http://localhost:8000/api/health/"
echo "   - Celery Flower: http://localhost:5555"
echo ""
echo "📝 Useful commands:"
echo "   - View logs: docker-compose logs -f"
echo "   - Stop services: docker-compose down"
echo "   - Restart services: docker-compose restart"
echo "   - Create superuser: docker-compose exec web python manage.py createsuperuser"
echo ""
echo "🔍 Monitoring:"
echo "   - View all logs: docker-compose logs"
echo "   - View specific service: docker-compose logs web"
echo "   - Access container: docker-compose exec web bash"
echo ""

# Keep script running to maintain containers
echo "🔄 Services are running. Press Ctrl+C to stop..."
docker-compose logs -f 