"""Phase 5 tests: Loanword filtering + Don't-Know option."""
import numpy as np
import pytest

from irt_cat_engine.config import TRANSPARENT_LOANWORDS, LOANWORD_MAX_PER_TEST
from irt_cat_engine.data.load_vocabulary import VocabWord
from irt_cat_engine.models.irt_2pl import ItemParameters, probability
from irt_cat_engine.models.ability_estimator import estimate_theta_eap
from irt_cat_engine.item_bank.parameter_initializer import initialize_item_parameters
from irt_cat_engine.cat.item_selector import ContentTracker, select_next_item
from irt_cat_engine.cat.session import CATSession


# ── Loanword Tests ──────────────────────────────────────────────


class TestLoanwordConfig:
    """Test loanword configuration and flagging."""

    def test_transparent_loanwords_not_empty(self):
        """TRANSPARENT_LOANWORDS should contain known loanwords."""
        assert len(TRANSPARENT_LOANWORDS) > 50
        assert "computer" in TRANSPARENT_LOANWORDS
        assert "pizza" in TRANSPARENT_LOANWORDS
        assert "banana" in TRANSPARENT_LOANWORDS

    def test_vocabword_loanword_flag(self):
        """VocabWord should have is_loanword field."""
        w = VocabWord(
            word_display="computer", freq_rank=100,
            pos="noun", cefr="A1", meaning_ko="컴퓨터",
            definition_en="an electronic device", is_loanword=True,
        )
        assert w.is_loanword is True

    def test_item_parameters_loanword_flag(self):
        """ItemParameters should carry is_loanword."""
        item = ItemParameters(
            item_id=0, word="computer", difficulty_b=0.0,
            discrimination_a=1.0, is_loanword=True,
        )
        assert item.is_loanword is True


class TestLoanwordDiscrimination:
    """Test that loanword discrimination is reduced for Type 1/2."""

    def _make_word(self, word: str, is_loanword: bool) -> VocabWord:
        return VocabWord(
            word_display=word, freq_rank=100,
            pos="noun", cefr="B1", meaning_ko="뜻",
            definition_en="meaning", is_loanword=is_loanword,
        )

    def test_loanword_type1_discrimination_reduced(self):
        """Loanword on Type 1 should have lower discrimination."""
        loanword = self._make_word("computer", is_loanword=True)
        regular = self._make_word("determine", is_loanword=False)

        items_loan = initialize_item_parameters([loanword], question_type=1)
        items_reg = initialize_item_parameters([regular], question_type=1)

        assert items_loan[0].discrimination_a < items_reg[0].discrimination_a

    def test_loanword_type3_discrimination_unchanged(self):
        """Loanword on Type 3 should NOT have reduced discrimination."""
        loanword = self._make_word("computer", is_loanword=True)
        regular = self._make_word("determine", is_loanword=False)

        items_loan = initialize_item_parameters([loanword], question_type=3)
        items_reg = initialize_item_parameters([regular], question_type=3)

        # Same word metadata, so discrimination should be the same
        assert abs(items_loan[0].discrimination_a - items_reg[0].discrimination_a) < 0.01

    def test_loanword_flag_passed_to_item_params(self):
        """is_loanword should propagate from VocabWord to ItemParameters."""
        word = self._make_word("pizza", is_loanword=True)
        items = initialize_item_parameters([word], question_type=1)
        assert items[0].is_loanword is True


