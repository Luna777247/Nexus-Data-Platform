"""
Retry Configuration Loader
Loads retry and circuit breaker configurations from YAML file
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from retry_handler import RetryConfig, CircuitBreakerConfig, RetryStrategy


logger = logging.getLogger(__name__)


class RetryConfigLoader:
    """Load retry configurations from YAML file"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize config loader
        
        Args:
            config_path: Path to retry-config.yaml file
        """
        if config_path is None:
            # Try to find config file in standard locations
            possible_paths = [
                Path(__file__).parent.parent.parent / "configs" / "retry-config.yaml",  # From packages/shared
                Path.cwd() / "configs" / "retry-config.yaml",
                Path.cwd() / "retry-config.yaml",
            ]
            
            for path in possible_paths:
                if path.exists():
                    config_path = str(path)
                    break
        
        if config_path is None or not Path(config_path).exists():
            logger.warning(f"Retry config file not found. Using default configurations.")
            self.config_data = {}
        else:
            with open(config_path, 'r') as f:
                self.config_data = yaml.safe_load(f) or {}
            logger.info(f"Loaded retry configuration from {config_path}")
    
    def get_retry_config(self, service: str, operation: str = "default") -> RetryConfig:
        """
        Get RetryConfig for a specific service and operation
        
        Args:
            service: Service name (e.g., 'kafka', 'spark', 'database')
            operation: Operation type (e.g., 'producer', 'consumer', 'read')
        
        Returns:
            RetryConfig instance
        """
        # Get service config
        service_config = self.config_data.get(service, {})
        
        # Get operation-specific config or default
        operation_config = service_config.get(operation, {})
        
        # Fallback to default config
        default_config = self.config_data.get('default', {})
        
        # Merge configs (operation > service > default)
        config = {
            'max_attempts': operation_config.get('max_attempts') or 
                          service_config.get('max_attempts') or 
                          default_config.get('max_attempts', 3),
            
            'initial_delay': operation_config.get('initial_delay') or 
                           service_config.get('initial_delay') or 
                           default_config.get('initial_delay', 1.0),
            
            'max_delay': operation_config.get('max_delay') or 
                        service_config.get('max_delay') or 
                        default_config.get('max_delay', 30.0),
            
            'exponential_base': operation_config.get('exponential_base') or 
                              service_config.get('exponential_base') or 
                              default_config.get('exponential_base', 2.0),
            
            'jitter': operation_config.get('jitter') if 'jitter' in operation_config else \
                     service_config.get('jitter') if 'jitter' in service_config else \
                     default_config.get('jitter', True),
        }
        
        return RetryConfig(
            max_attempts=config['max_attempts'],
            initial_delay=config['initial_delay'],
            max_delay=config['max_delay'],
            exponential_base=config['exponential_base'],
            jitter=config['jitter']
        )
    
    def get_circuit_breaker_config(self, service: str) -> CircuitBreakerConfig:
        """
        Get CircuitBreakerConfig for a specific service
        
        Args:
            service: Service name (e.g., 'kafka', 'spark', 'database')
        
        Returns:
            CircuitBreakerConfig instance
        """
        service_config = self.config_data.get(service, {})
        cb_config = service_config.get('circuit_breaker', {})
        default_cb = self.config_data.get('default', {}).get('circuit_breaker', {})
        
        return CircuitBreakerConfig(
            failure_threshold=cb_config.get('failure_threshold') or 
                            default_cb.get('failure_threshold', 5),
            success_threshold=cb_config.get('success_threshold') or 
                            default_cb.get('success_threshold', 2),
            timeout=cb_config.get('timeout') or 
                   default_cb.get('timeout', 60)
        )
    
    def get_retry_strategy(self, service: str, operation: str = "default") -> RetryStrategy:
        """
        Get retry strategy for a service/operation
        
        Args:
            service: Service name
            operation: Operation type
        
        Returns:
            RetryStrategy enum value
        """
        service_config = self.config_data.get(service, {})
        operation_config = service_config.get(operation, {})
        default_config = self.config_data.get('default', {})
        
        strategy_str = (
            operation_config.get('strategy') or 
            service_config.get('strategy') or 
            default_config.get('strategy', 'exponential')
        )
        
        try:
            return RetryStrategy(strategy_str.lower())
        except ValueError:
            logger.warning(f"Invalid strategy '{strategy_str}', using exponential")
            return RetryStrategy.EXPONENTIAL


# Global config loader instance
_config_loader: Optional[RetryConfigLoader] = None


def get_config_loader() -> RetryConfigLoader:
    """Get global RetryConfigLoader instance"""
    global _config_loader
    if _config_loader is None:
        _config_loader = RetryConfigLoader()
    return _config_loader


# Convenience functions
def get_retry_config(service: str, operation: str = "default") -> RetryConfig:
    """Get RetryConfig for service/operation"""
    return get_config_loader().get_retry_config(service, operation)


def get_circuit_breaker_config(service: str) -> CircuitBreakerConfig:
    """Get CircuitBreakerConfig for service"""
    return get_config_loader().get_circuit_breaker_config(service)


def get_retry_strategy(service: str, operation: str = "default") -> RetryStrategy:
    """Get RetryStrategy for service/operation"""
    return get_config_loader().get_retry_strategy(service, operation)
