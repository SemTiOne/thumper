"""End-to-end integration tests for the Jamf Pro deploy plugin.

Unlike test_jamf_client.py (which short-circuits httpx with MockTransport),
these run the REAL plugin and REAL JamfClient against a fake Jamf Pro server on
a real socket. That exercises what mocks can't: the OAuth round-trip, the bearer
token actually being attached to every call, our hand-built policy XML being
parsed by a server, real status codes, and httpx encoding over the wire.
"""
import importlib.util
import socket
import threading
import time
from pathlib import Path

import pytest
import uvicorn

from thumper.plugins.base import AgentInstall

from fake_jamf import create_fake_jamf

PLUGIN_FILE = Path(__file__).resolve().parents[1] / "plugins" / "deploy" / "mdm" / "plugin.py"
GOOD_COMMAND = ("curl -fsSL 'https://t/api/install.sh?tripwire=tw1&token=x' "
                "-o /tmp/thumper-install.sh && sudo sh /tmp/thumper-install.sh")


def load_plugin_module():
    spec = importlib.util.spec_from_file_location("thumper_plugin_mdm_integ", PLUGIN_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class RunningServer:
    """Run a FastAPI app on a real loopback socket in a background thread."""

    def __init__(self, app):
        self.port = _free_port()
        self.app = app
        config = uvicorn.Config(app, host="127.0.0.1", port=self.port, log_level="warning")
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self._server.run, daemon=True)

    @property
    def base_url(self):
        return f"http://127.0.0.1:{self.port}"

    def __enter__(self):
        self._thread.start()
        deadline = time.monotonic() + 10
        while not self._server.started:
            if time.monotonic() > deadline:
                raise RuntimeError("fake Jamf server did not start")
            time.sleep(0.02)
        return self

    def __exit__(self, *exc):
        self._server.should_exit = True
        self._thread.join(timeout=10)


def make_config(base_url, smart_group="All Macs"):
    return {"base_url": base_url, "client_id": "cid", "client_secret": "secret",
            "smart_group": smart_group}


def make_install(tripwire_id="tw1"):
    return AgentInstall(tripwire_id=tripwire_id, server_url="https://t",
                        enroll_token="e", command=GOOD_COMMAND)


@pytest.fixture
def plugin_cls():
    return load_plugin_module().Plugin


def test_deploy_end_to_end(plugin_cls):
    app = create_fake_jamf(seed_groups={"All Macs": [{"id": 1}, {"id": 2}, {"id": 3}]})
    with RunningServer(app) as srv:
        plugin = plugin_cls(make_config(srv.base_url))
        result = plugin.deploy(make_install(), [])

    store = app.state.store
    # A real OAuth token was minted and attached (else every call would 401).
    assert store["token_requests"] >= 1
    # One script + one policy were actually created server-side, over the wire.
    assert len(store["scripts"]) == 1
    assert len(store["policies"]) == 1
    script = next(iter(store["scripts"].values()))
    policy = next(iter(store["policies"].values()))
    assert script["name"] == "Thumper Agent - tw1"
    assert "sudo" not in script["scriptContents"]
    assert policy["general"]["name"] == "Thumper Agent - tw1"
    assert policy["script_id"] == script["id"]   # policy references the script we made
    # DeployResult reflects the scoped group's live member count (3).
    assert result.state == "pending"
    assert "3 devices in scope" in result.message


def test_deploy_is_idempotent(plugin_cls):
    app = create_fake_jamf(seed_groups={"All Macs": [{"id": 1}]})
    with RunningServer(app) as srv:
        plugin = plugin_cls(make_config(srv.base_url))
        plugin.deploy(make_install(), [])
        plugin.deploy(make_install(), [])   # same tripwire_id → must UPDATE, not duplicate

    store = app.state.store
    assert len(store["scripts"]) == 1, "re-deploy must update the script in place"
    assert len(store["policies"]) == 1, "re-deploy must update the policy in place"


def test_status_reports_deployed_policy(plugin_cls):
    app = create_fake_jamf(seed_groups={"All Macs": [{"id": 1}, {"id": 2}]})
    with RunningServer(app) as srv:
        plugin = plugin_cls(make_config(srv.base_url))
        plugin.deploy(make_install(), [])
        status = plugin.status([])

    assert len(status) == 1
    entry = next(iter(status.values()))
    assert entry["name"] == "Thumper Agent - tw1"
    assert entry["enabled"] is True
    assert entry["smart_group"] == "All Macs"
    assert entry["scope_count"] == 2


def test_deploy_to_empty_group_does_not_crash(plugin_cls):
    # Empty group → Classic JSON returns "computers": null. The real bug we fixed:
    # this must report 0 in scope, not raise TypeError after creating the policy.
    app = create_fake_jamf(seed_groups={"All Macs": None})
    with RunningServer(app) as srv:
        plugin = plugin_cls(make_config(srv.base_url))
        result = plugin.deploy(make_install(), [])

    assert result.state == "pending"
    assert "0 devices in scope" in result.message
    assert len(app.state.store["policies"]) == 1


def test_redeploy_finds_script_past_first_page(plugin_cls):
    # 150 unrelated scripts already exist, so "Thumper Agent - tw1" (created on the
    # first deploy) lives beyond page 0. A single-page lookup would miss it on the
    # second deploy and create a DUPLICATE. The paginated lookup must find it.
    app = create_fake_jamf(seed_groups={"All Macs": [{"id": 1}]}, filler_scripts=150)
    with RunningServer(app) as srv:
        plugin = plugin_cls(make_config(srv.base_url))
        plugin.deploy(make_install(), [])
        plugin.deploy(make_install(), [])

    thumper_scripts = [s for s in app.state.store["scripts"].values()
                       if s["name"] == "Thumper Agent - tw1"]
    assert len(thumper_scripts) == 1, "must update the existing script, not duplicate it"


def test_wrong_credentials_surface_as_plugin_error(plugin_cls):
    # Real auth round-trip: bad secret → 401 from /api/oauth/token → PluginError.
    from thumper.plugins.base import PluginError
    app = create_fake_jamf(seed_groups={"All Macs": [{"id": 1}]})
    with RunningServer(app) as srv:
        config = make_config(srv.base_url)
        config["client_secret"] = "wrong"
        plugin = plugin_cls(config)
        with pytest.raises(PluginError):
            plugin.deploy(make_install(), [])
