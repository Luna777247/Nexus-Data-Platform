<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/drive/1QquQhMaMmfBUqiD6rIo99SopUQQtrOl6

## Run Locally

**Prerequisites:**  Node.js


1. Install dependencies:
   `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key
3. Run the app:
   `npm run dev`

---

## Build & Run với Docker

```bash
cd apps/ui
# Copy .env.example thành .env và chỉnh sửa endpoint nếu cần
cp .env.example .env
# Build image
docker build -t nexus-ui .
# Run container
# (hoặc dùng docker-compose nếu đã cấu hình service ui)
docker run -d -p 3000:80 --env-file .env --name nexus-ui nexus-ui
```

## Environment Variables
- Xem file `.env.example` để biết các biến cần thiết

## Production static
- Build ra static và serve bằng Nginx (xem Dockerfile)

## Tích hợp
- Kết nối API backend, Superset, Grafana, Elasticsearch, Kibana, Prometheus
- Hỗ trợ JWT, RBAC (nên kiểm tra lại code)

## Healthcheck
- Truy cập `/` kiểm tra UI hoạt động
