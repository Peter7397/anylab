"""
Advanced RAG Service with Priority 2 Improvements:
- Hybrid Search (BM25 + Vector)
- Cross-Encoder Reranking
- Enhanced Context Generation
- Query Understanding
"""
import requests
import hashlib
import logging
from typing import List, Dict
from django.db import connection
from django.conf import settings
from django.core.cache import cache
from .models import DocumentChunk, UploadedFile, QueryHistory
from .improved_rag_service import ImprovedRAGService
from .hybrid_search import hybrid_search_engine, query_processor
from .reranker import advanced_reranker, context_optimizer

logger = logging.getLogger(__name__)

class AdvancedRAGService(ImprovedRAGService):
    """Advanced RAG service with hybrid search and reranking"""
    
    def __init__(self, model_name=None):
        super().__init__(model_name)
        
        # Advanced search settings
        self.use_hybrid_search = True
        self.use_reranking = True
        self.use_query_expansion = True
        
        # Performance settings
        self.hybrid_cache_ttl = 3600  # 1 hour for hybrid search results
        
    def search_with_hybrid_and_reranking(self, query: str, top_k: int = 8) -> List[Dict]:
        """Advanced search pipeline with hybrid search and reranking"""
        try:
            # Create cache key for advanced search
            query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
            cache_key = f"advanced_search_{query_hash}_{top_k}_{self.similarity_threshold}"
            
            # Try cache first
            cached_results = cache.get(cache_key)
            if cached_results is not None:
                logger.info(f"Using cached advanced search results for: {query[:30]}...")
                return cached_results
            
            # Step 1: Query Processing and Adaptive Expansion
            query_type = query_processor.classify_query(query)
            # Use adaptive expansion - only expand if it would be beneficial
            if self.use_query_expansion and query_processor.should_expand_query(query):
                expanded_query = query_processor.expand_query(query)
                expansion_applied = True
            else:
                expanded_query = query
                expansion_applied = False
            
            logger.info(f"Query type: {query_type}, expansion applied: {expansion_applied}")
            
            # Step 2: Vector Search (get more candidates for hybrid)
            vector_candidates = 30 if self.use_hybrid_search else self.top_k_candidates
            vector_results = self.search_relevant_documents_with_scoring(
                expanded_query, top_k=vector_candidates
            )
            
            if not vector_results:
                return []
            
            # Step 3: Hybrid Search (combine vector + BM25)
            if self.use_hybrid_search and len(vector_results) > 1:
                hybrid_results = hybrid_search_engine.hybrid_search(
                    query, vector_results, top_k=top_k * 2  # Get more for reranking
                )
                logger.info(f"Hybrid search: {len(hybrid_results)} results")
            else:
                hybrid_results = vector_results[:top_k * 2]
                logger.info("Using vector-only search")
            
            # Step 4: Advanced Reranking
            if self.use_reranking and len(hybrid_results) > 1:
                reranked_results = advanced_reranker.advanced_rerank(query, hybrid_results)
                logger.info(f"Advanced reranking: {len(reranked_results)} results")
            else:
                reranked_results = hybrid_results
                logger.info("Skipping reranking")
            
            # Step 5: Final selection
            final_results = reranked_results[:top_k]
            
            # Add search metadata
            for result in final_results:
                result['query_type'] = query_type
                result['search_method'] = 'advanced_hybrid_reranked'
            
            # Cache results
            cache.set(cache_key, final_results, self.hybrid_cache_ttl)
            
            avg_final_score = sum(r.get('final_rerank_score', r.get('hybrid_score', 0)) 
                                for r in final_results) / len(final_results)
            logger.info(f"Advanced search complete: {len(final_results)} results, "
                       f"avg score: {avg_final_score:.3f}")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Error in advanced search: {e}")
            # Fallback to improved search
            return self.search_relevant_documents_with_scoring(query, top_k)
    
    def generate_advanced_response(self, query: str, documents: List[Dict]) -> str:
        """Generate response with advanced context optimization"""
        if not documents:
            return "I don't know."
        
        try:
            # Determine query type
            query_type = documents[0].get('query_type', 'general')
            
            # Generate optimized context
            optimized_context = context_optimizer.optimize_context(query, documents)
            
            # Generate enhanced prompt
            enhanced_prompt = context_optimizer.generate_enhanced_prompt(
                query, optimized_context, query_type
            )
            
            # Generate response with enhanced parameters
            response = self.ollama_generate_advanced(enhanced_prompt, query_type)
            
            # Clean response to remove any unwanted markdown formatting
            cleaned_response = self.clean_response_formatting(response)
            
            return cleaned_response
            
        except Exception as e:
            logger.error(f"Error generating advanced response: {e}")
            # Fallback to standard response generation
            return self.generate_enhanced_response(query, documents)
    
    def clean_response_formatting(self, response: str) -> str:
        """Remove unwanted markdown formatting and symbols from response"""
        import re
        
        if not response:
            return response
            
        # Remove markdown headers (### #### etc.)
        cleaned = re.sub(r'^#{1,6}\s+', '', response, flags=re.MULTILINE)
        
        # Remove extra markdown symbols that might appear
        cleaned = re.sub(r'\*\*\*+', '', cleaned)  # Remove multiple asterisks
        cleaned = re.sub(r'---+', '', cleaned)     # Remove horizontal rules
        cleaned = re.sub(r'===+', '', cleaned)     # Remove equals-based rules
        
        # Clean up multiple newlines while preserving paragraph structure
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        # Remove leading/trailing whitespace
        cleaned = cleaned.strip()
        
        return cleaned
    
    def ollama_generate_advanced(self, prompt: str, query_type: str = 'general', model: str = None) -> str:
        """Generate response with query-type specific parameters"""
        if model is None:
            model = self.model_name
        
        # Create cache key
        prompt_hash = hashlib.md5(prompt.encode('utf-8')).hexdigest()
        cache_key = f"advanced_response_{model}_{query_type}_{prompt_hash}"
        
        # Try cache first
        cached_response = cache.get(cache_key)
        if cached_response is not None:
            logger.debug(f"Using cached advanced response: {prompt_hash[:8]}...")
            return cached_response
        
        # Query-type specific parameters
        type_params = {
            'procedural': {
                'num_predict': 1200,  # Longer for step-by-step
                'temperature': 0.1,   # Very focused
                'top_p': 0.8,
                'repeat_penalty': 1.2
            },
            'definitional': {
                'num_predict': 800,   # Medium length
                'temperature': 0.15,  # Focused but some creativity
                'top_p': 0.85,
                'repeat_penalty': 1.15
            },
            'troubleshooting': {
                'num_predict': 1000,  # Detailed solutions
                'temperature': 0.1,   # Very focused
                'top_p': 0.8,
                'repeat_penalty': 1.25
            },
            'locational': {
                'num_predict': 600,   # Shorter, specific
                'temperature': 0.05,  # Extremely focused
                'top_p': 0.75,
                'repeat_penalty': 1.1
            },
            'general': {
                'num_predict': 1024,  # Balanced
                'temperature': 0.2,   # Balanced
                'top_p': 0.9,
                'repeat_penalty': 1.1
            }
        }
        
        params = type_params.get(query_type, type_params['general'])
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False,
                    "options": {
                        **params,
                        "top_k": 40,
                        "num_ctx": 4096
                    }
                },
                timeout=getattr(settings, 'OLLAMA_REQUEST_TIMEOUT', 120)
            )
            response.raise_for_status()
            response_text = response.json()["message"]["content"]
            
            # Cache the response
            cache.set(cache_key, response_text, self.response_cache_ttl)
            logger.debug(f"Generated and cached advanced response: {prompt_hash[:8]}...")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error in advanced generation: {e}")
            raise
    
    def query_with_advanced_rag(self, query: str, top_k: int = 8, user=None) -> Dict:
        """Complete advanced RAG pipeline"""
        try:
            # Create cache key
            query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
            cache_key = f"advanced_rag_{query_hash}_{top_k}"
            
            # Try cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"Using cached advanced RAG result: {query[:30]}...")
                return cached_result
            
            # Step 1: Advanced search with hybrid and reranking
            relevant_docs = self.search_with_hybrid_and_reranking(query, top_k)
            
            if not relevant_docs:
                response = "I don't know."
                result = {
                    "response": response,
                    "sources": [],
                    "query": query,
                    "search_method": "advanced_rag",
                    "search_stats": {
                        "total_results": 0,
                        "query_type": "unknown"
                    }
                }
            else:
                # Step 2: Generate advanced response
                response = self.generate_advanced_response(query, relevant_docs)
                
                # Calculate search statistics
                query_type = relevant_docs[0].get('query_type', 'general')
                avg_final_score = sum(r.get('final_rerank_score', r.get('hybrid_score', 0)) 
                                    for r in relevant_docs) / len(relevant_docs)
                
                result = {
                    "response": response,
                    "sources": relevant_docs,
                    "query": query,
                    "search_method": "advanced_rag",
                    "search_stats": {
                        "total_results": len(relevant_docs),
                        "query_type": query_type,
                        "avg_final_score": avg_final_score,
                        "hybrid_search": self.use_hybrid_search,
                        "reranking": self.use_reranking,
                        "query_expansion": self.use_query_expansion
                    }
                }
            
            # Cache result
            cache.set(cache_key, result, self.response_cache_ttl)
            
            # Save to history with advanced metadata
            if user:
                QueryHistory.objects.create(
                    query=query,
                    response=response,
                    sources=relevant_docs,
                    query_type='advanced_rag',
                    user=user
                )
            
            logger.info(f"Advanced RAG complete: {len(relevant_docs)} sources, "
                       f"query type: {result['search_stats'].get('query_type', 'unknown')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in advanced RAG: {e}")
            return {
                "response": f"Error processing query: {str(e)}",
                "sources": [],
                "query": query,
                "search_method": "error",
                "search_stats": {"error": str(e)}
            }
    
    def get_search_analytics(self) -> Dict:
        """Get analytics about search performance"""
        try:
            with connection.cursor() as cursor:
                # Get query type distribution
                cursor.execute("""
                    SELECT query_type, COUNT(*) as count
                    FROM ai_assistant_queryhistory 
                    WHERE query_type IN ('advanced_rag', 'enhanced_rag', 'rag')
                    GROUP BY query_type
                    ORDER BY count DESC;
                """)
                query_type_stats = cursor.fetchall()
                
                # Get recent performance
                cursor.execute("""
                    SELECT COUNT(*) as total_queries,
                           AVG(LENGTH(response)) as avg_response_length
                    FROM ai_assistant_queryhistory 
                    WHERE created_at >= NOW() - INTERVAL '24 hours';
                """)
                recent_stats = cursor.fetchone()
            
            return {
                "query_type_distribution": [
                    {"type": row[0], "count": row[1]} for row in query_type_stats
                ],
                "recent_24h": {
                    "total_queries": recent_stats[0] if recent_stats else 0,
                    "avg_response_length": recent_stats[1] if recent_stats else 0
                },
                "search_features": {
                    "hybrid_search": self.use_hybrid_search,
                    "reranking": self.use_reranking,
                    "query_expansion": self.use_query_expansion,
                    "similarity_threshold": self.similarity_threshold
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting search analytics: {e}")
            return {"error": str(e)}

# Global advanced RAG service instance
advanced_rag_service = AdvancedRAGService()
