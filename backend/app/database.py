"""SQLAlchemy database engine and session configuration."""

import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings
from app.logging_config import mask_sensitive_url

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""
    pass


def get_engine():
    """Create SQLAlchemy engine with appropriate pooling and dialect settings."""
    settings = get_settings()
    db_url = settings.normalized_database_url

    connect_args = {}
    if "sqlite" in db_url:
        connect_args["check_same_thread"] = False
        engine = create_engine(
            db_url,
            connect_args=connect_args,
            echo=False,
        )
    else:
        # PostgreSQL with psycopg 3
        engine = create_engine(
            db_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False,
        )

    logger.info("Database engine initialized", extra={"extra_fields": {"database_url": mask_sensitive_url(db_url)}})
    return engine


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
