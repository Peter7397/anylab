# RAG System Backup Documentation

## Overview
This document provides a complete backup and restoration guide for the OnLab RAG (Retrieval-Augmented Generation) system. The system includes three types of RAG implementations: Basic RAG, Advanced RAG, and Comprehensive RAG, along with document management and knowledge library features.

## System Architecture

### Backend Components
- **Django REST Framework** with JWT authentication
- **PostgreSQL** with pgvector extension for vector storage
- **Ollama** (Qwen model) for AI processing
- **Redis** for caching and session management
- **Custom RAG Services**: Basic, Advanced, and Comprehensive implementations

### Frontend Components
- **React** with TypeScript
- **Tailwind CSS** for styling
- **React Router** for navigation
- **Local Storage** for chat history persistence
- **Four AI Interfaces**: Free AI Chat, Basic RAG, Advanced RAG, Comprehensive RAG

## Current Working State (August 2024)

### ✅ Functional Features
1. **Authentication System**
   - JWT-based authentication
   - Login/logout functionality
   - Protected routes

2. **RAG Search Systems**
   - **Basic RAG**: Simple document retrieval and response generation
   - **Advanced RAG**: Enhanced search with better context understanding
   - **Comprehensive RAG**: Multi-step reasoning with detailed analysis
   - All three systems working with proper error handling

3. **Document Management**
   - Document upload (PDF, DOCX, TXT, etc.)
   - Document storage and vectorization
   - Document search and retrieval
   - Document viewer with multiple tabs

4. **Knowledge Library**
   - Document Viewer (separate page)
   - Document Manager (separate page)
   - Useful Links management (separate page)
   - Sharing & Collaboration features (separate page)

5. **UI/UX Features**
   - Unified styling across all AI interfaces
   - Expandable chat history panels
   - Performance statistics display
   - Source references and copy functionality
   - Responsive design with right-side history panels

6. **State Persistence**
   - Local storage for chat history
   - Separate history for each RAG interface
   - Persistent user preferences

### 🔧 Technical Implementations

#### Backend Services
```python
# Key files and their purposes:
backend/ai_assistant/
├── views.py              # API endpoints for all RAG types
├── urls.py               # URL routing
├── rag_service.py        # Basic RAG implementation
├── advanced_rag_service.py    # Advanced RAG implementation
├── comprehensive_rag_service.py # Comprehensive RAG implementation
└── models.py             # Document and chunk models
```

#### Frontend Components
```typescript
// Key components and their purposes:
frontend/src/components/AI/
├── ChatAssistant.tsx           # Free AI Chat interface
├── BasicRagSearch.tsx          # Basic RAG interface
├── RagSearch.tsx               # Advanced RAG interface
├── ComprehensiveRagSearch.tsx  # Comprehensive RAG interface
├── DocumentViewerPage.tsx      # Document viewer page
├── DocumentManagerPage.tsx     # Document management page
├── UsefulLinksPage.tsx         # Links management page
└── SharingCollaborationPage.tsx # Collaboration features
```

## Backup Strategy

### 1. Code Backup
```bash
# Create a complete code backup
tar -czf onlab_rag_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
  --exclude=node_modules \
  --exclude=venv \
  --exclude=.git \
  --exclude=build \
  --exclude=media \
  --exclude=staticfiles \
  .
```

### 2. Database Backup
```bash
# PostgreSQL backup
pg_dump -h localhost -U your_username -d onlab_db > onlab_db_backup_$(date +%Y%m%d_%H%M%S).sql

# Redis backup (if using persistence)
cp /var/lib/redis/dump.rdb redis_backup_$(date +%Y%m%d_%H%M%S).rdb
```

### 3. Configuration Backup
```bash
# Environment files
cp backend/.env backend_env_backup_$(date +%Y%m%d_%H%M%S)
cp frontend/.env frontend_env_backup_$(date +%Y%m%d_%H%M%S)

# Docker configurations
cp docker-compose.yml docker_compose_backup_$(date +%Y%m%d_%H%M%S).yml
```

### 4. Document Storage Backup
```bash
# Backup uploaded documents
tar -czf documents_backup_$(date +%Y%m%d_%H%M%S).tar.gz backend/media/
```

## Restoration Process

### 1. Environment Setup
```bash
# Install dependencies
cd backend && pip install -r requirements.txt
cd frontend && npm install

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Database Restoration
```bash
# Restore PostgreSQL database
psql -h localhost -U your_username -d onlab_db < onlab_db_backup_YYYYMMDD_HHMMSS.sql

