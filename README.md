# OnLab0812 - Comprehensive Laboratory Management System

## Overview

OnLab0812 is a modern, full-stack laboratory management system that combines AI-powered document processing, system monitoring, and comprehensive laboratory operations management. Built with Django, React, and Docker, it provides a complete solution for laboratory environments.

## 🚀 Features

### AI Assistant & Document Management
- **Advanced RAG (Retrieval-Augmented Generation)** with multiple search strategies
- **PDF Document Processing** with intelligent chunking and embedding
- **Hybrid Search** combining vector and keyword-based retrieval
- **Document Viewer** with real-time annotation capabilities
- **Knowledge Library** for centralized document management

### System Monitoring
- **Real-time System Metrics** monitoring (CPU, Memory, Disk, Network)
- **Application Performance Monitoring** with detailed analytics
- **Database Health Monitoring** with PostgreSQL integration
- **Alert Management** with customizable notification systems
- **Log Analysis** with advanced filtering and search

### Laboratory Management
- **User Management** with role-based access control
- **Maintenance Scheduling** with calendar integration
- **Equipment Tracking** and maintenance history
- **Inventory Management** for laboratory supplies
- **Reporting & Analytics** with customizable dashboards

### Technical Features
- **Docker-based Deployment** for consistent environments
- **PostgreSQL with pgvector** for efficient vector storage
- **React Frontend** with modern UI/UX design
- **RESTful API** with comprehensive documentation
- **Real-time Updates** using WebSocket connections

## 🏗️ Architecture

```
OnLab0812/
├── backend/                 # Django Backend
│   ├── ai_assistant/       # AI & RAG Services
│   ├── monitoring/         # System Monitoring
│   ├── maintenance/        # Maintenance Management
│   ├── users/             # User Management
│   └── onlab/             # Main Django Project
├── frontend/              # React Frontend
│   ├── src/
│   │   ├── components/    # React Components
│   │   ├── services/      # API Services
│   │   └── types/         # TypeScript Types
│   └── public/           # Static Assets
├── appmon/               # Application Monitoring Service
├── sysmon/               # System Monitoring Service
└── docker-compose.yml    # Docker Configuration
```

## 🛠️ Technology Stack

### Backend
- **Django 4.2+** - Web framework
- **PostgreSQL** - Primary database
- **pgvector** - Vector database extension
- **Celery** - Task queue
- **Redis** - Caching and message broker

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **React Router** - Navigation
- **Axios** - HTTP client

### AI & ML
- **Sentence Transformers** - Text embeddings
- **Ollama** - Local LLM integration
- **RAG Pipeline** - Document retrieval and generation

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Nginx** - Reverse proxy
- **SSL/TLS** - Secure communication

## 📋 Prerequisites

- Docker and Docker Compose
- Git
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/OnLab0812.git
cd OnLab0812
```

### 2. Environment Setup
```bash
# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit configuration files as needed
```

### 3. Start with Docker
```bash
# Start all services
docker-compose up -d

# Or use the hybrid startup script
./start-hybrid.sh
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin

## 🔧 Development Setup

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend Development
```bash
cd frontend
npm install
npm start
```

## 📚 Documentation

- [API Documentation](backend/API_DOCUMENTATION.md)
- [Docker Setup Guide](DOCKER_SETUP.md)
- [RAG System Guide](RAG_SYSTEM_BACKUP_README.md)
- [Quick Start Guide](QUICK_START_GUIDE.md)

## 🔐 Security Features

- **JWT Authentication** with refresh tokens
- **Role-based Access Control** (RBAC)
- **HTTPS/SSL** encryption
- **Input Validation** and sanitization
- **SQL Injection** protection
- **XSS Protection** headers

## 📊 Monitoring & Analytics

- **Real-time System Metrics**
- **Application Performance Monitoring**
- **Database Query Analytics**
- **User Activity Tracking**
- **Error Logging** and alerting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the documentation in the `/docs` folder
- Review the troubleshooting guides

## 🔄 Version History

- **v1.0.0** - Initial release with core features
- **v1.1.0** - Enhanced RAG system and monitoring
- **v1.2.0** - UI improvements and performance optimizations

---

**OnLab0812** - Empowering laboratories with intelligent management solutions.
