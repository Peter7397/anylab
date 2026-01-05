"""
Rate Limiting for RAG Queries
Prevents abuse and manages resource usage
"""
import time
import logging
from typing import Dict, Optional
from collections import defaultdict
from threading import Lock
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter with per-user limits and query cost tracking
    
    Supports:
    - Per-user rate limiting
    - Query cost tracking (based on complexity)
    - Sliding window algorithm
    - Configurable limits
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        cost_per_query: float = 1.0,
        max_cost_per_hour: float = 100.0
    ):
        """
        Initialize rate limiter
        
        Args:
            requests_per_minute: Max requests per minute per user
            requests_per_hour: Max requests per hour per user
            cost_per_query: Base cost per query (can be adjusted by complexity)
            max_cost_per_hour: Maximum cost per hour per user
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.cost_per_query = cost_per_query
        self.max_cost_per_hour = max_cost_per_hour
        self.lock = Lock()
        
        # In-memory tracking (can be moved to Redis for distributed systems)
        self.user_requests: Dict[str, list] = defaultdict(list)
        self.user_costs: Dict[str, list] = defaultdict(list)
    
    def is_allowed(
        self,
        user_id: str,
        query: Optional[str] = None,
        query_cost: Optional[float] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Check if request is allowed
        
        Args:
            user_id: User identifier
            query: Optional query text (for cost calculation)
            query_cost: Optional explicit query cost
            
        Returns:
            Tuple of (is_allowed: bool, reason: Optional[str])
        """
        current_time = time.time()
        
        # Calculate query cost if not provided
        if query_cost is None:
            query_cost = self._calculate_query_cost(query) if query else self.cost_per_query
        
        with self.lock:
            # Clean old entries (older than 1 hour)
            self._clean_old_entries(user_id, current_time)
            
            # Check per-minute limit
            recent_requests = [
                req_time for req_time in self.user_requests[user_id]
                if current_time - req_time < 60
            ]
            
            if len(recent_requests) >= self.requests_per_minute:
                return False, f"Rate limit exceeded: {len(recent_requests)} requests in the last minute (limit: {self.requests_per_minute})"
            
            # Check per-hour limit
            hourly_requests = [
                req_time for req_time in self.user_requests[user_id]
                if current_time - req_time < 3600
            ]
            
            if len(hourly_requests) >= self.requests_per_hour:
                return False, f"Rate limit exceeded: {len(hourly_requests)} requests in the last hour (limit: {self.requests_per_hour})"
            
            # Check cost limit
            hourly_costs = [
                cost for cost, cost_time in self.user_costs[user_id]
                if current_time - cost_time < 3600
            ]
            total_hourly_cost = sum(hourly_costs) + query_cost
            
            if total_hourly_cost > self.max_cost_per_hour:
                return False, f"Cost limit exceeded: {total_hourly_cost:.2f} cost in the last hour (limit: {self.max_cost_per_hour})"
            
            # Record request
            self.user_requests[user_id].append(current_time)
            self.user_costs[user_id].append((query_cost, current_time))
            
            return True, None
    
    def _calculate_query_cost(self, query: Optional[str]) -> float:
        """
        Calculate query cost based on complexity
        
        Args:
            query: Query text
            
        Returns:
            Query cost (float)
        """
        if not query:
            return self.cost_per_query
        
        # Base cost
        cost = self.cost_per_query
        
        # Adjust cost based on query length
        query_length = len(query)
        if query_length > 500:
            cost *= 1.5  # Longer queries cost more
        elif query_length > 1000:
            cost *= 2.0
        
        # Adjust cost based on complexity indicators
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in ['comprehensive', 'detailed', 'explain', 'analyze']):
            cost *= 1.3  # Complex queries cost more
        
        return cost
    
    def _clean_old_entries(self, user_id: str, current_time: float):
        """Remove entries older than 1 hour"""
        # Keep only entries from last hour
        cutoff = current_time - 3600
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if req_time > cutoff
        ]
        self.user_costs[user_id] = [
            (cost, cost_time) for cost, cost_time in self.user_costs[user_id]
            if cost_time > cutoff
        ]
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get rate limiting statistics for user"""
        current_time = time.time()
        
        with self.lock:
            self._clean_old_entries(user_id, current_time)
            
            recent_requests = [
                req_time for req_time in self.user_requests[user_id]
                if current_time - req_time < 60
            ]
            
            hourly_requests = [
                req_time for req_time in self.user_requests[user_id]
                if current_time - req_time < 3600
            ]
            
            hourly_costs = [
                cost for cost, _ in self.user_costs[user_id]
                if current_time - _ < 3600
            ]
            
            return {
                'requests_last_minute': len(recent_requests),
                'requests_last_hour': len(hourly_requests),
                'cost_last_hour': sum(hourly_costs),
                'limit_per_minute': self.requests_per_minute,
                'limit_per_hour': self.requests_per_hour,
                'max_cost_per_hour': self.max_cost_per_hour,
                'remaining_minute': max(0, self.requests_per_minute - len(recent_requests)),
                'remaining_hour': max(0, self.requests_per_hour - len(hourly_requests)),
                'remaining_cost': max(0, self.max_cost_per_hour - sum(hourly_costs))
            }
    
    def reset_user_limits(self, user_id: str):
        """Reset rate limits for a user (admin function)"""
        with self.lock:
            self.user_requests[user_id] = []
            self.user_costs[user_id] = []
            logger.info(f"Rate limits reset for user: {user_id}")


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(
            requests_per_minute=getattr(settings, 'RAG_RATE_LIMIT_PER_MINUTE', 60),
            requests_per_hour=getattr(settings, 'RAG_RATE_LIMIT_PER_HOUR', 1000),
            cost_per_query=getattr(settings, 'RAG_COST_PER_QUERY', 1.0),
            max_cost_per_hour=getattr(settings, 'RAG_MAX_COST_PER_HOUR', 100.0)
        )
    return _rate_limiter

