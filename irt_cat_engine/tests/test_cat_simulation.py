"""Simulation test: validate CAT system with virtual test-takers."""
import numpy as np
import pytest

from irt_cat_engine.models.irt_2pl import ItemParameters, probability
from irt_cat_engine.cat.session import CATSession
from irt_cat_engine.cat.stopping_rules import StoppingRules


def _generate_synthetic_item_pool(n: int = 500, seed: int = 42) -> list[ItemParameters]:
    """Generate a synthetic item pool for simulation."""
    rng = np.random.RandomState(seed)
    items = []
    topics = ["action", "emotions", "daily life", "animals", "health", "food", "nature", "society"]
    cefrs = ["A1", "A2", "B1", "B2", "C1"]
    pos_list = ["NOUN", "VERB", "ADJ"]

    for i in range(n):
        b = rng.normal(0, 1.2)  # difficulty centered at 0
        a = rng.uniform(0.5, 2.0)
        items.append(ItemParameters(
            item_id=i,
            word=f"word_{i}",
            difficulty_b=float(np.clip(b, -3, 3)),
            discrimination_a=float(a),
            guessing_c=0.0,
            question_type=rng.choice([1, 2, 3, 5]),
            pos=rng.choice(pos_list),
            cefr=cefrs[min(int((b + 3) / 6 * 5), 4)],
            topic=rng.choice(topics),
        ))
    return items


def _simulate_response(theta_true: float, item: ItemParameters, rng: np.random.RandomState) -> bool:
    """Simulate a response based on the 2PL model."""
    p = probability(theta_true, item.discrimination_a, item.difficulty_b)
    return bool(rng.random() < p)


class TestCATSimulation:
    """Simulation tests with synthetic data."""

    @pytest.fixture
    def item_pool(self):
        return _generate_synthetic_item_pool(n=500)

    def test_single_simulation(self, item_pool):
        """A single simulated test-taker should get reasonable estimate."""
        rng = np.random.RandomState(123)
        theta_true = 0.5

        session = CATSession(
            item_pool=item_pool,
            initial_theta=0.0,
            stopping_rules=StoppingRules(min_items=10, max_items=30, se_threshold=0.35),
        )

        while not session.is_complete:
            item = session.get_next_item()
            if item is None:
                break
            is_correct = _simulate_response(theta_true, item, rng)
            session.record_response(item, is_correct)

        assert session.is_complete
        assert abs(session.current_theta - theta_true) < 1.5  # Rough check
        assert len(session.responses) >= 10
        assert len(session.responses) <= 30

    def test_high_ability_learner(self, item_pool):
        """High ability learner (theta=2) should get positive estimate."""
        rng = np.random.RandomState(456)
        theta_true = 2.0

        session = CATSession(
            item_pool=item_pool,
            initial_theta=0.0,
            stopping_rules=StoppingRules(min_items=15, max_items=30),
        )

        while not session.is_complete:
            item = session.get_next_item()
            if item is None:
                break
            is_correct = _simulate_response(theta_true, item, rng)
            session.record_response(item, is_correct)

        assert session.current_theta > 0.5

    def test_low_ability_learner(self, item_pool):
        """Low ability learner (theta=-2) should get negative estimate."""
        rng = np.random.RandomState(789)
        theta_true = -2.0

        session = CATSession(
            item_pool=item_pool,
            initial_theta=0.0,
            stopping_rules=StoppingRules(min_items=15, max_items=30),
        )

        while not session.is_complete:
            item = session.get_next_item()
            if item is None:
                break
            is_correct = _simulate_response(theta_true, item, rng)
            session.record_response(item, is_correct)

        assert session.current_theta < -0.5

    def test_results_report(self, item_pool):
        """Results report should contain all expected fields."""
        rng = np.random.RandomState(111)
        theta_true = 0.0

        session = CATSession(
            item_pool=item_pool,
            initial_theta=0.0,
            stopping_rules=StoppingRules(min_items=15, max_items=20),
        )

        while not session.is_complete:
            item = session.get_next_item()
            if item is None:
                break
            is_correct = _simulate_response(theta_true, item, rng)
            session.record_response(item, is_correct)

        results = session.get_results()

        assert "theta" in results
        assert "se" in results
        assert "cefr_level" in results
        assert "cefr_probabilities" in results
        assert "curriculum_level" in results
        assert "vocab_size_estimate" in results
        assert "accuracy" in results
        assert results["cefr_level"] in ["A1", "A2", "B1", "B2", "C1"]
        assert results["vocab_size_estimate"] > 0
        assert 0 <= results["accuracy"] <= 1

    def test_batch_simulation_rmse(self, item_pool):
        """Batch simulation: RMSE should be < 0.6 with 500-item pool."""
        n_simulations = 100
        rng = np.random.RandomState(42)
        theta_trues = rng.uniform(-2.5, 2.5, n_simulations)
        errors = []

        for theta_true in theta_trues:
            session = CATSession(
                item_pool=item_pool,
                initial_theta=0.0,
                stopping_rules=StoppingRules(min_items=15, max_items=30, se_threshold=0.35),
            )

            while not session.is_complete:
                item = session.get_next_item()
                if item is None:
                    break
                is_correct = _simulate_response(float(theta_true), item, rng)
                session.record_response(item, is_correct)

            errors.append(session.current_theta - float(theta_true))

        errors = np.array(errors)
        rmse = float(np.sqrt(np.mean(errors ** 2)))
        bias = float(np.mean(np.abs(errors)))
        correlation = float(np.corrcoef(theta_trues, theta_trues + errors)[0, 1])

        # Relaxed criteria for 500-item pool (plan targets are for full 9183 pool)
        assert rmse < 0.6, f"RMSE {rmse:.3f} exceeds 0.6"
        assert bias < 0.5, f"Mean absolute bias {bias:.3f} exceeds 0.5"
        assert correlation > 0.85, f"Correlation {correlation:.3f} below 0.85"
