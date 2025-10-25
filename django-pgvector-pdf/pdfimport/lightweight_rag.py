from sentence_transformers import SentenceTransformer
from django.db import connection
import re

class LightweightRAGService:
    def __init__(self):
        self.embedding_model = None
        
    def load_embedding_model(self):
        """Load only the embedding model (much lighter than LLM)"""
        if not self.embedding_model:
            self.embedding_model = SentenceTransformer('/model/all-MiniLM-L6-v2')
            
    def search_relevant_documents(self, query, top_k=10):
        """Search for relevant documents using vector similarity"""
        self.load_embedding_model()
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])[0].tolist()
        
        # Search for similar documents with proper vector casting
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, content, uploaded_file_id, page_number FROM pdfimport_document
                ORDER BY embedding <#> %s::vector
                LIMIT %s;
            """, [query_embedding, top_k])
            results = cursor.fetchall()
            
        return [{"id": row[0], "content": row[1], "uploaded_file_id": row[2], "page_number": row[3]} for row in results]
    
    def extract_key_sentences(self, documents, query):
        """Extract sentences that contain query keywords"""
        query_words = set(re.findall(r'\w+', query.lower()))
        relevant_sentences = []
        
        for doc in documents:
            sentences = re.split(r'[.!?]+', doc['content'])
            for sentence in sentences:
                sentence_words = set(re.findall(r'\w+', sentence.lower()))
                if query_words.intersection(sentence_words):
                    relevant_sentences.append(sentence.strip())
                    
        return relevant_sentences[:5]  # Return top 5 relevant sentences
    
    def generate_simple_response(self, query, documents):
        """Generate a simple response using extracted sentences"""
        relevant_sentences = self.extract_key_sentences(documents, query)
        
        if not relevant_sentences:
            return "I couldn't find specific information about that in the documents."
            
        response = f"Based on the documents, here's what I found about '{query}':\n\n"
        response += "\n".join([f"• {sentence}" for sentence in relevant_sentences])
        
        return response
    
    def query_with_lightweight_rag(self, query, top_k=10):
        """Lightweight RAG pipeline using only embeddings and text extraction"""
        # Step 1: Retrieve relevant documents
        relevant_docs = self.search_relevant_documents(query, top_k)
        
        if not relevant_docs:
            return {
                "response": "I couldn't find any relevant information in the uploaded documents.",
                "sources": [],
                "query": query,
                "method": "lightweight"
            }
            
        # Step 2: Generate simple response
        response = self.generate_simple_response(query, relevant_docs)
        
        return {
            "response": response,
            "sources": relevant_docs,
            "query": query,
            "method": "lightweight"
        } 