"""Personalized learning recommendation engine.

Generates study plans based on 5D dimension scores after a diagnostic test.
Each weak dimension gets targeted exercises using the vocabulary database.
"""
import random
from dataclasses import dataclass

from .dimension_analyzer import DIMENSIONS

CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1"]

FOCUS_THRESHOLD = 70   # score < 70% → needs study
PRIORITY_THRESHOLD = 40  # score < 40% → high priority

DIMENSION_TIPS = {
    "semantic": {
        "ko": "단어의 정확한 의미와 유사 단어 간 미묘한 차이에 집중하세요.",
        "en": "Focus on exact meanings and subtle differences between similar words.",
    },
    "contextual": {
        "ko": "문장 속에서 단어를 사용하는 연습을 하세요. 연어(함께 쓰이는 단어)에 주의하세요.",
        "en": "Practice using words in sentences. Pay attention to collocations.",
    },
    "form": {
        "ko": "단어 가족을 공부하세요: 같은 어근에서 파생된 명사, 동사, 형용사, 부사를 함께 학습하세요.",
        "en": "Study word families: learn nouns, verbs, adjectives from the same root together.",
    },
    "relational": {
        "ko": "동의어, 반의어, 관련 단어를 함께 학습하여 어휘 네트워크를 확장하세요.",
        "en": "Build your word network by learning synonyms, antonyms, and related words together.",
    },
    "pragmatic": {
        "ko": "격식체와 비격식체 단어를 구분하는 연습을 하세요. 학술적 글쓰기와 일상 대화의 어휘가 다릅니다.",
        "en": "Notice when words are formal vs. informal. Academic writing uses different vocabulary.",
    },
}


def get_adjacent_cefr(cefr: str) -> list[str]:
    """Return CEFR levels within ±1 of the given level."""
    idx = CEFR_LEVELS.index(cefr) if cefr in CEFR_LEVELS else 2  # default B1
    return [CEFR_LEVELS[i] for i in range(len(CEFR_LEVELS)) if abs(i - idx) <= 1]


def _find_distractors(all_words, target_word, pos: str, cefr: str, count: int = 3):
    """Find distractor words matching POS, preferring same CEFR then adjacent."""
    target_lower = target_word.word_display.lower()

    # Try exact CEFR + same POS
    pool = [w for w in all_words
            if w.word_display.lower() != target_lower
            and w.pos == pos and w.cefr == cefr]
    random.shuffle(pool)
    if len(pool) >= count:
        return pool[:count]

    # Fallback: adjacent CEFR levels
    adjacent = get_adjacent_cefr(cefr)
    pool = [w for w in all_words
            if w.word_display.lower() != target_lower
            and w.pos == pos and w.cefr in adjacent]
    random.shuffle(pool)
    return pool[:count]


def _generate_semantic_exercise(word, idx, all_words) -> dict | None:
    """Definition matching exercise."""
    if not word.meaning_ko:
        return None

    distractors = _find_distractors(all_words, word, word.pos, word.cefr)
    if len(distractors) < 3:
        return None

    correct_idx = random.randint(0, 3)
    options = []
    d_idx = 0
    for i in range(4):
        if i == correct_idx:
            options.append(word.meaning_ko)
        else:
            options.append(distractors[d_idx].meaning_ko)
            d_idx += 1

    return {
        "id": f"sem-{idx}",
        "dimension": "semantic",
        "word": word.word_display,
        "cefr": word.cefr,
        "type": "definition-match",
        "prompt": f'"{word.word_display}"의 뜻은?',
        "prompt_en": f'What does "{word.word_display}" mean?',
        "options": options,
        "correct_index": correct_idx,
        "explanation": f'"{word.word_display}": {word.meaning_ko}',
    }


def _generate_contextual_exercise(word, idx, all_words) -> dict | None:
    """Sentence fill-in-blank exercise."""
    sentence = word.sentence_1
    if not sentence:
        return None

    # Replace word in sentence with blank
    import re
    blanked = re.sub(rf'\b{re.escape(word.word_display)}\b', '_____', sentence, flags=re.IGNORECASE)
    if blanked == sentence:
        return None

    distractors = _find_distractors(all_words, word, word.pos, word.cefr)
    if len(distractors) < 3:
        return None

    correct_idx = random.randint(0, 3)
    options = []
    d_idx = 0
    for i in range(4):
        if i == correct_idx:
            options.append(word.word_display)
        else:
            options.append(distractors[d_idx].word_display)
            d_idx += 1

    return {
        "id": f"ctx-{idx}",
        "dimension": "contextual",
        "word": word.word_display,
        "cefr": word.cefr,
        "type": "sentence-blank",
        "prompt": f'빈칸에 알맞은 단어를 고르세요:\n"{blanked}"',
        "prompt_en": f'Fill in the blank:\n"{blanked}"',
        "options": options,
        "correct_index": correct_idx,
        "explanation": f'"{word.word_display}" ({word.meaning_ko})',
    }


