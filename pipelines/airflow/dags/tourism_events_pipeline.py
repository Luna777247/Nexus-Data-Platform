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

    import os
    import boto3
    from botocore.config import Config

    data_file = '/tmp/raw_tourism_data.json'
    if not os.path.exists(data_file):
        raise FileNotFoundError(f"Data file not found: {data_file}")

    # Build NDJSON for Spark ingestion
    ndjson_file = '/tmp/raw_tourism_events.jsonl'
    with open(data_file, 'r') as source_handle:
        raw_data = json.load(source_handle)

    with open(ndjson_file, 'w') as output_handle:
        for source_data in raw_data.values():
            for record in source_data.get('records', []):
                output_handle.write(json.dumps(record) + "\n")

    endpoint = os.getenv('S3_ENDPOINT', 'http://minio:9000')
    bucket_name = os.getenv('S3_BUCKET', 'data-lake')
    region = os.getenv('S3_REGION', 'us-east-1')
    access_key = os.getenv('AWS_ACCESS_KEY_ID', 'minioadmin')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY', 'minioadmin123')

    s3_client = boto3.client(
        's3',
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
        config=Config(signature_version='s3v4', s3={'addressing_style': 'path'}),
    )

    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except Exception:
        logger.info(f"Bucket {bucket_name} not found. Creating...")
        s3_client.create_bucket(Bucket=bucket_name)

    object_name = f"raw/tourism/{datetime.now().strftime('%Y/%m/%d')}/events.ndjson"
    s3_client.upload_file(ndjson_file, bucket_name, object_name)
    file_size = os.path.getsize(ndjson_file)

    logger.info("✅ File uploaded successfully")
    logger.info(f"   Size: {file_size} bytes")
    logger.info(f"   Path: s3://{bucket_name}/{object_name}")

    return {'status': 'success', 'size': file_size, 'object': object_name}

# ============================================
# TASK 4: Trigger Spark Processing
# ============================================
def load_clickhouse_from_processed(**context):
    """Load ClickHouse from Spark processed output stored in MinIO"""
    logger.info("Loading processed events from MinIO into ClickHouse...")

    import boto3
    import json
    from botocore.config import Config
    import clickhouse_connect

    run_date = context.get('ds', datetime.utcnow().strftime('%Y-%m-%d'))
    year, month, day = run_date.split('-')
    prefix = f"processed/tourism/events/{year}/{month}/{day}/"

    endpoint = os.getenv('S3_ENDPOINT', 'http://minio:9000')
    bucket_name = os.getenv('S3_BUCKET', 'data-lake')
    region = os.getenv('S3_REGION', 'us-east-1')
    access_key = os.getenv('AWS_ACCESS_KEY_ID', 'minioadmin')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY', 'minioadmin123')

    s3_client = boto3.client(
        's3',
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
        config=Config(signature_version='s3v4', s3={'addressing_style': 'path'}),
    )

    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    objects = [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('.json')]

    if not objects:
        raise FileNotFoundError(f"No processed output found at s3://{bucket_name}/{prefix}")

    rows = []
    for key in objects:
        body = s3_client.get_object(Bucket=bucket_name, Key=key)['Body'].read().decode('utf-8')
        for line in body.splitlines():
            record = json.loads(line)
            rows.append(
                [
                    datetime.utcnow(),
                    int(record.get('user_id', 0)),
                    record.get('event_type', 'unknown'),
                    float(record.get('amount', 0.0)),
                    record.get('region', 'unknown'),
                    record.get('source', 'unknown'),
                ]
            )

    if not rows:
        logger.warning("No records found in processed output")
        return {'inserted_rows': 0, 'status': 'skipped'}

    clickhouse_client = clickhouse_connect.get_client(
        host=os.getenv('CLICKHOUSE_HOST', 'clickhouse'),
        port=int(os.getenv('CLICKHOUSE_PORT', '8123')),
        username=os.getenv('CLICKHOUSE_USER', 'admin'),
        password=os.getenv('CLICKHOUSE_PASSWORD', 'admin123'),
        database=os.getenv('CLICKHOUSE_DATABASE', 'analytics'),
    )

    clickhouse_client.insert(
        'analytics.events',
        rows,
        column_names=['timestamp', 'user_id', 'event_type', 'amount', 'region', 'source'],
    )

    logger.info("✅ ClickHouse loaded from processed output")
    logger.info(f"   Inserted rows: {len(rows)}")

    return {'inserted_rows': len(rows), 'status': 'completed'}

