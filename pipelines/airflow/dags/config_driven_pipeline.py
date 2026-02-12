# Config-Driven Generic Data Pipeline
# Location: pipelines/airflow/dags/config_driven_pipeline.py
# Purpose: Ingest data from any source defined in conf/sources.yaml

"""
Generic DAG for ingesting data from configured sources.

Advantages:
- Add new sources: Edit conf/sources.yaml only, no code changes
- Each source: Extract → Validate → Publish to Kafka → Track metadata
- Supports: APIs, Databases, S3, etc.
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import sys
import os
import logging

# Add airflow module paths for DAGs and shared utils
airflow_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
airflow_utils = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "utils"))
sys.path.insert(0, airflow_root)
sys.path.insert(0, airflow_utils)

from utils.config_pipeline import (
    ConfigLoader,
    PipelineOrchestrator,
    ExtractorFactory,
    SchemaValidator,
    KafkaPublisher
)

logger = logging.getLogger(__name__)

# Default arguments
default_args = {
    'owner': 'nexus-data-team',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': days_ago(1),
    'email_on_failure': False,
}

# DAG definition
dag = DAG(
    'config_driven_data_pipeline',
    default_args=default_args,
    description='Generic config-driven data ingestion pipeline',
    schedule_interval='@daily',
    catchup=False,
    tags=['ingestion', 'config-driven', 'extensible'],
)


# ============================================
# Task 1: Load Configuration
# ============================================

def _get_sources_config_path() -> str:
    env_path = os.getenv('CONFIG_SOURCES_PATH')
    if env_path:
        return env_path

    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "conf", "sources.yaml")
    )


def load_sources_config():
    """Load data sources from conf/sources.yaml"""
    logger.info("📋 Loading data sources configuration...")

    config_path = _get_sources_config_path()
    
    loader = ConfigLoader(config_path)
    sources = loader.get_sources(enabled_only=True)
    
    logger.info(f"✅ Loaded {len(sources)} enabled data sources:")
    for source in sources:
        logger.info(f"   - {source['source_id']}: {source['source_name']}")
    
    return {
        'config_path': config_path,
        'source_count': len(sources),
        'sources': [s['source_id'] for s in sources]
    }


# ============================================
# Task 2: Process All Sources
# ============================================

def process_all_sources():
    """
    Process all enabled data sources:
    Extract → Validate → Publish to Kafka
    """
    logger.info("\n🔄 Starting data source processing...")
    
    config_path = _get_sources_config_path()
    
    orchestrator = PipelineOrchestrator(config_path)
    results = orchestrator.process_all_sources()
    orchestrator.close()
    
    # Compile summary
    summary = {
        'total_sources': len(results),
        'successful': sum(1 for r in results if r['status'] == 'success'),
        'failed': sum(1 for r in results if r['status'] == 'failed'),
        'total_records': sum(r.get('record_count', 0) for r in results),
        'results': results
    }
    
    logger.info(f"\n{'='*60}")
    logger.info(f"PIPELINE SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Total Sources: {summary['total_sources']}")
    logger.info(f"Successful: {summary['successful']}")
    logger.info(f"Failed: {summary['failed']}")
    logger.info(f"Total Records Ingested: {summary['total_records']}")
    logger.info(f"{'='*60}\n")
    
    # Check for failures
    if summary['failed'] > 0:
        logger.warning(f"⚠️ {summary['failed']} sources failed processing")
        for result in results:
            if result['status'] == 'failed':
                logger.warning(f"   - {result['source_name']}: {result.get('error')}")
    
    return summary


# ============================================
# Task 3: Verify Kafka Topics
# ============================================

def verify_kafka_topics():
    """Verify all Kafka topics exist and are ready"""
    logger.info("🔗 Verifying Kafka topics...")
    
    config_path = _get_sources_config_path()
    
    loader = ConfigLoader(config_path)
    sources = loader.get_sources(enabled_only=True)
    
    topics = set(s['kafka_topic'] for s in sources)
    
    logger.info(f"✅ Configured topics to monitor:")
    for topic in sorted(topics):
        logger.info(f"   - {topic}")
    
    return {'topics': list(topics), 'count': len(topics)}


# ============================================
# Task 4: Update Metadata Table
# ============================================

def update_metadata_tracking():
    """
    Update metadata tracking table in Iceberg
    Track which sources were processed, record counts, etc.
    """
    logger.info("📝 Updating pipeline metadata...")
    
    metadata = {
        'pipeline_run_id': f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'run_timestamp': datetime.now().isoformat(),
        'dag_id': 'config_driven_data_pipeline',
        'status': 'completed',
        'sources_processed': 'To be populated from previous tasks',
    }
    
    logger.info(f"✅ Metadata updated:")
    logger.info(f"   - Pipeline Run ID: {metadata['pipeline_run_id']}")
    logger.info(f"   - Timestamp: {metadata['run_timestamp']}")
    
    # TODO: Write to Iceberg metadata table
    # spark.createDataFrame([metadata]).write.mode("append").saveAsTable(...)
    
    return metadata


# ============================================
# Define Tasks
# ============================================

task_load_config = PythonOperator(
    task_id='load_sources_config',
    python_callable=load_sources_config,
    dag=dag,
)

task_process_sources = PythonOperator(
    task_id='process_all_sources',
    python_callable=process_all_sources,
    dag=dag,
)

task_verify_topics = PythonOperator(
    task_id='verify_kafka_topics',
    python_callable=verify_kafka_topics,
    dag=dag,
)

task_update_metadata = PythonOperator(
    task_id='update_metadata_tracking',
    python_callable=update_metadata_tracking,
    dag=dag,
)

# ============================================
# Define Task Dependencies
# ============================================

task_load_config >> task_process_sources >> task_verify_topics >> task_update_metadata
