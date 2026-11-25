# Day 14 Lab — Mission Answers

**Sinh viên:** Le Doan Duong (theo tên repository)
**Môi trường làm bài:** Linux, Python 3.12; Docker CLI có nhưng Docker daemon từ chối kết nối. Dependencies Python không thể tải vì môi trường không có DNS/network.

> Các bước cần Railway/Render, Docker daemon, hoặc màn hình Grafana/Jaeger được đánh dấu rõ. Không ghi URL, screenshot hay kết quả đo không có thật.

## Part 1: Localhost vs Production

### Exercise 1.1 — Anti-patterns trong bản basic

1. API key nằm cứng trong source, có thể bị lộ khi commit và không thể rotate an toàn.
2. Port cố định, không tôn trọng biến `PORT` do platform cấp.
3. Bật debug mode ở production có thể lộ thông tin lỗi và tăng rủi ro bảo mật.
4. Không có health/readiness probe để orchestrator biết process sống và sẵn sàng nhận traffic.
5. Dùng `print()`/log text không cấu trúc, khó lọc và tổng hợp.
6. Không xử lý graceful shutdown; request đang chạy có thể bị cắt khi deploy/restart.
7. Không giới hạn request hay ngân sách gọi LLM.

### Exercise 1.2 — Chạy basic

Chưa chạy được trong môi trường hiện tại: các package FastAPI/Uvicorn chưa có sẵn và truy cập package index bị lỗi DNS. Lệnh dự kiến: `cd 01-localhost-vs-production/develop && pip install -r requirements.txt && python app.py`.

### Exercise 1.3 — Basic và advanced

| Feature | Basic | Advanced | Tại sao quan trọng? |
|---|---|---|---|
| Config | Hardcode | Environment variables | Cùng một image dùng được ở dev/staging/prod; secret không nằm trong Git. |
| Health | Không có | `/health` liveness và `/ready` readiness | Nền tảng restart process chết và tránh gửi traffic tới instance chưa sẵn sàng. |
| Logging | `print()`/text | JSON có field ổn định | Dễ tìm kiếm, lọc, phân tích và nối với trace. |
| Shutdown | Dừng đột ngột | Chờ request đang xử lý rồi thoát | Tránh mất request trong lúc deploy hoặc scale down. |
| Security | Key cố định/thiếu auth | API key từ env, JWT ở ví dụ nâng cao | Có thể thu hồi/rotate và xác thực caller. |

## Part 2: Docker

### Exercise 2.1 — Dockerfile cơ bản

1. Base image: `python:3.11-slim` theo Dockerfile ở `02-docker/develop`.
2. Working directory: `/app`.
3. Copy `requirements.txt` và cài dependencies trước source để Docker cache layer dependencies; sửa code không buộc cài lại package.
4. `CMD` cung cấp lệnh mặc định có thể override khi chạy container. `ENTRYPOINT` xác định executable chính; đối số truyền lúc `docker run` thường được nối vào entrypoint.

### Exercise 2.2 — Build/run

Chưa có số image size vì Docker daemon không truy cập được (`permission denied` trên socket). Không suy đoán số liệu.

### Exercise 2.3 — Multi-stage

Stage builder cài/build dependencies. Stage runtime chỉ chứa Python slim, runtime dependencies và source cần chạy. Loại build tool/cache khỏi image cuối giúp giảm kích thước, bề mặt tấn công và thời gian tải.

### Exercise 2.4 — Compose

Kiến trúc: `Client → Nginx:80 → Agent:8000 → Redis:6379`. Compose khởi động agent, Redis và Nginx; Nginx cân bằng request đến agent, agent dùng Redis để lưu state/chia sẻ dữ liệu giữa instances. File production của Part 6 hiện cung cấp agent + Redis; stack Nginx minh họa ở Part 5.

## Part 3: Cloud Deployment

### Exercise 3.1 — Railway

Chưa deploy: môi trường hiện tại không có Railway CLI/account credentials hay quyền cấu hình project. Cấu hình Railway đã chuẩn bị trong `06-lab-complete/railway.toml`; URL công khai và kiểm tra endpoint cần hoàn tất sau khi kết nối tài khoản.

