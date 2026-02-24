"""Phase 6 tests: 5D Dimension Analysis + Recommendation Engine + Learn API."""
import pytest

from irt_cat_engine.data.load_vocabulary import VocabWord
from irt_cat_engine.models.irt_2pl import ItemParameters
from irt_cat_engine.reporting.dimension_analyzer import (
    QUESTION_TYPE_TO_DIMENSION,
    DIMENSIONS,
    compute_dimension_scores,
)
from irt_cat_engine.reporting.recommendation_engine import (
    get_adjacent_cefr,
    generate_study_plan,
    FOCUS_THRESHOLD,
    PRIORITY_THRESHOLD,
)


# ── Helpers ──────────────────────────────────────────────────────

def _make_item(item_id: int, word: str, question_type: int = 1, cefr: str = "B1") -> ItemParameters:
    """Create a minimal ItemParameters with question_type."""
    return ItemParameters(
        item_id=item_id,
        word=word,
        difficulty_b=0.0,
        discrimination_a=1.0,
        question_type=question_type,
        cefr=cefr,
    )


def _make_vocab(word: str, cefr: str = "B1", pos: str = "noun",
                meaning_ko: str = "뜻", synonym=None, antonym=None,
                sentence_1: str = "") -> VocabWord:
    """Create a minimal VocabWord."""
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


# ── Dimension Analyzer Tests ────────────────────────────────────


class TestQuestionTypeDimensionMapping:
    """Test QUESTION_TYPE_TO_DIMENSION mapping."""

    def test_type1_semantic(self):
        assert QUESTION_TYPE_TO_DIMENSION[1] == "semantic"

    def test_type2_semantic(self):
        assert QUESTION_TYPE_TO_DIMENSION[2] == "semantic"

    def test_type3_relational(self):
        assert QUESTION_TYPE_TO_DIMENSION[3] == "relational"

    def test_type4_relational(self):
        assert QUESTION_TYPE_TO_DIMENSION[4] == "relational"

    def test_type5_contextual(self):
        assert QUESTION_TYPE_TO_DIMENSION[5] == "contextual"

    def test_type6_contextual(self):
        assert QUESTION_TYPE_TO_DIMENSION[6] == "contextual"

    def test_all_5_dimensions_defined(self):
        keys = [d["key"] for d in DIMENSIONS]
        assert "semantic" in keys
        assert "contextual" in keys
        assert "form" in keys
        assert "relational" in keys
        assert "pragmatic" in keys

    def test_dimensions_have_labels(self):
        for d in DIMENSIONS:
            assert "label" in d and d["label"]
            assert "label_ko" in d and d["label_ko"]
            assert "color" in d and d["color"].startswith("#")


class TestComputeDimensionScores:
    """Test dimension score computation."""

    def test_basic_scoring(self):
        """Correct/total counts and score percentage."""
        items = [_make_item(0, "a", 1), _make_item(1, "b", 1), _make_item(2, "c", 1)]
        responses = [1, 1, 0]  # 2/3 correct for semantic

        scores = compute_dimension_scores(items, responses)
        semantic = next(s for s in scores if s["dimension"] == "semantic")
        assert semantic["correct"] == 2
        assert semantic["total"] == 3
        assert semantic["score"] == 67  # round(66.7)

    def test_empty_dimension_score_none(self):
        """Dimensions with no items should have score=None."""
        items = [_make_item(0, "a", 1)]  # only semantic
        responses = [1]

        scores = compute_dimension_scores(items, responses)
        form = next(s for s in scores if s["dimension"] == "form")
        assert form["total"] == 0
        assert form["score"] is None

    def test_multiple_dimensions(self):
        """Items from multiple dimensions scored separately."""
        items = [
            _make_item(0, "a", 1),  # semantic
            _make_item(1, "b", 3),  # relational
            _make_item(2, "c", 5),  # contextual
            _make_item(3, "d", 1),  # semantic
        ]
        responses = [1, 0, 1, 0]

        scores = compute_dimension_scores(items, responses)
        semantic = next(s for s in scores if s["dimension"] == "semantic")
        relational = next(s for s in scores if s["dimension"] == "relational")
        contextual = next(s for s in scores if s["dimension"] == "contextual")

        assert semantic["correct"] == 1 and semantic["total"] == 2
        assert relational["correct"] == 0 and relational["total"] == 1
        assert contextual["correct"] == 1 and contextual["total"] == 1

    def test_all_correct(self):
        """100% in a dimension."""
        items = [_make_item(0, "a", 3), _make_item(1, "b", 4)]
        responses = [1, 1]

        scores = compute_dimension_scores(items, responses)
        relational = next(s for s in scores if s["dimension"] == "relational")
        assert relational["score"] == 100

    def test_all_wrong(self):
        """0% in a dimension."""
        items = [_make_item(0, "a", 5), _make_item(1, "b", 6)]
        responses = [0, 0]

        scores = compute_dimension_scores(items, responses)
        contextual = next(s for s in scores if s["dimension"] == "contextual")
        assert contextual["score"] == 0

    def test_returns_all_5_dimensions(self):
        """Always returns exactly 5 dimension entries."""
        items = [_make_item(0, "a", 1)]
        responses = [1]

        scores = compute_dimension_scores(items, responses)
        assert len(scores) == 5
        dims = {s["dimension"] for s in scores}
        assert dims == {"semantic", "contextual", "form", "relational", "pragmatic"}

    def test_dimension_metadata(self):
        """Each score entry has required metadata fields."""
        items = [_make_item(0, "a", 1)]
        responses = [1]

        scores = compute_dimension_scores(items, responses)
        for s in scores:
            assert "dimension" in s
            assert "label" in s
            assert "label_ko" in s
            assert "color" in s
            assert "correct" in s
            assert "total" in s
            assert "score" in s


