"""The SPA fallback handler serves index.html for unknown client-side routes so a
refresh of /tripwires boots React, while API/health 404s stay JSON. It must also
preserve headers the original error carried (it overrides the default handler)."""
import asyncio

from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from thumper import main


def _request(path):
    return Request({"type": "http", "method": "GET", "path": path,
                    "query_string": b"", "headers": []})


def test_unknown_client_route_serves_index_html(tmp_path, monkeypatch):
    (tmp_path / "index.html").write_text("<html>thumper-spa-boot</html>")
    monkeypatch.setattr(main, "UI_DIST", tmp_path)

    resp = TestClient(main.app).get("/tripwires")  # a client-side route, no API match

    assert resp.status_code == 200
    assert "thumper-spa-boot" in resp.text


def test_unknown_api_path_stays_json_404(tmp_path, monkeypatch):
    (tmp_path / "index.html").write_text("<html>spa</html>")
    monkeypatch.setattr(main, "UI_DIST", tmp_path)

    resp = TestClient(main.app).get("/api/does-not-exist")

    assert resp.status_code == 404
    assert resp.headers["content-type"].startswith("application/json")
    assert resp.json()["detail"]


def test_handler_preserves_error_headers():
    # A non-SPA error (e.g. 405 with Allow) must keep its headers, which a naive
    # JSONResponse(detail, status) would drop.
    exc = StarletteHTTPException(status_code=405, detail="Method Not Allowed",
                                 headers={"Allow": "POST"})
    resp = asyncio.run(main.spa_fallback_handler(_request("/api/integrations/x/test"), exc))

    assert resp.status_code == 405
    assert resp.headers["allow"] == "POST"