# Restore Redis (if needed)
cp redis_backup_YYYYMMDD_HHMMSS.rdb /var/lib/redis/dump.rdb
```

### 3. Configuration Restoration
```bash
# Restore environment files
cp backend_env_backup_YYYYMMDD_HHMMSS backend/.env
cp frontend_env_backup_YYYYMMDD_HHMMSS frontend/.env
```

### 4. Document Restoration
```bash
# Restore uploaded documents
tar -xzf documents_backup_YYYYMMDD_HHMMSS.tar.gz -C backend/
```

### 5. Service Startup
```bash
# Start required services
docker run -d --name onlab_redis -p 6379:6379 redis:7-alpine
docker run -d --name onlab_postgres -e POSTGRES_DB=onlab_db -e POSTGRES_USER=your_user -e POSTGRES_PASSWORD=your_password -p 5432:5432 postgres:13

# Start Ollama (if not already running)
ollama serve

# Start backend
cd backend && python manage.py runserver 0.0.0.0:8000

# Start frontend
cd frontend && npm start
```

## Key Configuration Files

### Backend Environment (.env)
```env
DEBUG=True
SECRET_KEY=your_secret_key
DATABASE_URL=postgresql://user:password@localhost:5432/onlab_db
OLLAMA_API_URL=http://localhost:11434
REDIS_URL=redis://localhost:6379
```

### Frontend Environment (.env)
```env
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_BASE_URL=http://localhost:3000
```

## Known Working Configurations

### Dependencies Versions
```txt
# Backend (requirements.txt)
Django==4.2.7
djangorestframework==3.14.0
psycopg2-binary==2.9.7
redis==4.6.0
requests==2.31.0
python-dotenv==1.0.0

# Frontend (package.json)
react: ^18.2.0
react-router-dom: ^6.8.1
typescript: ^4.9.5
tailwindcss: ^3.3.0
lucide-react: ^0.263.1
```

### Database Schema
```sql
-- Key tables for RAG functionality
CREATE TABLE ai_assistant_uploadedfile (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255),
    file_path VARCHAR(500),
    uploaded_at TIMESTAMP
);

CREATE TABLE ai_assistant_documentfile (
    id SERIAL PRIMARY KEY,
    file_id INTEGER REFERENCES ai_assistant_uploadedfile(id),
    title VARCHAR(255),
    content TEXT,
    file_type VARCHAR(50)
);

CREATE TABLE ai_assistant_documentchunk (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES ai_assistant_documentfile(id),
    content TEXT,
    embedding vector(1536)
);
```

## Troubleshooting Guide

### Common Issues and Solutions

1. **401 Authentication Errors**
   - Check JWT token validity
   - Verify middleware configuration in `backend/onlab/middleware.py`

2. **Ollama Connection Issues**
   - Ensure Ollama is running: `ollama serve`
   - Check OLLAMA_API_URL in backend/.env

3. **Redis Connection Errors**
   - Start Redis container: `docker run -d --name onlab_redis -p 6379:6379 redis:7-alpine`
   - Verify Redis URL configuration

4. **Database Connection Issues**
   - Check PostgreSQL service status
   - Verify database credentials in .env file
   - Ensure pgvector extension is installed

5. **Frontend Build Issues**
   - Clear node_modules and reinstall: `rm -rf node_modules && npm install`
   - Check TypeScript compilation errors

### Performance Optimization
- Vector search uses pgvector with cosine similarity
- Redis caching for session management
- Local storage for chat history persistence
- Optimized chunk sizes for document processing

## Security Considerations

### Current Security Measures
- JWT authentication with expiration
- Protected API endpoints
- Input validation and sanitization
- Secure file upload handling

### Recommended Enhancements
- HTTPS enforcement in production
- Rate limiting for API endpoints
- File type validation
- User permission management

## Monitoring and Logging

### Log Files
```bash
# Backend logs
tail -f backend/server.log
tail -f backend/logs/django.log

# Frontend logs (browser console)
# Check browser developer tools for client-side errors
```

### Health Checks
```bash
# API health check
curl http://localhost:8000/api/health/

# Database connection
python manage.py dbshell

# Redis connection
redis-cli ping
```

## Future Enhancements

### Planned Features
- Multi-language support
- Advanced document preprocessing
- Real-time collaboration
- Advanced analytics dashboard
- Mobile application

### Technical Debt
- Code refactoring for better modularity
- Enhanced error handling
- Performance optimization
- Comprehensive testing suite

## Contact and Support

For technical support or questions about this RAG system:
- Review this documentation first
- Check the troubleshooting section
- Examine log files for error details
- Verify all service dependencies are running

---

**Last Updated**: August 2024
**System Version**: OnLab RAG v1.0
**Backup Created**: $(date +%Y-%m-%d %H:%M:%S)
