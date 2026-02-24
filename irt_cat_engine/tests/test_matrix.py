"""Tests for vocabulary matrix computation (Phase 8)."""
import pytest

from irt_cat_engine.models.irt_2pl import ItemParameters
from irt_cat_engine.data.load_vocabulary import VocabWord
from irt_cat_engine.reporting.matrix_generator import (
    _classify_probability,
    _cefr_to_estimated_probability,
    _sample_representative_words,
    compute_vocab_matrix,
    KNOWLEDGE_STATES,
)


# ── Helpers ──────────────────────────────────────────────────────

def _make_item(item_id: int, word: str, cefr: str = "B1",
               difficulty_b: float = 0.0, discrimination_a: float = 1.0) -> ItemParameters:
    return ItemParameters(
        item_id=item_id, word=word,
        difficulty_b=difficulty_b, discrimination_a=discrimination_a,
        question_type=1, cefr=cefr,
    )


def _make_vocab(word: str, cefr: str = "B1", freq_rank: int = 100,
                pos: str = "noun") -> VocabWord:
    return VocabWord(
        word_display=word, freq_rank=freq_rank, pos=pos,
        cefr=cefr, meaning_ko=f"{word}의 뜻", definition_en=f"def of {word}",
    )


# ── Knowledge state classification ──────────────────────────────

class TestClassifyProbability:
    def test_not_known(self):
        assert _classify_probability(0.0) == "not_known"
        assert _classify_probability(0.1) == "not_known"
        assert _classify_probability(0.29) == "not_known"

    def test_emerging(self):
        assert _classify_probability(0.3) == "emerging"
        assert _classify_probability(0.49) == "emerging"

    def test_developing(self):
        assert _classify_probability(0.5) == "developing"
        assert _classify_probability(0.69) == "developing"

    def test_comfortable(self):
        assert _classify_probability(0.7) == "comfortable"
        assert _classify_probability(0.89) == "comfortable"

    def test_mastered(self):
        assert _classify_probability(0.9) == "mastered"
        assert _classify_probability(0.99) == "mastered"
        assert _classify_probability(1.0) == "mastered"

    def test_boundaries(self):
        """Each boundary value belongs to the higher state."""
        assert _classify_probability(0.3) == "emerging"
        assert _classify_probability(0.5) == "developing"
        assert _classify_probability(0.7) == "comfortable"
        assert _classify_probability(0.9) == "mastered"


# ── CEFR estimation ─────────────────────────────────────────────

class TestCEFREstimation:
    def test_user_well_above_word(self):
        p = _cefr_to_estimated_probability("A1", "B2")
        assert p > 0.9

    def test_user_at_word_level(self):
        p = _cefr_to_estimated_probability("B1", "B1")
        assert 0.4 < p < 0.7

    def test_user_well_below_word(self):
        p = _cefr_to_estimated_probability("C1", "A1")
        assert p < 0.3

    def test_higher_gap_higher_probability(self):
        p_close = _cefr_to_estimated_probability("B1", "B2")
        p_far = _cefr_to_estimated_probability("A1", "C1")
        assert p_far > p_close


# ── Sampling ─────────────────────────────────────────────────────

class TestSampling:
    def test_sample_size_respected(self):
        words = [_make_vocab(f"w{i}", cefr="B1", freq_rank=i) for i in range(200)]
        sample = _sample_representative_words(words, sample_size=50)
        assert len(sample) <= 50

    def test_empty_returns_empty(self):
        assert _sample_representative_words([], 100) == []

    def test_stratified_across_cefr(self):
        words = []
        for cefr in ("A1", "A2", "B1", "B2", "C1"):
            for i in range(20):
                words.append(_make_vocab(f"{cefr}_{i}", cefr=cefr, freq_rank=i + 1))
        sample = _sample_representative_words(words, sample_size=50)
        cefr_in_sample = set(w.cefr for w in sample)
        assert len(cefr_in_sample) >= 4

    def test_sorted_by_freq_rank(self):
        words = [_make_vocab(f"w{i}", freq_rank=100 - i) for i in range(50)]
        sample = _sample_representative_words(words, sample_size=30)
        ranks = [w.freq_rank for w in sample]
        assert ranks == sorted(ranks)


