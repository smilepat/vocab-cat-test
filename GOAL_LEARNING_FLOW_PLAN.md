# 목표 기반 어휘 학습 플로우 계획

## 📋 개요

"학습 진행" 버튼을 누르면 진단 테스트 없이 선택한 학습 목표(초등/중학/고등/수능 어휘)에 맞는 단어들을 플래시카드 방식으로 학습하게 됩니다.

---

## 🎯 학습 목표별 전략

### 1. 초등 어휘 (800단어)
**대상**: Elementary 3-4, 5-6 교육과정
**학습 전략**: 기본 인지 중심
- **첫 노출**: 60% 한글 뜻 (Type 1), 20% 유의어 (Type 3), 20% 문장 완성 (Type 5)
- **복습**: 40% Type 1, 30% Type 3, 20% Type 4, 10% Type 5
- **마스터**: 40% Type 3, 30% Type 4, 30% Type 5

### 2. 중학교과 어휘 (1,200단어)
**대상**: Middle School 1-3 교육과정
**학습 전략**: 관계어 이해 강화
- **첫 노출**: 40% Type 1, 30% Type 3, 20% Type 5, 10% Type 6
- **복습**: 30% Type 1, 25% Type 3, 20% Type 4, 15% Type 5, 10% Type 6
- **마스터**: 균등 분배 (Types 2, 3, 4, 5, 6 각 20%)

### 3. 고등학교 어휘 (1,000단어)
**대상**: High School 1-3 교육과정
**학습 전략**: 깊이 있는 이해
- **첫 노출**: 30% Type 1, 30% Type 3, 30% Type 5, 10% Type 6
- **복습**: 각 Type 20% 균등 분배
- **마스터**: 25% Type 2, 15% Type 3/4, 25% Type 5, 20% Type 6

### 4. 수능 어휘 (5,000단어)
**대상**: High School + University 교육과정
**학습 전략**: 종합 마스터
- **첫 노출**: 30% Type 1, 10% Type 2, 20% Type 3, 30% Type 5, 10% Type 6
- **복습**: 모든 Type 균등 (각 20%)
- **마스터**: 30% Type 2/5, 10% Type 3/4, 20% Type 6

---

## 🔄 학습 사이클

### Phase 1: 첫 노출 (First Exposure)
```
사용자 액션: 학습 진행 버튼 클릭
         ↓
시스템: 학습 세션 생성
         ↓
시스템: 학습 목표에 맞는 새 단어 선택
         ↓
시스템: "첫 노출" 문항 유형 선택 (목표별 분포)
         ↓
화면: 플래시카드 표시
         ↓
사용자: 답 확인 → 자기 평가 (몰랐어요/어려웠어요/좋아요/쉬웠어요)
         ↓
시스템: SM-2 알고리즘으로 복습 일정 계산
         ↓
시스템: 다음 단어 표시
```

### Phase 2: 복습 (Review)
```
사용자 액션: 학습 진행 (복습 단어 있음)
         ↓
시스템: 복습 시간이 된 단어 우선 선택
         ↓
시스템: "복습" 문항 유형 선택 (더 어려운 유형)
         ↓
화면: 플래시카드 표시
         ↓
사용자: 자기 평가
         ↓
시스템: SM-2로 다음 복습 일정 재계산
  - 몰랐어요(0): 바로 다시 복습
  - 어려웠어요(1): 1일 후
  - 좋아요(2): 현재 간격 × 2.5배
  - 쉬웠어요(3): 현재 간격 × 3.25배
```

### Phase 3: 마스터 (Mastery)
```
조건: 5회 이상 복습 + 80% 이상 정답률 + 7일 이상 간격
         ↓
시스템: 단어를 "마스터" 상태로 변경
         ↓
진행률: words_mastered 카운트 증가
         ↓
완료 조건: 목표 단어 수만큼 마스터 달성
```

---

## 📊 학습 화면 구성

### 상단: 진행률 표시
```
┌─────────────────────────────────────────┐
│ 초등 어휘                        나가기 │
├─────────────────────────────────────────┤
│ 진행률: 25.5% (마스터: 204/800)        │
│ [████████░░░░░░░░░░░░░░░░░░░░░]         │
│ 학습한 단어: 312 | 복습 횟수: 847      │
└─────────────────────────────────────────┘
```

### 중앙: 플래시카드
```
┌─────────────────────────────────────────┐
│ [새 단어]  DVK 레벨 1        B1 · n.   │
├─────────────────────────────────────────┤
│                                         │
│  I need to _____ my homework.          │
│                                         │
│  ○ finish                              │
│  ○ start                               │
│  ○ forget                              │
│  ○ lose                                │
│                                         │
│         [답 확인하기]                   │
└─────────────────────────────────────────┘
```

