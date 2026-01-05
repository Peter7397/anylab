"""
Circuit Breaker Pattern for External Service Calls
Prevents cascading failures by stopping requests when service is down
"""
import logging
import time
from enum import Enum
from typing import Callable, Any, Optional
from threading import Lock
from django.conf import settings

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker implementation with exponential backoff
    
    Prevents overwhelming a failing service by:
    1. Opening circuit after failure threshold
    2. Rejecting requests when open
    3. Testing recovery in half-open state
    4. Closing circuit when service recovers
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
        name: str = "circuit_breaker"
    ):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying half-open
            expected_exception: Exception type that counts as failure
            name: Name for logging
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED
        self.lock = Lock()
        
        # Statistics
        self.total_calls = 0
        self.total_failures = 0
        self.total_rejected = 0
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: If function call fails
        """
        with self.lock:
            self.total_calls += 1
            
            # Check if circuit should transition
            self._check_state_transition()
            
            # Reject if circuit is open
            if self.state == CircuitState.OPEN:
                self.total_rejected += 1
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Service unavailable. Last failure: {self.last_failure_time}"
                )
        
        # Try to execute function
        try:
            result = func(*args, **kwargs)
            
            # Success - reset failure count if in half-open
            with self.lock:
                if self.state == CircuitState.HALF_OPEN:
                    logger.info(f"Circuit breaker '{self.name}' recovered, closing circuit")
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.last_failure_time = None
                elif self.state == CircuitState.CLOSED:
                    # Reset failure count on success
                    self.failure_count = 0
            
            return result
            
        except self.expected_exception as e:
            # Failure - increment count
            with self.lock:
                self.total_failures += 1
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    if self.state != CircuitState.OPEN:
                        logger.warning(
                            f"Circuit breaker '{self.name}' opened after {self.failure_count} failures. "
                            f"Will retry after {self.recovery_timeout}s"
                        )
                    self.state = CircuitState.OPEN
                elif self.state == CircuitState.HALF_OPEN:
                    # Failed test - back to open
                    logger.warning(f"Circuit breaker '{self.name}' test failed, reopening")
                    self.state = CircuitState.OPEN
            
            raise
    
    def _check_state_transition(self):
        """Check if circuit should transition states"""
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time:
                elapsed = time.time() - self.last_failure_time
                if elapsed >= self.recovery_timeout:
                    logger.info(f"Circuit breaker '{self.name}' entering HALF_OPEN state for testing")
                    self.state = CircuitState.HALF_OPEN
                    self.failure_count = 0
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics"""
        with self.lock:
            return {
                'name': self.name,
                'state': self.state.value,
                'failure_count': self.failure_count,
                'total_calls': self.total_calls,
                'total_failures': self.total_failures,
                'total_rejected': self.total_rejected,
                'last_failure_time': self.last_failure_time,
                'success_rate': (
                    (self.total_calls - self.total_failures - self.total_rejected) / self.total_calls
                    if self.total_calls > 0 else 0.0
                )
            }
    
    def reset(self):
        """Manually reset circuit breaker"""
        with self.lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None
            logger.info(f"Circuit breaker '{self.name}' manually reset")


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    pass


# Global circuit breakers for common services
_ollama_circuit_breaker: Optional[CircuitBreaker] = None


def get_ollama_circuit_breaker() -> CircuitBreaker:
    """Get or create Ollama circuit breaker"""
    global _ollama_circuit_breaker
    if _ollama_circuit_breaker is None:
        _ollama_circuit_breaker = CircuitBreaker(
            failure_threshold=getattr(settings, 'OLLAMA_CIRCUIT_BREAKER_THRESHOLD', 5),
            recovery_timeout=getattr(settings, 'OLLAMA_CIRCUIT_BREAKER_TIMEOUT', 60.0),
            expected_exception=Exception,
            name="ollama"
        )
    return _ollama_circuit_breaker

