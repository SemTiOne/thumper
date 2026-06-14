"""Shared test fixtures."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from thumper.db import Base, get_db
from thumper.main import app


@pytest.fixture
def client_db():
    """A TestClient wired to a fresh in-memory SQLite session, yielded together
    so tests can both drive the API and seed/inspect the same session."""
    engine = create_engine("sqlite://", echo=False,
                           connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app), db
    del app.dependency_overrides[get_db]
    db.close()
