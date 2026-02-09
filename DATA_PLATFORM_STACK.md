# 🏗️ Data Platform Stack - Công Nghệ Opensource Hoàn Chỉnh

## 📐 Kiến Trúc Tổng Quan

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA PLATFORM ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐             │
│  │ DATA SOURCES │────▶│  INGESTION   │────▶│   STORAGE    │             │
│  │              │     │              │     │              │             │
│  │ • APIs       │     │ • Kafka      │     │ • HDFS       │             │
│  │ • Databases  │     │ • Airflow    │     │ • S3/MinIO   │             │
│  │ • Files      │     │ • Logstash   │     │ • Delta Lake │             │
│  │ • Streams    │     │ • Nifi       │     │              │             │
│  └──────────────┘     └──────────────┘     └──────────────┘             │
│                                                      ▼                   │
│                                            ┌──────────────────┐         │
│                                            │   PROCESSING     │         │
│                                            │                  │         │
│                                            │ • Spark          │         │
│                                            │ • Flink          │         │
│                                            │ • Presto/Trino   │         │
│                                            │ • Dbt            │         │
│                                            └──────────────────┘         │
│                                                      ▼                   │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │  SERVING LAYER                                           │          │
│  │  • Clickhouse/Druid (Analytics)                         │          │
│  │  • Elasticsearch (Search)                               │          │
│  │  • Redis (Cache)                                        │          │
│  │  • GraphQL API                                          │          │
│  └──────────────────────────────────────────────────────────┘          │
│                                                      ▼                   │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │  CONSUMPTION                                             │          │
│  │  • BI Tools (Superset, Metabase)                        │          │
│  │  • Dashboards (Grafana)                                 │          │
│  │  • ML Models (MLflow)                                   │          │
│  │  • Data Apps (Streamlit, Jupyter)                       │          │
│  └──────────────────────────────────────────────────────────┘          │
│                                                      │                   │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │  MONITORING & GOVERNANCE (Cross-cutting)                │          │
│  │  • Data Quality (Great Expectations)                    │          │
│  │  • Metadata Catalog (DataHub, Atlas)                    │          │
│  │  • Infrastructure (Prometheus, Grafana)                 │          │
│  └──────────────────────────────────────────────────────────┘          │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 1. DATA INGESTION (Thu Thập Dữ Liệu)

### **A. Kafka** (Event Streaming)
```bash
# Cài đặt Kafka
docker run -d \
  --name kafka \
  -p 9092:9092 \
  -e KAFKA_BROKER_ID=1 \
  -e KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092 \
  confluentinc/cp-kafka:latest
```
**Ưu điểm:**
- ✅ Xử lý stream real-time 1 triệu events/giây+
- ✅ Fault-tolerant, highly scalable
- ✅ Tích hợp dễ với các công cụ khác

---

### **B. Apache Airflow** (Workflow Orchestration)
```python
# Example DAG for data ingestion
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def extract_api_data():
    import requests
    response = requests.get('https://api.example.com/data')
    return response.json()

with DAG('daily_data_ingestion', start_date=datetime(2024,1,1), schedule_interval='@daily'):
    extract = PythonOperator(
        task_id='extract_data',
        python_callable=extract_api_data
    )
```
**Ưu điểm:**
- ✅ Scheduling & orchestration
- ✅ DAG visualization
- ✅ Error handling & retry logic

---

### **C. Apache NiFi** (Data Flow Automation)
```xml
<!-- NiFi Configuration -->
<nifi>
  <processors>
    <processor>
      <type>GetHTTP</type>
      <property name="URL">https://api.data.io</property>
    </processor>
    <processor>
      <type>PutS3Object</type>
      <property name="Bucket">data-lake</property>
    </processor>
  </processors>
</nifi>
```
**Ưu điểm:**
- ✅ Visual UI cho data routing
- ✅ Real-time monitoring
- ✅ Backpressure handling

---

### **D. Logstash/Filebeat** (Log Ingestion)
```yaml
# filebeat.yml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/app/*.log

output.elasticsearch:
  hosts: ["localhost:9200"]
  index: "logs-%{[agent.version]}-%{+yyyy.MM.dd}"
```

---

## 💾 2. DATA STORAGE (Lưu Trữ Dữ Liệu)

