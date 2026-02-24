"""Phase 7 tests: Oxford coverage, estimated vocabulary, weekly plan."""
import pytest

from irt_cat_engine.models.irt_2pl import ItemParameters
from irt_cat_engine.reporting.score_mapper import (
    CEFR_VOCAB_ESTIMATES,
    _estimate_oxford_coverage,
    generate_diagnostic_report,
)
from irt_cat_engine.reporting.recommendation_engine import (
    generate_study_plan,
    _build_weekly_plan,
)
from irt_cat_engine.data.load_vocabulary import VocabWord


# ── Helpers ──────────────────────────────────────────────────────

def _make_item(item_id: int, word: str, cefr: str = "B1",
               difficulty_b: float = 0.0, discrimination_a: float = 1.0,
               question_type: int = 1) -> ItemParameters:
    return ItemParameters(
        item_id=item_id,
        word=word,
        difficulty_b=difficulty_b,
        discrimination_a=discrimination_a,
        question_type=question_type,
        cefr=cefr,
    )


def _make_vocab(word: str, cefr: str = "B1", pos: str = "noun",
                meaning_ko: str = "뜻", synonym=None, antonym=None,
                sentence_1: str = "") -> VocabWord:
    return VocabWord(
        word_display=word,
        freq_rank=100,
        pos=pos,
        cefr=cefr,
        meaning_ko=meaning_ko,
        definition_en=f"definition of {word}",
        synonym=synonym or [],
        antonym=antonym or [],
        sentence_1=sentence_1,
    )


# ── CEFR Vocab Estimates ────────────────────────────────────────


class TestCEFRVocabEstimates:
    """Test CEFR_VOCAB_ESTIMATES mapping."""

    def test_all_levels_present(self):
        for level in ("A1", "A2", "B1", "B2", "C1"):
            assert level in CEFR_VOCAB_ESTIMATES

    def test_monotonically_increasing(self):
        levels = ["A1", "A2", "B1", "B2", "C1"]
        for i in range(len(levels) - 1):
            assert CEFR_VOCAB_ESTIMATES[levels[i]] < CEFR_VOCAB_ESTIMATES[levels[i + 1]]

    def test_a1_is_1000(self):
        assert CEFR_VOCAB_ESTIMATES["A1"] == 1000

    def test_c1_is_8000(self):
        assert CEFR_VOCAB_ESTIMATES["C1"] == 8000


# ── Oxford Coverage ─────────────────────────────────────────────


class TestOxfordCoverage:
    """Test _estimate_oxford_coverage function."""

    def test_high_theta_high_coverage(self):
        """Learner with high ability should cover most core items."""
        items = [
            _make_item(i, f"word{i}", cefr="A1", difficulty_b=-1.0)
            for i in range(10)
        ] + [
            _make_item(i + 10, f"word{i + 10}", cefr="A2", difficulty_b=-0.5)
            for i in range(10)
        ] + [
            _make_item(i + 20, f"word{i + 20}", cefr="B1", difficulty_b=0.0)
            for i in range(10)
        ]
        coverage = _estimate_oxford_coverage(theta=2.0, full_item_bank=items)
        assert coverage >= 0.9

    def test_low_theta_low_coverage(self):
        """Learner with low ability should cover fewer core items."""
        items = [
            _make_item(i, f"word{i}", cefr="B1", difficulty_b=0.5)
            for i in range(20)
        ]
        coverage = _estimate_oxford_coverage(theta=-2.0, full_item_bank=items)
        assert coverage < 0.3

    def test_empty_bank_returns_zero(self):
        coverage = _estimate_oxford_coverage(theta=0.0, full_item_bank=[])
        assert coverage == 0.0

    def test_no_core_items_returns_zero(self):
        """If all items are B2/C1, no core items → 0 coverage."""
        items = [
            _make_item(i, f"word{i}", cefr="C1", difficulty_b=1.5)
            for i in range(10)
        ]
        coverage = _estimate_oxford_coverage(theta=0.0, full_item_bank=items)
        assert coverage == 0.0

    def test_coverage_range(self):
        """Coverage should be in [0, 1]."""
        items = [
            _make_item(i, f"word{i}", cefr="A1", difficulty_b=0.0)
            for i in range(20)
        ]
        for theta in [-3.0, -1.0, 0.0, 1.0, 3.0]:
            coverage = _estimate_oxford_coverage(theta=theta, full_item_bank=items)
            assert 0.0 <= coverage <= 1.0


# ── Diagnostic Report Integration ───────────────────────────────


