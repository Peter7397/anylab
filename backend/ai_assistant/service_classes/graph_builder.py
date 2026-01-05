"""
Graph Builder Service for Neo4j

Builds and maintains the knowledge graph by creating nodes and relationships
from extracted entities and documents.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from django.utils import timezone

from .neo4j_service import get_neo4j_service
from .graph_entity_extractor import GraphEntityExtractor, ExtractedEntity
from ..models import UploadedFile, DocumentFile, DocumentChunk
from ..rag_service import EnhancedRAGService

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Service for building and maintaining the Neo4j knowledge graph"""
    
    def __init__(
        self,
        neo4j_service: Optional[Any] = None,
        entity_extractor: Optional[Any] = None,
        rag_service: Optional[Any] = None
    ):
        """
        Initialize graph builder with dependency injection
        
        Args:
            neo4j_service: Optional Neo4jService instance (for testing)
            entity_extractor: Optional GraphEntityExtractor instance (for testing)
            rag_service: Optional RAGService instance (for testing)
        """
        # Dependency injection: Use provided services or defaults
        self.neo4j = neo4j_service or get_neo4j_service()
        self.entity_extractor = entity_extractor or GraphEntityExtractor()
        self.rag_service = rag_service or EnhancedRAGService()  # For generating embeddings
        logger.info("GraphBuilder initialized with embedding support")
    
    def build_graph_from_document(self, uploaded_file: UploadedFile, chunks: List[DocumentChunk] = None) -> Dict[str, Any]:
        """
        Build graph nodes and relationships from a document
        
        Args:
            uploaded_file: UploadedFile instance
            chunks: Optional list of DocumentChunk instances
            
        Returns:
            Dictionary with build statistics
        """
        try:
            logger.info(f"Building graph for document: {uploaded_file.filename}")
            
            # Get document content from chunks
            if chunks is None:
                chunks = DocumentChunk.objects.filter(uploaded_file=uploaded_file)
            
            # Combine chunk content
            content = "\n\n".join([chunk.content for chunk in chunks])
            
            if not content.strip():
                logger.warning(f"No content found for document {uploaded_file.id}")
                return {'success': False, 'error': 'No content found'}
            
            # Create document node
            document_node_id = self._create_document_node(uploaded_file)
            
            # Extract entities (now includes concepts and important information)
            entities = self.entity_extractor.extract_entities(
                content, 
                document_id=str(uploaded_file.id)
            )
            
            # Calculate importance scores for chunks
            chunk_importance = self._calculate_chunk_importance(chunks, entities)
            
            # Create entity nodes and relationships
            entity_nodes_created = 0
            relationships_created = 0
            
            for entity in entities:
                # Create or get entity node
                entity_node_id = self._create_or_get_entity_node(entity)
                entity_nodes_created += 1
                
                # Create CONTAINS relationship
                if self._create_contains_relationship(document_node_id, entity_node_id, entity):
                    relationships_created += 1
            
            # Link entities together
            entity_links = self.entity_extractor.link_entities(entities)
            for entity_id, related_ids in entity_links.items():
                for related_id in related_ids:
                    if self._create_entity_relationship(entity_id, related_id):
                        relationships_created += 1
            
            # Create document relationships (if metadata has related_documents)
            if hasattr(uploaded_file, 'document_files'):
                doc_files = uploaded_file.document_files.all()
                for doc_file in doc_files:
                    if doc_file.metadata and isinstance(doc_file.metadata, dict):
                        related_docs = doc_file.metadata.get('related_documents', [])
                        for related_doc_id in related_docs:
                            self._create_document_relationship(document_node_id, str(related_doc_id))
            
            stats = {
                'success': True,
                'document_node_id': document_node_id,
                'entities_extracted': len(entities),
                'entity_nodes_created': entity_nodes_created,
                'relationships_created': relationships_created,
            }
            
            logger.info(f"Graph built for {uploaded_file.filename}: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error building graph for document {uploaded_file.id}: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _create_document_node(self, uploaded_file: UploadedFile) -> str:
        """Create or update document node in Neo4j"""
        document_id = str(uploaded_file.id)
        
        query = """
        MERGE (d:Document {id: $document_id})
        ON CREATE SET
            d.title = $title,
            d.filename = $filename,
            d.type = $type,
            d.file_hash = $file_hash,
            d.file_size = $file_size,
            d.page_count = $page_count,
            d.uploaded_at = $uploaded_at,
            d.processing_status = $processing_status,
            d.created = $created_at
        ON MATCH SET
            d.title = $title,
            d.filename = $filename,
            d.processing_status = $processing_status,
            d.updated = $updated_at
        RETURN d.id AS id
        """
        
        try:
            now = datetime.now().isoformat()
            uploaded_at_str = uploaded_file.uploaded_at.isoformat() if uploaded_file.uploaded_at else now
            
            result = self.neo4j.execute_query(query, {
                'document_id': document_id,
                'title': uploaded_file.filename,
                'filename': uploaded_file.filename,
                'type': 'document',
                'file_hash': uploaded_file.file_hash or '',
                'file_size': uploaded_file.file_size or 0,
                'page_count': uploaded_file.page_count or 0,
                'uploaded_at': uploaded_at_str,
                'processing_status': uploaded_file.processing_status or 'unknown',
                'created_at': uploaded_at_str,
                'updated_at': now,
            })
            
            if result:
                return result[0]['id']
            return document_id
            
        except Exception as e:
            logger.error(f"Error creating document node: {e}")
            return document_id
    
    def _create_or_get_entity_node(self, entity: ExtractedEntity) -> str:
        """Create or get entity node in Neo4j with embedding"""
        entity_id = self.entity_extractor._generate_entity_id(entity)
        
        # Generate embedding for entity (for semantic similarity search)
        embedding = None
        try:
            # Use entity text for embedding (includes context for better semantic matching)
            embedding_text = entity.text
            if entity.context:
                # Include context for better semantic understanding
                embedding_text = f"{entity.text} {entity.context[:200]}"
            
            embedding = self.rag_service.get_embedding_from_ollama(embedding_text)
            logger.debug(f"Generated embedding for entity: {entity.text[:50]}...")
        except Exception as e:
            logger.warning(f"Failed to generate embedding for entity {entity.text[:50]}: {e}")
            # Continue without embedding - entity will still be created
        
        query = """
        MERGE (e:Entity {id: $entity_id})
        ON CREATE SET
            e.name = $name,
            e.normalized_name = $normalized_name,
            e.type = $type,
            e.confidence = $confidence,
            e.created = $created_at,
            e.occurrence_count = 1,
            e.embedding = CASE WHEN $embedding IS NOT NULL THEN $embedding ELSE e.embedding END
        ON MATCH SET
            e.name = $name,
            e.normalized_name = $normalized_name,
            e.type = $type,
            e.occurrence_count = COALESCE(e.occurrence_count, 0) + 1,
            e.updated = $updated_at,
            e.embedding = CASE WHEN $embedding IS NOT NULL THEN $embedding ELSE e.embedding END
        RETURN e.id AS id
        """
        
        try:
            now = datetime.now().isoformat()
            result = self.neo4j.execute_query(query, {
                'entity_id': entity_id,
                'name': entity.text,
                'normalized_name': entity.normalized_text,
                'type': entity.entity_type,
                'confidence': entity.confidence,
                'created_at': now,
                'updated_at': now,
                'embedding': embedding,  # Store as array property in Neo4j
            })
            
            if result:
                return result[0]['id']
            return entity_id
            
        except Exception as e:
            logger.error(f"Error creating entity node: {e}")
            return entity_id
    
    def _create_contains_relationship(self, document_id: str, entity_id: str, entity: ExtractedEntity) -> bool:
        """Create CONTAINS relationship between document and entity"""
        query = """
        MATCH (d:Document {id: $document_id})
        MATCH (e:Entity {id: $entity_id})
        MERGE (d)-[r:CONTAINS]->(e)
        ON CREATE SET
            r.confidence = $confidence,
            r.context = $context,
            r.created = datetime()
        ON MATCH SET
            r.confidence = CASE 
                WHEN $confidence > r.confidence THEN $confidence 
                ELSE r.confidence 
            END,
            r.occurrence_count = COALESCE(r.occurrence_count, 0) + 1,
            r.updated = datetime()
        RETURN r
        """
        
        try:
            result = self.neo4j.execute_query(query, {
                'document_id': document_id,
                'entity_id': entity_id,
                'confidence': entity.confidence,
                'context': entity.context[:500],  # Limit context length
            })
            return len(result) > 0
            
        except Exception as e:
            logger.error(f"Error creating CONTAINS relationship: {e}")
            return False
    
    def _create_entity_relationship(self, entity_id: str, related_entity_id: str, relationship_type: str = 'RELATED_TO') -> bool:
        """Create relationship between entities"""
        query = f"""
        MATCH (e1:Entity {{id: $entity_id}})
        MATCH (e2:Entity {{id: $related_entity_id}})
        WHERE e1 <> e2
        MERGE (e1)-[r:{relationship_type}]->(e2)
        ON CREATE SET
            r.co_occurrence_count = 1,
            r.created = datetime()
        ON MATCH SET
            r.co_occurrence_count = COALESCE(r.co_occurrence_count, 0) + 1,
            r.updated = datetime()
        RETURN r
        """
        
        try:
            result = self.neo4j.execute_query(query, {
                'entity_id': entity_id,
                'related_entity_id': related_entity_id,
            })
            return len(result) > 0
            
        except Exception as e:
            logger.error(f"Error creating entity relationship: {e}")
            return False
    
    def _create_document_relationship(self, document_id: str, related_document_id: str) -> bool:
        """Create relationship between documents"""
        query = """
        MATCH (d1:Document {id: $document_id})
        MATCH (d2:Document {id: $related_document_id})
        WHERE d1 <> d2
        MERGE (d1)-[r:RELATED_TO]->(d2)
        ON CREATE SET r.created = datetime()
        RETURN r
        """
        
        try:
            result = self.neo4j.execute_query(query, {
                'document_id': document_id,
                'related_document_id': related_document_id,
            })
            return len(result) > 0
            
        except Exception as e:
            logger.error(f"Error creating document relationship: {e}")
            return False
    
    def _calculate_chunk_importance(self, chunks: List[DocumentChunk], entities: List) -> Dict[int, float]:
        """
        Calculate importance scores for chunks based on:
        1. Presence of important entities (concepts, key terms, important info)
        2. Position in document (introduction/conclusion often more important)
        3. Section headers and key phrases
        4. Length and content quality
        """
        chunk_scores = {}
        
        if not chunks:
            return chunk_scores
        
        # Create entity position map
        entity_positions = {}
        for entity in entities:
            entity_type = entity.entity_type
            importance = entity.confidence
            
            # Higher importance for conceptual entities
            if entity_type in ['CONCEPT', 'KEY_TERM', 'IMPORTANT_INFO', 'KEY_POINT']:
                importance *= 1.5
            
            # Map entity positions to chunks
            for chunk in chunks:
                chunk_start = getattr(chunk, 'start_pos', 0)
                chunk_end = chunk_start + len(chunk.content)
                
                if entity.start_pos >= chunk_start and entity.end_pos <= chunk_end:
                    if chunk.id not in chunk_scores:
                        chunk_scores[chunk.id] = 0.0
                    chunk_scores[chunk.id] += importance
        
        # Boost scores for chunks in important positions
        total_chunks = len(chunks)
        for idx, chunk in enumerate(chunks):
            if chunk.id not in chunk_scores:
                chunk_scores[chunk.id] = 0.5  # Base score
            
            # Boost for introduction (first 10% of chunks)
            if idx < total_chunks * 0.1:
                chunk_scores[chunk.id] += 0.2
            
            # Boost for conclusion (last 10% of chunks)
            if idx >= total_chunks * 0.9:
                chunk_scores[chunk.id] += 0.2
            
            # Boost for chunks with section headers
            content_lower = chunk.content.lower()
            if any(keyword in content_lower for keyword in ['summary', 'conclusion', 'overview', 'key point']):
                chunk_scores[chunk.id] += 0.3
        
        # Normalize scores to 0-1 range
        if chunk_scores:
            max_score = max(chunk_scores.values())
            if max_score > 0:
                chunk_scores = {k: min(v / max_score, 1.0) for k, v in chunk_scores.items()}
        
        logger.info(f"Calculated importance scores for {len(chunk_scores)} chunks")
        return chunk_scores
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph"""
        return self.neo4j.get_graph_stats()

