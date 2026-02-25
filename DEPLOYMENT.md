# Deployment Guide - IRT CAT Engine

이 문서는 IRT CAT Engine (vocab-cat-test) 애플리케이션을 다양한 환경에 배포하는 방법을 설명합니다.

## 목차

- [사전 요구사항](#사전-요구사항)
- [환경 설정](#환경-설정)
- [로컬 개발 환경](#로컬-개발-환경)
- [Docker 배포](#docker-배포)
- [Google Cloud Run 배포](#google-cloud-run-배포)
- [Vercel 프론트엔드 배포](#vercel-프론트엔드-배포)
- [환경 변수 설정](#환경-변수-설정)
- [문제 해결](#문제-해결)

---

## 사전 요구사항

### 필수 소프트웨어
- **Python 3.13+** (백엔드)
- **Node.js 18+** (프론트엔드)
- **Git** (버전 관리)
- **Docker** (컨테이너 배포 시)

### 선택 사항
- **PostgreSQL** (Production 환경 권장)
- **Redis** (세션 관리, 향후 확장용)
- **Google Cloud SDK** (Cloud Run 배포 시)

---

## 환경 설정

### 1. .env 파일 생성

루트 디렉토리에 `.env` 파일을 생성합니다:

```bash
cp .env.example .env
```

### 2. 필수 환경 변수 설정

`.env` 파일을 편집하여 환경에 맞게 설정:

```env
# CORS 설정 - 프론트엔드 도메인 추가
ALLOWED_ORIGINS=http://localhost:5173,https://your-frontend-domain.com

# 데이터베이스 (개발: SQLite, Production: PostgreSQL)
DATABASE_URL=sqlite:///./irt_cat_engine/db/irt_cat.db

# 로그 레벨
LOG_LEVEL=INFO
LOG_FILE_PATH=./logs/app.log
```

---

## 로컬 개발 환경

### 백엔드 실행

```bash
# 1. 의존성 설치
cd irt_cat_engine
pip install -r requirements.txt

# 2. 데이터베이스 초기화 (자동)
# 첫 실행 시 자동으로 SQLite DB가 생성됩니다

# 3. 서버 실행
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

서버가 실행되면:
- API 문서: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### 프론트엔드 실행

```bash
# 1. 프론트엔드 디렉토리로 이동
cd irt_cat_engine/frontend

# 2. 의존성 설치
npm install

# 3. 개발 서버 실행
npm run dev
```

프론트엔드가 실행되면:
- 개발 서버: http://localhost:5173

---

## Docker 배포

### 1. Docker 이미지 빌드

```bash
# 루트 디렉토리에서 실행
docker build -t vocab-cat-api:latest .
```

### 2. 로컬에서 Docker 실행

```bash
docker run -d \
  --name vocab-cat-api \
  -p 8000:8000 \
  -e ALLOWED_ORIGINS="http://localhost:5173,https://your-domain.com" \
  -e LOG_LEVEL="INFO" \
  vocab-cat-api:latest
```

### 3. Docker Compose 사용 (PostgreSQL 포함)

`docker-compose.yml` 파일 생성:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: vocab_cat
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: your_secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://admin:your_secure_password@postgres:5432/vocab_cat
      ALLOWED_ORIGINS: http://localhost:5173
      LOG_LEVEL: INFO
    depends_on:
      - postgres
    volumes:
      - ./logs:/app/logs

volumes:
  postgres_data:
```

실행:

```bash
docker-compose up -d
```

---

## Google Cloud Run 배포

### 1. Google Cloud 프로젝트 설정

```bash
# Google Cloud SDK 설치 후
gcloud init
gcloud config set project YOUR_PROJECT_ID
```

### 2. Container Registry에 이미지 푸시

```bash
# 이미지 빌드 및 태그
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/vocab-cat-api

# 또는 Docker로 빌드 후 푸시
docker build -t gcr.io/YOUR_PROJECT_ID/vocab-cat-api .
docker push gcr.io/YOUR_PROJECT_ID/vocab-cat-api
```

### 3. Cloud Run에 배포

```bash
gcloud run deploy vocab-cat-api \
  --image gcr.io/YOUR_PROJECT_ID/vocab-cat-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ALLOWED_ORIGINS="https://your-frontend.vercel.app" \
  --set-env-vars LOG_LEVEL="INFO" \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10
```

### 4. Cloud SQL (PostgreSQL) 연결

Cloud SQL 인스턴스를 사용하는 경우:

```bash
gcloud run deploy vocab-cat-api \
  --image gcr.io/YOUR_PROJECT_ID/vocab-cat-api \
  --add-cloudsql-instances YOUR_PROJECT_ID:us-central1:vocab-cat-db \
  --set-env-vars DATABASE_URL="postgresql://user:pass@/vocab_cat?host=/cloudsql/YOUR_PROJECT_ID:us-central1:vocab-cat-db"
```

---

## Vercel 프론트엔드 배포

### 1. Vercel CLI 설치

```bash
npm install -g vercel
```

### 2. 프론트엔드 빌드 설정

`irt_cat_engine/frontend/vite.config.ts`에서 API URL 설정:

```typescript
export default defineConfig({
  plugins: [react()],
  define: {
    'import.meta.env.VITE_API_BASE': JSON.stringify(
      process.env.VITE_API_BASE || 'http://localhost:8000/api/v1'
    ),
  },
})
```

### 3. 배포

```bash
cd irt_cat_engine/frontend

# 프로덕션 배포
vercel --prod

# 환경 변수 설정
vercel env add VITE_API_BASE production
# 값 입력: https://your-cloud-run-url.run.app/api/v1
```

### 4. GitHub 자동 배포 (권장)

1. GitHub 저장소에 코드 푸시
2. Vercel 대시보드에서 프로젝트 import
3. 빌드 설정:
   - **Framework Preset**: Vite
   - **Root Directory**: `irt_cat_engine/frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. 환경 변수 추가:
   - `VITE_API_BASE`: Cloud Run API URL

---

## 환경 변수 설정

### 백엔드 환경 변수

| 변수 | 설명 | 기본값 | 필수 |
|------|------|--------|------|
| `ALLOWED_ORIGINS` | CORS 허용 도메인 (쉼표 구분) | `http://localhost:5173,...` | ✅ |
| `DATABASE_URL` | 데이터베이스 연결 URL | `sqlite:///...` | ✅ |
| `LOG_LEVEL` | 로그 레벨 | `INFO` | ❌ |
| `LOG_FILE_PATH` | 로그 파일 경로 | `./logs/app.log` | ❌ |
| `VOCAB_DATA_PATH` | 어휘 CSV 파일 경로 | `./9000word_full_db.csv` | ❌ |
| `GRAPH_DATA_PATH` | 어휘 그래프 JSON 경로 | `./vocabulary_graph.json` | ❌ |
| `PORT` | API 서버 포트 | `8000` | ❌ |

### 프론트엔드 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `VITE_API_BASE` | 백엔드 API 기본 URL | `http://localhost:8000/api/v1` |

---

## 문제 해결

### 1. CORS 오류

**증상**: 프론트엔드에서 API 호출 시 CORS 오류

**해결**:
```bash
# .env 파일에서 ALLOWED_ORIGINS에 프론트엔드 도메인 추가
ALLOWED_ORIGINS=http://localhost:5173,https://your-frontend.vercel.app
```

### 2. 데이터 로딩 실패

**증상**: "Vocabulary data not loaded yet"

**해결**:
- `9000word_full_db.csv` 파일이 올바른 위치에 있는지 확인
- 파일 권한 확인
- 로그 확인: `./logs/app.log`

### 3. Docker 빌드 실패

**증상**: "COPY failed"

**해결**:
- `.dockerignore` 파일이 필수 파일을 제외하지 않는지 확인
- Dockerfile의 COPY 경로 확인

### 4. Cloud Run 메모리 부족

**증상**: 503 오류, 컨테이너 재시작

**해결**:
```bash
# 메모리 할당 증가
gcloud run services update vocab-cat-api \
  --memory 2Gi \
  --cpu 2
```

### 5. 데이터베이스 연결 실패

**증상**: "could not connect to database"

**해결**:
- `DATABASE_URL` 환경 변수 확인
- PostgreSQL이 실행 중인지 확인
- Cloud SQL의 경우 Cloud SQL Proxy 설정 확인

---

## 보안 체크리스트

배포 전 다음 사항을 확인하세요:

- [ ] `.env` 파일이 `.gitignore`에 포함되어 있음
- [ ] `ALLOWED_ORIGINS`가 실제 도메인으로 제한됨 (와일드카드 `*` 사용 안 함)
- [ ] 데이터베이스 비밀번호가 강력함
- [ ] HTTPS 사용 (HTTP 차단)
- [ ] 로그 파일에 민감한 정보가 기록되지 않음
- [ ] API Rate Limiting 설정 (선택 사항)

---

## 성능 최적화 팁

### 백엔드
- Cloud Run: CPU 2개, 메모리 2GB 권장
- PostgreSQL 연결 풀링 설정 (SQLAlchemy)
- Redis 세션 관리 (다중 인스턴스 환경)

### 프론트엔드
- Vite 빌드 최적화 (code splitting)
- CDN 사용 (Vercel 자동 지원)
- 이미지 최적화

---

## 추가 자료

- [FastAPI 배포 가이드](https://fastapi.tiangolo.com/deployment/)
- [Google Cloud Run 문서](https://cloud.google.com/run/docs)
- [Vercel 배포 가이드](https://vercel.com/docs)
- [Docker 공식 문서](https://docs.docker.com/)

---

**문제가 발생하면**: 
1. `./logs/app.log` 확인
2. `docker logs <container-id>` 또는 `gcloud run logs read` 확인
3. GitHub Issues에 문의
