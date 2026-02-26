"""Goal-based vocabulary learning service with DVK progression.

Implements Depth of Vocabulary Knowledge (DVK) aware learning system
following the plan in DEPTH_OF_VOCABULARY_KNOWLEDGE_PLAN.md
"""
import random
from datetime import datetime, timedelta, timezone
from typing import Literal

from sqlalchemy.orm import Session

from ..data.db_models import User, GoalLearningSession, LearnedWord


# Question type distribution per learning goal (DVK Phase 1)
# Based on DEPTH_OF_VOCABULARY_KNOWLEDGE_PLAN.md
GOAL_QUESTION_DISTRIBUTIONS = {
    "elementary": {
        "name": "초등 어휘",
        "target_count": 800,
        "curriculum_levels": ["Elementary 3-4", "Elementary 5-6"],
        "distributions": {
            "first_exposure": [1] * 60 + [3] * 20 + [5] * 20,  # 60% Type 1, 20% Type 3, 20% Type 5
            "review": [1] * 40 + [3] * 30 + [4] * 20 + [5] * 10,
            "mastery": [3] * 40 + [4] * 30 + [5] * 30,
        },
    },
    "middle": {
        "name": "중학교과 어휘",
        "target_count": 1200,
        "curriculum_levels": ["Middle School 1", "Middle School 2", "Middle School 3"],
        "distributions": {
            "first_exposure": [1] * 40 + [3] * 30 + [5] * 20 + [6] * 10,
            "review": [1] * 30 + [3] * 25 + [4] * 20 + [5] * 15 + [6] * 10,
            "mastery": [2] * 20 + [3] * 20 + [4] * 20 + [5] * 20 + [6] * 20,
        },
    },
    "high": {
        "name": "고등학교 어휘",
        "target_count": 1000,
        "curriculum_levels": ["High School 1", "High School 2", "High School 3"],
        "distributions": {
            "first_exposure": [1] * 30 + [3] * 30 + [5] * 30 + [6] * 10,
            "review": [2] * 20 + [3] * 20 + [4] * 20 + [5] * 20 + [6] * 20,
            "mastery": [2] * 25 + [3] * 15 + [4] * 15 + [5] * 25 + [6] * 20,
        },
    },
    "suneung": {
        "name": "수능 어휘",
        "target_count": 5000,
        "curriculum_levels": ["High School 1", "High School 2", "High School 3", "University"],
        "distributions": {
            "first_exposure": [1] * 30 + [2] * 10 + [3] * 20 + [5] * 30 + [6] * 10,
            "review": [2] * 20 + [3] * 20 + [4] * 20 + [5] * 20 + [6] * 20,
            "mastery": [2] * 30 + [3] * 10 + [4] * 10 + [5] * 30 + [6] * 20,
        },
    },
}


def get_learning_stage(review_count: int, correct_count: int) -> Literal["first_exposure", "review", "mastery"]:
    """Determine the learning stage for a word based on review history.

    - first_exposure: Never seen or seen once
    - review: Seen 2-4 times
    - mastery: Seen 5+ times with 80%+ accuracy
    """
    if review_count == 0:
        return "first_exposure"

    if review_count >= 5 and correct_count / review_count >= 0.8:
        return "mastery"

    if review_count >= 2:
        return "review"

    return "first_exposure"


def select_question_type_for_word(
    goal_id: str,
    learning_stage: Literal["first_exposure", "review", "mastery"],
) -> int:
    """Select appropriate question type based on DVK progression.

    Uses goal-specific distributions defined in GOAL_QUESTION_DISTRIBUTIONS.
    """
    goal_config = GOAL_QUESTION_DISTRIBUTIONS.get(goal_id)
    if not goal_config:
        # Default to elementary distribution
        goal_config = GOAL_QUESTION_DISTRIBUTIONS["elementary"]

    distribution = goal_config["distributions"][learning_stage]
    return random.choice(distribution)


def filter_words_by_goal(vocab_words: list, goal_id: str) -> list:
    """Filter vocabulary words based on learning goal curriculum levels."""
    goal_config = GOAL_QUESTION_DISTRIBUTIONS.get(goal_id)
    if not goal_config:
        return vocab_words

    curriculum_levels = set(goal_config["curriculum_levels"])

    filtered = [
        word for word in vocab_words
        if hasattr(word, 'kr_curriculum') and word.kr_curriculum in curriculum_levels
    ]

    # If filtering results in too few words, fall back to all words
    if len(filtered) < 100:
        return vocab_words

    return filtered


def calculate_next_review(
    ease_factor: float,
    interval_days: float,
    self_rating: int,
) -> tuple[datetime, float, float]:
    """Calculate next review date using modified SM-2 algorithm.

    Args:
        ease_factor: Current ease factor (2.5 default)
        interval_days: Current interval in days
        self_rating: 0=forgot, 1=hard, 2=good, 3=easy

    Returns:
        (next_review_date, new_ease_factor, new_interval_days)
    """
    # SM-2 algorithm adjustments
    if self_rating == 0:  # Forgot
        new_interval = 0.0
        new_ease = max(1.3, ease_factor - 0.2)
    elif self_rating == 1:  # Hard
        new_interval = max(1.0, interval_days * 1.2)
        new_ease = max(1.3, ease_factor - 0.15)
    elif self_rating == 2:  # Good
        if interval_days == 0:
            new_interval = 1.0
        else:
            new_interval = interval_days * ease_factor
        new_ease = ease_factor
    else:  # Easy (3)
        if interval_days == 0:
            new_interval = 4.0
        else:
            new_interval = interval_days * ease_factor * 1.3
        new_ease = ease_factor + 0.15

    next_review = datetime.now(timezone.utc) + timedelta(days=new_interval)

    return next_review, new_ease, new_interval


