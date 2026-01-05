"""
Validation utilities for file processing.
"""

import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def validate_metadata_completeness(metadata: dict, uploaded_file) -> bool:
    """
    Validate metadata completeness
    
    QUALITY CHECK: Ensure all required metadata is present
    """
    try:
        # Check if metadata is None or not a dict
        if metadata is None:
            logger.error(f"Metadata is None for file {uploaded_file.filename if uploaded_file else 'unknown'}")
            return False
        
        if not isinstance(metadata, dict):
            logger.error(f"Metadata is not a dict (type: {type(metadata)}) for file {uploaded_file.filename if uploaded_file else 'unknown'}")
            return False
        
        # Check required fields
        required_fields = ['filename', 'file_size', 'file_hash']
        
        for field in required_fields:
            if field not in metadata or not metadata.get(field):
                logger.warning(f"Missing required metadata field: {field}")
                return False
        
        # Validate metadata values
        if metadata.get('file_size', 0) <= 0:
            logger.warning(f"Invalid file size: {metadata.get('file_size', 0)}")
            return False
        
        if not metadata.get('file_hash'):
            logger.warning("Missing file hash")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Metadata validation error: {e}", exc_info=True)
        return False


def verify_ollama_connection(ollama_url: str = None):
    """
    Verify Ollama service is accessible before processing
    Raises exception if Ollama is not available
    
    Args:
        ollama_url: Optional Ollama URL. If not provided, uses settings.OLLAMA_API_URL
    """
    if ollama_url is None:
        ollama_url = getattr(settings, 'OLLAMA_API_URL', 'http://ollama:11434')
    
    try:
        # Quick health check - try to list models
        response = requests.get(
            f"{ollama_url}/api/tags",
            timeout=5
        )
        response.raise_for_status()
        logger.info(f"Ollama connection verified at {ollama_url}")
    except requests.exceptions.ConnectionError as e:
        raise Exception(f"Cannot connect to Ollama at {ollama_url}. Is Ollama running? Error: {str(e)}")
    except requests.exceptions.Timeout as e:
        raise Exception(f"Ollama at {ollama_url} did not respond within 5 seconds. Is Ollama running?")
    except Exception as e:
        raise Exception(f"Failed to verify Ollama connection: {str(e)}")

