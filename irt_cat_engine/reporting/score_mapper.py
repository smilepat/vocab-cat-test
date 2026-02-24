"""Map theta scores to interpretable scales (CEFR, curriculum, vocab size)."""
import numpy as np
from scipy import stats

from ..config import THETA_CEFR_BOUNDARIES, THETA_CURRICULUM_BOUNDARIES
from ..models.irt_2pl import ItemParameters, probability
from .dimension_analyzer import compute_dimension_scores

# CEFR level -> approximate known vocabulary count (for display purposes)
CEFR_VOCAB_ESTIMATES: dict[str, int] = {
    "A1": 1000, "A2": 2000, "B1": 3500, "B2": 5000, "C1": 8000,
}


def _estimate_oxford_coverage(theta: float, full_item_bank: list[ItemParameters]) -> float:
    """Estimate coverage of high-frequency words (freq_rank <= 3000).

    Read-only post-test metric. Does not affect IRT model or item selection.
    Uses existing probability() function to compute P(correct | theta) for each
    high-frequency item; coverage = fraction where P >= 0.5.
    """
    # Use CEFR as proxy for high-frequency: A1/A2/B1 are core vocabulary.
    core_items = [
        item for item in full_item_bank
        if item.cefr in ("A1", "A2", "B1")
    ]

    if not core_items:
        return 0.0

    known_count = sum(
        1 for item in core_items
        if probability(theta, item.discrimination_a, item.difficulty_b, item.guessing_c) >= 0.5
    )
    return round(known_count / len(core_items), 3)


def theta_to_cefr(theta: float, se: float) -> tuple[str, dict[str, float]]:
    """Map theta to CEFR level with probability distribution.

    Returns:
        (primary_level, probabilities_dict)
    """
    probabilities = {}
    primary_level = "B1"  # default

    for level, (low, high) in THETA_CEFR_BOUNDARIES.items():
        p = stats.norm.cdf(high, theta, se) - stats.norm.cdf(low, theta, se)
        probabilities[level] = round(float(p), 4)

    # Primary level is the one with highest probability
    primary_level = max(probabilities, key=probabilities.get)

    return primary_level, probabilities


def theta_to_curriculum(theta: float) -> str:
    """Map theta to Korean curriculum level."""
    for level, (low, high) in THETA_CURRICULUM_BOUNDARIES.items():
        if low <= theta < high:
            return level
    if theta >= 1.2:
        return "고등 이상 (Beyond High School)"
    return "초등 수준 (Elementary)"


def theta_to_vocab_size(theta: float, items: list[ItemParameters]) -> int:
    """Estimate vocabulary size by summing P(correct) across all items.

    This gives the expected number of words the learner knows.
    """
    total = sum(
        probability(theta, item.discrimination_a, item.difficulty_b, item.guessing_c)
        for item in items
    )
    return int(round(total))