### **A. HDFS** (Hadoop Distributed File System)
```bash
# Khởi tạo HDFS
hdfs namenode -format
start-dfs.sh

# Upload dữ liệu
hdfs dfs -put /local/data.csv /data/
```
**Ưu điểm:**
- ✅ Scalable storage cho big data
- ✅ Fault tolerance
- ✅ Write-once-read-many (WORM)

---

### **B. MinIO/S3** (Object Storage)
```python
# MinIO Client
from minio import Minio

client = Minio(
    "minio.example.com",
    access_key="minioadmin",
    secret_key="minioadmin"
)

# Upload file
with open('data.parquet', 'rb') as f:
    client.put_object('data-lake', 'exports/data.parquet', f, length=-1)
```
**Ưu điểm:**
- ✅ S3-compatible
- ✅ Unlimited scalability
- ✅ Multi-datacenter support

---

### **C. Delta Lake** (ACID Transactions)
```python
# Write data with Delta Lake
import pandas as pd
from delta import configure_spark_with_delta_pip

spark = configure_spark_with_delta_pip(SparkSession.builder).getOrCreate()

df = pd.DataFrame({'id': [1, 2, 3], 'value': [10, 20, 30]})
spark.createDataFrame(df).write.format('delta').mode('overwrite').save('s3://data/delta/')

# Time travel
spark.read.format('delta').option('versionAsOf', 0).load('s3://data/delta/').show()
```
**Ưu điểm:**
- ✅ ACID transactions trên data lake
- ✅ Schema enforcement
- ✅ Time travel capability

---

### **D. PostgreSQL + TimescaleDB** (Time-series Data)
```sql
-- TimescaleDB setup
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

CREATE TABLE metrics (
  time TIMESTAMPTZ NOT NULL,
  device_id TEXT,
  temperature FLOAT,
  humidity FLOAT
);

SELECT create_hypertable('metrics', 'time', if_not_exists => TRUE);

-- Query example
SELECT device_id, AVG(temperature) 
FROM metrics 
WHERE time > NOW() - INTERVAL '7 days'
GROUP BY device_id;
```

---

## ⚙️ 3. DATA PROCESSING (Xử Lý Dữ Liệu)

### **A. Apache Spark** (Batch & Stream Processing)
```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, window

spark = SparkSession.builder.appName("DataProcessor").getOrCreate()

# Batch Processing
df = spark.read.parquet('s3://data-lake/raw/')
processed = df.filter(col('quality_score') > 0.8) \
    .groupBy('region') \
    .agg(avg('revenue').alias('avg_revenue'))
processed.write.parquet('s3://data-lake/processed/')

# Stream Processing
kafka_df = spark.readStream.format('kafka') \
    .option('kafka.bootstrap.servers', 'localhost:9092') \
    .option('subscribe', 'events') \
    .load()

transformed = kafka_df.groupBy(window('timestamp', '5 minutes'), 'event_type').count()
transformed.writeStream.format('console').start().awaitTermination()
```
**Ưu điểm:**
- ✅ Xử lý batch & stream
- ✅ Distributed computing
- ✅ 100x faster than Hadoop MapReduce

---

### **B. Apache Flink** (Real-time Stream Processing)
```java
// Flink Streaming Job
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

DataStream<Event> events = env
    .addSource(new KafkaSource<>(...))
    .keyBy(e -> e.userId)
    .window(TumblingEventTimeWindows.of(Time.minutes(5)))
    .aggregate(new CountAggregate(), new WindowFunction() {...})
    .addSink(new ElasticsearchSink<>(...));

env.execute("RealTimeAnalytics");
```
**Ưu điểm:**
- ✅ Sub-second latency
- ✅ Event-time processing
- ✅ Complex event processing (CEP)

---

### **C. dbt** (Data Transformation Orchestration)
```sql
-- models/staging/stg_customers.sql
{{ config(
    materialized='table',
    unique_key='customer_id'
) }}

SELECT 
    id as customer_id,
    name,
    email,
    created_at,
    _dbt_extracted_at as loaded_at
FROM {{ source('raw', 'customers') }}
WHERE deleted_at IS NULL

-- dbt run
-- dbt test
-- dbt docs generate
```
**Ưu điểm:**
- ✅ Version control for data
- ✅ Dependency resolution
- ✅ Testing & documentation

---

