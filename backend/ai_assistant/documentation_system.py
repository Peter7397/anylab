"""
Documentation System for AnyLab AI Assistant

This module provides comprehensive documentation generation and management capabilities
for the AnyLab AI Assistant platform, including API documentation, user guides,
developer documentation, and automated documentation updates.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import markdown
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class DocumentationType(Enum):
    """Types of documentation supported by the system"""
    API_DOCS = "api_docs"
    USER_GUIDE = "user_guide"
    DEVELOPER_DOCS = "developer_docs"
    ADMIN_GUIDE = "admin_guide"
    TROUBLESHOOTING = "troubleshooting"
    RELEASE_NOTES = "release_notes"
    CHANGELOG = "changelog"
    FAQ = "faq"
    TUTORIAL = "tutorial"
    REFERENCE = "reference"


class DocumentationFormat(Enum):
    """Supported documentation formats"""
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    RESTRUCTURED_TEXT = "rst"
    JSON = "json"
    YAML = "yaml"


class DocumentationStatus(Enum):
    """Documentation status levels"""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    OUTDATED = "outdated"


@dataclass
class DocumentationMetadata:
    """Metadata for documentation entries"""
    id: str
    title: str
    doc_type: DocumentationType
    format: DocumentationFormat
    status: DocumentationStatus
    version: str
    author: str
    created_at: datetime
    updated_at: datetime
    tags: List[str]
    description: str
    target_audience: List[str]
    prerequisites: List[str]
    related_docs: List[str]
    last_reviewed: Optional[datetime] = None
    review_notes: Optional[str] = None
    approval_status: Optional[str] = None


@dataclass
class DocumentationSection:
    """Represents a section within documentation"""
    id: str
    title: str
    content: str
    order: int
    subsections: List['DocumentationSection']
    metadata: Dict[str, Any]


class DocumentationGenerator:
    """Generates various types of documentation"""
    
    def __init__(self):
        self.templates_dir = os.path.join(settings.BASE_DIR, 'ai_assistant', 'documentation', 'templates')
        self.output_dir = os.path.join(settings.BASE_DIR, 'ai_assistant', 'documentation', 'generated')
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure required directories exist"""
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_api_documentation(self, endpoints: List[Dict[str, Any]]) -> str:
        """Generate comprehensive API documentation"""
        sections = [
            self._generate_api_overview(),
            self._generate_authentication_section(),
            self._generate_endpoints_section(endpoints),
            self._generate_error_codes_section(),
            self._generate_examples_section(),
            self._generate_rate_limiting_section()
        ]
        
        return self._combine_sections(sections)
    
    def generate_user_guide(self, features: List[Dict[str, Any]]) -> str:
        """Generate user guide documentation"""
        sections = [
            self._generate_user_overview(),
            self._generate_getting_started_section(),
            self._generate_features_section(features),
            self._generate_troubleshooting_section(),
            self._generate_faq_section()
        ]
        
        return self._combine_sections(sections)
    
    def generate_developer_docs(self, codebase_info: Dict[str, Any]) -> str:
        """Generate developer documentation"""
        sections = [
            self._generate_developer_overview(),
            self._generate_architecture_section(codebase_info),
            self._generate_setup_section(),
            self._generate_contribution_section(),
            self._generate_testing_section()
        ]
        
        return self._combine_sections(sections)
    
    def _generate_api_overview(self) -> DocumentationSection:
        """Generate API overview section"""
        content = """
# API Overview

The AnyLab AI Assistant API provides comprehensive endpoints for:

- **RAG (Retrieval-Augmented Generation)**: Advanced search and question-answering
- **Document Management**: Upload, process, and manage documents
- **Content Collection**: Automated scraping and content collection
- **User Management**: Authentication and authorization
- **Analytics**: Performance tracking and usage analytics

## Base URL
```
https://anylab.dpdns.org/api/ai/
```

## Authentication
All API endpoints require authentication using JWT tokens.
        """
        
        return DocumentationSection(
            id="api_overview",
            title="API Overview",
            content=content.strip(),
            order=1,
            subsections=[],
            metadata={}
        )
    
    def _generate_authentication_section(self) -> DocumentationSection:
        """Generate authentication section"""
        content = """
# Authentication

The API uses JWT (JSON Web Token) authentication.

## Getting a Token

1. Login with your credentials:
```bash
curl -X POST https://anylab.dpdns.org/api/ai/auth/login/ \\
  -H "Content-Type: application/json" \\
  -d '{"username": "your_username", "password": "your_password"}'
```

2. Use the returned token in subsequent requests:
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
  https://anylab.dpdns.org/api/ai/rag/search/
```

## Token Refresh

Tokens expire after 24 hours. Use the refresh endpoint to get a new token.
        """
        
        return DocumentationSection(
            id="authentication",
            title="Authentication",
            content=content.strip(),
            order=2,
            subsections=[],
            metadata={}
        )
    
    def _generate_endpoints_section(self, endpoints: List[Dict[str, Any]]) -> DocumentationSection:
        """Generate endpoints documentation section"""
        content = "# API Endpoints\n\n"
        
        for endpoint in endpoints:
            content += f"""
## {endpoint['name']}

**Method:** `{endpoint['method']}`  
**URL:** `{endpoint['url']}`  
**Description:** {endpoint['description']}

### Parameters
{self._format_parameters(endpoint.get('parameters', []))}

### Response
{self._format_response(endpoint.get('response', {}))}

### Example
```bash
{endpoint.get('example', '')}
```

---
"""
        
        return DocumentationSection(
            id="endpoints",
            title="API Endpoints",
            content=content.strip(),
            order=3,
            subsections=[],
            metadata={}
        )
    
    def _format_parameters(self, parameters: List[Dict[str, Any]]) -> str:
        """Format parameters for documentation"""
        if not parameters:
            return "No parameters required."
        
        formatted = "| Parameter | Type | Required | Description |\n"
        formatted += "|-----------|------|----------|-------------|\n"
        
        for param in parameters:
            formatted += f"| {param['name']} | {param['type']} | {param.get('required', False)} | {param['description']} |\n"
        
        return formatted
    
    def _format_response(self, response: Dict[str, Any]) -> str:
        """Format response for documentation"""
        if not response:
            return "Standard JSON response."
        
        return f"""
```json
{json.dumps(response, indent=2)}
```
"""
    
    def _generate_error_codes_section(self) -> DocumentationSection:
        """Generate error codes section"""
        content = """
# Error Codes

The API uses standard HTTP status codes:

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Internal Server Error |

## Error Response Format

```json
{
    "error": "Error message",
    "code": "ERROR_CODE",
    "details": "Additional error details"
}
```
        """
        
        return DocumentationSection(
            id="error_codes",
            title="Error Codes",
            content=content.strip(),
            order=4,
            subsections=[],
            metadata={}
        )
    
    def _generate_examples_section(self) -> DocumentationSection:
        """Generate examples section"""
        content = """
# Examples

## RAG Search

```bash
curl -X POST https://anylab.dpdns.org/api/ai/rag/search/ \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "How to troubleshoot HPLC issues?",
    "search_mode": "comprehensive",
    "top_k": 5
  }'
```

## Document Upload

```bash
curl -X POST https://anylab.dpdns.org/api/ai/documents/upload/enhanced/ \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -F "file=@document.pdf"
```

## GitHub Repository Scan

```bash
curl -X POST https://anylab.dpdns.org/api/ai/github/scan/ \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "repository_url": "https://github.com/agilent/example-repo",
    "scan_depth": "shallow",
    "file_types": ["md", "txt", "py"]
  }'
```
        """
        
        return DocumentationSection(
            id="examples",
            title="Examples",
            content=content.strip(),
            order=5,
            subsections=[],
            metadata={}
        )
    
    def _generate_rate_limiting_section(self) -> DocumentationSection:
        """Generate rate limiting section"""
        content = """
# Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Standard endpoints**: 100 requests per minute
- **Heavy operations**: 10 requests per minute
- **File uploads**: 5 requests per minute

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Request limit per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the rate limit resets
        """
        
        return DocumentationSection(
            id="rate_limiting",
            title="Rate Limiting",
            content=content.strip(),
            order=6,
            subsections=[],
            metadata={}
        )
    
    def _generate_user_overview(self) -> DocumentationSection:
        """Generate user guide overview"""
        content = """
# AnyLab AI Assistant - User Guide

Welcome to AnyLab AI Assistant, your comprehensive laboratory management system with AI-powered assistance.

## What is AnyLab?

AnyLab is a sophisticated platform designed to help laboratory professionals:

- **Manage Documents**: Upload, organize, and search through technical documentation
- **Get AI Assistance**: Ask questions and get intelligent answers based on your documents
- **Access Knowledge**: Browse curated content from Agilent and other sources
- **Troubleshoot Issues**: Find solutions to common laboratory problems
- **Stay Updated**: Receive notifications about new content and updates

## Key Features

- **Dual Organization**: Switch between General Agilent Products and Lab Informatics Focus
- **AI-Powered Search**: Advanced RAG (Retrieval-Augmented Generation) capabilities
- **Document Processing**: Automatic processing of PDFs, images, and other formats
- **Content Collection**: Automated gathering of relevant technical content
- **User Contributions**: Share your own resources with the community
        """
        
        return DocumentationSection(
            id="user_overview",
            title="User Guide Overview",
            content=content.strip(),
            order=1,
            subsections=[],
            metadata={}
        )
    
    def _generate_getting_started_section(self) -> DocumentationSection:
        """Generate getting started section"""
        content = """
# Getting Started

## 1. Access AnyLab

Navigate to: https://anylab.dpdns.org

## 2. Login

Use your credentials to access the platform. If you don't have an account, contact your administrator.

## 3. Choose Your Mode

Select between:
- **General Agilent Products**: Broad coverage of Agilent instruments and software
- **Lab Informatics Focus**: Specialized content for laboratory informatics

## 4. Start Exploring

- Use the search bar to find specific information
- Browse the sidebar for organized content
- Upload your own documents
- Ask questions using the AI Assistant
        """
        
        return DocumentationSection(
            id="getting_started",
            title="Getting Started",
            content=content.strip(),
            order=2,
            subsections=[],
            metadata={}
        )
    
    def _generate_features_section(self, features: List[Dict[str, Any]]) -> DocumentationSection:
        """Generate features section"""
        content = "# Features\n\n"
        
        for feature in features:
            content += f"""
## {feature['name']}

{feature['description']}

### How to Use
{feature.get('usage', 'See the specific feature documentation for detailed usage instructions.')}

### Benefits
{feature.get('benefits', 'This feature helps improve your laboratory workflow and productivity.')}

---
"""
        
        return DocumentationSection(
            id="features",
            title="Features",
            content=content.strip(),
            order=3,
            subsections=[],
            metadata={}
        )
    
    def _generate_troubleshooting_section(self) -> DocumentationSection:
        """Generate troubleshooting section"""
        content = """
# Troubleshooting

## Common Issues

### Login Problems
- **Issue**: Cannot log in
- **Solution**: Check your credentials and ensure your account is active
- **Contact**: System administrator

### Search Not Working
- **Issue**: Search returns no results
- **Solution**: Try different keywords or check if content exists
- **Alternative**: Use the AI Assistant for more flexible queries

### File Upload Issues
- **Issue**: Files not uploading
- **Solution**: Check file size (max 50MB) and format (PDF, DOC, TXT, etc.)
- **Alternative**: Try uploading smaller files or different formats

### Performance Issues
- **Issue**: Slow response times
- **Solution**: Check your internet connection and try again
- **Alternative**: Contact support if issues persist

## Getting Help

- **Documentation**: Check this user guide
- **AI Assistant**: Ask questions directly in the platform
- **Support**: Contact your system administrator
- **Community**: Share issues and solutions with other users
        """
        
        return DocumentationSection(
            id="troubleshooting",
            title="Troubleshooting",
            content=content.strip(),
            order=4,
            subsections=[],
            metadata={}
        )
    
    def _generate_faq_section(self) -> DocumentationSection:
        """Generate FAQ section"""
        content = """
# Frequently Asked Questions

## General Questions

**Q: What is AnyLab?**
A: AnyLab is an AI-powered laboratory management system that helps you organize, search, and manage technical documentation.

**Q: How do I switch between organization modes?**
A: Use the toggle in the sidebar to switch between "General Agilent Products" and "Lab Informatics Focus".

**Q: Can I upload my own documents?**
A: Yes, you can upload various document types including PDFs, Word documents, and text files.

## Technical Questions

**Q: What file formats are supported?**
A: PDF, DOC, DOCX, TXT, MD, and various image formats (with OCR processing).

**Q: How does the AI search work?**
A: The system uses advanced RAG (Retrieval-Augmented Generation) technology to understand your queries and find relevant information.

**Q: Is my data secure?**
A: Yes, all data is encrypted and access is controlled through authentication and authorization.

## Usage Questions

**Q: How do I find specific information?**
A: Use the search bar, browse the sidebar categories, or ask the AI Assistant directly.

**Q: Can I share documents with others?**
A: Yes, you can contribute documents to the community knowledge base.

**Q: How often is content updated?**
A: Content is updated automatically through our collection systems and user contributions.
        """
        
        return DocumentationSection(
            id="faq",
            title="FAQ",
            content=content.strip(),
            order=5,
            subsections=[],
            metadata={}
        )
    
    def _generate_developer_overview(self) -> DocumentationSection:
        """Generate developer overview"""
        content = """
# Developer Documentation

This documentation is for developers who want to contribute to or integrate with the AnyLab AI Assistant platform.

## Architecture Overview

AnyLab is built using:

- **Backend**: Django REST Framework with PostgreSQL and Redis
- **Frontend**: React with TypeScript
- **AI/ML**: Ollama with Qwen models, pgvector for embeddings
- **Infrastructure**: Docker containers with automated deployment

## Key Components

- **RAG System**: Advanced retrieval-augmented generation
- **Document Processing**: Multi-format document handling
- **Content Collection**: Automated web scraping and processing
- **User Management**: Authentication and authorization
- **Analytics**: Performance and usage tracking
        """
        
        return DocumentationSection(
            id="developer_overview",
            title="Developer Overview",
            content=content.strip(),
            order=1,
            subsections=[],
            metadata={}
        )
    
    def _generate_architecture_section(self, codebase_info: Dict[str, Any]) -> DocumentationSection:
        """Generate architecture section"""
        content = f"""
# Architecture

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (React)       │◄──►│   (Django)      │◄──►│   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   AI Services   │
                       │   (Ollama)      │
                       └─────────────────┘
```

## Component Details

### Backend Services
{self._format_component_details(codebase_info.get('backend_services', []))}

### Frontend Components
{self._format_component_details(codebase_info.get('frontend_components', []))}

### Database Schema
{self._format_component_details(codebase_info.get('database_schema', []))}
        """
        
        return DocumentationSection(
            id="architecture",
            title="Architecture",
            content=content.strip(),
            order=2,
            subsections=[],
            metadata={}
        )
    
    def _format_component_details(self, components: List[Dict[str, Any]]) -> str:
        """Format component details for documentation"""
        if not components:
            return "Component details will be added here."
        
        formatted = ""
        for component in components:
            formatted += f"- **{component['name']}**: {component['description']}\n"
        
        return formatted
    
    def _generate_setup_section(self) -> DocumentationSection:
        """Generate setup section"""
        content = """
# Development Setup

## Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Redis 6+
- Docker (optional)

## Backend Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd anylab/backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup database**
```bash
python manage.py migrate
python manage.py createsuperuser
```

5. **Run development server**
```bash
python manage.py runserver
```

## Frontend Setup

1. **Navigate to frontend directory**
```bash
cd ../frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Start development server**
```bash
npm start
```

## Docker Setup

```bash
docker-compose up -d
```
        """
        
        return DocumentationSection(
            id="setup",
            title="Development Setup",
            content=content.strip(),
            order=3,
            subsections=[],
            metadata={}
        )
    
    def _generate_contribution_section(self) -> DocumentationSection:
        """Generate contribution section"""
        content = """
# Contributing

## Getting Started

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Code Standards

- Follow PEP 8 for Python code
- Use TypeScript for frontend code
- Write comprehensive tests
- Document your changes
- Follow the existing code style

## Testing

Run tests before submitting:

```bash
# Backend tests
python manage.py test

# Frontend tests
npm test
```

## Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Add a clear description of changes
4. Request review from maintainers
        """
        
        return DocumentationSection(
            id="contribution",
            title="Contributing",
            content=content.strip(),
            order=4,
            subsections=[],
            metadata={}
        )
    
    def _generate_testing_section(self) -> DocumentationSection:
        """Generate testing section"""
        content = """
# Testing

## Test Structure

- **Unit Tests**: Test individual components
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows
- **Performance Tests**: Test system performance

## Running Tests

### Backend Tests
```bash
# Run all tests
python manage.py test

# Run specific test module
python manage.py test ai_assistant.tests.test_rag_views

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Frontend Tests
```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage
```

## Test Data

Test data is managed through fixtures and factories:
- `fixtures/`: Static test data
- `factories/`: Dynamic test data generation
        """
        
        return DocumentationSection(
            id="testing",
            title="Testing",
            content=content.strip(),
            order=5,
            subsections=[],
            metadata={}
        )
    
    def _combine_sections(self, sections: List[DocumentationSection]) -> str:
        """Combine sections into a single document"""
        sorted_sections = sorted(sections, key=lambda x: x.order)
        
        combined = ""
        for section in sorted_sections:
            combined += f"\n{section.content}\n\n"
        
        return combined.strip()


