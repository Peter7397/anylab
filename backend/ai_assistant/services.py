import logging
from typing import List, Optional
from django.conf import settings
import numpy as np

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for handling text embeddings with dual-mode support."""
    
    def __init__(self):
        self.performance_model = None
        self.lightweight_model = None
        self.current_model = None
        self.current_model_name = None
        self.mode = settings.EMBEDDING_MODE
        # Offline fallback using hashing if sentence-transformers models
        # are unavailable (e.g., no internet to download weights)
        self.fallback_hasher = None
        # Use 384 to match MiniLM-L6-v2 dimensions for better forward compatibility
        self.fallback_dimension = 384
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize both performance and lightweight models."""
        try:
            from sentence_transformers import SentenceTransformer
            import os
            
            # Initialize performance model (BGE-m3)
            try:
                perf_path = os.getenv('EMBEDDING_PERFORMANCE_MODEL_PATH')
                model_id = perf_path if perf_path and os.path.isdir(perf_path) else settings.EMBEDDING_PERFORMANCE_MODEL
                self.performance_model = SentenceTransformer(
                    model_id,
                    device=settings.EMBEDDING_DEVICE
                )
                logger.info(f"Successfully loaded performance model: {settings.EMBEDDING_PERFORMANCE_MODEL}")
            except Exception as e:
                logger.warning(f"Failed to load performance model {settings.EMBEDDING_PERFORMANCE_MODEL}: {e}")
                self.performance_model = None
            
            # Initialize lightweight model (MiniLM)
            try:
                light_path = os.getenv('EMBEDDING_LIGHTWEIGHT_MODEL_PATH')
                model_id = light_path if light_path and os.path.isdir(light_path) else settings.EMBEDDING_LIGHTWEIGHT_MODEL
                self.lightweight_model = SentenceTransformer(
                    model_id,
                    device=settings.EMBEDDING_DEVICE
                )
                logger.info(f"Successfully loaded lightweight model: {settings.EMBEDDING_LIGHTWEIGHT_MODEL}")
            except Exception as e:
                logger.warning(f"Failed to load lightweight model {settings.EMBEDDING_LIGHTWEIGHT_MODEL}: {e}")
                self.lightweight_model = None
            
            # Set current model based on mode
            self._set_current_model()
            
        except Exception as e:
            logger.error(f"Failed to initialize embedding models: {e}")
            self.performance_model = None
            self.lightweight_model = None
            self.current_model = None
            self.current_model_name = None
        finally:
            # Prepare hashing fallback if no model is available
            offline_only = getattr(settings, 'EMBEDDING_OFFLINE_ONLY', True)
            if self.current_model is None or offline_only:
                try:
                    from sklearn.feature_extraction.text import HashingVectorizer
                    self.fallback_hasher = HashingVectorizer(
                        n_features=self.fallback_dimension,
                        alternate_sign=False,
                        norm='l2',
                        stop_words=None
                    )
                    self.current_model = None  # ensure we use fallback path
                    self.current_model_name = f"hashing-embeddings-{self.fallback_dimension}"
                    logger.warning("Using offline hashing-based embeddings fallback")
                except Exception as ex:
                    logger.error(f"Failed to create hashing fallback: {ex}")
    
    def _set_current_model(self):
        """Set the current model based on the configured mode."""
        if self.mode == 'performance':
            if self.performance_model:
                self.current_model = self.performance_model
                self.current_model_name = settings.EMBEDDING_PERFORMANCE_MODEL
                logger.info("Using performance mode with BGE-m3")
            elif self.lightweight_model:
                self.current_model = self.lightweight_model
                self.current_model_name = settings.EMBEDDING_LIGHTWEIGHT_MODEL
                logger.warning("Performance model unavailable, falling back to lightweight mode")
            else:
                self.current_model = None
                self.current_model_name = None
                logger.error("No embedding models available")
        
        elif self.mode == 'lightweight':
            if self.lightweight_model:
                self.current_model = self.lightweight_model
                self.current_model_name = settings.EMBEDDING_LIGHTWEIGHT_MODEL
                logger.info("Using lightweight mode with MiniLM-L6-v2")
            else:
                self.current_model = None
                self.current_model_name = None
                logger.error("Lightweight model unavailable")
        
        else:  # auto mode
            if self.performance_model:
                self.current_model = self.performance_model
                self.current_model_name = settings.EMBEDDING_PERFORMANCE_MODEL
                logger.info("Auto mode: Using performance model (BGE-m3)")
            elif self.lightweight_model:
                self.current_model = self.lightweight_model
                self.current_model_name = settings.EMBEDDING_LIGHTWEIGHT_MODEL
                logger.info("Auto mode: Using lightweight model (MiniLM-L6-v2)")
            else:
                self.current_model = None
                self.current_model_name = None
                logger.error("Auto mode: No embedding models available")
    
    def switch_mode(self, mode: str):
        """Switch between performance and lightweight modes."""
        if mode not in ['performance', 'lightweight', 'auto']:
            logger.error(f"Invalid mode: {mode}. Must be 'performance', 'lightweight', or 'auto'")
            return False
        
        self.mode = mode
        self._set_current_model()
        logger.info(f"Switched to {mode} mode")
        return self.current_model is not None
    
    def get_embeddings(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Generate embeddings for a list of texts."""
        # Primary path: sentence-transformers model
        if self.current_model:
            try:
                embeddings = self.current_model.encode(texts, convert_to_tensor=False)
                return embeddings.tolist() if hasattr(embeddings, 'tolist') else embeddings
            except Exception as e:
                logger.error(f"Error generating embeddings: {e}")
                return None
        
        # Fallback path: hashing vectorizer (offline, stateless)
        if self.fallback_hasher is not None:
            try:
                sparse = self.fallback_hasher.transform(texts)
                dense = sparse.toarray().astype(np.float32)
                return dense.tolist()
            except Exception as e:
                logger.error(f"Hashing fallback failed: {e}")
                return None
        
        logger.error("No embedding backend available")
        return None
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text."""
        embeddings = self.get_embeddings([text])
        return embeddings[0] if embeddings else None
    
    def similarity(self, text1: str, text2: str) -> Optional[float]:
        """Calculate cosine similarity between two texts."""
        embeddings = self.get_embeddings([text1, text2])
        if not embeddings or len(embeddings) < 2:
            return None
        
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return None
    
    def get_model_info(self):
        """Get information about available models and current mode."""
        return {
            'current_mode': self.mode,
            'current_model': self.current_model_name,
            'performance_model_available': self.performance_model is not None,
            'lightweight_model_available': self.lightweight_model is not None,
            'performance_model_name': settings.EMBEDDING_PERFORMANCE_MODEL,
            'lightweight_model_name': settings.EMBEDDING_LIGHTWEIGHT_MODEL,
        }

"""Global service instances for embeddings and related functionality."""

# Initialize a global embedding service instance at import time so views and
# other modules can use it directly. If models fail to load (e.g., no network),
# the service will log and gracefully return None on requests.
embedding_service = EmbeddingService()
