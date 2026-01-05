"""
Standardized Error Handling for RAG Services
Provides consistent error handling patterns across all services
"""
import logging
from typing import Any, Optional, Dict, TypeVar, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"  # Recoverable, can continue
    MEDIUM = "medium"  # May affect quality but can continue
    HIGH = "high"  # Significant issue, may need fallback
    CRITICAL = "critical"  # Cannot continue, must fail


@dataclass
class ServiceResult:
    """
    Standard result object for service operations
    
    Provides consistent success/error handling across all services
    """
    success: bool
    data: Any = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    severity: ErrorSeverity = ErrorSeverity.LOW
    metadata: Optional[Dict[str, Any]] = None
    
    def is_success(self) -> bool:
        """Check if operation was successful"""
        return self.success
    
    def is_failure(self) -> bool:
        """Check if operation failed"""
        return not self.success
    
    def get_data_or_raise(self):
        """Get data or raise exception if failed"""
        if not self.success:
            raise ServiceError(
                self.error or "Unknown error",
                code=self.error_code,
                severity=self.severity
            )
        return self.data
    
    @classmethod
    def success_result(cls, data: Any, metadata: Optional[Dict] = None) -> 'ServiceResult':
        """Create success result"""
        return cls(success=True, data=data, metadata=metadata)
    
    @classmethod
    def failure_result(
        cls,
        error: str,
        error_code: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        metadata: Optional[Dict] = None
    ) -> 'ServiceResult':
        """Create failure result"""
        return cls(
            success=False,
            error=error,
            error_code=error_code,
            severity=severity,
            metadata=metadata
        )


class ServiceError(Exception):
    """Base exception for service errors"""
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        metadata: Optional[Dict] = None
    ):
        super().__init__(message)
        self.code = code
        self.severity = severity
        self.metadata = metadata or {}


class RAGServiceError(ServiceError):
    """RAG service specific errors"""
    pass


class EmbeddingError(ServiceError):
    """Embedding generation errors"""
    pass


class GraphServiceError(ServiceError):
    """Graph service errors"""
    pass


def handle_service_error(
    error: Exception,
    context: str = "",
    default_error_code: str = "unknown_error",
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
) -> ServiceResult:
    """
    Standardized error handling for service operations
    
    Args:
        error: Exception that occurred
        context: Context where error occurred
        default_error_code: Default error code if not in exception
        severity: Error severity level
        
    Returns:
        ServiceResult with error information
    """
    error_message = str(error)
    error_code = default_error_code
    
    # Extract error code from exception if available
    if hasattr(error, 'code'):
        error_code = error.code
    elif hasattr(error, 'default_code'):
        error_code = error.default_code
    
    # Determine severity based on error type
    if isinstance(error, (ConnectionError, TimeoutError)):
        severity = ErrorSeverity.HIGH
    elif isinstance(error, ValueError):
        severity = ErrorSeverity.MEDIUM
    elif isinstance(error, KeyError, AttributeError):
        severity = ErrorSeverity.LOW
    
    # Log error with context
    log_message = f"Service error in {context}: {error_message}" if context else f"Service error: {error_message}"
    
    if severity == ErrorSeverity.CRITICAL:
        logger.critical(log_message, exc_info=True)
    elif severity == ErrorSeverity.HIGH:
        logger.error(log_message, exc_info=True)
    elif severity == ErrorSeverity.MEDIUM:
        logger.warning(log_message)
    else:
        logger.info(log_message)
    
    return ServiceResult.failure_result(
        error=error_message,
        error_code=error_code,
        severity=severity,
        metadata={'context': context, 'exception_type': type(error).__name__}
    )


def safe_execute(
    func: Callable[[], T],
    context: str = "",
    default_error_code: str = "execution_error",
    return_result: bool = False
) -> T | ServiceResult:
    """
    Safely execute a function with standardized error handling
    
    Args:
        func: Function to execute
        context: Context for error messages
        default_error_code: Default error code
        return_result: If True, return ServiceResult instead of raising
        
    Returns:
        Function result or ServiceResult if return_result=True
        
    Raises:
        ServiceError: If return_result=False and error occurs
    """
    try:
        result = func()
        if return_result:
            return ServiceResult.success_result(result)
        return result
    except Exception as e:
        error_result = handle_service_error(e, context, default_error_code)
        if return_result:
            return error_result
        raise ServiceError(
            error_result.error,
            code=error_result.error_code,
            severity=error_result.severity,
            metadata=error_result.metadata
        ) from e


def with_error_handling(
    context: str = "",
    default_error_code: str = "operation_error",
    return_result: bool = False
):
    """
    Decorator for standardized error handling
    
    Usage:
        @with_error_handling(context="embedding_generation", return_result=True)
        def generate_embedding(text):
            ...
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            return safe_execute(
                lambda: func(*args, **kwargs),
                context=context or func.__name__,
                default_error_code=default_error_code,
                return_result=return_result
            )
        return wrapper
    return decorator

