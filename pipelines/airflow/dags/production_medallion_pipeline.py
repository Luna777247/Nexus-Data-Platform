"""
Nexus Data Platform - Production Medallion ETL Pipeline
Implements improved architecture with:
- Separated Spark clusters (streaming vs batch)
- Governance integration (Quality, Lineage)
- Monitoring & Observability
- DLQ handling
- Iceberg catalog

Architecture:
    Airflow (Orchestrator) → Spark Batch Cluster → Bronze → Silver → Gold
    (Spark Streaming Cluster runs separately for real-time ingestion)

Layers:
    🥉 Bronze: Raw data from Kafka/CDC/APIs
    🥈 Silver: Cleaned & validated data
    🥇 Gold: Business aggregations & analytics
"""

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import logging
import os
import sys

# Add utils to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))

from lineage_tracker import LineageTracker
from metrics_emitter import MetricsEmitter

logger = logging.getLogger(__name__)

# Default arguments
default_args = {
    'owner': 'nexus-data-team',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': True,
    'email': ['data-team@nexus.com'],
}

# DAG definition - Production Medallion ETL
dag = DAG(
    'production_medallion_etl',
    default_args=default_args,
    description='[PRODUCTION] Medallion Architecture: Bronze → Silver → Gold',
    schedule_interval='@hourly',
    start_date=days_ago(1),
    catchup=False,
    tags=['etl', 'medallion', 'lakehouse', 'production'],
    max_active_runs=1,
)


# ════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════

def track_job_start(**context):
    """Track job start in lineage system"""
    try:
        lineage = LineageTracker()
        lineage.track_job_start(
            job_name=context['task'].task_id,
            job_type='etl',
            parameters={
                'execution_date': str(context['ds']),
                'dag_run_id': context['dag_run'].run_id
            }
        )
        logger.info(f"✅ Tracked job start: {context['task'].task_id}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to track lineage: {e}")


def emit_job_metrics(**context):
    """Emit job completion metrics to Prometheus"""
    try:
        task_instance = context['task_instance']
        duration = (
            task_instance.end_date - task_instance.start_date
        ).total_seconds()
        
        metrics = MetricsEmitter(job_name=task_instance.task_id)
        metrics.emit_histogram(
            "airflow_task_duration_seconds",
            duration,
            labels={
                "dag_id": context['dag'].dag_id,
                "task_id": task_instance.task_id,
                "status": "success" if task_instance.state == "success" else "failed"
            }
        )
        metrics.push_metrics()
        logger.info(f"✅ Emitted metrics for: {task_instance.task_id}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to emit metrics: {e}")


# ════════════════════════════════════════════════════════════════
# TASK 1: BRONZE → SILVER ETL (Cleaning & Validation)
# ════════════════════════════════════════════════════════════════

track_bronze_to_silver_start = PythonOperator(
    task_id='track_bronze_to_silver_start',
    python_callable=track_job_start,
    dag=dag,
)

bronze_to_silver = BashOperator(
    task_id='bronze_to_silver_etl',
    bash_command="""
    spark-submit \
        --master spark://spark-batch-master:7077 \
        --deploy-mode client \
        --conf spark.sql.catalog.iceberg=org.apache.iceberg.spark.SparkCatalog \
        --conf spark.sql.catalog.iceberg.type=rest \
        --conf spark.sql.catalog.iceberg.uri=http://iceberg-rest:8080 \
        --conf spark.sql.catalog.iceberg.warehouse=s3a://iceberg-warehouse/ \
        --conf spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions \
        --conf spark.hadoop.fs.s3a.endpoint=http://minio-1:9000 \
        --conf spark.hadoop.fs.s3a.access.key=minioadmin \
        --conf spark.hadoop.fs.s3a.secret.key=minioadmin123 \
        --conf spark.hadoop.fs.s3a.path.style.access=true \
        --conf spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem \
        --packages org.apache.iceberg:iceberg-spark-runtime-3.3_2.12:1.4.0,org.apache.hadoop:hadoop-aws:3.3.4 \
        /opt/airflow/jobs/spark/bronze_to_silver_enhanced.py \
        --date {{ ds }} \
        --enable-quality-checks \
        --enable-lineage-tracking \
        --enable-dlq
    """,
    dag=dag,
)

