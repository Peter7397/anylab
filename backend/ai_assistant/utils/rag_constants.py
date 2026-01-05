"""
Constants and configuration for RAG system
Centralizes magic numbers and configurable values
"""
from django.conf import settings


# Embedding Configuration
EMBEDDING_DIMENSIONS = 1024  # BGE-M3 standard dimensions
EMBEDDING_MODEL = getattr(settings, 'EMBEDDING_MODEL', 'bge-m3')
EMBEDDING_CACHE_TTL = getattr(settings, 'EMBEDDING_CACHE_TTL', 24 * 3600)  # 24 hours

# RAG Retrieval Configuration
DEFAULT_TOP_K = 10
COMPREHENSIVE_TOP_K = 30
COMPREHENSIVE_CANDIDATES = 120
INITIAL_TOP_K = 120  # For enhanced retrieval pipeline
FINAL_TOP_K = 24  # After all processing

# Similarity Thresholds
DEFAULT_SIMILARITY_THRESHOLD = 0.25
MIN_SIMILARITY_THRESHOLD = 0.2
ABSTAIN_SIMILARITY_THRESHOLD = 0.3
MIN_HYBRID_SCORE = 0.2

# RRF (Reciprocal Rank Fusion) Configuration
RRF_K = 60  # RRF constant (typically 60)

# MMR (Maximal Marginal Relevance) Configuration
MMR_LAMBDA = 0.7  # Balance between relevance (1.0) and diversity (0.0)
MMR_LAMBDA_COMPREHENSIVE = 0.6  # More diversity for comprehensive search

# Deduplication Configuration
MAX_RESULTS_PER_SOURCE = 3
CONTENT_SIMILARITY_THRESHOLD = 0.85  # For content deduplication

# Query Processing Configuration
USE_ADAPTIVE_EXPANSION = getattr(settings, 'RAG_USE_ADAPTIVE_EXPANSION', True)
MIN_QUERY_LENGTH = 3
MAX_QUERY_LENGTH = 500

# Batch Processing Configuration
BATCH_SIZE_EMBEDDINGS = 200
MAX_CONCURRENT_WORKERS = getattr(settings, 'RAG_MAX_CONCURRENT_WORKERS', 20)  # Increased from 10
MAX_BATCH_SIZE = 200

# HTTP Connection Pooling
HTTP_POOL_CONNECTIONS = getattr(settings, 'HTTP_POOL_CONNECTIONS', 10)
HTTP_POOL_MAXSIZE = getattr(settings, 'HTTP_POOL_MAXSIZE', 20)
HTTP_MAX_RETRIES = getattr(settings, 'HTTP_MAX_RETRIES', 3)
HTTP_BACKOFF_FACTOR = getattr(settings, 'HTTP_BACKOFF_FACTOR', 0.3)

# Circuit Breaker Configuration
OLLAMA_CIRCUIT_BREAKER_THRESHOLD = getattr(settings, 'OLLAMA_CIRCUIT_BREAKER_THRESHOLD', 5)
OLLAMA_CIRCUIT_BREAKER_TIMEOUT = getattr(settings, 'OLLAMA_CIRCUIT_BREAKER_TIMEOUT', 60.0)

# Cache TTL Configuration
SEARCH_CACHE_TTL = getattr(settings, 'SEARCH_CACHE_TTL', 3600)  # 1 hour
RESPONSE_CACHE_TTL = getattr(settings, 'RESPONSE_CACHE_TTL', 1800)  # 30 minutes
COMPREHENSIVE_CACHE_TTL = 21600  # 6 hours

# Context Length Configuration
MAX_CONTEXT_LENGTH = 8000  # Reduced from 20000 for better performance
MAX_CHARS_PER_DOC = 500
MAX_TOTAL_CHARS = 4000
MAX_DOCS_SIMPLE_QUERY = 5
MAX_DOCS_COMPLEX_QUERY = 8

# Ollama Configuration
OLLAMA_REQUEST_TIMEOUT = getattr(settings, 'OLLAMA_REQUEST_TIMEOUT', 120)
OLLAMA_COMPREHENSIVE_TIMEOUT = 480  # Longer timeout for comprehensive responses
OLLAMA_EMBEDDING_TIMEOUT = 60

# LLM Generation Parameters
# Procedural queries
PROCEDURAL_NUM_PREDICT = 6000
PROCEDURAL_TEMPERATURE = 0.05
PROCEDURAL_TOP_P = 0.7
PROCEDURAL_REPEAT_PENALTY = 1.3
PROCEDURAL_NUM_CTX = 16384
PROCEDURAL_TOP_K = 30

# Definitional queries
DEFINITIONAL_NUM_PREDICT = 5000
DEFINITIONAL_TEMPERATURE = 0.05
DEFINITIONAL_TOP_P = 0.75
DEFINITIONAL_REPEAT_PENALTY = 1.25
DEFINITIONAL_NUM_CTX = 16384
DEFINITIONAL_TOP_K = 30

# Troubleshooting queries
TROUBLESHOOTING_NUM_PREDICT = 6000
TROUBLESHOOTING_TEMPERATURE = 0.05
TROUBLESHOOTING_TOP_P = 0.7
TROUBLESHOOTING_REPEAT_PENALTY = 1.3
TROUBLESHOOTING_NUM_CTX = 16384
TROUBLESHOOTING_TOP_K = 30

# General queries
GENERAL_NUM_PREDICT = 5000
GENERAL_TEMPERATURE = 0.05
GENERAL_TOP_P = 0.8
GENERAL_REPEAT_PENALTY = 1.2
GENERAL_NUM_CTX = 16384
GENERAL_TOP_K = 30

# Standard RAG queries (faster, less comprehensive)
STANDARD_NUM_PREDICT = 768
STANDARD_TEMPERATURE = 0.3
STANDARD_TOP_P = 0.9
STANDARD_REPEAT_PENALTY = 1.1
STANDARD_NUM_CTX = 4096
STANDARD_TOP_K = 40

# Graph RAG Configuration
GRAPH_ENTITY_SIMILARITY_THRESHOLD = 0.6
GRAPH_MAX_SIMILAR_ENTITIES = 10
GRAPH_MAX_CONTEXT = 5
GRAPH_MAX_PATHS = 5
GRAPH_BOOST_FACTOR = 1.3  # Boost for graph-connected documents
GRAPH_LOWER_WEIGHT = 0.7  # Lower weight for graph-only results

# Entity Weights (for graph RAG)
ENTITY_WEIGHTS = {
    'IMPORTANT_INFO': 1.2,
    'KEY_POINT': 1.1,
    'CONCEPT': 1.0,
    'KEY_TERM': 1.0,
    'TOPIC': 0.95,
    'PROCEDURE': 0.9,
    'PRODUCT': 1.0,
    'ERROR_CODE': 0.9,
    'VERSION': 0.8,
    'PROBLEM': 0.7,
    'SOLUTION': 0.7,
    'SOFTWARE': 0.6,
    'CATEGORY': 0.5,
}

# Performance Monitoring
ENABLE_PERFORMANCE_MONITORING = getattr(settings, 'RAG_ENABLE_PERFORMANCE_MONITORING', True)

# Abstain Guardrail Configuration
MIN_RESULTS_THRESHOLD = 1
MIN_SIMILARITY_FOR_ABSTAIN = 0.3

