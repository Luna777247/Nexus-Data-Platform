# 🚀 Quick Start - Production Architecture

## TL;DR

```bash
# 1. Start production stack
cd infra/docker-stack
docker-compose -f docker-compose-production.yml up -d

# 2. Create DLQ topics
./scripts/create-dlq-topics.sh

# 3. Trigger production ETL
airflow dags trigger production_medallion_etl

# 4. Monitor
open http://localhost:9090  # Prometheus
open http://localhost:3000  # Grafana (admin/admin123)
```

## 📦 What's New

### Separated Spark Clusters
```
Spark Streaming: localhost:8080 (real-time)
Spark Batch:     localhost:8082 (ETL)
```

### Governance Stack
- **Data Quality:** Great Expectations integration
- **Lineage:** OpenMetadata (localhost:8585)
- **DLQ:** 3 error recovery topics

### Monitoring
- **Prometheus:** localhost:9090
- **Grafana:** localhost:3000

## 🎯 Key Commands

### Check Cluster Status
```bash
# Spark Streaming
curl http://localhost:8080/json/ | jq '.workers'

# Spark Batch
curl http://localhost:8082/json/ | jq '.workers'

# Kafka topics
docker exec nexus-kafka-1 kafka-topics --list \
  --bootstrap-server localhost:9092
```

### Run Enhanced ETL
```bash
spark-submit \
  --master spark://spark-batch-master:7077 \
  jobs/spark/bronze_to_silver_enhanced.py \
  --date $(date +%Y-%m-%d) \
  --enable-quality-checks \
  --enable-lineage-tracking \
  --enable-dlq
```

### View Metrics
```bash
# Quality score
curl -s http://localhost:9090/api/v1/query?query=data_quality_score | jq

# Job duration
curl -s http://localhost:9090/api/v1/query?query=job_duration_seconds | jq

# Kafka lag
curl -s http://localhost:9090/api/v1/query?query=kafka_consumer_lag_messages | jq
```

## 📊 Dashboards

### Grafana Dashboards
1. **Platform Overview** - System health
2. **Data Quality** - Quality scores by layer
3. **Performance** - Job duration, throughput
4. **Kafka Monitoring** - Consumer lag

### Prometheus Queries
```promql
# 95th percentile job duration
histogram_quantile(0.95, job_duration_seconds)

# Records processed rate
rate(records_processed_total[5m])

# Quality score by layer
avg(data_quality_score) by (layer)
```

## 🔧 Troubleshooting

### No metrics in Prometheus?
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health!="up")'
```

### Spark job failed?
```bash
# Check Spark logs
docker logs nexus-spark-batch-master

# Check DLQ for errors
docker exec nexus-kafka-1 kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic dlq_processing_errors \
  --from-beginning
```

### Quality checks failing?
```bash
# Check quality report in job logs
docker logs <spark-job-container> | grep "DATA QUALITY REPORT"
```

## 📚 Full Documentation

- [ARCHITECTURE_IMPROVEMENTS.md](ARCHITECTURE_IMPROVEMENTS.md) - Complete guide
- [CODE_CHANGES_ARCHITECTURE.md](CODE_CHANGES_ARCHITECTURE.md) - Code changes summary
- [kien-truc](kien-truc) - Architecture diagram
- [luong-xu-ly](luong-xu-ly) - Processing flow

## ✅ Health Check

All green? ✓
```bash
# Run health check
./scripts/health-check-production.sh
```

Expected output:
```
✓ Kafka cluster healthy (3/3 brokers)
✓ Spark Streaming cluster (1 master, 2 workers)
✓ Spark Batch cluster (1 master, 2 workers)
✓ PostgreSQL (Iceberg) responding
✓ MinIO distributed (4/4 nodes)
✓ Prometheus scraping 8 targets
✓ Grafana accessible
✓ OpenMetadata API responding
```

---

**Need help?** Check [ARCHITECTURE_IMPROVEMENTS.md](ARCHITECTURE_IMPROVEMENTS.md) for detailed guide.
