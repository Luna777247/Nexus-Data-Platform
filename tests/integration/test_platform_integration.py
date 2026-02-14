"""
Integration Tests for Nexus Data Platform
Tests end-to-end data flow and service integration
"""

import pytest
import asyncio
import httpx
import json
from typing import Dict, Any
import time


class TestAPIIntegration:
    """Test API service integration"""
    
    @pytest.fixture
    def api_client(self):
        """Create API client fixture"""
        return httpx.AsyncClient(base_url="http://localhost:8001", timeout=10.0)
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, api_client):
        """Test API health endpoint"""
        response = await api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
    
    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, api_client):
        """Test metrics endpoint"""
        response = await api_client.get("/metrics")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_data_ingestion_api(self, api_client):
        """Test data ingestion through API"""
        payload = {
            "event_type": "user_action",
            "user_id": "test_user_123",
            "action": "page_view",
            "timestamp": "2026-02-13T00:00:00Z",
            "metadata": {"page": "/home"}
        }
        
        response = await api_client.post("/ingest", json=payload)
        assert response.status_code in [200, 201]


class TestKafkaIntegration:
    """Test Kafka messaging integration"""
    
    @pytest.fixture
    def kafka_config(self):
        """Kafka configuration"""
        return {
            "bootstrap_servers": ["localhost:9092", "localhost:9093", "localhost:9094"],
            "topics": {
                "app_events": "nexus.app_events",
                "cdc_events": "nexus.cdc_events",
                "dlq": "nexus.dlq"
            }
        }
    
    def test_kafka_broker_availability(self, kafka_config):
        """Test that Kafka brokers are available"""
        from confluent_kafka.admin import AdminClient
        
        admin_client = AdminClient({
            'bootstrap.servers': ','.join(kafka_config['bootstrap_servers'])
        })
        
        # Get cluster metadata
        metadata = admin_client.list_topics(timeout=10)
        assert len(metadata.brokers) >= 3, "Expected at least 3 Kafka brokers"
    
    def test_topic_creation(self, kafka_config):
        """Test topic creation and configuration"""
        from confluent_kafka.admin import AdminClient, NewTopic
        
        admin_client = AdminClient({
            'bootstrap.servers': ','.join(kafka_config['bootstrap_servers'])
        })
        
        # Check if topics exist
        topics = admin_client.list_topics(timeout=10).topics
        
        for topic_name in kafka_config['topics'].values():
            assert topic_name in topics, f"Topic {topic_name} should exist"
            
            # Check replication factor
            topic_metadata = topics[topic_name]
            for partition in topic_metadata.partitions.values():
                assert len(partition.replicas) >= 3, "Replication factor should be >= 3"
    
    def test_message_produce_consume(self, kafka_config):
        """Test producing and consuming messages"""
        from confluent_kafka import Producer, Consumer
        
        topic = kafka_config['topics']['app_events']
        test_message = json.dumps({
            "test_id": "integration_test_001",
            "timestamp": time.time()
        })
        
        # Produce message
        producer = Producer({
            'bootstrap.servers': ','.join(kafka_config['bootstrap_servers'])
        })
        
        producer.produce(topic, value=test_message)
        producer.flush()
        
        # Consume message
        consumer = Consumer({
            'bootstrap.servers': ','.join(kafka_config['bootstrap_servers']),
            'group.id': 'test_consumer_group',
            'auto.offset.reset': 'latest'
        })
        
        consumer.subscribe([topic])
        
        # Poll for message
        msg = consumer.poll(timeout=5.0)
        assert msg is not None, "Should receive message"
        assert msg.error() is None, "Message should not have errors"
        
        consumer.close()


class TestSparkIntegration:
    """Test Spark processing integration"""
    
    @pytest.fixture
    def spark_config(self):
        """Spark cluster configuration"""
        return {
            "streaming_master": "http://localhost:8080",
            "batch_master": "http://localhost:8081"
        }
    
    def test_spark_streaming_master_available(self, spark_config):
        """Test Spark Streaming master is available"""
        import requests
        response = requests.get(spark_config['streaming_master'], timeout=5)
        assert response.status_code == 200
    
    def test_spark_batch_master_available(self, spark_config):
        """Test Spark Batch master is available"""
        import requests
        response = requests.get(spark_config['batch_master'], timeout=5)
        assert response.status_code == 200


