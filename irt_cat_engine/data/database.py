"""SQLAlchemy database engine and session management.

Uses SQLite for development, easily swappable to PostgreSQL for production.
Database URL is configured via DATABASE_URL environment variable.
"""
import os
import logging
from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

logger = logging.getLogger("irt_cat_engine.database")

DB_DIR = Path(__file__).parent.parent / "db"
DB_DIR.mkdir(exist_ok=True)

DEFAULT_DATABASE_URL = f"sqlite:///{DB_DIR / 'irt_cat.db'}"


def get_database_url() -> str:
    """Get database URL from environment or use default SQLite."""
    db_url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    
    # Handle special case for SQLite file paths
    if db_url.startswith("sqlite:///") and not db_url.startswith("sqlite:////"):
        # Relative path - make it absolute if needed
        if not Path(db_url.replace("sqlite:///", "")).is_absolute():
            db_path = DB_DIR / db_url.replace("sqlite:///./irt_cat_engine/db/", "").replace("sqlite:///", "")
            db_url = f"sqlite:///{db_path}"
    
    logger.info(f"Using database: {db_url.split('@')[-1] if '@' in db_url else db_url}")
    return db_url


class Base(DeclarativeBase):
    pass


# Create engine with environment-based URL
DATABASE_URL = get_database_url()
engine_kwargs = {"echo": False}

# PostgreSQL-specific optimizations
if DATABASE_URL.startswith("postgresql"):
    engine_kwargs.update({
        "pool_pre_ping": True,  # Verify connections before using
        "pool_size": 10,
        "max_overflow": 20,
    })
# SQLite-specific optimizations
elif DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update({
        "connect_args": {
            "check_same_thread": False,  # Allow multi-threading
            "timeout": 30,  # 30 seconds timeout for locks
        },
        "pool_pre_ping": True,  # Check connection health
    })

engine = create_engine(DATABASE_URL, **engine_kwargs)


# Enable WAL mode for SQLite to improve concurrent access
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Configure SQLite for better performance and concurrency."""
    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_conn.cursor()
        # WAL mode allows concurrent reads and writes
        cursor.execute("PRAGMA journal_mode=WAL")
        # NORMAL synchronous mode is faster and still safe with WAL
        cursor.execute("PRAGMA synchronous=NORMAL")
        # Increase cache size for better performance (10MB)
        cursor.execute("PRAGMA cache_size=-10000")
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        logger.debug("SQLite PRAGMA settings applied: WAL mode, NORMAL sync, 10MB cache")


SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db():
    """Create all tables."""
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully")


def get_db() -> Session:
    """Get a database session (for FastAPI dependency injection)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