class TestLoanwordContentTracker:
    """Test ContentTracker loanword constraints."""

    def test_loanword_counter(self):
        """ContentTracker should count loanwords."""
        tracker = ContentTracker()
        loanword_item = ItemParameters(
            item_id=0, word="computer", difficulty_b=0.0,
            discrimination_a=1.0, is_loanword=True,
        )
        regular_item = ItemParameters(
            item_id=1, word="determine", difficulty_b=0.0,
            discrimination_a=1.0, is_loanword=False,
        )

        tracker.record(loanword_item)
        assert tracker.loanword_count == 1

        tracker.record(regular_item)
        assert tracker.loanword_count == 1  # Didn't increase

        tracker.record(ItemParameters(
            item_id=2, word="pizza", difficulty_b=0.0,
            discrimination_a=1.0, is_loanword=True,
        ))
        assert tracker.loanword_count == 2

    def test_loanword_limit_enforced(self):
        """After LOANWORD_MAX_PER_TEST, is_loanword_ok should return False."""
        tracker = ContentTracker()

        # Fill up to max
        for i in range(LOANWORD_MAX_PER_TEST):
            tracker.record(ItemParameters(
                item_id=i, word=f"loanword_{i}", difficulty_b=0.0,
                discrimination_a=1.0, is_loanword=True,
            ))

        assert tracker.is_loanword_ok(True) is False
        assert tracker.is_loanword_ok(False) is True  # Regular words still OK

    def test_select_next_item_skips_loanwords_at_limit(self):
        """select_next_item should skip loanwords when limit reached."""
        # Create a pool with enough regular items to avoid fallback (top_n=5)
        items = [
            ItemParameters(
                item_id=0, word="computer", difficulty_b=0.0,
                discrimination_a=2.0,  # Higher info to prefer
                is_loanword=True,
            ),
        ]
        # Add 10 regular items so candidates >= top_n after filtering
        for i in range(1, 11):
            items.append(ItemParameters(
                item_id=i, word=f"word_{i}", difficulty_b=float(i) * 0.1,
                discrimination_a=1.0,
                is_loanword=False,
            ))

        tracker = ContentTracker()
        # Max out loanwords
        for i in range(LOANWORD_MAX_PER_TEST):
            tracker.record(ItemParameters(
                item_id=100 + i, word=f"loan_{i}", difficulty_b=0.0,
                discrimination_a=1.0, is_loanword=True,
            ))

        selected = select_next_item(
            theta=0.0, item_pool=items,
            administered_ids=set(),
            content_tracker=tracker,
        )
        # Should NOT select the loanword
        assert selected is not None
        assert selected.is_loanword is False


# ── Don't-Know Tests ────────────────────────────────────────────


class TestDontKnowEAP:
    """Test EAP estimation with dont_know_flags."""

    def _make_items(self, n: int) -> list[ItemParameters]:
        return [
            ItemParameters(
                item_id=i, word=f"word_{i}",
                difficulty_b=(i - n/2) / (n/4),
                discrimination_a=1.0,
                guessing_c=0.0,
            )
            for i in range(n)
        ]

    def test_eap_accepts_dont_know_flags(self):
        """estimate_theta_eap should accept dont_know_flags parameter."""
        items = self._make_items(5)
        responses = [1, 0, 1, 0, 0]
        flags = [False, True, False, False, True]

        theta, se = estimate_theta_eap(items, responses, dont_know_flags=flags)
        assert isinstance(theta, float)
        assert isinstance(se, float)
        assert se > 0

    def test_eap_no_flags_same_as_none(self):
        """Without flags, result should be same as flags=None."""
        items = self._make_items(5)
        responses = [1, 0, 1, 0, 1]

        theta1, se1 = estimate_theta_eap(items, responses)
        theta2, se2 = estimate_theta_eap(items, responses, dont_know_flags=None)

        assert abs(theta1 - theta2) < 1e-10
        assert abs(se1 - se2) < 1e-10

    def test_2pl_dont_know_same_as_wrong(self):
        """In 2PL mode (c=0), dont_know should produce same result as regular wrong."""
        items = self._make_items(5)
        responses = [1, 0, 1, 0, 0]

        # Without dont_know
        theta1, se1 = estimate_theta_eap(items, responses)

        # With dont_know on the wrong answers
        flags = [False, True, False, True, True]
        theta2, se2 = estimate_theta_eap(items, responses, dont_know_flags=flags)

        # In 2PL, c is already 0, so dont_know flag has no effect
        assert abs(theta1 - theta2) < 1e-10
        assert abs(se1 - se2) < 1e-10

    def test_3pl_dont_know_on_wrong_answers_constant_factor(self):
        """In 3PL, c override on wrong answers is a constant factor — EAP is unchanged.

        This is a known IRT property: for incorrect responses, (1-P) = (1-c)*Q_2PL,
        so changing c only scales the likelihood by a constant that normalizes away.
        The dont_know flag preserves data quality for item calibration and analytics,
        but does not change theta estimation for incorrect responses.
        """
        items = [
            ItemParameters(
                item_id=i, word=f"word_{i}",
                difficulty_b=(i - 5) / 2.5,
                discrimination_a=1.0,
                guessing_c=0.20,
            )
            for i in range(10)
        ]
        responses = [1, 0, 1, 0, 0, 1, 0, 0, 1, 0]

        theta_no_flag, _ = estimate_theta_eap(items, responses)

        # Flags only on wrong answers (as in real usage)
        flags = [False, True, False, True, True, False, True, True, False, True]
        theta_dk, _ = estimate_theta_eap(items, responses, dont_know_flags=flags)

        # Same result because c override on wrong answers is a constant factor
        assert abs(theta_no_flag - theta_dk) < 1e-10

    def test_3pl_c_override_affects_correct_responses(self):
        """Verify that c parameter DOES affect estimation when applied to correct responses.

        This confirms the EAP implementation correctly uses the c parameter —
        the effect only manifests through correct responses where guessing matters.
        """
        items = [
            ItemParameters(
                item_id=i, word=f"word_{i}",
                difficulty_b=(i - 5) / 2.5,
                discrimination_a=1.0,
                guessing_c=0.20,
            )
            for i in range(10)
        ]
        responses = [1, 0, 1, 0, 0, 1, 0, 0, 1, 0]

        theta_with_c, _ = estimate_theta_eap(items, responses)

        # Compare: same items but c=0 (2PL equivalent)
        items_no_c = [
            ItemParameters(
                item_id=i, word=f"word_{i}",
                difficulty_b=(i - 5) / 2.5,
                discrimination_a=1.0,
                guessing_c=0.0,  # No guessing
            )
            for i in range(10)
        ]
        theta_no_c, _ = estimate_theta_eap(items_no_c, responses)

        # Should differ because c affects P for correct answers
        assert abs(theta_with_c - theta_no_c) > 0.01, (
            f"c parameter should affect theta through correct responses: "
            f"c=0.20 → {theta_with_c:.4f}, c=0 → {theta_no_c:.4f}"
        )


