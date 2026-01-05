"""
Cache utility functions for consistent cache key generation
"""
import hashlib
from typing import Optional, Dict, Any
from django.conf import settings


def generate_cache_key(
    prefix: str,
    content: str,
    additional_params: Optional[Dict[str, Any]] = None,
    use_sha256: bool = False
) -> str:
    """
    Generate a consistent cache key from content and parameters
    
    Args:
        prefix: Cache key prefix (e.g., 'embedding', 'rag_query')
        content: Main content to hash (query, text, etc.)
        additional_params: Optional additional parameters to include in key
        use_sha256: If True, use SHA256 instead of MD5 (more secure, slower)
        
    Returns:
        Cache key string
    """
    # Hash the main content
    if use_sha256:
        hash_obj = hashlib.sha256(content.encode('utf-8'))
    else:
        hash_obj = hashlib.md5(content.encode('utf-8'))
    
    # Add additional parameters to hash if provided
    if additional_params:
        # Sort keys for consistent ordering
        param_str = '_'.join(f"{k}:{v}" for k, v in sorted(additional_params.items()))
        hash_obj.update(param_str.encode('utf-8'))
    
    content_hash = hash_obj.hexdigest()
    
    # Build cache key
    if additional_params:
        # Include readable params in key for debugging
        param_str = '_'.join(f"{k}_{v}" for k, v in sorted(additional_params.items()))
        return f"{prefix}_{content_hash[:16]}_{param_str}"
    else:
        return f"{prefix}_{content_hash}"


def generate_embedding_cache_key(text: str, model: str = 'bge-m3') -> str:
    """
    Generate cache key for embeddings
    
    Args:
        text: Text to embed
        model: Embedding model name
        
    Returns:
        Cache key string
    """
    return generate_cache_key(
        'embedding',
        text,
        additional_params={'model': model}
    )


def generate_rag_query_cache_key(
    query: str,
    top_k: int,
    language: str = 'en-US',
    search_mode: Optional[str] = None
) -> str:
    """
    Generate cache key for RAG queries
    
    Args:
        query: User query
        top_k: Number of results
        language: Language code
        search_mode: Optional search mode (comprehensive, advanced, etc.)
        
    Returns:
        Cache key string
    """
    params = {
        'top_k': top_k,
        'language': language
    }
    if search_mode:
        params['mode'] = search_mode
    
    return generate_cache_key('rag_query', query, additional_params=params)


def generate_response_cache_key(
    prompt: str,
    model: Optional[str] = None,
    language: str = 'en-US',
    query_type: Optional[str] = None
) -> str:
    """
    Generate cache key for LLM responses
    
    Args:
        prompt: Prompt text
        model: Model name (optional)
        language: Language code
        query_type: Optional query type
        
    Returns:
        Cache key string
    """
    params = {'language': language}
    if model:
        params['model'] = model
    if query_type:
        params['type'] = query_type
    
    return generate_cache_key('response', prompt, additional_params=params)


def generate_search_cache_key(
    query: str,
    top_k: int,
    similarity_threshold: Optional[float] = None
) -> str:
    """
    Generate cache key for search results
    
    Args:
        query: Search query
        top_k: Number of results
        similarity_threshold: Optional similarity threshold
        
    Returns:
        Cache key string
    """
    params = {'top_k': top_k}
    if similarity_threshold is not None:
        params['threshold'] = similarity_threshold
    
    return generate_cache_key('search', query, additional_params=params)

