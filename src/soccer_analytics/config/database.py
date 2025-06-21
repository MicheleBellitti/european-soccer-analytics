"""Database configuration and session management."""

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .settings import settings

logger = logging.getLogger(__name__)

# Base class for all ORM models
Base = declarative_base()

# Database engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance (if using SQLite)."""
    if "sqlite" in settings.database_url:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def create_test_engine(database_url: str):
    """Create a test database engine."""
    return create_engine(
        database_url,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
    )


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Provide a transactional scope around a series of operations.
    
    Yields:
        Session: SQLAlchemy session
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    Used primarily for FastAPI-style dependency injection.
    
    Yields:
        Session: SQLAlchemy session
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    """Initialize the database by creating all tables."""
    try:
        # Import all models to ensure they are registered with Base
        from soccer_analytics.data_models.models import (
            League, Team, Player, Match, PlayerStats, TeamStats
        )
        
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def drop_db() -> None:
    """Drop all database tables. Use with caution!"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise


def check_db_connection() -> bool:
    """
    Check if database connection is working.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        from sqlalchemy import text
        with get_db_session() as session:
            session.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False