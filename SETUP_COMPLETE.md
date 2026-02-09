# ⚡ Nexus Data Platform - Complete Setup Guide

## 📊 What's Deployed

```
├── Docker Stack (10 services)
├── Airflow DAG (Tourism Events Pipeline)
├── Spark Job (Data Processing)
└── FastAPI Endpoints (Data Serving)
```

---

## 🚀 Quick Start

### 1️⃣ Check Service Status

```bash
cd /workspaces/Nexus-Data-Platform/docker-stack
./health-check.sh

# Expected output:
# ✅ ClickHouse is OK
# ✅ Elasticsearch is OK
# ⚠️  (Some services may still be starting)
```

### 2️⃣ Access Services

Wait 2-3 minutes for all services to fully start, then access:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Airflow** | http://localhost:8888 | admin / admin |
| **MinIO Console** | http://localhost:9001 | minioadmin / minioadmin123 |
| **ClickHouse** | http://localhost:8123 | (HTTP API) |
| **Elasticsearch** | http://localhost:9200 | (HTTP API) |
| **Redis** | redis-cli -h localhost -a redis123 | - |
| **Superset** | http://localhost:8088 | admin / admin123 |
| **Kafka** | localhost:9092 | (Programmatic access) |

---

## 🔄 Working with Data Pipeline

### View Airflow DAG

```bash
# DAG file location
/workspaces/Nexus-Data-Platform/airflow/dags/tourism_events_pipeline.py

# Access UI
http://localhost:8888/dags/tourism_events_pipeline
```

**DAG Tasks:**
1. **extract_tourism_data** - Extract from APIs
2. **validate_data_quality** - Data quality checks
3. **upload_to_minio** - Upload to object storage
4. **trigger_spark_processing** - Process data
5. **update_data_catalog** - Metadata management
6. **send_notification** - Pipeline completion

### Trigger DAG Manually

```bash
cd /workspaces/Nexus-Data-Platform/docker-stack

# View dags
docker exec nexus-airflow-webserver airflow dags list

# Trigger DAG
docker exec nexus-airflow-scheduler airflow dags trigger tourism_events_pipeline

# View logs
docker exec nexus-airflow-scheduler airflow tasks logs tourism_events_pipeline extract_tourism_data $(date +%Y-%m-%d)
```

---

## 🔥 Running Spark Jobs

### 1. Copy Spark Job to Container

```bash
docker cp /workspaces/Nexus-Data-Platform/spark/tourism_processing.py \
  nexus-clickhouse:/spark_job.py
```

### 2. Submit Job

```bash
# Local mode
python /workspaces/Nexus-Data-Platform/spark/tourism_processing.py

# Or in production via Spark cluster:
# spark-submit \
#   --master spark://spark-master:7077 \
#   --executor-memory 4g \
#   tourism_processing.py
```

### 3. Monitor Output

Check ClickHouse for results:

```bash
docker exec nexus-clickhouse clickhouse-client --query "
SELECT 
    region, 
    event_type, 
    count() as cnt,
    sum(amount) as total
FROM analytics.events
GROUP BY region, event_type
LIMIT 10
"
```

---

## 🌐 Running FastAPI

### 1. Install Dependencies

```bash
pip install -r /workspaces/Nexus-Data-Platform/api/requirements.txt
```

### 2. Start API Server

```bash
cd /workspaces/Nexus-Data-Platform/api
python main.py

# Or with Uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Access API Documentation

```
http://localhost:8000/docs          # Interactive Swagger UI
http://localhost:8000/redoc         # ReDoc documentation
```

### 4. Test API Endpoints

```bash
# Get all tours
curl http://localhost:8000/api/v1/tours

# Get tours by region
curl "http://localhost:8000/api/v1/tours?region=VN"

# Get tour details
curl http://localhost:8000/api/v1/tours/t1

# Get regional statistics
curl http://localhost:8000/api/v1/analytics/regional-stats

# Get recommendations
curl "http://localhost:8000/api/v1/recommendations?user_id=101"

# Check health
curl http://localhost:8000/health
```

---

## 📝 Testing with Kafka

### 1. Create Kafka Topic

```bash
docker exec nexus-kafka kafka-topics.sh \
  --bootstrap-server kafka:9092 \
  --create \
  --topic tourism_events \
  --partitions 3 \
  --replication-factor 1
```

### 2. Produce Message

```bash
# Start producer
docker exec -it nexus-kafka kafka-console-producer.sh \
  --bootstrap-server kafka:9092 \
  --topic tourism_events

# Type message (JSON)
{"user_id": 101, "event_type": "booking", "amount": 999.99, "region": "VN"}
```

### 3. Consume Message

```bash
docker exec -it nexus-kafka kafka-console-consumer.sh \
  --bootstrap-server kafka:9092 \
  --topic tourism_events \
  --from-beginning
```

---

## 🗂️ MinIO - Object Storage

### 1. Create Bucket

```bash
# Using AWS CLI with MinIO endpoint
aws s3 mb s3://data-lake \
  --endpoint-url http://localhost:9000 \
  --region us-east-1

