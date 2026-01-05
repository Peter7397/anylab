"""
Ollama embedding generation module.
"""

import logging
import hashlib
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class OllamaEmbeddingGenerator:
    """Generate embeddings using Ollama BGE-M3"""
    
    def __init__(self, ollama_url=None, embedding_model='bge-m3', embedding_dims=1024):
        self.ollama_url = ollama_url or getattr(settings, 'OLLAMA_API_URL', 'http://ollama:11434')
        self.embedding_model = embedding_model
        self.embedding_dims = embedding_dims
        self.max_concurrent_workers = 3  # Reduced to prevent overload
        self.embedding_cache_ttl = 24 * 3600  # 24 hours
    
    def get_embedding(self, text: str) -> list:
        """
        Get single embedding from BGE-M3 ONLY
        NO FALLBACKS - Quality requirement
        """
        # Clean null bytes from text
        if isinstance(text, str):
            text = text.replace('\x00', '').replace('\0', '')
            text = ''.join(char for char in text if ord(char) >= 32 or char in ['\n', '\r', '\t'])
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                response = requests.post(
                    f"{self.ollama_url}/api/embeddings",
                    json={
                        "model": self.embedding_model,
                        "prompt": text
                    },
                    timeout=300  # 5 minutes
                )
                response.raise_for_status()
                embedding = response.json()["embedding"]
                
                # Ensure correct dimensions
                if len(embedding) != self.embedding_dims:
                    if len(embedding) < self.embedding_dims:
                        embedding = list(embedding) + [0.0] * (self.embedding_dims - len(embedding))
                    else:
                        embedding = embedding[:self.embedding_dims]
                
                return embedding
                
            except requests.exceptions.Timeout:
                retry_count += 1
                logger.warning(f"BGE-M3 timeout (attempt {retry_count}/{max_retries})")
                if retry_count >= max_retries:
                    raise Exception("BGE-M3 embedding timeout after multiple retries")
                time.sleep(2 ** retry_count)
                
            except Exception as e:
                logger.error(f"BGE-M3 embedding error: {e}")
                raise Exception(f"BGE-M3 embedding failed: {str(e)}")
        
        raise Exception("Failed to get BGE-M3 embedding after all retries")
    
    def get_embeddings_batch(self, texts: list) -> list:
        """
        Get batch embeddings from BGE-M3 using parallel processing with caching
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embeddings corresponding to input texts (same order)
        """
        if not texts:
            return []
        
        results = [None] * len(texts)
        cache_hits = 0
        api_calls_needed = []
        
        # Phase 1: Check cache for all texts
        for idx, text in enumerate(texts):
            # Clean null bytes
            if isinstance(text, str):
                text = text.replace('\x00', '').replace('\0', '')
                text = ''.join(char for char in text if ord(char) >= 32 or char in ['\n', '\r', '\t'])
                texts[idx] = text
            
            if not text.strip():
                results[idx] = [0.0] * self.embedding_dims
                continue
            
            text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
            cache_key = f"embedding_bge_m3_{text_hash}"
            cached_embedding = cache.get(cache_key)
            
            if cached_embedding is not None:
                results[idx] = cached_embedding
                cache_hits += 1
            else:
                api_calls_needed.append((idx, text))
        
        if cache_hits > 0:
            logger.info(f"Cache hits: {cache_hits}/{len(texts)} chunks ({(cache_hits/len(texts)*100):.1f}%)")
        
        # Phase 2: Process uncached texts with parallel API calls
        if api_calls_needed:
            logger.info(f"Fetching {len(api_calls_needed)} embeddings from Ollama (parallel processing with {self.max_concurrent_workers} workers)")
            
            def fetch_embedding(idx, text):
                """Fetch embedding with retry logic"""
                max_retries = 3
                retry_count = 0
                while retry_count < max_retries:
                    try:
                        response = requests.post(
                            f"{self.ollama_url}/api/embeddings",
                            json={
                                "model": self.embedding_model,
                                "prompt": text
                            },
                            timeout=600  # 10 minutes for model loading
                        )
                        response.raise_for_status()
                        embedding = response.json()["embedding"]
                        
                        # Ensure correct dimensions
                        if len(embedding) != self.embedding_dims:
                            if len(embedding) < self.embedding_dims:
                                embedding = list(embedding) + [0.0] * (self.embedding_dims - len(embedding))
                            else:
                                embedding = embedding[:self.embedding_dims]
                        
                        # Cache it
                        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
                        cache_key = f"embedding_bge_m3_{text_hash}"
                        cache.set(cache_key, embedding, self.embedding_cache_ttl)
                        
                        return idx, embedding
                        
                    except requests.exceptions.Timeout:
                        retry_count += 1
                        logger.warning(f"BGE-M3 timeout for chunk {idx} (attempt {retry_count}/{max_retries})")
                        if retry_count >= max_retries:
                            raise Exception(f"BGE-M3 embedding timeout for chunk {idx} after {max_retries} attempts")
                        time.sleep(2 ** retry_count)
                        
                    except requests.exceptions.RequestException as e:
                        retry_count += 1
                        logger.warning(f"BGE-M3 request error for chunk {idx} (attempt {retry_count}/{max_retries}): {e}")
                        if retry_count >= max_retries:
                            raise Exception(f"BGE-M3 embedding failed for chunk {idx}: {str(e)}")
                        time.sleep(2 ** retry_count)
                        
                    except Exception as e:
                        logger.error(f"BGE-M3 embedding error for chunk {idx}: {e}")
                        retry_count += 1
                        if retry_count >= max_retries:
                            raise Exception(f"BGE-M3 embedding failed for chunk {idx}: {str(e)}")
                        time.sleep(2 ** retry_count)
                
                raise Exception(f"Failed to get BGE-M3 embedding for chunk {idx} after all retries")
            
            # Use ThreadPoolExecutor for parallel processing
            with ThreadPoolExecutor(max_workers=self.max_concurrent_workers) as executor:
                futures = {executor.submit(fetch_embedding, idx, text): (idx, text) 
                          for idx, text in api_calls_needed}
                
                failed_chunks = []
                for future in as_completed(futures):
                    try:
                        idx, embedding = future.result()
                        results[idx] = embedding
                    except Exception as e:
                        idx, text = futures[future]
                        logger.error(f"Error processing chunk {idx}: {e}")
                        failed_chunks.append((idx, str(e)))
                
                # If we have failures, fail the entire batch
                if failed_chunks:
                    error_details = "; ".join([f"Chunk {idx}: {error[:100]}" for idx, error in failed_chunks[:5]])
                    if len(failed_chunks) > 5:
                        error_details += f" ... and {len(failed_chunks) - 5} more"
                    
                    error_msg = (
                        f"Failed to generate embeddings for {len(failed_chunks)}/{len(api_calls_needed)} chunks. "
                        f"First errors: {error_details}. "
                        f"Ollama URL: {self.ollama_url}. "
                        f"Please check Ollama is running and has sufficient memory."
                    )
                    logger.error(error_msg)
                    raise Exception(error_msg)
        
        return results

