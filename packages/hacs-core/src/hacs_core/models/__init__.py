"""
Backward-compatibility facade for healthcare models.

This module re-exports public healthcare model types from `hacs_models` so that
legacy imports like `from hacs_core.models import Patient` continue to work.

New code should import from `hacs_models` directly.
"""

from hacs_models import *  # noqa: F401,F403

try:
    # Mirror public API for introspection tools
    __all__ = list(
        getattr(__import__("hacs_models", fromlist=["__all__"]), "__all__", [])
    )
except Exception:  # pragma: no cover - best-effort compatibility
    __all__ = []
