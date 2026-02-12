# Nexus Data Platform - Recommended Improvements Configuration

## 🎯 Mục Đích

Tệp này chứa các cấu hình khuyến nghị để cải tiến tính ổn định và hiệu suất của kiến trúc.

---

## 1. Health Checks Configuration

> **Lợi ích:** Phát hiện services bị down, kích hoạt tự động restart  
> **Impact:** +25-30% stability

### Template Health Check

```yaml
# Để thêm vào từng service trong docker-compose
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:PORT/health"]
  interval: 10s
  timeout: 5s
  retries: 3
  start_period: 30s
```

### Cấu Hình cụ thể cho mỗi service:

#### **Kafka Broker**
```yaml
kafka-1:
  healthcheck:
    test: 
      - CMD
      - kafka-broker-api-versions
      - --bootstrap-server=localhost:9092
    interval: 10s
    timeout: 5s
    retries: 5
    start_period: 30s
```

#### **Spark Master**
```yaml
spark-stream-master:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8080/json/"]
    interval: 15s
    timeout: 5s
    retries: 3
    start_period: 30s
```

#### **PostgreSQL**
```yaml
postgres-iceberg:
  healthcheck:
    test: 
      - CMD-SHELL
      - "pg_isready -U postgres"
    interval: 10s
    timeout: 5s
    retries: 5
    start_period: 10s
```

#### **Redis (if added)**
```yaml
redis:
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 5s
    retries: 3
```

#### **API (FastAPI)**
```yaml
api:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 10s
    timeout: 5s
    retries: 3
    start_period: 10s
```

---

## 2. Resource Limits Configuration

> **Lợi ích:** Ngăn OOM, stable performance  
> **Impact:** Prevents crashes, better resource management

### Memory Allocation Strategy

```yaml
# Tổng memory cần: ~30GB cho full platform
# Distribute based on workload requirements
```

### Service-by-Service Limits

#### **Kafka Cluster** (3 brokers)
```yaml
kafka-1:
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: "1"
      reservations:
        memory: 1.5G
        cpus: "0.5"

kafka-2:
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: "1"
      reservations:
        memory: 1.5G
        cpus: "0.5"

kafka-3:
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: "1"
      reservations:
        memory: 1.5G
        cpus: "0.5"
```

#### **Spark Streaming Cluster**
```yaml
spark-stream-master:
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: "2"
      reservations:
        memory: 1.5G
        cpus: "1"

spark-stream-worker-1:
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: "2"
      reservations:
        memory: 1.5G
        cpus: "1"

spark-stream-worker-2:
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: "2"
      reservations:
        memory: 1.5G
        cpus: "1"
```

#### **Spark Batch Cluster**
```yaml
spark-batch-master:
  deploy:
    resources:
      limits:
        memory: 4G
        cpus: "4"
      reservations:
        memory: 3G
        cpus: "2"

spark-batch-worker-1:
  deploy:
    resources:
      limits:
        memory: 4G
        cpus: "4"
      reservations:
        memory: 3G
        cpus: "2"

spark-batch-worker-2:
  deploy:
    resources:
      limits:
        memory: 4G
        cpus: "4"
      reservations:
        memory: 3G
        cpus: "2"
```

#### **PostgreSQL**
```yaml
postgres-iceberg:
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: "2"
      reservations:
        memory: 1.5G
        cpus: "1"
```

#### **MinIO Nodes**
```yaml
minio-1:
  deploy:
    resources:
      limits:
        memory: 1.5G
        cpus: "1"
      reservations:
        memory: 1G
        cpus: "0.5"

minio-2:
  deploy:
    resources:
      limits:
        memory: 1.5G
        cpus: "1"
      reservations:
        memory: 1G
        cpus: "0.5"

minio-3:
  deploy:
    resources:
      limits:
        memory: 1.5G
        cpus: "1"
      reservations:
        memory: 1G
        cpus: "0.5"

minio-4:
  deploy:
    resources:
      limits:
        memory: 1.5G
        cpus: "1"
      reservations:
        memory: 1G
        cpus: "0.5"
```

#### **Monitoring Stack**
```yaml
prometheus:
  deploy:
    resources:
      limits:
        memory: 1G
        cpus: "1"
      reservations:
        memory: 512M
        cpus: "0.5"

grafana:
  deploy:
    resources:
      limits:
        memory: 1G
        cpus: "1"
      reservations:
        memory: 512M
        cpus: "0.5"

kafka-exporter:
  deploy:
    resources:
      limits:
        memory: 512M
        cpus: "0.5"
      reservations:
        memory: 256M
        cpus: "0.25"
```

#### **Total Resource Budget**
```
Kafka:           6G limit (1.5G × 3 + 0.5G buffer)
Spark Streaming: 6G limit (2G × 3)
Spark Batch:     12G limit (4G × 3)
Storage:         6G limit (1.5G × 4 MinIO)
PostgreSQL:      2G limit
Monitoring:      2.5G limit
───────────────────────────
TOTAL:          ~35G limit, ~25G reserve
```

