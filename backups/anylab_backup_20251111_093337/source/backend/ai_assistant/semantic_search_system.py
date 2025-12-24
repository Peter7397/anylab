"""
Semantic Search System

This module provides semantic search functionality
including vector similarity search, semantic understanding, and context-aware results.
"""

import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from django.utils import timezone as django_timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)


class SearchType(Enum):
    """Search type enumeration"""
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    VECTOR = "vector"
    CONTEXTUAL = "contextual"
    MULTIMODAL = "multimodal"


class SearchMode(Enum):
    """Search mode enumeration"""
    EXACT = "exact"
    FUZZY = "fuzzy"
    SEMANTIC = "semantic"
    CONTEXTUAL = "contextual"
    SIMILARITY = "similarity"


class SearchResultType(Enum):
    """Search result type enumeration"""
    DOCUMENT = "document"
    CONTENT = "content"
    METADATA = "metadata"
    ENTITY = "entity"
    RELATIONSHIP = "relationship"
    CONCEPT = "concept"
    TOPIC = "topic"


@dataclass
class SearchQuery:
    """Search query structure"""
    id: str
    query_text: str
    search_type: SearchType
    search_mode: SearchMode
    filters: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class SearchResult:
    """Search result structure"""
    id: str
    content_id: str
    title: str
    content: str
    relevance_score: float
    semantic_score: float
    keyword_score: float
    result_type: SearchResultType
    highlights: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class SemanticVector:
    """Semantic vector structure"""
    id: str
    content_id: str
    vector: List[float]
    dimension: int
    model_name: str
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class SearchContext:
    """Search context structure"""
    user_id: str
    session_id: str
    previous_queries: List[str] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    domain_knowledge: Dict[str, Any] = field(default_factory=dict)
    temporal_context: Dict[str, Any] = field(default_factory=dict)
    spatial_context: Dict[str, Any] = field(default_factory=dict)


