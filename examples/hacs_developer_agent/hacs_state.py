"""
HACS Agent State - DeepAgents Pattern

Simplified state management for HACS agents following the DeepAgents pattern.
"""

from typing import Annotated, Any, Dict, List, Literal, NotRequired

from langgraph.prebuilt.chat_agent_executor import AgentState
from typing_extensions import TypedDict


class HACSAdminTask(TypedDict):
    """Admin task to track for HACS operations."""

    content: str
    status: Literal["pending", "in_progress", "completed"]
    priority: Literal["low", "normal", "high", "critical"]
    assigned_specialist: str  # Which HACS subagent handles this


class HACSSystemStatus(TypedDict):
    """HACS system status tracking."""

    database_connected: bool
    migration_status: str
    vector_store_available: bool
    last_health_check: str


def admin_task_reducer(left, right):
    """Reducer for admin tasks."""
    if left is None:
        return right
    elif right is None:
        return left
    else:
        # Merge task lists, avoiding duplicates by task content
        existing_contents = {task["content"] for task in left}
        new_tasks = [task for task in right if task["content"] not in existing_contents]
        return left + new_tasks


def system_status_reducer(left, right):
    """Reducer for system status."""
    if left is None:
        return right
    elif right is None:
        return left
    else:
        return {**left, **right}


class HACSAgentState(AgentState):
    """DeepAgents-style state with HACS extensions."""

    # Core deep agent fields
    todos: NotRequired[List[Dict[str, Any]]]

    def files_reducer(
        left: Dict[str, str] | None, right: Dict[str, str] | None
    ) -> Dict[str, str] | None:
        if left is None:
            return right
        if right is None:
            return left
        return {**left, **right}

    files: Annotated[NotRequired[Dict[str, str]], files_reducer]

    # HACS extensions
    admin_tasks: Annotated[NotRequired[List[HACSAdminTask]], admin_task_reducer]
    system_status: Annotated[NotRequired[HACSSystemStatus], system_status_reducer]
    current_patient_id: NotRequired[str]
    active_clinical_workflow: NotRequired[str]
    session_actor: NotRequired[str]
    session_role: NotRequired[str]
    audit_trail: NotRequired[List[Dict[str, Any]]]
