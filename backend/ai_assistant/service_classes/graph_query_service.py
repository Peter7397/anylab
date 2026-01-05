"""
Graph Query Service for Neo4j

Provides graph-based query capabilities for entity traversal and relationship discovery.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Set
from typing import Optional, Any
from .neo4j_service import get_neo4j_service
from .graph_entity_extractor import GraphEntityExtractor
from ..rag_service import EnhancedRAGService

logger = logging.getLogger(__name__)


class GraphQueryService:
    """Service for querying the knowledge graph"""
    
    def __init__(
        self,
        neo4j_service: Optional[Any] = None,
        entity_extractor: Optional[Any] = None,
        rag_service: Optional[Any] = None
    ):
        """
        Initialize graph query service with dependency injection
        
        Args:
            neo4j_service: Optional Neo4jService instance (for testing)
            entity_extractor: Optional GraphEntityExtractor instance (for testing)
            rag_service: Optional RAGService instance (for testing)
        """
        # Dependency injection: Use provided services or defaults
        self.neo4j = neo4j_service or get_neo4j_service()
        self.entity_extractor = entity_extractor or GraphEntityExtractor()
        self.rag_service = rag_service or EnhancedRAGService()  # For generating query embeddings
        logger.info("GraphQueryService initialized with embedding support")
    
    def find_documents_by_entities(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Find documents by extracting entities and concepts from query and traversing graph
        Now includes semantic similarity search using entity embeddings
        
        Args:
            query: User query text
            max_results: Maximum number of documents to return
            
        Returns:
            List of document information with relevance scores
        """
        try:
            # Extract entities from query (now includes concepts and important info)
            entities = self.entity_extractor.extract_entities(query)
            
            # Also find semantically similar entities using embeddings
            similar_entities = self._find_similar_entities_by_embedding(query, max_similar=10)
            
            # Combine exact matches and semantic matches
            all_entity_ids = set()
            if entities:
                for entity in entities:
                    entity_id = self.entity_extractor._generate_entity_id(entity)
                    all_entity_ids.add(entity_id)
            
            # Add semantically similar entities
            for similar_entity in similar_entities:
                all_entity_ids.add(similar_entity.get('entity_id'))
            
            if not all_entity_ids:
                logger.info("No entities found in query for graph search")
                # Try semantic search as fallback
                return self._find_documents_by_semantic_similarity(query, max_results)
            
            logger.info(f"Found {len(entities)} exact entities and {len(similar_entities)} similar entities in query")
            
            # Find documents containing these entities
            document_scores = {}
            
            for entity_id in all_entity_ids:
                # Query graph for documents containing this entity
                query_str = """
                MATCH (d:Document)-[r:CONTAINS]->(e:Entity {id: $entity_id})
                RETURN d.id AS document_id, 
                       d.filename AS filename,
                       d.title AS title,
                       r.confidence AS confidence,
                       e.name AS entity_name,
                       e.type AS entity_type
                """
                
                results = self.neo4j.execute_query(query_str, {
                    'entity_id': entity_id
                })
                
                # Score documents (higher score for more entity matches, higher confidence)
                for result in results:
                    doc_id = result['document_id']
                    if doc_id not in document_scores:
                        document_scores[doc_id] = {
                            'document_id': doc_id,
                            'filename': result.get('filename', 'Unknown'),
                            'title': result.get('title', result.get('filename', 'Unknown')),
                            'score': 0.0,
                            'matched_entities': [],
                            'entity_count': 0
                        }
                    
                    # Check if this is a semantic match (not exact)
                    is_semantic_match = entity_id in [se.get('entity_id') for se in similar_entities]
                    similarity_score = next((se.get('similarity', 0.5) for se in similar_entities if se.get('entity_id') == entity_id), 1.0)
                    
                    # Add entity match
                    document_scores[doc_id]['matched_entities'].append({
                        'name': result.get('entity_name'),
                        'type': result.get('entity_type'),
                        'confidence': result.get('confidence', 0.5),
                        'semantic_match': is_semantic_match,
                        'similarity': similarity_score
                    })
                    
                    # Update score (weighted by confidence and entity type importance)
                    entity_weight = self._get_entity_weight(result.get('entity_type', ''))
                    confidence = result.get('confidence', 0.5)
                    
                    # Boost score for important entity types (concepts, key terms, important info)
                    importance_boost = 1.0
                    entity_type = result.get('entity_type', '')
                    if entity_type in ['CONCEPT', 'KEY_TERM', 'IMPORTANT_INFO', 'KEY_POINT']:
                        importance_boost = 1.5  # 50% boost for conceptual matches
                    
                    # Apply similarity score for semantic matches (reduce weight slightly)
                    similarity_multiplier = similarity_score if is_semantic_match else 1.0
                    if is_semantic_match:
                        similarity_multiplier *= 0.8  # Slightly reduce weight for semantic matches
                    
                    document_scores[doc_id]['score'] += entity_weight * confidence * importance_boost * similarity_multiplier
                    document_scores[doc_id]['entity_count'] += 1
            
            # Get related documents via graph traversal (2-hop)
            if entities:
                graph_documents = self._find_related_documents_via_graph(entities, max_results * 2)
                
                # Merge with entity-based results
                for doc_id, doc_info in graph_documents.items():
                    if doc_id not in document_scores:
                        document_scores[doc_id] = doc_info
                    else:
                        # Boost score for graph-connected documents
                        document_scores[doc_id]['score'] += doc_info.get('score', 0) * 0.5
            
            # Sort by score and return top results
            sorted_docs = sorted(
                document_scores.values(),
                key=lambda x: x['score'],
                reverse=True
            )[:max_results]
            
            logger.info(f"Graph search found {len(sorted_docs)} documents ({len([e for e in all_entity_ids if e in [se.get('entity_id') for se in similar_entities]])} semantic matches)")
            return sorted_docs
            
        except Exception as e:
            logger.error(f"Error in graph-based document search: {e}", exc_info=True)
            # Check if it's a connection error - provide better error message
            from .neo4j_service import Neo4jConnectionError
            if isinstance(e, Neo4jConnectionError):
                logger.warning("Graph search unavailable - Neo4j connection failed, falling back to vector search only")
            return []
    
    def _find_related_documents_via_graph(self, entities: List, max_results: int = 20) -> Dict[str, Dict[str, Any]]:
        """
        Find related documents by traversing the graph (2-hop)
        
        Finds documents that:
        1. Share entities with query entities (co-occurrence)
        2. Are connected via entity relationships
        """
        document_scores = {}
        
        try:
            # Get entity IDs
            entity_ids = [self.entity_extractor._generate_entity_id(e) for e in entities]
            
            if not entity_ids:
                return document_scores
            
            # Find documents via entity co-occurrence
            query_str = """
            MATCH (qEntity:Entity)
            WHERE qEntity.id IN $entity_ids
            MATCH (qEntity)<-[:CONTAINS]-(doc1:Document)-[:CONTAINS]->(sharedEntity:Entity)<-[:CONTAINS]-(doc2:Document)
            WHERE doc2.id <> doc1.id
            RETURN DISTINCT doc2.id AS document_id,
                   doc2.filename AS filename,
                   doc2.title AS title,
                   count(DISTINCT sharedEntity) AS shared_entity_count
            ORDER BY shared_entity_count DESC
            LIMIT $max_results
            """
            
            results = self.neo4j.execute_query(query_str, {
                'entity_ids': entity_ids,
                'max_results': max_results
            })
            
            for result in results:
                doc_id = str(result['document_id'])
                document_scores[doc_id] = {
                    'document_id': doc_id,
                    'filename': result.get('filename', 'Unknown'),
                    'title': result.get('title', result.get('filename', 'Unknown')),
                    'score': result.get('shared_entity_count', 0) * 0.3,  # Lower weight for indirect matches
                    'matched_entities': [],
                    'entity_count': 0,
                    'graph_connected': True
                }
            
        except Exception as e:
            logger.error(f"Error finding related documents via graph: {e}")
        
        return document_scores
    
    def _get_entity_weight(self, entity_type: str) -> float:
        """Get weight for entity type (higher = more important)"""
        weights = {
            # High importance: concepts and key information
            'IMPORTANT_INFO': 1.2,
            'KEY_POINT': 1.1,
            'CONCEPT': 1.0,
            'KEY_TERM': 1.0,
            'TOPIC': 0.95,
            'PROCEDURE': 0.9,
            # Medium-high: domain-specific entities
            'PRODUCT': 1.0,
            'ERROR_CODE': 0.9,
            'VERSION': 0.8,
            'PROBLEM': 0.7,
            'SOLUTION': 0.7,
            'SOFTWARE': 0.6,
            'CATEGORY': 0.5,
        }
        return weights.get(entity_type, 0.5)
    
    def _find_similar_entities_by_embedding(self, query: str, max_similar: int = 10, similarity_threshold: float = 0.6) -> List[Dict[str, Any]]:
        """
        Find entities similar to query using embedding cosine similarity
        
        Optimized to:
        1. Try Neo4j vector index if available (5.11+)
        2. Limit entity loading to reduce memory usage
        3. Use efficient similarity calculation
        
        Args:
            query: User query text
            max_similar: Maximum number of similar entities to return
            similarity_threshold: Minimum cosine similarity (0-1)
            
        Returns:
            List of similar entities with similarity scores
        """
        from .utils.rag_constants import GRAPH_ENTITY_SIMILARITY_THRESHOLD, GRAPH_MAX_SIMILAR_ENTITIES
        
        try:
            # Generate query embedding
            query_embedding = self.rag_service.get_embedding_from_ollama(query)
            
            # Try vector index search first (Neo4j 5.11+)
            vector_index_results = self._try_vector_index_search(query_embedding, max_similar, similarity_threshold)
            if vector_index_results:
                logger.info(f"Found {len(vector_index_results)} entities using vector index")
                return vector_index_results
            
            # Fallback to optimized Python-based similarity search
            return self._python_similarity_search(query_embedding, max_similar, similarity_threshold)
            
        except Exception as e:
            logger.error(f"Error finding similar entities by embedding: {e}")
            return []
    
    def _try_vector_index_search(self, query_embedding: List[float], max_similar: int, threshold: float) -> List[Dict[str, Any]]:
        """Try to use Neo4j vector index for similarity search"""
        try:
            # Neo4j 5.11+ vector index query
            query_str = """
            CALL db.index.vector.queryNodes('entity_embedding_vector', $top_k, $query_embedding)
            YIELD node, score
            WHERE score >= $threshold
            RETURN node.id AS entity_id,
                   node.name AS name,
                   node.type AS type,
                   score AS similarity
            ORDER BY score DESC
            LIMIT $max_similar
            """
            
            # Request more candidates to filter by threshold
            top_k = max_similar * 3  # Get 3x candidates for threshold filtering
            
            results = self.neo4j.execute_query(query_str, {
                'query_embedding': query_embedding,
                'top_k': top_k,
                'threshold': threshold,
                'max_similar': max_similar
            })
            
            if results:
                return [
                    {
                        'entity_id': r.get('entity_id'),
                        'name': r.get('name'),
                        'type': r.get('type'),
                        'similarity': float(r.get('similarity', 0))
                    }
                    for r in results
                ]
        except Exception as e:
            logger.debug(f"Vector index search not available: {e}")
        
        return []
    
    def _python_similarity_search(self, query_embedding: List[float], max_similar: int, threshold: float) -> List[Dict[str, Any]]:
        """Python-based similarity search with optimized entity loading"""
        from .utils.rag_constants import GRAPH_MAX_SIMILAR_ENTITIES
        
        # Limit entity loading - only get entities with embeddings, prioritize by type
        # Load fewer entities but smarter selection
        max_entities_to_load = min(500, max_similar * 50)  # Reduced from 1000
        
        query_str = """
        MATCH (e:Entity)
        WHERE e.embedding IS NOT NULL
        WITH e
        ORDER BY 
            CASE e.type
                WHEN 'CONCEPT' THEN 1
                WHEN 'KEY_TERM' THEN 2
                WHEN 'IMPORTANT_INFO' THEN 3
                WHEN 'KEY_POINT' THEN 4
                ELSE 5
            END,
            e.occurrence_count DESC
        RETURN e.id AS entity_id,
               e.name AS name,
               e.type AS type,
               e.embedding AS embedding
        LIMIT $limit
        """
        
        entities = self.neo4j.execute_query(query_str, {'limit': max_entities_to_load})
        
        if not entities:
            logger.debug("No entities with embeddings found")
            return []
        
        # Calculate cosine similarity efficiently using numpy
        similar_entities = []
        query_vec = np.array(query_embedding, dtype=np.float32)
        query_norm = np.linalg.norm(query_vec)
        
        if query_norm == 0:
            return []
        
        # Batch process entities for better performance
        entity_vectors = []
        entity_metadata = []
        
        for entity in entities:
            entity_embedding = entity.get('embedding')
            if not entity_embedding:
                continue
            
            try:
                entity_vec = np.array(entity_embedding, dtype=np.float32)
                entity_norm = np.linalg.norm(entity_vec)
                
                if entity_norm > 0:
                    entity_vectors.append(entity_vec)
                    entity_metadata.append({
                        'entity_id': entity.get('entity_id'),
                        'name': entity.get('name'),
                        'type': entity.get('type'),
                        'norm': entity_norm
                    })
            except Exception as e:
                logger.debug(f"Error processing entity {entity.get('name')}: {e}")
                continue
        
        if not entity_vectors:
            return []
        
        # Batch calculate similarities
        entity_matrix = np.array(entity_vectors)
        similarities = np.dot(entity_matrix, query_vec) / (np.array([m['norm'] for m in entity_metadata]) * query_norm)
        
        # Filter by threshold and sort
        for idx, similarity in enumerate(similarities):
            if similarity >= threshold:
                similar_entities.append({
                    'entity_id': entity_metadata[idx]['entity_id'],
                    'name': entity_metadata[idx]['name'],
                    'type': entity_metadata[idx]['type'],
                    'similarity': float(similarity)
                })
        
        # Sort by similarity and return top results
        similar_entities.sort(key=lambda x: x['similarity'], reverse=True)
        
        logger.info(f"Found {len(similar_entities)} entities similar to query (threshold: {threshold}, loaded: {len(entities)})")
        return similar_entities[:max_similar]
    
    def _find_documents_by_semantic_similarity(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Fallback: Find documents using semantic similarity when no entities found
        
        This uses the vector embeddings to find semantically similar content
        """
        try:
            # Use vector search to find similar chunks
            from ..models import DocumentChunk
            from django.db.models import Q
            import numpy as np
            
            # Get query embedding (simplified - in production, use proper embedding service)
            # For now, we'll use a text-based similarity approach
            query_lower = query.lower()
            query_terms = set(query_lower.split())
            
            # Find chunks with high term overlap
            all_chunks = DocumentChunk.objects.filter(
                uploaded_file__isnull=False
            ).select_related('uploaded_file')[:1000]  # Limit for performance
            
            scored_chunks = []
            for chunk in all_chunks:
                chunk_lower = chunk.content.lower()
                chunk_terms = set(chunk_lower.split())
                
                # Calculate term overlap
                overlap = len(query_terms & chunk_terms)
                if overlap > 0:
                    score = overlap / max(len(query_terms), 1)
                    scored_chunks.append({
                        'document_id': str(chunk.uploaded_file_id),
                        'filename': chunk.uploaded_file.filename,
                        'score': score,
                        'matched_entities': [],
                        'entity_count': overlap
                    })
            
            # Group by document and aggregate scores
            doc_scores = {}
            for item in scored_chunks:
                doc_id = item['document_id']
                if doc_id not in doc_scores:
                    doc_scores[doc_id] = item
                else:
                    doc_scores[doc_id]['score'] += item['score']
                    doc_scores[doc_id]['entity_count'] += item['entity_count']
            
            # Sort and return top results
            sorted_docs = sorted(
                doc_scores.values(),
                key=lambda x: x['score'],
                reverse=True
            )[:max_results]
            
            logger.info(f"Semantic similarity search found {len(sorted_docs)} documents")
            return sorted_docs
            
        except Exception as e:
            logger.error(f"Error in semantic similarity search: {e}")
            return []
    
    def get_entity_context(self, entities: List, max_context: int = 5) -> Dict[str, Any]:
        """
        Get contextual information about entities from graph
        
        Returns relationships and co-occurrences
        """
        try:
            entity_ids = [self.entity_extractor._generate_entity_id(e) for e in entities]
            
            if not entity_ids:
                return {'relationships': [], 'co_occurrences': []}
            
            # Find entity relationships
            rel_query = """
            MATCH (e1:Entity)-[r:RELATED_TO]->(e2:Entity)
            WHERE e1.id IN $entity_ids OR e2.id IN $entity_ids
            RETURN e1.name AS entity1, 
                   e1.type AS type1,
                   e2.name AS entity2,
                   e2.type AS type2,
                   r.co_occurrence_count AS co_occurrence
            ORDER BY r.co_occurrence_count DESC
            LIMIT $max_context
            """
            
            relationships = self.neo4j.execute_query(rel_query, {
                'entity_ids': entity_ids,
                'max_context': max_context * 2
            })
            
            # Find co-occurring entities
            co_occ_query = """
            MATCH (e:Entity)
            WHERE e.id IN $entity_ids
            MATCH (d:Document)-[:CONTAINS]->(e)
            MATCH (d)-[:CONTAINS]->(co:Entity)
            WHERE NOT co.id IN $entity_ids
            RETURN DISTINCT co.name AS name,
                   co.type AS type,
                   count(DISTINCT d) AS document_count
            ORDER BY document_count DESC
            LIMIT $max_context
            """
            
            co_occurrences = self.neo4j.execute_query(co_occ_query, {
                'entity_ids': entity_ids,
                'max_context': max_context
            })
            
            return {
                'relationships': relationships,
                'co_occurrences': co_occurrences
            }
            
        except Exception as e:
            logger.error(f"Error getting entity context: {e}")
            return {'relationships': [], 'co_occurrences': []}
    
    def get_shortest_paths_between_query_entities(self, entities: List, max_paths: int = 5) -> List[Dict[str, Any]]:
        """
        Find shortest paths between entities mentioned in the query.
        Returns a list of paths with node names/types and relationship types.
        """
        try:
            entity_ids = [self.entity_extractor._generate_entity_id(e) for e in entities]
            if len(entity_ids) < 2:
                return []
            
            cypher = """
            MATCH (e1:Entity), (e2:Entity)
            WHERE e1.id IN $entity_ids AND e2.id IN $entity_ids AND e1 <> e2
            CALL algo.shortestPath.stream(e1, e2, null) YIELD nodeId, cost
            RETURN nodes(algo.getPath(nodeId)) AS nodes, relationships(algo.getPath(nodeId)) AS rels
            LIMIT $max_paths
            """
            # Fallback generic path if algo.* not available in community edition
            cypher_fallback = """
            MATCH (e1:Entity),(e2:Entity)
            WHERE e1.id IN $entity_ids AND e2.id IN $entity_ids AND e1 <> e2
            MATCH p = shortestPath((e1)-[*..3]-(e2))
            RETURN nodes(p) AS nodes, relationships(p) AS rels
            LIMIT $max_paths
            """
            try:
                results = self.neo4j.execute_query(cypher, {
                    'entity_ids': entity_ids,
                    'max_paths': max_paths
                })
            except Exception:
                results = self.neo4j.execute_query(cypher_fallback, {
                    'entity_ids': entity_ids,
                    'max_paths': max_paths
                })
            
            paths = []
            for r in results:
                nodes = r.get('nodes', [])
                rels = r.get('rels', [])
                path_repr = {
                    'nodes': [
                        {
                            'name': n.get('name', n.get('title', '')) if isinstance(n, dict) else None,
                            'type': n.get('type', '') if isinstance(n, dict) else ''
                        } for n in nodes
                    ],
                    'relations': [
                        {
                            'type': rel.type if hasattr(rel, 'type') else getattr(rel, 'rel_type', 'RELATED_TO')
                        } for rel in rels
                    ]
                }
                paths.append(path_repr)
            
            return paths
        except Exception as e:
            logger.error(f"Error fetching shortest paths between entities: {e}")
            return []
    
    def find_related_documents(self, document_id: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Find documents related to a given document via shared entities
        """
        try:
            query_str = """
            MATCH (d1:Document {id: $document_id})-[:CONTAINS]->(e:Entity)<-[:CONTAINS]-(d2:Document)
            WHERE d1 <> d2
            RETURN d2.id AS document_id,
                   d2.filename AS filename,
                   d2.title AS title,
                   count(DISTINCT e) AS shared_entities
            ORDER BY shared_entities DESC
            LIMIT $max_results
            """
            
            results = self.neo4j.execute_query(query_str, {
                'document_id': str(document_id),
                'max_results': max_results
            })
            
            return [
                {
                    'document_id': str(r['document_id']),
                    'filename': r.get('filename', 'Unknown'),
                    'title': r.get('title', r.get('filename', 'Unknown')),
                    'shared_entities': r.get('shared_entities', 0)
                }
                for r in results
            ]
            
        except Exception as e:
            logger.error(f"Error finding related documents: {e}")
            return []

