"""Plugin framework: base classes + loader. The actual plugins live in the
repo-root plugins/ tree (config.PLUGINS_DIR), one directory each.
"""
from .base import AgentInstall, AlertPlugin, DeployPlugin, DeployResult, PluginError

__all__ = ["AgentInstall", "AlertPlugin", "DeployPlugin", "DeployResult", "PluginError"]
