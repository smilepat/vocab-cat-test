"""Prometheus metrics middleware for monitoring."""
import time
import logging
from typing import Callable

from fastapi import Request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger("irt_cat_engine.metrics")

# Define metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)

REQUEST_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests in progress",
    ["method", "endpoint"]
)

# CAT-specific metrics
TEST_SESSIONS_CREATED = Counter(
    "test_sessions_created_total",
    "Total number of test sessions created"
)

TEST_SESSIONS_COMPLETED = Counter(
    "test_sessions_completed_total",
    "Total number of test sessions completed"
)

ITEMS_ADMINISTERED = Counter(
    "items_administered_total",
    "Total number of items administered",
    ["question_type"]
)

THETA_ESTIMATES = Histogram(
    "theta_estimates",
    "Distribution of theta estimates",
    buckets=[-3, -2, -1, -0.5, 0, 0.5, 1, 2, 3]
)

ACTIVE_SESSIONS = Gauge(
    "active_sessions",
    "Number of currently active test sessions"
)

ITEM_GENERATION_SCORE = Histogram(
    "item_generation_score",
    "Distribution of generated item quality score (0-100)",
    ["stage", "model", "exam_type"],
    buckets=[0, 20, 40, 50, 60, 70, 80, 90, 95, 100],
)

ITEM_GENERATION_TARGET_GAP = Histogram(
    "item_generation_target_gap",
    "Absolute gap between target and actual difficulty",
    ["stage", "model", "exam_type"],
    buckets=[0, 1, 2, 3, 5, 8, 13, 21],
)

ITEM_GENERATION_ACCEPTED_TOTAL = Counter(
    "item_generation_accepted_total",
    "Total number of generated items accepted",
    ["stage", "model", "exam_type"],
)

ITEM_GENERATION_REJECTED_TOTAL = Counter(
    "item_generation_rejected_total",
    "Total number of generated items rejected",
    ["stage", "model", "exam_type"],
)


def observe_item_generation_score(
    score: float,
    *,
    stage: str = "final",
    model: str = "unknown",
    exam_type: str = "csat",
) -> None:
    """Record a generated item score into histogram metrics."""
    score_value = max(0.0, min(100.0, float(score)))
    ITEM_GENERATION_SCORE.labels(stage=stage, model=model, exam_type=exam_type).observe(score_value)


def observe_item_generation_target_gap(
    target_difficulty: float,
    actual_difficulty: float,
    *,
    stage: str = "final",
    model: str = "unknown",
    exam_type: str = "csat",
) -> None:
    """Record absolute difficulty gap for generated items."""
    gap = abs(float(target_difficulty) - float(actual_difficulty))
    ITEM_GENERATION_TARGET_GAP.labels(stage=stage, model=model, exam_type=exam_type).observe(gap)


def record_item_generation_outcome(
    accepted: bool,
    *,
    stage: str = "final",
    model: str = "unknown",
    exam_type: str = "csat",
) -> None:
    """Count whether generated item is accepted or rejected."""
    labels = {"stage": stage, "model": model, "exam_type": exam_type}
    if accepted:
        ITEM_GENERATION_ACCEPTED_TOTAL.labels(**labels).inc()
    else:
        ITEM_GENERATION_REJECTED_TOTAL.labels(**labels).inc()


def record_item_generation(
    score: float,
    *,
    accepted: bool,
    stage: str = "final",
    model: str = "unknown",
    exam_type: str = "csat",
    target_difficulty: float | None = None,
    actual_difficulty: float | None = None,
) -> None:
    """Record score, outcome and optional target-gap metrics for one generated item."""
    observe_item_generation_score(score, stage=stage, model=model, exam_type=exam_type)
    record_item_generation_outcome(accepted, stage=stage, model=model, exam_type=exam_type)

    if target_difficulty is not None and actual_difficulty is not None:
        observe_item_generation_target_gap(
            target_difficulty,
            actual_difficulty,
            stage=stage,
            model=model,
            exam_type=exam_type,
        )


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics for all HTTP requests."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and collect metrics."""
        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)
        
        method = request.method
        path = request.url.path
        
        # Track in-progress requests
        REQUEST_IN_PROGRESS.labels(method=method, endpoint=path).inc()
        
        # Measure duration
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            logger.error(f"Request failed: {e}", exc_info=True)
            status_code = 500
            raise
        finally:
            # Record metrics
            duration = time.time() - start_time
            REQUEST_COUNT.labels(method=method, endpoint=path, status_code=status_code).inc()
            REQUEST_DURATION.labels(method=method, endpoint=path).observe(duration)
            REQUEST_IN_PROGRESS.labels(method=method, endpoint=path).dec()
        
        return response


def get_metrics():
    """Return Prometheus metrics in text format."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