class TestDiagnosticReportNewFields:
    """Test that generate_diagnostic_report includes Phase 7 fields."""

    @pytest.fixture
    def report(self):
        items_admin = [_make_item(0, "cat", "A1", -0.5), _make_item(1, "dog", "A2", 0.0)]
        responses = [1, 1]
        full_bank = items_admin + [
            _make_item(2, "run", "B1", 0.5),
            _make_item(3, "big", "A1", -1.0),
        ]
        return generate_diagnostic_report(
            theta=0.5, se=0.3,
            items_administered=items_admin,
            responses=responses,
            full_item_bank=full_bank,
        )

    def test_has_oxford_coverage(self, report):
        assert "oxford_coverage" in report
        assert isinstance(report["oxford_coverage"], float)
        assert 0.0 <= report["oxford_coverage"] <= 1.0

    def test_has_estimated_vocabulary(self, report):
        assert "estimated_vocabulary" in report
        assert isinstance(report["estimated_vocabulary"], int)
        assert report["estimated_vocabulary"] > 0

    def test_estimated_vocabulary_matches_cefr(self, report):
        cefr = report["cefr_level"]
        assert report["estimated_vocabulary"] == CEFR_VOCAB_ESTIMATES.get(cefr, 3500)

    def test_existing_fields_preserved(self, report):
        """Ensure existing report fields are not broken."""
        for key in ("theta", "se", "reliability", "cefr_level",
                     "cefr_probabilities", "curriculum_level",
                     "vocab_size_estimate", "total_items", "total_correct",
                     "accuracy", "dimension_scores"):
            assert key in report


# ── Weekly Plan ──────────────────────────────────────────────────


class TestWeeklyPlan:
    """Test _build_weekly_plan function."""

    def test_always_returns_list(self):
        plan = _build_weekly_plan([])
        assert isinstance(plan, list)

    def test_has_week_4_review(self):
        """Week 4 should always exist for comprehensive review."""
        recs = [{"dimension": "semantic", "label_ko": "의미", "priority": "high"}]
        plan = _build_weekly_plan(recs)
        assert any(w["week"] == 4 for w in plan)

    def test_week_structure(self):
        recs = [
            {"dimension": "semantic", "label_ko": "의미", "priority": "high"},
            {"dimension": "relational", "label_ko": "관계어", "priority": "medium"},
        ]
        plan = _build_weekly_plan(recs)
        for week in plan:
            assert "week" in week
            assert "focus" in week
            assert "daily_target" in week
            assert "description_ko" in week
            assert "description_en" in week
            assert isinstance(week["focus"], list)
            assert week["daily_target"] > 0

    def test_high_priority_comes_first(self):
        recs = [
            {"dimension": "semantic", "label_ko": "의미", "priority": "high"},
            {"dimension": "contextual", "label_ko": "문맥", "priority": "medium"},
        ]
        plan = _build_weekly_plan(recs)
        # Week 1 should focus on high-priority dimension
        assert "semantic" in plan[0]["focus"]


class TestStudyPlanWeeklyIntegration:
    """Test that generate_study_plan includes weekly_plan."""

    @pytest.fixture
    def vocab_pool(self):
        words = []
        names = [
            "happy", "sad", "run", "walk", "big", "small", "beautiful", "ugly",
            "fast", "slow", "eat", "drink", "read", "write", "teach", "learn",
            "strong", "weak", "bright", "dark", "quiet", "loud", "clean", "dirty",
            "warm", "cold", "thick", "thin", "deep", "shallow",
        ]
        for i, name in enumerate(names):
            words.append(_make_vocab(
                name, cefr="B1", pos="adjective" if i < 10 else "verb",
                meaning_ko=f"뜻{i}",
                synonym=[names[(i + 1) % len(names)]],
                antonym=[names[(i + 2) % len(names)]],
                sentence_1=f"She is {name} today." if i < 10 else "",
            ))
        return words

    def test_plan_has_weekly_plan(self, vocab_pool):
        dim_scores = [
            {"dimension": "semantic", "label": "Semantic", "label_ko": "의미", "color": "#3b82f6", "correct": 1, "total": 5, "score": 20},
            {"dimension": "contextual", "label": "Contextual", "label_ko": "문맥", "color": "#10b981", "correct": 4, "total": 5, "score": 80},
            {"dimension": "form", "label": "Form", "label_ko": "형태", "color": "#f59e0b", "correct": 0, "total": 0, "score": None},
            {"dimension": "relational", "label": "Relational", "label_ko": "관계어", "color": "#ef4444", "correct": 3, "total": 5, "score": 60},
            {"dimension": "pragmatic", "label": "Pragmatic", "label_ko": "화용", "color": "#8b5cf6", "correct": 0, "total": 0, "score": None},
        ]
        plan = generate_study_plan(dim_scores, vocab_pool, "B1")
        assert "weekly_plan" in plan
        assert isinstance(plan["weekly_plan"], list)
        assert len(plan["weekly_plan"]) >= 1

    def test_weekly_plan_has_4_weeks_max(self, vocab_pool):
        dim_scores = [
            {"dimension": "semantic", "label": "Semantic", "label_ko": "의미", "color": "#3b82f6", "correct": 1, "total": 5, "score": 20},
            {"dimension": "contextual", "label": "Contextual", "label_ko": "문맥", "color": "#10b981", "correct": 2, "total": 5, "score": 40},
            {"dimension": "form", "label": "Form", "label_ko": "형태", "color": "#f59e0b", "correct": 0, "total": 0, "score": None},
            {"dimension": "relational", "label": "Relational", "label_ko": "관계어", "color": "#ef4444", "correct": 1, "total": 5, "score": 20},
            {"dimension": "pragmatic", "label": "Pragmatic", "label_ko": "화용", "color": "#8b5cf6", "correct": 0, "total": 0, "score": None},
        ]
        plan = generate_study_plan(dim_scores, vocab_pool, "B1")
        assert len(plan["weekly_plan"]) <= 4
