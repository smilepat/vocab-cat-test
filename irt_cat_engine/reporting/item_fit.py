"""Item fit analysis: infit and outfit mean-square statistics.

Used to identify poorly functioning items that don't fit the IRT model.
- Infit MNSQ: information-weighted, sensitive to unexpected responses near item difficulty
- Outfit MNSQ: unweighted, sensitive to outlier responses far from item difficulty

Acceptable range: 0.7 - 1.3 (Wilson, 2005)
"""
import numpy as np

from ..models.irt_2pl import probability


def compute_item_fit(
    b: float,
    a: float,
    responses: list[tuple[float, int]],
    c: float = 0.0,
) -> dict:
    """Compute infit and outfit statistics for a single item.

    Args:
        b: Item difficulty
        a: Item discrimination
        responses: List of (theta, response) pairs
        c: Guessing parameter (0 for 2PL)

    Returns:
        Dict with infit_mnsq, outfit_mnsq, n_responses, and flags
    """
    if len(responses) < 5:
        return {
            "infit_mnsq": None,
            "outfit_mnsq": None,
            "n_responses": len(responses),
            "flag": "insufficient_data",
        }

    # Compute expected scores and variances for each response
    z_sq_weighted = []  # For infit
    z_sq_unweighted = []  # For outfit
    variances = []

    for theta, resp in responses:
        p = probability(theta, a, b, c)
        p = np.clip(p, 1e-6, 1 - 1e-6)
        q = 1.0 - p
        variance = p * q

        # Standardized residual squared
        residual = resp - p
        z_sq = (residual ** 2) / variance if variance > 1e-10 else 0.0

        z_sq_weighted.append(z_sq * variance)
        z_sq_unweighted.append(z_sq)
        variances.append(variance)

    total_variance = sum(variances)

    # Infit MNSQ: variance-weighted
    infit_mnsq = sum(z_sq_weighted) / total_variance if total_variance > 0 else 1.0

    # Outfit MNSQ: unweighted mean
    outfit_mnsq = np.mean(z_sq_unweighted)

    # Flag problematic items
    flag = "ok"
    if infit_mnsq > 1.3 or outfit_mnsq > 1.3:
        flag = "underfit"  # Too much noise / item doesn't discriminate well
    elif infit_mnsq < 0.7 or outfit_mnsq < 0.7:
        flag = "overfit"  # Too predictable / redundant item

    return {
        "infit_mnsq": round(float(infit_mnsq), 3),
        "outfit_mnsq": round(float(outfit_mnsq), 3),
        "n_responses": len(responses),
        "flag": flag,
    }


def analyze_item_bank_fit(
    items_data: list[dict],
) -> dict:
    """Analyze fit statistics across the item bank.

    Args:
        items_data: List of dicts with keys: b, a, responses [(theta, resp), ...]

    Returns:
        Summary statistics and flagged items
    """
    results = []
    flagged_underfit = []
    flagged_overfit = []
    insufficient = 0

    for item in items_data:
        fit = compute_item_fit(
            b=item["b"],
            a=item["a"],
            responses=item["responses"],
            c=item.get("c", 0.0),
        )
        fit["item_id"] = item.get("item_id", -1)
        fit["word"] = item.get("word", "")
        results.append(fit)

        if fit["flag"] == "underfit":
            flagged_underfit.append(fit)
        elif fit["flag"] == "overfit":
            flagged_overfit.append(fit)
        elif fit["flag"] == "insufficient_data":
            insufficient += 1

    # Summary
    valid = [r for r in results if r["infit_mnsq"] is not None]
    infits = [r["infit_mnsq"] for r in valid]
    outfits = [r["outfit_mnsq"] for r in valid]

    return {
        "total_items": len(items_data),
        "analyzed": len(valid),
        "insufficient_data": insufficient,
        "mean_infit": round(float(np.mean(infits)), 3) if infits else None,
        "mean_outfit": round(float(np.mean(outfits)), 3) if outfits else None,
        "underfit_count": len(flagged_underfit),
        "overfit_count": len(flagged_overfit),
        "flagged_underfit": sorted(flagged_underfit, key=lambda x: -x["infit_mnsq"])[:20],
        "flagged_overfit": sorted(flagged_overfit, key=lambda x: x["infit_mnsq"])[:20],
    }
