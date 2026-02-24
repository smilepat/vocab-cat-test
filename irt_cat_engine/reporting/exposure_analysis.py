"""Item exposure analysis for monitoring test pool health.

Identifies over-exposed and under-used items, provides pool utilization
metrics, and generates recommendations for pool expansion.
"""
import numpy as np

from ..models.irt_2pl import ItemParameters


def analyze_exposure(
    items: list[ItemParameters],
    exposure_counts: dict[int, int],
    total_sessions: int,
    max_exposure_target: float = 0.25,
) -> dict:
    """Analyze item exposure rates across the pool.

    Args:
        items: Full item pool
        exposure_counts: Dict mapping item_id -> number of times administered
        total_sessions: Total number of test sessions conducted
        max_exposure_target: Target maximum exposure rate (Sympson-Hetter)

    Returns:
        Comprehensive exposure analysis report
    """
    if total_sessions == 0:
        return {
            "total_sessions": 0,
            "pool_size": len(items),
            "message": "No sessions conducted yet",
        }

    # Compute exposure rates
    rates = []
    never_used = []
    over_exposed = []
    under_used = []

    for item in items:
        count = exposure_counts.get(item.item_id, 0)
        rate = count / total_sessions
        rates.append(rate)

        if count == 0:
            never_used.append(item.item_id)
        elif rate > max_exposure_target:
            over_exposed.append({
                "item_id": item.item_id,
                "word": item.word,
                "rate": round(rate, 4),
                "count": count,
                "difficulty_b": round(item.difficulty_b, 3),
                "cefr": item.cefr,
            })

    rates_array = np.array(rates)

    # Pool utilization: what fraction of items have been used at least once
    items_used = sum(1 for r in rates if r > 0)
    utilization = items_used / len(items) if items else 0.0

    # Effective pool size: items with non-negligible exposure
    effective_pool = sum(1 for r in rates if r >= 0.01)

    # Gini coefficient for exposure inequality
    gini = _compute_gini(rates_array)

    # Distribution by CEFR
    cefr_exposure: dict[str, list[float]] = {}
    for item, rate in zip(items, rates):
        cefr_exposure.setdefault(item.cefr, []).append(rate)

    cefr_stats = {}
    for cefr, cefr_rates in sorted(cefr_exposure.items()):
        arr = np.array(cefr_rates)
        cefr_stats[cefr] = {
            "count": len(arr),
            "mean_rate": round(float(np.mean(arr)), 4),
            "max_rate": round(float(np.max(arr)), 4),
            "used_pct": round(float(np.mean(arr > 0)) * 100, 1),
        }

    # Distribution by difficulty band
    difficulty_bands = [
        ("very_easy", -3.0, -1.5),
        ("easy", -1.5, -0.5),
        ("medium", -0.5, 0.5),
        ("hard", 0.5, 1.5),
        ("very_hard", 1.5, 3.0),
    ]
    band_stats = {}
    for label, lo, hi in difficulty_bands:
        band_rates = [r for item, r in zip(items, rates) if lo <= item.difficulty_b < hi]
        if band_rates:
            arr = np.array(band_rates)
            band_stats[label] = {
                "count": len(arr),
                "mean_rate": round(float(np.mean(arr)), 4),
                "used_pct": round(float(np.mean(arr > 0)) * 100, 1),
            }

    # Recommendations
    recommendations = _generate_recommendations(
        utilization, gini, over_exposed, never_used, len(items), total_sessions
    )

    return {
        "total_sessions": total_sessions,
        "pool_size": len(items),
        "items_used": items_used,
        "items_never_used": len(never_used),
        "utilization_pct": round(utilization * 100, 1),
        "effective_pool_size": effective_pool,
        "mean_exposure_rate": round(float(np.mean(rates_array)), 4),
        "median_exposure_rate": round(float(np.median(rates_array)), 4),
        "max_exposure_rate": round(float(np.max(rates_array)), 4),
        "std_exposure_rate": round(float(np.std(rates_array)), 4),
        "gini_coefficient": round(gini, 4),
        "over_exposed_count": len(over_exposed),
        "over_exposed_items": sorted(over_exposed, key=lambda x: -x["rate"])[:20],
        "cefr_exposure": cefr_stats,
        "difficulty_band_exposure": band_stats,
        "recommendations": recommendations,
    }


