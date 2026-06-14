import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from thumper import store
from thumper.db import Base, get_db
from thumper.main import app


@pytest.fixture
def client():
    engine = create_engine("sqlite://", echo=False,
                           connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app), db
    del app.dependency_overrides[get_db]
    db.close()


def test_deliveries_endpoint_returns_recorded_attempts(client):
    tc, db = client
    store.record_delivery(db, alert_id="al_1", plugin="webhook", status="ok", error=None)
    store.record_delivery(db, alert_id="al_1", plugin="splunk", status="failed",
                          error="connection refused")

    resp = tc.get("/api/alerts/al_1/deliveries")
    assert resp.status_code == 200
    body = resp.json()
    assert {d["plugin"]: d["status"] for d in body} == {"webhook": "ok", "splunk": "failed"}
    failed = next(d for d in body if d["plugin"] == "splunk")
    assert failed["error"] == "connection refused"
    assert failed["alert_id"] == "al_1"


def test_deliveries_endpoint_empty_for_unknown_alert(client):
    tc, _ = client
    resp = tc.get("/api/alerts/nope/deliveries")
    assert resp.status_code == 200
    assert resp.json() == []
