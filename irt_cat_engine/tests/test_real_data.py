"""Test with real vocabulary database — validates data loading and parameter initialization."""
import pytest
import numpy as np

from irt_cat_engine.data.load_vocabulary import load_vocabulary, get_vocab_stats
from irt_cat_engine.item_bank.parameter_initializer import (
    initialize_item_parameters, get_parameter_statistics,
    compute_difficulty_b, compute_discrimination_a,
)
from irt_cat_engine.item_bank.distractor_engine import DistractorEngine
from irt_cat_engine.models.irt_2pl import ItemParameters, probability
from irt_cat_engine.cat.session import CATSession
from irt_cat_engine.cat.stopping_rules import StoppingRules
from irt_cat_engine.config import VOCAB_DB_PATH


@pytest.fixture(scope="module")
def vocab():
    """Load vocabulary DB once for all tests in this module."""
    if not VOCAB_DB_PATH.exists():
        pytest.skip(f"Vocabulary DB not found: {VOCAB_DB_PATH}")
    return load_vocabulary()


@pytest.fixture(scope="module")
def items(vocab):
    return initialize_item_parameters(vocab, question_type=1)


class TestDataLoading:
    def test_load_count(self, vocab):
        """Should load ~9,183 words."""
        assert 9000 < len(vocab) < 9500

    def test_required_fields(self, vocab):
        """Every word should have core fields."""
        for w in vocab[:100]:
            assert w.word_display
            assert w.pos
            assert w.cefr in ("A1", "A2", "B1", "B2", "C1", "")
            assert w.meaning_ko

    def test_cefr_distribution(self, vocab):
        stats = get_vocab_stats(vocab)
        dist = stats["cefr_distribution"]
        assert dist.get("B1", 0) > 2000
        assert dist.get("A1", 0) > 1000
        assert stats["total_words"] > 9000

    def test_data_cleaning(self, vocab):
        """freq_grade should be cleaned of dirty values."""
        valid_grades = {"최고빈도", "고빈도", "중빈도", "저빈도", ""}
        for w in vocab:
            assert w.freq_grade in valid_grades, f"Dirty freq_grade: '{w.freq_grade}' for {w.word_display}"

    def test_educational_value_cleaning(self, vocab):
        """educational_value should be int 1-10 or None."""
        for w in vocab:
            if w.educational_value is not None:
                assert 1 <= w.educational_value <= 10, (
                    f"Invalid edu_value: {w.educational_value} for {w.word_display}"
                )

    def test_synonym_parsing(self, vocab):
        """Words with synonyms should have list parsed correctly."""
        with_syn = [w for w in vocab if w.synonym]
        assert len(with_syn) > 7000
        for w in with_syn[:50]:
            assert isinstance(w.synonym, list)
            assert all(isinstance(s, str) for s in w.synonym)


class TestParameterInitialization:
    def test_b_range(self, items):
        """b values should be roughly in [-3, 3]."""
        bs = [item.difficulty_b for item in items]
        assert min(bs) > -4
        assert max(bs) < 4
        assert -0.5 < np.mean(bs) < 0.5  # Roughly centered

    def test_a_range(self, items):
        """a values should be in valid range.

        Loanwords on Type 1/2 have discrimination reduced by
        LOANWORD_DISCRIMINATION_FACTOR, so they can go below A_MIN.
        """
        for item in items:
            if item.is_loanword:
                assert 0.15 <= item.discrimination_a <= 2.5
            else:
                assert 0.4 <= item.discrimination_a <= 2.5

    def test_easy_words_low_b(self, vocab):
        """High-frequency A1 words should have low b."""
        easy_words = [w for w in vocab if w.cefr == "A1" and w.freq_rank < 100]
        for w in easy_words[:5]:
            b = compute_difficulty_b(w)
            assert b < 0, f"A1 word '{w.word_display}' has b={b:.2f}"

    def test_hard_words_high_b(self, vocab):
        """Low-frequency B2/C1 words should have high b."""
        hard_words = [w for w in vocab if w.cefr in ("B2", "C1") and w.freq_rank > 8000]
        for w in hard_words[:5]:
            b = compute_difficulty_b(w)
            assert b > 0, f"B2/C1 word '{w.word_display}' has b={b:.2f}"

    def test_statistics(self, items):
        stats = get_parameter_statistics(items)
        assert stats["count"] > 9000
        assert -0.5 < stats["b_mean"] < 0.5
        assert stats["b_std"] > 0.3
        assert stats["a_mean"] > 0.5


class TestDistractorEngine:
    @pytest.fixture(scope="class")
    def engine(self, vocab):
        return DistractorEngine(vocab)

    def test_meaning_distractors(self, vocab, engine):
        """Should generate 3 distractors for Type 1."""
        target = next(w for w in vocab if w.cefr == "B1" and w.pos == "NOUN")
        distractors = engine.generate_meaning_distractors(target, n=3)
        assert len(distractors) == 3
        # Distractors should not be the same as correct answer
        for d in distractors:
            assert d != target.meaning_ko

    def test_generate_full_item_type1(self, vocab, engine):
        """Should generate a complete Type 1 item."""
        target = next(w for w in vocab if w.cefr == "B1" and w.pos == "VERB")
        item = engine.generate_item(target, question_type=1)
        assert item is not None
        assert item["correct_answer"] == target.meaning_ko
        assert len(item["distractors"]) == 3

    def test_generate_synonym_item(self, vocab, engine):
        """Should generate Type 3 item for words with synonyms."""
        target = next(w for w in vocab if w.synonym and w.pos == "ADJ")
        item = engine.generate_item(target, question_type=3)
        if item is not None:
            assert item["correct_answer"] in target.synonym
            assert len(item["distractors"]) == 3


class TestRealDataSimulation:
    def test_simulation_with_real_params(self, items):
        """Run a simulated CAT with real item parameters."""
        rng = np.random.RandomState(42)
        theta_true = 0.0

        # Use a subset for speed
        pool = items[:2000]

        session = CATSession(
            item_pool=pool,
            initial_theta=0.0,
            stopping_rules=StoppingRules(min_items=15, max_items=30, se_threshold=0.35),
        )

        while not session.is_complete:
            item = session.get_next_item()
            if item is None:
                break
            p = probability(theta_true, item.discrimination_a, item.difficulty_b)
            is_correct = bool(rng.random() < p)
            session.record_response(item, is_correct)

        results = session.get_results()
        assert results["cefr_level"] in ("A1", "A2", "B1", "B2", "C1")
        assert results["vocab_size_estimate"] > 0
        assert abs(results["theta"] - theta_true) < 1.5
        print(f"\n=== Real Data Simulation Results ===")
        print(f"  True theta: {theta_true}")
        print(f"  Estimated theta: {results['theta']}")
        print(f"  SE: {results['se']}")
        print(f"  CEFR: {results['cefr_level']}")
        print(f"  Curriculum: {results['curriculum_level']}")
        print(f"  Vocab size: {results['vocab_size_estimate']}")
        print(f"  Items used: {results['total_items']}")
        print(f"  Accuracy: {results['accuracy']}")
        print(f"  Termination: {session.termination_reason}")
