# Deployment Information

## Trạng thái

Chưa có public URL. Chưa deploy Railway/Render vì phiên làm việc này không có thông tin đăng nhập/tài khoản cloud. Không ghi URL giả.

## Platform config đã chuẩn bị

Railway dùng `06-lab-complete/railway.toml` và Dockerfile tại `06-lab-complete/`. Cần cấu hình `AGENT_API_KEY`, `REDIS_URL`, `RATE_LIMIT_PER_MINUTE`, `DAILY_BUDGET_USD`, `PORT`, `ENVIRONMENT` trên platform. Redis phải là dịch vụ dùng chung và `REDIS_URL` trỏ tới dịch vụ đó.

## Lệnh kiểm tra sau khi deploy

```bash
curl https://<domain>/health
curl https://<domain>/ready
curl -X POST https://<domain>/ask \
  -H 'X-API-Key: <AGENT_API_KEY>' \
  -H 'Content-Type: application/json' \
  -d '{"question":"What is deployment?"}'
```

Kỳ vọng: `/health` và `/ready` trả 200 khi Redis sẵn sàng; `/ask` trả 200 với key đúng và 401 nếu thiếu/sai key. Chạy `python check_production_ready.py --public-url https://<domain>` để xác minh URL.

## Screenshots

Chưa có screenshot deployment do chưa deploy.
