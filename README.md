---

# Hướng dẫn chạy hệ thống Nexus Data Platform với Docker Compose

## 1. Chuẩn bị
- Cài đặt Docker và Docker Compose
- Clone repository này về máy
- Copy các file .env.example thành .env trong apps/api và apps/ui, chỉnh sửa endpoint/secret nếu cần

## 2. Build các image cần thiết
```bash
# Build backend (api) và frontend (ui) từ thư mục gốc project
cd d:\Nexus-Data-Platform
# Build backend (api)
docker build -t nexus-api -f apps/api/Dockerfile apps/api
# Build frontend (ui)
cd apps/ui
npm install react-is

cd d:\Nexus-Data-Platform
docker build -t nexus-ui -f apps/ui/Dockerfile apps/ui
```

## 3. Chạy toàn bộ hệ thống
```bash
cd infra/docker-stack
docker-compose up -d
```

## 4. Truy cập các dịch vụ
- UI: http://localhost (qua reverse proxy nginx)
- API: http://localhost/api/
- Superset: http://localhost/superset/
- Grafana: http://localhost/grafana/
- Kibana: http://localhost/kibana/
- Prometheus: http://localhost:9090

## 5. Kiểm tra trạng thái
```bash
docker-compose ps
docker-compose logs --tail=100 -f
```

## 6. Dừng hệ thống
```bash
docker-compose down
```

## 7. Lưu ý
- Đảm bảo các port không bị chiếm dụng
- Có thể chỉnh sửa docker-compose.yml để bật/tắt các service không cần thiết
- Để production, nên cấu hình HTTPS cho nginx và đổi các mật khẩu mặc định

---
