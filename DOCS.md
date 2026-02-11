# 📚 Nexus Data Platform - Complete Documentation

**Last Updated**: February 11, 2026  
**Status**: ✅ Production Ready | Docker + Kubernetes

> This document consolidates all technical documentation.  
> **Navigation:** [README.md](./README.md) (overview) | [DOCS.md](./DOCS.md) (you are here) | [k8s/README.md](./k8s/README.md) (Kubernetes)

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture](#architecture)
3. [Setup Complete](#setup-complete)
4. [Project Structure (Monorepo)](#project-structure-monorepo)
5. [Technology Stack](#technology-stack)
6. [Quick Reference](#quick-reference)
7. [Implementation Guide](#implementation-guide)
8. [Troubleshooting](#troubleshooting)

---

<a id="quick-start"></a>
## 🚀 Quick Start

### Docker Compose (5 minutes)

```bash
cd /workspaces/Nexus-Data-Platform/infra/docker-stack
docker-compose up -d
./health-check.sh
```

**Access Services:**
| Service | URL | Credentials |
|---------|-----|-------------|
| Airflow | http://localhost:8888 | admin / admin |
| MinIO Console | http://localhost:9001 | minioadmin / minioadmin123 |
| ClickHouse | http://localhost:8123 | - |
| FastAPI Docs | http://localhost:8000/docs | - |
| Superset | http://localhost:8088 | admin / admin123 |

### Kubernetes (local)

```bash
# Build images
docker build -t nexus-api:local -f apps/api/Dockerfile .
docker build -t nexus-frontend:local --build-arg VITE_API_URL=http://localhost:8000 -f apps/frontend/Dockerfile .

# Load to kind/minikube
kind load docker-image nexus-api:local --name nexus-data-platform
kind load docker-image nexus-frontend:local --name nexus-data-platform

# Deploy
kubectl apply -f k8s/stack.yaml
kubectl -n nexus-data-platform get pods
```

### Frontend & API (Local Dev)

```bash
# Frontend
npm install
npm run frontend:dev  # http://localhost:3000

# API
pip install -r apps/api/requirements.txt
cd apps/api && python main.py  # http://localhost:8000
```

---

<a id="architecture"></a>
## 📐 Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA PLATFORM ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐             │
│  │ DATA SOURCES │────▶│  INGESTION   │────▶│   STORAGE    │             │
│  │              │     │              │     │              │             │
│  │ • APIs       │     │ • Kafka      │     │ • MinIO      │             │
│  │ • Databases  │     │ • Airflow    │     │ • Delta Lake │             │
│  │ • Files      │     │ • Logstash   │     │              │             │
│  │ • Streams    │     │              │     │              │             │
│  └──────────────┘     └──────────────┘     └──────────────┘             │
│                                                      ▼                   │
│                                            ┌──────────────────┐         │
│                                            │   PROCESSING     │         │
│                                            │                  │         │
│                                            │ • Spark          │         │
│                                            │ • Flink          │         │
│                                            │ • Trino          │         │
│                                            │ • dbt            │         │
│                                            └──────────────────┘         │
│                                                      ▼                   │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │  SERVING LAYER                                           │          │
│  │  • ClickHouse (Analytics)                               │          │
│  │  • Elasticsearch (Search)                               │          │
│  │  • Redis (Cache)                                        │          │
│  │  • FastAPI / GraphQL                                    │          │
│  └──────────────────────────────────────────────────────────┘          │
│                                                      ▼                   │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │  CONSUMPTION                                             │          │
│  │  • Superset BI Dashboard                                │          │
│  │  • React UI                                             │          │
│  │  • Custom Applications                                  │          │
│  └──────────────────────────────────────────────────────────┘          │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

### Deployment Options

```bash
# Docker Compose
cd infra/docker-stack && docker-compose up -d

# Kubernetes (local)
kubectl apply -f k8s/stack.yaml
```

---

<a id="setup-complete"></a>
## ⚡ Setup Complete - Full Instructions

### 1. Check Service Status

```bash
cd /workspaces/Nexus-Data-Platform/infra/docker-stack
./health-check.sh

# Expected output:
# ✅ ClickHouse is OK
# ✅ Elasticsearch is OK
# ✅ Kafka is OK
```

### 2. Working with Airflow

**View DAG:**
```bash
# DAG location: pipelines/airflow/dags/tourism_events_pipeline.py
# Access UI: http://localhost:8888/dags/tourism_events_pipeline

# View DAGs
docker exec nexus-airflow-webserver airflow dags list

# Trigger DAG
docker exec nexus-airflow-scheduler airflow dags trigger tourism_events_pipeline

# View logs
docker exec nexus-airflow-scheduler airflow tasks logs tourism_events_pipeline extract_tourism_data $(date +%Y-%m-%d)
```

**DAG Tasks:**
1. **extract_tourism_data** - Extract from APIs
2. **validate_data_quality** - Data quality checks
3. **upload_to_minio** - Upload to object storage
4. **trigger_spark_processing** - Process data
5. **update_data_catalog** - Metadata management
6. **send_notification** - Pipeline completion

### 3. Spark Jobs

```bash
# Local mode
python /workspaces/Nexus-Data-Platform/jobs/spark/tourism_processing.py

# Or submit to Spark cluster
spark-submit \
  --master spark://spark-master:7077 \
  --executor-memory 4g \
  tourism_processing.py

# Check results in ClickHouse
docker exec nexus-clickhouse clickhouse-client --query "
SELECT region, event_type, count() as cnt, sum(amount) as total
FROM analytics.events
GROUP BY region, event_type
LIMIT 10
"
```

### 4. FastAPI

**Install Dependencies:**
```bash
pip install -r /workspaces/Nexus-Data-Platform/apps/api/requirements.txt
```

**Start Server:**
```bash
cd /workspaces/Nexus-Data-Platform/apps/api
python main.py

# Or with Uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Test Endpoints:**
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

**Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 5. Kafka

**Create Topic:**
```bash
docker exec nexus-kafka kafka-topics.sh \
  --bootstrap-server kafka:9092 \
  --create \
  --topic tourism_events \
  --partitions 3 \
  --replication-factor 1
```

**Produce Message:**
```bash
docker exec -it nexus-kafka kafka-console-producer.sh \
  --bootstrap-server kafka:9092 \
  --topic tourism_events

# Type JSON message:
{"user_id": 101, "event_type": "booking", "amount": 999.99, "region": "VN"}
```

**Consume Message:**
```bash
docker exec -it nexus-kafka kafka-console-consumer.sh \
  --bootstrap-server kafka:9092 \
  --topic tourism_events \
  --from-beginning
```

### 6. MinIO - Object Storage

**Create Bucket:**
```bash
aws s3 mb s3://data-lake \
  --endpoint-url http://localhost:9000 \
  --region us-east-1
```

**Upload File:**
```bash
aws s3 cp /tmp/data.json s3://data-lake/raw/ \
  --endpoint-url http://localhost:9000
```

**List Files:**
```bash
aws s3 ls s3://data-lake/ \
  --endpoint-url http://localhost:9000 \
  --recursive
```

### 7. ClickHouse

**Connect CLI:**
```bash
docker exec -it nexus-clickhouse clickhouse-client

# Or HTTP
curl 'http://localhost:8123/?query=SELECT%20version()'
```

**Sample Queries:**
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

### 8. Elasticsearch

**Create Index:**
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

**Index Document:**
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

**Search:**
```bash
curl http://localhost:9200/tourism_events/_search \
  -H "Content-Type: application/json" \
  -d '{"query": {"match": {"event_type": "booking"}}}'
```

### 9. Redis Cache

**Connect CLI:**
```bash
redis-cli -h localhost -a redis123
```

**Basic Commands:**
```bash
SET key:name "value"
GET key:name
SETEX cache:user:101 3600 "user_data_json"
KEYS *
DEL cache:user:101
INFO stats
```

---

<a id="project-structure-monorepo"></a>
## 🗂️ Project Structure (Monorepo)

```
nexus-data-platform/
├── apps/                          # Applications
│   ├── frontend/                  # React UI
│   │   ├── src/
│   │   │   ├── components/        # React components
│   │   │   ├── services/          # API clients
│   │   │   └── App.tsx
│   │   ├── Dockerfile
│   │   ├── nginx.conf
│   │   ├── package.json
│   │   └── vite.config.ts
│   └── api/                       # FastAPI backend
│       ├── main.py                # REST endpoints
│       ├── Dockerfile
│       └── requirements.txt
│
├── pipelines/airflow/             # Orchestration
│   └── dags/
│       └── tourism_events_pipeline.py
│
├── jobs/spark/                    # Data processing
│   └── tourism_processing.py
│
├── infra/docker-stack/            # Infrastructure
│   ├── docker-compose.yml         # 10 services
│   ├── health-check.sh
│   ├── clickhouse/init.sql
│   └── trino/config.properties
│
├── k8s/                           # Kubernetes
│   ├── stack.yaml                 # Full K8s manifests
│   └── README.md
│
├── packages/shared/               # Shared packages
│   ├── types.ts                   # TypeScript types
│   ├── schemas/                   # Data contracts
│   │   ├── event.schema.json
│   │   ├── event.avsc
│   │   ├── event.parquet.json
│   │   └── tour.schema.json
│   └── package.json
│
├── configs/                       # Config templates
│   ├── frontend.env.example
│   └── api.env.example
│
├── tests/                         # Test suites
│   ├── api/test_health.py
│   ├── airflow/test_dag_import.py
│   └── spark/test_schema_contracts.py
│
├── .github/workflows/             # CI/CD
│   └── ci.yml
│
├── package.json                   # Root workspace
├── pytest.ini                     # Test config
└── README.md                      # Overview
```

### Key Directories

**apps/frontend/** - React UI Application
- Custom components with Recharts visualization
- API client service for FastAPI integration
- Vite build system with TypeScript

**apps/api/** - FastAPI Backend
- 12+ REST endpoints for data access
- Redis caching layer (2-hour TTL)
- Environment-driven configuration

**pipelines/airflow/** - Orchestration
- tourism_events_pipeline.py: 6-task DAG
- Extract → Validate → Upload → Process → Catalog → Notify

**jobs/spark/** - Data Processing
- Loads shared event schema from packages/shared/
- Processes tourism events
- Generates ML recommendations

**packages/shared/** - Shared Contracts
- event.schema.json (JSON Schema)
- event.avsc (Avro format)
- tour.schema.json (Tour data contract)
- types.ts (TypeScript interfaces)

**infra/docker-stack/** - Infrastructure
- 10 services: Kafka, MinIO, ClickHouse, PostgreSQL, etc.
- Health checks included
- Docker Compose configuration

---

<a id="technology-stack"></a>
## 🔄 Technology Stack

### Data Ingestion
- **Kafka** (7.5.0) - Event streaming, 1M+ events/sec
- **Airflow** (2.7.0) - Orchestration, scheduling
- **PostgreSQL** (15) - Metadata storage

### Data Storage  
- **MinIO** (latest) - S3-compatible object storage
- **ClickHouse** (latest) - Analytics database (100-1000x faster)
- **Redis** (7-alpine) - In-memory cache

### Data Processing
- **Spark** (3.5.0) - Batch processing, Spark SQL
- **Trino** (latest) - SQL query engine across sources

### Search & Analytics
- **Elasticsearch** (8.10.0) - Full-text search, logging
- **ClickHouse** - OLAP analytics, sub-second queries

### API & Frontend
- **FastAPI** (0.104.1) - REST API, automatic docs
- **React** (19.2.4) - Modern UI
- **Recharts** (3.7.0) - Data visualization

### Deployment
- **Docker** - Containerization
- **Docker Compose** - Local orchestration
- **Kubernetes** - Production ready manifests

### Quality & Testing
- **pytest** (7.4.3) - Python testing
- **Great Expectations** - Data quality checks
- **GitHub Actions** - CI/CD pipeline

---

<a id="quick-reference"></a>
## 📋 Quick Reference

### Docker Compose Commands

```bash
# Start all services
docker-compose up -d

# View status
docker-compose ps

# View logs
docker-compose logs -f <service>

# Stop all
docker-compose down

# Restart service
docker-compose restart <service>

# Execute command in container
docker exec <container> <command>
```

### Kubernetes Commands

```bash
# Apply manifests
kubectl apply -f k8s/stack.yaml

# Check pods
kubectl -n nexus-data-platform get pods

# Port-forward service
kubectl -n nexus-data-platform port-forward svc/<service> <local>:<remote>

# View logs
kubectl -n nexus-data-platform logs <pod>

# Delete manifests
kubectl delete -f k8s/stack.yaml
```

### Development Commands

```bash
# Frontend dev
npm run frontend:dev

# Frontend build
npm run frontend:build

# API dev
cd apps/api && python main.py

# Run tests
pytest

# Verify monorepo
./verify-monorepo.sh

# Health check
./check-platform.sh
```

### Data Operations

**Kafka:**
```bash
# List topics
docker exec kafka kafka-topics.sh --bootstrap-server kafka:9092 --list

# Create topic
docker exec kafka kafka-topics.sh --bootstrap-server kafka:9092 \
  --create --topic <name> --partitions 3 --replication-factor 1

# Describe topic
docker exec kafka kafka-topics.sh --bootstrap-server kafka:9092 \
  --describe --topic <name>
```

**ClickHouse:**
```bash
# Connect
docker exec -it clickhouse clickhouse-client

# Query
docker exec clickhouse clickhouse-client --query "SELECT * FROM analytics.events LIMIT 10"

# Backup
docker exec clickhouse clickhouse-client --query "BACKUP TO '/tmp/backup'"
```

**MinIO:**
```bash
# Set up CLI
aws configure --profile minio
# Access Key: minioadmin
# Secret Key: minioadmin123

# List buckets
aws s3 ls --endpoint-url http://localhost:9000 --profile minio

# Upload file
aws s3 cp file.txt s3://bucket/ --endpoint-url http://localhost:9000 --profile minio
```

---

<a id="implementation-guide"></a>
## 🛠️ Implementation Guide

### Step 1: Deploy Infrastructure

```bash
# Navigate to docker stack
cd infra/docker-stack

# Start services
docker-compose up -d

# Verify all services are running
docker-compose ps

# Check health
./health-check.sh
```

**Expected Services (10 total):**
- ✅ Zookeeper
- ✅ Kafka
- ✅ MinIO
- ✅ Trino
- ✅ ClickHouse
- ✅ Elasticsearch
- ✅ Redis
- ✅ PostgreSQL
- ✅ Airflow Webserver
- ✅ Airflow Scheduler
- ✅ Superset

### Step 2: Check Airflow DAG

```bash
# View DAG in UI
# http://localhost:8888/dags/tourism_events_pipeline

# View DAG file
cat pipelines/airflow/dags/tourism_events_pipeline.py

# Trigger DAG
docker exec nexus-airflow-scheduler \
  airflow dags trigger tourism_events_pipeline
```

### Step 3: Run Spark Job

```bash
# Install PySpark dependencies
pip install pyspark==3.5.0

# Run job
python jobs/spark/tourism_processing.py

# Check results
docker exec nexus-clickhouse clickhouse-client --query \
  "SELECT * FROM analytics.events LIMIT 5"
```

### Step 4: Deploy API

```bash
# Install dependencies
pip install -r apps/api/requirements.txt

# Start API
cd apps/api && python main.py

# Test API
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/tours
```

### Step 5: Deploy Frontend

```bash
# Install dependencies
npm install

# Start dev server
npm run frontend:dev

# Opens http://localhost:3000
```

### Step 6: Create Dashboards

```bash
# Access Superset
# http://localhost:8088
# Login: admin / admin123

# Create database connection to ClickHouse
# Host: clickhouse
# Port: 9000

# Create dashboard with analytics.events table
```

---

<a id="troubleshooting"></a>
## 🔧 Troubleshooting

### Docker Issues

**Port Already in Use:**
```bash
lsof -i :8888  # Find process
kill -9 <PID>  # Kill process
```

**Service Not Starting:**
```bash
# Check logs
docker-compose logs <service>

# Restart service
docker-compose restart <service>

# View detailed logs
docker-compose logs -f --tail 100 <service>
```

**Out of Memory:**
```bash
# Increase Docker memory in Desktop settings (Mac/Windows)
# Or in daemon.json (Linux)
```

### Kafka Issues

**Producer Not Sending:**
```bash
# Check broker is running
docker exec kafka kafka-broker-api-versions.sh --bootstrap-server kafka:9092

# Check topics
docker exec kafka kafka-topics.sh --bootstrap-server kafka:9092 --list
```

**Consumer Lag:**
```bash
# Add more partitions
docker exec kafka kafka-topics.sh --bootstrap-server kafka:9092 \
  --alter --topic tourism_events --partitions 6

# Scale consumers horizontally
```

### Spark Issues

**Out of Memory:**
```bash
# Increase executor memory
spark-submit \
  --executor-memory 4g \
  --driver-memory 2g \
  jobs/spark/tourism_processing.py
```

**Slow Queries:**
```bash
# Add indexes in ClickHouse
ALTER TABLE analytics.events ADD INDEX user_idx (user_id) TYPE hash

# Repartition data
df.repartition(10).write.mode('overwrite').parquet('path')
```

### ClickHouse Issues

**Insert Slow:**
```bash
# Batch inserts
INSERT INTO analytics.events
SELECT ... WHERE ...

# Use async_insert
SET async_insert = 1
```

**SELECT Timeout:**
```bash
# Add index
ALTER TABLE analytics.events ADD INDEX ts_idx (timestamp) TYPE hash

# Reduce time range
SELECT * FROM analytics.events WHERE timestamp > now() - INTERVAL 7 DAY
```

### API Issues

**Redis Connection Error:**
```bash
# Check Redis is running
docker-compose logs redis

# Test connection
redis-cli -h localhost -a redis123 ping
# Expected: PONG
```

**Database Connection Error:**
```bash
# Check PostgreSQL
docker-compose logs postgres

# Test connection
psql -h localhost -U admin -d nexus_data
```

---

## 📚 Additional Resources

- **[Kafka Documentation](https://kafka.apache.org/documentation/)**
- **[Spark Documentation](https://spark.apache.org/docs/latest/)**
- **[ClickHouse Documentation](https://clickhouse.com/docs)**
- **[Airflow Documentation](https://airflow.apache.org/docs/)**
- **[FastAPI Documentation](https://fastapi.tiangolo.com/)**
- **[Docker Documentation](https://docs.docker.com/)**
- **[Kubernetes Documentation](https://kubernetes.io/docs/)**

---

## ✅ Deployment Checklist

- [ ] All Docker services running
- [ ] Airflow DAG triggered successfully
- [ ] Spark job processed data
- [ ] ClickHouse tables populated
- [ ] FastAPI endpoints responding
- [ ] React frontend loads
- [ ] Redis cache working
- [ ] Superset dashboard created
- [ ] Data quality checks passing
- [ ] Monitoring alerts configured

---

**Made with ❤️ for data engineering** • 🚀 **Deploy. Process. Analyze.**
