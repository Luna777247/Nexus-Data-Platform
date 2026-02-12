"""
Schema Registry Integration for Nexus Data Platform
Location: pipelines/airflow/utils/schema_registry.py

Purpose:
- Register and validate Avro/JSON schemas
- Schema evolution management
- Integration with Confluent Schema Registry
"""

import json
import logging
from typing import Dict, Any, Optional, List
import os

try:
    from confluent_kafka.schema_registry import SchemaRegistryClient, Schema
    from confluent_kafka.schema_registry.avro import AvroSerializer, AvroDeserializer
    from confluent_kafka.serialization import SerializationContext, MessageField
    HAS_SCHEMA_REGISTRY = True
except ModuleNotFoundError:
    HAS_SCHEMA_REGISTRY = False
    logger = logging.getLogger(__name__)
    logger.warning("⚠️  confluent-kafka not installed, Schema Registry disabled")

logger = logging.getLogger(__name__)


class SchemaRegistryManager:
    """Manage schemas in Confluent Schema Registry"""
    
    def __init__(self, schema_registry_url: Optional[str] = None):
        """
        Initialize Schema Registry Manager
        
        Args:
            schema_registry_url: Schema Registry URL (default from env)
        """
        if not HAS_SCHEMA_REGISTRY:
            logger.error("❌ Schema Registry client not available (install confluent-kafka)")
            self.client = None
            return
        
        self.schema_registry_url = schema_registry_url or os.getenv(
            'SCHEMA_REGISTRY_URL',
            'http://schema-registry:8081'
        )
        
        try:
            self.client = SchemaRegistryClient({
                'url': self.schema_registry_url
            })
            logger.info(f"✅ Schema Registry connected: {self.schema_registry_url}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Schema Registry: {e}")
            self.client = None
    
    def register_schema(
        self,
        subject: str,
        schema_str: str,
        schema_type: str = "AVRO"
    ) -> Optional[int]:
        """
        Register a new schema
        
        Args:
            subject: Schema subject name (e.g., 'events-value')
            schema_str: Schema definition (JSON string)
            schema_type: Schema type (AVRO, JSON, PROTOBUF)
            
        Returns:
            int: Schema ID if successful, None otherwise
        """
        if not self.client:
            logger.error("❌ Schema Registry client not available")
            return None
        
        try:
            schema = Schema(schema_str, schema_type)
            schema_id = self.client.register_schema(subject, schema)
            
            logger.info(f"✅ Schema registered: {subject} (ID: {schema_id})")
            return schema_id
            
        except Exception as e:
            logger.error(f"❌ Failed to register schema '{subject}': {e}")
            return None
    
    def get_schema(self, subject: str, version: Optional[int] = None) -> Optional[Schema]:
        """
        Get schema for a subject
        
        Args:
            subject: Schema subject name
            version: Specific version (None for latest)
            
        Returns:
            Schema: Schema object if found, None otherwise
        """
        if not self.client:
            return None
        
        try:
            if version:
                schema = self.client.get_version(subject, version)
            else:
                schema = self.client.get_latest_version(subject)
            
            logger.info(f"✅ Retrieved schema: {subject} (version {schema.version})")
            return schema
            
        except Exception as e:
            logger.error(f"❌ Failed to get schema '{subject}': {e}")
            return None
    
    def check_compatibility(
        self,
        subject: str,
        new_schema_str: str,
        schema_type: str = "AVRO"
    ) -> bool:
        """
        Check if new schema is compatible with existing
        
        Args:
            subject: Schema subject name
            new_schema_str: New schema definition
            schema_type: Schema type
            
        Returns:
            bool: True if compatible, False otherwise
        """
        if not self.client:
            return False
        
        try:
            new_schema = Schema(new_schema_str, schema_type)
            is_compatible = self.client.test_compatibility(subject, new_schema)
            
            if is_compatible:
                logger.info(f"✅ Schema is compatible: {subject}")
            else:
                logger.warning(f"⚠️  Schema NOT compatible: {subject}")
            
            return is_compatible
            
        except Exception as e:
            logger.error(f"❌ Failed to check compatibility: {e}")
            return False
    
    def list_subjects(self) -> List[str]:
        """
        List all schema subjects
        
        Returns:
            list: List of subject names
        """
        if not self.client:
            return []
        
        try:
            subjects = self.client.get_subjects()
            logger.info(f"📋 Found {len(subjects)} schema subjects")
            return subjects
        except Exception as e:
            logger.error(f"❌ Failed to list subjects: {e}")
            return []
    
    def get_schema_versions(self, subject: str) -> List[int]:
        """
        Get all versions of a schema
        
        Args:
            subject: Schema subject name
            
        Returns:
            list: List of version numbers
        """
        if not self.client:
            return []
        
        try:
            versions = self.client.get_versions(subject)
            logger.info(f"📋 Schema '{subject}' has {len(versions)} versions")
            return versions
        except Exception as e:
            logger.error(f"❌ Failed to get versions: {e}")
            return []
    
    def create_avro_serializer(self, schema_str: str) -> Optional[AvroSerializer]:
        """
        Create Avro serializer
        
        Args:
            schema_str: Avro schema definition
            
        Returns:
            AvroSerializer: Serializer instance
        """
        if not HAS_SCHEMA_REGISTRY:
            return None
        
        try:
            return AvroSerializer(
                schema_registry_client=self.client,
                schema_str=schema_str
            )
        except Exception as e:
            logger.error(f"❌ Failed to create Avro serializer: {e}")
            return None
    
    def create_avro_deserializer(self, schema_str: str) -> Optional[AvroDeserializer]:
        """
        Create Avro deserializer
        
        Args:
            schema_str: Avro schema definition
            
        Returns:
            AvroDeserializer: Deserializer instance
        """
        if not HAS_SCHEMA_REGISTRY:
            return None
        
        try:
            return AvroDeserializer(
                schema_registry_client=self.client,
                schema_str=schema_str
            )
        except Exception as e:
            logger.error(f"❌ Failed to create Avro deserializer: {e}")
            return None


