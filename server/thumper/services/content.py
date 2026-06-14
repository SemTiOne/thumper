"""Render the bait body for a tripwire, per its credential source.

source = template -> generate a fresh fake (unique per call, so each endpoint's
                     instance differs).
source = custom   -> the operator's bring-your-own content (future).
source = managed  -> a monitored real credential from the managed service (future).

Alerting is source-independent: whichever body is planted, a READ fires the
tripwire. Source only affects whether a *usage* signal is possible later.
"""
from ..tokens import generate_token


def render_content(*, token_type: str, source: str, custom_content: str | None) -> str:
    if source == "custom":
        if not custom_content:
            raise ValueError("custom source requires custom_content")
        return custom_content
    if source == "managed":
        # Not yet implemented; fall back to a template so the tripwire still alerts.
        return generate_token(token_type)
    return generate_token(token_type)
