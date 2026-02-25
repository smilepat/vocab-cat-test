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
