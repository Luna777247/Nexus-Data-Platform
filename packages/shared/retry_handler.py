"""
Retry Handler with Circuit Breaker Pattern
Provides robust retry logic for external services and operations
"""

import time
import logging
from typing import Callable, Any, Optional, Dict
from functools import wraps
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import threading


logger = logging.getLogger(__name__)


# ============================================
# Circuit Breaker States
# ============================================

class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation, allow all requests
    OPEN = "open"          # Circuit tripped, reject all requests
    HALF_OPEN = "half_open"  # Testing if service recovered


# ============================================
# Circuit Breaker
# ============================================

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5  # Number of failures before opening circuit
    success_threshold: int = 2  # Number of successes to close circuit from half-open
    timeout: int = 60  # Seconds before trying again (half-open)
    expected_exceptions: tuple = (Exception,)  # Exceptions that count as failures


class CircuitBreaker:
    """
    Circuit Breaker implementation
    
    Prevents cascading failures by temporarily blocking calls to failing services
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self._lock = threading.Lock()
        
        logger.info(f"Circuit breaker '{name}' initialized with config: {config}")
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        with self._lock:
            if self.state == CircuitState.OPEN:
                # Check if timeout has passed
                if self.last_failure_time and \
                   datetime.now() - self.last_failure_time > timedelta(seconds=self.config.timeout):
                    logger.info(f"Circuit '{self.name}' moving to HALF_OPEN state")
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is OPEN. "
                        f"Retry after {self.config.timeout} seconds."
                    )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        
        except self.config.expected_exceptions as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call"""
        with self._lock:
            self.failure_count = 0
            
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    logger.info(f"Circuit '{self.name}' moving to CLOSED state")
                    self.state = CircuitState.CLOSED
                    self.success_count = 0
    
    def _on_failure(self):
        """Handle failed call"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.state == CircuitState.HALF_OPEN:
                logger.warning(f"Circuit '{self.name}' reopening due to failure in HALF_OPEN state")
                self.state = CircuitState.OPEN
                self.success_count = 0
            
            elif self.failure_count >= self.config.failure_threshold:
                logger.error(
                    f"Circuit '{self.name}' OPEN after {self.failure_count} failures"
                )
                self.state = CircuitState.OPEN
    
    def reset(self):
        """Manually reset circuit breaker"""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None
        logger.info(f"Circuit '{self.name}' manually reset to CLOSED")


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


# ============================================
# Retry Configuration
# ============================================

@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True  # Add randomness to prevent thundering herd
    retry_on_exceptions: tuple = (Exception,)


# ============================================
# Retry Strategies
# ============================================

class RetryStrategy(str, Enum):
    """Retry strategies"""
    FIXED = "fixed"  # Fixed delay between retries
    EXPONENTIAL = "exponential"  # Exponential backoff
    LINEAR = "linear"  # Linear increase in delay


def calculate_delay(
    attempt: int,
    strategy: RetryStrategy,
    config: RetryConfig
) -> float:
    """Calculate delay before next retry"""
    
    if strategy == RetryStrategy.FIXED:
        delay = config.initial_delay
    
    elif strategy == RetryStrategy.EXPONENTIAL:
        delay = min(
            config.initial_delay * (config.exponential_base ** (attempt - 1)),
            config.max_delay
        )
    
    elif strategy == RetryStrategy.LINEAR:
        delay = min(
            config.initial_delay * attempt,
            config.max_delay
        )
    
    else:
        delay = config.initial_delay
    
    # Add jitter to prevent thundering herd
    if config.jitter:
        import random
        delay = delay * (0.5 + random.random())
    
    return delay


# ============================================
# Retry Decorator
# ============================================

def retry(
    config: Optional[RetryConfig] = None,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    on_retry: Optional[Callable] = None,
    circuit_breaker: Optional[CircuitBreaker] = None
):
    """
    Decorator to add retry logic to functions
    
    Args:
        config: RetryConfig object
        strategy: RetryStrategy (fixed, exponential, linear)
        on_retry: Callback function called before each retry
        circuit_breaker: CircuitBreaker instance for additional protection
    
    Example:
        @retry(
            config=RetryConfig(max_attempts=5, initial_delay=2.0),
            strategy=RetryStrategy.EXPONENTIAL
        )
        def call_external_api():
            # API call code
            pass
    """
    
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    # Use circuit breaker if provided
                    if circuit_breaker:
                        return circuit_breaker.call(func, *args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                
                except config.retry_on_exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts:
                        logger.error(
                            f"Function '{func.__name__}' failed after {config.max_attempts} attempts: {e}"
                        )
                        raise
                    
                    delay = calculate_delay(attempt, strategy, config)
                    
                    logger.warning(
                        f"Function '{func.__name__}' failed (attempt {attempt}/{config.max_attempts}). "
                        f"Retrying in {delay:.2f}s... Error: {e}"
                    )
                    
                    # Call retry callback if provided
                    if on_retry:
                        on_retry(attempt, delay, e)
                    
                    time.sleep(delay)
            
            # Should not reach here, but just in case
            raise last_exception
        
        return wrapper
    return decorator


# ============================================
# Retry with Context Manager
# ============================================

class RetryContext:
    """
    Context manager for retry logic
    
    Example:
        with RetryContext(max_attempts=3) as retry_ctx:
            result = some_risky_operation()
    """
    
    def __init__(
        self,
        config: Optional[RetryConfig] = None,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        circuit_breaker: Optional[CircuitBreaker] = None
    ):
        self.config = config or RetryConfig()
        self.strategy = strategy
        self.circuit_breaker = circuit_breaker
        self.attempt = 0
        self.last_exception = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return True
        
        # Check if exception should trigger retry
        if not isinstance(exc_val, self.config.retry_on_exceptions):
            return False
        
        self.attempt += 1
        self.last_exception = exc_val
        
        if self.attempt >= self.config.max_attempts:
            logger.error(f"Max retry attempts ({self.config.max_attempts}) reached")
            return False
        
        delay = calculate_delay(self.attempt, self.strategy, self.config)
        logger.warning(f"Retry attempt {self.attempt}/{self.config.max_attempts} in {delay:.2f}s")
        time.sleep(delay)
        
        return True  # Suppress exception to retry


# ============================================
# Circuit Breaker Manager
# ============================================

class CircuitBreakerManager:
    """Global circuit breaker manager"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._breakers: Dict[str, CircuitBreaker] = {}
        return cls._instance
    
    def get_breaker(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """Get or create a circuit breaker"""
        if name not in self._breakers:
            with self._lock:
                if name not in self._breakers:
                    config = config or CircuitBreakerConfig()
                    self._breakers[name] = CircuitBreaker(name, config)
        return self._breakers[name]
    
    def get_all_states(self) -> Dict[str, str]:
        """Get states of all circuit breakers"""
        return {
            name: breaker.state.value
            for name, breaker in self._breakers.items()
        }
    
    def reset_all(self):
        """Reset all circuit breakers"""
        for breaker in self._breakers.values():
            breaker.reset()


# Global circuit breaker manager instance
circuit_breaker_manager = CircuitBreakerManager()


# ============================================
# Convenience Functions
# ============================================

def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """Get or create a circuit breaker by name"""
    return circuit_breaker_manager.get_breaker(name, config)


def get_all_circuit_states() -> Dict[str, str]:
    """Get states of all circuit breakers"""
    return circuit_breaker_manager.get_all_states()
