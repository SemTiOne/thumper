"""Helpers for reading/merging integration config and masking secrets."""
import json

from sqlalchemy.orm import Session

from .. import store
from ..plugins.registry import get_manifest


def mask_config(manifest: dict, config: dict) -> dict:
    """Echo non-secret config back for display; replace secrets with bullets."""
    masked: dict = {}
    for field in manifest.get("config_schema", []):
        value = config.get(field["key"])
        if value in (None, ""):
            continue
        masked[field["key"]] = "••••••••" if field["type"] == "secret" else value
    return masked


def saved_config(db: Session, plugin: str) -> dict:
    row = store.get_integration(db, plugin)
    return json.loads(row.config_json) if row else {}


def merge_config(existing: dict, incoming: dict) -> dict:
    """Apply non-empty incoming values over existing. Blank secret fields left
    untouched so re-saving a form without re-typing secrets doesn't wipe them."""
    return {**existing, **{k: v for k, v in incoming.items() if v not in (None, "")}}