class SchemaValidator:
    """Validate data against registered schemas"""
    
    def __init__(self, schema_registry_url: Optional[str] = None):
        self.registry = SchemaRegistryManager(schema_registry_url)
    
    def validate_message(
        self,
        message: Dict[str, Any],
        subject: str,
        version: Optional[int] = None
    ) -> tuple[bool, List[str]]:
        """
        Validate message against schema
        
        Args:
            message: Message to validate
            subject: Schema subject
            version: Schema version (None for latest)
            
        Returns:
            tuple: (is_valid, errors_list)
        """
        if not self.registry.client:
            return False, ["Schema Registry not available"]
        
        try:
            schema = self.registry.get_schema(subject, version)
            if not schema:
                return False, [f"Schema not found: {subject}"]
            
            # Parse schema (Avro or JSON Schema)
            schema_dict = json.loads(schema.schema_str)
            
            # Simple validation (can be enhanced with avro-python3 or jsonschema)
            errors = self._validate_fields(message, schema_dict)
            
            is_valid = len(errors) == 0
            
            if is_valid:
                logger.debug(f"✅ Message valid for schema: {subject}")
            else:
                logger.warning(f"⚠️  Message validation failed: {errors}")
            
            return is_valid, errors
            
        except Exception as e:
            logger.error(f"❌ Validation error: {e}")
            return False, [str(e)]
    
    def _validate_fields(
        self,
        message: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> List[str]:
        """Simple field validation (can be enhanced)"""
        errors = []
        
        if 'fields' in schema:
            # Avro schema
            for field in schema['fields']:
                field_name = field['name']
                if field_name not in message:
                    # Check if field has default
                    if 'default' not in field:
                        errors.append(f"Missing required field: {field_name}")
        
        elif 'required' in schema:
            # JSON Schema
            for field_name in schema['required']:
                if field_name not in message:
                    errors.append(f"Missing required field: {field_name}")
        
        return errors


# Example schemas
EXAMPLE_EVENT_SCHEMA = """{
    "type": "record",
    "name": "Event",
    "namespace": "io.nexus.events",
    "fields": [
        {"name": "event_id", "type": "string"},
        {"name": "event_type", "type": "string"},
        {"name": "user_id", "type": "int"},
        {"name": "timestamp", "type": "long", "logicalType": "timestamp-millis"},
        {"name": "amount", "type": ["null", "double"], "default": null},
        {"name": "region", "type": "string"},
        {"name": "source", "type": "string"}
    ]
}"""


# Convenience function
def register_event_schema(schema_registry_url: Optional[str] = None) -> Optional[int]:
    """Register example event schema"""
    manager = SchemaRegistryManager(schema_registry_url)
    return manager.register_schema("events-value", EXAMPLE_EVENT_SCHEMA, "AVRO")
