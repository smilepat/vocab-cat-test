"""Vocabulary Matrix generator.

Computes knowledge-depth states for a representative sample of vocabulary words,
using IRT probability for words with item parameters and CEFR-based estimation
for words without. Purely additive read-only module — does not modify IRT logic.
"""

from ..models.irt_2pl import ItemParameters, probability
from ..data.load_vocabulary import VocabWord
from ..config import THETA_CEFR_BOUNDARIES

KNOWLEDGE_STATES = [
    {"key": "not_known",   "label": "Not Known",    "label_ko": "미학습",    "color": "#e2e8f0", "min_p": 0.0,  "max_p": 0.3},
    {"key": "emerging",    "label": "Emerging",      "label_ko": "인식",     "color": "#93c5fd", "min_p": 0.3,  "max_p": 0.5},
    {"key": "developing",  "label": "Developing",    "label_ko": "발전",     "color": "#86efac", "min_p": 0.5,  "max_p": 0.7},
    {"key": "comfortable", "label": "Comfortable",   "label_ko": "익숙",     "color": "#fde047", "min_p": 0.7,  "max_p": 0.9},
    {"key": "mastered",    "label": "Mastered",       "label_ko": "완전 습득", "color": "#fca5a5", "min_p": 0.9,  "max_p": 1.01},
]

_CEFR_ORDER = ["A1", "A2", "B1", "B2", "C1"]


def _classify_probability(p: float) -> str:
    """Map IRT probability to knowledge state key."""
    for state in KNOWLEDGE_STATES:
        if state["min_p"] <= p < state["max_p"]:
            return state["key"]
    return "mastered" if p >= 0.9 else "not_known"


def _cefr_to_estimated_probability(word_cefr: str, user_cefr: str) -> float:
    """Estimate probability for words without IRT parameters using CEFR proximity."""
    try:
        word_idx = _CEFR_ORDER.index(word_cefr)
    except ValueError:
        word_idx = 2
    try:
        user_idx = _CEFR_ORDER.index(user_cefr)
    except ValueError:
        user_idx = 2

    diff = user_idx - word_idx
    if diff >= 2:
        return 0.92
    elif diff == 1:
        return 0.78
    elif diff == 0:
        return 0.55
    elif diff == -1:
        return 0.38
    else:
        return 0.15


def _sample_representative_words(
    vocab_words: list[VocabWord],
    sample_size: int = 100,
) -> list[VocabWord]:
    """Sample words stratified by CEFR level for a representative grid."""
    by_cefr: dict[str, list[VocabWord]] = {}
    for w in vocab_words:
        cefr = w.cefr if w.cefr in _CEFR_ORDER else "B1"
        by_cefr.setdefault(cefr, []).append(w)

    total = sum(len(v) for v in by_cefr.values())
    if total == 0:
        return []

    sampled: list[VocabWord] = []
    for level in _CEFR_ORDER:
        pool = by_cefr.get(level, [])
        if not pool:
            continue
        n = max(5, round(len(pool) / total * sample_size))
        n = min(n, len(pool), sample_size - len(sampled))
        if n <= 0:
            continue
        sorted_pool = sorted(pool, key=lambda w: w.freq_rank)
        if len(sorted_pool) <= n:
            sampled.extend(sorted_pool)
        else:
            step = len(sorted_pool) / n
            sampled.extend(sorted_pool[int(i * step)] for i in range(n))

    return sorted(sampled[:sample_size], key=lambda w: w.freq_rank)


def compute_vocab_matrix(
    theta: float,
    cefr_level: str,
    vocab_words: list[VocabWord],
    item_bank: list[ItemParameters],
    sample_size: int = 100,
) -> dict:
    """Compute vocabulary matrix data for current and goal states.

    Read-only post-test metric. Does not affect IRT model or item selection.
    """
    item_lookup: dict[str, ItemParameters] = {
        item.word.lower(): item for item in item_bank
    }

    sampled = _sample_representative_words(vocab_words, sample_size)

    # Goal theta: midpoint of next CEFR level
    try:
        idx = _CEFR_ORDER.index(cefr_level)
    except ValueError:
        idx = 2
    next_level = _CEFR_ORDER[min(idx + 1, len(_CEFR_ORDER) - 1)]
    low, high = THETA_CEFR_BOUNDARIES[next_level]
    goal_theta = (low + high) / 2
    if goal_theta <= theta + 0.1:
        goal_theta = theta + 0.5

    words = []
    current_counts: dict[str, int] = {s["key"]: 0 for s in KNOWLEDGE_STATES}
    goal_counts: dict[str, int] = {s["key"]: 0 for s in KNOWLEDGE_STATES}
    changed_count = 0

    for vw in sampled:
        item = item_lookup.get(vw.word_display.lower())

        if item is not None:
            current_p = probability(theta, item.discrimination_a, item.difficulty_b, item.guessing_c)
            goal_p = probability(goal_theta, item.discrimination_a, item.difficulty_b, item.guessing_c)
        else:
            current_p = _cefr_to_estimated_probability(vw.cefr, cefr_level)
            next_idx = min(idx + 1, 4)
            goal_cefr = _CEFR_ORDER[next_idx]
            goal_p = _cefr_to_estimated_probability(vw.cefr, goal_cefr)

        current_state = _classify_probability(current_p)
        goal_state = _classify_probability(goal_p)

        current_counts[current_state] += 1
        goal_counts[goal_state] += 1
        if current_state != goal_state:
            changed_count += 1

        words.append({
            "word": vw.word_display,
            "meaning_ko": vw.meaning_ko,
            "cefr": vw.cefr,
            "pos": vw.pos,
            "freq_rank": vw.freq_rank,
            "current_state": current_state,
            "current_probability": round(float(current_p), 3),
            "goal_state": goal_state,
            "goal_probability": round(float(goal_p), 3),
            "has_irt_params": item is not None,
        })

    return {
        "words": words,
        "total_sampled": len(words),
        "current_theta": round(theta, 3),
        "goal_theta": round(goal_theta, 3),
        "goal_cefr": next_level,
        "summary": {
            "counts": current_counts,
            "total": len(words),
        },
        "goal_summary": {
            "counts": goal_counts,
            "total": len(words),
            "words_changed": changed_count,
        },
        "states": KNOWLEDGE_STATES,
    }
