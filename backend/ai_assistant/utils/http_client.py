"""
HTTP Client with Connection Pooling
Reuses connections for better performance
"""
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.conf import settings

logger = logging.getLogger(__name__)


class PooledHTTPClient:
    """
    HTTP client with connection pooling and retry logic
    
    Reuses connections to improve performance and reduce overhead
    """
    
    def __init__(
        self,
        base_url: str,
        pool_connections: int = 10,
        pool_maxsize: int = 20,
        max_retries: int = 3,
        backoff_factor: float = 0.3
    ):
        """
        Initialize pooled HTTP client
        
        Args:
            base_url: Base URL for requests
            pool_connections: Number of connection pools to cache
            pool_maxsize: Maximum number of connections per pool
            max_retries: Maximum number of retries
            backoff_factor: Backoff factor for retries (exponential)
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )
        
        # Configure adapter with connection pooling
        adapter = HTTPAdapter(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=retry_strategy
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        logger.info(
            f"PooledHTTPClient initialized for {base_url} "
            f"(pools: {pool_connections}, maxsize: {pool_maxsize})"
        )
    
    def post(self, path: str, **kwargs):
        """Make POST request"""
        url = f"{self.base_url}{path}"
        return self.session.post(url, **kwargs)
    
    def get(self, path: str, **kwargs):
        """Make GET request"""
        url = f"{self.base_url}{path}"
        return self.session.get(url, **kwargs)
    
    def close(self):
        """Close session and cleanup"""
        self.session.close()
        logger.debug(f"PooledHTTPClient closed for {self.base_url}")


# Global HTTP clients
_http_clients: dict = {}


def get_http_client(base_url: str) -> PooledHTTPClient:
    """
    Get or create pooled HTTP client for base URL
    
    Args:
        base_url: Base URL for the client
        
    Returns:
        PooledHTTPClient instance
    """
    if base_url not in _http_clients:
        _http_clients[base_url] = PooledHTTPClient(
            base_url=base_url,
            pool_connections=getattr(settings, 'HTTP_POOL_CONNECTIONS', 10),
            pool_maxsize=getattr(settings, 'HTTP_POOL_MAXSIZE', 20),
            max_retries=getattr(settings, 'HTTP_MAX_RETRIES', 3),
            backoff_factor=getattr(settings, 'HTTP_BACKOFF_FACTOR', 0.3)
        )
    return _http_clients[base_url]