class SemanticSearchSystem:
    """Semantic Search System"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize semantic search system"""
        self.config = config or {}
        self.search_enabled = self.config.get('search_enabled', True)
        self.semantic_enabled = self.config.get('semantic_enabled', True)
        self.vector_enabled = self.config.get('vector_enabled', True)
        self.cache_enabled = self.config.get('cache_enabled', True)
        self.max_results = self.config.get('max_results', 20)
        self.similarity_threshold = self.config.get('similarity_threshold', 0.7)
        
        # Initialize components
        self.vectors = {}
        self.search_queries = {}
        self.search_results = {}
        self.search_contexts = {}
        self.cache = cache if self.cache_enabled else None
        
        # Initialize search system
        self._initialize_search_system()
        
        logger.info("Semantic Search System initialized")
    
    def _initialize_search_system(self):
        """Initialize search system components"""
        try:
            # Initialize search processors
            self.search_processors = {
                SearchType.SEMANTIC: self._semantic_search,
                SearchType.KEYWORD: self._keyword_search,
                SearchType.HYBRID: self._hybrid_search,
                SearchType.VECTOR: self._vector_search,
                SearchType.CONTEXTUAL: self._contextual_search,
                SearchType.MULTIMODAL: self._multimodal_search
            }
            
            # Initialize vector operations
            self.vector_operations = {
                'cosine_similarity': self._cosine_similarity,
                'euclidean_distance': self._euclidean_distance,
                'dot_product': self._dot_product,
                'manhattan_distance': self._manhattan_distance
            }
            
            # Initialize search modes
            self.search_modes = {
                SearchMode.EXACT: self._exact_search,
                SearchMode.FUZZY: self._fuzzy_search,
                SearchMode.SEMANTIC: self._semantic_search,
                SearchMode.CONTEXTUAL: self._contextual_search,
                SearchMode.SIMILARITY: self._similarity_search
            }
            
            logger.info("Search system components initialized")
            
        except Exception as e:
            logger.error(f"Error initializing search system: {e}")
            raise
    
    def search(self, query_text: str, search_type: SearchType = SearchType.SEMANTIC,
               search_mode: SearchMode = SearchMode.SEMANTIC, 
               filters: Dict[str, Any] = None, context: Dict[str, Any] = None,
               user_id: str = None, session_id: str = None) -> List[SearchResult]:
        """Perform semantic search"""
        try:
            # Check cache first
            if self.cache_enabled:
                cache_key = f"semantic_search_{hash(query_text)}_{hash(str(filters))}_{hash(str(context))}"
                cached_result = self.cache.get(cache_key)
                if cached_result:
                    return cached_result
            
            # Create search query
            query_id = f"search_query_{django_timezone.now().strftime('%Y%m%d_%H%M%S')}_{hash(query_text) % 10000}"
            query = SearchQuery(
                id=query_id,
                query_text=query_text,
                search_type=search_type,
                search_mode=search_mode,
                filters=filters or {},
                context=context or {},
                user_id=user_id,
                session_id=session_id
            )
            
            # Store query
            self.search_queries[query_id] = query
            
            # Get search processor
            processor = self.search_processors.get(search_type)
            if not processor:
                return []
            
            # Perform search
            results = processor(query)
            
            # Store results
            for result in results:
                self.search_results[result.id] = result
            
            # Cache results
            if self.cache_enabled:
                self.cache.set(cache_key, results, timeout=3600)
            
            return results
            
        except Exception as e:
            logger.error(f"Error performing semantic search: {e}")
            return []
    
    def _semantic_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform semantic search"""
        try:
            results = []
            
            # Generate query vector
            query_vector = self._generate_query_vector(query.query_text)
            
            # Search vectors
            for vector_id, vector in self.vectors.items():
                # Calculate similarity
                similarity = self._cosine_similarity(query_vector, vector.vector)
                
                if similarity >= self.similarity_threshold:
                    # Create search result
                    result = SearchResult(
                        id=f"search_result_{vector_id}",
                        content_id=vector.content_id,
                        title=f"Content {vector.content_id}",
                        content=f"Content for {vector.content_id}",
                        relevance_score=similarity,
                        semantic_score=similarity,
                        keyword_score=0.0,
                        result_type=SearchResultType.CONTENT,
                        highlights=self._generate_highlights(query.query_text, f"Content for {vector.content_id}"),
                        metadata={
                            'vector_id': vector_id,
                            'model_name': vector.model_name,
                            'dimension': vector.dimension
                        }
                    )
                    results.append(result)
            
            # Sort by relevance score
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Limit results
            results = results[:self.max_results]
            
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def _keyword_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform keyword search"""
        try:
            results = []
            query_lower = query.query_text.lower()
            query_words = query_lower.split()
            
            # Mock keyword search
            for i in range(10):  # Mock 10 results
                content_id = f"content_{i}"
                title = f"Document {i}"
                content = f"This is document {i} with content about {query.query_text}"
                
                # Calculate keyword score
                keyword_score = self._calculate_keyword_score(query_words, content)
                
                if keyword_score > 0:
                    result = SearchResult(
                        id=f"keyword_result_{i}",
                        content_id=content_id,
                        title=title,
                        content=content,
                        relevance_score=keyword_score,
                        semantic_score=0.0,
                        keyword_score=keyword_score,
                        result_type=SearchResultType.DOCUMENT,
                        highlights=self._generate_highlights(query.query_text, content),
                        metadata={'search_type': 'keyword'}
                    )
                    results.append(result)
            
            # Sort by relevance score
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in keyword search: {e}")
            return []
    
    def _hybrid_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform hybrid search combining semantic and keyword search"""
        try:
            # Get semantic results
            semantic_results = self._semantic_search(query)
            
            # Get keyword results
            keyword_results = self._keyword_search(query)
            
            # Combine results
            combined_results = {}
            
            # Add semantic results
            for result in semantic_results:
                combined_results[result.content_id] = result
            
            # Add keyword results
            for result in keyword_results:
                if result.content_id in combined_results:
                    # Combine scores
                    existing_result = combined_results[result.content_id]
                    existing_result.relevance_score = (existing_result.semantic_score + result.keyword_score) / 2
                    existing_result.keyword_score = result.keyword_score
                else:
                    combined_results[result.content_id] = result
            
            # Convert to list and sort
            results = list(combined_results.values())
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return []
    
    def _vector_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform vector similarity search"""
        try:
            results = []
            
            # Generate query vector
            query_vector = self._generate_query_vector(query.query_text)
            
            # Search vectors
            for vector_id, vector in self.vectors.items():
                # Calculate similarity
                similarity = self._cosine_similarity(query_vector, vector.vector)
                
                if similarity >= self.similarity_threshold:
                    # Create search result
                    result = SearchResult(
                        id=f"vector_result_{vector_id}",
                        content_id=vector.content_id,
                        title=f"Vector Content {vector.content_id}",
                        content=f"Vector content for {vector.content_id}",
                        relevance_score=similarity,
                        semantic_score=similarity,
                        keyword_score=0.0,
                        result_type=SearchResultType.CONTENT,
                        highlights=self._generate_highlights(query.query_text, f"Vector content for {vector.content_id}"),
                        metadata={
                            'vector_id': vector_id,
                            'model_name': vector.model_name,
                            'dimension': vector.dimension
                        }
                    )
                    results.append(result)
            
            # Sort by relevance score
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
    
    def _contextual_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform contextual search"""
        try:
            results = []
            
            # Get user context
            user_context = self._get_user_context(query.user_id, query.session_id)
            
            # Perform semantic search with context
            semantic_results = self._semantic_search(query)
            
            # Apply context filtering and boosting
            for result in semantic_results:
                # Apply context boosting
                context_boost = self._calculate_context_boost(result, user_context)
                result.relevance_score *= context_boost
                
                # Add context metadata
                result.context = user_context
                
                results.append(result)
            
            # Sort by relevance score
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in contextual search: {e}")
            return []
    
    def _multimodal_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform multimodal search"""
        try:
            results = []
            
            # Combine text and other modalities
            text_results = self._semantic_search(query)
            
            # Mock multimodal results
            for result in text_results:
                result.metadata['multimodal'] = True
                result.metadata['modalities'] = ['text', 'image', 'audio']
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in multimodal search: {e}")
            return []
    
    def _exact_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform exact search"""
        try:
            results = []
            query_lower = query.query_text.lower()
            
            # Mock exact search
            for i in range(5):  # Mock 5 results
                content_id = f"exact_content_{i}"
                title = f"Exact Document {i}"
                content = f"This is exact document {i} with {query.query_text}"
                
                if query_lower in content.lower():
                    result = SearchResult(
                        id=f"exact_result_{i}",
                        content_id=content_id,
                        title=title,
                        content=content,
                        relevance_score=1.0,
                        semantic_score=0.0,
                        keyword_score=1.0,
                        result_type=SearchResultType.DOCUMENT,
                        highlights=[query.query_text],
                        metadata={'search_type': 'exact'}
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in exact search: {e}")
            return []
    
    def _fuzzy_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform fuzzy search"""
        try:
            results = []
            query_lower = query.query_text.lower()
            
            # Mock fuzzy search
            for i in range(8):  # Mock 8 results
                content_id = f"fuzzy_content_{i}"
                title = f"Fuzzy Document {i}"
                content = f"This is fuzzy document {i} with similar content to {query.query_text}"
                
                # Calculate fuzzy score
                fuzzy_score = self._calculate_fuzzy_score(query_lower, content.lower())
                
                if fuzzy_score > 0.5:
                    result = SearchResult(
                        id=f"fuzzy_result_{i}",
                        content_id=content_id,
                        title=title,
                        content=content,
                        relevance_score=fuzzy_score,
                        semantic_score=0.0,
                        keyword_score=fuzzy_score,
                        result_type=SearchResultType.DOCUMENT,
                        highlights=self._generate_highlights(query.query_text, content),
                        metadata={'search_type': 'fuzzy'}
                    )
                    results.append(result)
            
            # Sort by relevance score
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in fuzzy search: {e}")
            return []
    
    def _similarity_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform similarity search"""
        try:
            results = []
            
            # Generate query vector
            query_vector = self._generate_query_vector(query.query_text)
            
            # Search vectors
            for vector_id, vector in self.vectors.items():
                # Calculate similarity
                similarity = self._cosine_similarity(query_vector, vector.vector)
                
                if similarity >= self.similarity_threshold:
                    # Create search result
                    result = SearchResult(
                        id=f"similarity_result_{vector_id}",
                        content_id=vector.content_id,
                        title=f"Similar Content {vector.content_id}",
                        content=f"Similar content for {vector.content_id}",
                        relevance_score=similarity,
                        semantic_score=similarity,
                        keyword_score=0.0,
                        result_type=SearchResultType.CONTENT,
                        highlights=self._generate_highlights(query.query_text, f"Similar content for {vector.content_id}"),
                        metadata={
                            'vector_id': vector_id,
                            'model_name': vector.model_name,
                            'dimension': vector.dimension
                        }
                    )
                    results.append(result)
            
            # Sort by relevance score
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return []
    
    def _generate_query_vector(self, query_text: str) -> List[float]:
        """Generate query vector"""
        try:
            # Mock vector generation
            # In production, use actual embedding model
            vector = [0.1] * 384  # Mock 384-dimensional vector
            
            # Add some variation based on query
            for i, char in enumerate(query_text):
                if i < len(vector):
                    vector[i] += ord(char) * 0.001
            
            return vector
            
        except Exception as e:
            logger.error(f"Error generating query vector: {e}")
            return [0.0] * 384
    
    def _cosine_similarity(self, vector1: List[float], vector2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            if len(vector1) != len(vector2):
                return 0.0
            
            # Convert to numpy arrays
            v1 = np.array(vector1)
            v2 = np.array(vector2)
            
            # Calculate cosine similarity
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def _euclidean_distance(self, vector1: List[float], vector2: List[float]) -> float:
        """Calculate Euclidean distance between two vectors"""
        try:
            if len(vector1) != len(vector2):
                return float('inf')
            
            # Convert to numpy arrays
            v1 = np.array(vector1)
            v2 = np.array(vector2)
            
            # Calculate Euclidean distance
            distance = np.linalg.norm(v1 - v2)
            return float(distance)
            
        except Exception as e:
            logger.error(f"Error calculating Euclidean distance: {e}")
            return float('inf')
    
    def _dot_product(self, vector1: List[float], vector2: List[float]) -> float:
        """Calculate dot product between two vectors"""
        try:
            if len(vector1) != len(vector2):
                return 0.0
            
            # Convert to numpy arrays
            v1 = np.array(vector1)
            v2 = np.array(vector2)
            
            # Calculate dot product
            dot_product = np.dot(v1, v2)
            return float(dot_product)
            
        except Exception as e:
            logger.error(f"Error calculating dot product: {e}")
            return 0.0
    
    def _manhattan_distance(self, vector1: List[float], vector2: List[float]) -> float:
        """Calculate Manhattan distance between two vectors"""
        try:
            if len(vector1) != len(vector2):
                return float('inf')
            
            # Convert to numpy arrays
            v1 = np.array(vector1)
            v2 = np.array(vector2)
            
            # Calculate Manhattan distance
            distance = np.sum(np.abs(v1 - v2))
            return float(distance)
            
        except Exception as e:
            logger.error(f"Error calculating Manhattan distance: {e}")
            return float('inf')
    
    def _calculate_keyword_score(self, query_words: List[str], content: str) -> float:
        """Calculate keyword score for content"""
        try:
            content_lower = content.lower()
            matches = sum(1 for word in query_words if word in content_lower)
            
            if not query_words:
                return 0.0
            
            score = matches / len(query_words)
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating keyword score: {e}")
            return 0.0
    
    def _calculate_fuzzy_score(self, query: str, content: str) -> float:
        """Calculate fuzzy score for content"""
        try:
            # Simple fuzzy matching
            query_words = query.split()
            content_words = content.split()
            
            matches = 0
            for query_word in query_words:
                for content_word in content_words:
                    if query_word in content_word or content_word in query_word:
                        matches += 1
                        break
            
            if not query_words:
                return 0.0
            
            score = matches / len(query_words)
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating fuzzy score: {e}")
            return 0.0
    
    def _generate_highlights(self, query: str, content: str) -> List[str]:
        """Generate highlights from content"""
        try:
            highlights = []
            query_words = query.split()
            content_lower = content.lower()
            
            # Find sentences containing query words
            sentences = content.split('.')
            for sentence in sentences:
                sentence_lower = sentence.lower()
                if any(word in sentence_lower for word in query_words):
                    highlights.append(sentence.strip())
            
            return highlights[:3]  # Limit to 3 highlights
            
        except Exception as e:
            logger.error(f"Error generating highlights: {e}")
            return []
    
    def _get_user_context(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Get user context"""
        try:
            if user_id in self.search_contexts:
                return self.search_contexts[user_id]
            
            # Return default context
            return {
                'user_id': user_id,
                'session_id': session_id,
                'preferences': {},
                'domain_knowledge': {},
                'temporal_context': {},
                'spatial_context': {}
            }
            
        except Exception as e:
            logger.error(f"Error getting user context: {e}")
            return {}
    
    def _calculate_context_boost(self, result: SearchResult, context: Dict[str, Any]) -> float:
        """Calculate context boost for result"""
        try:
            boost = 1.0
            
            # Apply user preferences boost
            if 'preferences' in context:
                preferences = context['preferences']
                if 'preferred_categories' in preferences:
                    if result.metadata.get('category') in preferences['preferred_categories']:
                        boost *= 1.2
            
            # Apply domain knowledge boost
            if 'domain_knowledge' in context:
                domain_knowledge = context['domain_knowledge']
                if 'expertise_areas' in domain_knowledge:
                    if result.metadata.get('expertise_area') in domain_knowledge['expertise_areas']:
                        boost *= 1.1
            
            return boost
            
        except Exception as e:
            logger.error(f"Error calculating context boost: {e}")
            return 1.0
    
    def add_vector(self, content_id: str, vector: List[float], model_name: str = "default") -> SemanticVector:
        """Add a semantic vector"""
        try:
            vector_id = f"vector_{content_id}_{model_name}"
            
            semantic_vector = SemanticVector(
                id=vector_id,
                content_id=content_id,
                vector=vector,
                dimension=len(vector),
                model_name=model_name
            )
            
            self.vectors[vector_id] = semantic_vector
            
            logger.info(f"Added vector: {vector_id}")
            return semantic_vector
            
        except Exception as e:
            logger.error(f"Error adding vector: {e}")
            raise
    
    def get_vector(self, vector_id: str) -> Optional[SemanticVector]:
        """Get a semantic vector by ID"""
        return self.vectors.get(vector_id)
    
    def get_vectors_by_content(self, content_id: str) -> List[SemanticVector]:
        """Get vectors for a content ID"""
        try:
            return [v for v in self.vectors.values() if v.content_id == content_id]
        except Exception as e:
            logger.error(f"Error getting vectors by content: {e}")
            return []
    
    def delete_vector(self, vector_id: str):
        """Delete a semantic vector"""
        try:
            if vector_id in self.vectors:
                del self.vectors[vector_id]
                logger.info(f"Deleted vector: {vector_id}")
            
        except Exception as e:
            logger.error(f"Error deleting vector: {e}")
    
    def get_search_query(self, query_id: str) -> Optional[SearchQuery]:
        """Get a search query by ID"""
        return self.search_queries.get(query_id)
    
    def get_search_queries(self, user_id: str = None) -> List[SearchQuery]:
        """Get search queries filtered by user"""
        try:
            queries = list(self.search_queries.values())
            
            if user_id:
                queries = [q for q in queries if q.user_id == user_id]
            
            return sorted(queries, key=lambda x: x.created_at, reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting search queries: {e}")
            return []
    
    def get_search_result(self, result_id: str) -> Optional[SearchResult]:
        """Get a search result by ID"""
        return self.search_results.get(result_id)
    
    def get_search_results(self, query_id: str = None) -> List[SearchResult]:
        """Get search results filtered by query"""
        try:
            results = list(self.search_results.values())
            
            if query_id:
                results = [r for r in results if r.id.startswith(f"search_result_{query_id}")]
            
            return sorted(results, key=lambda x: x.relevance_score, reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting search results: {e}")
            return []
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """Get search statistics"""
        try:
            stats = {
                'total_queries': len(self.search_queries),
                'total_results': len(self.search_results),
                'total_vectors': len(self.vectors),
                'queries_by_type': {},
                'queries_by_mode': {},
                'average_results_per_query': 0,
                'cache_enabled': self.cache_enabled,
                'search_enabled': self.search_enabled,
                'semantic_enabled': self.semantic_enabled,
                'vector_enabled': self.vector_enabled
            }
            
            # Count queries by type
            for query in self.search_queries.values():
                search_type = query.search_type.value
                stats['queries_by_type'][search_type] = stats['queries_by_type'].get(search_type, 0) + 1
                
                search_mode = query.search_mode.value
                stats['queries_by_mode'][search_mode] = stats['queries_by_mode'].get(search_mode, 0) + 1
            
            # Calculate average results per query
            if stats['total_queries'] > 0:
                stats['average_results_per_query'] = stats['total_results'] / stats['total_queries']
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting search statistics: {e}")
            return {}
    
    def export_search_data(self) -> Dict[str, Any]:
        """Export search data"""
        try:
            return {
                'vectors': [
                    {
                        'id': v.id,
                        'content_id': v.content_id,
                        'vector': v.vector,
                        'dimension': v.dimension,
                        'model_name': v.model_name,
                        'created_at': v.created_at.isoformat(),
                        'updated_at': v.updated_at.isoformat()
                    }
                    for v in self.vectors.values()
                ],
                'queries': [
                    {
                        'id': q.id,
                        'query_text': q.query_text,
                        'search_type': q.search_type.value,
                        'search_mode': q.search_mode.value,
                        'filters': q.filters,
                        'context': q.context,
                        'user_id': q.user_id,
                        'session_id': q.session_id,
                        'created_at': q.created_at.isoformat()
                    }
                    for q in self.search_queries.values()
                ],
                'results': [
                    {
                        'id': r.id,
                        'content_id': r.content_id,
                        'title': r.title,
                        'content': r.content,
                        'relevance_score': r.relevance_score,
                        'semantic_score': r.semantic_score,
                        'keyword_score': r.keyword_score,
                        'result_type': r.result_type.value,
                        'highlights': r.highlights,
                        'metadata': r.metadata,
                        'context': r.context,
                        'created_at': r.created_at.isoformat()
                    }
                    for r in self.search_results.values()
                ]
            }
            
        except Exception as e:
            logger.error(f"Error exporting search data: {e}")
            return {}
    
    def import_search_data(self, data: Dict[str, Any]):
        """Import search data"""
        try:
            # Import vectors
            if 'vectors' in data:
                for vector_data in data['vectors']:
                    vector = SemanticVector(
                        id=vector_data['id'],
                        content_id=vector_data['content_id'],
                        vector=vector_data['vector'],
                        dimension=vector_data['dimension'],
                        model_name=vector_data['model_name'],
                        created_at=datetime.fromisoformat(vector_data['created_at']),
                        updated_at=datetime.fromisoformat(vector_data['updated_at'])
                    )
                    self.vectors[vector.id] = vector
            
            # Import queries
            if 'queries' in data:
                for query_data in data['queries']:
                    query = SearchQuery(
                        id=query_data['id'],
                        query_text=query_data['query_text'],
                        search_type=SearchType(query_data['search_type']),
                        search_mode=SearchMode(query_data['search_mode']),
                        filters=query_data.get('filters', {}),
                        context=query_data.get('context', {}),
                        user_id=query_data.get('user_id'),
                        session_id=query_data.get('session_id'),
                        created_at=datetime.fromisoformat(query_data['created_at'])
                    )
                    self.search_queries[query.id] = query
            
            # Import results
            if 'results' in data:
                for result_data in data['results']:
                    result = SearchResult(
                        id=result_data['id'],
                        content_id=result_data['content_id'],
                        title=result_data['title'],
                        content=result_data['content'],
                        relevance_score=result_data['relevance_score'],
                        semantic_score=result_data['semantic_score'],
                        keyword_score=result_data['keyword_score'],
                        result_type=SearchResultType(result_data['result_type']),
                        highlights=result_data.get('highlights', []),
                        metadata=result_data.get('metadata', {}),
                        context=result_data.get('context', {}),
                        created_at=datetime.fromisoformat(result_data['created_at'])
                    )
                    self.search_results[result.id] = result
            
            logger.info("Search data imported successfully")
            
        except Exception as e:
            logger.error(f"Error importing search data: {e}")
            raise
