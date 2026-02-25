# 로컬 테스트 가이드

## ✅ 현재 상태

### 백엔드
- **서버**: http://localhost:8000
- **상태**: ✅ 실행 중
- **데이터**: 9,183개 단어 로드 완료
- **데이터베이스**: SQLite (irt_cat_engine/db/irt_cat.db)

### 프론트엔드
- **Vercel**: https://vocab-cat-test.vercel.app
- **상태**: ✅ 배포 완료

---

## 🚀 로컬에서 백엔드 실행하기

### 방법 1: 프로젝트 루트에서 실행 (권장)
```bash
cd f:/vocab-cat-test
python -m uvicorn irt_cat_engine.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 방법 2: 백그라운드 실행
```bash
cd f:/vocab-cat-test
python -m uvicorn irt_cat_engine.api.main:app --host 0.0.0.0 --port 8000 &
```

---

## 🧪 API 엔드포인트 테스트

### 1. Health Check
```bash
curl http://localhost:8000/health
```

**예상 응답**:
```json
{
  "status": "healthy",
  "data_loaded": true,
  "vocab_count": 9183,
  "active_sessions": 0,
  "database": {
    "connected": true,
    "url_type": "sqlite"
  },
  "version": "0.2.0",
  "uptime_check": "ok"
}
```

### 2. Root Endpoint
```bash
curl http://localhost:8000/
```

### 3. Prometheus Metrics
```bash
curl http://localhost:8000/metrics
```

### 4. API Documentation
브라우저에서 접속:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🎯 전체 스택 로컬 테스트

### 프론트엔드도 로컬에서 실행
```bash
cd irt_cat_engine/frontend
npm run dev
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000

### 테스트 시나리오

#### 1. 테스트 시작
```bash
curl -X POST http://localhost:8000/api/v1/test/start \
  -H "Content-Type: application/json" \
  -d '{
    "nickname": "TestUser",
    "grade": "중2",
    "self_assess": "intermediate",
    "exam_experience": "none",
    "question_type": 0
  }'
```

#### 2. 응답 제출
```bash
# 위에서 받은 session_id와 item_id 사용
curl -X POST http://localhost:8000/api/v1/test/{session_id}/respond \
  -H "Content-Type: application/json" \
  -d '{
    "item_id": 1234,
    "is_correct": true,
    "is_dont_know": false,
    "response_time_ms": 3000
  }'
```

#### 3. 결과 조회
```bash
curl http://localhost:8000/api/v1/test/{session_id}/results
```

---

## 🔍 로그 확인

### 서버 로그
서버를 포그라운드로 실행한 경우 콘솔에서 실시간 확인

### 파일 로그
로그 파일이 설정된 경우:
```bash
tail -f logs/app.log
```

---

## 🛠️ 문제 해결

### 포트 8000이 이미 사용 중
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID {프로세스ID} /F

# 다른 포트 사용
python -m uvicorn irt_cat_engine.api.main:app --port 8001
```

### 데이터 로딩 실패
- `9000word_full_db.csv` 파일 존재 확인
- `vocabulary_graph.json` 파일 존재 확인 (선택사항)

### Import 오류
반드시 **프로젝트 루트**에서 실행:
```bash
cd f:/vocab-cat-test
python -m uvicorn irt_cat_engine.api.main:app --port 8000
```

---

## 📊 모니터링

### 실시간 메트릭 확인
```bash
# 지속적으로 메트릭 확인
watch -n 5 "curl -s http://localhost:8000/metrics | grep http_requests_total"
```

### 활성 세션 확인
```bash
curl -s http://localhost:8000/health | grep active_sessions
```

---

## 🎨 프론트엔드-백엔드 연결

### Vercel 프론트엔드 → 로컬 백엔드

**문제**: Vercel 배포된 프론트엔드는 localhost에 접근 불가

**해결책**:
1. **로컬에서 프론트엔드 실행** (권장)
2. **ngrok 같은 터널 서비스 사용**
3. **백엔드도 배포**

### 로컬 프론트엔드 설정
```bash
cd irt_cat_engine/frontend

# .env.local 생성
echo "VITE_API_BASE=http://localhost:8000/api/v1" > .env.local

# 실행
npm run dev
```

---

## ✅ 테스트 체크리스트

- [ ] 백엔드 서버 시작 성공
- [ ] Health check 정상 응답
- [ ] API 문서 접속 가능 (http://localhost:8000/docs)
- [ ] 테스트 세션 생성 가능
- [ ] 문항 응답 정상 작동
- [ ] 결과 조회 정상 작동
- [ ] Prometheus 메트릭 수집 중
- [ ] 프론트엔드 연결 성공 (로컬 실행 시)

---

**현재 실행 중인 서버**:
- Backend: http://localhost:8000 ✅
- Frontend (Vercel): https://vocab-cat-test.vercel.app ✅
- Frontend (로컬): http://localhost:5173 (실행 시)
