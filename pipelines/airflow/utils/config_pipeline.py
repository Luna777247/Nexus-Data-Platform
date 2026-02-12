# Generic Data Extraction & Transformation Engine
# Location: pipelines/airflow/utils/config_pipeline.py
# Purpose: Extensible extraction, validation, and loading for any data source

"""
Config-driven pipeline utilities for Nexus Data Platform
- Load source configurations
- Generic extraction from APIs, databases, etc.
- Schema validation
- Kafka publishing
- Iceberg loading
"""

import yaml
import json
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
try:
    import pandas as pd
except ModuleNotFoundError:
    pd = None

try:
    from kafka import KafkaProducer
    from kafka.errors import KafkaError
except ModuleNotFoundError:
    KafkaProducer = None

    class KafkaError(Exception):
        pass
import os

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Load and manage data source configurations"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize config loader
        
        Args:
            config_path: Path to sources.yaml
        """
        self.config_path = config_path or os.getenv('CONFIG_SOURCES_PATH', 'configs/sources.yaml')
        self.config = self._load_config()
        self.global_config = self.config.get('global', {})
        
    def _load_config(self) -> dict:
        """Load configuration from DB (preferred) or YAML file"""
        if self._should_use_db():
            logger.info("🔍 DATA_SOURCES_DB_ENABLED=true, attempting to load from PostgreSQL...")
            config = self._load_config_from_db()
            if config:
                logger.info(f"✅ Loaded {len(config.get('sources', []))} sources from PostgreSQL database")
                return config
            logger.warning("⚠️  DB load failed, falling back to YAML file")
        else:
            logger.info("📄 DATA_SOURCES_DB_ENABLED=false, loading from YAML file")

        return self._load_config_from_file()

    def _load_config_from_file(self) -> dict:
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
            logger.info(f"📄 Loaded {len(config.get('sources', []))} sources from YAML file: {self.config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"❌ Config file not found: {self.config_path}")
            return {'sources': []}

    def _should_use_db(self) -> bool:
        flag = os.getenv('DATA_SOURCES_DB_ENABLED')
        if flag is None:
            return True
        return flag.lower() in {'1', 'true', 'yes'}

    def _load_config_from_db(self) -> Optional[dict]:
        db_host = os.getenv('DATA_SOURCES_DB_HOST', 'postgres')
        db_port = int(os.getenv('DATA_SOURCES_DB_PORT', '5432'))
        db_user = os.getenv('DATA_SOURCES_DB_USER', 'admin')
        db_password = os.getenv('DATA_SOURCES_DB_PASSWORD', 'admin123')
        db_name = os.getenv('DATA_SOURCES_DB_NAME', 'nexus_data')

        try:
            with psycopg2.connect(
                host=db_host,
                port=db_port,
                user=db_user,
                password=db_password,
                dbname=db_name,
            ) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        "SELECT source_id, source_name, source_type, enabled, config FROM data_sources"
                    )
                    rows = cursor.fetchall()

            sources = []
            for row in rows:
                source = dict(row.get('config') or {})
                source.setdefault('source_id', row.get('source_id'))
                source.setdefault('source_name', row.get('source_name'))
                source.setdefault('source_type', row.get('source_type'))
                source.setdefault('enabled', row.get('enabled'))
                sources.append(source)

            if not sources:
                return None

            return {
                'global': self._load_global_config(),
                'sources': sources,
            }
        except Exception as exc:
            logger.warning(f"Could not load sources from DB: {exc}")
            return None

    def _load_global_config(self) -> dict:
        config = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f) or {}
            except Exception as exc:
                logger.warning(f"Could not load global config from YAML: {exc}")

        global_config = config.get('global')
        if global_config:
            return global_config

        return {
            'data_lake_bucket': os.getenv('DATA_LAKE_BUCKET', 'data-lake'),
            'warehouse_bucket': os.getenv('WAREHOUSE_BUCKET', 'iceberg-warehouse'),
            'kafka_bootstrap_servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'),
            'default_partition_by': os.getenv('DEFAULT_PARTITION_BY', 'ingestion_date'),
        }
    
    def get_sources(self, enabled_only: bool = True) -> List[Dict]:
        """
        Get list of data sources
        
        Args:
            enabled_only: Only return enabled sources
            
        Returns:
            List of source configurations
        """
        sources = self.config.get('sources', [])
        
        if enabled_only:
            sources = [s for s in sources if s.get('enabled', True)]
        
        # Filter by environment variable if set
        enabled_sources = os.getenv('ENABLED_SOURCES', '')
        if enabled_sources:
            enabled_ids = set(enabled_sources.split(','))
            sources = [s for s in sources if s['source_id'] in enabled_ids]
        
        return sources
    
    def get_source(self, source_id: str) -> Optional[Dict]:
        """Get specific source configuration by ID"""
        sources = self.get_sources(enabled_only=False)
        for source in sources:
            if source['source_id'] == source_id:
                return source
        return None


class KafkaPublisher:
    """Publish events to Kafka topics based on config"""
    
    def __init__(self, bootstrap_servers: Optional[str] = None):
        """
        Initialize Kafka publisher
        
        Args:
            bootstrap_servers: Kafka servers (comma-separated)
        """
        self.bootstrap_servers = (
            bootstrap_servers or 
            os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
        ).split(',')
        
        self.producer = None
        self._connect()
    
    def _connect(self):
        """Connect to Kafka"""
        if KafkaProducer is None:
            logger.warning("⚠️  Kafka client not installed in this environment")
            self.producer = None
            return
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3,
            )
            logger.info(f"✅ Kafka producer connected to {self.bootstrap_servers}")
        except Exception as e:
            logger.warning(f"⚠️  Could not connect to Kafka: {e}")
            self.producer = None
    
    def publish(self, topic: str, message: Dict) -> bool:
        """
        Publish message to Kafka topic
        
        Args:
            topic: Topic name
            message: Message to publish
            
        Returns:
            True if published successfully
        """
        if not self.producer:
            logger.warning("Kafka producer not available")
            return False
        
        try:
            future = self.producer.send(topic, value=message)
            metadata = future.get(timeout=5)
            logger.info(
                f"Published to {topic}: "
                f"partition={metadata.partition}, offset={metadata.offset}"
            )
            return True
        except KafkaError as e:
            logger.error(f"Error publishing to Kafka: {e}")
            return False
    
    def close(self):
        """Close Kafka producer"""
        if self.producer:
            self.producer.close()


class ExtractorFactory:
    """Factory for creating source-specific extractors"""
    
    @staticmethod
    def get_extractor(source_config: Dict):
        """
        Get appropriate extractor based on source type
        
        Args:
            source_config: Source configuration dict
            
        Returns:
            Extractor instance
        """
        source_type = source_config.get('source_type', 'api')
        
        if source_type == 'api':
            return APIExtractor(source_config)
        elif source_type == 'jdbc':
            return JDBCExtractor(source_config)
        elif source_type == 's3':
            return S3Extractor(source_config)
        else:
            raise ValueError(f"Unknown source type: {source_type}")


class APIExtractor:
    """Extract data from REST API"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.location = config.get('location')
        self.method = config.get('method', 'GET')
        self.batch_size = config.get('batch_size', 1000)
        self.auth_type = config.get('auth_type', 'none')
    
    def extract(self) -> List[Dict]:
        """
        Extract data from API
        
        Returns:
            List of records
        """
        logger.info(f"Extracting data from {self.location}")
        
        try:
            headers = self._build_headers()
            params = {'limit': self.batch_size}
            
            response = requests.request(
                method=self.method,
                url=self.location,
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Handle paginated responses
            if isinstance(data, dict) and 'data' in data:
                records = data['data']
            elif isinstance(data, list):
                records = data
            else:
                records = [data]
            
            logger.info(f"✅ Extracted {len(records)} records from {self.location}")
            return records
            
        except Exception as e:
            logger.error(f"❌ Failed to extract from {self.location}: {e}")
            raise
    
    def _build_headers(self) -> Dict:
        """Build request headers based on auth type"""
        headers = {'Content-Type': 'application/json'}
        
        if self.auth_type == 'bearer':
            token = os.getenv('API_BEARER_TOKEN', '')
            headers['Authorization'] = f'Bearer {token}'
        elif self.auth_type == 'api_key':
            api_key = os.getenv('API_KEY', '')
            key_header = self.config.get('api_key_header', 'X-API-Key')
            headers[key_header] = api_key
        elif self.auth_type == 'basic':
            username = os.getenv('API_USERNAME', '')
            password = os.getenv('API_PASSWORD', '')
            import base64
            credentials = base64.b64encode(f'{username}:{password}'.encode()).decode()
            headers['Authorization'] = f'Basic {credentials}'
        
        return headers


class JDBCExtractor:
    """Extract data from JDBC source (PostgreSQL, MySQL, etc.)"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.jdbc_url = config.get('jdbc_url')
        self.source_table = config.get('source_table')
        self.query = config.get('query')
    
    def extract(self) -> List[Dict]:
        """
        Extract data from JDBC source in Spark
        This would be used in a Spark job
        
        Returns:
            Spark DataFrame (when used in Spark context)
        """
        logger.info(f"Extracting from JDBC: {self.jdbc_url}")
        
        # This would be implemented in Spark job
        raise NotImplementedError(
            "JDBC extraction should be done in Spark job "
            "using spark.read.jdbc()"
        )


class S3Extractor:
    """Extract data from S3/MinIO"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.location = config.get('location')
        self.format = config.get('format', 'parquet')
    
    def extract(self) -> List[Dict]:
        """Extract data from S3 in Spark job"""
        logger.info(f"Extracting from S3: {self.location}")
        raise NotImplementedError("S3 extraction should be done in Spark job")


class SchemaValidator:
    """Validate data against schema"""
    
    def __init__(self, schema_path: str):
        """
        Initialize validator
        
        Args:
            schema_path: Path to schema.json file
        """
        self.schema = self._load_schema(schema_path)
        self.required_fields = set(self.schema.get('required', []))
    
    def _load_schema(self, schema_path: str) -> Dict:
        """Load schema from JSON file"""
        try:
            with open(schema_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load schema {schema_path}: {e}")
            return {}
    
    def validate(self, records: List[Dict]) -> tuple[List[Dict], List[str]]:
        """
        Validate records against schema
        
        Args:
            records: List of records to validate
            
        Returns:
            Tuple of (valid_records, error_messages)
        """
        valid_records = []
        errors = []
        
        for idx, record in enumerate(records):
            # Check required fields
            missing = self.required_fields - set(record.keys())
            if missing:
                errors.append(
                    f"Record {idx}: Missing required fields: {missing}"
                )
                continue
            
            # Additional validation could go here
            valid_records.append(record)
        
        logger.info(
            f"✅ Validated {len(valid_records)}/{len(records)} records"
        )
        
        if errors:
            logger.warning(f"⚠️ Validation errors: {len(errors)}")
        
        return valid_records, errors


class PipelineOrchestrator:
    """Coordinate full extraction pipeline"""
    
    def __init__(self, config_path: str = "configs/sources.yaml"):
        """
        Initialize pipeline
        
        Args:
            config_path: Path to sources.yaml
        """
        self.config_loader = ConfigLoader(config_path)
        self.kafka_publisher = KafkaPublisher()
    
    def process_source(self, source_config: Dict) -> Dict:
        """
        Process a single source from config to Kafka
        
        Args:
            source_config: Source configuration dict
            
        Returns:
            Processing result dict
        """
        source_id = source_config['source_id']
        source_name = source_config['source_name']
        
        logger.info(f"\n{'='*50}")
        logger.info(f"Processing: {source_name}")
        logger.info(f"{'='*50}")
        
        result = {
            'source_id': source_id,
            'source_name': source_name,
            'status': 'success',
            'record_count': 0,
            'errors': []
        }
        
        try:
            # Step 1: Extract
            extractor = ExtractorFactory.get_extractor(source_config)
            records = extractor.extract()
            result['record_count'] = len(records)
            
            # Step 2: Validate
            schema_file = source_config.get('schema_file')
            if schema_file:
                validator = SchemaValidator(schema_file)
                records, validation_errors = validator.validate(records)
                result['errors'].extend(validation_errors)
            
            # Step 3: Publish to Kafka
            topic = source_config['kafka_topic']
            if records:
                # Wrap records with metadata
                for record in records:
                    message = {
                        'source_id': source_id,
                        'source_name': source_name,
                        'ingestion_timestamp': datetime.now().isoformat(),
                        'data': record
                    }
                    self.kafka_publisher.publish(topic, message)
                
                logger.info(f"✅ Published {len(records)} records to {topic}")
            
            logger.info(f"✅ Completed: {source_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to process {source_name}: {e}")
            result['status'] = 'failed'
            result['error'] = str(e)
        
        return result
    
    def process_all_sources(self) -> List[Dict]:
        """
        Process all enabled sources
        
        Returns:
            List of processing results
        """
        sources = self.config_loader.get_sources(enabled_only=True)
        results = []
        
        for source in sources:
            result = self.process_source(source)
            results.append(result)
        
        # Summary
        successful = sum(1 for r in results if r['status'] == 'success')
        logger.info(f"\n{'='*50}")
        logger.info(f"Summary: {successful}/{len(results)} sources processed successfully")
        logger.info(f"{'='*50}\n")
        
        return results
    
    def close(self):
        """Cleanup resources"""
        if self.kafka_publisher:
            self.kafka_publisher.close()
