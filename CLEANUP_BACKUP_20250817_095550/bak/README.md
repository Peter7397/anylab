# OneLab Backend

A comprehensive Django-based backend for the OneLab IT operations and troubleshooting platform.

## 🚀 Features

### Core Modules
- **User Management**: Custom user model with roles and permissions
- **System Monitoring**: Real-time system metrics, logs, and alerts
- **Maintenance Management**: Task scheduling, SQL health monitoring, performance baselines
- **AI Assistant**: Knowledge base, chat sessions, document processing

### Technology Stack
- **Framework**: Django 5.2.4 + Django REST Framework
- **Database**: PostgreSQL (with SQLite for development)
- **Authentication**: JWT (JSON Web Tokens)
- **Background Tasks**: Celery + Redis
- **AI Models**: Qwen 2.5-7B-Instruct, BAAI/bge-m3
- **File Storage**: Local file system with media handling

## 📁 Project Structure

```
backend/
├── onelab/                 # Main Django project
│   ├── settings.py        # Django settings
│   ├── urls.py           # Main URL configuration
│   ├── celery.py         # Celery configuration
│   └── admin.py          # Admin interface
├── users/                 # User management app
│   ├── models.py         # User, Role, UserRole models
│   ├── views.py          # API views
│   └── urls.py           # URL routing
├── monitoring/            # System monitoring app
│   ├── models.py         # System, metrics, logs, alerts
│   ├── views.py          # API views
│   └── urls.py           # URL routing
├── maintenance/           # Maintenance management app
│   ├── models.py         # Tasks, schedules, SQL health
│   ├── views.py          # API views
│   └── urls.py           # URL routing
├── ai_assistant/         # AI assistant app
│   ├── models.py         # Knowledge base, chat, AI models
│   ├── views.py          # API views
│   └── urls.py           # URL routing
├── requirements.txt      # Python dependencies
├── env_example.txt      # Environment variables template
└── README.md           # This file
```

## 🗄️ Database Models

### Users App
- **User**: Extended user model with employee info
- **Role**: User roles and permissions
- **UserRole**: Many-to-many relationship

### Monitoring App
- **System**: PC/system information
- **SystemMetrics**: Performance metrics (CPU, memory, disk, network)
- **LogEntry**: System and application logs
- **Alert**: System alerts and notifications
- **NetworkConnection**: Network connection tracking
- **DatabaseMetrics**: Database performance metrics

### Maintenance App
- **MaintenanceTask**: Scheduled maintenance tasks
- **MaintenanceSchedule**: Recurring maintenance schedules
- **SQLQuery**: Database query monitoring
- **DatabaseBackup**: Backup tracking
- **PerformanceBaseline**: System performance baselines

### AI Assistant App
- **KnowledgeDocument**: Knowledge base documents
- **DocumentChunk**: Document chunks for vector search
- **ChatSession**: AI chat sessions
- **ChatMessage**: Individual chat messages
- **AIModel**: AI model configurations
- **AIConversationTemplate**: Predefined conversation templates
- **AIUsageLog**: AI usage analytics

## 🛠️ Setup Instructions

### 1. Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration
```bash
# Copy environment template
cp env_example.txt .env

# Edit .env file with your settings
# Key variables to configure:
# - SECRET_KEY
# - DATABASE settings
# - REDIS settings
# - AI model paths
```

### 3. Database Setup
```bash
# Create database migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 4. Start Development Server
```bash
# Start Django development server
python manage.py runserver

# Start Celery worker (in separate terminal)
celery -A onelab worker --loglevel=info

# Start Celery beat (in separate terminal)
celery -A onelab beat --loglevel=info
```

## 🔧 Configuration

### Environment Variables
- `DEBUG`: Enable/disable debug mode
- `SECRET_KEY`: Django secret key
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`: Database settings
- `REDIS_URL`: Redis connection URL
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`: Celery settings
- `AI_MODEL_PATH`, `EMBEDDING_MODEL_PATH`: AI model paths
- `MEDIA_URL`, `MEDIA_ROOT`: File storage settings
- `CORS_ALLOWED_ORIGINS`: CORS settings for frontend
- `JWT_SECRET_KEY`, `JWT_ACCESS_TOKEN_LIFETIME`, `JWT_REFRESH_TOKEN_LIFETIME`: JWT settings

### Database Configuration
- **Development**: SQLite (default)
- **Production**: PostgreSQL with pgvector extension

### Celery Configuration
- **Broker**: Redis
- **Result Backend**: Redis
- **Task Queues**: ai_queue, monitoring_queue, maintenance_queue, default
- **Periodic Tasks**: System monitoring, metrics collection, maintenance checks

## 🔌 API Endpoints

### Authentication
- `POST /api/token/`: Obtain JWT token
- `POST /api/token/refresh/`: Refresh JWT token
- `POST /api/token/verify/`: Verify JWT token

### Users
- `GET /api/users/`: User list (placeholder)

### Monitoring
- `GET /api/monitoring/`: System list (placeholder)

### Maintenance
- `GET /api/maintenance/`: Task list (placeholder)

### AI Assistant
- `GET /api/ai/`: Chat list (placeholder)

## 🧪 Testing

```bash
# Run tests
python manage.py test

# Run specific app tests
python manage.py test users
python manage.py test monitoring
python manage.py test maintenance
python manage.py test ai_assistant
```

## 📊 Admin Interface

Access the Django admin interface at `http://localhost:8000/admin/` to manage:
- Users and roles
- Systems and metrics
- Maintenance tasks
- AI models and knowledge base
- Logs and alerts

## 🔄 Background Tasks

### Periodic Tasks
- **System Monitoring**: Every 60 seconds
- **Metrics Collection**: Every 5 minutes
- **Maintenance Schedule Check**: Every hour
- **Document Processing**: Every 30 seconds

### Task Queues
- **ai_queue**: AI processing tasks
- **monitoring_queue**: System monitoring tasks
- **maintenance_queue**: Maintenance tasks
- **default**: General tasks

## 🚀 Deployment

### Production Checklist
1. Set `DEBUG=False`
2. Configure PostgreSQL database
3. Set up Redis for Celery
4. Configure static file serving
5. Set up environment variables
6. Install AI models
7. Configure logging
8. Set up monitoring

### Docker Support
```bash
# Build and run with Docker Compose
docker-compose up --build
```

## 📈 Monitoring

### Logging
- File logging: `logs/onelab.log`
- Console logging for development
- Structured logging with timestamps

### Health Checks
- Database connectivity
- Redis connectivity
- Celery worker status
- AI model availability

## 🔮 Future Enhancements

- **Real-time Updates**: WebSocket integration
- **Advanced AI**: Fine-tuned models for specific domains
- **Analytics Dashboard**: Usage analytics and insights
- **API Documentation**: Auto-generated API docs
- **Testing Coverage**: Comprehensive test suite
- **Performance Optimization**: Caching and query optimization

## 📝 License

This project is part of the OneLab platform for IT operations and troubleshooting.

## 🤝 Contributing

1. Follow Django coding standards
2. Write tests for new features
3. Update documentation
4. Use meaningful commit messages
5. Test thoroughly before submitting

---

**OneLab Backend** - Empowering IT operations with AI-driven insights and comprehensive monitoring. 