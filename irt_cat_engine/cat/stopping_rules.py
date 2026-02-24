"""CAT stopping criteria."""
from ..config import (
    CAT_MIN_ITEMS, CAT_MAX_ITEMS, CAT_SE_THRESHOLD,
    CAT_CONVERGENCE_WINDOW, CAT_CONVERGENCE_EPSILON,
)


class StoppingRules:
    """Evaluate whether a CAT session should terminate."""

    def __init__(
        self,
        min_items: int = CAT_MIN_ITEMS,
        max_items: int = CAT_MAX_ITEMS,
        se_threshold: float = CAT_SE_THRESHOLD,
        convergence_window: int = CAT_CONVERGENCE_WINDOW,
        convergence_epsilon: float = CAT_CONVERGENCE_EPSILON,
    ):
        self.min_items = min_items
        self.max_items = max_items
        self.se_threshold = se_threshold
        self.convergence_window = convergence_window
        self.convergence_epsilon = convergence_epsilon

    def should_stop(
        self,
        items_completed: int,
        current_se: float,
        theta_history: list[float],
    ) -> tuple[bool, str]:
        """Check whether the test should stop.

        Returns:
            (should_stop, reason)
        """
        # Maximum items reached
        if items_completed >= self.max_items:
            return True, "max_items"

        # Below minimum: never stop
        if items_completed < self.min_items:
            return False, ""

        # SE threshold reached
        if current_se < self.se_threshold:
            return True, "se_threshold"

        # Convergence: last N theta estimates are stable
        if len(theta_history) >= self.convergence_window:
            recent = theta_history[-self.convergence_window:]
            diffs = [abs(recent[i] - recent[i - 1]) for i in range(1, len(recent))]
            if all(d < self.convergence_epsilon for d in diffs):
                return True, "convergence"

        return False, ""
