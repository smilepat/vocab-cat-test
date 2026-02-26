# Depth of Vocabulary Knowledge (DVK) 문항 유형 구현 계획

**Date**: 2026-02-26
**Project**: vocab-cat-test
**Purpose**: 학습 목표 기반 학습에서 다양한 DVK 측정 문항 활용 방안

---

## 📊 현재 시스템 분석

### 기존 문항 유형 (6가지)

| Type | 문항 형식 | Dimension | 난이도 | DVK Depth |
|------|-----------|-----------|--------|-----------|
| **1** | 한국어 뜻 고르기 | Semantic | +0.0 | **Shallow** (Recognition) |
| **2** | 영어 정의 매칭 | Semantic | +0.6 | **Medium** (Comprehension) |
| **3** | 유의어 선택 | Relational | +0.2 | **Medium** (Association) |
| **4** | 반의어 선택 | Relational | +0.3 | **Medium** (Association) |
| **5** | 문장 빈칸 채우기 | Contextual | +0.5 | **Deep** (Production) |
| **6** | 연어 판단 | Contextual | +0.2 | **Medium** (Collocation) |

### 5D Vocabulary Dimensions

1. **Semantic** (의미 이해): Types 1, 2
2. **Relational** (관계어): Types 3, 4
3. **Contextual** (문맥 사용): Types 5, 6
4. **Form** (형태 변환): ⚠️ **현재 없음**
5. **Pragmatic** (화용 맥락): ⚠️ **현재 없음**

---

## 🎯 DVK (Depth of Vocabulary Knowledge) 이론

### Nation (2001) - Vocabulary Knowledge Framework

```
┌─────────────────────────────────────────────────────┐
│                 Word Knowledge                      │
├─────────────────────────────────────────────────────┤
│ 1. Form          │ - Spoken form (발음)           │
│                  │ - Written form (철자)          │
│                  │ - Word parts (형태소)          │
├─────────────────────────────────────────────────────┤
│ 2. Meaning       │ - Concept (개념)               │
│                  │ - Referents (지시 대상)        │
│                  │ - Associations (연상)          │
├─────────────────────────────────────────────────────┤
│ 3. Use           │ - Grammatical functions (문법) │
│                  │ - Collocations (연어)          │
│                  │ - Constraints (제약)           │
└─────────────────────────────────────────────────────┘
```

### DVK Levels (깊이 수준)

| Level | Knowledge Type | Assessment | Examples |
|-------|---------------|------------|----------|
| **1. Recognition** | 단어를 봤을 때 안다 | 한국어 뜻 고르기 | Type 1 |
| **2. Recall** | 단어의 의미를 기억 | 영어 정의 매칭 | Type 2 |
| **3. Association** | 관련어를 안다 | 유의어/반의어 | Types 3, 4 |
| **4. Collocation** | 함께 쓰는 단어 안다 | 연어 판단 | Type 6 |
| **5. Usage** | 문맥에서 사용 가능 | 문장 완성 | Type 5 |
| **6. Production** | 자유롭게 산출 가능 | 작문 (미구현) | - |

---

## 🆕 추가 필요 문항 유형

### Type 7: Word Formation (형태 변환) - Form Dimension

**목적**: 파생어, 굴절, 품사 변환 지식 측정

#### 7-1. 품사 변환
```
문제: Choose the correct form to complete the sentence.
"The scientist made an important ________ in cancer research."

A) discover
B) discovery ✓
C) discovering
D) discovered
```

#### 7-2. 파생어 인식
```
문제: Which word is NOT derived from "create"?
A) creative
B) creation
C) creature ✓
D) creator
```

#### 7-3. 접두사/접미사
```
문제: "un-" + "happy" = ?
A) unhappy ✓
B) dishappy
C) inhappy
D) nonhappy
```

**데이터 필요**:
- `word_family` 필드 활용 (이미 있음!)
- 파생어 관계 DB
- 품사별 변환 규칙

---

### Type 8: Pragmatic Usage (화용 맥락) - Pragmatic Dimension

**목적**: 격식성, 상황별 사용, 문화적 맥락 이해 측정

#### 8-1. Register (격식성)
```
문제: Which word is more FORMAL?
Context: Writing a business email to your boss

A) ask
B) request ✓
C) wanna know
D) beg
```

#### 8-2. Situational Appropriateness
```
문제: Best word to use when meeting someone for the first time?
A) Hey
B) Yo
C) Nice to meet you ✓
D) What's up
```

**데이터 필요**:
- `register` 필드 활용 (formal/informal/casual)
- 상황별 사용 예시
- 문화적 함의 데이터

---

### Type 9: Phonological Knowledge (발음 지식)

**목적**: 발음 규칙, 강세, 소리 인식

