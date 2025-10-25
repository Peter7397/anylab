# 🔧 RAG Connection Issue - FIXED!

## ❌ **Problem:**
When running RAG queries, you got this error:
```
Error processing RAG query: HTTPConnectionPool(host='host.docker.internal', port=11434): Max retries exceeded with url: /api/chat (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0xffff2023dfd0>: Failed to establish a new connection: [Errno 111] Connection refused'))
```

## ✅ **Root Cause:**
The Django application was trying to connect to `host.docker.internal:11434` instead of the Ollama container directly.

## 🔧 **Solution Applied:**

### **1. Fixed RAG Service Connection**
Updated `pdfimport/rag_service.py`:

**Before:**
```python
response = requests.post(
    "http://host.docker.internal:11434/api/chat",
    # ...
)
```

**After:**
```python
import os

class QwenRAGService:
    def __init__(self, model_name="qwen2:latest"):
        self.model_name = model_name
        self.embedding_model = None
        # Get Ollama URL from environment or use default
        self.ollama_url = os.getenv('OLLAMA_API_BASE_URL', 'http://ollama:11434')

    def ollama_generate(self, prompt, model=None):
        if model is None:
            model = self.model_name
        response = requests.post(
            f"{self.ollama_url}/api/chat",
            # ...
        )
```

### **2. Environment Variable Configuration**
The `.env` file already had the correct setting:
```bash
OLLAMA_API_BASE_URL=http://ollama:11434
```

### **3. Container Communication**
- ✅ Web container can reach Ollama container
- ✅ Ollama API is responding correctly
- ✅ RAG service is using the correct URL

## 🧪 **Test Results:**

### **Ollama Connection Test:**
```bash
docker compose exec web curl -s http://ollama:11434/api/tags
# ✅ Returns available models

docker compose exec web curl -s -X POST http://ollama:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2:latest","messages":[{"role":"user","content":"Hello"}],"stream":false}'
# ✅ Returns AI response
```

### **RAG Service Test:**
```bash
docker compose exec web python3 test_rag.py
# ✅ RAG service initialized
# ✅ Ollama URL: http://ollama:11434
# ✅ Ollama response: Hello! As an artificial intelligence...
# ✅ RAG service is working correctly!
```

## 🎯 **Current Status:**

✅ **RAG Queries** - Now working correctly  
✅ **Ollama Integration** - Connected properly  
✅ **Container Communication** - All services communicating  
✅ **Environment Variables** - Properly configured  

## 🚀 **Next Steps:**

1. **Test RAG Query in Web Interface:**
   - Go to http://localhost:8000
   - Navigate to RAG Query section
   - Try asking a question about your uploaded documents

2. **Upload Some PDFs:**
   - Upload PDF documents through the web interface
   - The system will extract text and create embeddings

3. **Test Vector Search:**
   - Use the vector search feature to find relevant content
   - Then use RAG to get AI-powered responses

## 📋 **Verification Commands:**

```bash
# Check all services are running
docker compose ps

# Test Ollama connection
docker compose exec web curl -s http://ollama:11434/api/tags

# Test RAG service
docker compose exec web python3 test_rag.py

# Check web interface
curl http://localhost:8000
```

## 🎉 **Issue Resolved!**

The RAG query functionality should now work correctly. The Django application can properly communicate with the Ollama container, and you should be able to use the RAG features in the web interface. 