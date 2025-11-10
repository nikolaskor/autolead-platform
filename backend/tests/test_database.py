"""
Database connection tests.

Tests basic database connectivity and session management.
"""
import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.core.database import engine, SessionLocal, check_database_connection


def test_database_connection():
    """Test that database connection works."""
    assert check_database_connection() is True


def test_session_creation():
    """Test that database sessions can be created."""
    db = SessionLocal()
    try:
        assert db is not None
    finally:
        db.close()


def test_basic_query():
    """Test basic SQL query execution."""
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT 1 as test"))
        row = result.fetchone()
        assert row[0] == 1
    finally:
        db.close()


def test_database_url_configured():
    """Test that database URL is properly configured."""
    from app.core.config import settings
    assert settings.DATABASE_URL is not None
    parsed = make_url(settings.DATABASE_URL)
    assert parsed.drivername.startswith("postgresql")

