"""
Enhanced Kafka Producer with Retry Logic and Circuit Breaker
Production-ready Kafka producer with comprehensive error handling
"""

import json
import logging
from typing import Dict, Any, Optional, Callable
from kafka import KafkaProducer
from kafka.errors import (
    KafkaError, 
    KafkaTimeoutError,
    NoBrokersAvailable,
    BrokerNotAvailableError
)

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent / "packages" / "shared"))

from retry_handler import retry, RetryConfig, RetryStrategy, get_circuit_breaker
from retry_config_loader import get_retry_config, get_circuit_breaker_config


logger = logging.getLogger(__name__)


class EnhancedKafkaProducer:
    """
    Kafka Producer with retry logic and circuit breaker
    
    Features:
    - Automatic retries on transient failures
    - Circuit breaker to prevent cascading failures
    - Configurable retry strategies
    - Dead Letter Queue (DLQ) support
    - Metrics and monitoring
    """
    
    def __init__(
        self,
        bootstrap_servers: str,
        dlq_topic: Optional[str] = "dlq_general_errors",
        **kafka_config
    ):
        """
        Initialize enhanced Kafka producer
        
        Args:
            bootstrap_servers: Kafka broker addresses
            dlq_topic: Dead Letter Queue topic for failed messages
            **kafka_config: Additional Kafka producer configuration
        """
        self.bootstrap_servers = bootstrap_servers
        self.dlq_topic = dlq_topic
        
        # Get retry configuration
        self.retry_config = get_retry_config('kafka', 'producer')
        self.cb_config = get_circuit_breaker_config('kafka')
        
        # Create circuit breaker for producer
        self.circuit_breaker = get_circuit_breaker(
            'kafka_producer',
            self.cb_config
        )
        
        # Initialize producer with retry logic
        self.producer = self._create_producer(kafka_config)
        
        # Metrics
        self.metrics = {
            'messages_sent': 0,
            'messages_failed': 0,
            'dlq_messages': 0,
            'retries': 0,
            'circuit_breaks': 0
        }
        
        logger.info(f"Enhanced Kafka Producer initialized with retry config: {self.retry_config}")
    
    def _create_producer(self, kafka_config: Dict) -> KafkaProducer:
        """Create Kafka producer with connection retry"""
        
        @retry(
            config=self.retry_config,
            strategy=RetryStrategy.EXPONENTIAL,
            on_retry=lambda attempt, delay, error: logger.warning(
                f"Kafka connection retry {attempt}, waiting {delay:.2f}s: {error}"
            )
        )
        def connect():
            return KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',  # Wait for all replicas
                retries=0,  # We handle retries ourselves
                max_in_flight_requests_per_connection=1,  # Ensure ordering
                **kafka_config
            )
        
        try:
            return connect()
        except Exception as e:
            logger.error(f"Failed to create Kafka producer after retries: {e}")
            raise
    
    def send_message(
        self,
        topic: str,
        message: Dict[Any, Any],
        key: Optional[bytes] = None,
        on_success: Optional[Callable] = None,
        on_error: Optional[Callable] = None
    ) -> bool:
        """
        Send message to Kafka with retry logic
        
        Args:
            topic: Kafka topic name
            message: Message payload (will be JSON serialized)
            key: Optional message key for partitioning
            on_success: Callback on successful send
            on_error: Callback on failure
        
        Returns:
            True if message sent successfully, False otherwise
        """
        
        @retry(
            config=self.retry_config,
            strategy=RetryStrategy.EXPONENTIAL,
            circuit_breaker=self.circuit_breaker,
            on_retry=lambda attempt, delay, error: self._on_retry(attempt, delay, error, message)
        )
        def send():
            future = self.producer.send(topic, value=message, key=key)
            return future.get(timeout=10)  # Wait for acknowledgment
        
        try:
            metadata = send()
            self.metrics['messages_sent'] += 1
            
            if on_success:
                on_success(metadata)
            
            logger.debug(f"Message sent to {topic}: partition={metadata.partition}, offset={metadata.offset}")
            return True
        
        except Exception as e:
            self.metrics['messages_failed'] += 1
            logger.error(f"Failed to send message to {topic} after retries: {e}")
            
            # Send to DLQ
            if self.dlq_topic:
                self._send_to_dlq(topic, message, str(e))
            
            if on_error:
                on_error(e)
            
            return False
    
    def _on_retry(self, attempt: int, delay: float, error: Exception, message: Dict):
        """Callback called on each retry attempt"""
        self.metrics['retries'] += 1
        logger.warning(
            f"Kafka send retry {attempt}/{self.retry_config.max_attempts}, "
            f"waiting {delay:.2f}s. Error: {error}"
        )
    
    def _send_to_dlq(self, original_topic: str, message: Dict, error: str):
        """Send failed message to Dead Letter Queue"""
        try:
            dlq_message = {
                'original_topic': original_topic,
                'original_message': message,
                'error': error,
                'timestamp': str(Path(__file__).parent),
                'retry_count': self.retry_config.max_attempts
            }
            
            # Send to DLQ without retry (avoid infinite loop)
            future = self.producer.send(self.dlq_topic, value=dlq_message)
            future.get(timeout=5)
            
            self.metrics['dlq_messages'] += 1
            logger.info(f"Message sent to DLQ: {self.dlq_topic}")
        
        except Exception as e:
            logger.error(f"Failed to send message to DLQ: {e}")
    
    def flush(self, timeout: Optional[float] = None):
        """Flush pending messages"""
        try:
            self.producer.flush(timeout=timeout)
        except Exception as e:
            logger.error(f"Error flushing producer: {e}")
    
    def close(self):
        """Close producer"""
        try:
            self.producer.close()
            logger.info("Kafka producer closed")
        except Exception as e:
            logger.error(f"Error closing producer: {e}")
    
    def get_metrics(self) -> Dict[str, int]:
        """Get producer metrics"""
        return self.metrics.copy()
    
    def reset_metrics(self):
        """Reset all metrics to zero"""
        for key in self.metrics:
            self.metrics[key] = 0


# ============================================
# Example Usage
# ============================================

def example_usage():
    """Example of using EnhancedKafkaProducer"""
    
    # Create producer
    producer = EnhancedKafkaProducer(
        bootstrap_servers='kafka-1:9092,kafka-2:9093,kafka-3:9094',
        dlq_topic='dlq_general_errors'
    )
    
    # Send message with callbacks
    def on_success(metadata):
        print(f"✅ Message sent: partition={metadata.partition}, offset={metadata.offset}")
    
    def on_error(error):
        print(f"❌ Message failed: {error}")
    
    message = {
        'user_id': 'user_123',
        'event_type': 'page_view',
        'timestamp': '2026-02-13T10:30:00Z'
    }
    
    success = producer.send_message(
        topic='topic_user_events',
        message=message,
        on_success=on_success,
        on_error=on_error
    )
    
    # Get metrics
    metrics = producer.get_metrics()
    print(f"Producer metrics: {metrics}")
    
    # Close producer
    producer.flush()
    producer.close()


if __name__ == "__main__":
    example_usage()
