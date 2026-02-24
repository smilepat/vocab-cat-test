"""CAT item selection with maximum information + content balancing + exposure control."""
import random

import numpy as np

from ..config import CONTENT_BALANCE, CAT_MAX_EXPOSURE_RATE, LOANWORD_MAX_PER_TEST
from ..models.irt_2pl import ItemParameters, fisher_information


class ContentTracker:
    """Track content balance during a test session."""

    def __init__(self):
        self.pos_counts: dict[str, int] = {}
        self.topic_counts: dict[str, int] = {}
        self.type_counts: dict[int, int] = {}
        self.cefr_counts: dict[str, int] = {}
        self.loanword_count: int = 0
        self.total = 0

    def record(self, item: ItemParameters):
        self.pos_counts[item.pos] = self.pos_counts.get(item.pos, 0) + 1
        self.topic_counts[item.topic] = self.topic_counts.get(item.topic, 0) + 1
        self.type_counts[item.question_type] = self.type_counts.get(item.question_type, 0) + 1
        self.cefr_counts[item.cefr] = self.cefr_counts.get(item.cefr, 0) + 1
        if item.is_loanword:
            self.loanword_count += 1
        self.total += 1

    def is_topic_ok(self, topic: str) -> bool:
        max_same = CONTENT_BALANCE["max_same_topic"]
        return self.topic_counts.get(topic, 0) < max_same

    def is_loanword_ok(self, is_loanword: bool) -> bool:
        if not is_loanword:
            return True
        return self.loanword_count < LOANWORD_MAX_PER_TEST

    def preferred_question_types(self, items_completed: int) -> list[int] | None:
        """Return preferred question types based on test progression."""
        if items_completed < 5:
            return [1, 2]  # Receptive only for warm-up
        elif items_completed < 15:
            return [1, 2, 3, 5]  # Add relational and contextual
        return None  # All types eligible


class ExposureController:
    """Sympson-Hetter exposure control."""

    def __init__(self, item_count: int, target_max_rate: float = CAT_MAX_EXPOSURE_RATE):
        self.k = {i: 1.0 for i in range(item_count)}  # exposure parameters
        self.admin_counts = {i: 0 for i in range(item_count)}
        self.select_counts = {i: 0 for i in range(item_count)}
        self.total_tests = 0
        self.target = target_max_rate

    def is_eligible(self, item_id: int) -> bool:
        """Probabilistic eligibility check."""
        return random.random() < self.k.get(item_id, 1.0)

    def record_selection(self, item_id: int):
        self.select_counts[item_id] = self.select_counts.get(item_id, 0) + 1

    def record_administration(self, item_id: int):
        self.admin_counts[item_id] = self.admin_counts.get(item_id, 0) + 1

    def end_test(self):
        self.total_tests += 1

    def recalibrate(self):
        """Recalibrate exposure parameters based on actual rates."""
        if self.total_tests < 10:
            return
        for item_id in self.k:
            if self.select_counts.get(item_id, 0) > 0:
                actual_rate = self.admin_counts.get(item_id, 0) / self.total_tests
                if actual_rate > self.target:
                    self.k[item_id] *= self.target / actual_rate
                else:
                    self.k[item_id] = min(1.0, self.k[item_id] * 1.05)


def select_next_item(
    theta: float,
    item_pool: list[ItemParameters],
    administered_ids: set[int],
    content_tracker: ContentTracker,
    exposure_controller: ExposureController | None = None,
    top_n: int = 5,
) -> ItemParameters | None:
    """Select the next item using maximum Fisher information with constraints.

    Args:
        theta: Current ability estimate
        item_pool: Full item pool
        administered_ids: Set of already-administered item IDs
        content_tracker: Tracks content balance
        exposure_controller: Optional exposure control
        top_n: Select randomly from top-N highest information items

    Returns:
        Selected item or None if no eligible items
    """
    # 1. Filter out administered items
    available = [item for item in item_pool if item.item_id not in administered_ids]
    if not available:
        return None

    # 2. Apply content constraints
    preferred_types = content_tracker.preferred_question_types(content_tracker.total)
    candidates = []
    for item in available:
        # Topic constraint
        if not content_tracker.is_topic_ok(item.topic):
            continue
        # Loanword constraint
        if not content_tracker.is_loanword_ok(item.is_loanword):
            continue
        # Question type preference
        if preferred_types is not None and item.question_type not in preferred_types:
            continue
        candidates.append(item)

    # Fallback: if too few candidates after filtering, relax constraints
    if len(candidates) < top_n:
        candidates = [
            item for item in available
            if content_tracker.is_topic_ok(item.topic)
        ]
    if len(candidates) < top_n:
        candidates = available

    # 3. Apply exposure control
    if exposure_controller is not None:
        eligible = [item for item in candidates if exposure_controller.is_eligible(item.item_id)]
        if eligible:
            candidates = eligible

    # 4. Calculate Fisher Information
    info_items = []
    for item in candidates:
        info = fisher_information(theta, item.discrimination_a, item.difficulty_b, item.guessing_c)
        info_items.append((info, item))

    # 5. Select from top-N
    info_items.sort(key=lambda x: x[0], reverse=True)
    top_items = [item for _, item in info_items[:top_n]]

    if not top_items:
        return None

    selected = random.choice(top_items)

    # Record
    if exposure_controller is not None:
        exposure_controller.record_selection(selected.item_id)
        exposure_controller.record_administration(selected.item_id)

    return selected