def _generate_relational_exercise(word, idx, all_words) -> dict | None:
    """Synonym/antonym exercise."""
    synonyms = word.synonym if isinstance(word.synonym, list) else []
    antonyms = word.antonym if isinstance(word.antonym, list) else []

    if synonyms:
        target = synonyms[0]
        prompt = f'"{word.word_display}"의 동의어는?'
        prompt_en = f'Which word is a SYNONYM of "{word.word_display}"?'
        explanation = f'"{target}"은/는 "{word.word_display}"의 동의어입니다. ({word.meaning_ko})'
    elif antonyms:
        target = antonyms[0]
        prompt = f'"{word.word_display}"의 반의어는?'
        prompt_en = f'Which word is an ANTONYM of "{word.word_display}"?'
        explanation = f'"{target}"은/는 "{word.word_display}"의 반의어입니다. ({word.meaning_ko})'
    else:
        return None

    distractors = _find_distractors(all_words, word, word.pos, word.cefr)
    distractor_words = [d.word_display for d in distractors if d.word_display != target]
    if len(distractor_words) < 3:
        return None
    distractor_words = distractor_words[:3]

    correct_idx = random.randint(0, 3)
    options = []
    d_idx = 0
    for i in range(4):
        if i == correct_idx:
            options.append(target)
        else:
            options.append(distractor_words[d_idx])
            d_idx += 1

    return {
        "id": f"rel-{idx}",
        "dimension": "relational",
        "word": word.word_display,
        "cefr": word.cefr,
        "type": "synonym-antonym",
        "prompt": prompt,
        "prompt_en": prompt_en,
        "options": options,
        "correct_index": correct_idx,
        "explanation": explanation,
    }


def _generate_form_exercise(word, idx, all_words) -> dict | None:
    """Word family exercise — requires word_family data."""
    family = getattr(word, 'word_family', None) or []
    if not family:
        return None

    target = family[0]
    distractors = _find_distractors(all_words, word, word.pos, word.cefr)
    distractor_words = [d.word_display for d in distractors
                        if d.word_display.lower() not in [f.lower() for f in family]]
    if len(distractor_words) < 3:
        return None
    distractor_words = distractor_words[:3]

    correct_idx = random.randint(0, 3)
    options = []
    d_idx = 0
    for i in range(4):
        if i == correct_idx:
            options.append(target)
        else:
            options.append(distractor_words[d_idx])
            d_idx += 1

    return {
        "id": f"frm-{idx}",
        "dimension": "form",
        "word": word.word_display,
        "cefr": word.cefr,
        "type": "word-family",
        "prompt": f'"{word.word_display}"와 같은 단어 가족에 속하는 단어는?',
        "prompt_en": f'Which word belongs to the same word family as "{word.word_display}"?',
        "options": options,
        "correct_index": correct_idx,
        "explanation": f'"{target}"은/는 "{word.word_display}"의 단어 가족입니다. ({", ".join(family)})',
    }


def _generate_pragmatic_exercise(word, idx, all_words) -> dict | None:
    """Register identification exercise."""
    register = getattr(word, 'register', '') or ''
    if not register or register in ('', 'general', 'neutral'):
        return None

    register_map = {
        'formal': (0, 'formal/academic'),
        'informal': (2, 'informal/casual'),
        'literary': (3, 'literary/elevated'),
    }
    if register not in register_map:
        return None

    correct_idx_fixed, label = register_map[register]
    options = ["Formal / Academic", "Neutral / General", "Informal / Casual", "Literary / Elevated"]

    return {
        "id": f"prg-{idx}",
        "dimension": "pragmatic",
        "word": word.word_display,
        "cefr": word.cefr,
        "type": "register-identify",
        "prompt": f'"{word.word_display}"의 사용역(register)은?',
        "prompt_en": f'What register does "{word.word_display}" belong to?',
        "options": options,
        "correct_index": correct_idx_fixed,
        "explanation": f'"{word.word_display}"은/는 {label}입니다. ({word.meaning_ko})',
    }


EXERCISE_GENERATORS = {
    "semantic": _generate_semantic_exercise,
    "contextual": _generate_contextual_exercise,
    "relational": _generate_relational_exercise,
    "form": _generate_form_exercise,
    "pragmatic": _generate_pragmatic_exercise,
}