# ── Full matrix computation ──────────────────────────────────────

class TestComputeVocabMatrix:
    @pytest.fixture
    def setup(self):
        cefr_list = ["A1"] * 20 + ["A2"] * 20 + ["B1"] * 20 + ["B2"] * 20 + ["C1"] * 20
        b_list = [-1.5] * 20 + [-0.7] * 20 + [0.0] * 20 + [0.7] * 20 + [1.5] * 20
        vocab = [_make_vocab(f"word{i}", cefr=cefr_list[i], freq_rank=i + 1) for i in range(100)]
        items = [_make_item(i, f"word{i}", cefr=cefr_list[i], difficulty_b=b_list[i]) for i in range(100)]
        return vocab, items

    def test_returns_expected_keys(self, setup):
        vocab, items = setup
        result = compute_vocab_matrix(0.0, "B1", vocab, items, sample_size=50)
        for key in ("words", "summary", "goal_summary", "states",
                     "current_theta", "goal_theta", "total_sampled"):
            assert key in result

    def test_word_count_matches(self, setup):
        vocab, items = setup
        result = compute_vocab_matrix(0.0, "B1", vocab, items, sample_size=50)
        assert result["total_sampled"] == len(result["words"])
        assert result["total_sampled"] <= 50

    def test_summary_counts_add_up(self, setup):
        vocab, items = setup
        result = compute_vocab_matrix(0.0, "B1", vocab, items, sample_size=50)
        counts = result["summary"]["counts"]
        total = sum(counts.values())
        assert total == result["summary"]["total"]

    def test_high_theta_more_mastered(self, setup):
        vocab, items = setup
        hi = compute_vocab_matrix(2.0, "C1", vocab, items, sample_size=50)
        lo = compute_vocab_matrix(-2.0, "A1", vocab, items, sample_size=50)
        assert hi["summary"]["counts"]["mastered"] > lo["summary"]["counts"]["mastered"]

    def test_goal_theta_higher(self, setup):
        vocab, items = setup
        result = compute_vocab_matrix(0.0, "B1", vocab, items, sample_size=50)
        assert result["goal_theta"] > result["current_theta"]

    def test_goal_has_more_mastered(self, setup):
        vocab, items = setup
        result = compute_vocab_matrix(0.0, "B1", vocab, items, sample_size=50)
        assert result["goal_summary"]["counts"]["mastered"] >= result["summary"]["counts"]["mastered"]

    def test_word_fields(self, setup):
        vocab, items = setup
        result = compute_vocab_matrix(0.0, "B1", vocab, items, sample_size=10)
        for w in result["words"]:
            assert "word" in w
            assert "meaning_ko" in w
            assert "cefr" in w
            assert "current_state" in w
            assert "goal_state" in w
            assert 0.0 <= w["current_probability"] <= 1.0
            assert 0.0 <= w["goal_probability"] <= 1.0

    def test_five_states(self, setup):
        vocab, items = setup
        result = compute_vocab_matrix(0.0, "B1", vocab, items, sample_size=10)
        assert len(result["states"]) == 5

    def test_no_irt_params_uses_cefr(self):
        vocab = [_make_vocab("orphan", cefr="A1", freq_rank=1)]
        result = compute_vocab_matrix(1.0, "B2", vocab, [], sample_size=1)
        assert len(result["words"]) == 1
        assert result["words"][0]["has_irt_params"] is False
        assert result["words"][0]["current_state"] == "mastered"

    def test_changed_count(self, setup):
        vocab, items = setup
        result = compute_vocab_matrix(0.0, "B1", vocab, items, sample_size=50)
        assert result["goal_summary"]["words_changed"] >= 0
        assert result["goal_summary"]["words_changed"] <= result["total_sampled"]
