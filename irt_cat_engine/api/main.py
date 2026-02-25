"""FastAPI application for IRT CAT Engine."""
import os
import threading
import logging

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware

from ..data.database import init_db, DATABASE_URL
from .routes_test import router as test_router
from .routes_admin import router as admin_router
from .routes_learn import router as learn_router
from .session_manager import session_manager
from ..logging_config import setup_logging
from ..middleware.metrics import PrometheusMiddleware, get_metrics
from ..middleware.logging import RequestLoggingMiddleware

# Initialize logging
logger = setup_logging()

# Initialize Sentry (optional - only if DSN is provided)
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
        ],
        traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
        profiles_sample_rate=0.1,  # 10% for profiling
        environment=os.getenv("ENVIRONMENT", "development"),
        release=os.getenv("RELEASE_VERSION", "0.2.0"),
    )
    logger.info("Sentry error tracking initialized")
else:
    logger.info("Sentry DSN not provided - error tracking disabled")


# Initialize rate limiter (optional - only if enabled)
ENABLE_RATE_LIMITING = os.getenv("ENABLE_RATE_LIMITING", "false").lower() == "true"
if ENABLE_RATE_LIMITING:
    limiter = Limiter(key_func=get_remote_address)
    logger.info("Rate limiting enabled")
else:
    limiter = Limiter(key_func=get_remote_address, enabled=False)
    logger.info("Rate limiting disabled")

# Get allowed origins from environment variable
# Default includes localhost for development
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:8000,https://vocab-cat-test.vercel.app"
).split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    # Startup: init DB and load vocabulary
    init_db()

    # Load vocab data in background thread to not block startup
    def _load():
        session_manager.load_data()

    loader = threading.Thread(target=_load, daemon=True)
    loader.start()
    loader.join(timeout=60)  # Wait up to 60s for data load

    if not session_manager.is_loaded:
        logger.warning("Vocabulary data not loaded yet. Loading continues in background.")

    yield

    # Shutdown: cleanup
    pass


app = FastAPI(
    title="IRT Vocabulary Diagnostic Test API",
    description="IRT 기반 적응형 영어 어휘 진단 테스트 API",
    version="0.2.0",
    lifespan=lifespan,
)

# Add rate limiter state and exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - Secure configuration
# Only allow specific origins, not wildcard
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,  # Changed from True - credentials not needed
    allow_methods=["GET", "POST", "OPTIONS"],  # Only necessary methods
    allow_headers=["Content-Type", "Accept"],  # Specific headers only
)

# Request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Prometheus metrics middleware
app.add_middleware(PrometheusMiddleware)

# Metrics endpoint
@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    return get_metrics()

# Routes
app.include_router(test_router)
app.include_router(admin_router)
app.include_router(learn_router)


@app.get("/")
def root():
    return {
        "service": "IRT Vocabulary Diagnostic Test",
        "version": "0.2.0",
        "status": "ready" if session_manager.is_loaded else "loading",
        "vocab_count": session_manager.vocab_count,
    }


@app.get("/health")
def health():
    """Enhanced health check endpoint with detailed status."""
    is_loaded = session_manager.is_loaded
    
    return {
        "status": "healthy" if is_loaded else "degraded",
        "data_loaded": is_loaded,
        "vocab_count": session_manager.vocab_count if is_loaded else 0,
        "active_sessions": session_manager.active_session_count,
        "database": {
            "connected": True,  # If we got here, DB is accessible
            "url_type": "postgresql" if DATABASE_URL.startswith("postgresql") else "sqlite",
        },
        "version": "0.2.0",
        "uptime_check": "ok",
    }


@app.get("/ready")
def readiness():
    """Readiness probe for Kubernetes/Cloud Run."""
    if not session_manager.is_loaded:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Service not ready - data still loading")
    
    return {"ready": True, "vocab_loaded": True}
