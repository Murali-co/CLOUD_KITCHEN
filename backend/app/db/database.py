import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app.core.config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy 2.x Engine with connection pool
# Note: In SQLite (e.g. for testing), pool parameters differ from MySQL
is_sqlite = settings.DATABASE_URL.startswith("sqlite")

engine_kwargs = {
    "echo": False,
    "pool_pre_ping": True,
}

if not is_sqlite:
    engine_kwargs.update({
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
        "pool_recycle": settings.DB_POOL_RECYCLE,
    })

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

# Reusable SessionLocal factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)

from app.models.base import Base


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a transactional SQLAlchemy database session.
    Automatically rolls back uncommitted changes on unhandled exceptions and closes session.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"Database session error encountered: {e}")
        raise
    finally:
        db.close()


def check_db_connectivity() -> dict:
    """
    Performs a lightweight query (SELECT 1) to evaluate database connectivity.
    Returns status dict with boolean flag and diagnostic message.
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            scalar = result.scalar()
            if scalar == 1:
                return {"status": "connected", "available": True, "detail": "MySQL server reachable"}
            return {"status": "degraded", "available": False, "detail": "Unexpected query result"}
    except OperationalError as oe:
        logger.warning(f"Database connection offline: {oe.orig if hasattr(oe, 'orig') else oe}")
        return {"status": "disconnected", "available": False, "detail": "Database server offline or unreachable"}
    except SQLAlchemyError as se:
        logger.warning(f"Database error: {se}")
        return {"status": "error", "available": False, "detail": str(se)}
    except Exception as ex:
        logger.warning(f"Unexpected error checking DB: {ex}")
        return {"status": "error", "available": False, "detail": "Connection failed"}
