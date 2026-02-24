"""Admin API routes for parameter management and analytics."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..data.database import get_db
from ..data.db_models import Response, ItemExposure, TestSession
from ..reporting.exposure_analysis import analyze_exposure, identify_expansion_needs
from ..config import IRT_MODEL
from .schemas import RecalibrateResponse
from .session_manager import session_manager

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/recalibrate", response_model=RecalibrateResponse)
def recalibrate_parameters(db: Session = Depends(get_db)):
    """Recalibrate item exposure parameters based on accumulated response data.

    This updates the Sympson-Hetter exposure control parameters and
    collects item-level statistics for future Bayesian parameter updates.
    """
    from sqlalchemy import func, case

    item_stats = (
        db.query(
            Response.item_id,
            Response.word,
            func.count(Response.id).label("admin_count"),
            func.sum(case((Response.is_correct == True, 1), else_=0)).label("correct_count"),
        )
        .group_by(Response.item_id, Response.word)
        .all()
    )

    updated = 0
    for row in item_stats:
        exposure = db.get(ItemExposure, row.item_id)
        if exposure is None:
            exposure = ItemExposure(
                item_id=row.item_id,
                word=row.word,
                admin_count=row.admin_count,
                correct_count=row.correct_count or 0,
            )
            db.add(exposure)
        else:
            exposure.admin_count = row.admin_count
            exposure.correct_count = row.correct_count or 0
        updated += 1

    db.commit()

    return RecalibrateResponse(
        items_recalibrated=updated,
        message=f"Updated exposure statistics for {updated} items from response data.",
    )


@router.get("/stats")
def get_server_stats():
    """Get server statistics."""
    return {
        "vocab_loaded": session_manager.is_loaded,
        "vocab_count": session_manager.vocab_count,
        "active_sessions": session_manager.active_session_count,
        "irt_model": IRT_MODEL,
    }


@router.post("/cleanup")
def cleanup_stale_sessions():
    """Remove stale sessions from memory."""
    removed = session_manager.cleanup_stale_sessions()
    return {"removed": removed, "remaining": session_manager.active_session_count}


@router.get("/exposure")
def get_exposure_analysis(db: Session = Depends(get_db)):
    """Get item exposure analysis report.

    Analyzes how evenly items are being used across test sessions,
    identifies over-exposed and under-used items, and provides
    recommendations for pool health.
    """
    if not session_manager.is_loaded:
        raise HTTPException(status_code=503, detail="Server data not loaded")

    # Get total completed sessions
    total_sessions = db.query(func.count(TestSession.id)).filter(
        TestSession.completed_at.is_not(None)
    ).scalar() or 0

    # Get exposure counts from ItemExposure table
    exposures = db.query(ItemExposure).all()
    exposure_counts = {e.item_id: e.admin_count for e in exposures}

    item_pool = session_manager.get_item_pool(question_type=1)

    report = analyze_exposure(item_pool, exposure_counts, total_sessions)
    return report


@router.get("/exposure/expansion")
def get_expansion_needs(db: Session = Depends(get_db)):
    """Identify areas where the item pool needs expansion.

    Analyzes which difficulty ranges, CEFR levels, and topics
    need more items based on exposure patterns.
    """
    if not session_manager.is_loaded:
        raise HTTPException(status_code=503, detail="Server data not loaded")

    total_sessions = db.query(func.count(TestSession.id)).filter(
        TestSession.completed_at.is_not(None)
    ).scalar() or 0

    exposures = db.query(ItemExposure).all()
    exposure_counts = {e.item_id: e.admin_count for e in exposures}

    item_pool = session_manager.get_item_pool(question_type=1)

    return identify_expansion_needs(item_pool, exposure_counts, total_sessions)