# ============================================
# TASK 5: Verify processed output
# ============================================
def verify_processed_output(**context):
    """Verify Spark output for record count and basic quality"""
    logger.info("Verifying processed output quality...")

    import boto3
    import json
    from botocore.config import Config

    run_date = context.get('ds', datetime.utcnow().strftime('%Y-%m-%d'))
    year, month, day = run_date.split('-')
    prefix = f"processed/tourism/events/{year}/{month}/{day}/"

    endpoint = os.getenv('S3_ENDPOINT', 'http://minio:9000')
    bucket_name = os.getenv('S3_BUCKET', 'data-lake')
    region = os.getenv('S3_REGION', 'us-east-1')
    access_key = os.getenv('AWS_ACCESS_KEY_ID', 'minioadmin')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY', 'minioadmin123')

    s3_client = boto3.client(
        's3',
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
        config=Config(signature_version='s3v4', s3={'addressing_style': 'path'}),
    )

    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    objects = [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('.json')]

    if not objects:
        raise FileNotFoundError(f"No processed output found at s3://{bucket_name}/{prefix}")

    required_fields = EVENT_SCHEMA.get('required', [])
    total_records = 0
    invalid_records = 0
    missing_field_counts = {field: 0 for field in required_fields}

    for key in objects:
        body = s3_client.get_object(Bucket=bucket_name, Key=key)['Body'].read().decode('utf-8')
        for line in body.splitlines():
            record = json.loads(line)
            total_records += 1
            missing = [field for field in required_fields if field not in record]
            if missing:
                invalid_records += 1
                for field in missing:
                    missing_field_counts[field] += 1

    quality_score = 0.0
    if total_records > 0:
        quality_score = 100.0 - ((invalid_records / total_records) * 100.0)

    logger.info("✅ Processed output verification complete")
    logger.info(f"   Records: {total_records}")
    logger.info(f"   Invalid: {invalid_records}")
    logger.info(f"   Quality Score: {quality_score:.2f}%")

    return {
        'records': total_records,
        'invalid_records': invalid_records,
        'quality_score': quality_score,
        'missing_field_counts': missing_field_counts,
        'prefix': prefix,
    }

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
        'location': f's3://data-lake/raw/tourism/{datetime.now().strftime("%Y/%m/%d")}/events.ndjson',
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

# Task 4: Spark processing (spark-submit)
task_process = BashOperator(
    task_id='spark_submit_processing',
    bash_command=(
        "spark-submit --master local[*] "
        "--packages org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 "
        "--conf spark.hadoop.fs.s3a.connection.timeout=60000 "
        "--conf spark.hadoop.fs.s3a.connection.establish.timeout=60000 "
        "--conf spark.hadoop.fs.s3a.connection.request.timeout=60000 "
        "--conf spark.hadoop.fs.s3a.socket.timeout=60000 "
        "--conf spark.hadoop.fs.s3a.threads.keepalivetime=60000 "
        "--conf spark.hadoop.fs.s3a.multipart.purge.age=86400000 "
        "--conf spark.hadoop.fs.s3a.multipart.purge.interval=3600000 "
        "--conf spark.hadoop.fs.s3a.aws.credentials.provider=org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider "
        "--conf spark.hadoop.fs.s3a.access.key=minioadmin "
        "--conf spark.hadoop.fs.s3a.secret.key=minioadmin123 "
        "--conf spark.hadoop.fs.s3a.endpoint=http://minio:9000 "
        "--conf spark.hadoop.fs.s3a.path.style.access=true "
        "/opt/airflow/jobs/tourism_processing.py "
        "--input s3a://data-lake/raw/tourism/{{ ds | replace('-', '/') }}/events.ndjson "
        "--output s3a://data-lake/processed/tourism/events/{{ ds | replace('-', '/') }}/"
    ),
    dag=dag,
)

# Task 5: Verify processed output
task_verify_output = PythonOperator(
    task_id='verify_processed_output',
    python_callable=verify_processed_output,
    dag=dag,
)

# Task 6: Load ClickHouse from Spark output
task_load_clickhouse = PythonOperator(
    task_id='load_clickhouse_from_processed',
    python_callable=load_clickhouse_from_processed,
    dag=dag,
)

# Task 7: Catalog
task_catalog = PythonOperator(
    task_id='update_data_catalog',
    python_callable=update_data_catalog,
    dag=dag,
)

# Task 8: Notification
task_notify = BashOperator(
    task_id='send_notification',
    bash_command='echo "✅ Tourism events ingestion pipeline completed at $(date)"',
    dag=dag,
)

# ============================================
# Define Task Dependencies
# ============================================

task_extract >> task_validate >> task_upload >> task_process >> task_verify_output >> task_load_clickhouse >> task_catalog >> task_notify
