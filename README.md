# AnyLab0812 - Comprehensive Laboratory Management System

## Overview

AnyLab0812 is a practical, end-to-end knowledge platform for labs. It helps teams centralize technical documents, search them with AI (RAG), and collaborate through a streamlined, modern web UI. Built with Django + PostgreSQL (pgvector) and React, it’s designed to run locally or on-prem—no external LLM dependency required—so your content stays in your environment.

- **What it does**: Ingests PDFs and other artifacts, extracts and chunks content, builds embeddings, and enables fast, accurate retrieval/QA.
- **Why it matters**: Reduces time spent searching manuals, policies, and SOPs; improves consistency and onboarding; raises confidence in answers.
- **How it’s used**: Upload content, manage it in the Knowledge Library, then use RAG search or the AI Assistant to ask questions with traceable sources.

**Slogan: Smart Knowledge, Securely in Your Lab**

## 🚀 Features

### AI Assistant & Document Management
- **Advanced RAG (Retrieval-Augmented Generation)** with multiple search strategies
- **PDF Document Processing** with intelligent chunking and embedding
- **Hybrid Search** combining vector and keyword-based retrieval (BM25 + Vector)
- **Document Viewer** with real-time annotation capabilities
- **Knowledge Library** for centralized document management
- **Multiple Search Modes**: Comprehensive, Advanced, Enhanced, and Basic RAG
- **Real-time Document Processing** with Ollama integration
- **Smart Caching** for improved performance and response times
- **Content Filtering** with dynamic presets
- **Document Analytics** and search statistics

### Laboratory Management
- **User Management** with role-based access control
- **Reporting & Analytics** with customizable dashboards

### Technical Features
- **Docker-based Deployment** for consistent environments
- **PostgreSQL with pgvector** for efficient vector storage
- **React Frontend** with modern UI/UX design
- **RESTful API** with comprehensive documentation
- **Real-time Updates** using WebSocket connections

## 🏗️ Architecture

```
AnyLab0812/
├── backend/                 # Django Backend
│   ├── ai_assistant/       # AI & RAG Services
│   ├── users/              # User Management
│   └── anylab/             # Main Django Project
├── frontend/              # React Frontend
│   ├── src/
│   │   ├── components/    # React Components
│   │   ├── services/      # API Services
│   │   └── types/         # TypeScript Types
│   └── public/           # Static Assets
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
- **Ollama Integration** - Local LLM with Qwen 2.5-7B model
- **BGE-M3 Embeddings** - High-quality text embeddings via Ollama
- **Advanced RAG Pipeline** - Multi-mode document retrieval and generation
- **Smart Chunking** - Enhanced document processing with semantic understanding
- **Hybrid Search Engine** - Combines vector similarity with keyword matching
- **Cross-Encoder Reranking** - Advanced result ranking for better accuracy

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Cloudflare Tunnel** - Secure remote access (replaces nginx reverse proxy)
- **SSL/TLS** - Secure communication via Cloudflare

## 📋 Prerequisites

- Docker and Docker Compose
- Git
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/AnyLab0812.git
cd AnyLab0812
```

### 2. Environment Setup
```bash
# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit configuration files as needed
```

### 3. Start Services
```bash
# Recommended: hybrid startup (backend services + frontend)
./start-hybrid.sh

# Or start with Docker Compose (backend stack only)
cd backend && docker compose up -d
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001 (changed from 8000 to avoid conflict with 7English)
- **Admin Panel**: http://localhost:8001/admin

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

- [Backend API Documentation](backend/API_DOCUMENTATION.md)
- [AI Assistant API Reference](backend/ai_assistant/API_DOCUMENTATION.md)
- [Chinese Localization Guide](CHINESE_LOCALIZATION_GUIDE.md) - Comprehensive guide for implementing Chinese (Simplified) localization
- [Localization Implementation Plan](LOCALIZATION_IMPLEMENTATION_PLAN.md) - Detailed step-by-step implementation plan with tasks and timeline
- [Backup Guide](BACKUP_GUIDE.md) - Complete backup and restore procedures
- [Cloudflare Tunnel Setup](CLOUDFLARE_TUNNEL_SETUP.md) - Remote access configuration
- [Website Integration Documentation](WEBSITE_INTEGRATION_DOCUMENTATION.md)
- [Quick Start Guide](QUICK_START_GUIDE.md)
- [Testing Guide](TESTING_GUIDE.md)

## 🔐 Security Features

- **JWT Authentication** with refresh tokens
- **Role-based Access Control** (RBAC)
- **HTTPS/SSL** encryption
- **Input Validation** and sanitization
- **SQL Injection** protection
- **XSS Protection** headers

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

## ✅ Current Implementation Status

### Completed Features
- ✅ **RAG System** - 4 levels of search (Basic, Enhanced, Advanced, Comprehensive)
- ✅ **Document Management** - Upload, process, search, and manage documents
- ✅ **Vector Database** - 686 chunks with embeddings stored
- ✅ **Content Filtering** - Dynamic filtering with presets
- ✅ **API Authentication** - JWT-based authentication
- ✅ **CORS Configuration** - Support for production domain
- ✅ **Cache Optimization** - Standardized 24h embedding cache across services
- ✅ **Analytics Endpoints** - Query history, index info, performance stats

### Enabled Endpoints
- ✅ `/api/ai/rag/search/` - Basic RAG search
- ✅ `/api/ai/rag/search/advanced/` - Advanced RAG with hybrid search
- ✅ `/api/ai/rag/search/comprehensive/` - Comprehensive RAG with maximum detail
- ✅ `/api/ai/rag/search/vector/` - Vector similarity search
- ✅ `/api/ai/documents/` - Document management
- ✅ `/api/ai/content/` - Content filtering

### System Configuration
- **Ollama Models**: `qwen2.5:latest` (LLM), `bge-m3:latest` (embeddings)
- **Database**: PostgreSQL with pgvector extension
- **Chunks**: 686 document chunks ready for retrieval
- **Cache Strategy**: 24h embeddings, 1h search, 30m responses

## 🔄 Version History

- **v1.1.0 (build 3)** - CURRENT - Docs refresh, Website integration docs, startup guides fixed
- v1.0.1 (build 2) - RAG improvements, cache standardization, analytics endpoints
- v1.0.0 (build 1) - Initial release with core features

---

**AnyLab0812** - Smart Knowledge, Securely in Your Lab with intelligent management solutions.