### **D. Presto/Trino** (SQL Query Engine)
```sql
-- Query across multiple data sources
SELECT 
    c.customer_id,
    c.name,
    o.total_amount,
    m.avg_price
FROM hive.default.customers c
JOIN postgres.public.orders o ON c.id = o.customer_id
JOIN elasticsearch.products m ON o.product_id = m.id
WHERE c.country = 'Vietnam'
```
**Ưu điểm:**
- ✅ Query multiple data sources with SQL
- ✅ In-memory query execution
- ✅ ANSI SQL compliant

---

## 📊 4. DATA SERVING (Phân Phối Dữ Liệu)

### **A. ClickHouse** (Analytics Database)
```sql
-- Create table
CREATE TABLE events (
    timestamp DateTime,
    user_id UInt32,
    event_type String,
    value Float64
) ENGINE = MergeTree()
ORDER BY (timestamp, user_id);

-- Fast aggregation queries
SELECT 
    event_type,
    count() as count,
    avg(value) as avg_value
FROM events
WHERE timestamp > now() - interval 7 day
GROUP BY event_type;
```
**Ưu điểm:**
- ✅ 100-1000x faster queries
- ✅ Columnar storage
- ✅ Real-time analytics

---

### **B. Elasticsearch** (Search & Analytics)
```json
// Index documents
POST /events/_doc
{
  "timestamp": "2024-01-01T10:00:00Z",
  "user_id": 123,
  "event_type": "purchase",
  "amount": 99.99
}

// Search with aggregation
GET /events/_search
{
  "aggs": {
    "by_event_type": {
      "terms": {
        "field": "event_type.keyword"
      }
    }
  }
}
```
**Ưu điểm:**
- ✅ Full-text search
- ✅ Sub-second search latency
- ✅ Real-time aggregations

---

### **C. Redis** (Caching & Cache Layer)
```python
import redis

cache = redis.Redis(host='localhost', port=6379, db=0)

# Cache query results
def get_user_data(user_id):
    cached = cache.get(f'user:{user_id}')
    if cached:
        return json.loads(cached)
    
    # Query from DB
    data = db.query(f'SELECT * FROM users WHERE id = {user_id}')
    cache.setex(f'user:{user_id}', 3600, json.dumps(data))
    return data
```
**Ưu điểm:**
- ✅ Sub-millisecond latency
- ✅ High throughput
- ✅ Support pub/sub

---

### **D. GraphQL API** (Data Access Layer)
```graphql
type Query {
  user(id: ID!): User
  events(filter: EventFilter!): [Event!]!
  analytics(metric: String!): Analytics
}

type User {
  id: ID!
  name: String!
  events: [Event!]!
}

type Event {
  id: ID!
  type: String!
  timestamp: DateTime!
  value: Float
}

# Query example
query {
  user(id: "123") {
    name
    events(limit: 10) {
      type
      timestamp
      value
    }
  }
}
```

---

## 📱 5. DATA CONSUMPTION (Tiêu Thụ Dữ Liệu)

### **A. Apache Superset** (BI Dashboard)
```python
# Create dashboard
docker run -d -p 8088:8088 \
  --name superset \
  apache/superset:latest

# Setup
superset fab create-admin --username admin --password admin

# Access: http://localhost:8088
```

---

### **B. Metabase** (Analytics Dashboard)
```bash
docker run -d -p 3000:3000 \
  -e MB_DB_TYPE=postgres \
  -e MB_DB_DBNAME=metabase \
  metabase/metabase:latest
```

---

### **C. Great Expectations** (Data Quality)
```python
import great_expectations as gx

context = gx.get_context()

# Define expectations
validator = context.get_validator(
    batch_request={
        "datasource_name": "my_datasource",
        "data_connector_name": "default",
        "data_asset_name": "my_table"
    }
)

validator.expect_column_values_to_be_in_set(
    'status', ['active', 'inactive']
)
validator.save_expectation_suite(discard_failed_expectations=False)

# Validate
checkpoint = context.add_checkpoint(
    name="my_checkpoint",
    validations=[...],
)
results = checkpoint.run()
```

---

### **D. MLflow** (ML Lifecycle Management)
```python
import mlflow
from sklearn.ensemble import RandomForestClassifier

with mlflow.start_run():
    model = RandomForestClassifier(n_estimators=100)
    model.fit(X_train, y_train)
    
    accuracy = model.score(X_test, y_test)
    mlflow.log_metric("accuracy", accuracy)
    mlflow.log_param("n_estimators", 100)
    mlflow.sklearn.log_model(model, "model")

# Serve model
mlflow models serve -m runs:/{run_id}/model -p 5000
```

---

