from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

os.environ["WEIRD_DEMO_MODE"] = "true"
os.environ["WEIRD_LLM_PROVIDER"] = "mock"
os.environ["WEIRD_ADMIN_TOKEN"] = "test-admin"
os.environ["WEIRD_EXPLORE_SOURCES"] = "false"
os.environ["WEIRD_USE_PGVECTOR"] = "false"
os.environ["WEIRD_EMBEDDING_BACKEND"] = "hashed"


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "weird.db"


@pytest.fixture()
def session(db_path: Path) -> Generator[Session, None, None]:
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    from weird.config import get_settings
    from weird.db import get_session_factory, init_db, reset_engine

    get_settings.cache_clear()
    reset_engine()
    init_db()
    factory = get_session_factory()
    db = factory()
    from weird.seed import seed

    seed(db)
    db.commit()
    try:
        yield db
    finally:
        db.close()
        reset_engine()
        get_settings.cache_clear()


@pytest.fixture()
def client(session: Session) -> Generator[TestClient, None, None]:
    from weird.api import app
    from weird.db import get_db

    def _override():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