def _compute_gini(values: np.ndarray) -> float:
    """Compute Gini coefficient (0 = perfect equality, 1 = perfect inequality)."""
    if len(values) == 0 or np.sum(values) == 0:
        return 0.0
    sorted_vals = np.sort(values)
    n = len(sorted_vals)
    index = np.arange(1, n + 1)
    return float((2 * np.sum(index * sorted_vals) - (n + 1) * np.sum(sorted_vals)) / (n * np.sum(sorted_vals)))


def _generate_recommendations(
    utilization: float,
    gini: float,
    over_exposed: list[dict],
    never_used: list[int],
    pool_size: int,
    total_sessions: int,
) -> list[str]:
    """Generate actionable recommendations based on exposure analysis."""
    recs = []

    if utilization < 0.3 and total_sessions >= 100:
        recs.append(
            f"Low pool utilization ({utilization*100:.0f}%). "
            "Consider adjusting content balance constraints to allow more diverse item selection."
        )

    if gini > 0.7:
        recs.append(
            f"High exposure inequality (Gini={gini:.2f}). "
            "A small subset of items dominates. Tighten Sympson-Hetter exposure control."
        )

    if len(over_exposed) > pool_size * 0.05:
        recs.append(
            f"{len(over_exposed)} items exceed target exposure rate. "
            "Recalibrate exposure control parameters."
        )

    if len(never_used) > pool_size * 0.5 and total_sessions >= 500:
        recs.append(
            f"{len(never_used)} items ({len(never_used)/pool_size*100:.0f}%) never used. "
            "Review item parameters — some may have unreachable difficulty levels."
        )

    if total_sessions >= 5000 and utilization > 0.8:
        recs.append(
            "High utilization with many sessions. Consider expanding the item pool "
            "with additional question types or vocabulary sources."
        )

    if not recs:
        recs.append("Pool health is good. No immediate action needed.")

    return recs


def identify_expansion_needs(
    items: list[ItemParameters],
    exposure_counts: dict[int, int],
    total_sessions: int,
) -> dict:
    """Identify areas where the item pool needs expansion.

    Returns analysis of which difficulty ranges, CEFR levels, and topics
    need more items based on exposure patterns.
    """
    if total_sessions < 100:
        return {"message": "Insufficient data for expansion analysis", "min_sessions": 100}

    # Find difficulty gaps: ranges where items are over-exposed
    rates_by_b = []
    for item in items:
        count = exposure_counts.get(item.item_id, 0)
        rate = count / total_sessions
        rates_by_b.append((item.difficulty_b, rate, item.cefr, item.topic))

    # Group by difficulty bands
    bands = {}
    for b, rate, cefr, topic in rates_by_b:
        band = round(b * 2) / 2  # Round to 0.5 increments
        bands.setdefault(band, []).append(rate)

    high_demand_bands = []
    for band, band_rates in sorted(bands.items()):
        mean_rate = float(np.mean(band_rates))
        if mean_rate > 0.15:  # High demand relative to pool
            high_demand_bands.append({
                "difficulty_range": f"{band:.1f} to {band+0.5:.1f}",
                "item_count": len(band_rates),
                "mean_exposure": round(mean_rate, 4),
            })

    # CEFR gaps
    cefr_needs = {}
    cefr_groups: dict[str, list[float]] = {}
    for item in items:
        count = exposure_counts.get(item.item_id, 0)
        rate = count / total_sessions
        cefr_groups.setdefault(item.cefr, []).append(rate)

    for cefr, cefr_rates in sorted(cefr_groups.items()):
        mean_rate = float(np.mean(cefr_rates))
        if mean_rate > 0.10:
            cefr_needs[cefr] = {
                "current_items": len(cefr_rates),
                "mean_exposure": round(mean_rate, 4),
                "suggested_additional": max(10, int(len(cefr_rates) * 0.3)),
            }

    return {
        "total_sessions": total_sessions,
        "high_demand_difficulty_bands": high_demand_bands,
        "cefr_expansion_needs": cefr_needs,
    }
