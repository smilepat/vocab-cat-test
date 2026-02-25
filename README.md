# IRT CAT Engine - Adaptive Vocabulary Diagnostic Test

![Version](https://img.shields.io/badge/version-0.2.0-blue)
![Python](https://img.shields.io/badge/python-3.13+-green)
![React](https://img.shields.io/badge/react-19.2-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 소개

**IRT CAT Engine**은 문항반응이론(Item Response Theory)과 컴퓨터 적응 검사(Computerized Adaptive Testing)를 활용한 영어 어휘 진단 시스템입니다.

### 주요 특징

- 📊 **적응형 테스트**: 15-40문항으로 100문항 고정형 검사와 동일한 정확도
- 🎯 **정밀 진단**: IRT 2PL/3PL 모델 기반 능력 측정 (θ)
- 📈 **5차원 분석**: 의미, 관계, 맥락, 형태, 화용 영역별 어휘 능력 평가
- 🌐 **CEFR 매핑**: A1-C1 레벨 자동 판정 및 확률 분포 제공
- 📚 **9,183단어**: 58개 메타데이터 컬럼으로 구성된 방대한 어휘 데이터베이스
- 🔄 **실시간 적응**: Fisher Information 기반 최적 문항 선택
- 📱 **반응형 UI**: React 19 기반 모바일/데스크톱 지원

---

## 기술 스택

### Backend
- **Python 3.13+**: FastAPI, NumPy, SciPy, SQLAlchemy
- **Database**: SQLite (dev), PostgreSQL (production)
- **Migration**: Alembic
- **Testing**: pytest (162 tests, 100% pass)

### Frontend
- **React 19**: TypeScript, Vite
- **Styling**: CSS Modules
- **i18n**: Korean/English 지원

### DevOps
- **Docker**: 컨테이너화 배포
- **Docker Compose**: PostgreSQL 통합 개발 환경
- **Cloud Run**: Production 배포
- **Vercel**: 프론트엔드 호스팅

---

## 빠른 시작

### 1. 의존성 설치

#### 백엔드
```bash
cd irt_cat_engine
pip install -r requirements.txt
```

#### 프론트엔드
```bash
cd irt_cat_engine/frontend
npm install
```

### 2. 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 편집 (ALLOWED_ORIGINS 등 설정)
```

### 3. 로컬 실행

#### 백엔드
```bash
cd irt_cat_engine
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs

#### 프론트엔드
```bash
cd irt_cat_engine/frontend
npm run dev
```
- Dev Server: http://localhost:5173

### 4. Docker Compose (권장)

PostgreSQL 포함 전체 스택 실행:

```bash
docker-compose up -d
```

서비스:
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- PostgreSQL: localhost:5432

---

## 프로젝트 구조

```
vocab-cat-test/
├── 9000word_full_db.csv              # 어휘 데이터베이스 (9,183 단어)
├── vocabulary_graph.json             # 단어 관계 그래프 (48MB)
├── Dockerfile                        # 백엔드 Docker 이미지
├── docker-compose.yml                # 전체 스택 구성
├── .env.example                      # 환경 변수 템플릿
├── DEPLOYMENT.md                     # 배포 가이드
│
└── irt_cat_engine/
    ├── alembic/                      # DB 마이그레이션
    ├── models/                       # IRT 수학 모델
    ├── cat/                          # CAT 엔진
    ├── item_bank/                    # 문항 관리
    ├── data/                         # 데이터 로딩
    ├── reporting/                    # 진단 보고서
    ├── api/                          # REST API
    │   ├── main.py                   # FastAPI 앱
    │   ├── routes_test.py            # 테스트 엔드포인트
    │   ├── routes_admin.py           # 관리 엔드포인트
    │   └── schemas.py                # Pydantic 스키마
    │
    ├── frontend/                     # React 프론트엔드
    │   ├── src/
    │   │   ├── components/           # React 컴포넌트
    │   │   ├── utils/                # 유틸리티 (API 재시도 등)
    │   │   └── i18n/                 # 다국어 지원
    │   └── package.json
    │
    ├── tests/                        # 테스트 (162개)
    └── requirements.txt              # Python 의존성
```

---

## API 엔드포인트

### 테스트 관련
- `POST /api/v1/test/start` - 새 테스트 세션 시작
- `POST /api/v1/test/{id}/respond` - 응답 제출 및 다음 문항
- `GET /api/v1/test/{id}/results` - 진단 결과 조회
- `GET /api/v1/user/{id}/history` - 사용자 테스트 이력

### 학습 지원
- `GET /api/v1/learn/{id}/plan` - 4주 학습 계획
- `GET /api/v1/learn/{id}/matrix` - 어휘 지식 상태 매트릭스

### 시스템
- `GET /health` - 상세 헬스 체크
- `GET /ready` - Kubernetes 준비 상태 프로브
- `GET /api/v1/admin/stats` - 통계

전체 API 문서: http://localhost:8000/docs

---

## 테스트

### 백엔드 테스트

```bash
cd irt_cat_engine
pytest tests/ -v
```

**결과**: 162 tests, 100% pass in 260.60s

### 프론트엔드 빌드

```bash
cd irt_cat_engine/frontend
npm run build
```

---

## 배포

상세한 배포 가이드는 [DEPLOYMENT.md](DEPLOYMENT.md)를 참조하세요.

### 간단 요약

#### Google Cloud Run (백엔드)
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/vocab-cat-api
gcloud run deploy vocab-cat-api --image gcr.io/PROJECT_ID/vocab-cat-api
```

#### Vercel (프론트엔드)
```bash
cd irt_cat_engine/frontend
vercel --prod
```

---

## 환경 변수

주요 환경 변수 (전체 목록은 `.env.example` 참조):

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `DATABASE_URL` | 데이터베이스 연결 URL | `sqlite:///...` |
| `ALLOWED_ORIGINS` | CORS 허용 도메인 | `http://localhost:5173,...` |
| `LOG_LEVEL` | 로그 레벨 | `INFO` |
| `VITE_API_BASE` | 프론트엔드 API URL | `http://localhost:8000/api/v1` |

---

## 라이선스

MIT License

---

## 기여

이슈 및 풀 리퀘스트를 환영합니다!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 연락처

프로젝트 관련 문의: [GitHub Issues](https://github.com/yourusername/vocab-cat-test/issues)

---

**🤖 Powered by IRT & CAT**
