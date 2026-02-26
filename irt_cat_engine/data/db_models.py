"""SQLAlchemy ORM models for IRT CAT Engine."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, JSON, Text,
)
from sqlalchemy.orm import relationship

from .database import Base


def _uuid() -> str:
    return uuid.uuid4().hex


class User(Base):
    __tablename__ = "users"

    id = Column(String(32), primary_key=True, default=_uuid)
    nickname = Column(String(100), nullable=True)
    grade = Column(String(20), nullable=False, default="중2")
    self_assess = Column(String(20), nullable=False, default="intermediate")
    exam_experience = Column(String(20), nullable=False, default="none")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    sessions = relationship("TestSession", back_populates="user", order_by="TestSession.started_at.desc()")


class TestSession(Base):
    __tablename__ = "test_sessions"

    id = Column(String(32), primary_key=True, default=_uuid)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    # Initial state
    initial_theta = Column(Float, nullable=False, default=0.0)

    # Final results (filled on completion)
    final_theta = Column(Float, nullable=True)
    final_se = Column(Float, nullable=True)
    reliability = Column(Float, nullable=True)
    cefr_level = Column(String(5), nullable=True)
    cefr_probabilities = Column(JSON, nullable=True)
    curriculum_level = Column(String(50), nullable=True)
    vocab_size_estimate = Column(Integer, nullable=True)
    total_items = Column(Integer, nullable=True)
    total_correct = Column(Integer, nullable=True)
    accuracy = Column(Float, nullable=True)
    termination_reason = Column(String(50), nullable=True)
    topic_strengths = Column(JSON, nullable=True)
    topic_weaknesses = Column(JSON, nullable=True)
    dimension_scores = Column(JSON, nullable=True)

    user = relationship("User", back_populates="sessions")
    responses = relationship("Response", back_populates="session", order_by="Response.sequence")


class Response(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(32), ForeignKey("test_sessions.id"), nullable=False)
    item_id = Column(Integer, nullable=False)
    word = Column(String(100), nullable=False)
    question_type = Column(Integer, nullable=False, default=1)
    is_correct = Column(Boolean, nullable=False)
    is_dont_know = Column(Boolean, nullable=False, default=False)
    response_time_ms = Column(Integer, nullable=True)
    sequence = Column(Integer, nullable=False)

    # Theta tracking
    theta_before = Column(Float, nullable=False)
    theta_after = Column(Float, nullable=False)
    se_before = Column(Float, nullable=False)
    se_after = Column(Float, nullable=False)

    # Item metadata for later analysis
    difficulty_b = Column(Float, nullable=False)
    discrimination_a = Column(Float, nullable=False)

    session = relationship("TestSession", back_populates="responses")


class ItemExposure(Base):
    """Track how often each item is administered (for exposure control)."""
    __tablename__ = "item_exposure"

    item_id = Column(Integer, primary_key=True)
    word = Column(String(100), nullable=False)
    admin_count = Column(Integer, nullable=False, default=0)
    correct_count = Column(Integer, nullable=False, default=0)
    last_administered = Column(DateTime, nullable=True)


class GoalLearningSession(Base):
    """Goal-based learning session (e.g., elementary, middle school vocabulary)."""
    __tablename__ = "goal_learning_sessions"

    id = Column(String(32), primary_key=True, default=_uuid)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False)
    goal_id = Column(String(50), nullable=False)  # "elementary", "middle", "high", etc.
    goal_name = Column(String(100), nullable=False)
    target_word_count = Column(Integer, nullable=False)

    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_activity_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    # Progress tracking
    words_studied = Column(Integer, nullable=False, default=0)
    words_mastered = Column(Integer, nullable=False, default=0)
    total_reviews = Column(Integer, nullable=False, default=0)

    user = relationship("User", backref="goal_sessions")
    learned_words = relationship("LearnedWord", back_populates="session", order_by="LearnedWord.last_reviewed_at.desc()")


class LearnedWord(Base):
    """Track individual words learned in goal-based sessions."""
    __tablename__ = "learned_words"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(32), ForeignKey("goal_learning_sessions.id"), nullable=False)
    word = Column(String(100), nullable=False)

    # First exposure
    first_seen_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    first_question_type = Column(Integer, nullable=False)

    # Current learning state
    dvk_level = Column(Integer, nullable=False, default=1)  # 1-6: Recognition to Production
    review_count = Column(Integer, nullable=False, default=0)
    correct_count = Column(Integer, nullable=False, default=0)
    last_reviewed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Spaced repetition data
    next_review_at = Column(DateTime, nullable=True)
    ease_factor = Column(Float, nullable=False, default=2.5)  # SM-2 algorithm
    interval_days = Column(Float, nullable=False, default=0.0)

    # Self-assessment history (JSON array of {date, rating, question_type})
    assessment_history = Column(JSON, nullable=True)

    is_mastered = Column(Boolean, nullable=False, default=False)
    mastered_at = Column(DateTime, nullable=True)

    session = relationship("GoalLearningSession", back_populates="learned_words")
