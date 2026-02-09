# 🛠️ Data Platform Implementation Guide - Hướng Dẫn Triển Khai Thực Tế

## 1️⃣ Quick Start: Triển Khai Stack Cơ Bản

### Bước 1: Cài Đặt Docker Compose

```bash
cd /workspaces/Nexus-Data-Platform
mkdir -p docker-stack
cd docker-stack

# Tạo docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # 1. Message Queue
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
    ports:
      - "2181:2181"

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT

  # 2. Object Storage
  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  # 3. SQL Query Engine
  trino:
    image: trinodb/trino:latest
    ports:
      - "8080:8080"
    volumes:
      - ./trino/config.properties:/etc/trino/config.properties
      - ./trino/catalog:/etc/trino/catalog
    environment:
      TRINO_PASSWORD: admin123

  # 4. Analytics Database
  clickhouse:
    image: clickhouse/clickhouse-server:latest
    ports:
      - "8123:8123"
      - "9000:9000"
    volumes:
      - clickhouse_data:/var/lib/clickhouse
    environment:
      CLICKHOUSE_DB: default

  # 5. Search Engine
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.10.0
    ports:
      - "9200:9200"
      - "9300:9300"
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  # 6. Caching Layer
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # 7. PostgreSQL for Metadata
  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: admin123
      POSTGRES_DB: dataplatform
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # 8. Orchestration
  airflow-webserver:
    image: apache/airflow:2.7.0-python3.11
    ports:
      - "8888:8080"
    environment:
      AIRFLOW_UID: 50000
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql://admin:admin123@postgres:5432/airflow
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
    depends_on:
      - postgres
    command: webserver

  airflow-scheduler:
    image: apache/airflow:2.7.0-python3.11
    environment:
      AIRFLOW_UID: 50000
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql://admin:admin123@postgres:5432/airflow
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
    depends_on:
      - postgres
    command: scheduler

  # 9. BI Tool
  superset:
    image: apache/superset:latest
    ports:
      - "8088:8088"
    environment:
      SUPERSET_SECRET_KEY: supersecretkey
    depends_on:
      - postgres

volumes:
  minio_data:
  clickhouse_data:
  elasticsearch_data:
  redis_data:
  postgres_data:
EOF
```

### Bước 2: Khởi Động Stack

```bash
docker-compose up -d

# Kiểm tra status
docker-compose ps

# View logs
docker-compose logs -f
```

---

## 2️⃣ Data Ingestion - Chi Tiết

### Kafka Setup & Usage

```python
# producer.py - Tạo dữ liệu vào Kafka
from kafka import KafkaProducer
import json
from datetime import datetime
import time
import random

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def generate_event():
    return {
        'timestamp': datetime.now().isoformat(),
        'user_id': random.randint(1, 1000),
        'event_type': random.choice(['click', 'purchase', 'view', 'search']),
        'amount': round(random.uniform(10, 500), 2),
        'region': random.choice(['VN', 'SG', 'TH', 'ID'])
    }

# Gửi events
for i in range(100):
    event = generate_event()
    producer.send('events', value=event)
    print(f"Sent: {event}")
    time.sleep(1)

producer.flush()
producer.close()
```

```python
# consumer.py - Đọc từ Kafka
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'events',
    bootstrap_servers=['localhost:9092'],
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest'
)

print("Listening to Kafka topic 'events'...")
for message in consumer:
    event = message.value
    print(f"Received: {event}")
    # Process event...
```

### Airflow DAG - Automated Ingestion