#### 9-1. 발음 유사성
```
문제: Which word rhymes with "cat"?
A) hat ✓
B) car
C) cut
D) cake
```

#### 9-2. 강세 위치
```
문제: Where is the stress in "photograph"?
A) PHO-to-graph ✓
B) pho-TO-graph
C) pho-to-GRAPH
D) Equal stress
```

**데이터 필요**:
- `ipa` 필드 활용
- 음절 분리 데이터
- 발음 규칙 DB

---

### Type 10: Morphological Awareness (형태소 인식)

**목적**: 접두사, 접미사, 어근 분해 능력

```
문제: Break down "uncomfortable" into morphemes:
A) un- + comfort + -able ✓
B) uncomfort + -able
C) un- + com- + fort + -able
D) Cannot be broken down
```

**데이터 필요**:
- `morpheme` 필드 활용
- 어근 DB
- 접사 목록

---

### Type 11: Connotation (함축 의미)

**목적**: 긍정/부정 뉘앙스, 감정 색채

```
문제: Which word has a NEGATIVE connotation?
A) slender
B) thin
C) skinny ✓
D) slim
```

**데이터 필요**:
- 감정 극성 DB
- 뉘앙스 차이 설명

---

### Type 12: Multi-meaning (다의어)

**목적**: 동형이의어, 다의어 구분

```
문제: "bank" has multiple meanings. Select the sentence where "bank" means 금융기관:
A) The river bank is steep.
B) I need to go to the bank. ✓
C) Bank on me for support.
D) The plane will bank left.
```

**데이터 필요**:
- 다의어 목록
- 의미별 예문

---

## 📚 학습 목표별 문항 유형 활용 전략

### 초등 어휘 (800개) - Focus: Recognition & Basic Usage

**추천 문항 비율:**
- Type 1 (한국어 뜻): **60%**
- Type 3 (유의어): **20%**
- Type 5 (문장 완성): **20%**

**학습 방식:**
```
1. 단어 카드 (Recognition)
   - 앞면: apple
   - 뒷면: 사과

2. 간단한 문장 (Usage)
   - "I like to eat ______." (apple)

3. 그림 매칭 (Visual Association)
   - 그림을 보고 단어 선택
```

---

### 중학교과 어휘 (1,200개) - Focus: Meaning & Relations

**추천 문항 비율:**
- Type 1 (한국어 뜻): **40%**
- Type 3 (유의어): **20%**
- Type 4 (반의어): **15%**
- Type 5 (문장 완성): **20%**
- Type 7 (형태 변환): **5%**

**학습 방식:**
```
1. 의미 확장
   - happy → glad (유의어)
   - happy ↔ sad (반의어)

2. 품사 변환
   - happy (adj) → happiness (noun)

3. 문맥 이해
   - "She felt ______ when she received the gift."
```

---

### 고등학교 어휘 (1,000개) - Focus: Deep Understanding

**추천 문항 비율:**
- Type 2 (영어 정의): **30%**
- Type 5 (문장 완성): **30%**
- Type 6 (연어): **15%**
- Type 7 (형태 변환): **10%**
- Type 8 (화용): **10%**
- Type 11 (함축): **5%**

**학습 방식:**
```
1. 영영 사전 스타일
   - "A person who studies the stars and planets" → astronomer

2. 고급 문맥
   - "The ______ implications of this decision are far-reaching."

3. 연어 학습
   - make a decision (O)
   - do a decision (X)
```

---

### 수능 어휘 (5,000개) - Focus: Comprehensive Mastery

**추천 문항 비율:**
- Type 2 (영어 정의): **25%**
- Type 5 (문장 완성): **30%**
- Type 6 (연어): **15%**
- Type 7 (형태 변환): **10%**
- Type 8 (화용): **10%**
- Type 11 (함축): **5%**
- Type 12 (다의어): **5%**

**학습 방식:**
```
1. 학술적 문맥
   - "The researcher ______ a novel hypothesis."

2. 다의어 구분
   - "address" → 주소 / 다루다 / 연설하다

3. 격식성 인식
   - commence (formal) vs start (neutral)
```

---

## 🔧 구현 방안

### Phase 1: 기존 6가지 문항 활용 (즉시 가능)

**현재 DB 필드로 가능한 것:**
```python
AVAILABLE_TYPES = {
    "elementary": [1, 3, 5],  # 쉬운 문항만
    "middle": [1, 2, 3, 4, 5],  # 대부분 문항
    "high": [1, 2, 3, 4, 5, 6],  # 모든 기존 문항
    "suneung": [1, 2, 3, 4, 5, 6]  # 모든 문항
}
```

