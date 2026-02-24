"""Two-Parameter Logistic (2PL) IRT Model."""
import numpy as np
from dataclasses import dataclass


@dataclass
class ItemParameters:
    """IRT item parameters."""
    item_id: int
    word: str
    difficulty_b: float
    discrimination_a: float
    guessing_c: float = 0.0  # Reserved for 3PL upgrade
    question_type: int = 1
    pos: str = ""
    cefr: str = ""
    topic: str = ""
    is_loanword: bool = False


def probability(theta: float, a: float, b: float, c: float = 0.0) -> float:
    """Calculate probability of correct response under 2PL (or 3PL) model.

    P(X=1|θ) = c + (1-c) / (1 + exp(-a*(θ-b)))
    For 2PL, c=0: P(X=1|θ) = 1 / (1 + exp(-a*(θ-b)))
    """
    exponent = -a * (theta - b)
    exponent = np.clip(exponent, -500, 500)  # Prevent overflow
    p = c + (1.0 - c) / (1.0 + np.exp(exponent))
    return float(p)


def probability_array(theta: float, items: list[ItemParameters]) -> np.ndarray:
    """Calculate probabilities for multiple items at once."""
    a = np.array([item.discrimination_a for item in items])
    b = np.array([item.difficulty_b for item in items])
    c = np.array([item.guessing_c for item in items])
    exponent = np.clip(-a * (theta - b), -500, 500)
    return c + (1.0 - c) / (1.0 + np.exp(exponent))


def fisher_information(theta: float, a: float, b: float, c: float = 0.0) -> float:
    """Calculate Fisher Information of an item at a given theta.

    For 2PL: I(θ) = a² * P(θ) * Q(θ)
    For 3PL: I(θ) = a² * Q(θ) * (P(θ)-c)² / ((1-c)² * P(θ))
    """
    p = probability(theta, a, b, c)
    q = 1.0 - p

    if c == 0.0:
        # 2PL formula
        return a * a * p * q
    else:
        # 3PL formula
        if p < 1e-10:
            return 0.0
        return a * a * q * (p - c) ** 2 / ((1.0 - c) ** 2 * p)


def fisher_information_array(theta: float, items: list[ItemParameters]) -> np.ndarray:
    """Calculate Fisher Information for multiple items."""
    return np.array([
        fisher_information(theta, item.discrimination_a, item.difficulty_b, item.guessing_c)
        for item in items
    ])


def log_likelihood(theta: float, items: list[ItemParameters], responses: list[int]) -> float:
    """Calculate log-likelihood of response pattern given theta."""
    ll = 0.0
    for item, response in zip(items, responses):
        p = probability(theta, item.discrimination_a, item.difficulty_b, item.guessing_c)
        p = np.clip(p, 1e-10, 1.0 - 1e-10)
        if response == 1:
            ll += np.log(p)
        else:
            ll += np.log(1.0 - p)
    return ll
