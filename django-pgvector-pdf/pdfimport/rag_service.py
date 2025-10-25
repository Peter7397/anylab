import requests
from .models import Document
from django.db import connection
import numpy as np
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
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant. Use only the following context to answer the question."},
                    {"role": "user", "content": prompt}
                ],
                "stream": False
            }
        )
        response.raise_for_status()
        return response.json()["message"]["content"]

    def search_relevant_documents(self, query, top_k=10):
        from sentence_transformers import SentenceTransformer
        if not self.embedding_model:
            self.embedding_model = SentenceTransformer('/model/all-MiniLM-L6-v2')
        query_embedding = self.embedding_model.encode([query])[0].tolist()
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, content, uploaded_file_id, page_number FROM pdfimport_document
                ORDER BY embedding <#> %s::vector
                LIMIT %s;
            """, [query_embedding, top_k])
            results = cursor.fetchall()
        return [{"id": row[0], "content": row[1], "uploaded_file_id": row[2], "page_number": row[3]} for row in results]

    def generate_response(self, query, context_documents):
        # Build context with reference numbers
        context_lines = []
        for idx, doc in enumerate(context_documents, 1):
            context_lines.append(f"[{idx}] {doc['content']}")
        context = "\n".join(context_lines)
        prompt = (
            "You are a helpful assistant. "
            "Answer the user's question ONLY using the provided context below. "
            "Cite all information derived from the context using bracketed reference numbers (e.g., [1], or multiple [1][3]). "
            "If the requested information is not found in the context, respond directly with: \"I don't know.\" "
            "Do not use your internal knowledge base or common sense to answer questions. "
            "Answers should be concise and to the point, without additional explanation or elaboration.\n\n"
            f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
        )
        return self.ollama_generate(prompt)

    def query_with_rag(self, query, top_k=10):
        relevant_docs = self.search_relevant_documents(query, top_k)
        if not relevant_docs:
            return "I couldn't find any relevant information in the uploaded documents."
        response = self.generate_response(query, relevant_docs)
        return {
            "response": response,
            "sources": relevant_docs,
            "query": query
        } 