**학습 시 문항 선택 로직:**
```python
def select_question_type_for_word(
    word: VocabWord,
    goal_id: str,
    learning_stage: str  # "first", "review", "mastery"
) -> int:
    """
    학습 목표와 단계에 따라 적절한 문항 유형 선택
    """
    available_types = AVAILABLE_TYPES[goal_id]

    if learning_stage == "first":
        # 첫 학습: 쉬운 문항 (Type 1)
        return 1

    elif learning_stage == "review":
        # 복습: 중간 난이도 (Types 3, 4, 5)
        return random.choice([3, 4, 5] if all in available_types)

    elif learning_stage == "mastery":
        # 숙달 확인: 어려운 문항 (Types 2, 5)
        return random.choice([2, 5] if all in available_types)
```

---

### Phase 2: 형태 변환 문항 추가 (Type 7)

**필요 데이터 구조:**
```python
# 이미 있는 필드 활용
word_family = ["happy", "happiness", "happily", "unhappy"]

# 새로운 문항 생성
{
    "type": 7,
    "subtype": "pos_conversion",
    "stem": "Complete with the noun form: She expressed her ______.",
    "target_word": "happy",
    "correct_answer": "happiness",
    "distractors": ["happily", "happier", "unhappy"]
}
```

**구현 파일:**
- `distractor_engine.py`에 `generate_form_item()` 추가
- `word_family` 필드 활용

---

### Phase 3: 화용 문항 추가 (Type 8)

**필요 데이터 구조:**
```python
# register 필드 활용
register_data = {
    "request": "formal",
    "ask": "neutral",
    "beg": "informal"
}

# 새로운 문항 생성
{
    "type": 8,
    "subtype": "register",
    "stem": "Which is more formal for business communication?",
    "context": "Email to supervisor",
    "options": ["ask", "request", "beg", "wanna"],
    "correct_answer": "request"
}
```

---

### Phase 4: 다의어 문항 추가 (Type 12)

**필요 데이터 구조:**
```python
# 다의어 DB (신규 필요)
multi_meanings = {
    "bank": [
        {"meaning": "금융기관", "sentence": "I go to the bank."},
        {"meaning": "강둑", "sentence": "The river bank."},
        {"meaning": "기울다", "sentence": "The plane banks left."}
    ]
}
```

---

## 📊 문항 난이도 조정 (IRT b 값)

### 기존 Type 1-6 (이미 적용 중)
```python
QUESTION_TYPE_B_MODIFIER = {
    1: 0.0,   # 한국어 뜻 (가장 쉬움)
    2: 0.6,   # 영어 정의 (가장 어려움)
    3: 0.2,   # 유의어
    4: 0.3,   # 반의어
    5: 0.5,   # 문장 완성
    6: 0.2,   # 연어
}
```

### 새로운 Types 추가 제안
```python
QUESTION_TYPE_B_MODIFIER = {
    1: 0.0,   # 한국어 뜻
    2: 0.6,   # 영어 정의
    3: 0.2,   # 유의어
    4: 0.3,   # 반의어
    5: 0.5,   # 문장 완성
    6: 0.2,   # 연어
    7: 0.4,   # 형태 변환 (새로 추가)
    8: 0.5,   # 화용 맥락 (새로 추가)
    9: 0.3,   # 발음 지식 (새로 추가)
    10: 0.6,  # 형태소 분해 (새로 추가)
    11: 0.7,  # 함축 의미 (새로 추가)
    12: 0.6,  # 다의어 구분 (새로 추가)
}
```

---

## 🎓 학습 진행 시나리오 예시

### 시나리오: 중학교과 어휘 1,200개 학습

#### Stage 1: 첫 노출 (First Encounter)
```
단어: "happy"

[카드 앞면]
happy
[A1] [ADJ]

이 단어의 뜻을 아시나요?

[답 확인하기]

[카드 뒷면]
뜻: 행복한, 기쁜
영어 정의: Feeling or showing pleasure

예문:
- I am happy to see you.
- She looks happy today.

[✓ 알고 있었어요] [✗ 몰랐어요]
```

#### Stage 2: 의미 확인 (Recognition Test)
```
Type 1: 한국어 뜻 고르기

다음 단어 'happy'의 뜻으로 가장 알맞은 것을 고르세요.

A) 슬픈
B) 행복한 ✓
C) 화난
D) 피곤한
```

#### Stage 3: 관계 학습 (Relational Knowledge)
```
Type 3: 유의어

'happy'와 의미가 가장 비슷한 단어를 고르세요.

A) sad
B) glad ✓
C) angry
D) tired
```

#### Stage 4: 확장 학습 (Extended Knowledge)
```
Type 7: 형태 변환

올바른 형태를 선택하세요:
"She expressed her ______ about the news."

A) happy
B) happiness ✓
C) happily
D) happier
```

