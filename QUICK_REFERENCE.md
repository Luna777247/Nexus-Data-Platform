# 📋 Data Platform Setup - Quick Reference & Checklist

## 🎯 PROJECT OVERVIEW

**Nexus Data Platform** = End-to-end data platform cho tourism industry

```
┌─────────────────────────────────────────────────────────────────┐
│ ARCHITECTURE LAYERS                                             │
├─────────────────────────────────────────────────────────────────┤
│ 1. INGESTION: Kafka, Airflow, NiFi                             │
│ 2. STORAGE:   MinIO, Delta Lake, HDFS                          │
│ 3. PROCESSING: Spark, Flink, dbt                               │
│ 4. SERVING:   ClickHouse, Elasticsearch, Redis, GraphQL        │
│ 5. CONSUMPTION: Superset, Metabase, Custom UI                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Quick Start (5 Minutes)

```bash
# 1. Clone & navigate
cd /workspaces/Nexus-Data-Platform

# 2. Start full stack
cd docker-stack
docker-compose up -d

# 3. Verify services
docker-compose ps

# 4. Access tools
Airflow:       http://localhost:8888
MinIO:         http://localhost:9001 (minioadmin/minioadmin)
ClickHouse:    http://localhost:8123
Elasticsearch: http://localhost:9200
Superset:      http://localhost:8088
```

---

## 📦 SETUP CHECKLIST

### Phase 1: Environment Setup
- [ ] Docker & Docker Compose installed
- [ ] Python 3.11+ installed
- [ ] Dependencies installed: `npm install`
- [ ] Environment variables configured in `.env.local`

### Phase 2: Data Ingestion
- [ ] Kafka cluster running
- [ ] Airflow webserver & scheduler running
- [ ] First DAG deployed
- [ ] Test event producer created
- [ ] Data validation rules defined

### Phase 3: Data Storage
- [ ] MinIO/S3 bucket created
- [ ] Delta Lake configured
- [ ] Sample data loaded
- [ ] Partitioning strategy defined
- [ ] Backup strategy implemented

### Phase 4: Data Processing
- [ ] Spark cluster configured
- [ ] First Spark job runs successfully
- [ ] dbt models created
- [ ] Data tests passing
- [ ] Processing DAGs scheduled

### Phase 5: Data Serving
- [ ] ClickHouse tables created
- [ ] Sample queries working
- [ ] Elasticsearch indexes created
- [ ] Redis cache configured
- [ ] Query optimization tuned

### Phase 6: API & Frontend
- [ ] FastAPI endpoints created
- [ ] GraphQL schema defined
- [ ] React dashboard updated
- [ ] API documentation generated
- [ ] Authentication configured

### Phase 7: Monitoring & Quality
- [ ] Great Expectations rules defined
- [ ] Data quality tests active
- [ ] Dashboards created in Superset
- [ ] Alerts configured
- [ ] Performance metrics tracked

### Phase 8: Production Readiness
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Security audit done
- [ ] Scalability tested
- [ ] Disaster recovery plan ready

---

## 🔧 SERVICE STATUS CHECK

```bash
#!/bin/bash
# save as: health-check.sh

echo "=== DATA PLATFORM HEALTH CHECK ==="

# Kafka
echo "1. Kafka:"
docker exec kafka kafka-topics.sh --bootstrap-server kafka:9092 --list || echo "❌"

# MinIO
echo "2. MinIO:"
curl -s http://localhost:9000/minio/health/live > /dev/null && echo "✅" || echo "❌"

# ClickHouse
echo "3. ClickHouse:"
curl -s http://localhost:8123/ping > /dev/null && echo "✅" || echo "❌"

# Elasticsearch
echo "4. Elasticsearch:"
curl -s http://localhost:9200/_cluster/health | grep -q green && echo "✅" || echo "❌"

# Redis
echo "5. Redis:"
redis-cli -h localhost ping | grep -q PONG && echo "✅" || echo "❌"

# Airflow
echo "6. Airflow:"
curl -s http://localhost:8888/health | grep -q healthy && echo "✅" || echo "❌"

echo "=== CHECK COMPLETE ==="
```

---

## 🚀 KEY COMMANDS

### Kafka
```bash
# Create topic
docker exec kafka kafka-topics.sh --bootstrap-server kafka:9092 \
  --create --topic events --partitions 3 --replication-factor 1

# Produce message
docker exec kafka kafka-console-producer.sh --bootstrap-server kafka:9092 --topic events

# Consume message
docker exec kafka kafka-console-consumer.sh --bootstrap-server kafka:9092 \
  --topic events --from-beginning
