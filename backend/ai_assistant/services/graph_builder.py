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

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Service for building and maintaining the Neo4j knowledge graph"""
    
    def __init__(self):
        """Initialize graph builder"""
        self.neo4j = get_neo4j_service()
        self.entity_extractor = GraphEntityExtractor()
        logger.info("GraphBuilder initialized")
    
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
            
            # Extract entities
            entities = self.entity_extractor.extract_entities(
                content, 
                document_id=str(uploaded_file.id)
            )
            
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
        """Create or get entity node in Neo4j"""
        entity_id = self.entity_extractor._generate_entity_id(entity)
        
        query = """
        MERGE (e:Entity {id: $entity_id})
        ON CREATE SET
            e.name = $name,
            e.normalized_name = $normalized_name,
            e.type = $type,
            e.confidence = $confidence,
            e.created = $created_at,
            e.occurrence_count = 1
        ON MATCH SET
            e.name = $name,
            e.normalized_name = $normalized_name,
            e.type = $type,
            e.occurrence_count = COALESCE(e.occurrence_count, 0) + 1,
            e.updated = $updated_at
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
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph"""
        return self.neo4j.get_graph_stats()

