"""
Common Integration Utilities

Shared utilities and patterns used across all HACS integrations to eliminate
code duplication and ensure consistent behavior.
"""

from .tool_loader import (
    get_availability,
    get_all_hacs_tools,
    get_all_hacs_tools_sync,
    load_hacs_tools,
    load_hacs_tools_sync,
)

__all__ = [
    "get_availability",
    "get_all_hacs_tools",
    "get_all_hacs_tools_sync",
    "load_hacs_tools",
    "load_hacs_tools_sync",
]
