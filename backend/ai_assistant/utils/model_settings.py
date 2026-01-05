"""
Utility functions for getting dynamic model settings.
"""
from django.conf import settings
from django.core.cache import cache

DYNAMIC_SETTINGS_CACHE_KEY = 'system_settings:dynamic'
DYNAMIC_SETTINGS_CACHE_TTL = 86400 * 365  # 1 year
OCR_SETTING_CACHE_KEY = 'enable_ocr_for_scanned_files'

# Model mappings for AI modes
# Note: Ollama model names may vary. Common formats:
# - qwen2.5:7b, qwen2.5:1.5b, qwen2.5:2b
# - qwen2:2b (older format, may not exist)
AI_MODE_MODELS = {
    'performance': 'qwen2.5:7b',   # Larger, more accurate model
    'lightweight': 'qwen2.5:1.5b', # Smaller, faster model (use qwen2.5:2b if 1.5b not available)
}


def get_ocr_enabled():
    """
    Get OCR enabled setting, checking cache first, then falling back to settings.py.
    """
    # Check cache first
    cached = cache.get(OCR_SETTING_CACHE_KEY)
    if cached is not None:
        return cached
    
    # Fall back to settings.py
    return getattr(settings, 'ENABLE_OCR_FOR_SCANNED_FILES', True)


def set_ocr_enabled(enabled: bool):
    """
    Set OCR enabled setting in cache.
    """
    cache.set(OCR_SETTING_CACHE_KEY, enabled, DYNAMIC_SETTINGS_CACHE_TTL)


def get_ollama_model():
    """
    Get the Ollama model name, checking dynamic settings first, then falling back to settings.py.
    
    Returns:
        str: The Ollama model name (e.g., 'qwen2:2b', 'llama3:8b')
    """
    # Check cache for dynamic settings
    cached = cache.get(DYNAMIC_SETTINGS_CACHE_KEY)
    if cached and 'ollama_model' in cached:
        return cached['ollama_model']
    
    # Fall back to settings.py
    return getattr(settings, 'OLLAMA_MODEL', 'llama3:8b')


def get_model_for_ai_mode(ai_mode: str) -> str:
    """
    Get the recommended Ollama model for a given AI mode.
    
    Args:
        ai_mode: 'performance' or 'lightweight'
    
    Returns:
        str: Recommended model name for the mode
    """
    return AI_MODE_MODELS.get(ai_mode, AI_MODE_MODELS['lightweight'])


def set_ollama_model(model_name: str, ai_mode: str = None):
    """
    Set the Ollama model in cache.
    
    Args:
        model_name: The model name to set (e.g., 'qwen2:2b')
        ai_mode: Optional AI mode ('performance' or 'lightweight') to store with the model
    """
    cached = cache.get(DYNAMIC_SETTINGS_CACHE_KEY) or {}
    cached['ollama_model'] = model_name
    if ai_mode:
        cached['ai_mode'] = ai_mode
    cache.set(DYNAMIC_SETTINGS_CACHE_KEY, cached, DYNAMIC_SETTINGS_CACHE_TTL)


def get_current_ai_mode() -> str:
    """
    Get the current AI mode from cache, or infer from model.
    
    Returns:
        str: 'performance' or 'lightweight', defaults to 'lightweight'
    """
    cached = cache.get(DYNAMIC_SETTINGS_CACHE_KEY)
    if cached and 'ai_mode' in cached and cached['ai_mode']:
        return cached['ai_mode']
    
    # Infer from current model
    current_model = get_ollama_model()
    for mode, model in AI_MODE_MODELS.items():
        if model == current_model:
            return mode
    
    # Default to lightweight
    return 'lightweight'