### 하단: 자기 평가 (답 확인 후)
```
┌─────────────────────────────────────────┐
│ 이 단어를 얼마나 잘 기억하시나요?       │
├─────────────────────────────────────────┤
│ [❌ 몰랐어요] [🤔 어려웠어요]          │
│ [✅ 좋아요]   [💯 쉬웠어요]            │
└─────────────────────────────────────────┘
```

---

## 🧠 DVK (Depth of Vocabulary Knowledge) 진행

### Level 1: Recognition (인지)
- **문항**: Type 1 (한글 뜻 매칭)
- **능력**: 단어를 봤을 때 뜻을 안다
- **예시**: "finish" → "끝내다"

### Level 2: Recall (회상)
- **문항**: Type 2 (영어 정의 매칭)
- **능력**: 단어의 의미를 영어로 이해
- **예시**: "finish" → "to complete something"

### Level 3: Association (연상)
- **문항**: Type 3, 4 (유의어/반의어)
- **능력**: 관련 단어들을 연결
- **예시**: "finish" ↔️ complete, start

### Level 4: Collocation (연어)
- **문항**: Type 6 (연어 판단)
- **능력**: 함께 쓰이는 단어 조합
- **예시**: "finish homework" ✓, "finish cat" ✗

### Level 5: Usage (사용)
- **문항**: Type 5 (문장 완성)
- **능력**: 문맥에서 적절히 사용
- **예시**: "I need to _____ my homework."

### Level 6: Production (산출)
- **구현 예정**: 작문 과제
- **능력**: 자유롭게 문장 생성

---

## 📈 학습 우선순위 알고리즘

```python
def get_next_word():
    # 우선순위 1: 복습 시간이 된 단어 (due for review)
    due_words = filter(lambda w: w.next_review_at <= now, learned_words)
    if due_words:
        return oldest_due_word(due_words)

    # 우선순위 2: 새 단어 (학습 목표 내)
    unstudied_words = filter(lambda w: w not in learned_words, goal_words)
    if unstudied_words:
        return random.choice(unstudied_words)

    # 우선순위 3: 마스터 안 된 단어 복습
    non_mastered = filter(lambda w: not w.is_mastered, learned_words)
    if non_mastered:
        return least_recently_reviewed(non_mastered)

    # 모든 단어 마스터 완료!
    return None
```

---

## 🎓 자기 평가 → SM-2 알고리즘 매핑

| 자기 평가 | 점수 | Ease Factor | 다음 간격 | 설명 |
|----------|------|-------------|-----------|------|
| ❌ 몰랐어요 | 0 | -0.2 | 즉시 | 바로 다시 학습 |
| 🤔 어려웠어요 | 1 | -0.15 | 간격 × 1.2 | 짧은 간격 복습 |
| ✅ 좋아요 | 2 | 유지 | 간격 × EF | 정상 진행 |
| 💯 쉬웠어요 | 3 | +0.15 | 간격 × EF × 1.3 | 간격 확장 |

**Ease Factor (EF)**:
- 초기값: 2.5
- 최소값: 1.3 (너무 낮아지지 않도록)
- 범위: 1.3 ~ 무한대

**첫 복습 간격**:
- 몰랐어요/어려웠어요: 1일
- 좋아요: 1일
- 쉬웠어요: 4일

---

## 🏆 마스터 조건

단어가 "마스터" 상태로 변경되는 조건:

```
✓ 복습 횟수 ≥ 5회
  AND
✓ 정답률 ≥ 80%
  AND
✓ 복습 간격 ≥ 7일
```

**효과**:
- `is_mastered = True` 플래그 설정
- `mastered_at` 타임스탬프 기록
- `words_mastered` 카운트 증가
- 진행률 바 업데이트

---

## 🔄 데이터 흐름

### 1. 학습 시작
```
POST /api/v1/learn/goal/start
{
  "goal_id": "elementary",
  "goal_name": "초등 어휘",
  "target_word_count": 800,
  "nickname": "학습자"
}

→ Response:
{
  "session_id": "abc123",
  "user_id": "user456",
  "first_card": {
    "word": "finish",
    "question_type": 1,
    "stem": "다음 단어의 뜻은?",
    "correct_answer": "끝내다",
    "options": ["끝내다", "시작하다", "잊다", "잃다"],
    "dvk_level": 1,
    "is_first_exposure": true
  }
}
```

### 2. 답안 제출
```
POST /api/v1/learn/goal/{session_id}/submit
{
  "word": "finish",
  "question_type": 1,
  "self_rating": 2,  // 0-3
  "is_correct": true,
  "response_time_ms": 3500
}

→ Response:
{
  "next_card": { ... },  // 다음 학습 카드
  "session_progress": {
    "words_studied": 1,
    "words_mastered": 0,
    "total_reviews": 1,
    "target_word_count": 800,
    "completion_percentage": 0.0
  }
}
```

