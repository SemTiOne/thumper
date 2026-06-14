"""The /api/trigger route must schedule deliver_alert as a background task."""
from thumper import store
from thumper.api import routes
from thumper.db import Deployment
from thumper.services.signing import sign


def _insert_deployment(db, *, did, secret, path):
    db.add(Deployment(id=did, tripwire_id="tw_1", endpoint_id="ep_1", path=path,
                      content="bait-body", hmac_secret=secret, state="planted",
                      created_at="2026-01-01T00:00:00Z"))
    db.commit()


def test_trigger_schedules_deliver_alert_with_signed_event(client_db, monkeypatch):
    tc, db = client_db
    secret = "s3cr3t"
    _insert_deployment(db, did="dep_1", secret=secret, path="/home/u/.aws/credentials")

    captured = {}
    monkeypatch.setattr(routes, "deliver_alert", lambda event: captured.update(event))

    body = b"deployment_id=dep_1\nprocess=cat\nos_user=alice\nevent_type=openat\n"
    resp = tc.post("/api/trigger", content=body,
                   headers={"X-Thumper-Signature": sign(secret, body)})

    assert resp.status_code == 200
    alert_id = resp.json()["alert_id"]
    assert captured.get("alert_id") == alert_id
    assert captured.get("process") == "cat"
    assert captured.get("os_user") == "alice"
    assert captured.get("accessed_path") == "/home/u/.aws/credentials"


def test_trigger_bad_signature_schedules_nothing(client_db, monkeypatch):
    tc, db = client_db
    _insert_deployment(db, did="dep_1", secret="right-secret", path="/x")

    calls = []
    monkeypatch.setattr(routes, "deliver_alert", lambda event: calls.append(event))

    body = b"deployment_id=dep_1\nprocess=cat\n"
    resp = tc.post("/api/trigger", content=body,
                   headers={"X-Thumper-Signature": sign("wrong-secret", body)})

    assert resp.status_code == 401
    assert calls == []
