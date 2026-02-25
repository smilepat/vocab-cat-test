# 부하 테스트 및 성능 검증 가이드

## 도구 설치

### 1. Locust (Python 기반)
```bash
pip install locust
```

### 2. k6 (권장)
- Windows: `choco install k6`
- Mac: `brew install k6`
- Linux: https://k6.io/docs/getting-started/installation/

---

## 성능 벤치마크 목표

### 백엔드 API
| 엔드포인트 | P50 | P95 | P99 | 에러율 |
|-----------|-----|-----|-----|--------|
| `/health` | <100ms | <200ms | <500ms | <0.1% |
| `/metrics` | <200ms | <500ms | <1s | <0.1% |
| `/api/v1/test/start` | <2s | <4s | <6s | <1% |
| `/api/v1/test/{id}/respond` | <1s | <2s | <4s | <1% |

### 시스템 리소스
- **CPU 사용률**: <70% (평균)
- **메모리 사용률**: <80%
- **동시 사용자**: 100명 이상
- **처리량**: 50 req/s 이상

---

## 간단한 성능 테스트

### Python으로 간단한 테스트
```python
import time
import requests

def test_health():
    start = time.time()
    response = requests.get("http://localhost:8000/health")
    duration = time.time() - start
    print(f"Health check: {response.status_code} ({duration*1000:.0f}ms)")

def test_start():
    start = time.time()
    response = requests.post("http://localhost:8000/api/v1/test/start", json={
        "nickname": "TestUser",
        "grade": "중2",
        "self_assess": "intermediate"
    })
    duration = time.time() - start
    print(f"Start test: {response.status_code} ({duration*1000:.0f}ms)")

# 실행
for i in range(10):
    test_health()
    test_start()
```

---

## 모니터링

### Prometheus 메트릭 확인
```bash
curl http://localhost:8000/metrics
```

### Cloud Run 메트릭
- Google Cloud Console → Cloud Run → 서비스 선택 → Metrics
- 요청 수, 응답 시간, 메모리 사용량 확인

---

**성능 테스트 결과를 기록하고 최적화 계획을 수립하세요!**