emit_bronze_to_silver_metrics = PythonOperator(
    task_id='emit_bronze_to_silver_metrics',
    python_callable=emit_job_metrics,
    dag=dag,
)


# ════════════════════════════════════════════════════════════════
# TASK 2: SILVER → GOLD ETL (Aggregations & Business Logic)
# ════════════════════════════════════════════════════════════════

track_silver_to_gold_start = PythonOperator(
    task_id='track_silver_to_gold_start',
    python_callable=track_job_start,
    dag=dag,
)

silver_to_gold = BashOperator(
    task_id='silver_to_gold_etl',
    bash_command="""
    spark-submit \
        --master spark://spark-batch-master:7077 \
        --deploy-mode client \
        --conf spark.sql.catalog.iceberg=org.apache.iceberg.spark.SparkCatalog \
        --conf spark.sql.catalog.iceberg.type=rest \
        --conf spark.sql.catalog.iceberg.uri=http://iceberg-rest:8080 \
        --conf spark.sql.catalog.iceberg.warehouse=s3a://iceberg-warehouse/ \
        --conf spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions \
        --conf spark.hadoop.fs.s3a.endpoint=http://minio-1:9000 \
        --conf spark.hadoop.fs.s3a.access.key=minioadmin \
        --conf spark.hadoop.fs.s3a.secret.key=minioadmin123 \
        --conf spark.hadoop.fs.s3a.path.style.access=true \
        --conf spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem \
        --packages org.apache.iceberg:iceberg-spark-runtime-3.3_2.12:1.4.0,org.apache.hadoop:hadoop-aws:3.3.4 \
        /opt/airflow/jobs/spark/silver_to_gold_enhanced.py \
        --date {{ ds }} \
        --enable-quality-checks \
        --enable-lineage-tracking
    """,
    dag=dag,
)

emit_silver_to_gold_metrics = PythonOperator(
    task_id='emit_silver_to_gold_metrics',
    python_callable=emit_job_metrics,
    dag=dag,
)


# ════════════════════════════════════════════════════════════════
# TASK 3: GOLD → CLICKHOUSE (Analytics Serving)
# ════════════════════════════════════════════════════════════════

track_gold_to_clickhouse_start = PythonOperator(
    task_id='track_gold_to_clickhouse_start',
    python_callable=track_job_start,
    dag=dag,
)

gold_to_clickhouse = BashOperator(
    task_id='gold_to_clickhouse_load',
    bash_command="""
    spark-submit \
        --master spark://spark-batch-master:7077 \
        --deploy-mode client \
        --conf spark.sql.catalog.iceberg=org.apache.iceberg.spark.SparkCatalog \
        --conf spark.sql.catalog.iceberg.type=rest \
        --conf spark.sql.catalog.iceberg.uri=http://iceberg-rest:8080 \
        --packages org.apache.iceberg:iceberg-spark-runtime-3.3_2.12:1.4.0,ru.yandex.clickhouse:clickhouse-jdbc:0.4.6 \
        /opt/airflow/jobs/spark/gold_to_clickhouse.py \
        --date {{ ds }}
    """,
    dag=dag,
)

emit_gold_to_clickhouse_metrics = PythonOperator(
    task_id='emit_gold_to_clickhouse_metrics',
    python_callable=emit_job_metrics,
    dag=dag,
)


# ════════════════════════════════════════════════════════════════
# TASK DEPENDENCIES
# ════════════════════════════════════════════════════════════════

# Bronze → Silver flow
track_bronze_to_silver_start >> bronze_to_silver >> emit_bronze_to_silver_metrics

# Silver → Gold flow
emit_bronze_to_silver_metrics >> track_silver_to_gold_start >> silver_to_gold >> emit_silver_to_gold_metrics

# Gold → ClickHouse flow
emit_silver_to_gold_metrics >> track_gold_to_clickhouse_start >> gold_to_clickhouse >> emit_gold_to_clickhouse_metrics