### Exercise 3.2 — Railway và Render

`railway.toml` cấu hình builder/deploy bằng TOML. `render.yaml` là Blueprint YAML mô tả service, build/start command, health check và biến môi trường. Cả hai là Infrastructure as Code, nhưng schema và cách khởi tạo service khác nhau.

### Exercise 3.3 — Cloud Run CI/CD

Cloud Build lấy source, build image và deploy lên Cloud Run theo cấu hình service. Cloud Run quản lý HTTPS, autoscaling và có thể scale về zero; cần cấu hình quyền IAM, region, port và secret phù hợp.

## Part 4: API Security

### Exercise 4.1 — API key

Server đọc `X-API-Key`, so sánh với secret cấu hình ở môi trường. Thiếu/sai key phải trả 401. Rotate bằng cách tạo key mới, cập nhật secret trên platform và chuyển client; khi xác nhận đã chuyển xong thì thu hồi key cũ. Tránh log key.

### Exercise 4.2 — JWT

Client gửi thông tin đăng nhập tới endpoint token; server xác thực và ký JWT có thời hạn. Client gọi API bằng `Authorization: Bearer <token>`. API xác minh chữ ký và claim/expiry. JWT hữu ích cho danh tính/ủy quyền có claim; API key phù hợp xác thực đơn giản giữa service/client được quản lý. Không lưu mật khẩu dạng plaintext.

### Exercise 4.3 — Rate limiting

Ví dụ production trong lab dùng giới hạn theo cửa sổ thời gian và Redis; Part 6 triển khai sliding window 60 giây theo API key, trả 429 và `Retry-After`. Admin có thể có quota riêng cao hơn qua role/allowlist có kiểm soát, nhưng không nên bỏ giới hạn hoàn toàn.

### Exercise 4.4 — Cost guard

Part 6 lưu tổng chi phí theo ngày UTC trong Redis, tính cost từ input/output token và giá trên 1K token; trước LLM kiểm tra ngưỡng và trả 402 khi đã hết ngân sách. Bản triển khai hoàn chỉnh ở `06-lab-complete/app/cost_guard.py`.

## Part 5: Scaling & Reliability

### Exercise 5.1 — Health checks

`/health` trả 200 nếu process còn chạy; đây là liveness. `/ready` ping Redis và trả 200 khi dependency sẵn sàng, 503 khi không kết nối được; readiness không nên làm orchestrator restart process còn sống.

### Exercise 5.2 — Graceful shutdown

Uvicorn nhận SIGTERM, ngừng nhận request mới, chờ request in-flight hoàn thành rồi gọi lifespan shutdown để đóng Redis client. Không tự ghi signal handler thay thế handler Uvicorn.

### Exercise 5.3 — Stateless

State phiên/rate limit/chi phí lưu ở Redis dùng chung thay vì dictionary trong RAM. Mọi instance đọc cùng state, nên request tiếp theo có thể tới instance khác và state vẫn tồn tại sau restart.

### Exercise 5.4 — Load balancing

Compose dùng Nginx reverse proxy để phân phối request tới nhiều agent. Tăng replica không tự động giảm latency nếu upstream LLM hoặc dependency khác là nút thắt. Thí nghiệm Docker chưa chạy được do daemon không khả dụng.

### Exercise 5.5 — Stateless test

Kiểm chứng bằng cách tạo state, restart/kill một instance rồi gửi request tới instance khác; state phải còn do nằm ở Redis. Bộ kiểm tra `check_production_ready.py` có kiểm tra rate-limit state qua lần restart agent.

## Part 6: Production-ready agent

Đã triển khai 12 hạng mục trong checklist: multi-stage Dockerfile non-root/healthcheck; Compose agent + Redis; `.dockerignore`; liveness/readiness; API key; Redis sliding-window limiter; Redis daily cost guard; cấu hình env; JSON logs; FastAPI lifespan shutdown; Railway config. Script chấm chưa chạy được tới runtime vì thiếu `fastapi`/`uvicorn`; cài package thất bại do network/DNS, còn Docker socket báo permission denied. Vì vậy chưa thể tuyên bố `PASS 12/12`.

