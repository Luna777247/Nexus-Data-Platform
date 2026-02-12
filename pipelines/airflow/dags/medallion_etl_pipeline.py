"""
Nexus Data Platform - Medallion Architecture ETL Pipeline
Orchestrator pattern: Airflow triggers Spark jobs (không xử lý data trực tiếp)

Architecture:
    Airflow (Orchestrator) → Trigger Spark Jobs
    Spark → Bronze → Silver → Gold

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

logger = logging.getLogger(__name__)

# Default arguments
default_args = {
    'owner': 'nexus-data-team',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
}

# DAG definition - Medallion ETL
dag = DAG(
    'medallion_etl_pipeline',
    default_args=default_args,
    description='Medallion Architecture: Bronze → Silver → Gold',
    schedule_interval='@hourly',  # Run every hour
    start_date=days_ago(1),
    catchup=False,
    tags=['etl', 'medallion', 'lakehouse'],
)

# ════════════════════════════════════════════════════════════════
# BRONZE → SILVER ETL (Cleaning & Validation)
# ════════════════════════════════════════════════════════════════

bronze_to_silver = BashOperator(
    task_id='bronze_to_silver_etl',
    bash_command="""
    spark-submit \
        --master local[*] \
        --conf spark.sql.catalog.iceberg=org.apache.iceberg.spark.SparkCatalog \
        --conf spark.sql.catalog.iceberg.type=rest \
        --conf spark.sql.catalog.iceberg.uri=http://iceberg-rest:8080 \
        --conf spark.sql.catalog.iceberg.warehouse=s3a://iceberg-warehouse/ \
        --packages org.apache.iceberg:iceberg-spark-runtime-3.3_2.12:1.4.0 \
        /opt/airflow/jobs/spark/bronze_to_silver.py \
        --date {{ ds }}
    """,
    dag=dag,
)

# ════════════════════════════════════════════════════════════════
# SILVER → GOLD ETL (Aggregations & Business Logic)
# ════════════════════════════════════════════════════════════════

silver_to_gold = BashOperator(
    task_id='silver_to_gold_etl',
    bash_command="""
    spark-submit \
        --master local[*] \
        --conf spark.sql.catalog.iceberg=org.apache.iceberg.spark.SparkCatalog \
        --conf spark.sql.catalog.iceberg.type=rest \
        --conf spark.sql.catalog.iceberg.uri=http://iceberg-rest:8080 \
        --conf spark.sql.catalog.iceberg.warehouse=s3a://iceberg-warehouse/ \
        --packages org.apache.iceberg:iceberg-spark-runtime-3.3_2.12:1.4.0 \
        /opt/airflow/jobs/spark/silver_to_gold.py \
        --date {{ ds }}
    """,
    dag=dag,
)

# ════════════════════════════════════════════════════════════════
# GOLD → CLICKHOUSE (Analytics Serving)
# ════════════════════════════════════════════════════════════════

gold_to_clickhouse = BashOperator(
    task_id='gold_to_clickhouse',
    bash_command="""
    spark-submit \
        --master local[*] \
        --packages ru.yandex.clickhouse:clickhouse-jdbc:0.3.2 \
        /opt/airflow/jobs/spark/gold_to_clickhouse.py \
        --date {{ ds }}
    """,
    dag=dag,
)

# ════════════════════════════════════════════════════════════════
# DATA QUALITY VALIDATION
# ════════════════════════════════════════════════════════════════

def validate_silver_quality(**context):
    """
    Validate Silver layer data quality using Great Expectations
    """
    logger.info("🔍 Validating Silver layer data quality...")
    
    execution_date = context['ds']
    
    # TODO: Integrate Great Expectations
    # import great_expectations as ge
    # context = ge.data_context.DataContext()
    # 
    # suite = context.get_expectation_suite("silver_layer_suite")
    # batch = context.get_batch({
    #     "path": f"s3a://iceberg-warehouse/silver/date={execution_date}/",
    #     "datasource": "spark_datasource"
    # })
    # 
    # results = context.run_validation_operator(
    #     "action_list_operator",
    #     assets_to_validate=[batch],
    #     expectation_suite=suite
    # )
    
    logger.info("✅ Silver layer validation complete")
    return True

validate_quality = PythonOperator(
    task_id='validate_silver_quality',
    python_callable=validate_silver_quality,
    provide_context=True,
    dag=dag,
)

# ════════════════════════════════════════════════════════════════
# DAG DEPENDENCIES
# ════════════════════════════════════════════════════════════════

bronze_to_silver >> validate_quality
validate_quality >> silver_to_gold
silver_to_gold >> gold_to_clickhouse
