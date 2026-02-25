# IRT CAT Engine - 적응형 영어 어휘 진단 테스트

IRT(문항반응이론) 기반 CAT(컴퓨터 적응형 검사) 시스템으로, 9,183개 영어 단어 데이터베이스를 활용하여 한국 영어 학습자의 어휘력을 정밀 진단합니다.

## 개요

- **핵심 원리**: 2PL/3PL IRT 모델로 학습자 능력(theta)을 추정하고, Fisher 정보량 기반으로 최적 문항을 선택
- **문항 수**: 15~40문항 적응적 종료 (대부분 20~30문항 내에서 완료)
- **결과**: CEFR 레벨(A1~C1), 추정 어휘 크기, 교육과정 수준, 토픽별 강약점 진단
- **정밀도**: 10,000명 시뮬레이션 검증 — RMSE 0.327, 상관계수 0.975

## 기술 스택

| 계층 | 기술 |
|------|------|
| IRT 엔진 | Python 3.11+, NumPy, SciPy |
| 백엔드 API | FastAPI, SQLAlchemy, Pydantic |
| 데이터베이스 | SQLite (개발), PostgreSQL 전환 가능 |
| 프론트엔드 | React 19, TypeScript, Vite |
| 테스트 | pytest (71개 테스트) |

## 프로젝트 구조

```
irt_cat_engine/
├── models/                     # IRT 수리 모델
│   ├── irt_2pl.py              # 2PL/3PL 확률, Fisher 정보량, 로그우도
│   └── ability_estimator.py    # EAP/MLE 능력 추정
├── cat/                        # 적응형 테스트 로직
│   ├── session.py              # CAT 세션 오케스트레이터
│   ├── item_selector.py        # 문항 선택 (최대 정보량 + 내용 균형 + 노출 제어)
│   └── stopping_rules.py       # 종료 기준 (SE 임계치, 수렴, 최대 문항)
├── item_bank/                  # 문항 은행
│   ├── parameter_initializer.py # 난이도(b), 변별도(a), 추측(c) 초기화
│   ├── distractor_engine.py    # 오답지 생성 (4가지 전략)
│   └── calibrator.py           # Bayesian 온라인 파라미터 보정
├── reporting/                  # 결과 보고
│   ├── score_mapper.py         # theta → CEFR, 교육과정, 어휘크기 매핑
│   ├── item_fit.py             # 문항 적합도 분석 (infit/outfit MNSQ)
│   └── exposure_analysis.py    # 문항 노출 분석 및 풀 확장 필요 분석
├── data/                       # 데이터 계층
│   ├── load_vocabulary.py      # 9,183 단어 TSV 로더 (데이터 정제 포함)
│   ├── topic_mapper.py         # 3,295개 토픽 → 29개 카테고리 통합
│   ├── graph_connector.py      # vocabulary_graph.json 그래프 DB 연결
│   ├── database.py             # SQLAlchemy 엔진/세션
│   └── db_models.py            # ORM 모델 (User, TestSession, Response)
├── api/                        # REST API
│   ├── main.py                 # FastAPI 앱 (CORS, 라이프사이클)
│   ├── routes_test.py          # 테스트 세션 API
│   ├── routes_admin.py         # 관리자 API (보정, 노출 분석)
│   ├── schemas.py              # Pydantic 요청/응답 모델
│   └── session_manager.py      # 인메모리 세션 관리 (Redis 전환 가능)
├── frontend/                   # React 프론트엔드
│   └── src/
│       ├── App.tsx             # 메인 상태 머신 (설문 → 테스트 → 결과)
│       ├── components/         # SurveyScreen, TestScreen, ResultsScreen
│       ├── i18n/               # 한국어/영어 번역 시스템
│       ├── hooks/useApi.ts     # API 호출 헬퍼
│       └── types/api.ts        # TypeScript 인터페이스
├── config.py                   # 전체 설정 상수
├── tests/                      # 테스트 (71개)
└── requirements.txt            # Python 의존성
```

## 설치 및 실행

### 1. Python 백엔드 설치

```bash
cd irt_cat_engine
pip install -r requirements.txt
```

### 2. 백엔드 서버 실행

```bash
# 프로젝트 루트(vocabulary-db/)에서 실행
uvicorn irt_cat_engine.api.main:app --reload --host 0.0.0.0 --port 8000
```

서버 시작 시 9,183개 단어 데이터 로딩 (약 5~10초). 로딩 완료 후 API 사용 가능.