def start_goal_learning_session(
    db: Session,
    user_id: str | None,
    nickname: str | None,
    goal_id: str,
    goal_name: str,
    target_word_count: int,
) -> tuple[GoalLearningSession, User]:
    """Create a new goal-based learning session."""
    # Create or get user
    if user_id:
        user = db.get(User, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
    else:
        user = User(nickname=nickname)
        db.add(user)
        db.flush()

    # Create learning session
    session = GoalLearningSession(
        user_id=user.id,
        goal_id=goal_id,
        goal_name=goal_name,
        target_word_count=target_word_count,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return session, user


def get_next_word_to_learn(
    db: Session,
    session_id: str,
    vocab_words: list,
) -> tuple[dict, int, bool]:
    """Get the next word to learn in this session.

    Returns:
        (word_data, question_type, is_first_exposure)
    """
    session = db.get(GoalLearningSession, session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    # Filter words by goal curriculum
    goal_words = filter_words_by_goal(vocab_words, session.goal_id)

    # Get words already studied in this session
    studied_words = db.query(LearnedWord).filter(
        LearnedWord.session_id == session_id
    ).all()

    studied_word_dict = {lw.word: lw for lw in studied_words}
    studied_word_set = set(studied_word_dict.keys())

    # Priority 1: Words due for review (spaced repetition)
    now = datetime.now(timezone.utc)
    due_words = [
        lw for lw in studied_words
        if lw.next_review_at and lw.next_review_at <= now and not lw.is_mastered
    ]

    if due_words:
        # Sort by oldest review first
        due_words.sort(key=lambda w: w.next_review_at)
        learned_word = due_words[0]

        # Find the word data
        word_data = next((w for w in goal_words if w.word_display == learned_word.word), None)
        if word_data:
            learning_stage = get_learning_stage(learned_word.review_count, learned_word.correct_count)
            question_type = select_question_type_for_word(session.goal_id, learning_stage)
            return word_data, question_type, False

    # Priority 2: New word
    unstudied_words = [w for w in goal_words if w.word_display not in studied_word_set]

    if unstudied_words:
        # Pick a random new word
        word_data = random.choice(unstudied_words)
        question_type = select_question_type_for_word(session.goal_id, "first_exposure")
        return word_data, question_type, True

    # Priority 3: Review any non-mastered word
    non_mastered = [lw for lw in studied_words if not lw.is_mastered]
    if non_mastered:
        # Sort by least recently reviewed
        non_mastered.sort(key=lambda w: w.last_reviewed_at)
        learned_word = non_mastered[0]

        word_data = next((w for w in goal_words if w.word_display == learned_word.word), None)
        if word_data:
            learning_stage = get_learning_stage(learned_word.review_count, learned_word.correct_count)
            question_type = select_question_type_for_word(session.goal_id, learning_stage)
            return word_data, question_type, False

    # No more words to learn
    raise StopIteration("All words in this goal have been mastered")


def submit_learning_card(
    db: Session,
    session_id: str,
    word: str,
    question_type: int,
    self_rating: int,
    is_correct: bool,
    response_time_ms: int | None,
) -> LearnedWord:
    """Record a learning card submission and update word progress."""
    session = db.get(GoalLearningSession, session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    # Get or create LearnedWord
    learned_word = db.query(LearnedWord).filter(
        LearnedWord.session_id == session_id,
        LearnedWord.word == word,
    ).first()

    now = datetime.now(timezone.utc)

    if not learned_word:
        # First exposure
        learned_word = LearnedWord(
            session_id=session_id,
            word=word,
            first_question_type=question_type,
            dvk_level=1,
            assessment_history=[],
        )
        db.add(learned_word)
        session.words_studied += 1

    # Update review statistics
    learned_word.review_count += 1
    if is_correct:
        learned_word.correct_count += 1

    learned_word.last_reviewed_at = now

    # Calculate next review using SM-2
    next_review, new_ease, new_interval = calculate_next_review(
        learned_word.ease_factor,
        learned_word.interval_days,
        self_rating,
    )

    learned_word.next_review_at = next_review
    learned_word.ease_factor = new_ease
    learned_word.interval_days = new_interval

    # Update DVK level (1-6) based on question type and performance
    if is_correct and question_type > learned_word.dvk_level:
        learned_word.dvk_level = question_type

    # Check mastery: 5+ reviews with 80%+ accuracy and interval >= 7 days
    if (
        learned_word.review_count >= 5
        and learned_word.correct_count / learned_word.review_count >= 0.8
        and learned_word.interval_days >= 7.0
    ):
        if not learned_word.is_mastered:
            learned_word.is_mastered = True
            learned_word.mastered_at = now
            session.words_mastered += 1

    # Append to assessment history
    if not learned_word.assessment_history:
        learned_word.assessment_history = []

    learned_word.assessment_history.append({
        "date": now.isoformat(),
        "rating": self_rating,
        "question_type": question_type,
        "is_correct": is_correct,
        "response_time_ms": response_time_ms,
    })

    # Update session stats
    session.total_reviews += 1
    session.last_activity_at = now

    db.commit()
    db.refresh(learned_word)
    db.refresh(session)

    return learned_word