def generate_diagnostic_report(
    theta: float,
    se: float,
    items_administered: list[ItemParameters],
    responses: list[int],
    full_item_bank: list[ItemParameters],
) -> dict:
    """Generate a comprehensive diagnostic report.

    Returns dict with all result mappings and analysis.
    """
    cefr_level, cefr_probs = theta_to_cefr(theta, se)
    curriculum_level = theta_to_curriculum(theta)
    vocab_size = theta_to_vocab_size(theta, full_item_bank)

    # Per-topic analysis
    topic_results: dict[str, dict] = {}
    for item, response in zip(items_administered, responses):
        topic = item.topic or "general"
        if topic not in topic_results:
            topic_results[topic] = {"correct": 0, "total": 0}
        topic_results[topic]["total"] += 1
        if response == 1:
            topic_results[topic]["correct"] += 1

    topic_strengths = []
    topic_weaknesses = []
    for topic, data in topic_results.items():
        rate = data["correct"] / data["total"] if data["total"] > 0 else 0
        entry = {"topic": topic, "correct": data["correct"], "total": data["total"], "rate": round(rate, 2)}
        if rate >= 0.7:
            topic_strengths.append(entry)
        elif rate < 0.5 and data["total"] >= 2:
            topic_weaknesses.append(entry)

    # Overall accuracy
    total_correct = sum(responses)
    total_items = len(responses)
    accuracy = total_correct / total_items if total_items > 0 else 0

    # Reliability estimate
    reliability = 1.0 - se ** 2 if se < 1.0 else max(0.0, 1.0 - se ** 2)

    # Per-CEFR analysis
    cefr_results: dict[str, dict] = {}
    for item, response in zip(items_administered, responses):
        c = item.cefr or "unknown"
        if c not in cefr_results:
            cefr_results[c] = {"correct": 0, "total": 0}
        cefr_results[c]["total"] += 1
        if response == 1:
            cefr_results[c]["correct"] += 1

    cefr_detail = []
    for cefr_val, data in sorted(cefr_results.items()):
        rate = data["correct"] / data["total"] if data["total"] > 0 else 0
        cefr_detail.append({
            "cefr": cefr_val, "correct": data["correct"],
            "total": data["total"], "rate": round(rate, 2),
        })

    # Recommended study areas
    recommendations = []
    for entry in sorted(topic_weaknesses, key=lambda x: x["rate"]):
        recommendations.append(
            f"'{entry['topic']}' 영역 어휘 학습 강화 (정답률 {int(entry['rate']*100)}%)"
        )
    if cefr_level in ("A1", "A2"):
        recommendations.append("기초 고빈도 어휘(A1-A2) 반복 학습 권장")
    elif cefr_level in ("B2", "C1"):
        recommendations.append("학술/전문 어휘(B2-C1) 확장 학습 권장")

    # 5D dimension analysis
    dimension_scores = compute_dimension_scores(items_administered, responses)

    # Post-test metrics (read-only, does not affect IRT)
    oxford_coverage = _estimate_oxford_coverage(theta, full_item_bank)
    estimated_vocabulary = CEFR_VOCAB_ESTIMATES.get(cefr_level, 3500)

    return {
        "theta": round(theta, 3),
        "se": round(se, 3),
        "reliability": round(reliability, 3),
        "cefr_level": cefr_level,
        "cefr_probabilities": cefr_probs,
        "curriculum_level": curriculum_level,
        "vocab_size_estimate": vocab_size,
        "total_items": total_items,
        "total_correct": total_correct,
        "accuracy": round(accuracy, 3),
        "topic_strengths": sorted(topic_strengths, key=lambda x: -x["rate"]),
        "topic_weaknesses": sorted(topic_weaknesses, key=lambda x: x["rate"]),
        "cefr_detail": cefr_detail,
        "recommendations": recommendations,
        "dimension_scores": dimension_scores,
        "oxford_coverage": oxford_coverage,
        "estimated_vocabulary": estimated_vocabulary,
    }


def generate_longitudinal_report(
    sessions: list[dict],
) -> dict:
    """Generate a longitudinal progress report across multiple test sessions.

    Args:
        sessions: List of dicts with keys: theta, se, cefr_level, vocab_size_estimate,
                  started_at, total_items, accuracy

    Returns:
        Progress analysis over time
    """
    if not sessions:
        return {"message": "No test history available", "sessions": 0}

    thetas = [s["theta"] for s in sessions if s.get("theta") is not None]
    vocab_sizes = [s["vocab_size_estimate"] for s in sessions if s.get("vocab_size_estimate")]

    report = {
        "sessions": len(sessions),
        "theta_trend": thetas,
        "latest_theta": thetas[-1] if thetas else None,
        "theta_change": round(thetas[-1] - thetas[0], 3) if len(thetas) >= 2 else None,
        "latest_cefr": sessions[-1].get("cefr_level") if sessions else None,
        "vocab_trend": vocab_sizes,
        "vocab_change": vocab_sizes[-1] - vocab_sizes[0] if len(vocab_sizes) >= 2 else None,
    }

    # Determine trend direction
    if len(thetas) >= 3:
        recent_avg = np.mean(thetas[-3:])
        early_avg = np.mean(thetas[:3])
        diff = recent_avg - early_avg
        if diff > 0.2:
            report["trend"] = "improving"
        elif diff < -0.2:
            report["trend"] = "declining"
        else:
            report["trend"] = "stable"
    elif len(thetas) >= 2:
        report["trend"] = "improving" if thetas[-1] > thetas[0] + 0.1 else "stable"
    else:
        report["trend"] = "insufficient_data"

    return report
