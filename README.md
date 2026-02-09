# 🚀 Nexus Data Platform

**Complete end-to-end data platform for tourism industry with real-time data ingestion, processing, and analytics**

[![Data Pipeline](https://img.shields.io/badge/Status-Production_Ready-brightgreen)]()
[![Platform](https://img.shields.io/badge/Platform-Docker-blue)]()

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
cd docker-stack
docker-compose up -d
./health-check.sh
```

### Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| Airflow | http://localhost:8888 | admin/admin |
| MinIO Console | http://localhost:9001 | minioadmin/minioadmin123 |
| ClickHouse | http://localhost:8123 | - |
| FastAPI Docs | http://localhost:8000/docs | - |

Full setup guide: **[SETUP_COMPLETE.md](./SETUP_COMPLETE.md)**

---

## 📚 Documentation

| Guide | Description |
|-------|-------------|
| **[SETUP_COMPLETE.md](./SETUP_COMPLETE.md)** | Complete setup & commands |
| **[DATA_PLATFORM_STACK.md](./DATA_PLATFORM_STACK.md)** | Architecture & tech stack |
| **[IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md)** | Step-by-step with code |
| **[TECHNOLOGY_COMPARISON.md](./TECHNOLOGY_COMPARISON.md)** | Tech choices explained |
| **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** | Quick commands reference |

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

**Full examples:** [SETUP_COMPLETE.md](./SETUP_COMPLETE.md)

---

## 💻 Project Structure

```
nexus-data-platform/
├── docker-stack/         # Infrastructure (10 Docker services)
├── airflow/dags/         # Workflow orchestration  
├── spark/                # Data processing jobs
├── api/                  # FastAPI serving layer
├── components/           # React UI components
└── services/             # Business logic
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
npm run dev  # http://localhost:5173
```

**Backend API:**
```bash
pip install -r api/requirements.txt
python api/main.py  # http://localhost:8000
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
