# Google Cloud Run 배포 가이드

## 사전 준비

### 1. Google Cloud SDK 설치 확인
```bash
gcloud --version
```

설치되지 않은 경우: https://cloud.google.com/sdk/docs/install

### 2. 프로젝트 설정
```bash
# Google Cloud 로그인
gcloud auth login

# 프로젝트 설정
gcloud config set project YOUR_PROJECT_ID

# Cloud Run API 활성화
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

## 배포 단계

### 1. Docker 이미지 빌드 및 푸시

```bash
# 프로젝트 ID 확인
PROJECT_ID=$(gcloud config get-value project)
echo "Project ID: $PROJECT_ID"

# Cloud Build로 이미지 빌드 및 푸시
gcloud builds submit --tag gcr.io/$PROJECT_ID/vocab-cat-api
```

### 2. Cloud Run 배포

#### 기본 배포 (SQLite)
```bash
gcloud run deploy vocab-cat-api \
  --image gcr.io/$PROJECT_ID/vocab-cat-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --set-env-vars ALLOWED_ORIGINS="https://your-frontend-domain.vercel.app" \
  --set-env-vars LOG_LEVEL="INFO" \
  --set-env-vars ENABLE_RATE_LIMITING="true"
```

#### Cloud SQL (PostgreSQL) 사용 시
```bash
# Cloud SQL 인스턴스 생성 (처음만)
gcloud sql instances create vocab-cat-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# 데이터베이스 생성
gcloud sql databases create vocab_cat --instance=vocab-cat-db

# 사용자 생성
gcloud sql users create vocab_admin \
  --instance=vocab-cat-db \
  --password=YOUR_SECURE_PASSWORD

# Cloud Run 배포 (Cloud SQL 연결)
gcloud run deploy vocab-cat-api \
  --image gcr.io/$PROJECT_ID/vocab-cat-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --add-cloudsql-instances $PROJECT_ID:us-central1:vocab-cat-db \
  --set-env-vars ALLOWED_ORIGINS="https://your-frontend-domain.vercel.app" \
  --set-env-vars DATABASE_URL="postgresql://vocab_admin:YOUR_SECURE_PASSWORD@/vocab_cat?host=/cloudsql/$PROJECT_ID:us-central1:vocab-cat-db" \
  --set-env-vars LOG_LEVEL="INFO" \
  --set-env-vars ENABLE_RATE_LIMITING="true"
```

#### Sentry 에러 추적 포함
```bash
gcloud run deploy vocab-cat-api \
  --image gcr.io/$PROJECT_ID/vocab-cat-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --set-env-vars ALLOWED_ORIGINS="https://your-frontend-domain.vercel.app" \
  --set-env-vars LOG_LEVEL="INFO" \
  --set-env-vars ENABLE_RATE_LIMITING="true" \
  --set-env-vars SENTRY_DSN="https://your-sentry-dsn@sentry.io/project-id" \
  --set-env-vars ENVIRONMENT="production" \
  --set-env-vars RELEASE_VERSION="0.2.0"
```

### 3. 배포 확인

```bash
# 서비스 URL 확인
gcloud run services describe vocab-cat-api \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)'

# Health check
SERVICE_URL=$(gcloud run services describe vocab-cat-api --platform managed --region us-central1 --format 'value(status.url)')
curl $SERVICE_URL/health

# Prometheus 메트릭 확인
curl $SERVICE_URL/metrics
```

### 4. 데이터베이스 마이그레이션 실행

Cloud SQL 사용 시 초기 마이그레이션:

```bash
# Cloud SQL Proxy 실행 (로컬)
cloud_sql_proxy -instances=$PROJECT_ID:us-central1:vocab-cat-db=tcp:5432

# 다른 터미널에서 마이그레이션 실행
cd irt_cat_engine
export DATABASE_URL="postgresql://vocab_admin:YOUR_SECURE_PASSWORD@localhost:5432/vocab_cat"
alembic upgrade head
```

## 업데이트 배포

코드 변경 후 재배포:

```bash
# 1. 새 이미지 빌드
gcloud builds submit --tag gcr.io/$PROJECT_ID/vocab-cat-api

# 2. Cloud Run 업데이트
gcloud run deploy vocab-cat-api \
  --image gcr.io/$PROJECT_ID/vocab-cat-api \
  --platform managed \
  --region us-central1
```

## 로그 확인

```bash
# 실시간 로그 스트리밍
gcloud run services logs tail vocab-cat-api \
  --platform managed \
  --region us-central1

# 최근 로그 조회
gcloud run services logs read vocab-cat-api \
  --platform managed \
  --region us-central1 \
  --limit 50
```

## 비용 최적화

### 최소 인스턴스 설정
```bash
gcloud run services update vocab-cat-api \
  --min-instances 0 \
  --max-instances 10 \
  --region us-central1
```

### 자동 스케일링 조정
```bash
gcloud run services update vocab-cat-api \
  --concurrency 80 \
  --region us-central1
```

## 트러블슈팅

### 배포 실패 시
```bash
# 빌드 로그 확인
gcloud builds list --limit 5

# 특정 빌드 로그 상세 확인
gcloud builds log BUILD_ID
```

### 메모리 부족 시
```bash
# 메모리 증가
gcloud run services update vocab-cat-api \
  --memory 4Gi \
  --region us-central1
```

### 느린 응답 시
```bash
# CPU 증가
gcloud run services update vocab-cat-api \
  --cpu 4 \
  --region us-central1
```

## 보안 강화

### 1. IAM 인증 활성화
```bash
gcloud run services update vocab-cat-api \
  --no-allow-unauthenticated \
  --region us-central1
```

### 2. VPC 연결 (Cloud SQL 보안)
```bash
gcloud run services update vocab-cat-api \
  --vpc-connector YOUR_VPC_CONNECTOR \
  --region us-central1
```

## 모니터링 설정

### Cloud Monitoring 대시보드
1. Google Cloud Console → Monitoring
2. Dashboards → Create Dashboard
3. 메트릭 추가:
   - Request count
   - Request latency
   - Error rate
   - Memory utilization
   - CPU utilization

### 알림 설정
```bash
# 에러율 5% 초과 시 알림
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Error Rate" \
  --condition-threshold-value=5 \
  --condition-threshold-duration=300s
```

## 배포 완료 후

1. ✅ Health check 확인: `$SERVICE_URL/health`
2. ✅ API 문서 확인: `$SERVICE_URL/docs`
3. ✅ 메트릭 확인: `$SERVICE_URL/metrics`
4. ✅ 프론트엔드에서 API URL 업데이트
5. ✅ Sentry에서 에러 모니터링 시작

---

**배포된 URL을 기록하고 프론트엔드 환경 변수에 설정하세요!**