### **E. Grafana** (Metrics Visualization)
```yaml
# docker-compose.yml
grafana:
  image: grafana/grafana:latest
  ports:
    - "3000:3000"
  environment:
    GF_SECURITY_ADMIN_PASSWORD: admin123
  volumes:
    - grafana_data:/var/lib/grafana
```

**Dashboard Configuration:**
```json
{
  "dashboard": {
    "title": "Data Pipeline Metrics",
    "panels": [
      {
        "title": "Query Latency",
        "targets": [{
          "expr": "histogram_quantile(0.95, query_duration_seconds)"
        }]
      }
    ]
  }
}
```

**Ưu điểm:**
- ✅ Real-time metrics visualization
- ✅ Alerting capabilities
- ✅ Multi-datasource support

---

### **F. Jupyter Notebook** (Interactive Data Science)
```python
# Launch Jupyter
docker run -d -p 8888:8888 \
  -v $(pwd)/notebooks:/home/jovyan/work \
  jupyter/datascience-notebook:latest

# Example notebook cell
import pandas as pd
import matplotlib.pyplot as plt
from pyspark.sql import SparkSession

# Connect to Spark
spark = SparkSession.builder \
    .appName("DataAnalysis") \
    .config("spark.sql.warehouse.dir", "s3://data-lake/") \
    .getOrCreate()

# Load and visualize data
df = spark.read.parquet("s3://data-lake/processed/events/")
df.groupBy("event_type").count().toPandas().plot(kind='bar')
plt.show()
```

**Ưu điểm:**
- ✅ Interactive data exploration
- ✅ Support multiple kernels (Python, R, Scala)
- ✅ Share notebooks as reports

---

### **G. Streamlit** (Data Apps)
```python
# app.py - Streamlit Dashboard
import streamlit as st
import pandas as pd
import clickhouse_driver

st.title("📊 Tourism Analytics Dashboard")

# Connect to ClickHouse
client = clickhouse_driver.Client(
    host='localhost',
    port=8123,
    user='admin',
    password='admin123'
)

# Query data
query = """
    SELECT 
        region,
        count() as total_bookings,
        sum(amount) as revenue
    FROM analytics.events
    WHERE timestamp > now() - interval 7 day
    GROUP BY region
"""

df = pd.DataFrame(client.execute(query), columns=['Region', 'Bookings', 'Revenue'])

# Display metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Bookings", df['Bookings'].sum())
col2.metric("Total Revenue", f"${df['Revenue'].sum():,.2f}")
col3.metric("Avg Booking Value", f"${df['Revenue'].sum() / df['Bookings'].sum():,.2f}")

# Charts
st.bar_chart(df.set_index('Region')['Revenue'])
st.dataframe(df)
```

**Run Streamlit:**
```bash
streamlit run app.py --server.port 8501
# Access: http://localhost:8501
```

**Ưu điểm:**
- ✅ Quick prototyping of data apps
- ✅ Interactive widgets
- ✅ Easy deployment

---

## 🔍 6. MONITORING & GOVERNANCE (Quản Trị & Giám Sát)

### **A. Great Expectations** (Data Quality Validation)
```python
import great_expectations as gx
from great_expectations.checkpoint import Checkpoint

context = gx.get_context()

# Create expectation suite
suite = context.add_expectation_suite("tourism_data_quality")

validator = context.get_validator(
    batch_request={
        "datasource_name": "clickhouse_datasource",
        "data_connector_name": "default",
        "data_asset_name": "analytics.events"
    },
    expectation_suite_name="tourism_data_quality"
)

# Define quality expectations
validator.expect_column_values_to_not_be_null("user_id")
validator.expect_column_values_to_be_between("amount", min_value=0, max_value=100000)
validator.expect_column_values_to_be_in_set("event_type", ["booking", "view", "click"])
validator.expect_table_row_count_to_be_between(min_value=1000)

validator.save_expectation_suite(discard_failed_expectations=False)

# Run validation checkpoint
checkpoint = context.add_checkpoint(
    name="daily_quality_check",
    config_version=1,
    validations=[
        {
            "batch_request": batch_request,
            "expectation_suite_name": "tourism_data_quality"
        }
    ]
)

results = checkpoint.run()
print(f"Validation Success: {results['success']}")
```

**Ưu điểm:**
- ✅ Automated data quality checks
- ✅ Documentation generation
- ✅ Integration with Airflow/dbt

---

