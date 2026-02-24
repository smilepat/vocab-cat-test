"""API routes for learning recommendations."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..data.database import get_db
from ..data.db_models import TestSession
from ..reporting.recommendation_engine import generate_study_plan
from ..reporting.matrix_generator import compute_vocab_matrix
from .session_manager import session_manager

router = APIRouter(prefix="/api/v1", tags=["learn"])


@router.get("/learn/{session_id}/plan")
def get_study_plan(session_id: str, db: Session = Depends(get_db)):
    """Generate a personalized study plan from test results."""
    db_session = db.get(TestSession, session_id)
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if db_session.final_theta is None:
        raise HTTPException(status_code=400, detail="Test not completed yet")

    dimension_scores = db_session.dimension_scores
    if not dimension_scores:
        raise HTTPException(status_code=400, detail="No dimension scores available")

    # Load vocab words for exercise generation
    if not session_manager.is_loaded:
        raise HTTPException(status_code=503, detail="Server is still loading data")

    vocab_words = session_manager._vocab
    cefr_level = db_session.cefr_level or "B1"

    plan = generate_study_plan(
        dimension_scores=dimension_scores,
        vocab_words=vocab_words,
        cefr_level=cefr_level,
    )

    return plan


@router.get("/learn/{session_id}/matrix")
def get_vocab_matrix(session_id: str, db: Session = Depends(get_db)):
    """Generate vocabulary matrix visualization data."""
    db_session = db.get(TestSession, session_id)
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if db_session.final_theta is None:
        raise HTTPException(status_code=400, detail="Test not completed yet")

    if not session_manager.is_loaded:
        raise HTTPException(status_code=503, detail="Server is still loading data")

    vocab_words = session_manager._vocab
    item_bank = session_manager.get_item_pool(question_type=1)
    cefr_level = db_session.cefr_level or "B1"
    theta = db_session.final_theta

    return compute_vocab_matrix(
        theta=theta,
        cefr_level=cefr_level,
        vocab_words=vocab_words,
        item_bank=item_bank,
        sample_size=100,
    )
