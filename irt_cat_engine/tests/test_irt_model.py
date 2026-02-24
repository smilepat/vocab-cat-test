"""Tests for IRT model core functions."""
import pytest
import numpy as np

from irt_cat_engine.models.irt_2pl import (
    probability, fisher_information, log_likelihood, ItemParameters,
    probability_array, fisher_information_array,
)
from irt_cat_engine.models.ability_estimator import (
    estimate_theta_eap, estimate_theta_mle, estimate_initial_theta,
)


class TestProbability:
    def test_midpoint(self):
        """When theta=b, P should be 0.5 for 2PL."""
        assert abs(probability(0.0, 1.0, 0.0) - 0.5) < 1e-6

    def test_high_theta(self):
        """High theta relative to b should give P near 1."""
        p = probability(3.0, 1.0, 0.0)
        assert p > 0.95

    def test_low_theta(self):
        """Low theta relative to b should give P near 0."""
        p = probability(-3.0, 1.0, 0.0)
        assert p < 0.05

    def test_high_discrimination(self):
        """Higher discrimination makes the curve steeper."""
        p_low_a = probability(0.5, 0.5, 0.0)
        p_high_a = probability(0.5, 2.0, 0.0)
        # Both should be > 0.5, but high a should be higher
        assert p_high_a > p_low_a

    def test_range(self):
        """P should always be in [0, 1]."""
        for theta in np.linspace(-5, 5, 100):
            p = probability(theta, 1.5, 0.0)
            assert 0 <= p <= 1

    def test_3pl_guessing(self):
        """With guessing c=0.25, P should be >= 0.25."""
        p = probability(-5.0, 1.0, 0.0, c=0.25)
        assert p >= 0.25 - 1e-6


class TestFisherInformation:
    def test_max_at_b(self):
        """Fisher information is maximized when theta=b for 2PL."""
        info_at_b = fisher_information(0.0, 1.0, 0.0)
        info_away = fisher_information(2.0, 1.0, 0.0)
        assert info_at_b > info_away

    def test_proportional_to_a_squared(self):
        """Information scales with a^2."""
        info_a1 = fisher_information(0.0, 1.0, 0.0)
        info_a2 = fisher_information(0.0, 2.0, 0.0)
        assert abs(info_a2 / info_a1 - 4.0) < 0.01

    def test_nonnegative(self):
        """Fisher information is always non-negative."""
        for theta in np.linspace(-5, 5, 50):
            info = fisher_information(theta, 1.0, 0.5)
            assert info >= 0


class TestAbilityEstimation:
    def _make_items(self, bs: list[float], a: float = 1.0) -> list[ItemParameters]:
        return [
            ItemParameters(item_id=i, word=f"w{i}", difficulty_b=b, discrimination_a=a)
            for i, b in enumerate(bs)
        ]

    def test_eap_all_correct_positive_theta(self):
        """All correct responses should give positive theta."""
        items = self._make_items([-1.0, 0.0, 1.0])
        responses = [1, 1, 1]
        theta, se = estimate_theta_eap(items, responses)
        assert theta > 0.5

    def test_eap_all_incorrect_negative_theta(self):
        """All incorrect responses should give negative theta."""
        items = self._make_items([-1.0, 0.0, 1.0])
        responses = [0, 0, 0]
        theta, se = estimate_theta_eap(items, responses)
        assert theta < -0.5

    def test_eap_mixed(self):
        """Mixed responses on medium items → theta near 0."""
        items = self._make_items([0.0, 0.0, 0.0, 0.0])
        responses = [1, 1, 0, 0]
        theta, se = estimate_theta_eap(items, responses)
        assert -0.5 < theta < 0.5

    def test_eap_se_decreases_with_more_items(self):
        """SE should decrease as more items are administered."""
        items_5 = self._make_items([0.0] * 5)
        items_20 = self._make_items([0.0] * 20)
        _, se_5 = estimate_theta_eap(items_5, [1, 0, 1, 0, 1])
        _, se_20 = estimate_theta_eap(items_20, [1, 0, 1, 0, 1] * 4)
        assert se_20 < se_5

    def test_eap_returns_finite(self):
        """EAP should always return finite values."""
        items = self._make_items([0.0])
        theta, se = estimate_theta_eap(items, [1])
        assert np.isfinite(theta)
        assert np.isfinite(se)
        assert se > 0

    def test_mle_mixed(self):
        """MLE on mixed responses should give reasonable estimate."""
        items = self._make_items([-1.0, 0.0, 1.0, 2.0])
        responses = [1, 1, 0, 0]
        theta, se = estimate_theta_mle(items, responses)
        assert -1.0 < theta < 1.5

    def test_initial_theta_grades(self):
        """Initial theta should vary by grade level."""
        t_elem = estimate_initial_theta("초3-4")
        t_mid = estimate_initial_theta("중2")
        t_high = estimate_initial_theta("고3")
        assert t_elem < t_mid < t_high


class TestArrayFunctions:
    def test_probability_array(self):
        items = [
            ItemParameters(item_id=0, word="a", difficulty_b=-1.0, discrimination_a=1.0),
            ItemParameters(item_id=1, word="b", difficulty_b=0.0, discrimination_a=1.0),
            ItemParameters(item_id=2, word="c", difficulty_b=1.0, discrimination_a=1.0),
        ]
        probs = probability_array(0.0, items)
        assert len(probs) == 3
        assert probs[0] > probs[1] > probs[2]  # easier items have higher P

    def test_info_array(self):
        items = [
            ItemParameters(item_id=0, word="a", difficulty_b=0.0, discrimination_a=0.5),
            ItemParameters(item_id=1, word="b", difficulty_b=0.0, discrimination_a=2.0),
        ]
        infos = fisher_information_array(0.0, items)
        assert infos[1] > infos[0]  # higher a → more info