```

### MinIO
```bash
# Create bucket
aws s3 mb s3://data-lake --endpoint-url http://localhost:9000 \
  --region us-east-1

# Upload file
aws s3 cp /tmp/data.parquet s3://data-lake/raw/ --endpoint-url http://localhost:9000

# List files
aws s3 ls s3://data-lake --endpoint-url http://localhost:9000 --recursive
```

### Spark
```bash
# Submit job
spark-submit \
  --master local[4] \
  --executor-memory 2g \
  --driver-memory 1g \
  spark_processing.py

# Run in cluster
spark-submit \
  --master spark://localhost:7077 \
  --executor-memory 4g \
  spark_processing.py
```

### ClickHouse
```bash
# Connect to CLI
clickhouse-client --host localhost --port 9000

# Execute query
clickhouse-client --host localhost --query "SELECT version()"
```

### Airflow
```bash
# List DAGs
airflow dags list

# Trigger DAG
airflow dags trigger data_ingestion_pipeline

# View logs
airflow tasks logs data_ingestion_pipeline extract_data 2024-01-01
```

---

## 📊 SAMPLE DATA FLOW

### Scenario: Tourism Event Pipeline

```
1. USER INTERACTION (Frontend)
   └─ User views tour, clicks "Book" button
   └─ Event: {user_id, tour_id, event_type: "purchase", amount: 999.99}

2. INGESTION (Kafka)
   └─ Event sent to Kafka topic: "tourism_events"
   └─ Producers: Mobile app, Web app, API calls

3. ORCHESTRATION (Airflow)
   └─ Daily DAG: "tour_booking_pipeline"
   └─ Time: 02:00 UTC every day
   └─ Tasks:
      ├─ Extract events from Kafka
      ├─ Validate data quality
      ├─ Upload to MinIO
      └─ Trigger Spark processing

4. PROCESSING (Spark)
   └─ Read raw events from MinIO
   └─ Transformations:
      ├─ Deduplicate events
      ├─ Enrich with user/tour data
      ├─ Calculate metrics by region/tour_type
      ├─ Generate recommendations (hybrid filter)
   └─ Write to ClickHouse

5. ANALYTICS (ClickHouse)
   └─ Aggregate tables:
      ├─ daily_bookings (sum by region, tour_type)
      ├─ user_stats (avg booking value, frequency)
      ├─ recommendation_scores (popularity, ratings)

6. SERVING (API)
   └─ FastAPI endpoints:
      ├─ GET /tours - list all tours (cached in Redis)
      ├─ GET /analytics/region-stats - region breakdown
      ├─ POST /recommendations - get user recommendations
   └─ GraphQL queries:
      ├─ userBookings
      ├─ regionMetrics
      ├─ popularTours

7. CONSUMPTION (Frontend)
   └─ React Dashboard shows:
      ├─ Real-time bookings worldwide
      ├─ Regional revenue breakdown
      ├─ Top recommendations for user
      ├─ Data quality metrics
```

---

## 🎓 LEARNING PATH

### Week 1-2: Fundamentals
- [ ] Understand ETL/ELT concepts
- [ ] Learn Kafka basics (producers, consumers, topics)
- [ ] Study Spark architecture & DataFrame API
- [ ] Read SQL fundamentals

### Week 3-4: Hands-on Basics
- [ ] Deploy Docker stack
- [ ] Write first Kafka producer
- [ ] Create Spark job
- [ ] Query ClickHouse

### Week 5-6: Integration
- [ ] Create Airflow DAG
- [ ] Connect Kafka → Spark → ClickHouse
- [ ] Build simple API endpoint
- [ ] Create dashboard

### Week 7-8: Advanced
- [ ] Optimize Spark queries
- [ ] Implement data quality tests
- [ ] Add monitoring & alerting
- [ ] Scale to larger datasets

### Week 9-10: Production Ready
- [ ] Performance tuning
- [ ] Security hardening
- [ ] Documentation
- [ ] Runbooks for operations

---

## 📚 DOCUMENTATION STRUCTURE

```
/workspaces/Nexus-Data-Platform/
├── README.md                           (Main overview)
├── DATA_PLATFORM_STACK.md             ✅ (Architecture & technologies)
├── IMPLEMENTATION_GUIDE.md            ✅ (Step-by-step setup)
├── TECHNOLOGY_COMPARISON.md           ✅ (Tech choices)
├── QUICK_REFERENCE.md                 ✅ (This file)
├── docker-stack/
│   ├── docker-compose.yml
│   ├── trino/config.properties
│   └── health-check.sh
├── airflow/dags/
│   ├── data_ingestion.py
│   ├── spark_processing.py
│   └── data_validation.py
├── spark/
│   ├── processing.py
│   └── recommendations.py
├── dbt/
│   ├── models/staging/
│   ├── models/marts/
│   └── macros/
├── api/
│   ├── main.py                        (FastAPI)
│   ├── graphql/schema.py
│   └── requirements.txt
└── web/                               (React UI)
```

---

## 🔐 SECURITY CHECKLIST

- [ ] Change default passwords (MinIO, Airflow, etc.)
- [ ] Setup authentication (JWT, OAuth2)
- [ ] Enable SSL/TLS for all services
- [ ] Configure firewall rules
- [ ] Setup encrypted secrets management
- [ ] Enable audit logging
- [ ] Regular backups implemented
- [ ] Network policies configured

---

## 💡 TROUBLESHOOTING GUIDE

### Kafka Issues
```
Problem: Producer not sending messages
Solution: Check broker is running, verify bootstrap servers

