"""
Graphic RAG Service
Provides visual search capabilities using image embeddings
"""
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from django.db import connection
from django.core.cache import cache
from .visual_embedding import get_visual_embedding_service

logger = logging.getLogger(__name__)


class GraphicRAGService:
    """
    Service for visual/Graphic RAG search
    
    Combines:
    - Text embeddings (from OCR)
    - Visual embeddings (from CLIP/vision models)
    - Hybrid search for best results
    """
    
    def __init__(self, visual_embedding_service=None):
        """
        Initialize Graphic RAG service
        
        Args:
            visual_embedding_service: Optional VisualEmbeddingService instance
        """
        self.visual_embedding_service = visual_embedding_service or get_visual_embedding_service()
    
    def search_by_image(
        self,
        image_path: str,
        top_k: int = 10,
        similarity_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Search for similar images using visual embeddings
        
        Args:
            image_path: Path to query image
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of similar image documents
        """
        try:
            # Generate query visual embedding
            query_embedding = self.visual_embedding_service.get_embedding_from_image(image_path)
            if not query_embedding:
                logger.error("Failed to generate visual embedding for query image")
                return []
            
            # Search for similar visual embeddings
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT dc.id, dc.content, dc.uploaded_file_id, dc.page_number, dc.chunk_index,
                           COALESCE(uf.filename, 'Unknown Document') as filename,
                           dc.visual_embedding <=> %s::vector AS similarity
                    FROM ai_assistant_documentchunk dc
                    LEFT JOIN ai_assistant_uploadedfile uf ON dc.uploaded_file_id = uf.id
                    WHERE dc.visual_embedding IS NOT NULL
                      AND dc.has_visual_content = TRUE
                    ORDER BY dc.visual_embedding <=> %s::vector
                    LIMIT %s;
                """, [query_embedding, query_embedding, top_k])
                results = cursor.fetchall()
            
            # Format results
            formatted_results = []
            for row in results:
                similarity = 1.0 - float(row[6])  # Convert distance to similarity
                if similarity >= similarity_threshold:
                    formatted_results.append({
                        "id": row[0],
                        "content": row[1],
                        "uploaded_file_id": row[2],
                        "page_number": row[3],
                        "chunk_index": row[4],
                        "filename": row[5],
                        "similarity": similarity,
                        "type": "visual"
                    })
            
            logger.info(f"Found {len(formatted_results)} visually similar images")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in visual search: {e}")
            return []
    
    def hybrid_search(
        self,
        query_text: str,
        query_image_path: Optional[str] = None,
        top_k: int = 10,
        text_weight: float = 0.6,
        visual_weight: float = 0.4
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining text and visual embeddings
        
        Args:
            query_text: Text query
            query_image_path: Optional image query
            top_k: Number of results
            text_weight: Weight for text similarity (0-1)
            visual_weight: Weight for visual similarity (0-1)
            
        Returns:
            List of hybrid search results
        """
        from ..rag_service import EnhancedRAGService
        
        results = []
        
        # Text search
        if query_text:
            rag_service = EnhancedRAGService()
            text_embedding = rag_service.get_embedding_from_ollama(query_text)
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT dc.id, dc.content, dc.uploaded_file_id, dc.page_number,
                           COALESCE(uf.filename, 'Unknown') as filename,
                           dc.embedding <=> %s::vector AS text_similarity
                    FROM ai_assistant_documentchunk dc
                    LEFT JOIN ai_assistant_uploadedfile uf ON dc.uploaded_file_id = uf.id
                    WHERE dc.embedding IS NOT NULL
                    ORDER BY dc.embedding <=> %s::vector
                    LIMIT %s;
                """, [text_embedding, text_embedding, top_k * 2])
                text_results = cursor.fetchall()
            
            for row in text_results:
                text_sim = 1.0 - float(row[5])
                results.append({
                    "id": row[0],
                    "content": row[1],
                    "uploaded_file_id": row[2],
                    "page_number": row[3],
                    "filename": row[4],
                    "text_similarity": text_sim,
                    "visual_similarity": 0.0,
                    "combined_score": text_sim * text_weight
                })
        
        # Visual search
        if query_image_path:
            visual_results = self.search_by_image(query_image_path, top_k=top_k * 2)
            
            # Merge with text results
            result_map = {r["id"]: r for r in results}
            
            for visual_result in visual_results:
                chunk_id = visual_result["id"]
                if chunk_id in result_map:
                    # Combine scores
                    result_map[chunk_id]["visual_similarity"] = visual_result["similarity"]
                    result_map[chunk_id]["combined_score"] = (
                        result_map[chunk_id].get("text_similarity", 0.0) * text_weight +
                        visual_result["similarity"] * visual_weight
                    )
                else:
                    # Add new visual-only result
                    results.append({
                        **visual_result,
                        "text_similarity": 0.0,
                        "combined_score": visual_result["similarity"] * visual_weight
                    })
        
        # Sort by combined score and return top_k
        results.sort(key=lambda x: x.get("combined_score", 0.0), reverse=True)
        return results[:top_k]

