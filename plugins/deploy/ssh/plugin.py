"""SSH deploy plugin: run the agent install command on hosts over SSH.

Real and usable for hosts you can reach. Auth uses your local ssh client
(keys / agent), so no secrets are stored here. Each host self-enrolls and pulls
its own unique token instance.

The install command fetches the Bash agent (thumper_agent.sh) from the server
itself, so nothing needs to be pre-present on the host beyond curl + openssl.
"""
import shlex
import subprocess

from thumper.plugins.base import AgentInstall, DeployPlugin, DeployResult, PluginError


class Plugin(DeployPlugin):
    def _hosts(self) -> list[str]:
        return [h.strip() for h in (self.config.get("hosts") or "").split(",") if h.strip()]

    def deploy(self, install: AgentInstall, targets: list[str]) -> DeployResult:
        hosts = targets or self._hosts()
        user = self.config.get("user")
        if not hosts or not user:
            raise PluginError("SSH plugin needs 'hosts' and 'user'.")

        opts = shlex.split(self.config.get("ssh_options", ""))
        ok = 0
        errors: list[str] = []
        for host in hosts:
            # argv list (no shell=True): ssh runs install.command remotely, but
            # nothing is re-parsed by a local shell, so there's no injection via
            # opts/user/host. shlex.split keeps multi-token ssh_options working.
            cmd = ["ssh", *opts, f"{user}@{host}", install.command]
            try:
                proc = subprocess.run(cmd, capture_output=True, timeout=60)
                if proc.returncode == 0:
                    ok += 1
                else:
                    errors.append(f"{host}: {proc.stderr.decode(errors='replace').strip()[:120]}")
            # ssh/subprocess can fail many ways (timeout, missing binary, network);
            # collect and report per-host rather than aborting the whole batch.
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{host}: {exc}")

        state = "deployed" if ok else "failed"
        message = f"Ran agent install on {ok}/{len(hosts)} host(s)."
        if errors:
            message += " Errors: " + "; ".join(errors)
        return DeployResult(state=state, deployed_count=ok, message=message)