class DocumentationManager:
    """Manages documentation lifecycle and updates"""
    
    def __init__(self):
        self.generator = DocumentationGenerator()
        self.cache_key_prefix = "doc_system"
    
    def generate_documentation(self, doc_type: DocumentationType, **kwargs) -> str:
        """Generate documentation of specified type"""
        cache_key = f"{self.cache_key_prefix}:{doc_type.value}"
        
        # Check cache first
        cached_doc = cache.get(cache_key)
        if cached_doc:
            logger.info(f"Retrieved cached documentation for {doc_type.value}")
            return cached_doc
        
        # Generate new documentation
        if doc_type == DocumentationType.API_DOCS:
            content = self.generator.generate_api_documentation(kwargs.get('endpoints', []))
        elif doc_type == DocumentationType.USER_GUIDE:
            content = self.generator.generate_user_guide(kwargs.get('features', []))
        elif doc_type == DocumentationType.DEVELOPER_DOCS:
            content = self.generator.generate_developer_docs(kwargs.get('codebase_info', {}))
        else:
            content = f"Documentation for {doc_type.value} is not yet implemented."
        
        # Cache the result
        cache.set(cache_key, content, timeout=3600)  # 1 hour cache
        
        logger.info(f"Generated documentation for {doc_type.value}")
        return content
    
    def save_documentation(self, content: str, metadata: DocumentationMetadata) -> bool:
        """Save documentation to file system"""
        try:
            filename = f"{metadata.id}_{metadata.version}.md"
            filepath = os.path.join(self.generator.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Saved documentation: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save documentation: {e}")
            return False
    
    def get_documentation_list(self) -> List[DocumentationMetadata]:
        """Get list of all documentation entries"""
        # This would typically query a database
        # For now, return a mock list
        return [
            DocumentationMetadata(
                id="api_docs_v1",
                title="API Documentation",
                doc_type=DocumentationType.API_DOCS,
                format=DocumentationFormat.MARKDOWN,
                status=DocumentationStatus.PUBLISHED,
                version="1.0",
                author="System",
                created_at=timezone.now(),
                updated_at=timezone.now(),
                tags=["api", "reference"],
                description="Complete API reference documentation",
                target_audience=["developers", "integrators"],
                prerequisites=["basic programming knowledge"],
                related_docs=["developer_docs"]
            )
        ]
    
    def update_documentation(self, doc_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing documentation"""
        try:
            # This would typically update a database record
            logger.info(f"Updated documentation: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update documentation: {e}")
            return False
    
    def archive_documentation(self, doc_id: str) -> bool:
        """Archive outdated documentation"""
        try:
            # This would typically update the status in a database
            logger.info(f"Archived documentation: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to archive documentation: {e}")
            return False


class DocumentationValidator:
    """Validates documentation quality and completeness"""
    
    def __init__(self):
        self.required_sections = {
            DocumentationType.API_DOCS: ["overview", "authentication", "endpoints"],
            DocumentationType.USER_GUIDE: ["overview", "getting_started", "features"],
            DocumentationType.DEVELOPER_DOCS: ["overview", "architecture", "setup"]
        }
    
    def validate_documentation(self, content: str, doc_type: DocumentationType) -> Dict[str, Any]:
        """Validate documentation content"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        # Check for required sections
        required_sections = self.required_sections.get(doc_type, [])
        for section in required_sections:
            if section.lower() not in content.lower():
                validation_result["errors"].append(f"Missing required section: {section}")
                validation_result["is_valid"] = False
        
        # Check content quality
        if len(content) < 100:
            validation_result["warnings"].append("Documentation seems too short")
        
        if not any(word in content.lower() for word in ["example", "usage", "how to"]):
            validation_result["suggestions"].append("Consider adding usage examples")
        
        return validation_result


# Example usage and testing
if __name__ == "__main__":
    # Initialize the documentation system
    doc_manager = DocumentationManager()
    validator = DocumentationValidator()
    
    # Generate API documentation
    api_endpoints = [
        {
            "name": "RAG Search",
            "method": "POST",
            "url": "/api/ai/rag/search/",
            "description": "Perform RAG-based search on documents",
            "parameters": [
                {"name": "query", "type": "string", "required": True, "description": "Search query"},
                {"name": "search_mode", "type": "string", "required": False, "description": "Search mode"}
            ],
            "response": {"results": [], "total": 0},
            "example": "curl -X POST /api/ai/rag/search/ -d '{\"query\": \"test\"}'"
        }
    ]
    
    api_docs = doc_manager.generate_documentation(
        DocumentationType.API_DOCS,
        endpoints=api_endpoints
    )
    
    # Validate the documentation
    validation = validator.validate_documentation(api_docs, DocumentationType.API_DOCS)
    
    print("Documentation generated successfully!")
    print(f"Validation result: {validation}")
