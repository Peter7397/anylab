"""
Comprehensive RAG Service for Maximum Detail and Complete Answers
Designed to provide exhaustive, detailed responses using all available information
"""
import requests
import hashlib
import logging
from typing import List, Dict
from django.db import connection
from django.conf import settings
from django.core.cache import cache
from .models import DocumentChunk, UploadedFile, QueryHistory
from .advanced_rag_service import AdvancedRAGService
from .hybrid_search import hybrid_search_engine, query_processor
from .reranker import advanced_reranker

logger = logging.getLogger(__name__)

class ComprehensiveContextOptimizer:
    """Optimizer for maximum information extraction and comprehensive context"""
    
    def __init__(self, max_context_length: int = 12000):  # Increased from 4000
        self.max_context_length = max_context_length
        self.min_sources_for_comprehensive = 3
        
    def extract_all_relevant_information(self, query: str, documents: List[Dict]) -> Dict:
        """Extract maximum information from all relevant sources"""
        if not documents:
            return {"context": "", "source_count": 0, "total_info": 0}
        
        # Group documents by source file for better organization
        sources_by_file = {}
        for doc in documents:
            filename = doc.get('filename', 'Unknown')
            if filename not in sources_by_file:
                sources_by_file[filename] = []
            sources_by_file[filename].append(doc)
        
        comprehensive_sections = []
        total_characters = 0
        sources_used = 0
        
        # Process each source file comprehensively
        for filename, file_docs in sources_by_file.items():
            if total_characters >= self.max_context_length:
                break
                
            # Sort documents within each file by relevance
            file_docs.sort(key=lambda x: x.get('final_rerank_score', x.get('hybrid_score', 0)), reverse=True)
            
            # Create comprehensive section for this source
            section_parts = []
            section_header = f"\n=== SOURCE: {filename} ===\n"
            
            for i, doc in enumerate(file_docs):
                available_space = self.max_context_length - total_characters - len(section_header) - 100
                if available_space <= 0:
                    break
                
                content = doc.get('content', '')
                page = doc.get('page_number', 1)
                relevance = doc.get('final_rerank_score', doc.get('hybrid_score', 0))
                
                # Include more content per document for comprehensive answers
                if len(content) > available_space:
                    # Smart truncation - try to keep complete sections
                    truncated = content[:available_space]
                    # Look for natural break points
                    for break_point in ['. ', '.\n', ':\n', '\n\n']:
                        last_break = truncated.rfind(break_point)
                        if last_break > available_space * 0.6:  # Keep at least 60% of content
                            truncated = truncated[:last_break + len(break_point)]
                            break
                    content = truncated
                
                doc_part = f"[Page {page}, Relevance: {relevance:.3f}]\n{content}"
                section_parts.append(doc_part)
                total_characters += len(doc_part) + 10  # +10 for formatting
                
                if total_characters >= self.max_context_length:
                    break
            
            if section_parts:
                section_content = section_header + "\n\n".join(section_parts)
                comprehensive_sections.append(section_content)
                sources_used += 1
        
        # Combine all sections
        comprehensive_context = "\n\n".join(comprehensive_sections)
        
        logger.info(f"Comprehensive context: {sources_used} sources, {len(comprehensive_context)} characters")
        
        return {
            "context": comprehensive_context,
            "source_count": sources_used,
            "total_info": len(comprehensive_context),
            "sources_by_file": len(sources_by_file)
        }
    
    def generate_comprehensive_prompt(self, query: str, context_info: Dict, query_type: str = 'general') -> str:
        """Generate prompt optimized for comprehensive, detailed responses"""
        
        context = context_info.get("context", "")
        source_count = context_info.get("source_count", 0)
        
        # Enhanced instruction for comprehensive responses
        comprehensive_instruction = (
            "You are an expert technical consultant providing comprehensive, detailed responses.\n\n"
            "CRITICAL INSTRUCTIONS FOR COMPREHENSIVE ANSWERS:\n"
            "1. Use ALL available information from the provided context - leave nothing out\n"
            "2. Provide COMPLETE, DETAILED answers regardless of length\n"
            "3. Include ALL relevant details, steps, procedures, and explanations\n"
            "4. Synthesize information from ALL sources to create a thorough response\n"
            "5. Cite sources using [Source: filename] format\n"
            "6. If multiple sources provide similar information, combine and elaborate\n"
            "7. Include specific details like version numbers, file paths, exact procedures\n"
            "8. Provide background context and explanations for better understanding\n"
            "9. Never truncate or summarize - give complete, exhaustive information\n"
            "10. Structure the response logically using clear paragraphs and natural flow\n"
            "11. Do NOT use markdown formatting, headers (###, ####), or special symbols\n"
            "12. Write in plain text with proper paragraph breaks and natural organization\n\n"
        )
        
        # Query-type specific comprehensive instructions
        type_specific_instructions = {
            'procedural': (
                "PROCEDURAL RESPONSE REQUIREMENTS:\n"
                "- Provide ALL steps in complete detail with sub-steps\n"
                "- Include prerequisites, requirements, and preparation steps\n"
                "- Explain the purpose and context of each major step\n"
                "- Include troubleshooting information for each step\n"
                "- Provide alternative methods if mentioned in sources\n"
                "- Include post-completion verification steps\n"
                "- Add warnings, cautions, and best practices\n\n"
            ),
            'definitional': (
                "DEFINITIONAL RESPONSE REQUIREMENTS:\n"
                "- Provide complete, comprehensive definitions\n"
                "- Include ALL aspects, features, and characteristics\n"
                "- Explain relationships to other concepts\n"
                "- Include examples, use cases, and applications\n"
                "- Cover technical specifications and requirements\n"
                "- Explain variations, types, or categories\n\n"
            ),
            'troubleshooting': (
                "TROUBLESHOOTING RESPONSE REQUIREMENTS:\n"
                "- Provide ALL possible causes and solutions\n"
                "- Include detailed diagnostic procedures\n"
                "- Explain symptoms and how to identify issues\n"
                "- Provide step-by-step resolution procedures\n"
                "- Include prevention measures and best practices\n"
                "- Cover related issues and their solutions\n\n"
            ),
            'general': (
                "COMPREHENSIVE RESPONSE REQUIREMENTS:\n"
                "- Address ALL aspects of the question thoroughly\n"
                "- Include background information and context\n"
                "- Provide detailed explanations and examples\n"
                "- Cover related topics and considerations\n"
                "- Include practical applications and implications\n\n"
            )
        }
        
        specific_instruction = type_specific_instructions.get(query_type, type_specific_instructions['general'])
        
        # Construct comprehensive prompt
        comprehensive_prompt = (
            f"{comprehensive_instruction}"
            f"QUERY TYPE: {query_type.title()}\n"
            f"{specific_instruction}"
            f"AVAILABLE SOURCES: {source_count} comprehensive sources with detailed information\n"
            f"CONTEXT LENGTH: {len(context)} characters of relevant information\n\n"
            f"COMPREHENSIVE CONTEXT:\n{context}\n\n"
            f"USER QUESTION: {query}\n\n"
            f"PROVIDE A COMPLETE, COMPREHENSIVE, DETAILED RESPONSE USING ALL AVAILABLE INFORMATION:\n"
        )
        
        return comprehensive_prompt