```python
# airflow/dags/data_ingestion.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import requests
import json

default_args = {
    'owner': 'data-team',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'data_ingestion_pipeline',
    default_args=default_args,
    description='Daily data ingestion from APIs',
    schedule_interval='@daily',
    start_date=days_ago(1),
    catchup=False,
)

def extract_api_data():
    """Extract data from external API"""
    urls = [
        'https://api.tourism.io/attractions',
        'https://api.travel.io/hotels',
        'https://api.booking.io/flights'
    ]
    
    all_data = {}
    for url in urls:
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            all_data[url] = response.json()
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
    
    # Save to MinIO
    with open('/tmp/raw_data.json', 'w') as f:
        json.dump(all_data, f)
    
    return all_data

def upload_to_minio():
    """Upload extracted data to MinIO"""
    from minio import Minio
    
    client = Minio(
        "localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
    )
    
    with open('/tmp/raw_data.json', 'rb') as f:
        client.put_object(
            'data-lake',
            'raw/data.json',
            f,
            length=-1
        )
    print("Data uploaded to MinIO")

def validate_data():
    """Data quality checks"""
    import json
    
    with open('/tmp/raw_data.json', 'r') as f:
        data = json.load(f)
    
    # Validation checks
    assert len(data) > 0, "No data extracted"
    assert all(isinstance(v, dict) for v in data.values()), "Invalid data format"
    
    print("Data validation passed")

# Define tasks
extract_task = PythonOperator(
    task_id='extract_data',
    python_callable=extract_api_data,
    dag=dag,
)

upload_task = PythonOperator(
    task_id='upload_to_storage',
    python_callable=upload_to_minio,
    dag=dag,
)

validate_task = PythonOperator(
    task_id='validate_data',
    python_callable=validate_data,
    dag=dag,
)

# Define dependencies
extract_task >> upload_task >> validate_task
```

---

## 3️⃣ Data Processing - Spark Jobs

### Spark Batch Processing

```python
# spark_processing.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, count, when, year, month
from pyspark.sql.window import Window

spark = SparkSession.builder \
    .appName("DataProcessing") \
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .getOrCreate()

# Read raw data from MinIO
df_raw = spark.read.json("s3a://data-lake/raw/")

# Data cleaning & transformation
df_clean = df_raw \
    .dropna(subset=['user_id', 'event_type']) \
    .filter(col('amount') > 0) \
    .withColumn('year', year(col('timestamp'))) \
    .withColumn('month', month(col('timestamp')))

# Aggregations
df_agg = df_clean.groupBy('region', 'event_type') \
    .agg(
        count('*').alias('event_count'),
        avg('amount').alias('avg_amount'),
        count(when(col('amount') > 100, 1)).alias('high_value_count')
    )

# Write processed data
df_agg.write \
    .format('parquet') \
    .mode('overwrite') \
    .save("s3a://data-lake/processed/")

print("Processing complete!")
```

### dbt Transformation

```sql
-- models/facts/fact_events.sql
{{ config(
    materialized='table',
    schema='analytics',
    unique_key='event_id'
) }}

SELECT 
    md5(CONCAT(user_id, timestamp, event_type)) as event_id,
    user_id,
    event_type,
    amount,
    region,
    CAST(timestamp AS DATE) as event_date,
    EXTRACT(HOUR FROM timestamp) as event_hour,
    NOW() as loaded_at
FROM {{ source('raw', 'events_raw') }}
WHERE timestamp >= '{{ var("start_date") }}'
```

---

## 4️⃣ Analytics Serving

### ClickHouse Setup

```sql
-- Create analytics database
CREATE DATABASE IF NOT EXISTS analytics;

-- Create events table
CREATE TABLE analytics.events (
    timestamp DateTime,
    user_id UInt32,
    event_type String,
    amount Float64,
    region String
) ENGINE = MergeTree()
ORDER BY (timestamp, user_id);

-- Fast aggregation queries
SELECT 
    region,
    event_type,
    count() as cnt,
    sum(amount) as total_amount,
    avg(amount) as avg_amount
FROM analytics.events
WHERE toDate(timestamp) = today()
GROUP BY region, event_type
ORDER BY cnt DESC;
```

### Python Client

```python
from clickhouse_driver import Client

client = Client('localhost', port=9000)

# Insert data
client.execute(
    'INSERT INTO analytics.events VALUES',
    [
        ('2024-01-01 10:00:00', 123, 'purchase', 99.99, 'VN'),
        ('2024-01-01 10:01:00', 124, 'click', 0, 'SG'),
    ]
)

# Query data
result = client.execute('''
    SELECT region, count() as cnt 
    FROM analytics.events 
    GROUP BY region
''')

print(result)
```

---

## 5️⃣ API & Dashboard

### FastAPI for Data API

