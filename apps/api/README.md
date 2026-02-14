# FastAPI Backend - Nexus Data Platform

## Build & Run with Docker

```bash
cd apps/api
# Copy .env.example to .env and chỉnh sửa nếu cần
cp .env.example .env
# Build image
docker build -t nexus-api .
# Run container
# (hoặc dùng docker-compose nếu đã cấu hình service api)
docker run -d -p 8000:8000 --env-file .env --name nexus-api nexus-api
```

## Environment Variables
- Xem file `.env.example` để biết các biến cần thiết

## Tích hợp
- Kết nối Postgres, Redis, Kafka, MinIO, Superset, Elasticsearch, Grafana, Prometheus
- Hỗ trợ JWT, RBAC (nên kiểm tra lại code)

## Healthcheck
- GET /health

## Tài liệu API
- Swagger: /docs
- Redoc: /redoc