class ComprehensiveRAGService(AdvancedRAGService):
    """RAG service optimized for comprehensive, detailed responses"""
    
    def __init__(self, model_name=None):
        super().__init__(model_name)
        
        # Enhanced settings for comprehensive responses
        self.comprehensive_top_k = 15  # Increased from 8
        self.comprehensive_candidates = 40  # Increased from 20
        self.similarity_threshold = 0.4  # Lowered for more inclusive results
        
        # Use comprehensive context optimizer
        self.comprehensive_optimizer = ComprehensiveContextOptimizer(max_context_length=12000)
        
        # Enhanced cache settings for comprehensive responses
        self.comprehensive_cache_ttl = 7200  # 2 hours for comprehensive results
        
    def search_for_comprehensive_results(self, query: str, top_k: int = None) -> List[Dict]:
        """Search for maximum relevant information across all sources"""
        if top_k is None:
            top_k = self.comprehensive_top_k
            
        try:
            # Create cache key for comprehensive search
            query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
            cache_key = f"comprehensive_search_{query_hash}_{top_k}_{self.similarity_threshold}"
            
            # Try cache first
            cached_results = cache.get(cache_key)
            if cached_results is not None:
                logger.info(f"Using cached comprehensive search results: {query[:30]}...")
                return cached_results
            
            # Step 1: Query processing with expansion for maximum coverage
            query_type = query_processor.classify_query(query)
            expanded_query = query_processor.expand_query(query)
            
            # Step 2: Cast a wide net for comprehensive coverage
            vector_results = self.search_relevant_documents_with_scoring(
                expanded_query, top_k=self.comprehensive_candidates
            )
            
            if not vector_results:
                return []
            
            # Step 3: Hybrid search with more candidates
            hybrid_results = hybrid_search_engine.hybrid_search(
                query, vector_results, top_k=top_k * 2  # Get more for comprehensive coverage
            )
            
            # Step 4: Advanced reranking but keep more results
            reranked_results = advanced_reranker.advanced_rerank(query, hybrid_results)
            
            # Step 5: Select comprehensive set of results
            comprehensive_results = reranked_results[:top_k]
            
            # Add comprehensive metadata
            for result in comprehensive_results:
                result['query_type'] = query_type
                result['search_method'] = 'comprehensive_rag'
                result['comprehensive_mode'] = True
            
            # Cache results
            cache.set(cache_key, comprehensive_results, self.comprehensive_cache_ttl)
            
            logger.info(f"Comprehensive search: {len(comprehensive_results)} results for maximum detail")
            
            return comprehensive_results
            
        except Exception as e:
            logger.error(f"Error in comprehensive search: {e}")
            # Fallback to advanced search
            return self.search_with_hybrid_and_reranking(query, top_k)
    
    def generate_comprehensive_response(self, query: str, documents: List[Dict]) -> str:
        """Generate comprehensive, detailed response using all available information"""
        if not documents:
            return "I don't have enough information in my knowledge base to provide a comprehensive answer to your question."
        
        try:
            # Extract comprehensive information from all sources
            context_info = self.comprehensive_optimizer.extract_all_relevant_information(query, documents)
            
            # Determine query type for specialized handling
            query_type = documents[0].get('query_type', 'general')
            
            # Generate comprehensive prompt
            comprehensive_prompt = self.comprehensive_optimizer.generate_comprehensive_prompt(
                query, context_info, query_type
            )
            
            # Generate comprehensive response with enhanced parameters
            response = self.ollama_generate_comprehensive(comprehensive_prompt, query_type)
            
            # Clean response to remove any unwanted markdown formatting
            cleaned_response = self.clean_response_formatting(response)
            
            return cleaned_response
            
        except Exception as e:
            logger.error(f"Error generating comprehensive response: {e}")
            # Fallback to advanced response generation
            return self.generate_advanced_response(query, documents)
    
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
    
    def ollama_generate_comprehensive(self, prompt: str, query_type: str = 'general', model: str = None) -> str:
        """Generate comprehensive response with parameters optimized for detailed answers"""
        if model is None:
            model = self.model_name
        
        # Create cache key
        prompt_hash = hashlib.md5(prompt.encode('utf-8')).hexdigest()
        cache_key = f"comprehensive_response_{model}_{query_type}_{prompt_hash}"
        
        # Try cache first
        cached_response = cache.get(cache_key)
        if cached_response is not None:
            logger.debug(f"Using cached comprehensive response: {prompt_hash[:8]}...")
            return cached_response
        
        # Comprehensive response parameters - optimized for detailed, complete answers
        comprehensive_params = {
            'procedural': {
                'num_predict': 3000,    # Much longer for complete procedures
                'temperature': 0.1,     # Very focused for accuracy
                'top_p': 0.8,
                'repeat_penalty': 1.15,
                'num_ctx': 8192        # Larger context window
            },
            'definitional': {
                'num_predict': 2500,    # Longer for comprehensive definitions
                'temperature': 0.15,    # Slightly more creative for examples
                'top_p': 0.85,
                'repeat_penalty': 1.1,
                'num_ctx': 8192
            },
            'troubleshooting': {
                'num_predict': 3500,    # Longest for complete troubleshooting
                'temperature': 0.1,     # Very focused for accuracy
                'top_p': 0.8,
                'repeat_penalty': 1.2,
                'num_ctx': 8192
            },
            'locational': {
                'num_predict': 2000,    # Moderate length for locations
                'temperature': 0.05,    # Extremely focused
                'top_p': 0.75,
                'repeat_penalty': 1.1,
                'num_ctx': 8192
            },
            'general': {
                'num_predict': 2800,    # Long for comprehensive coverage
                'temperature': 0.15,    # Balanced
                'top_p': 0.9,
                'repeat_penalty': 1.1,
                'num_ctx': 8192
            }
        }
        
        params = comprehensive_params.get(query_type, comprehensive_params['general'])
        
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
                        "top_k": 40
                    }
                },
                timeout=300  # Increased timeout for longer responses
            )
            response.raise_for_status()
            response_text = response.json()["message"]["content"]
            
            # Cache the comprehensive response
            cache.set(cache_key, response_text, self.comprehensive_cache_ttl)
            logger.info(f"Generated comprehensive response: {len(response_text)} characters")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error in comprehensive generation: {e}")
            raise
    
    def query_with_comprehensive_rag(self, query: str, top_k: int = None, user=None) -> Dict:
        """Complete comprehensive RAG pipeline for maximum detail"""
        if top_k is None:
            top_k = self.comprehensive_top_k
            
        try:
            # Create cache key
            query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
            cache_key = f"comprehensive_rag_{query_hash}_{top_k}"
            
            # Try cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"Using cached comprehensive RAG result: {query[:30]}...")
                return cached_result
            
            # Step 1: Comprehensive search for maximum information
            relevant_docs = self.search_for_comprehensive_results(query, top_k)
            
            if not relevant_docs:
                response = "I don't have enough information in my knowledge base to provide a comprehensive answer to your question. Please try rephrasing your question or check if the relevant documents have been uploaded."
                result = {
                    "response": response,
                    "sources": [],
                    "query": query,
                    "search_method": "comprehensive_rag",
                    "comprehensive_stats": {
                        "total_results": 0,
                        "query_type": "unknown",
                        "comprehensive_mode": True
                    }
                }
            else:
                # Step 2: Generate comprehensive response
                response = self.generate_comprehensive_response(query, relevant_docs)
                
                # Calculate comprehensive statistics
                query_type = relevant_docs[0].get('query_type', 'general')
                avg_score = sum(r.get('final_rerank_score', r.get('hybrid_score', 0)) 
                              for r in relevant_docs) / len(relevant_docs)
                
                # Count unique sources
                unique_sources = len(set(doc.get('filename', 'Unknown') for doc in relevant_docs))
                
                result = {
                    "response": response,
                    "sources": relevant_docs,
                    "query": query,
                    "search_method": "comprehensive_rag",
                    "comprehensive_stats": {
                        "total_results": len(relevant_docs),
                        "unique_sources": unique_sources,
                        "query_type": query_type,
                        "avg_relevance_score": avg_score,
                        "response_length": len(response),
                        "comprehensive_mode": True,
                        "context_characters": sum(len(doc.get('content', '')) for doc in relevant_docs)
                    }
                }
            
            # Cache result
            cache.set(cache_key, result, self.comprehensive_cache_ttl)
            
            # Save to history with comprehensive metadata
            if user:
                QueryHistory.objects.create(
                    query=query,
                    response=response,
                    sources=relevant_docs,
                    query_type='comprehensive_rag',
                    user=user
                )
            
            logger.info(f"Comprehensive RAG complete: {len(relevant_docs)} sources, "
                       f"{len(response)} chars, query type: {result['comprehensive_stats'].get('query_type')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in comprehensive RAG: {e}")
            return {
                "response": f"I apologize, but I encountered an error while processing your request for comprehensive information: {str(e)}",
                "sources": [],
                "query": query,
                "search_method": "error",
                "comprehensive_stats": {"error": str(e)}
            }

# Global comprehensive RAG service instance
comprehensive_rag_service = ComprehensiveRAGService()