- API 문서: http://localhost:8000/docs (Swagger UI)
- 헬스 체크: http://localhost:8000/health
- 메트릭: http://localhost:8000/metrics (Prometheus)

### 문항 생성 점수 메트릭 기록 (루프 코드에서 호출)

문항 생성 루프(별도 워커/스크립트)에서 아래 헬퍼를 호출하면 점수/채택률/난이도 오차를 Prometheus로 수집할 수 있습니다.

```python
from irt_cat_engine.middleware.metrics import record_item_generation

# 문항 1개 생성 완료 시
record_item_generation(
  score=87.5,
  accepted=True,
  stage="final",       # draft/review/final
  model="gpt-4.1-mini",# 모델명(소수 고정값만 권장)
  exam_type="csat",
  target_difficulty=0.8,
  actual_difficulty=1.1,
)
```

생성되는 주요 메트릭:

- `item_generation_score` (Histogram)
- `item_generation_target_gap` (Histogram)
- `item_generation_accepted_total` (Counter)
- `item_generation_rejected_total` (Counter)

### 3. 프론트엔드 설치 및 실행

```bash
cd irt_cat_engine/frontend
npm install
npm run dev
```

브라우저에서 http://localhost:5173 접속.

### 4. 테스트 실행

```bash
# 프로젝트 루트에서
python -m pytest irt_cat_engine/tests/ -v

# 10K 시뮬레이션 포함 (약 3분 소요)
python -m pytest irt_cat_engine/tests/test_large_simulation.py -v -s
```

## 사용 흐름

### 웹 UI 사용

1. **사전 설문** — 학년, 자기평가 수준, 시험 경험 선택
2. **적응형 테스트** — 4지선다 문항에 답변 (15~40문항)
   - 정답이면 더 어려운 문항, 오답이면 더 쉬운 문항이 출제
   - 진행 상황 (문항 번호, 정답률, CEFR 레벨) 실시간 표시
3. **결과 확인** — CEFR 레벨, 추정 어휘 크기, 토픽별 강약점

### API 직접 사용

