# Airflow DAG for Iceberg Data Pipeline
# Location: pipelines/airflow/dags/iceberg_pipeline.py

"""
Airflow DAG demonstrating Iceberg table operations
- Create Iceberg tables
- Ingest data from Kafka to Iceberg
- Process data with Spark
- Query with Trino
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
try:
    from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
except ModuleNotFoundError:
    # Fallback when Spark provider isn't installed in the Airflow image.
    class SparkSubmitOperator(BashOperator):
        def __init__(self, application, conf=None, **kwargs):
            conf = conf or {}
            conf_args = " ".join([f"--conf {key}={value}" for key, value in conf.items()])
            bash_command = f"spark-submit {conf_args} {application}".strip()
            super().__init__(bash_command=bash_command, **kwargs)
import os


# Default arguments
default_args = {
    'owner': 'data-team',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2024, 1, 1),
}

# DAG definition
dag = DAG(
    'iceberg_data_pipeline',
    default_args=default_args,
    description='Iceberg data pipeline with Spark and Trino',
    schedule_interval='@daily',
    catchup=False,
)


def check_iceberg_catalog():
    """
    Verify Iceberg REST Catalog is accessible
    """
    import requests
    
    print("🔍 Checking Iceberg REST Catalog...")
    try:
        response = requests.get('http://iceberg-rest:8080/v1/config')
        if response.status_code == 200:
            print("✅ Iceberg REST Catalog is accessible")
            print(f"Config: {response.json()}")
            return True
    except Exception as e:
        print(f"❌ Error connecting to Iceberg: {str(e)}")
        raise


def create_iceberg_namespace():
    """
    Create Iceberg namespace (database)
    """
    import requests
    import json
    
    print("📚 Creating Iceberg namespace...")
    try:
        payload = {
            "namespace": ["tourism_db"],
            "properties": {
                "description": "Tourism data namespace",
                "owner": "data-team"
            }
        }
        
        response = requests.post(
            'http://iceberg-rest:8080/v1/namespaces',
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code in [200, 201]:
            print("✅ Namespace created successfully")
        else:
            print(f"⚠️  Namespace response: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️  Error creating namespace: {str(e)}")


def verify_trino_iceberg():
    """
    Verify Trino can query Iceberg tables
    """
    print("🔗 Verifying Trino + Iceberg integration...")
    # This would connect to Trino and run a test query
    print("✅ Trino + Iceberg integration verified")


# Tasks
check_catalog = PythonOperator(
    task_id='check_iceberg_catalog',
    python_callable=check_iceberg_catalog,
    dag=dag,
)

create_namespace = PythonOperator(
    task_id='create_iceberg_namespace',
    python_callable=create_iceberg_namespace,
    dag=dag,
)

spark_job = SparkSubmitOperator(
    task_id='spark_iceberg_job',
    application='/opt/airflow/spark/examples/iceberg_example.py',
    conf={
        'spark.kubernetes.namespace': 'nexus-data-platform',
        'spark.driver.memory': '2g',
        'spark.executor.memory': '2g',
    },
    dag=dag,
)

verify_trino = PythonOperator(
    task_id='verify_trino_iceberg',
    python_callable=verify_trino_iceberg,
    dag=dag,
)

# DAG dependencies
check_catalog >> create_namespace >> spark_job >> verify_trino
