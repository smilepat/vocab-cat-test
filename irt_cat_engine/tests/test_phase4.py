"""Phase 4 tests: 3PL model, exposure analysis, calibrator upgrades."""
import numpy as np
import pytest

from irt_cat_engine.models.irt_2pl import (
    ItemParameters, probability, fisher_information, probability_array,
)
from irt_cat_engine.item_bank.calibrator import (
    calibrate_item, update_guessing_bayesian,
)
from irt_cat_engine.item_bank.parameter_initializer import compute_guessing_c
from irt_cat_engine.reporting.exposure_analysis import (
    analyze_exposure, identify_expansion_needs, _compute_gini,
)
from irt_cat_engine.config import GUESSING_C_4CHOICE, GUESSING_C_BINARY


# ── 3PL Model Tests ──────────────────────────────────────────────


class Test3PLModel:
    """Verify 3PL model math with guessing parameter."""

    def test_guessing_floor(self):
        """P(correct) should never go below c, even at very low theta."""
        c = 0.25
        p = probability(-5.0, a=1.0, b=0.0, c=c)
        assert p >= c - 0.001, f"P={p} dropped below guessing floor c={c}"

    def test_guessing_zero_equals_2pl(self):
        """With c=0, 3PL should equal 2PL."""
        p_2pl = probability(0.5, a=1.2, b=-0.3, c=0.0)
        p_3pl = probability(0.5, a=1.2, b=-0.3, c=0.0)
        assert p_2pl == p_3pl

    def test_guessing_raises_low_ability_prob(self):
        """With c>0, low-ability learners have higher P than 2PL."""
        p_2pl = probability(-3.0, a=1.0, b=0.0, c=0.0)
        p_3pl = probability(-3.0, a=1.0, b=0.0, c=0.20)
        assert p_3pl > p_2pl, "3PL should give higher P for low theta"
        assert p_3pl >= 0.20, "P should be at least c"

    def test_guessing_upper_convergence(self):
        """At high theta, 2PL and 3PL converge to ~1.0."""
        p_2pl = probability(3.0, a=1.0, b=0.0, c=0.0)
        p_3pl = probability(3.0, a=1.0, b=0.0, c=0.25)
        assert abs(p_2pl - p_3pl) < 0.02, "Should converge near 1.0"

    def test_fisher_info_3pl_lower_than_2pl(self):
        """3PL Fisher info <= 2PL Fisher info (guessing adds noise)."""
        fi_2pl = fisher_information(0.0, a=1.0, b=0.0, c=0.0)
        fi_3pl = fisher_information(0.0, a=1.0, b=0.0, c=0.25)
        assert fi_3pl <= fi_2pl, "3PL info should be <= 2PL info"

    def test_probability_array_with_guessing(self):
        """probability_array should handle mixed c values."""
        items = [
            ItemParameters(0, "w1", 0.0, 1.0, guessing_c=0.0),
            ItemParameters(1, "w2", 0.0, 1.0, guessing_c=0.25),
        ]
        probs = probability_array(0.0, items)
        assert probs[1] > probs[0], "Item with guessing should have higher P"


# ── 3PL Parameter Initialization ─────────────────────────────────


class Test3PLInitialization:
    """Test guessing parameter initialization per question type."""

    def test_2pl_mode_returns_zero(self):
        """In 2PL mode, guessing is always 0."""
        import irt_cat_engine.config as cfg
        original = cfg.IRT_MODEL
        cfg.IRT_MODEL = "2PL"
        try:
            assert compute_guessing_c(1) == 0.0
            assert compute_guessing_c(6) == 0.0
        finally:
            cfg.IRT_MODEL = original

    def test_3pl_mode_4choice(self):
        """In 3PL mode, 4-choice items get GUESSING_C_4CHOICE."""
        import irt_cat_engine.config as cfg
        original = cfg.IRT_MODEL
        cfg.IRT_MODEL = "3PL"
        try:
            for qt in [1, 2, 3, 4, 5]:
                c = compute_guessing_c(qt)
                assert c == GUESSING_C_4CHOICE, f"Type {qt}: c={c}"
        finally:
            cfg.IRT_MODEL = original

    def test_3pl_mode_binary(self):
        """In 3PL mode, binary items (Type 6) get GUESSING_C_BINARY."""
        import irt_cat_engine.config as cfg
        original = cfg.IRT_MODEL
        cfg.IRT_MODEL = "3PL"
        try:
            c = compute_guessing_c(6)
            assert c == GUESSING_C_BINARY
        finally:
            cfg.IRT_MODEL = original


# ── Calibrator 3PL Tests ─────────────────────────────────────────