class TestDontKnowSession:
    """Test CATSession with dont_know responses."""

    def _make_pool(self, n: int = 50) -> list[ItemParameters]:
        return [
            ItemParameters(
                item_id=i, word=f"word_{i}",
                difficulty_b=(i - n/2) / (n/4),
                discrimination_a=1.0,
            )
            for i in range(n)
        ]

    def test_record_response_with_dont_know(self):
        """CATSession.record_response should accept is_dont_know."""
        pool = self._make_pool()
        session = CATSession(item_pool=pool, initial_theta=0.0)

        item = pool[25]  # b ≈ 0.0
        session.record_response(item, is_correct=False, is_dont_know=True)

        assert len(session.dont_know_flags) == 1
        assert session.dont_know_flags[0] is True
        assert len(session.responses) == 1
        assert session.responses[0] == 0

    def test_dont_know_flags_accumulate(self):
        """dont_know_flags should accumulate over multiple responses."""
        pool = self._make_pool()
        session = CATSession(item_pool=pool, initial_theta=0.0)

        session.record_response(pool[20], is_correct=True, is_dont_know=False)
        session.record_response(pool[25], is_correct=False, is_dont_know=True)
        session.record_response(pool[30], is_correct=False, is_dont_know=False)

        assert session.dont_know_flags == [False, True, False]

    def test_session_default_no_dont_know(self):
        """Default is_dont_know should be False."""
        pool = self._make_pool()
        session = CATSession(item_pool=pool, initial_theta=0.0)

        session.record_response(pool[25], is_correct=True)
        assert session.dont_know_flags == [False]


class TestDontKnowAPI:
    """Test API handling of is_dont_know field."""

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

    def test_respond_accepts_dont_know(self):
        """POST /test/{id}/respond should accept is_dont_know field."""
        # Start a test
        start = self.client.post("/api/v1/test/start", json={
            "grade": "중2", "self_assess": "intermediate",
            "exam_experience": "none", "question_type": 1,
        })
        assert start.status_code == 200
        data = start.json()
        session_id = data["session_id"]
        first_item = data["first_item"]

        # Respond with dont_know
        resp = self.client.post(f"/api/v1/test/{session_id}/respond", json={
            "item_id": first_item["item_id"],
            "is_correct": False,
            "is_dont_know": True,
            "response_time_ms": 2000,
        })
        assert resp.status_code == 200
        resp_data = resp.json()
        assert resp_data["progress"]["items_completed"] == 1

    def test_respond_without_dont_know_defaults_false(self):
        """is_dont_know should default to False when omitted."""
        start = self.client.post("/api/v1/test/start", json={
            "grade": "중2", "self_assess": "intermediate",
            "exam_experience": "none", "question_type": 1,
        })
        data = start.json()
        session_id = data["session_id"]
        first_item = data["first_item"]

        resp = self.client.post(f"/api/v1/test/{session_id}/respond", json={
            "item_id": first_item["item_id"],
            "is_correct": True,
            "response_time_ms": 1500,
        })
        assert resp.status_code == 200
