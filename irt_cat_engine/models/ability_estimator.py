"""Ability (theta) estimation methods: EAP, MLE, MAP."""
import numpy as np
from scipy import stats

from ..config import (
    EAP_QUADRATURE_POINTS, EAP_QUAD_RANGE,
    THETA_PRIOR_MEAN, THETA_PRIOR_SD, THETA_RANGE,
)
from .irt_2pl import ItemParameters, probability


def estimate_theta_eap(
    items: list[ItemParameters],
    responses: list[int],
    dont_know_flags: list[bool] | None = None,
    prior_mean: float = THETA_PRIOR_MEAN,
    prior_sd: float = THETA_PRIOR_SD,
) -> tuple[float, float]:
    """Estimate theta using Expected A Posteriori (EAP) with Gauss-Hermite quadrature.

    Args:
        items: List of administered items
        responses: List of responses (1=correct, 0=incorrect)
        dont_know_flags: Optional list of booleans. When True for a response,
            the guessing parameter c is overridden to 0 for that response.
            In 2PL mode (c=0 everywhere), this has no effect.
            In 3PL mode, it provides more accurate estimation by removing
            guessing noise from "don't know" responses.

    Returns:
        (theta_hat, standard_error)
    """
    quad_points = np.linspace(EAP_QUAD_RANGE[0], EAP_QUAD_RANGE[1], EAP_QUADRATURE_POINTS)
    prior = stats.norm.pdf(quad_points, loc=prior_mean, scale=prior_sd)

    # Compute likelihood at each quadrature point
    likelihood = np.ones_like(quad_points)
    for i, (item, response) in enumerate(zip(items, responses)):
        # Override guessing_c to 0 for "don't know" responses
        c = 0.0 if (dont_know_flags and dont_know_flags[i]) else item.guessing_c
        p = np.array([
            probability(theta, item.discrimination_a, item.difficulty_b, c)
            for theta in quad_points
        ])
        p = np.clip(p, 1e-10, 1.0 - 1e-10)
        if response == 1:
            likelihood *= p
        else:
            likelihood *= (1.0 - p)

    # Posterior = likelihood * prior
    posterior = likelihood * prior
    total = np.trapezoid(posterior, quad_points)
    if total < 1e-30:
        # Fallback if posterior is essentially zero everywhere
        return prior_mean, prior_sd
    posterior /= total

    # EAP estimate = E[theta | data]
    theta_hat = float(np.trapezoid(quad_points * posterior, quad_points))

    # Standard error = sqrt(Var[theta | data])
    variance = float(np.trapezoid((quad_points - theta_hat) ** 2 * posterior, quad_points))
    se = np.sqrt(max(variance, 1e-10))

    return theta_hat, se


def estimate_theta_mle(
    items: list[ItemParameters],
    responses: list[int],
    max_iter: int = 50,
    tol: float = 1e-4,
) -> tuple[float, float]:
    """Estimate theta using Maximum Likelihood Estimation (Newton-Raphson).

    Returns:
        (theta_hat, standard_error)

    Note: MLE can fail when all responses are correct or all incorrect.
    Use EAP as a fallback.
    """
    # Check for all-correct or all-incorrect
    if all(r == 1 for r in responses):
        return THETA_RANGE[1], 1.5  # Return upper bound with high SE
    if all(r == 0 for r in responses):
        return THETA_RANGE[0], 1.5  # Return lower bound with high SE

    theta = 0.0  # Starting point

    for _ in range(max_iter):
        # First and second derivatives of log-likelihood
        dl = 0.0   # First derivative
        d2l = 0.0  # Second derivative

        for item, response in zip(items, responses):
            a = item.discrimination_a
            b = item.difficulty_b
            p = probability(theta, a, b, item.guessing_c)
            p = np.clip(p, 1e-10, 1.0 - 1e-10)
            q = 1.0 - p

            dl += a * (response - p)
            d2l -= a * a * p * q

        if abs(d2l) < 1e-10:
            break

        delta = -dl / d2l
        theta = float(np.clip(theta + delta, THETA_RANGE[0], THETA_RANGE[1]))

        if abs(delta) < tol:
            break

    # SE from observed information
    se = 1.0 / np.sqrt(max(abs(d2l), 1e-10))

    return theta, se


def estimate_initial_theta(
    grade: str,
    self_assess: str = "intermediate",
    exam_experience: str = "none",
    knows_calibrator: bool | None = None,
) -> float:
    """Estimate initial theta from user profile survey.

    Args:
        grade: Grade level (초3-4, 초5-6, 중1, ..., 대학, 성인)
        self_assess: Self-assessed level (beginner, intermediate, advanced)
        exam_experience: Exam experience (none, 내신, 수능, TOEIC, TOEFL)
        knows_calibrator: Whether user knows the calibrator word "determine"
    """
    from ..config import GRADE_THETA, SELF_ASSESS_ADJUST, EXAM_ADJUST

    theta = GRADE_THETA.get(grade, 0.0)
    theta += SELF_ASSESS_ADJUST.get(self_assess, 0.0)
    theta += EXAM_ADJUST.get(exam_experience, 0.0)

    if knows_calibrator is True:
        theta = max(theta, 0.0)
    elif knows_calibrator is False:
        theta = min(theta, 0.0)

    return float(np.clip(theta, THETA_RANGE[0], THETA_RANGE[1]))