#### Stage 5: 문맥 사용 (Contextual Usage)
```
Type 5: 문장 완성

빈칸에 알맞은 단어를 고르세요:
"I feel ______ when I spend time with my friends."

A) sad
B) angry
C) happy ✓
D) tired
```

#### Stage 6: 숙달 확인 (Mastery Check)
```
Type 2: 영어 정의

Choose the correct English definition of 'happy':

A) Feeling sad or depressed
B) Feeling pleasure or contentment ✓
C) Feeling angry or annoyed
D) Feeling tired or exhausted
```

---

## 📈 진행도 추적

### DVK 레벨별 진행도
```
단어: "happy"

┌─────────────────────────────────────┐
│ DVK Progress                        │
├─────────────────────────────────────┤
│ ✓ Recognition (Type 1)    100%     │
│ ✓ Association (Type 3, 4)  100%     │
│ ✓ Usage (Type 5)          100%     │
│ ◯ Production (Type 7)       0%      │
│ ◯ Comprehension (Type 2)    0%      │
├─────────────────────────────────────┤
│ Overall Mastery: 60%                │
└─────────────────────────────────────┘
```

---

## 🔄 적응형 문항 선택 알고리즘

```python
def select_next_question(
    word: VocabWord,
    learning_history: List[QuestionResult],
    goal_id: str
) -> int:
    """
    학습 이력을 기반으로 다음 문항 유형 선택
    """
    # 1. 완료한 문항 유형 확인
    completed_types = set(h.question_type for h in learning_history if h.is_correct)

    # 2. 목표별 필수 문항 유형
    required_types = {
        "elementary": [1, 5],        # 뜻 + 문장
        "middle": [1, 3, 4, 5],      # 뜻 + 관계어 + 문장
        "high": [1, 2, 3, 4, 5, 6],  # 모든 기본 유형
        "suneung": [1, 2, 3, 4, 5, 6, 7, 8]  # 확장 유형 포함
    }

    # 3. 아직 안 한 문항 중 선택
    pending_types = set(required_types[goal_id]) - completed_types

    if pending_types:
        # DVK 순서대로 (쉬운 것부터)
        dvk_order = [1, 3, 4, 6, 7, 5, 8, 2]
        for t in dvk_order:
            if t in pending_types:
                return t

    # 4. 모두 완료했으면 가장 어려운 문항으로 재확인
    return 2  # 영어 정의
```

---

## 📊 데이터베이스 요구사항

### 기존 필드 활용 (즉시 가능)
- ✅ `kr_curriculum`: 학습 목표 필터링
- ✅ `word_family`: 형태 변환 문항 (Type 7)
- ✅ `synonym`: 유의어 문항 (Type 3)
- ✅ `antonym`: 반의어 문항 (Type 4)
- ✅ `sentence_1, 2, 3`: 문맥 문항 (Type 5)
- ✅ `collocation`: 연어 문항 (Type 6)
- ✅ `register`: 화용 문항 (Type 8)
- ✅ `ipa`: 발음 문항 (Type 9)
- ✅ `morpheme`: 형태소 문항 (Type 10)

### 추가 필요 필드
- ⚠️ `connotation`: positive/negative/neutral (Type 11)
- ⚠️ `multiple_meanings`: JSON array of meanings (Type 12)
- ⚠️ `stress_pattern`: 강세 위치 (Type 9)

---

## 🎯 우선순위 구현 로드맵

### Phase 1 (즉시): 기존 문항 활용 ✅
- Type 1-6 활용
- 학습 목표별 문항 비율 조정
- 적응형 문항 선택 알고리즘

### Phase 2 (1주): 형태 변환 추가
- Type 7 구현
- `word_family` 활용

### Phase 3 (2주): 화용 맥락 추가
- Type 8 구현
- `register` 활용

### Phase 4 (4주): 고급 문항 추가
- Types 9-12 구현
- 새로운 데이터 필드 추가

---

## 💡 결론

### 즉시 구현 가능 (Phase 1)
현재 데이터베이스와 시스템으로 **Types 1-6을 학습 목표별로 차등 적용**하는 것만으로도 충분한 DVK 측정이 가능합니다.

**초등**: Type 1, 3, 5 (Recognition → Usage)
**중학**: Type 1, 2, 3, 4, 5 (+ Relations)
**고등**: Type 1-6 전체 (+ Collocation)
**수능**: Type 1-6 + 추후 확장

### 중장기 확장 (Phase 2-4)
- 형태 변환 (Type 7)
- 화용 맥락 (Type 8)
- 발음/형태소/함축/다의어 (Types 9-12)

---

**작성일**: 2026-02-26
**다음 단계**: Phase 1 구현 (기존 문항 유형 활용한 학습 시스템)
