# Benchmark & Observability Report — Day 14

**Họ tên:** Le Doan Duong  
**Ngày:** 2026-11-25  
**Môi trường:** Linux / Python 3.12. Docker CLI có mặt nhưng daemon từ chối socket (`permission denied`). Package index không phân giải DNS nên không cài được FastAPI/Uvicorn/Redis.

> Các phép đo bên dưới chưa chạy được. Không dùng số minh họa trong hướng dẫn làm bằng chứng. Hãy chạy lại trong môi trường có dependencies và Docker, rồi điền JSON/CSV/screenshot thật.

## 1. SLO

| SLI | Mục tiêu lab | Lý do |
|---|---:|---|
| p95 latency `/ask` | ≤ 500 ms | Giới hạn tail latency mẫu trong load test. |
| Error rate `/ask` | ≤ 2% | Mức lỗi mẫu chấp nhận được trong lab. |
| Accuracy | ≥ 85% | Ngưỡng quality gate; cần kết hợp kiểm tra regression. |

## 2. Hiệu năng (`develop/load_test.py`)

### 2.1 Concurrency vs latency — v2

| Concurrency | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Error rate | SLO |
|---:|---:|---:|---:|---:|---:|---|
| 1 | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa xác định |
| 10 | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa xác định |
| 50 | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa xác định |
| 100 | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa xác định |

Chưa chạy được do thiếu package runtime và Docker daemon. Cần lưu từng lần chạy bằng `--out reports/load_v2_c{concurrency}.json`. RPS không nhất thiết tăng tuyến tính: giới hạn CPU, worker, network, upstream latency và queueing sẽ trở thành nút thắt.

### 2.2 Tail latency

| `MOCK_SLOW_RATE` | avg (ms) | p95 (ms) | p99 (ms) |
|---:|---:|---:|---:|
| 0 | Chưa đo | Chưa đo | Chưa đo |
| 0.03 | Chưa đo | Chưa đo | Chưa đo |
| 0.1 | Chưa đo | Chưa đo | Chưa đo |

Chưa đo. Nhóm request chậm tác động mạnh tới p99; khi tỷ lệ request chậm vượt 5%, p95 cũng bị kéo lên. Average trộn request nhanh và chậm nên có thể che trải nghiệm của nhóm người dùng ở tail.

## 3. Eval chất lượng (`eval/run_eval.py`)

| Chỉ số | v1 | v2 ban đầu | v2 sau sửa KB |
|---|---:|---:|---:|
| Accuracy | Chưa chạy | Chưa chạy | Chưa chạy |
| Avg tokens / câu | Chưa chạy | Chưa chạy | Chưa chạy |
| Tổng cost | Chưa chạy | Chưa chạy | Chưa chạy |
| Cost / câu đúng | Chưa chạy | Chưa chạy | Chưa chạy |
| Quality gate | Chưa chạy | Chưa chạy | Chưa chạy |

Hướng dẫn lab dự kiến hai lỗi ban đầu ở `scaling-03` và `security-02`. Đã thêm câu trả lời trong knowledge base cho Kubernetes HPA (CPU, memory, custom metrics) và khác biệt JWT/API key (token, expiry, chữ ký). Cần xác nhận lại bằng eval; không đưa số ví dụ trong tài liệu vào bảng kết quả.

Trade-off dự kiến: retrieval tăng chất lượng và prompt tokens/cost, đồng thời tăng một ít latency. `.github/workflows/quality-gate.yml` chạy eval v2 với ngưỡng 100% trong pull request.

## 4. Observability stack

### 4.1 Screenshot

Chưa có screenshot. Docker daemon không khả dụng nên Grafana/Prometheus/Jaeger/Locust chưa khởi chạy.

### 4.2 Thí nghiệm

| Thay đổi | Alert | Thời gian tới firing | Panel |
|---|---|---|---|
| `MOCK_ERROR_RATE=0.2` | Chưa chạy | Chưa đo | Chưa đo |
| `MOCK_SLOW_RATE=0.3` | Chưa chạy | Chưa đo | Chưa đo |
| `LLM_MODEL=mock-llm-large` | Chưa chạy | Chưa đo | Chưa đo |
| Pause một agent | Chưa chạy | Chưa đo | Chưa đo |
| `AGENT_VERSION=v1` | Theo thiết kế không có infrastructure alert | N/A | Cần eval quality gate |

Quality regression không nhất thiết làm metric hạ tầng xấu; phát hiện bằng golden dataset eval, canary eval hoặc quality score monitoring.

### 4.3 Trace

Chưa có trace ID/sample thực tế. Sau khi bật stack, ghi trace chậm nhất, tổng duration, span chiếm thời gian và log có cùng `trace_id` tại đây.

## 5. Scaling (Locust, 100 users, 2 phút)

| Instances | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Failures |
|---:|---:|---:|---:|---:|---:|
| 1 | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo |
| 3 | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo |

Chưa chạy do Docker daemon không truy cập được. Nếu p95 không đổi khi scale, cần kiểm tra LLM latency/upstream hoặc dependency bottleneck qua dashboard và trace.

## 6. Kết luận

1. Percentile phơi bày tail latency mà average có thể che khuất.
2. State dùng chung trong Redis cho phép scale/restart instance mà vẫn giữ limiter và ngân sách.
3. Metrics, logs, traces và eval đo các khía cạnh khác nhau; cần phối hợp để phát hiện sự cố hạ tầng lẫn chất lượng.

Khi chạy production thật, bổ sung saturation/queue depth, Redis latency/availability, worker utilization, budget burn rate và chất lượng eval theo phiên bản.
