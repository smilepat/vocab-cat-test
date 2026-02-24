"""Bayesian online parameter calibration.

Updates item difficulty (b), discrimination (a), and guessing (c) parameters
based on accumulated response data, using empirical Bayes updating.
Supports 2PL and 3PL models.
"""
import numpy as np
from scipy.optimize import minimize_scalar, minimize

from ..models.irt_2pl import probability
from ..config import GUESSING_C_4CHOICE, GUESSING_C_BINARY


def update_difficulty_bayesian(
    current_b: float,
    responses: list[tuple[float, int]],
    a: float,
    c: float = 0.0,
    prior_sd: float = 0.5,
) -> float:
    """Update item difficulty using Bayesian posterior estimate.

    Args:
        current_b: Current difficulty estimate (prior mean)
        responses: List of (theta, response) pairs from test-takers
        a: Item discrimination parameter
        c: Item guessing parameter (0.0 for 2PL)
        prior_sd: Prior standard deviation

    Returns:
        Updated difficulty estimate (posterior mean)
    """
    if not responses:
        return current_b

    def neg_log_posterior(b: float) -> float:
        log_prior = -0.5 * ((b - current_b) / prior_sd) ** 2
        log_lik = 0.0
        for theta, resp in responses:
            p = probability(theta, a, b, c)
            p = np.clip(p, 1e-10, 1 - 1e-10)
            log_lik += resp * np.log(p) + (1 - resp) * np.log(1 - p)
        return -(log_prior + log_lik)

    result = minimize_scalar(neg_log_posterior, bounds=(-3.5, 3.5), method="bounded")
    return float(result.x)


def update_discrimination_bayesian(
    current_a: float,
    b: float,
    responses: list[tuple[float, int]],
    c: float = 0.0,
    prior_sd: float = 0.3,
) -> float:
    """Update item discrimination using Bayesian posterior estimate.

    Args:
        current_a: Current discrimination estimate (prior mean)
        b: Item difficulty parameter
        responses: List of (theta, response) pairs
        c: Item guessing parameter (0.0 for 2PL)
        prior_sd: Prior standard deviation

    Returns:
        Updated discrimination estimate (posterior mean)
    """
    if not responses or len(responses) < 20:
        return current_a

    def neg_log_posterior(a: float) -> float:
        if a < 0.1:
            return 1e10
        log_prior = -0.5 * ((a - current_a) / prior_sd) ** 2
        log_lik = 0.0
        for theta, resp in responses:
            p = probability(theta, a, b, c)
            p = np.clip(p, 1e-10, 1 - 1e-10)
            log_lik += resp * np.log(p) + (1 - resp) * np.log(1 - p)
        return -(log_prior + log_lik)

    result = minimize_scalar(neg_log_posterior, bounds=(0.2, 3.0), method="bounded")
    return float(result.x)


def update_guessing_bayesian(
    current_c: float,
    a: float,
    b: float,
    responses: list[tuple[float, int]],
    n_choices: int = 4,
    prior_sd: float = 0.05,
) -> float:
    """Update guessing parameter c using Bayesian posterior estimate.

    Uses a Beta-like prior centered on current_c with constraints:
    - c must be in [0.01, 1/n_choices] (cannot exceed random chance)
    - Requires many responses (500+) for stable estimation

    Args:
        current_c: Current guessing estimate (prior mean)
        a: Item discrimination parameter
        b: Item difficulty parameter
        responses: List of (theta, response) pairs
        n_choices: Number of answer choices (for upper bound)
        prior_sd: Prior standard deviation (tight — c is hard to estimate)

    Returns:
        Updated guessing estimate
    """
    if not responses or len(responses) < 500:
        return current_c

    c_upper = 1.0 / n_choices  # Cannot exceed random chance

    def neg_log_posterior(c: float) -> float:
        if c < 0.0 or c > c_upper:
            return 1e10
        log_prior = -0.5 * ((c - current_c) / prior_sd) ** 2
        log_lik = 0.0
        for theta, resp in responses:
            p = probability(theta, a, b, c)
            p = np.clip(p, 1e-10, 1 - 1e-10)
            log_lik += resp * np.log(p) + (1 - resp) * np.log(1 - p)
        return -(log_prior + log_lik)

    result = minimize_scalar(
        neg_log_posterior, bounds=(0.0, c_upper), method="bounded"
    )
    return float(np.clip(result.x, 0.0, c_upper))


def compute_empirical_difficulty(
    responses: list[tuple[float, int]],
) -> float | None:
    """Compute empirical difficulty from observed proportion correct.

    Useful as a sanity check against model-based estimates.
    """
    if not responses:
        return None
    total_correct = sum(r for _, r in responses)
    p_correct = total_correct / len(responses)
    if p_correct <= 0.01 or p_correct >= 0.99:
        return None
    from scipy import stats
    return float(-stats.norm.ppf(p_correct))


def calibrate_item(
    current_b: float,
    current_a: float,
    responses: list[tuple[float, int]],
    min_responses: int = 30,
    b_prior_sd: float = 0.5,
    a_prior_sd: float = 0.3,
    current_c: float = 0.0,
    use_3pl: bool = False,
    question_type: int = 1,
) -> tuple[float, float, float, dict]:
    """Full Bayesian calibration of an item's parameters.

    Args:
        current_b: Current difficulty
        current_a: Current discrimination
        responses: List of (theta_at_time, response) pairs
        min_responses: Minimum responses before updating a
        b_prior_sd: Prior SD for difficulty update
        a_prior_sd: Prior SD for discrimination update
        current_c: Current guessing parameter (0.0 for 2PL)
        use_3pl: Whether to estimate guessing parameter
        question_type: Question type (affects c upper bound)

    Returns:
        (new_b, new_a, new_c, metadata)
    """
    n = len(responses)
    if n == 0:
        return current_b, current_a, current_c, {"n_responses": 0, "updated": False}

    c = current_c
    new_b = update_difficulty_bayesian(current_b, responses, current_a, c, b_prior_sd)

    new_a = current_a
    if n >= min_responses:
        new_a = update_discrimination_bayesian(current_a, new_b, responses, c, a_prior_sd)

    new_c = current_c
    if use_3pl and n >= 500:
        n_choices = 2 if question_type == 6 else 4
        new_c = update_guessing_bayesian(current_c, new_a, new_b, responses, n_choices)

    empirical_b = compute_empirical_difficulty(responses)

    return new_b, new_a, new_c, {
        "n_responses": n,
        "updated": True,
        "b_change": round(new_b - current_b, 4),
        "a_change": round(new_a - current_a, 4),
        "c_change": round(new_c - current_c, 4) if use_3pl else 0.0,
        "empirical_b": round(empirical_b, 3) if empirical_b is not None else None,
        "p_correct": round(sum(r for _, r in responses) / n, 3),
        "model": "3PL" if use_3pl and n >= 500 else "2PL",
    }
