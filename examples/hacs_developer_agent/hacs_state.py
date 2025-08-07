"""
HACS Agent State - DeepAgents Pattern

Simplified state management for HACS agents following the DeepAgents pattern.
"""

from langgraph.prebuilt.chat_agent_executor import AgentState
from typing import NotRequired, Annotated, Dict, Any, List
from typing import Literal
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
    """
    HACS Agent State following DeepAgents pattern.
    
    Includes essential HACS admin context while keeping the structure lean.
    """
    
    # Admin task management (similar to todos in DeepAgents)
    admin_tasks: Annotated[NotRequired[List[HACSAdminTask]], admin_task_reducer]
    
    # HACS system status
    system_status: Annotated[NotRequired[HACSSystemStatus], system_status_reducer]
    
    # Current healthcare context (lightweight)
    current_patient_id: NotRequired[str]
    active_clinical_workflow: NotRequired[str]
    
    # Session metadata
    session_actor: NotRequired[str]
    session_role: NotRequired[str]
    audit_trail: NotRequired[List[Dict[str, Any]]]