## Part 7: Benchmark & Observability

### Exercise 7.1 — Metrics và cardinality

Counter tích lũy tổng số sự kiện; Gauge tăng/giảm theo giá trị hiện tại; Histogram đếm quan sát theo bucket và hỗ trợ tính percentile. Dùng URL path thô làm label tạo time series mới cho mỗi URL bot ngẫu nhiên, làm cardinality và RAM Prometheus tăng mạnh. Dùng route template/nhãn có tập giá trị nhỏ.

### Exercise 7.2 — Load test và SLO

Không có kết quả concurrency thực tế trong môi trường này: agent dependencies chưa cài được do DNS/network. p95/p99 mô tả tail, còn average có thể bị số đông request nhanh che lấp nhóm request chậm. Đặt SLO theo percentile (thường p95, và p99 cho luồng nhạy latency) cùng error rate, thay vì chỉ dùng average.

### Exercise 7.3 — Eval và quality gate

Repo mô tả baseline kỳ vọng v1 khoảng 4%, v2 ban đầu khoảng 91%, sau bổ sung knowledge base đạt 23/23. Đây là số tham khảo ghi trong hướng dẫn, không phải kết quả chạy trong phiên này. Đã bổ sung kiến thức HPA và JWT vào mock knowledge base. CI nên chạy eval cố định và dùng exit code/`--min-accuracy` để fail pull request khi dưới ngưỡng hoặc có regression.

### Exercise 7.4–7.6 — Observability, trace, alerts

Chưa khởi chạy được Docker stack nên không có dashboard, trace, alert firing hay thời gian phát hiện thực tế; không đính kèm screenshot giả. Cách đọc: p95 cách xa average biểu thị tail; input tokens thường nhiều hơn output do system prompt/context; metrics chỉ mở nội bộ cho Prometheus, không public qua Nginx. Trace chậm cần so duration các span; trace lỗi có exception event. Chất lượng v1 giảm cần eval trên golden dataset/quality gate vì health và latency metric không đo độ đúng câu trả lời. Prometheus alert chỉ firing sau khi biểu thức thỏa điều kiện trong khoảng `for`.

### Exercise 7.7 — Report

`BENCHMARK_REPORT.md` ghi rõ các phép đo chưa chạy và điều kiện cản trở. Cần chạy agent + Docker observability stack ở máy có dependencies/Docker, lưu JSON/CSV/screenshot thật rồi điền số liệu và alert timing.

## Câu hỏi thảo luận

1. API key public có thể bị sao chép để gọi dịch vụ, phát sinh chi phí hoặc truy cập dữ liệu. Thu hồi/rotate ngay, kiểm tra logs, giới hạn quyền/quota và loại bỏ secret khỏi lịch sử commit.
2. Stateless cho phép mọi replica phục vụ request bất kỳ mà không phụ thuộc RAM của replica trước.
3. Dev/prod parity là giữ runtime, dependencies, quy trình khởi động và dịch vụ gần giống nhau để giảm lỗi chỉ xuất hiện sau deploy; cấu hình khác nhau qua env.
4. Serverless có cold start và giới hạn thời lượng/kết nối; gọi LLM lâu hoặc cần kết nối bền có thể làm UX kém. Dùng khi tải biến động và scale-to-zero có lợi.
5. Không đưa `user_id`, `request_id` hay URL tùy ý thành metric label; dùng log/trace để tra giá trị high-cardinality.
6. Pull cho phép Prometheus chủ động scrape và kiểm soát trạng thái target; workload scale-to-zero cần cân nhắc metrics gateway/managed collection hoặc synthetic monitoring.
7. Sampling giảm chi phí lưu trace nhưng có thể bỏ lỡ lỗi hiếm; tail-based sampling ưu tiên giữ trace lỗi/chậm.
8. `for: 0s` dễ báo động giả do spike; quá dài như 30m làm phát hiện muộn.