### **B. Apache Atlas** (Metadata Catalog)
```python
# Atlas REST API - Register Data Asset
import requests

atlas_url = "http://localhost:21000"
auth = ("admin", "admin")

# Define entity
entity = {
    "entity": {
        "typeName": "hive_table",
        "attributes": {
            "qualifiedName": "analytics.events@cluster",
            "name": "events",
            "description": "Tourism events tracking table",
            "owner": "data-team",
            "createTime": 1609459200000,
            "columns": [
                {"name": "user_id", "type": "int", "comment": "User identifier"},
                {"name": "event_type", "type": "string", "comment": "Event category"},
                {"name": "amount", "type": "float", "comment": "Transaction amount"}
            ]
        }
    }
}

response = requests.post(
    f"{atlas_url}/api/atlas/v2/entity",
    json=entity,
    auth=auth
)

print(f"Entity registered: {response.json()['guid']}")
```

**Features:**
- ✅ Data lineage tracking
- ✅ Business glossary
- ✅ Data classification (PII, sensitive)

---

### **C. DataHub** (Modern Data Catalog)
```yaml
# docker-compose.yml for DataHub
datahub:
  services:
    datahub-gms:
      image: linkedin/datahub-gms:latest
      ports:
        - "8080:8080"
    
    datahub-frontend:
      image: linkedin/datahub-frontend-react:latest
      ports:
        - "9002:9002"
    
    datahub-actions:
      image: acryldata/datahub-actions:latest
```

**Ingest Metadata:**
```yaml
# recipe.yml
source:
  type: clickhouse
  config:
    host_port: localhost:8123
    username: admin
    password: admin123
    database: analytics

sink:
  type: datahub-rest
  config:
    server: http://localhost:8080
```

```bash
# Run ingestion
datahub ingest -c recipe.yml
```

**Ưu điểm:**
- ✅ Modern UI/UX
- ✅ Data discovery & search
- ✅ Column-level lineage
- ✅ Data profiling

---

### **D. Prometheus + Grafana** (Infrastructure Monitoring)
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'spark'
    static_configs:
      - targets: ['spark-master:4040']
  
  - job_name: 'clickhouse'
    static_configs:
      - targets: ['clickhouse:8001']
  
  - job_name: 'kafka'
    static_configs:
      - targets: ['kafka:9092']
  
  - job_name: 'airflow'
    static_configs:
      - targets: ['airflow:8080']
```

**Docker Compose:**
```yaml
prometheus:
  image: prom/prometheus:latest
  ports:
    - "9090:9090"
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
    - prometheus_data:/prometheus

grafana:
  image: grafana/grafana:latest
  ports:
    - "3000:3000"
  environment:
    GF_SECURITY_ADMIN_PASSWORD: admin123
  volumes:
    - grafana_data:/var/lib/grafana
```

**Key Metrics to Monitor:**
```promql
# Kafka lag
kafka_consumer_lag_sum

# Spark job duration
histogram_quantile(0.95, spark_job_duration_seconds_bucket)

# ClickHouse query rate
rate(clickhouse_query_total[5m])

# Airflow DAG failures
airflow_dag_failed_total

# Data quality score
great_expectations_validation_success_rate
```

**Alerting Rules:**
```yaml
groups:
  - name: data_platform_alerts
    interval: 30s
    rules:
      - alert: HighKafkaLag
        expr: kafka_consumer_lag_sum > 10000
        for: 5m
        annotations:
          summary: "Kafka consumer lag is high"
      
      - alert: AirflowDAGFailed
        expr: increase(airflow_dag_failed_total[10m]) > 0
        annotations:
          summary: "Airflow DAG failed"
      
      - alert: DataQualityFailure
        expr: great_expectations_validation_success_rate < 0.95
        annotations:
          summary: "Data quality validation below 95%"
```

**Ưu điểm:**
- ✅ Time-series metrics storage
- ✅ Powerful query language (PromQL)
- ✅ Alerting & notification
- ✅ Service discovery

---

### **E. Apache Ranger** (Data Access Control)
```xml
<!-- Ranger Policy for ClickHouse -->
<policy>
  <name>analytics_events_policy</name>
  <service>clickhouse-service</service>
  <resources>
    <database>analytics</database>
    <table>events</table>
  </resources>
  <policyItems>
    <accesses>
      <type>select</type>
      <isAllowed>true</isAllowed>
    </accesses>
    <users>
      <user>data-analyst-team</user>
    </users>
  </policyItems>
  <policyItems>
    <accesses>
      <type>select</type>
      <type>insert</type>
      <type>update</type>
      <isAllowed>true</isAllowed>
    </accesses>
    <users>
      <user>data-engineer-team</user>
    </users>
  </policyItems>
