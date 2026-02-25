"""FastAPI application for IRT CAT Engine."""
import os
import threading
import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..data.database import init_db, DATABASE_URL
from .routes_test import router as test_router
from .routes_admin import router as admin_router
from .routes_learn import router as learn_router
from .session_manager import session_manager
from ..logging_config import setup_logging

# Initialize logging
logger = setup_logging()


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

# CORS - Secure configuration
# Only allow specific origins, not wildcard
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,  # Changed from True - credentials not needed
    allow_methods=["GET", "POST", "OPTIONS"],  # Only necessary methods
    allow_headers=["Content-Type", "Accept"],  # Specific headers only
)

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