def generate_study_plan(
    dimension_scores: list[dict],
    vocab_words: list,
    cefr_level: str = "B1",
) -> dict:
    """Generate a personalized study plan from dimension scores.

    Args:
        dimension_scores: List of dimension score dicts from compute_dimension_scores().
        vocab_words: Full VocabWord list for exercise generation.
        cefr_level: Target CEFR level for word selection.

    Returns:
        Study plan dict with recommendations per dimension.
    """
    # Determine which dimensions need work
    weak_dims = [d for d in dimension_scores if d["score"] is not None and d["score"] < FOCUS_THRESHOLD]
    weak_dims.sort(key=lambda d: d["score"])

    # If no weak dims, recommend the lowest-scoring one
    scored = [d for d in dimension_scores if d["score"] is not None]
    if not weak_dims and scored:
        weak_dims = [min(scored, key=lambda d: d["score"])]

    recommendations = []
    adjacent = get_adjacent_cefr(cefr_level)

    for dim_score in weak_dims:
        dim_key = dim_score["dimension"]
        score = dim_score["score"]

        if score is not None and score < PRIORITY_THRESHOLD:
            priority = "high"
            exercise_count = 5
        elif score is not None and score < FOCUS_THRESHOLD:
            priority = "medium"
            exercise_count = 4
        else:
            priority = "low"
            exercise_count = 3

        # Select words at target CEFR level
        pool = [w for w in vocab_words if w.cefr in adjacent]
        random.shuffle(pool)
        pool = pool[:exercise_count * 5]  # oversample to account for generation failures

        generator = EXERCISE_GENERATORS.get(dim_key)
        exercises = []
        if generator:
            for i, word in enumerate(pool):
                if len(exercises) >= exercise_count:
                    break
                ex = generator(word, len(exercises), vocab_words)
                if ex is not None:
                    exercises.append(ex)

        tip = DIMENSION_TIPS.get(dim_key, {"ko": "", "en": ""})

        recommendations.append({
            "dimension": dim_key,
            "label": dim_score["label"],
            "label_ko": dim_score["label_ko"],
            "color": dim_score["color"],
            "score": score,
            "priority": priority,
            "tip_ko": tip["ko"],
            "tip_en": tip["en"],
            "exercises": exercises,
        })

    total_exercises = sum(len(r["exercises"]) for r in recommendations)

    # Generate 4-week roadmap
    weekly_plan = _build_weekly_plan(recommendations)

    return {
        "recommendations": recommendations,
        "total_exercises": total_exercises,
        "weak_dimensions": [d["dimension"] for d in weak_dims],
        "weekly_plan": weekly_plan,
    }


def _build_weekly_plan(recommendations: list[dict]) -> list[dict]:
    """Build a 4-week study roadmap from recommendations.

    - Weeks 1-2: High priority dimensions (intensive)
    - Week 3: Medium priority dimensions (reinforcement)
    - Week 4: Review all + retest recommendation
    """
    high = [r for r in recommendations if r["priority"] == "high"]
    medium = [r for r in recommendations if r["priority"] == "medium"]
    low = [r for r in recommendations if r["priority"] == "low"]

    weeks = []

    # Week 1: First high-priority dimension (or first medium if no high)
    w1_dims = high[:1] or medium[:1] or low[:1]
    if w1_dims:
        weeks.append({
            "week": 1,
            "focus": [d["dimension"] for d in w1_dims],
            "focus_labels": [d["label_ko"] for d in w1_dims],
            "daily_target": 5,
            "description_ko": "약점 차원 집중 학습",
            "description_en": "Focus on weakest dimension",
        })

    # Week 2: Remaining high-priority or next medium
    w2_dims = high[1:] or medium[:1] if len(high) > 1 else medium[:1] or low[:1]
    if w2_dims and isinstance(w2_dims, list) and w2_dims != w1_dims:
        weeks.append({
            "week": 2,
            "focus": [d["dimension"] for d in w2_dims],
            "focus_labels": [d["label_ko"] for d in w2_dims],
            "daily_target": 5,
            "description_ko": "약점 보강 학습",
            "description_en": "Reinforce weak areas",
        })
    elif w1_dims:
        weeks.append({
            "week": 2,
            "focus": [d["dimension"] for d in w1_dims],
            "focus_labels": [d["label_ko"] for d in w1_dims],
            "daily_target": 4,
            "description_ko": "지속 연습",
            "description_en": "Continue practice",
        })

    # Week 3: Medium priority or mixed review
    w3_dims = medium or low or high[:1]
    if w3_dims:
        weeks.append({
            "week": 3,
            "focus": [d["dimension"] for d in w3_dims[:2]],
            "focus_labels": [d["label_ko"] for d in w3_dims[:2]],
            "daily_target": 4,
            "description_ko": "중간 영역 보강",
            "description_en": "Strengthen moderate areas",
        })

    # Week 4: Comprehensive review + retest
    all_dims = [d["dimension"] for d in recommendations[:3]]
    all_labels = [d["label_ko"] for d in recommendations[:3]]
    weeks.append({
        "week": 4,
        "focus": all_dims,
        "focus_labels": all_labels,
        "daily_target": 3,
        "description_ko": "종합 복습 + 재테스트",
        "description_en": "Comprehensive review + retest",
    })

    return weeks
