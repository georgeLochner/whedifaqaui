"""Shared test fixtures."""

import io
import uuid
from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app
from app.models.video import Video

# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------

# Use a separate test database schema within the same PostgreSQL instance.
# Each test runs inside a transaction that is rolled back, keeping tests isolated.

_test_engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

TestSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=_test_engine
)


@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    """Create all tables once per test session."""
    Base.metadata.create_all(bind=_test_engine)
    yield
    # Tables are left in place; the test DB is ephemeral anyway.


@pytest.fixture()
def db():
    """Provide a transactional database session that rolls back after each test."""
    connection = _test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)

    # Start a SAVEPOINT so the application code can call commit() without
    # actually committing to the outer transaction.
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        nonlocal nested
        if trans.nested and not trans._parent.nested:
            nested = connection.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db: Session):
    """FastAPI TestClient with the DB dependency overridden to use the test session."""

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# File / storage fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_mkv_file():
    """Return an in-memory file-like object that mimics a .mkv upload."""
    content = b"\x1a\x45\xdf\xa3" + b"\x00" * 100  # EBML header magic bytes
    return ("test_video.mkv", io.BytesIO(content), "video/x-matroska")


@pytest.fixture()
def tmp_video_dir(tmp_path: Path, monkeypatch):
    """Override VIDEO_STORAGE_PATH to a temporary directory for tests."""
    monkeypatch.setattr(settings, "VIDEO_STORAGE_PATH", str(tmp_path))
    return tmp_path


# ---------------------------------------------------------------------------
# Model helpers
# ---------------------------------------------------------------------------


@pytest.fixture()
def make_video(db: Session):
    """Factory fixture to create Video records in the test DB."""

    def _make(
        *,
        title: str = "Test Video",
        recording_date: date | None = None,
        participants: list[str] | None = None,
        status: str = "uploaded",
        error_message: str | None = None,
    ) -> Video:
        video = Video(
            id=uuid.uuid4(),
            title=title,
            file_path="/data/videos/original/fake.mkv",
            recording_date=recording_date or date(2024, 1, 15),
            participants=participants,
            status=status,
            error_message=error_message,
        )
        db.add(video)
        db.flush()
        return video

    return _make
