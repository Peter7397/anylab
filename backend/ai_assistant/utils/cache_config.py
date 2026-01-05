"""
Standardized cache configuration for all services.

This module provides consistent cache TTL (Time To Live) values
across all services to ensure predictable caching behavior.
"""

# Standard cache durations (in seconds)
CACHE_DURATIONS = {
    # Short-term caches (frequently changing data)
    'short': 300,      # 5 minutes - for frequently updated data
    'medium': 1800,    # 30 minutes - for moderately stable data
    'long': 3600,      # 1 hour - for stable data
    'very_long': 86400,  # 24 hours - for very stable data
    
    # Service-specific cache durations
    'rag_query': 3600,           # 1 hour - RAG query results
    'rag_embedding': 86400,      # 24 hours - Embeddings (rarely change)
    'metadata': 3600,            # 1 hour - File metadata
    'document_chunk': 86400,     # 24 hours - Document chunks
    'vector_search': 1800,       # 30 minutes - Vector search results
    'query_expansion': 3600,     # 1 hour - Query expansion results
    'reranking': 1800,           # 30 minutes - Reranking results
    'health_check': 60,          # 1 minute - Health check results
    'system_settings': 300,      # 5 minutes - System settings
}

def get_cache_ttl(cache_type: str, default: int = 3600) -> int:
    """
    Get cache TTL for a specific cache type.
    
    Args:
        cache_type: Type of cache (e.g., 'rag_query', 'metadata')
        default: Default TTL if type not found
        
    Returns:
        Cache TTL in seconds
    """
    return CACHE_DURATIONS.get(cache_type, default)

