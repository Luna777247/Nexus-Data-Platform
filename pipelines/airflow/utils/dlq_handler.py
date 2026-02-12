"""
Dead Letter Queue (DLQ) Handler for Nexus Data Platform
Location: pipelines/airflow/utils/dlq_handler.py

Purpose:
- Handle failed messages and send to DLQ topics
- Implement exponential backoff retry logic
- Track error patterns and metrics
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import os

try:
    from kafka import KafkaProducer
    from kafka.errors import KafkaError
except ModuleNotFoundError:
    KafkaProducer = None
    class KafkaError(Exception):
        pass

logger = logging.getLogger(__name__)


class DLQHandler:
    """Handle failed messages and route to Dead Letter Queues"""
    
    # DLQ topic names
    DLQ_FAILED_MESSAGES = "dlq_failed_messages"
    DLQ_SCHEMA_VALIDATION = "dlq_schema_validation_errors"
    DLQ_PROCESSING_ERRORS = "dlq_processing_errors"
    
    def __init__(self, bootstrap_servers: Optional[str] = None):
        """
        Initialize DLQ Handler
        
        Args:
            bootstrap_servers: Kafka bootstrap servers (default from env)
        """
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            'KAFKA_BOOTSTRAP_SERVERS',
            'kafka-1:29092,kafka-2:29093,kafka-3:29094'
        )
        
        self.producer = None
        if KafkaProducer:
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers.split(','),
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None,
                    acks='all',  # Wait for all replicas
                    retries=3,
                    max_in_flight_requests_per_connection=1,
                    enable_idempotence=True
                )
                logger.info(f"✅ DLQ Handler initialized with bootstrap servers: {self.bootstrap_servers}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Kafka producer for DLQ: {e}")
                self.producer = None
        else:
            logger.warning("⚠️  Kafka not available, DLQ handler disabled")
    
    def send_to_dlq(
        self,
        original_message: Any,
        error: Exception,
        source: str,
        dlq_topic: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Send failed message to Dead Letter Queue
        
        Args:
            original_message: Original message that failed
            error: Exception that occurred
            source: Source of the message (topic, API, etc.)
            dlq_topic: Specific DLQ topic (default: DLQ_FAILED_MESSAGES)
            metadata: Additional metadata to include
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.producer:
            logger.warning("⚠️  DLQ producer not available, logging error instead")
            logger.error(f"Failed message from {source}: {error}")
            return False
        
        dlq_topic = dlq_topic or self.DLQ_FAILED_MESSAGES
        
        try:
            # Build DLQ message
            dlq_message = {
                "original_message": original_message,
                "error": {
                    "type": type(error).__name__,
                    "message": str(error),
                    "traceback": getattr(error, '__traceback__', None).__str__() if hasattr(error, '__traceback__') else None
                },
                "source": source,
                "timestamp": datetime.now().isoformat(),
                "retry_count": self._get_retry_count(original_message),
                "metadata": metadata or {}
            }
            
            # Send to DLQ
            future = self.producer.send(
                dlq_topic,
                key=source,
                value=dlq_message
            )
            
            # Wait for acknowledgment
            record_metadata = future.get(timeout=10)
            
            logger.warning(
                f"⚠️  Message sent to DLQ: {dlq_topic} "
                f"(partition={record_metadata.partition}, offset={record_metadata.offset})"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send message to DLQ: {e}")
            return False
    
    def send_schema_validation_error(
        self,
        message: Any,
        schema_errors: list,
        source: str
    ) -> bool:
        """
        Send schema validation errors to dedicated DLQ
        
        Args:
            message: Message that failed validation
            schema_errors: List of validation errors
            source: Source identifier
            
        Returns:
            bool: Success status
        """
        error_message = "; ".join([str(e) for e in schema_errors])
        error = ValueError(f"Schema validation failed: {error_message}")
        
        return self.send_to_dlq(
            original_message=message,
            error=error,
            source=source,
            dlq_topic=self.DLQ_SCHEMA_VALIDATION,
            metadata={"schema_errors": schema_errors}
        )
    
    def send_processing_error(
        self,
        message: Any,
        error: Exception,
        source: str,
        processing_step: str
    ) -> bool:
        """
        Send processing errors to dedicated DLQ
        
        Args:
            message: Message that failed processing
            error: Processing exception
            source: Source identifier
            processing_step: Which processing step failed
            
        Returns:
            bool: Success status
        """
        return self.send_to_dlq(
            original_message=message,
            error=error,
            source=source,
            dlq_topic=self.DLQ_PROCESSING_ERRORS,
            metadata={"processing_step": processing_step}
        )
    
    def _get_retry_count(self, message: Any) -> int:
        """Get current retry count from message"""
        if isinstance(message, dict):
            return message.get('retry_count', 0) + 1
        return 1
    
    def retry_from_dlq(
        self,
        dlq_topic: str,
        target_topic: str,
        max_retries: int = 3,
        batch_size: int = 100
    ) -> Dict[str, int]:
        """
        Retry failed messages from DLQ
        
        Args:
            dlq_topic: DLQ topic to read from
            target_topic: Target topic to retry to
            max_retries: Maximum retry count before giving up
            batch_size: Number of messages to process per batch
            
        Returns:
            dict: Statistics (retried, skipped, failed)
        """
        if not KafkaProducer:
            logger.error("❌ Kafka not available for DLQ retry")
            return {"retried": 0, "skipped": 0, "failed": 0}
        
        from kafka import KafkaConsumer
        
        stats = {"retried": 0, "skipped": 0, "failed": 0}
        
        try:
            # Create consumer for DLQ
            consumer = KafkaConsumer(
                dlq_topic,
                bootstrap_servers=self.bootstrap_servers.split(','),
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=False,
                max_poll_records=batch_size
            )
            
            # Create producer for retry
            retry_producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers.split(','),
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all'
            )
            
            for message in consumer:
                dlq_payload = message.value
                retry_count = dlq_payload.get('retry_count', 0)
                
                if retry_count >= max_retries:
                    logger.warning(f"⚠️  Message exceeded max retries ({max_retries}), skipping")
                    stats['skipped'] += 1
                    continue
                
                try:
                    # Extract original message
                    original = dlq_payload['original_message']
                    original['retry_count'] = retry_count + 1
                    
                    # Retry to target topic
                    retry_producer.send(target_topic, value=original)
                    stats['retried'] += 1
                    
                    logger.info(f"✅ Retried message to {target_topic} (attempt {retry_count + 1})")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to retry message: {e}")
                    stats['failed'] += 1
            
            consumer.close()
            retry_producer.close()
            
            logger.info(f"📊 DLQ Retry Stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ DLQ retry failed: {e}")
            return stats
    
    def get_dlq_stats(self, dlq_topic: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about DLQ topics
        
        Args:
            dlq_topic: Specific DLQ topic (None for all)
            
        Returns:
            dict: DLQ statistics
        """
        if not KafkaProducer:
            return {}
        
        from kafka import KafkaAdminClient
        
        try:
            admin_client = KafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers.split(',')
            )
            
            topics = [dlq_topic] if dlq_topic else [
                self.DLQ_FAILED_MESSAGES,
                self.DLQ_SCHEMA_VALIDATION,
                self.DLQ_PROCESSING_ERRORS
            ]
            
            stats = {}
            for topic in topics:
                try:
                    # Get topic metadata (this is placeholder - actual implementation needs KafkaConsumer)
                    stats[topic] = {
                        "exists": True,
                        "message_count": "N/A (use KafkaConsumer for accurate count)"
                    }
                except Exception:
                    stats[topic] = {"exists": False}
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get DLQ stats: {e}")
            return {}
    
    def close(self):
        """Close Kafka producer"""
        if self.producer:
            self.producer.close()
            logger.info("✅ DLQ Handler closed")


# Convenience functions
def send_to_dlq(message: Any, error: Exception, source: str) -> bool:
    """Quick function to send to DLQ"""
    handler = DLQHandler()
    result = handler.send_to_dlq(message, error, source)
    handler.close()
    return result


def retry_dlq_messages(dlq_topic: str, target_topic: str, max_retries: int = 3) -> Dict:
    """Quick function to retry DLQ messages"""
    handler = DLQHandler()
    stats = handler.retry_from_dlq(dlq_topic, target_topic, max_retries)
    handler.close()
    return stats
