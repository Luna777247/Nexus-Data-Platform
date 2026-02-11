"""
Nexus Data Platform - Tourism Events Ingestion DAG
Machine-readable: Extract → Validate → Store → Process
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import json
import os
import requests
import logging

logger = logging.getLogger(__name__)

SCHEMA_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "packages", "shared", "schemas", "event.schema.json")
)

def _load_event_schema():
    try:
        with open(SCHEMA_PATH, "r") as schema_file:
            return json.load(schema_file)
    except Exception as exc:
        logger.warning(f"⚠️  Could not load shared schema: {exc}")
        return {
            "properties": {
                "id": {"type": "string"},
                "user_id": {"type": "integer"},
                "amount": {"type": "number"},
                "region": {"type": "string"},
                "event_type": {"type": "string"},
                "source": {"type": "string"},
            },
            "required": ["id", "user_id", "amount", "region", "event_type", "source"],
        }

EVENT_SCHEMA = _load_event_schema()

# Default arguments
default_args = {
    'owner': 'nexus-data-team',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
}

# DAG definition
dag = DAG(
    'tourism_events_pipeline',
    default_args=default_args,
    description='Daily tourism events ingestion from APIs',
    schedule_interval='@daily',  # Run daily at 00:00 UTC
    start_date=days_ago(1),
    catchup=False,
    tags=['ingestion', 'tourism', 'events'],
)

# ============================================
# TASK 1: Extract data from multiple APIs
# ============================================
def extract_tourism_data():
    """Extract tourism events from external APIs"""
    logger.info("Starting data extraction from tourism APIs...")
    
    # Example API endpoints
    apis = {
        'tours': 'https://api.tourism.io/v1/tours?limit=1000',
        'bookings': 'https://api.tourism.io/v1/bookings?date=' + datetime.now().strftime('%Y-%m-%d'),
        'reviews': 'https://api.tourism.io/v1/reviews?recent=true&limit=500',
    }
    
    all_data = {}
    for source, url in apis.items():
        try:
            logger.info(f"Fetching {source} from {url}")
            # Mock response - in production, use real API
            response = {
                'source': source,
                'timestamp': datetime.now().isoformat(),
                'records': [
                    {
                        'id': f'{source}_{i}',
                        'user_id': 100 + i,
                        'amount': 99.99 + i,
                        'region': ['VN', 'SG', 'TH', 'ID'][i % 4],
                        'event_type': 'booking' if source == 'bookings' else 'view',
                        'source': source,
                    }
                    for i in range(5)
                ]
            }
            all_data[source] = response
            logger.info(f"✅ Extracted {len(response['records'])} records from {source}")
        except Exception as e:
            logger.error(f"❌ Error fetching {source}: {str(e)}")
            raise
    
    # Save to file for next task
    with open('/tmp/raw_tourism_data.json', 'w') as f:
        json.dump(all_data, f, indent=2)
    
    logger.info(f"✅ Extraction complete. Total sources: {len(all_data)}")
    return len(all_data)

# ============================================
# TASK 2: Validate data quality
# ============================================
def validate_data_quality():
    """Perform data quality checks"""
    logger.info("Starting data validation...")
    
    with open('/tmp/raw_tourism_data.json', 'r') as f:
        data = json.load(f)
    
    # Quality checks
    validation_results = {
        'total_sources': len(data),
        'total_records': 0,
        'quality_score': 0,
        'issues': []
    }
    
    for source, source_data in data.items():
        records = source_data.get('records', [])
        validation_results['total_records'] += len(records)
        
        # Check for missing fields
        for idx, record in enumerate(records):
            required_fields = EVENT_SCHEMA.get('required', [])
            missing = [f for f in required_fields if f not in record]
            if missing:
                validation_results['issues'].append(
                    f"Record {idx} in {source} missing fields: {missing}"
                )
    
    # Calculate quality score
    if validation_results['total_records'] > 0:
        validation_results['quality_score'] = 100 - (
            (len(validation_results['issues']) / validation_results['total_records']) * 100
        )
    
    logger.info(f"✅ Validation complete. Quality Score: {validation_results['quality_score']:.1f}%")
    logger.info(f"   Total records: {validation_results['total_records']}")
    
    if validation_results['issues']:
        logger.warning(f"   Issues found: {len(validation_results['issues'])}")
    
    # Save validation results
    with open('/tmp/validation_report.json', 'w') as f:
        json.dump(validation_results, f, indent=2)
    
    if validation_results['quality_score'] < 80:
        raise ValueError(f"Data quality too low: {validation_results['quality_score']:.1f}%")
    
    return validation_results

# ============================================
# TASK 3: Upload to MinIO (Data Lake)
# ============================================
def upload_to_minio():
    """Upload validated data to MinIO"""
    logger.info("Uploading data to MinIO...")
    
    # In production, use boto3/minio client
    # For now, simulate upload
    import os
    
    data_file = '/tmp/raw_tourism_data.json'
    if os.path.exists(data_file):
        file_size = os.path.getsize(data_file)
        
        # Simulate upload to s3://data-lake/raw/tourism/
        # bucket_name = 'data-lake'
        # object_name = f'raw/tourism/{datetime.now().strftime("%Y/%m/%d")}/events.json'
        
        logger.info(f"✅ File uploaded successfully")
        logger.info(f"   Size: {file_size} bytes")
        logger.info(f"   Path: s3://data-lake/raw/tourism/{datetime.now().strftime('%Y/%m/%d')}/events.json")
        
        return {'status': 'success', 'size': file_size}
    else:
        raise FileNotFoundError(f"Data file not found: {data_file}")

# ============================================
# TASK 4: Trigger Spark Processing
# ============================================
def trigger_spark_processing():
    """Trigger Spark job for data processing"""
    logger.info("Triggering Spark processing job...")
    
    # In production, use spark-submit or Spark REST API
    # spark-submit \
    #   --master spark://spark-master:7077 \
    #   --executor-memory 4g \
    #   /path/to/spark_job.py
    
    logger.info("✅ Spark job triggered")
    logger.info("   Expected duration: 5-10 minutes")
    logger.info("   Output: s3://data-lake/processed/tourism/")
    
    return {'job_id': 'spark_job_12345', 'status': 'submitted'}

# ============================================
# TASK 5: Create data catalog entry
# ============================================
def update_data_catalog():
    """Update data catalog with new dataset"""
    logger.info("Updating data catalog...")
    
    schema_properties = EVENT_SCHEMA.get('properties', {})
    catalog_entry = {
        'dataset_id': f'tourism_events_{datetime.now().strftime("%Y%m%d")}',
        'source': 'tourism_api',
        'ingestion_date': datetime.now().isoformat(),
        'location': f's3://data-lake/raw/tourism/{datetime.now().strftime("%Y/%m/%d")}/events.json',
        'record_count': 15,  # Would get from validation
        'quality_score': 95.0,
        'schema': {
            key: value.get('type', 'string') for key, value in schema_properties.items()
        }
    }
    
    logger.info(f"✅ Catalog updated: {catalog_entry['dataset_id']}")
    
    return catalog_entry

# ============================================
# Define Tasks
# ============================================

# Task 1: Extract
task_extract = PythonOperator(
    task_id='extract_tourism_data',
    python_callable=extract_tourism_data,
    dag=dag,
)

# Task 2: Validate
task_validate = PythonOperator(
    task_id='validate_data_quality',
    python_callable=validate_data_quality,
    dag=dag,
)

# Task 3: Upload
task_upload = PythonOperator(
    task_id='upload_to_minio',
    python_callable=upload_to_minio,
    dag=dag,
)

# Task 4: Process
task_process = PythonOperator(
    task_id='trigger_spark_processing',
    python_callable=trigger_spark_processing,
    dag=dag,
)

# Task 5: Catalog
task_catalog = PythonOperator(
    task_id='update_data_catalog',
    python_callable=update_data_catalog,
    dag=dag,
)

# Task 6: Notification
task_notify = BashOperator(
    task_id='send_notification',
    bash_command='echo "✅ Tourism events ingestion pipeline completed at $(date)"',
    dag=dag,
)

# ============================================
# Define Task Dependencies
# ============================================

task_extract >> task_validate >> task_upload >> task_process >> task_catalog >> task_notify