---

## 3. Prometheus Alert Rules

> **Lợi ích:** Proactive monitoring, early problem detection  
> **Impact:** -50% MTTR (Mean Time To Repair)

### Create: `infra/docker-stack/monitoring/prometheus_alerts.yml`

```yaml
groups:
  - name: Nexus_Alerts
    interval: 30s
    rules:
      # ════════════════════════════════════════════════
      # RESOURCE ALERTS
      # ════════════════════════════════════════════════
      
      - alert: HighMemoryUsage
        expr: |
          (container_memory_usage_bytes / container_spec_memory_limit_bytes) > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.container_name }}"
          description: "Memory usage is {{ $value | humanizePercentage }}"
      
      - alert: CriticalMemoryUsage
        expr: |
          (container_memory_usage_bytes / container_spec_memory_limit_bytes) > 0.95
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Critical memory usage on {{ $labels.container_name }}"
          description: "Immediate action required: {{ $value | humanizePercentage }}"
      
      # ════════════════════════════════════════════════
      # KAFKA ALERTS
      # ════════════════════════════════════════════════
      
      - alert: KafkaBrokerDown
        expr: up{job="kafka-brokers"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Kafka broker {{ $labels.instance }} is down"
          description: "Broker has been down for more than 1 minute"
      
      - alert: KafkaUnderReplicatedPartitions
        expr: kafka_controller_kafkacontroller_underreplicatedpartitionscount > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Kafka has under-replicated partitions"
          description: "Count: {{ $value }}"
      
      - alert: KafkaOfflinePartitions
        expr: kafka_controller_kafkacontroller_offlinepartitionscount > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Kafka has offline partitions"
          description: "Count: {{ $value }}"
      
      # ════════════════════════════════════════════════
      # SPARK ALERTS
      # ════════════════════════════════════════════════
      
      - alert: SparkApplicationFailed
        expr: spark_app_statuses{status="FAILED"} > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Spark application {{ $labels.app_name }} failed"
          description: "Application has failed"
      
      - alert: SparkExecutorLost
        expr: increase(spark_executor_task_failed[5m]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Spark executors are failing"
          description: "Failed tasks: {{ $value }}"
      
      # ════════════════════════════════════════════════
      # DATABASE ALERTS
      # ════════════════════════════════════════════════
      
      - alert: PostgreSQLDown
        expr: pg_up{job="postgresql"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL is down"
          description: "Unable to connect to PostgreSQL"
      
      - alert: PostgreSQLSlowQueries
        expr: |
          rate(pg_stat_statements_mean_exec_time{query!~".*pg_catalog.*"}[5m]) > 5000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow queries detected in PostgreSQL"
          description: "Query time: {{ $value | humanizeDuration }}"
      
      # ════════════════════════════════════════════════
      # API ALERTS
      # ════════════════════════════════════════════════
      
      - alert: HighErrorRate
        expr: |
          rate(http_requests_total{status=~"5.."}[5m]) / 
          rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate on {{ $labels.endpoint }}"
          description: "Error rate: {{ $value | humanizePercentage }}"
      
      - alert: SlowResponseTime
        expr: |
          histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow API responses"
          description: "95th percentile: {{ $value | humanizeDuration }}"
      
      # ════════════════════════════════════════════════
      # MINIO ALERTS
      # ════════════════════════════════════════════════
      
      - alert: MinIODiskUsageHigh
        expr: minio_disk_free_bytes / minio_disk_total_bytes < 0.15
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "MinIO disk usage is high"
          description: "Free space: {{ $value | humanizePercentage }}"
      
      # ════════════════════════════════════════════════
      # SERVICE HEALTH ALERTS
      # ════════════════════════════════════════════════
      
      - alert: ServiceDown
        expr: up{job!="prometheus"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"
          description: "Service has been down for more than 2 minutes"
```

### Update `prometheus.yml` để enable alerts:

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

rule_files:
  - "prometheus_alerts.yml"
```

---

## 4. Distributed Tracing Setup (Jaeger)

> **Lợi ích:** Better debugging, performance analysis  
> **Impact:** -50% debugging time

### Add Jaeger to docker-compose

```yaml
jaeger:
  image: jaegertracing/all-in-one:latest
  container_name: nexus-jaeger
  environment:
    COLLECTOR_ZIPKIN_HOST_PORT: ":9411"
    MEMORY_MAX_TRACES: 10000
  ports:
    - "6831:6831/udp"    # Jaeger Agent (Thrift compact)
    - "6832:6832/udp"    # Jaeger Agent (Thrift binary)
    - "5778:5778"        # Jaeger Agent (Serve configs)
    - "16686:16686"      # Jaeger UI
    - "14268:14268"      # Jaeger Collector (HTTP)
    - "14250:14250"      # Jaeger Collector (gRPC)
    - "9411:9411"        # Zipkin API
  networks:
    - nexus_network
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:16686/"]
    interval: 10s
    timeout: 5s
    retries: 3
  deploy:
    resources:
      limits:
        memory: 1G
        cpus: "1"
      reservations:
        memory: 512M
        cpus: "0.5"