</policy>
```

**Ưu điểm:**
- ✅ Centralized access control
- ✅ Fine-grained permissions
- ✅ Audit logging

---

## 🚀 Complete Docker Compose Stack

```yaml
version: '3.8'

services:
  # Orchestration
  airflow:
    image: apache/airflow:2.7.0
    ports:
      - "8080:8080"
    environment:
      AIRFLOW_UID: 50000

  # Message Queue
  kafka:
    image: confluentinc/cp-kafka:latest
    ports:
      - "9092:9092"
    environment:
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181

  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    ports:
      - "2181:2181"

  # Storage
  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
    volumes:
      - minio_data:/data
    command: server /data

  # Processing
  spark-master:
    image: bitnami/spark:latest
    ports:
      - "8081:8080"
    environment:
      SPARK_MODE: master

  # Analytics
  clickhouse:
    image: clickhouse/clickhouse-server:latest
    ports:
      - "8123:8123"
  
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    ports:
      - "9200:9200"

  # Caching
  redis:
    image: redis:latest
    ports:
      - "6379:6379"

  # BI Tools
  superset:
    image: apache/superset:latest
    ports:
      - "8088:8088"
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin123
  
  jupyter:
    image: jupyter/datascience-notebook:latest
    ports:
      - "8888:8888"
    volumes:
      - ./notebooks:/home/jovyan/work
  
  # Monitoring & Governance
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
  
  datahub-gms:
    image: linkedin/datahub-gms:latest
    ports:
      - "8080:8080"

volumes:
  minio_data:
  prometheus_data:
  grafana_data:
```

---

## 📋 Deployment Checklist - 6 Tầng Hoàn Chỉnh

### Tầng 1: Data Ingestion
- [ ] **Kafka**: Event streaming (port 9092)
- [ ] **Zookeeper**: Kafka coordination (port 2181)
- [ ] **Airflow**: Workflow orchestration (port 8080)
- [ ] **NiFi**: Visual data flow (optional)
- [ ] **Logstash/Filebeat**: Log collection

### Tầng 2: Data Storage
- [ ] **MinIO**: S3-compatible object storage (port 9000-9001)
- [ ] **HDFS**: Distributed file system (optional)
- [ ] **Delta Lake**: ACID transactions on data lake
- [ ] **PostgreSQL**: Metadata database (port 5432)
- [ ] **TimescaleDB**: Time-series extension

### Tầng 3: Data Processing
- [ ] **Spark**: Batch & stream processing (port 8081)
- [ ] **Flink**: Real-time stream processing (optional)
- [ ] **dbt**: Data transformation orchestration
- [ ] **Trino/Presto**: Federated SQL query engine

### Tầng 4: Data Serving
- [ ] **ClickHouse**: Analytics database (port 8123)
- [ ] **Elasticsearch**: Search engine (port 9200)
- [ ] **Redis**: Caching layer (port 6379)
- [ ] **GraphQL/REST API**: Data access layer

### Tầng 5: Data Consumption
- [ ] **Apache Superset**: BI dashboards (port 8088)
- [ ] **Metabase**: Analytics dashboards (port 3000)
- [ ] **Grafana**: Metrics visualization (port 3000)
- [ ] **Jupyter Notebook**: Interactive data science (port 8888)
- [ ] **Streamlit**: Data apps (port 8501)
- [ ] **MLflow**: ML model serving (port 5000)

### Tầng 6: Monitoring & Governance
- [ ] **Great Expectations**: Data quality validation
- [ ] **Apache Atlas**: Metadata catalog (port 21000)
- [ ] **DataHub**: Modern data catalog (port 9002)
- [ ] **Prometheus**: Metrics collection (port 9090)
- [ ] **Grafana**: Infrastructure monitoring (port 3000)
- [ ] **Apache Ranger**: Access control (optional)

---

## 📚 Learning Resources

- **Kafka**: https://kafka.apache.org/intro
- **Spark**: https://spark.apache.org/docs
- **dbt**: https://docs.getdbt.com
- **Trino**: https://trino.io/docs
- **ClickHouse**: https://clickhouse.com/docs