```bash
# 1. 테스트 시작
curl -X POST http://localhost:8000/api/v1/test/start \
  -H "Content-Type: application/json" \
  -d '{"grade": "중2", "self_assess": "intermediate", "question_type": 1}'

# 응답: { session_id, first_item, progress, ... }

# 2. 응답 제출 (반복)
curl -X POST http://localhost:8000/api/v1/test/{session_id}/respond \
  -H "Content-Type: application/json" \
  -d '{"item_id": 123, "is_correct": true, "response_time_ms": 3500}'

# 응답: { next_item, progress, ... } 또는 { is_complete: true, results }

# 3. 결과 조회
curl http://localhost:8000/api/v1/test/{session_id}/results

# 4. 사용자 이력
curl http://localhost:8000/api/v1/user/{user_id}/history
```

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/api/v1/test/start` | 새 테스트 세션 시작 |
| `POST` | `/api/v1/test/{id}/respond` | 응답 제출, 다음 문항 수신 |
| `GET` | `/api/v1/test/{id}/results` | 완료된 테스트 결과 조회 |
| `GET` | `/api/v1/user/{id}/history` | 사용자 테스트 이력 |
| `GET` | `/api/v1/admin/stats` | 서버 통계 |
| `GET` | `/api/v1/admin/exposure` | 문항 노출 분석 리포트 |
| `GET` | `/api/v1/admin/exposure/expansion` | 풀 확장 필요 영역 분석 |
| `POST` | `/api/v1/admin/recalibrate` | 파라미터 재보정 |
| `POST` | `/api/v1/admin/cleanup` | 만료 세션 정리 |

## 핵심 알고리즘

### IRT 2PL/3PL 모델

```
P(정답|θ) = c + (1-c) / (1 + exp(-a × (θ - b)))
```

- **θ (theta)**: 학습자 능력 (-3 ~ +3)
- **b**: 문항 난이도 — CEFR, 빈도등급, GSE, 교육과정, Lexile 가중 합산으로 초기화
- **a**: 문항 변별도 — 교육적 가치, POS, 동의어 수, 토픽 특이성으로 초기화
- **c**: 추측 파라미터 — 3PL 모드에서만 활성 (4지선다: 0.20, 이진: 0.40)

### 능력 추정: EAP (Expected A Posteriori)

- 사전분포 N(0, 1)에 대해 41포인트 구적법으로 사후분포 계산
- MLE와 달리 전부 정답/오답 시에도 유한한 추정값 보장

### 문항 선택

1. 내용 제약 필터 (토픽 최대 3회, POS 비율, 문항 유형 진행)
2. Sympson-Hetter 노출 제어 (최대 노출률 25%)
3. Fisher 정보량 계산: `I(θ) = a² × P × Q`
4. 상위 5문항 중 랜덤 선택 (다양성 확보)

### 종료 기준

| 기준 | 값 |
|------|-----|
| 표준오차(SE) 임계치 | SE < 0.30 |
| 최소 문항 수 | 15문항 |
| 최대 문항 수 | 40문항 |
| 능력 추정 수렴 | 5연속 Δθ < 0.05 |

### 문항 유형 (6종)

| 유형 | 설명 | 커버리지 |
|------|------|---------|
| Type 1 | 한국어 뜻 고르기 | 9,183 (100%) |
| Type 2 | 영어 정의 매칭 | 9,183 (100%) |
| Type 3 | 동의어 선택 | 7,896 (86%) |
| Type 4 | 반의어 선택 | 4,987 (54%) |
| Type 5 | 문장 빈칸 채우기 | 9,183 (100%) |
| Type 6 | 연어 판단 | 9,121 (99%) |

### 오답지 생성 전략

- **Strategy A**: 같은 POS + 인접 CEFR + 같은 토픽, 동의어 제외
- **Strategy B**: 동의어 문항용 — 정답은 동의어, 오답은 비-동의어
- **Strategy C**: 반의어 문항용 — 그래프 기반 형제어 + 폴백
- **Strategy D**: `vocabulary_graph.json` 기반 — hypernym 공유 형제어

## 결과 해석

### CEFR 레벨 매핑

| theta 범위 | CEFR | 설명 |
|-----------|------|------|
| -3.0 ~ -1.5 | A1 | 기초 학습자 |
| -1.5 ~ -0.5 | A2 | 초급 |
| -0.5 ~ +0.5 | B1 | 중급 |
| +0.5 ~ +1.5 | B2 | 중상급 |
| +1.5 ~ +3.0 | C1 | 고급 |

### 교육과정 수준 매핑

| theta 범위 | 수준 |
|-----------|------|
| < -0.8 | 초등 수준 |
| -0.8 ~ 0.3 | 중등 수준 |
| 0.3 ~ 1.2 | 고등 수준 |
| > 1.2 | 고등 이상 |

### 추정 어휘 크기

전체 9,183 단어에 대해 `P(정답|θ)` 합산 → 예상 어휘 수.

## 설정 변경

주요 설정은 [config.py](config.py)에서 변경:

```python
IRT_MODEL = "2PL"           # "3PL"로 변경 시 추측 파라미터 활성화
CAT_MIN_ITEMS = 15          # 최소 문항 수
CAT_MAX_ITEMS = 40          # 최대 문항 수
CAT_SE_THRESHOLD = 0.30     # SE 종료 임계치 (낮을수록 정밀, 문항 수 증가)
CAT_MAX_EXPOSURE_RATE = 0.25 # Sympson-Hetter 최대 노출률
MIN_SESSIONS_FOR_3PL = 5000 # 3PL 활성화에 필요한 최소 누적 세션 수
```

## 데이터 요구사항

루트 디렉토리에 다음 파일이 필요합니다:

- **`9000word_full_db.csv`** — 9,183단어 마스터 DB (58컬럼, TSV)
- **`07_Graph_DB_Project/vocabulary_graph.json`** — 어휘 관계 그래프 (선택사항, Strategy D용)

## 검증 결과

### 10,000명 시뮬레이션

| 지표 | 결과 | 목표 |
|------|------|------|
| RMSE | 0.327 | < 0.45 |
| 상관계수 | 0.975 | > 0.92 |
| 평균 SE | 0.30 | < 0.35 |
| 조기 종료율 | 65.8% | > 50% |

### 능력 범위별 정밀도

| 범위 | n | RMSE | 평균 문항 |
|------|---|------|----------|
| Low (-2.5~-1.5) | ~2,000 | 0.356 | 38.0 |
| Below Avg (-1.5~-0.5) | ~2,000 | 0.296 | 34.4 |
| Average (-0.5~0.5) | ~2,000 | 0.287 | 33.8 |
| Above Avg (0.5~1.5) | ~2,000 | 0.311 | 35.9 |
| High (1.5~2.5) | ~2,000 | 0.377 | 38.3 |