### 3. 진행률 조회
```
GET /api/v1/learn/goal/{session_id}/progress

→ Response:
{
  "words_studied": 312,
  "words_mastered": 204,
  "total_reviews": 847,
  "target_word_count": 800,
  "completion_percentage": 25.5
}
```

---

## 🎯 완료 조건

### 세션 완료
```
if (words_mastered >= target_word_count):
    show_completion_message()
    display_statistics()
    offer_next_goal()
```

### 완료 통계
```
┌─────────────────────────────────────────┐
│          🎉 축하합니다!                 │
│     초등 어휘 800단어 마스터 완료!      │
├─────────────────────────────────────────┤
│ 총 학습 기간: 45일                      │
│ 총 복습 횟수: 2,847회                   │
│ 평균 정답률: 87.3%                      │
│ 평균 복습 간격: 12.5일                  │
├─────────────────────────────────────────┤
│ [다음 목표 시작] [홈으로]              │
└─────────────────────────────────────────┘
```

---

## 📱 사용자 경험 플로우

### 시나리오 1: 완전 초보 학습자
```
Day 1:
- 새 단어 20개 학습 (모두 "몰랐어요" 선택)
- 즉시 재학습 → 대부분 "어려웠어요"로 개선
- 1일 후 복습 예약

Day 2:
- 어제 학습한 20개 복습
- 10개는 "좋아요", 10개는 "어려웠어요"
- 새 단어 15개 추가 학습

Day 7:
- 누적 100개 학습
- 30개 마스터 달성
- 진행률: 3.75%
```

### 시나리오 2: 중급 학습자
```
Day 1:
- 새 단어 50개 빠르게 학습
- 30개 "쉬웠어요", 15개 "좋아요", 5개 "어려웠어요"

Day 4:
- "쉬웠어요" 단어들 복습 (간격 4일)
- 대부분 다시 "쉬웠어요" → 간격 13일로 확장

Day 14:
- 누적 300개 학습
- 150개 마스터 달성
- 진행률: 18.75%
```

---

## 🔧 기술 구현 세부사항

### Database Schema
```sql
-- 학습 세션
goal_learning_sessions
- id (PK)
- user_id (FK)
- goal_id (elementary/middle/high/suneung)
- target_word_count
- words_studied
- words_mastered
- total_reviews
- started_at, last_activity_at

-- 학습 단어
learned_words
- id (PK)
- session_id (FK)
- word
- dvk_level (1-6)
- review_count
- correct_count
- next_review_at
- ease_factor (SM-2)
- interval_days (SM-2)
- is_mastered
- assessment_history (JSON)
```

### Frontend State Management
```typescript
interface GoalLearningState {
  sessionId: string;
  goalName: string;
  targetWordCount: number;
  currentCard: LearningCard | null;
  progress: GoalSessionProgress;
  loading: boolean;
}
```

### Backend Service Logic
```python
# 단어 선택 로직
get_next_word_to_learn(session_id, vocab_words)
  → (word_data, question_type, is_first_exposure)

# 문항 유형 선택
select_question_type_for_word(goal_id, learning_stage)
  → question_type (1-6)

# 답안 처리
submit_learning_card(session_id, word, self_rating, is_correct)
  → updated LearnedWord with new review schedule
```

---

## 🎨 UI/UX 개선 계획 (Future)

### Phase 2: 추가 기능
- [ ] 일일 학습 목표 설정 (예: 하루 20단어)
- [ ] 학습 스트릭 (연속 학습 일수)
- [ ] 배지 시스템 (마일스톤 달성)
- [ ] 학습 통계 대시보드
- [ ] 단어장 북마크 기능

### Phase 3: 고급 기능
- [ ] 음성 발음 듣기
- [ ] 예문 문장 듣기 (TTS)
- [ ] 단어 이미지 연상 학습
- [ ] 친구와 학습 진행률 비교
- [ ] 주간/월간 학습 리포트

---

## 📊 성공 지표 (Metrics)

### 학습 효과 지표
- **완료율**: words_mastered / target_word_count
- **평균 마스터 소요일**: avg(mastered_at - first_seen_at)
- **복습 효율**: correct_count / review_count
- **학습 지속성**: days_active / total_days

### 사용자 참여 지표
- **일일 활성 사용자 (DAU)**
- **세션 길이**: avg(session_duration)
- **일일 학습 단어 수**: avg(words_per_day)
- **이탈률**: users_quit / users_started

---

## 🚀 런칭 체크리스트

- [✅] Backend API 구현
- [✅] Frontend UI 구현
- [✅] Database 모델 생성
- [✅] DVK 문항 분포 설정
- [✅] SM-2 알고리즘 구현
- [✅] 마스터 조건 로직
- [ ] 사용자 테스트
- [ ] 성능 최적화
- [ ] 에러 처리 강화
- [ ] 배포 준비

---

**작성일**: 2026-02-26
**버전**: 1.0
**상태**: Phase 1 구현 완료, 테스트 준비 중
