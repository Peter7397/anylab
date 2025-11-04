"""
Graph-Enhanced RAG Service

Combines vector similarity search with graph traversal for enhanced retrieval.
Uses entity extraction and graph relationships to improve context.
"""

import logging
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.core.cache import cache
import hashlib

from .neo4j_service import get_neo4j_service
from .graph_query_service import GraphQueryService
from .graph_entity_extractor import GraphEntityExtractor
from ..comprehensive_rag_service import ComprehensiveRAGService
from ..models import DocumentChunk, UploadedFile

logger = logging.getLogger(__name__)


class GraphRAGService(ComprehensiveRAGService):
    """RAG service enhanced with graph-based retrieval"""
    
    def __init__(self, model_name=None):
        """Initialize Graph RAG service"""
        super().__init__(model_name)
        self.graph_query_service = GraphQueryService()
        self.entity_extractor = GraphEntityExtractor()
        logger.info("GraphRAGService initialized")
    
    def hybrid_search_with_graph(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Hybrid search combining vector similarity + graph traversal
        
        Steps:
        1. Vector similarity search (existing)
        2. Extract entities from query
        3. Graph-based document search
        4. Merge and rerank results
        """
        try:
            # Step 1: Vector similarity search (existing comprehensive search)
            vector_results = self.search_for_comprehensive_results(query, top_k=top_k * 2)
            
            logger.info(f"Vector search found {len(vector_results)} results")
            
            # Step 2: Graph-based search
            graph_results = self.graph_query_service.find_documents_by_entities(query, max_results=top_k)
            
            logger.info(f"Graph search found {len(graph_results)} results")
            
            # Step 3: Merge results
            merged_results = self._merge_vector_and_graph_results(vector_results, graph_results, top_k)
            
            logger.info(f"Merged results: {len(merged_results)} documents")
            
            # Step 4: Enhance with graph context
            enhanced_results = self._enhance_with_graph_context(query, merged_results)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error in hybrid graph search: {e}", exc_info=True)
            # Fallback to vector search only
            return self.search_for_comprehensive_results(query, top_k)
    
    def _merge_vector_and_graph_results(
        self, 
        vector_results: List[Dict], 
        graph_results: List[Dict],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Merge vector and graph search results
        
        Strategy:
        - Documents in both: boost score
        - Graph-only documents: add with lower priority
        - Vector-only documents: keep as is
        """
        # Create document map from vector results
        vector_docs = {}
        for result in vector_results:
            doc_id = str(result.get('uploaded_file_id', ''))
            if doc_id:
                vector_docs[doc_id] = result
                result['source'] = 'vector'
                result['graph_boost'] = False
        
        # Create document map from graph results
        graph_docs = {}
        for result in graph_results:
            doc_id = str(result.get('document_id', ''))
            graph_docs[doc_id] = result
        
        # Merge: boost documents found in both
        merged = []
        seen_doc_ids = set()
        
        # First: documents found in both (highest priority)
        for doc_id, vector_result in vector_docs.items():
            if doc_id in graph_docs:
                # Boost score for graph-connected documents
                graph_result = graph_docs[doc_id]
                vector_result['graph_boost'] = True
                vector_result['graph_score'] = graph_result.get('score', 0)
                vector_result['matched_entities'] = graph_result.get('matched_entities', [])
                
                # Boost final score
                original_score = vector_result.get('final_rerank_score', vector_result.get('hybrid_score', 0))
                vector_result['final_rerank_score'] = original_score * 1.3  # 30% boost
                vector_result['source'] = 'vector+graph'
                
                merged.append(vector_result)
                seen_doc_ids.add(doc_id)
        
        # Second: vector-only results (maintain original order)
        for doc_id, vector_result in vector_docs.items():
            if doc_id not in seen_doc_ids:
                merged.append(vector_result)
                seen_doc_ids.add(doc_id)
        
        # Third: graph-only results (add with lower priority)
        for doc_id, graph_result in graph_docs.items():
            if doc_id not in seen_doc_ids:
                # Convert graph result to document chunk format
                # We need to get the actual chunks from the document
                doc_id_int = int(doc_id) if doc_id.isdigit() else None
                if doc_id_int:
                    chunks = DocumentChunk.objects.filter(uploaded_file_id=doc_id_int).first()
                    if chunks:
                        graph_result['content'] = chunks.content[:500]  # Sample content
                        graph_result['uploaded_file_id'] = doc_id_int
                        graph_result['filename'] = graph_result.get('filename', 'Unknown')
                        graph_result['source'] = 'graph'
                        graph_result['final_rerank_score'] = graph_result.get('score', 0) * 0.7  # Lower weight
                        merged.append(graph_result)
                        seen_doc_ids.add(doc_id)
        
        # Sort by final score and return top_k
        merged.sort(key=lambda x: x.get('final_rerank_score', x.get('score', 0)), reverse=True)
        
        return merged[:top_k]
    
    def _enhance_with_graph_context(self, query: str, results: List[Dict]) -> List[Dict]:
        """Enhance results with graph context information"""
        try:
            # Extract entities from query
            query_entities = self.entity_extractor.extract_entities(query)
            
            if not query_entities:
                return results
            
            # Get entity context (relationships, co-occurrences) and paths
            entity_context = self.graph_query_service.get_entity_context(query_entities, max_context=5)
            entity_paths = self.graph_query_service.get_shortest_paths_between_query_entities(query_entities, max_paths=5)
            
            # Add graph context to each result
            for result in results:
                result['graph_context'] = {
                    'query_entities': [
                        {
                            'name': e.text,
                            'type': e.entity_type,
                            'normalized': e.normalized_text
                        }
                        for e in query_entities
                    ],
                    'relationships': entity_context.get('relationships', []),
                    'co_occurrences': entity_context.get('co_occurrences', []),
                    'paths': entity_paths
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Error enhancing with graph context: {e}")
            return results
    
    def generate_graph_enhanced_prompt(self, query: str, documents: List[Dict]) -> str:
        """Generate prompt enhanced with graph context"""
        if not documents:
            return ""
        
        # Get graph context from first document (if available)
        graph_context = documents[0].get('graph_context', {})
        
        # Build enhanced context section
        graph_section = ""
        if graph_context:
            entities = graph_context.get('query_entities', [])
            relationships = graph_context.get('relationships', [])
            
            if entities:
                graph_section = "\n\n=== KNOWLEDGE GRAPH CONTEXT ===\n"
                graph_section += "Query Entities Found:\n"
                for entity in entities:
                    graph_section += f"- {entity['name']} ({entity['type']})\n"
                
                if relationships:
                    graph_section += "\nRelated Entities:\n"
                    for rel in relationships[:5]:
                        graph_section += f"- {rel.get('entity1')} → {rel.get('entity2')}\n"
        
        # Build document context
        context_parts = []
        for idx, doc in enumerate(documents[:10], 1):
            content = doc.get('content', '')[:600]
            filename = doc.get('filename', 'Unknown')
            score = doc.get('final_rerank_score', doc.get('hybrid_score', 0))
            source = doc.get('source', 'unknown')
            
            # Add graph boost indicator
            boost_indicator = " [Graph-Enhanced]" if doc.get('graph_boost') else ""
            
            context_parts.append(
                f"[{idx}] {filename} (Score: {score:.3f}, Source: {source}{boost_indicator})\n{content}"
            )
        
        context = "\n\n".join(context_parts)
        
        # Enhanced prompt with graph information
        prompt = (
            "You are a technical documentation expert. Use ONLY the provided context below.\n\n"
            "KNOWLEDGE GRAPH CONTEXT:\n"
            "The context below includes information enriched with knowledge graph relationships. "
            "Documents marked as 'Graph-Enhanced' have been found through both semantic similarity "
            "and entity relationships, making them highly relevant.\n\n"
            f"{graph_section}\n"
            f"DOCUMENT CONTEXT:\n{context}\n\n"
            f"USER QUESTION: {query}\n\n"
            "PROVIDE A COMPREHENSIVE ANSWER using the context above. "
            "Pay special attention to Graph-Enhanced documents as they contain highly relevant information. "
            "Cite sources using bracketed numbers [1], [2], etc."
        )
        
        return prompt
    
    def query_with_graph_rag(self, query: str, top_k: int = 10, user=None) -> Dict[str, Any]:
        """
        Complete Graph RAG pipeline
        
        Combines vector search + graph traversal for enhanced retrieval and response
        """
        try:
            # Create cache key
            query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
            cache_key = f"graph_rag_{query_hash}_{top_k}"
            
            # Check cache
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info(f"Using cached graph RAG result: {query[:30]}...")
                return cached_result
            
            # Hybrid search with graph
            relevant_docs = self.hybrid_search_with_graph(query, top_k)
            
            if not relevant_docs:
                response = "I don't have enough information in my knowledge base to provide an answer."
                result = {
                    "response": response,
                    "sources": [],
                    "query": query,
                    "search_method": "graph_rag",
                    "graph_stats": {
                        "vector_results": 0,
                        "graph_results": 0,
                        "merged_results": 0,
                        "graph_enhanced": 0
                    }
                }
            else:
                # Generate enhanced prompt
                enhanced_prompt = self.generate_graph_enhanced_prompt(query, relevant_docs)
                
                # Generate response using comprehensive RAG
                response = self.generate_comprehensive_response(query, relevant_docs)
                
                # Calculate statistics
                graph_enhanced_count = sum(1 for doc in relevant_docs if doc.get('graph_boost'))
                
                result = {
                    "response": response,
                    "sources": relevant_docs,
                    "query": query,
                    "search_method": "graph_rag",
                    "graph_stats": {
                        "total_results": len(relevant_docs),
                        "graph_enhanced": graph_enhanced_count,
                        "vector_only": len(relevant_docs) - graph_enhanced_count,
                        "query_entities": relevant_docs[0].get('graph_context', {}).get('query_entities', []) if relevant_docs else []
                    }
                }
            
            # Cache result
            cache.set(cache_key, result, self.comprehensive_cache_ttl)
            
            # Save to history
            if user:
                from ..models import QueryHistory
                QueryHistory.objects.create(
                    query=query,
                    response=result.get('response', ''),
                    sources=relevant_docs,
                    query_type='graph_rag',
                    user=user
                )
            
            logger.info(f"Graph RAG complete: {len(relevant_docs)} sources, "
                       f"{result['graph_stats'].get('graph_enhanced', 0)} graph-enhanced")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in graph RAG query: {e}", exc_info=True)
            return {
                "response": f"I encountered an error: {str(e)}",
                "sources": [],
                "query": query,
                "search_method": "error",
                "graph_stats": {"error": str(e)}
            }


# Global Graph RAG service instance
graph_rag_service = GraphRAGService()