# Configure credentials
aws configure --profile minio
# Access Key: minioadmin
# Secret Key: minioadmin123
# Region: us-east-1
```

### 2. Upload File

```bash
aws s3 cp /tmp/data.json s3://data-lake/raw/ \
  --endpoint-url http://localhost:9000 \
  --profile minio
```

### 3. List Files

```bash
aws s3 ls s3://data-lake/ \
  --endpoint-url http://localhost:9000 \
  --profile minio \
  --recursive
```

---

## 📊 ClickHouse Queries

### 1. Connect to ClickHouse

```bash
# Using CLI
docker exec -it nexus-clickhouse clickhouse-client

# Or HTTP
curl 'http://localhost:8123/?query=SELECT%20version()'
```

### 2. Sample Queries

```sql
-- Check databases
SHOW DATABASES;

-- Check tables
SHOW TABLES IN analytics;

-- View schema
DESCRIBE analytics.events;

-- Query data
SELECT * FROM analytics.events LIMIT 10;

-- Aggregations
SELECT 
    region,
    count() as events,
    sum(amount) as total_revenue,
    avg(amount) as avg_amount
FROM analytics.events
GROUP BY region;
```

---

## 🔍 Elasticsearch / Search

### 1. Create Index

```bash
curl -X PUT http://localhost:9200/tourism_events \
  -H "Content-Type: application/json" \
  -d '{
    "mappings": {
      "properties": {
        "user_id": {"type": "integer"},
        "event_type": {"type": "keyword"},
        "amount": {"type": "float"},
        "region": {"type": "keyword"},
        "timestamp": {"type": "date"}
      }
    }
  }'
```

### 2. Index Document

```bash
curl -X POST http://localhost:9200/tourism_events/_doc \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 101,
    "event_type": "booking",
    "amount": 999.99,
    "region": "VN",
    "timestamp": "2024-02-09T10:00:00Z"
  }'
```

### 3. Search

```bash
# Search all bookings
curl http://localhost:9200/tourism_events/_search \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "match": {
        "event_type": "booking"
      }
    }
  }'
```

---

## 🎛️ Redis Cache Operations

### 1. Connect Redis CLI

```bash
redis-cli -h localhost -a redis123
```

### 2. Basic Commands

```bash
# Set key
SET key:name "value"

# Get key
GET key:name

# Set with expiry (3600 = 1 hour)
SETEX cache:user:101 3600 "user_data_json"

# Check keys
KEYS *

# Delete key
DEL cache:user:101

# Cache stats
INFO stats
```

---

## 🧪 Data Quality Checks

### Add Data Quality Rules

Edit `/workspaces/Nexus-Data-Platform/airflow/dags/tourism_events_pipeline.py`:

```python
def validate_data_quality():
    validations = [
        {'field': 'user_id', 'check': 'not_null'},
        {'field': 'amount', 'check': 'greater_than', 'value': 0},
        {'field': 'region', 'check': 'in_list', 'values': ['VN', 'SG', 'TH', 'ID']},
    ]
    # ... implement validations
```

---

## 🔧 Troubleshooting

### Port Already in Use

```bash
# Find process using port 8888
lsof -i :8888

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
```

### Service Not Starting

```bash
# Check logs
docker-compose -f docker-stack/docker-compose.yml logs <service_name>

# Restart service
docker-compose -f docker-stack/docker-compose.yml restart <service_name>
```

### Data Not Flowing

```bash
# Check Kafka topics
docker exec nexus-kafka kafka-topics.sh \
  --bootstrap-server kafka:9092 \
  --list

# Check Airflow logs
docker logs nexus-airflow-scheduler
docker logs nexus-airflow-webserver
```

---

## 📈 Next Steps

1. ✅ **Deploy Docker Stack** - DONE
2. ✅ **Test Services** - DONE
3. ✅ **Create DAG** - DONE
4. ✅ **Create Spark Job** - DONE
5. ✅ **Create API** - DONE
6. 🔄 **Configure BI Dashboard** (Superset)
7. 🔄 **Add Data Quality (Great Expectations)**
8. 🔄 **Setup Monitoring (Prometheus)**
9. 🔄 **Production Deployment**

---

## 📚 File Structure

```
/workspaces/Nexus-Data-Platform/
├── docker-stack/
│   ├── docker-compose.yml          ✅ 10 services
│   ├── clickhouse/init.sql
│   ├── trino/*.properties
│   └── health-check.sh
├── airflow/
│   └── dags/
│       └── tourism_events_pipeline.py  ✅ DAG with 6 tasks
├── spark/
│   └── tourism_processing.py       ✅ Spark job
├── api/
│   ├── main.py                     ✅ FastAPI endpoints
│   └── requirements.txt
└── [Documentation files]
```

---

## 📞 Support

For detailed documentation, see:
- `DATA_PLATFORM_STACK.md` - Architecture overview
- `IMPLEMENTATION_GUIDE.md` - Step-by-step setup
- `TECHNOLOGY_COMPARISON.md` - Tech choices
- `QUICK_REFERENCE.md` - Quick commands

🚀 **Ready to build a world-class data platform!**
