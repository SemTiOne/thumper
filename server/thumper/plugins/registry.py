"""Convenience re-exports so callers import a stable `registry` surface. The
loader caches discovery + module loading behind these names.
"""
from .loader import (
    discover_manifests,
    get_manifest,
    load_plugin,
    public_manifests,
    reset_cache,
)

__all__ = ["discover_manifests", "get_manifest", "load_plugin", "public_manifests",
           "reset_cache"]