```

### Integration in FastAPI

```python
# apps/api/main.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# Setup Jaeger exporter
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)

trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()
```

Access Jaeger UI: `http://localhost:16686`

---

## 5. PostgreSQL Query Optimization

> **Lợi ích:** Better catalog query performance  
> **Impact:** +15-20% query speed

### Recommended Indexes

```sql
-- For metadata catalog
CREATE INDEX idx_metadata_dataset_id ON metadata(dataset_id);
CREATE INDEX idx_metadata_created_at ON metadata(created_at DESC);
CREATE INDEX idx_metadata_layer ON metadata(layer);

-- For lineage tracking
CREATE INDEX idx_lineage_source_id ON lineage(source_id);
CREATE INDEX idx_lineage_target_id ON lineage(target_id);
CREATE INDEX idx_lineage_timestamp ON lineage(created_at DESC);

-- For performance tracking
CREATE INDEX idx_performance_job_id ON performance(job_id, timestamp DESC);
CREATE INDEX idx_performance_service ON performance(service_name, timestamp DESC);
```

### Monitor Query Performance

```sql
-- Check slow queries
SELECT 
    query,
    calls,
    mean_exec_time,
    max_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 1000
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

## 6. Scaling Kafka to 5 Brokers

> **Benefit:** +66% throughput  
> **Complexity:** Medium (requires testing)

### Add Kafka-4 and Kafka-5

```yaml
kafka-4:
  image: confluentinc/cp-kafka:7.5.0
  container_name: nexus-kafka-4
  depends_on:
    - zookeeper
  environment:
    KAFKA_BROKER_ID: 4
    KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
    KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka-4:29095,PLAINTEXT_HOST://localhost:9095
    KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
    KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 4
    KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 4
    KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 3
    KAFKA_DEFAULT_REPLICATION_FACTOR: 4
    KAFKA_MIN_INSYNC_REPLICAS: 3
    KAFKA_JMX_PORT: 9104
    KAFKA_JMX_HOSTNAME: kafka-4
  ports:
    - "9095:9095"
    - "9104:9104"
  networks:
    - nexus_network
  volumes:
    - kafka_4_data:/var/lib/kafka/data
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: "1"

kafka-5:
  image: confluentinc/cp-kafka:7.5.0
  container_name: nexus-kafka-5
  depends_on:
    - zookeeper
  environment:
    KAFKA_BROKER_ID: 5
    KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
    KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka-5:29096,PLAINTEXT_HOST://localhost:9096
    KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
    KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 4
    KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 4
    KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 3
    KAFKA_DEFAULT_REPLICATION_FACTOR: 4
    KAFKA_MIN_INSYNC_REPLICAS: 3
    KAFKA_JMX_PORT: 9105
    KAFKA_JMX_HOSTNAME: kafka-5
  ports:
    - "9096:9096"
    - "9105:9105"
  networks:
    - nexus_network
  volumes:
    - kafka_5_data:/var/lib/kafka/data
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: "1"
```

### Update Prometheus scrape config

```yaml
- job_name: 'kafka-brokers'
  static_configs:
    - targets:
        - 'kafka-1:9101'
        - 'kafka-2:9102'
        - 'kafka-3:9103'
        - 'kafka-4:9104'
        - 'kafka-5:9105'
```

---

## 🎯 Implementation Roadmap

### Phase 1: Critical (Week 1) ⚡
- [ ] Add health checks to all 22 services
- [ ] Configure memory limits
- [ ] Test health check functionality
- [ ] Document changes

### Phase 2: Monitoring (Week 2-3) 📊
- [ ] Deploy Prometheus alert rules
- [ ] Setup Jaeger distributed tracing
- [ ] Configure alerting channels
- [ ] Create Grafana dashboards

### Phase 3: Optimization (Week 4+) 🚀
- [ ] Add PostgreSQL indexes
- [ ] Scale Kafka to 5 brokers
- [ ] Setup PostgreSQL replication
- [ ] Performance testing

---

## ✅ Testing Checklist

- [ ] Health checks trigger service restart
- [ ] Memory limits prevent OOM
- [ ] Alerts fire for high resource usage
- [ ] Jaeger traces are collected
- [ ] Database queries use indexes
- [ ] Kafka handles 5000+ msgs/sec
- [ ] API response time < 500ms
- [ ] System survives 1 node failure

---

**Version:** 1.0  
**Last Updated:** February 12, 2026  
**Status:** Ready for Implementation
