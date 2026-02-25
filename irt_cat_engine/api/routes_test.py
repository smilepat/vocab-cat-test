"""API routes for test sessions."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
from sqlalchemy.orm import Session

from ..data.database import get_db
from ..data.db_models import User, TestSession, Response
from .schemas import (
    TestStartRequest, TestStartResponse, TestRespondRequest, TestRespondResponse,
    TestResultsResponse, ItemResponse, TestProgressResponse,
    CEFRProbabilities, TopicAnalysis, DimensionScore,
    UserHistoryResponse, UserHistoryEntry,
)
from .session_manager import session_manager

router = APIRouter(prefix="/api/v1", tags=["test"])


def _item_to_response(item_content: dict) -> ItemResponse:
    return ItemResponse(
        item_id=item_content["item_id"],
        word=item_content["word"],
        question_type=item_content["question_type"],
        stem=item_content.get("stem"),
        correct_answer=item_content.get("correct_answer"),
        distractors=item_content.get("distractors"),
        options=item_content.get("options"),
        pos=item_content.get("pos", ""),
        cefr=item_content.get("cefr", ""),
        explanation=item_content.get("explanation"),
    )


def _progress_from_session(cat_session) -> TestProgressResponse:
    progress = cat_session.get_progress()
    return TestProgressResponse(
        items_completed=progress["items_completed"],
        total_correct=progress["total_correct"],
        accuracy=progress["accuracy"],
        current_theta=progress["current_theta"],
        current_se=progress["current_se"],
        is_complete=progress["is_complete"],
    )


def _results_to_response(session_id: str, results: dict, termination_reason: str) -> TestResultsResponse:
    cefr_probs = results.get("cefr_probabilities", {})
    return TestResultsResponse(
        session_id=session_id,
        theta=results["theta"],
        se=results["se"],
        reliability=results["reliability"],
        cefr_level=results["cefr_level"],
        cefr_probabilities=CEFRProbabilities(
            A1=cefr_probs.get("A1", 0.0),
            A2=cefr_probs.get("A2", 0.0),
            B1=cefr_probs.get("B1", 0.0),
            B2=cefr_probs.get("B2", 0.0),
            C1=cefr_probs.get("C1", 0.0),
        ),
        curriculum_level=results["curriculum_level"],
        vocab_size_estimate=results["vocab_size_estimate"],
        total_items=results["total_items"],
        total_correct=results["total_correct"],
        accuracy=results["accuracy"],
        termination_reason=termination_reason,
        topic_strengths=[TopicAnalysis(**t) for t in results.get("topic_strengths", [])],
        topic_weaknesses=[TopicAnalysis(**t) for t in results.get("topic_weaknesses", [])],
        dimension_scores=[DimensionScore(**d) for d in results.get("dimension_scores", [])],
        oxford_coverage=results.get("oxford_coverage", 0.0),
        estimated_vocabulary=results.get("estimated_vocabulary", 0),
    )


@router.post("/test/start", response_model=TestStartResponse)
def start_test(req: TestStartRequest, db: Session = Depends(get_db)):
    """Start a new adaptive test session."""
    if not session_manager.is_loaded:
        raise HTTPException(status_code=503, detail="Server is still loading data. Try again shortly.")

    # Get or create user
    if req.user_id:
        user = db.get(User, req.user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {req.user_id} not found")
    else:
        user = User(
            nickname=req.nickname,
            grade=req.grade,
            self_assess=req.self_assess,
            exam_experience=req.exam_experience,
        )
        db.add(user)
        db.flush()

    # Create DB session record
    db_session = TestSession(user_id=user.id)
    db.add(db_session)
    db.flush()

    # Create in-memory CAT session
    active = session_manager.create_session(
        session_id=db_session.id,
        user_id=user.id,
        grade=req.grade,
        self_assess=req.self_assess,
        exam_experience=req.exam_experience,
        question_type=req.question_type,
    )

    # Update DB with initial theta
    db_session.initial_theta = active.cat_session.initial_theta
    db.commit()

    # Get first item
    first_item_params = active.cat_session.get_next_item()
    if first_item_params is None:
        raise HTTPException(status_code=500, detail="Failed to select first item")

    # Mixed mode: dynamically choose question type per item
    if req.question_type == 0:
        chosen_type = session_manager.choose_question_type(
            first_item_params, items_completed=0, type_counts={}
        )
        session_manager.adjust_item_difficulty(first_item_params, chosen_type)
        content_qt = chosen_type
    else:
        content_qt = req.question_type

    item_content = session_manager.generate_item_content(
        first_item_params, question_type=content_qt
    )
    if item_content is None:
        raise HTTPException(status_code=500, detail="Failed to generate item content")

    # Store pending item on the active session for later response matching
    active._pending_item = first_item_params

    return TestStartResponse(
        session_id=db_session.id,
        user_id=user.id,
        initial_theta=round(active.cat_session.initial_theta, 3),
        first_item=_item_to_response(item_content),
        progress=_progress_from_session(active.cat_session),
    )


@router.post("/test/{session_id}/respond", response_model=TestRespondResponse)
def respond_to_item(session_id: str, req: TestRespondRequest, db: Session = Depends(get_db)):
    """Submit a response and get the next item (or results if complete)."""
    active = session_manager.get_session(session_id)
    if active is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    cat = active.cat_session

    # Find the item by ID
    pending = getattr(active, "_pending_item", None)
    if pending is None or pending.item_id != req.item_id:
        # Look up in pool
        matching = [item for item in cat.item_pool if item.item_id == req.item_id]
        if not matching:
            raise HTTPException(status_code=400, detail=f"Item {req.item_id} not in pool")
        pending = matching[0]

    # Record response
    theta_before = cat.current_theta
    se_before = cat.current_se
    cat.record_response(pending, req.is_correct, is_dont_know=req.is_dont_know)

    # Save response to DB
    db_response = Response(
        session_id=session_id,
        item_id=pending.item_id,
        word=pending.word,
        question_type=pending.question_type,
        is_correct=req.is_correct,
        is_dont_know=req.is_dont_know,
        response_time_ms=req.response_time_ms,
        sequence=len(cat.responses),
        theta_before=theta_before,
        theta_after=cat.current_theta,
        se_before=se_before,
        se_after=cat.current_se,
        difficulty_b=pending.difficulty_b,
        discrimination_a=pending.discrimination_a,
    )
    db.add(db_response)

    progress = _progress_from_session(cat)

    if cat.is_complete:
        # Generate final results
        results = cat.get_results()

        # Update DB session
        db_session = db.get(TestSession, session_id)
        if db_session:
            db_session.completed_at = datetime.now(timezone.utc)
            db_session.final_theta = results["theta"]
            db_session.final_se = results["se"]
            db_session.reliability = results["reliability"]
            db_session.cefr_level = results["cefr_level"]
            db_session.cefr_probabilities = results["cefr_probabilities"]
            db_session.curriculum_level = results["curriculum_level"]
            db_session.vocab_size_estimate = results["vocab_size_estimate"]
            db_session.total_items = results["total_items"]
            db_session.total_correct = results["total_correct"]
            db_session.accuracy = results["accuracy"]
            db_session.termination_reason = cat.termination_reason
            db_session.topic_strengths = results["topic_strengths"]
            db_session.topic_weaknesses = results["topic_weaknesses"]
            db_session.dimension_scores = results.get("dimension_scores", [])

        db.commit()

        # Clean up memory
        session_manager.remove_session(session_id)

        return TestRespondResponse(
            is_complete=True,
            progress=progress,
            next_item=None,
            results=_results_to_response(session_id, results, cat.termination_reason),
        )

    # Get next item
    next_item_params = cat.get_next_item()
    if next_item_params is None:
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to select next item")

    # Mixed mode: dynamically choose question type per item
    if active.question_type == 0:
        type_counts = cat.content_tracker.type_counts if hasattr(cat, 'content_tracker') else {}
        chosen_type = session_manager.choose_question_type(
            next_item_params,
            items_completed=len(cat.responses),
            type_counts=type_counts,
        )
        session_manager.adjust_item_difficulty(next_item_params, chosen_type)
        content_qt = chosen_type
    else:
        content_qt = active.question_type

    item_content = session_manager.generate_item_content(
        next_item_params, question_type=content_qt
    )
    if item_content is None:
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to generate item content")

    active._pending_item = next_item_params
    db.commit()

    return TestRespondResponse(
        is_complete=False,
        progress=progress,
        next_item=_item_to_response(item_content),
        results=None,
    )


@router.get("/test/{session_id}/results", response_model=TestResultsResponse)
def get_results(session_id: str, db: Session = Depends(get_db)):
    """Get results for a completed test session."""
    db_session = db.get(TestSession, session_id)
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if db_session.final_theta is None:
        # Check if still active
        active = session_manager.get_session(session_id)
        if active is not None:
            raise HTTPException(status_code=400, detail="Test is still in progress")
        raise HTTPException(status_code=400, detail="Test was not completed")

    cefr_probs = db_session.cefr_probabilities or {}
    return TestResultsResponse(
        session_id=session_id,
        theta=db_session.final_theta,
        se=db_session.final_se,
        reliability=db_session.reliability,
        cefr_level=db_session.cefr_level,
        cefr_probabilities=CEFRProbabilities(
            A1=cefr_probs.get("A1", 0.0),
            A2=cefr_probs.get("A2", 0.0),
            B1=cefr_probs.get("B1", 0.0),
            B2=cefr_probs.get("B2", 0.0),
            C1=cefr_probs.get("C1", 0.0),
        ),
        curriculum_level=db_session.curriculum_level,
        vocab_size_estimate=db_session.vocab_size_estimate,
        total_items=db_session.total_items,
        total_correct=db_session.total_correct,
        accuracy=db_session.accuracy,
        termination_reason=db_session.termination_reason or "",
        topic_strengths=[TopicAnalysis(**t) for t in (db_session.topic_strengths or [])],
        topic_weaknesses=[TopicAnalysis(**t) for t in (db_session.topic_weaknesses or [])],
    )


@router.get("/user/{user_id}/history", response_model=UserHistoryResponse)
def get_user_history(user_id: str, db: Session = Depends(get_db)):
    """Get a user's test history."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    sessions = []
    for s in user.sessions:
        sessions.append(UserHistoryEntry(
            session_id=s.id,
            started_at=s.started_at.isoformat() if s.started_at else "",
            completed_at=s.completed_at.isoformat() if s.completed_at else None,
            final_theta=s.final_theta,
            cefr_level=s.cefr_level,
            curriculum_level=s.curriculum_level,
            vocab_size_estimate=s.vocab_size_estimate,
            total_items=s.total_items,
            accuracy=s.accuracy,
        ))

    return UserHistoryResponse(
        user_id=user_id,
        total_sessions=len(sessions),
        sessions=sessions,
    )
