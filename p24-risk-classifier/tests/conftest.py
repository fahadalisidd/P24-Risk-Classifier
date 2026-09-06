"""Pytest fixtures and test configuration."""
import pytest
from datetime import datetime, timezone, timedelta
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.clock import ControllableClock, set_global_clock, SystemClock
from app.db.base import Base
from app.db.session import get_db
from app.domain.enums import RuleAction
from app.domain.models import RiskRuleModel, PolicyPinModel, PolicyOverrideModel
from app.main import app


# In-memory SQLite engine for fast, isolated tests
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create fresh schema for each test function."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def test_clock() -> Generator[ControllableClock, None, None]:
    """Provide a controllable test clock pinned to 2026-08-25 12:00:00 UTC."""
    mock_clock = ControllableClock(datetime(2026, 8, 25, 12, 0, 0, tzinfo=timezone.utc))
    set_global_clock(mock_clock)
    yield mock_clock
    set_global_clock(SystemClock())


@pytest.fixture(scope="function")
def client(db_session: Session, test_clock: ControllableClock) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with overridden get_db and test clock."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
