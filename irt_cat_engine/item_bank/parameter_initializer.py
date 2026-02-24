"""Initialize IRT parameters (b, a) from vocabulary metadata."""
import numpy as np
from scipy import stats

from ..config import (
    B_WEIGHT_CEFR, B_WEIGHT_FREQ, B_WEIGHT_GSE,
    B_WEIGHT_CURRICULUM, B_WEIGHT_LEXILE,
    CEFR_NUMERIC, CURRICULUM_NUMERIC,
    A_BASE, A_MIN, A_MAX,
    EDU_VALUE_BONUS, POS_FACTOR, GENERAL_TOPICS,
    QUESTION_TYPE_B_MODIFIER,
    IRT_MODEL, GUESSING_C_4CHOICE, GUESSING_C_BINARY,
    LOANWORD_DISCRIMINATION_FACTOR,
)
from ..data.load_vocabulary import VocabWord, _parse_lexile_midpoint
from ..data.topic_mapper import map_topic
from ..models.irt_2pl import ItemParameters


def compute_difficulty_b(word: VocabWord, total_words: int = 9183) -> float:
    """Compute initial difficulty parameter b from word metadata.

    Combines CEFR, freq_rank, GSE, curriculum, and Lexile into a weighted
    composite, then transforms to IRT scale via probit.
    """
    # 1. CEFR numeric
    cefr_val = CEFR_NUMERIC.get(word.cefr, 0.45)  # Default to B1 midpoint

    # 2. Frequency normalized
    freq_val = word.freq_rank / total_words if word.freq_rank > 0 else 0.5

    # 3. GSE normalized (range ~10-70)
    if word.gse is not None and word.gse > 0:
        gse_val = np.clip((word.gse - 10.0) / 60.0, 0.0, 1.0)
    else:
        gse_val = None

    # 4. Curriculum normalized
    curriculum_val = CURRICULUM_NUMERIC.get(word.kr_curriculum, 0.45)

    # 5. Lexile normalized
    lexile_mid = _parse_lexile_midpoint(word.lexile)
    if lexile_mid is not None:
        lexile_val = np.clip((lexile_mid - 200.0) / 1200.0, 0.0, 1.0)
    else:
        lexile_val = None

    # Weighted composite (re-weight if some values missing)
    weights = {
        "cefr": B_WEIGHT_CEFR,
        "freq": B_WEIGHT_FREQ,
        "gse": B_WEIGHT_GSE if gse_val is not None else 0.0,
        "curriculum": B_WEIGHT_CURRICULUM,
        "lexile": B_WEIGHT_LEXILE if lexile_val is not None else 0.0,
    }
    values = {
        "cefr": cefr_val,
        "freq": freq_val,
        "gse": gse_val if gse_val is not None else 0.0,
        "curriculum": curriculum_val,
        "lexile": lexile_val if lexile_val is not None else 0.0,
    }

    total_weight = sum(weights.values())
    if total_weight < 1e-10:
        difficulty_raw = 0.5
    else:
        difficulty_raw = sum(weights[k] * values[k] for k in weights) / total_weight

    # Transform to IRT b-scale via probit
    difficulty_raw = np.clip(difficulty_raw, 0.01, 0.99)
    b = float(stats.norm.ppf(difficulty_raw))

    return b


def compute_discrimination_a(word: VocabWord) -> float:
    """Compute initial discrimination parameter a from word metadata."""
    a = A_BASE

    # 1. Synonym penalty: more synonyms → lower discrimination
    synonym_count = len(word.synonym)
    synonym_penalty = max(0.7, 1.0 - 0.05 * synonym_count)
    a *= synonym_penalty

    # 2. Educational value bonus
    if word.educational_value is not None:
        bonus = EDU_VALUE_BONUS.get(word.educational_value, 1.0)
    else:
        bonus = 1.0
    a *= bonus

    # 3. Topic specificity: general topics discriminate less
    topic_lower = word.topic.lower() if word.topic else ""
    is_general = any(t in topic_lower for t in GENERAL_TOPICS)
    if is_general:
        a *= 0.85

    # 4. POS factor: content words discriminate better
    pos_factor = POS_FACTOR.get(word.pos, 1.0)
    a *= pos_factor

    # 5. Oxford 3000 / NGSL commonality: very common words discriminate less
    if word.oxford3000 and word.oxford3000 not in ("", "N/A"):
        a *= 0.90

    return float(np.clip(a, A_MIN, A_MAX))


def compute_guessing_c(question_type: int) -> float:
    """Compute initial guessing parameter c based on question type.

    Only used when IRT_MODEL == "3PL". Returns 0.0 for 2PL mode.
    Reads IRT_MODEL at call time to support runtime config changes.
    """
    import irt_cat_engine.config as cfg
    if cfg.IRT_MODEL != "3PL":
        return 0.0
    if question_type == 6:
        return cfg.GUESSING_C_BINARY   # Binary choice (collocation judgment)
    return cfg.GUESSING_C_4CHOICE      # 4-choice items (Types 1-5)


def initialize_item_parameters(
    words: list[VocabWord],
    question_type: int = 1,
) -> list[ItemParameters]:
    """Initialize IRT parameters for all words.

    Args:
        words: List of vocabulary words
        question_type: Question type (1-6) for b modifier

    Returns:
        List of ItemParameters with computed b, a, and c values
    """
    total_words = len(words) if words else 9183
    b_modifier = QUESTION_TYPE_B_MODIFIER.get(question_type, 0.0)
    c = compute_guessing_c(question_type)

    items = []
    for i, word in enumerate(words):
        b = compute_difficulty_b(word, total_words) + b_modifier
        a = compute_discrimination_a(word)

        # Reduce discrimination for loanwords on Type 1/2 (meaning is trivially obvious)
        if word.is_loanword and question_type in (1, 2):
            a *= LOANWORD_DISCRIMINATION_FACTOR

        items.append(ItemParameters(
            item_id=i,
            word=word.word_display,
            difficulty_b=b,
            discrimination_a=a,
            guessing_c=c,
            question_type=question_type,
            pos=word.pos,
            cefr=word.cefr,
            topic=map_topic(word.topic),
            is_loanword=word.is_loanword,
        ))

    return items


def get_parameter_statistics(items: list[ItemParameters]) -> dict:
    """Get summary statistics of initialized parameters."""
    bs = [item.difficulty_b for item in items]
    as_ = [item.discrimination_a for item in items]

    return {
        "count": len(items),
        "b_mean": float(np.mean(bs)),
        "b_std": float(np.std(bs)),
        "b_min": float(np.min(bs)),
        "b_max": float(np.max(bs)),
        "b_median": float(np.median(bs)),
        "a_mean": float(np.mean(as_)),
        "a_std": float(np.std(as_)),
        "a_min": float(np.min(as_)),
        "a_max": float(np.max(as_)),
    }
