# 🚀 Nexus Data Platform

**Complete end-to-end data platform for tourism industry with real-time data ingestion, processing, and analytics**

[![Data Pipeline](https://img.shields.io/badge/Status-Production_Ready-brightgreen)]()
[![Platform](https://img.shields.io/badge/Platform-Docker%20%7C%20Kubernetes-blue)]()

---

## ✨ Platform Features

- 🔌 **Real-time Ingestion** - Kafka + Airflow orchestration  
- 💾 **Data Storage** - MinIO (S3-compatible) + Delta Lake + ClickHouse  
- ⚙️ **Data Processing** - Apache Spark batch & streaming jobs  
- 📊 **Analytics Engine** - ClickHouse for sub-second analytics  
- 🔍 **Search Layer** - Elasticsearch for full-text search  
- ⚡ **Caching** - Redis for ultra-fast data access  
- 🌐 **API Layer** - FastAPI REST + GraphQL support  
- 📈 **BI Dashboard** - Apache Superset visualization  

---

## 🎯 Quick Start

### Deploy Complete Stack (5 minutes)

```bash
cd infra/docker-stack
docker-compose up -d
./health-check.sh
```

### Deploy on Kubernetes (local)

```bash
docker build -t nexus-api:local -f apps/api/Dockerfile .
docker build -t nexus-frontend:local \
   --build-arg VITE_API_URL=http://localhost:8000 \
   -f apps/frontend/Dockerfile .
kubectl apply -f k8s/stack.yaml
kubectl -n nexus-data-platform get pods
```

### Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| Airflow | http://localhost:8888 | admin/admin |
| MinIO Console | http://localhost:9001 | minioadmin/minioadmin123 |
| ClickHouse | http://localhost:8123 | - |
| FastAPI Docs | http://localhost:8000/docs | - |

Full setup guide: **[DOCS.md](./DOCS.md)**

---

## 📚 Documentation

| Guide | Description |
|-------|-------------|
| **[DOCS.md](./DOCS.md)** | 📖 Complete technical documentation |
| **[k8s/README.md](./k8s/README.md)** | ☸️ Kubernetes manifests & local guide |

---

## 🔥 What's Included

✅ **Docker Stack** - 10 services (Kafka, Spark, ClickHouse, etc.)  
✅ **Airflow DAG** - Tourism events pipeline with 6 tasks  
✅ **Spark Job** - Data processing & ML recommendations  
✅ **FastAPI** - 12+ REST endpoints with caching  
✅ **React Dashboard** - Real-time data visualization  

---

## 🚀 Usage Examples

Run pipeline:
```bash
docker exec nexus-airflow-scheduler airflow dags trigger tourism_events_pipeline
```

Query analytics:
```bash
docker exec nexus-clickhouse clickhouse-client --query "SELECT region, count(*) FROM analytics.events GROUP BY region"
```

Test API:
```bash
curl http://localhost:8000/api/v1/tours?region=VN
```

**Full examples:** [DOCS.md](./DOCS.md)

---

## 💻 Project Structure

```
nexus-data-platform/
├── apps/frontend/        # React UI application
├── apps/api/             # FastAPI serving layer
├── pipelines/airflow/    # Workflow orchestration
├── jobs/spark/           # Data processing jobs
├── infra/docker-stack/   # Infrastructure (10 Docker services)
└── packages/shared/      # Shared contracts, types, utilities
```

---

## 📊 Architecture

```
Data Sources → Kafka → Airflow → MinIO → Spark → ClickHouse → FastAPI → React UI
                 ↓                           ↓         ↓
              Stream                    Batch     Analytics
```

See full architecture: **[DATA_PLATFORM_STACK.md](./DATA_PLATFORM_STACK.md)**

---

## 🛠️ Development

**Frontend:**
```bash
npm install
npm run frontend:dev  # http://localhost:5173
```

**Backend API:**
```bash
pip install -r apps/api/requirements.txt
python apps/api/main.py  # http://localhost:8000
```

---

## 📈 Performance

| Component | Throughput | Latency |
|-----------|-----------|---------|
| Kafka | 1M+ events/sec | <100ms |
| ClickHouse | 1M+ rows/sec | <100ms |
| Redis | 100K ops/sec | <1ms |
| FastAPI | 10K req/sec | <50ms |

---

## 📄 License

MIT License

---

**Made with ❤️ for data engineering** • [Full Documentation](./SETUP_COMPLETE.md) • 🚀 **Deploy. Process. Analyze.**
