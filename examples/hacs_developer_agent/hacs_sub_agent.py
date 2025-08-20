"""
Local shim that re-exports the shared subagent builder from hacs_utils.integrations.langgraph.

Kept for backward-compatibility with the example agent.
"""

from typing import List

from hacs_utils.integrations.langgraph.hacs_sub_agent import (
    HACSSubAgent,  # type: ignore F401
    _create_task_tool,  # type: ignore F401
)

__all__: List[str] = [
    "HACSSubAgent",
    "_create_task_tool",
]