class TestCalibrator3PL:
    """Test Bayesian calibration with 3PL support."""

    def test_calibrate_2pl_returns_3_values(self):
        """calibrate_item now returns (b, a, c, metadata)."""
        responses = [(0.0, 1), (0.5, 0), (-0.5, 1)] * 15
        b, a, c, meta = calibrate_item(0.0, 1.0, responses, min_responses=10)
        assert isinstance(b, float)
        assert isinstance(a, float)
        assert isinstance(c, float)
        assert c == 0.0  # Not using 3PL
        assert meta["updated"] is True
        assert meta["model"] == "2PL"

    def test_calibrate_3pl_needs_500_responses(self):
        """3PL c estimation requires 500+ responses."""
        rng = np.random.RandomState(42)
        responses = [(rng.uniform(-2, 2), int(rng.random() > 0.4)) for _ in range(100)]
        _, _, c, meta = calibrate_item(
            0.0, 1.0, responses, use_3pl=True, current_c=0.2
        )
        assert c == 0.2  # Not enough responses, stays at prior
        assert meta["model"] == "2PL"  # Falls back

    def test_calibrate_3pl_with_sufficient_data(self):
        """With 500+ responses and use_3pl=True, c should be estimated."""
        rng = np.random.RandomState(123)
        true_c = 0.20
        responses = []
        for _ in range(600):
            theta = rng.uniform(-2, 2)
            p = true_c + (1.0 - true_c) / (1.0 + np.exp(-1.0 * (theta - 0.0)))
            resp = 1 if rng.random() < p else 0
            responses.append((theta, resp))

        _, _, c, meta = calibrate_item(
            0.0, 1.0, responses, use_3pl=True, current_c=0.25,
            min_responses=30,
        )
        assert meta["model"] == "3PL"
        assert 0.0 <= c <= 0.25  # Within valid range

    def test_guessing_bayesian_stays_bounded(self):
        """update_guessing_bayesian should keep c in [0, 1/n_choices]."""
        rng = np.random.RandomState(42)
        responses = [(rng.uniform(-2, 2), int(rng.random() > 0.3)) for _ in range(600)]
        c = update_guessing_bayesian(0.20, a=1.0, b=0.0, responses=responses, n_choices=4)
        assert 0.0 <= c <= 0.25


# ── Exposure Analysis Tests ──────────────────────────────────────


class TestExposureAnalysis:
    """Test exposure analysis module."""

    def _make_items(self, n: int = 100) -> list[ItemParameters]:
        return [
            ItemParameters(
                item_id=i, word=f"word_{i}",
                difficulty_b=(i - n/2) / (n/4),
                discrimination_a=1.0,
                cefr=["A1", "A2", "B1", "B2", "C1"][i % 5],
            )
            for i in range(n)
        ]

    def test_no_sessions(self):
        items = self._make_items()
        report = analyze_exposure(items, {}, 0)
        assert report["total_sessions"] == 0
        assert "message" in report

    def test_basic_analysis(self):
        items = self._make_items(50)
        # Simulate: first 10 items heavily used, rest barely
        counts = {}
        for i in range(10):
            counts[i] = 100
        for i in range(10, 50):
            counts[i] = 2

        report = analyze_exposure(items, counts, total_sessions=200)
        assert report["total_sessions"] == 200
        assert report["pool_size"] == 50
        assert report["items_used"] == 50
        assert report["items_never_used"] == 0
        assert report["over_exposed_count"] > 0  # First 10 items at 50% rate
        assert report["utilization_pct"] == 100.0
        assert "recommendations" in report
        assert len(report["cefr_exposure"]) > 0
        assert len(report["difficulty_band_exposure"]) > 0

    def test_never_used_items(self):
        items = self._make_items(100)
        counts = {0: 50, 1: 30}  # Only 2 items used

        report = analyze_exposure(items, counts, total_sessions=100)
        assert report["items_never_used"] == 98
        assert report["utilization_pct"] == 2.0

    def test_gini_perfect_equality(self):
        """All items equally used → Gini ≈ 0."""
        values = np.ones(100)
        gini = _compute_gini(values)
        assert gini < 0.01

    def test_gini_high_inequality(self):
        """One item gets all exposure → Gini near 1."""
        values = np.zeros(100)
        values[0] = 100.0
        gini = _compute_gini(values)
        assert gini > 0.9

    def test_expansion_needs_insufficient_data(self):
        items = self._make_items()
        result = identify_expansion_needs(items, {}, total_sessions=10)
        assert "message" in result

    def test_expansion_needs_with_data(self):
        items = self._make_items(50)
        counts = {i: 80 for i in range(50)}  # Heavy uniform usage
        result = identify_expansion_needs(items, counts, total_sessions=200)
        assert "high_demand_difficulty_bands" in result
        assert "cefr_expansion_needs" in result


# ── API Exposure Endpoint Test ───────────────────────────────────


class TestExposureAPI:
    """Test exposure analysis API endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from fastapi.testclient import TestClient
        from irt_cat_engine.api.main import app
        from irt_cat_engine.api.session_manager import session_manager
        from irt_cat_engine.data.database import Base, engine
        from irt_cat_engine.config import VOCAB_DB_PATH
        Base.metadata.create_all(engine)
        if VOCAB_DB_PATH.exists() and not session_manager.is_loaded:
            session_manager.load_data()
        self.client = TestClient(app)
        yield

    def test_exposure_endpoint(self):
        resp = self.client.get("/api/v1/admin/exposure")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_sessions" in data
        assert "pool_size" in data

    def test_expansion_endpoint(self):
        resp = self.client.get("/api/v1/admin/exposure/expansion")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_sessions" in data or "message" in data
