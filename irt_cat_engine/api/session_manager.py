"""In-memory CAT session manager with Redis-ready interface.

Active test sessions live in memory for low-latency item selection.
Completed sessions are persisted to the database.
This can be swapped with a Redis-backed implementation later.
"""
import logging
import random
import time
from dataclasses import dataclass, field

import numpy as np

from ..cat.session import CATSession
from ..cat.stopping_rules import StoppingRules
from ..data.load_vocabulary import VocabWord, load_vocabulary
from ..data.graph_connector import vocab_graph
from ..item_bank.distractor_engine import DistractorEngine
from ..item_bank.parameter_initializer import initialize_item_parameters
from ..config import QUESTION_TYPE_B_MODIFIER
from ..models.irt_2pl import ItemParameters

logger = logging.getLogger("irt_cat_engine.session_manager")


@dataclass
class ActiveSession:
    """An active CAT session with all required context."""
    session_id: str
    user_id: str
    cat_session: CATSession
    question_type: int
    created_at: float = field(default_factory=time.time)


class SessionManager:
    """Manages active CAT sessions and provides item generation."""

    def __init__(self):
        self._active: dict[str, ActiveSession] = {}
        self._vocab: list[VocabWord] | None = None
        self._items_by_type: dict[int, list[ItemParameters]] = {}
        self._distractor_engine: DistractorEngine | None = None
        self._vocab_by_word: dict[str, VocabWord] = {}

    @property
    def is_loaded(self) -> bool:
        return self._vocab is not None

    def load_data(self):
        """Load vocabulary and initialize item parameters. Called once at startup."""
        if self._vocab is not None:
            return

        self._vocab = load_vocabulary()
        self._vocab_by_word = {w.word_display.lower(): w for w in self._vocab}

        # Load graph for Strategy D distractors (optional, non-blocking)
        try:
            vocab_graph.load()
            logger.info("Vocabulary graph loaded successfully")
        except FileNotFoundError:
            logger.warning("vocabulary_graph.json not found - enhanced distractors disabled")
        except Exception as e:
            logger.error(f"Failed to load vocabulary graph: {e}", exc_info=True)

        self._distractor_engine = DistractorEngine(
            self._vocab,
            graph=vocab_graph if vocab_graph.is_loaded else None,
        )

        # Pre-initialize item parameters for question type 1 (baseline)
        self._items_by_type[1] = initialize_item_parameters(self._vocab, question_type=1)

    def get_item_pool(self, question_type: int = 1) -> list[ItemParameters]:
        """Get or lazily initialize item pool for a question type."""
        if question_type not in self._items_by_type:
            self._items_by_type[question_type] = initialize_item_parameters(
                self._vocab, question_type=question_type
            )
        return self._items_by_type[question_type]

    def create_session(
        self,
        session_id: str,
        user_id: str,
        grade: str = "중2",
        self_assess: str = "intermediate",
        exam_experience: str = "none",
        question_type: int = 1,
    ) -> ActiveSession:
        """Create a new CAT session."""
        # Mixed mode (0) uses Type 1 pool for item selection;
        # actual question type is chosen dynamically per item.
        pool_type = 1 if question_type == 0 else question_type
        item_pool = self.get_item_pool(pool_type)

        cat_session = CATSession.create(
            item_pool=item_pool,
            grade=grade,
            self_assess=self_assess,
            exam_experience=exam_experience,
        )

        active = ActiveSession(
            session_id=session_id,
            user_id=user_id,
            cat_session=cat_session,
            question_type=question_type,
        )
        self._active[session_id] = active
        return active

    def get_session(self, session_id: str) -> ActiveSession | None:
        """Retrieve an active session."""
        return self._active.get(session_id)

    def remove_session(self, session_id: str):
        """Remove a completed session from memory."""
        self._active.pop(session_id, None)

    def generate_item_content(self, item: ItemParameters, question_type: int) -> dict | None:
        """Generate full item content (stem, options, distractors) for an IRT item."""
        vocab_word = self._vocab_by_word.get(item.word.lower())
        if vocab_word is None:
            return None

        result = self._distractor_engine.generate_item(vocab_word, question_type=question_type)
        if result is None:
            # Fallback to type 1 if requested type fails
            result = self._distractor_engine.generate_item(vocab_word, question_type=1)

        if result is None:
            return None

        # Shuffle options
        options = [result["correct_answer"]] + result["distractors"]
        random.shuffle(options)

        actual_type = result.get("question_type", question_type)
        explanation = self._generate_explanation(
            vocab_word, result["correct_answer"], actual_type
        )

        return {
            "item_id": item.item_id,
            "word": item.word,
            "question_type": actual_type,
            "stem": result["stem"],
            "correct_answer": result["correct_answer"],
            "distractors": result["distractors"],
            "options": options,
            "pos": item.pos,
            "cefr": item.cefr,
            "explanation": explanation,
        }

    def choose_question_type(
        self, item: ItemParameters, items_completed: int, type_counts: dict[int, int]
    ) -> int:
        """Choose a question type for mixed mode based on progression and data availability."""
        vocab_word = self._vocab_by_word.get(item.word.lower())
        if vocab_word is None:
            return 1

        # Get preferred types based on test progression
        from ..cat.item_selector import ContentTracker
        preferred = ContentTracker().preferred_question_types(items_completed)
        candidates = preferred if preferred else [1, 2, 3, 4, 5, 6]

        # Filter by data availability
        eligible = []
        for qt in candidates:
            if qt in (1, 2):
                eligible.append(qt)  # Always available
            elif qt == 3 and vocab_word.synonym:
                eligible.append(qt)
            elif qt == 4 and vocab_word.antonym:
                eligible.append(qt)
            elif qt == 5 and (vocab_word.sentence_1 or vocab_word.sentence_2):
                eligible.append(qt)
            elif qt == 6 and vocab_word.collocation:
                eligible.append(qt)

        if not eligible:
            return 1

        # Pick the least-used type for balanced distribution
        min_count = min(type_counts.get(qt, 0) for qt in eligible)
        least_used = [qt for qt in eligible if type_counts.get(qt, 0) == min_count]
        return random.choice(least_used)

    @staticmethod
    def adjust_item_difficulty(item: ItemParameters, chosen_type: int):
        """Apply question-type difficulty modifier to an item's b parameter."""
        modifier = QUESTION_TYPE_B_MODIFIER.get(chosen_type, 0.0)
        item.difficulty_b += modifier
        item.question_type = chosen_type

    @staticmethod
    def _generate_explanation(vocab_word, correct_answer: str, question_type: int) -> str:
        """Generate a bilingual explanation for the answer."""
        word = vocab_word.word_display
        ko = vocab_word.meaning_ko
        if question_type == 1:
            return f"'{word}'의 뜻: {ko}"
        elif question_type == 2:
            defn = vocab_word.definition_en or ko
            return f"'{word}' means: {defn} ({ko})"
        elif question_type == 3:
            return f"'{correct_answer}'은/는 '{word}'의 동의어입니다 ({ko})"
        elif question_type == 4:
            return f"'{correct_answer}'은/는 '{word}'의 반의어입니다 ({ko})"
        elif question_type == 5:
            return f"'{word}'가 빈칸에 적합한 단어입니다. ({ko})"
        elif question_type == 6:
            return f"'{word}': {ko}"
        return f"'{word}': {ko}"

    @property
    def active_session_count(self) -> int:
        return len(self._active)

    @property
    def vocab_count(self) -> int:
        return len(self._vocab) if self._vocab else 0

    def cleanup_stale_sessions(self, max_age_seconds: int = 3600):
        """Remove sessions older than max_age_seconds."""
        now = time.time()
        stale = [
            sid for sid, s in self._active.items()
            if now - s.created_at > max_age_seconds
        ]
        for sid in stale:
            self._active.pop(sid, None)
        return len(stale)


# Singleton instance
session_manager = SessionManager()