# ── Recommendation Engine Tests ─────────────────────────────────


class TestCEFRAdjacency:
    """Test get_adjacent_cefr helper."""

    def test_a1_adjacent(self):
        assert get_adjacent_cefr("A1") == ["A1", "A2"]

    def test_b1_adjacent(self):
        result = get_adjacent_cefr("B1")
        assert "A2" in result
        assert "B1" in result
        assert "B2" in result

    def test_c1_adjacent(self):
        assert get_adjacent_cefr("C1") == ["B2", "C1"]

    def test_unknown_defaults_b1(self):
        result = get_adjacent_cefr("X1")
        assert "B1" in result


class TestStudyPlanGeneration:
    """Test generate_study_plan."""

    @pytest.fixture
    def vocab_pool(self):
        """Create a decent-sized vocab pool for exercise generation."""
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

    def test_high_priority_for_low_scores(self, vocab_pool):
        """score < 40% → high priority with 5 exercises."""
        dim_scores = [
            {"dimension": "semantic", "label": "Semantic", "label_ko": "의미", "color": "#3b82f6", "correct": 1, "total": 5, "score": 20},
            {"dimension": "contextual", "label": "Contextual", "label_ko": "문맥", "color": "#10b981", "correct": 4, "total": 5, "score": 80},
            {"dimension": "form", "label": "Form", "label_ko": "형태", "color": "#f59e0b", "correct": 0, "total": 0, "score": None},
            {"dimension": "relational", "label": "Relational", "label_ko": "관계", "color": "#ef4444", "correct": 3, "total": 5, "score": 60},
            {"dimension": "pragmatic", "label": "Pragmatic", "label_ko": "화용", "color": "#8b5cf6", "correct": 0, "total": 0, "score": None},
        ]
        plan = generate_study_plan(dim_scores, vocab_pool, "B1")

        # semantic (20%) should be high priority
        sem_rec = next(r for r in plan["recommendations"] if r["dimension"] == "semantic")
        assert sem_rec["priority"] == "high"
        assert "semantic" in plan["weak_dimensions"]

    def test_medium_priority(self, vocab_pool):
        """score 40-70% → medium priority with 4 exercises."""
        dim_scores = [
            {"dimension": "semantic", "label": "Semantic", "label_ko": "의미", "color": "#3b82f6", "correct": 3, "total": 5, "score": 60},
            {"dimension": "contextual", "label": "Contextual", "label_ko": "문맥", "color": "#10b981", "correct": 4, "total": 5, "score": 80},
            {"dimension": "form", "label": "Form", "label_ko": "형태", "color": "#f59e0b", "correct": 0, "total": 0, "score": None},
            {"dimension": "relational", "label": "Relational", "label_ko": "관계", "color": "#ef4444", "correct": 4, "total": 5, "score": 80},
            {"dimension": "pragmatic", "label": "Pragmatic", "label_ko": "화용", "color": "#8b5cf6", "correct": 0, "total": 0, "score": None},
        ]
        plan = generate_study_plan(dim_scores, vocab_pool, "B1")

        sem_rec = next(r for r in plan["recommendations"] if r["dimension"] == "semantic")
        assert sem_rec["priority"] == "medium"

    def test_no_weak_dims_still_recommends_lowest(self, vocab_pool):
        """All dimensions strong → still recommend the lowest-scoring one."""
        dim_scores = [
            {"dimension": "semantic", "label": "Semantic", "label_ko": "의미", "color": "#3b82f6", "correct": 4, "total": 5, "score": 80},
            {"dimension": "contextual", "label": "Contextual", "label_ko": "문맥", "color": "#10b981", "correct": 5, "total": 5, "score": 100},
            {"dimension": "form", "label": "Form", "label_ko": "형태", "color": "#f59e0b", "correct": 0, "total": 0, "score": None},
            {"dimension": "relational", "label": "Relational", "label_ko": "관계", "color": "#ef4444", "correct": 4, "total": 5, "score": 80},
            {"dimension": "pragmatic", "label": "Pragmatic", "label_ko": "화용", "color": "#8b5cf6", "correct": 0, "total": 0, "score": None},
        ]
        plan = generate_study_plan(dim_scores, vocab_pool, "B1")

        # Should still generate at least one recommendation
        assert len(plan["recommendations"]) >= 1
        assert plan["recommendations"][0]["priority"] == "low"

    def test_plan_structure(self, vocab_pool):
        """Plan has expected top-level fields."""
        dim_scores = [
            {"dimension": "semantic", "label": "Semantic", "label_ko": "의미", "color": "#3b82f6", "correct": 1, "total": 5, "score": 20},
            {"dimension": "contextual", "label": "Contextual", "label_ko": "문맥", "color": "#10b981", "correct": 4, "total": 5, "score": 80},
            {"dimension": "form", "label": "Form", "label_ko": "형태", "color": "#f59e0b", "correct": 0, "total": 0, "score": None},
            {"dimension": "relational", "label": "Relational", "label_ko": "관계", "color": "#ef4444", "correct": 3, "total": 5, "score": 60},
            {"dimension": "pragmatic", "label": "Pragmatic", "label_ko": "화용", "color": "#8b5cf6", "correct": 0, "total": 0, "score": None},
        ]
        plan = generate_study_plan(dim_scores, vocab_pool, "B1")

        assert "recommendations" in plan
        assert "total_exercises" in plan
        assert "weak_dimensions" in plan
        assert isinstance(plan["recommendations"], list)
        assert isinstance(plan["total_exercises"], int)

    def test_recommendation_has_tips(self, vocab_pool):
        """Each recommendation should have bilingual tips."""
        dim_scores = [
            {"dimension": "semantic", "label": "Semantic", "label_ko": "의미", "color": "#3b82f6", "correct": 1, "total": 5, "score": 20},
            {"dimension": "contextual", "label": "Contextual", "label_ko": "문맥", "color": "#10b981", "correct": 4, "total": 5, "score": 80},
            {"dimension": "form", "label": "Form", "label_ko": "형태", "color": "#f59e0b", "correct": 0, "total": 0, "score": None},
            {"dimension": "relational", "label": "Relational", "label_ko": "관계", "color": "#ef4444", "correct": 3, "total": 5, "score": 60},
            {"dimension": "pragmatic", "label": "Pragmatic", "label_ko": "화용", "color": "#8b5cf6", "correct": 0, "total": 0, "score": None},
        ]
        plan = generate_study_plan(dim_scores, vocab_pool, "B1")

        for rec in plan["recommendations"]:
            assert "tip_ko" in rec
            assert "tip_en" in rec
            assert rec["tip_ko"]  # non-empty
            assert rec["tip_en"]

    def test_exercise_structure(self, vocab_pool):
        """Generated exercises should have required fields."""
        dim_scores = [
            {"dimension": "semantic", "label": "Semantic", "label_ko": "의미", "color": "#3b82f6", "correct": 1, "total": 5, "score": 20},
            {"dimension": "contextual", "label": "Contextual", "label_ko": "문맥", "color": "#10b981", "correct": 4, "total": 5, "score": 80},
            {"dimension": "form", "label": "Form", "label_ko": "형태", "color": "#f59e0b", "correct": 0, "total": 0, "score": None},
            {"dimension": "relational", "label": "Relational", "label_ko": "관계", "color": "#ef4444", "correct": 1, "total": 5, "score": 20},
            {"dimension": "pragmatic", "label": "Pragmatic", "label_ko": "화용", "color": "#8b5cf6", "correct": 0, "total": 0, "score": None},
        ]
        plan = generate_study_plan(dim_scores, vocab_pool, "B1")

        for rec in plan["recommendations"]:
            for ex in rec["exercises"]:
                assert "id" in ex
                assert "dimension" in ex
                assert "word" in ex
                assert "cefr" in ex
                assert "type" in ex
                assert "prompt" in ex
                assert "options" in ex
                assert len(ex["options"]) == 4
                assert "correct_index" in ex
                assert 0 <= ex["correct_index"] <= 3
                assert "explanation" in ex


# ── Explanation Generation Tests ─────────────────────────────────


class TestExplanationGeneration:
    """Test session_manager explanation generation."""

    def test_explanation_type1(self):
        from irt_cat_engine.api.session_manager import SessionManager
        w = _make_vocab("happy", meaning_ko="행복한")
        result = SessionManager._generate_explanation(w, "행복한", 1)
        assert "'happy'" in result
        assert "행복한" in result

    def test_explanation_type3(self):
        from irt_cat_engine.api.session_manager import SessionManager
        w = _make_vocab("happy", meaning_ko="행복한")
        result = SessionManager._generate_explanation(w, "glad", 3)
        assert "동의어" in result
        assert "'glad'" in result

    def test_explanation_type5(self):
        from irt_cat_engine.api.session_manager import SessionManager
        w = _make_vocab("happy", meaning_ko="행복한")
        result = SessionManager._generate_explanation(w, "happy", 5)
        assert "빈칸" in result
        assert "행복한" in result
