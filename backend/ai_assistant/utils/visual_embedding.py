"""
Visual Embedding Service for Graphic RAG
Supports CLIP and Ollama vision models for image embeddings
"""
import logging
import os
from typing import List, Optional, Any, Dict
import numpy as np
from PIL import Image
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

# Try to import CLIP
CLIP_AVAILABLE = False
try:
    import clip
    import torch
    CLIP_AVAILABLE = True
    logger.info("CLIP library available for visual embeddings")
except ImportError:
    logger.warning("CLIP library not available. Install with: pip install clip-by-openai torch")
    clip = None
    torch = None


class VisualEmbeddingService:
    """
    Service for generating visual embeddings from images
    
    Supports:
    - CLIP (OpenAI) - Primary method
    - Ollama vision models - Fallback
    """
    
    def __init__(
        self,
        clip_model_name: str = "ViT-B/32",
        device: Optional[str] = None,
        ollama_url: Optional[str] = None
    ):
        """
        Initialize visual embedding service
        
        Args:
            clip_model_name: CLIP model name (default: "ViT-B/32")
            device: Device to use (cuda/cpu, auto-detected if None)
            ollama_url: Ollama API URL for fallback
        """
        self.clip_model_name = clip_model_name
        self.ollama_url = ollama_url or getattr(settings, 'OLLAMA_API_URL', 'http://ollama:11434')
        self.device = device or ("cuda" if torch and torch.cuda.is_available() else "cpu")
        
        # Initialize CLIP if available
        self.clip_model = None
        self.clip_preprocess = None
        if CLIP_AVAILABLE:
            self._initialize_clip()
    
    def _initialize_clip(self):
        """Initialize CLIP model"""
        try:
            self.clip_model, self.clip_preprocess = clip.load(
                self.clip_model_name,
                device=self.device
            )
            self.clip_model.eval()
            logger.info(f"CLIP model {self.clip_model_name} loaded on {self.device}")
        except Exception as e:
            logger.error(f"Failed to initialize CLIP: {e}")
            self.clip_model = None
            self.clip_preprocess = None
    
    def get_embedding_from_image(
        self,
        image_path: str,
        use_cache: bool = True
    ) -> Optional[List[float]]:
        """
        Generate visual embedding from image
        
        Args:
            image_path: Path to image file
            use_cache: Whether to use cache
            
        Returns:
            List of float values (embedding vector) or None if failed
        """
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return None
        
        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(image_path)
            cached_embedding = cache.get(cache_key)
            if cached_embedding is not None:
                logger.debug(f"Using cached visual embedding for {image_path}")
                return cached_embedding
        
        # Try CLIP first
        if self.clip_model and self.clip_preprocess:
            embedding = self._get_clip_embedding(image_path)
            if embedding:
                if use_cache:
                    cache.set(cache_key, embedding, 24 * 3600)  # 24 hours
                return embedding
        
        # Fallback to Ollama if available
        embedding = self._get_ollama_vision_embedding(image_path)
        if embedding:
            if use_cache:
                cache.set(cache_key, embedding, 24 * 3600)
            return embedding
        
        logger.error(f"Failed to generate visual embedding for {image_path}")
        return None
    
    def _get_clip_embedding(self, image_path: str) -> Optional[List[float]]:
        """Generate embedding using CLIP"""
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert("RGB")
            image_tensor = self.clip_preprocess(image).unsqueeze(0).to(self.device)
            
            # Generate embedding
            with torch.no_grad():
                image_features = self.clip_model.encode_image(image_tensor)
                # Normalize features
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                embedding = image_features.cpu().numpy()[0].tolist()
            
            logger.debug(f"Generated CLIP embedding (dim: {len(embedding)})")
            return embedding
            
        except Exception as e:
            logger.error(f"CLIP embedding generation failed: {e}")
            return None
    
    def _get_ollama_vision_embedding(self, image_path: str) -> Optional[List[float]]:
        """Generate embedding using Ollama vision model (if available)"""
        try:
            import requests
            import base64
            
            # Read image and encode to base64
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Try to use Ollama vision model
            # Note: This requires Ollama to have a vision model available
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": "llava",  # Common vision model name
                    "image": image_data
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                embedding = result.get("embedding")
                if embedding:
                    logger.debug(f"Generated Ollama vision embedding (dim: {len(embedding)})")
                    return embedding
            
            logger.debug("Ollama vision model not available")
            return None
            
        except Exception as e:
            logger.debug(f"Ollama vision embedding not available: {e}")
            return None
    
    def _get_cache_key(self, image_path: str) -> str:
        """Generate cache key for image"""
        import hashlib
        file_hash = hashlib.md5(image_path.encode()).hexdigest()
        return f"visual_embedding_{file_hash}"
    
    def get_embeddings_batch(
        self,
        image_paths: List[str],
        use_cache: bool = True
    ) -> Dict[str, Optional[List[float]]]:
        """
        Generate embeddings for multiple images
        
        Args:
            image_paths: List of image file paths
            use_cache: Whether to use cache
            
        Returns:
            Dictionary mapping image_path -> embedding (or None if failed)
        """
        results = {}
        
        for image_path in image_paths:
            embedding = self.get_embedding_from_image(image_path, use_cache=use_cache)
            results[image_path] = embedding
        
        return results
    
    def get_embedding_dimensions(self) -> int:
        """Get embedding dimensions for current model"""
        if self.clip_model:
            # CLIP ViT-B/32 produces 512-dimensional embeddings
            return 512
        # Ollama vision models vary, default to 512
        return 512


# Global instance
_visual_embedding_service: Optional[VisualEmbeddingService] = None


def get_visual_embedding_service() -> VisualEmbeddingService:
    """Get or create visual embedding service instance"""
    global _visual_embedding_service
    if _visual_embedding_service is None:
        _visual_embedding_service = VisualEmbeddingService()
    return _visual_embedding_service