```python
# app/main.py
from fastapi import FastAPI, Query
from elasticsearch import Elasticsearch
import redis
from functools import lru_cache
import json

app = FastAPI(title="Data Platform API")

# Initialize clients
es = Elasticsearch(['http://elasticsearch:9200'])
cache = redis.Redis(host='redis', port=6379, db=0)

@app.get("/events")
def get_events(
    user_id: int = Query(...),
    limit: int = Query(10, le=100),
    offset: int = Query(0)
):
    """Get events for user"""
    cache_key = f"user:{user_id}:events"
    
    # Try cache first
    cached = cache.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Query Elasticsearch
    result = es.search(
        index="events",
        body={
            "query": {"match": {"user_id": user_id}},
            "size": limit,
            "from": offset
        }
    )
    
    events = [hit['_source'] for hit in result['hits']['hits']]
    cache.setex(cache_key, 3600, json.dumps(events))
    
    return {"events": events, "total": result['hits']['total']['value']}

@app.get("/analytics/region-stats")
def region_stats():
    """Regional statistics"""
    # Query ClickHouse
    from clickhouse_driver import Client
    client = Client('clickhouse', port=9000)
    
    result = client.execute('''
        SELECT 
            region,
            count() as event_count,
            sum(amount) as total_revenue,
            avg(amount) as avg_amount
        FROM analytics.events
        WHERE toDate(timestamp) = today()
        GROUP BY region
    ''')
    
    return {
        "regions": [
            {
                "name": row[0],
                "events": row[1],
                "revenue": row[2],
                "avg_amount": row[3]
            }
            for row in result
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### GraphQL Schema

```python
# graphql/schema.py
import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType

class Event(graphene.ObjectType):
    id = graphene.ID()
    user_id = graphene.Int()
    event_type = graphene.String()
    amount = graphene.Float()
    timestamp = graphene.DateTime()
    region = graphene.String()

class Analytics(graphene.ObjectType):
    total_revenue = graphene.Float()
    event_count = graphene.Int()
    avg_amount = graphene.Float()

class Query(graphene.ObjectType):
    user_events = graphene.List(Event, user_id=graphene.Int(required=True))
    region_analytics = graphene.Field(Analytics, region=graphene.String(required=True))
    
    def resolve_user_events(self, info, user_id):
        # Query from database
        return Event.query.filter_by(user_id=user_id).all()
    
    def resolve_region_analytics(self, info, region):
        # Aggregate from ClickHouse
        return Analytics(...)

schema = graphene.Schema(query=Query)
```

---

## ⚡ Performance Tuning

### Kafka Optimization

```properties
# server.properties
num.network.threads=8
num.io.threads=8
socket.send.buffer.bytes=102400
socket.receive.buffer.bytes=102400
socket.request.max.bytes=104857600

# Topic optimization
--create --topic events --partitions 12 --replication-factor 3
```

### Spark Configuration

```bash
spark-submit \
  --master spark://localhost:7077 \
  --executor-memory 4g \
  --driver-memory 2g \
  --executor-cores 4 \
  --conf spark.sql.shuffle.partitions=200 \
  --conf spark.default.parallelism=200 \
  spark_processing.py
```

### ClickHouse Optimization

```sql
-- Enable compression
ALTER TABLE events MODIFY SETTING compress_mark_type='lz4';

-- Create indexes
ALTER TABLE events ADD INDEX idx_user_id user_id TYPE bloom_filter;

-- Partitioning
CREATE TABLE events_partitioned (
    timestamp DateTime,
    user_id UInt32
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY user_id;
```

---

## 📊 Monitoring & Debugging

### Health Check Script

```bash
#!/bin/bash
# health_check.sh

echo "🔍 Checking Data Platform Health..."

# Check Kafka
echo "Kafka:"
docker exec kafka kafka-broker-api-versions.sh --bootstrap-server kafka:9092 || echo "❌ Kafka down"

# Check MinIO
echo "MinIO:"
curl -s http://localhost:9000/minio/health/live || echo "❌ MinIO down"

# Check ClickHouse
echo "ClickHouse:"
curl -s http://localhost:8123/ping || echo "❌ ClickHouse down"

# Check Redis
echo "Redis:"
redis-cli -h localhost ping || echo "❌ Redis down"

# Check Elasticsearch
echo "Elasticsearch:"
curl -s http://localhost:9200/_cluster/health || echo "❌ ES down"

# Check Airflow
echo "Airflow:"
curl -s http://localhost:8888/health || echo "❌ Airflow down"

echo "✅ Health check complete"
```

---

## 🎓 Next Steps

1. **Ingestion**: Setup Kafka producers & Airflow DAGs
2. **Processing**: Create Spark jobs & dbt models
3. **Serving**: Configure ClickHouse & Elasticsearch
4. **API**: Build FastAPI endpoints
5. **Monitoring**: Setup Superset dashboards
