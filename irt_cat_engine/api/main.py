"""FastAPI application for IRT CAT Engine."""
import threading

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..data.database import init_db
from .routes_test import router as test_router
from .routes_admin import router as admin_router
from .routes_learn import router as learn_router
from .session_manager import session_manager


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
        print("WARNING: Vocabulary data not loaded yet. Loading continues in background.")

    yield

    # Shutdown: cleanup
    pass


app = FastAPI(
    title="IRT Vocabulary Diagnostic Test API",
    description="IRT 기반 적응형 영어 어휘 진단 테스트 API",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    return {
        "status": "healthy",
        "data_loaded": session_manager.is_loaded,
        "active_sessions": session_manager.active_session_count,
    }