Problem: Consumer lag increasing
Solution: Add more partitions, scale consumers
```

### Spark Issues
```
Problem: Out of memory error
Solution: Increase executor memory, reduce partition size

Problem: Slow queries
Solution: Add indexes, repartition data, check executor count
```

### ClickHouse Issues
```
Problem: INSERT is slow
Solution: Batch inserts, use async_insert, check disk I/O

Problem: SELECT timeout
Solution: Add index, reduce time range, enable cache
```

---

## 🎯 RECOMMENDED TECH STACK (Nexus Use Case)

```
Architecture:
┌─────────────────────────────────────────────────┐
│ Tourism Events (API, Mobile, Web)              │
└──────────────────┬──────────────────────────────┘
                   │
┌─────────────────────────────────────────────────┐
│ Kafka Cluster (3 nodes)                        │
│ - Topic: tourism_events (12 partitions)        │
└──────────────────┬──────────────────────────────┘
                   │
┌─────────────────────────────────────────────────┐
│ Airflow (Orchestration)                        │
│ - Daily ingestion DAGs                         │
└──────────────────┬──────────────────────────────┘
                   │ Raw Data
┌─────────────────────────────────────────────────┐
│ MinIO/S3 (Data Lake)                           │
│ - s3://data-lake/raw/                          │
└──────────────────┬──────────────────────────────┘
                   │
┌─────────────────────────────────────────────────┐
│ Delta Lake (Features)                          │
│ - ACID transactions                            │
└──────────────────┬──────────────────────────────┘
                   │
┌─────────────────────────────────────────────────┐
│ Spark Cluster (Batch Processing)               │
│ - dbt models (transformation)                  │
│ - Hybrid recommendations (Collab Filtering)    │
└──────────────────┬──────────────────────────────┘
                   │ Processed Data
        ┌──────────┴──────────┐
        │                     │
┌──────────────────┐  ┌──────────────────┐
│ ClickHouse       │  │ Elasticsearch    │
│ - Fact tables    │  │ - Search index   │
│ - Fast analytics │  │ - Full-text      │
└────────┬─────────┘  └────────┬─────────┘
         │                     │
         └──────────┬──────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
    ┌─────────────┐      ┌──────────────┐
    │ Redis Cache │      │ GraphQL API  │
    │ (2hr TTL)   │      │ (FastAPI)    │
    └─────────────┘      └──────────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
              ┌─────────────┐      ┌─────────────┐
              │ Superset    │      │ React App   │
              │ BI Dashboard│      │ UI/Frontend │
              └─────────────┘      └─────────────┘
```

---

## 📞 Support & Resources

| Issue Type | Resource |
|-----------|----------|
| Kafka problems | https://kafka.apache.org/documentation |
| Spark errors | https://spark.apache.org/docs/latest/ |
| ClickHouse queries | https://clickhouse.com/docs |
| Airflow DAGs | https://airflow.apache.org/docs |
| dbt models | https://docs.getdbt.com |

---

## ✅ FINAL CHECKLIST

Before going production:

- [ ] All services deployed & running
- [ ] Data validation tests passing
- [ ] Performance benchmarks met
- [ ] Documentation updated
- [ ] Monitoring & alerting active
- [ ] Backup & recovery tested
- [ ] Security audit completed
- [ ] Team training done
- [ ] Runbooks created
- [ ] Go-live plan agreed

---

**Ready to build? Start with `docker-compose up -d` and explore!** 🚀