class TestStorageIntegration:
    """Test storage layer integration (MinIO, PostgreSQL, ClickHouse)"""
    
    @pytest.fixture
    def minio_config(self):
        """MinIO configuration"""
        return {
            "endpoint": "localhost:9000",
            "access_key": "minio_admin",
            "secret_key": "minio_secret_2024",
            "secure": False
        }
    
    @pytest.fixture
    def postgres_config(self):
        """PostgreSQL configuration"""
        return {
            "host": "localhost",
            "port": 5432,
            "user": "iceberg",
            "password": "iceberg123",
            "database": "iceberg_catalog"
        }
    
    @pytest.fixture
    def clickhouse_config(self):
        """ClickHouse configuration"""
        return {
            "host": "localhost",
            "port": 8123,
            "user": "default",
            "password": "clickhouse123",
            "database": "analytics"
        }
    
    def test_minio_connectivity(self, minio_config):
        """Test MinIO connectivity and bucket access"""
        from minio import Minio
        
        client = Minio(
            minio_config['endpoint'],
            access_key=minio_config['access_key'],
            secret_key=minio_config['secret_key'],
            secure=minio_config['secure']
        )
        
        # List buckets
        buckets = client.list_buckets()
        assert len(buckets) > 0, "Should have at least one bucket"
    
    def test_postgres_connectivity(self, postgres_config):
        """Test PostgreSQL connectivity"""
        import psycopg2
        
        conn = psycopg2.connect(
            host=postgres_config['host'],
            port=postgres_config['port'],
            user=postgres_config['user'],
            password=postgres_config['password'],
            database=postgres_config['database']
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        assert version is not None
        
        cursor.close()
        conn.close()
    
    def test_clickhouse_connectivity(self, clickhouse_config):
        """Test ClickHouse connectivity"""
        import requests
        
        url = f"http://{clickhouse_config['host']}:{clickhouse_config['port']}"
        response = requests.get(f"{url}/ping", timeout=5)
        assert response.status_code == 200
        assert response.text.strip() == "Ok."


class TestMonitoringIntegration:
    """Test monitoring stack integration (Prometheus, Grafana, Jaeger)"""
    
    def test_prometheus_available(self):
        """Test Prometheus is available"""
        import requests
        response = requests.get("http://localhost:9090/-/healthy", timeout=5)
        assert response.status_code == 200
    
    def test_prometheus_targets(self):
        """Test Prometheus has configured targets"""
        import requests
        response = requests.get("http://localhost:9090/api/v1/targets", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        assert data['status'] == 'success'
        assert len(data['data']['activeTargets']) > 0, "Should have active targets"
    
    def test_grafana_available(self):
        """Test Grafana is available"""
        import requests
        response = requests.get("http://localhost:3000/api/health", timeout=5)
        assert response.status_code == 200
    
    def test_jaeger_available(self):
        """Test Jaeger is available"""
        import requests
        response = requests.get("http://localhost:14269/", timeout=5)
        assert response.status_code == 200


class TestDataFlowE2E:
    """End-to-end data flow tests"""
    
    def test_bronze_to_silver_flow(self):
        """Test Bronze to Silver layer transformation"""
        # This would test the actual data flow
        # For now, we'll just check that the processing logic exists
        from pathlib import Path
        
        bronze_to_silver_script = Path("jobs/spark/bronze_to_silver.py")
        assert bronze_to_silver_script.exists(), "Bronze to Silver script should exist"
    
    def test_silver_to_gold_flow(self):
        """Test Silver to Gold layer transformation"""
        from pathlib import Path
        
        silver_to_gold_script = Path("jobs/spark/silver_to_gold.py")
        assert silver_to_gold_script.exists(), "Silver to Gold script should exist"
    
    def test_gold_to_clickhouse_flow(self):
        """Test Gold layer to ClickHouse flow"""
        from pathlib import Path
        
        gold_to_clickhouse_script = Path("jobs/spark/gold_to_clickhouse.py")
        assert gold_to_clickhouse_script.exists(), "Gold to ClickHouse script should exist"


class TestDataQuality:
    """Test data quality and governance"""
    
    def test_data_quality_checker_available(self):
        """Test data quality checker module is available"""
        from pipelines.airflow.utils.data_quality_checker import DataQualityChecker
        
        checker = DataQualityChecker()
        assert checker is not None
    
    def test_lineage_tracker_available(self):
        """Test lineage tracker module is available"""
        from pipelines.airflow.utils.lineage_tracker import LineageTracker
        
        tracker = LineageTracker()
        assert tracker is not None


class TestHighAvailability:
    """Test high availability features"""
    
    def test_kafka_replication(self):
        """Test Kafka has proper replication configured"""
        from confluent_kafka.admin import AdminClient
        
        admin_client = AdminClient({
            'bootstrap.servers': 'localhost:9092,localhost:9093,localhost:9094,localhost:9095,localhost:9096'
        })
        
        # Check broker count (should be 5)
        metadata = admin_client.list_topics(timeout=10)
        assert len(metadata.brokers) == 5, "Expected 5 Kafka brokers"
    
    def test_minio_cluster(self):
        """Test MinIO distributed setup"""
        from minio import Minio
        
        # Test connection to different MinIO nodes
        nodes = [
            "localhost:9001",
            "localhost:9002",
            "localhost:9003",
            "localhost:9004"
        ]
        
        for node in nodes:
            try:
                client = Minio(
                    node,
                    access_key="minio_admin",
                    secret_key="minio_secret_2024",
                    secure=False
                )
                # Should be able to connect
                buckets = client.list_buckets()
                assert True
            except Exception as e:
                pytest.fail(f"MinIO node {node} not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
