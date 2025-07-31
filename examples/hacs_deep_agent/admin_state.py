"""
HACS Admin Agent State

Simplified state management for admin operations, focusing on administrative
context rather than complex clinical workflows.
"""

from typing import Dict, List, Any, Optional
from typing_extensions import TypedDict
from datetime import datetime


class AdminAgentState(TypedDict):
    """
    Lean state for HACS Admin Agent focused on administrative operations.
    
    This replaces the complex clinical state with admin-specific context.
    """
    
    # Core LangGraph state (required)
    messages: List[Dict[str, Any]]
    remaining_steps: int
    
    # Admin context (essential)
    current_actor: Optional[Dict[str, Any]]  # Admin actor performing operations
    
    # Task management (lightweight)
    pending_tasks: List[Dict[str, Any]]      # Admin tasks to complete
    completed_tasks: List[Dict[str, Any]]    # Completed admin actions
    
    # System state (essential)
    active_systems: Dict[str, Any]           # Active HACS systems and services
    database_status: Dict[str, Any]          # Database connectivity and health
    
    # Audit and security (required for admin)
    audit_trail: List[Dict[str, Any]]        # Administrative action audit log
    session_context: Dict[str, Any]          # Current admin session context


def create_admin_state(
    actor_name: str = "HACS Admin Agent",
    actor_role: str = "admin"
) -> AdminAgentState:
    """
    Create initial admin agent state with minimal required context.
    
    Args:
        actor_name: Name of the admin actor
        actor_role: Role of the admin actor
        
    Returns:
        Initialized AdminAgentState
    """
    from hacs_core.actor import Actor
    
    admin_actor = Actor(name=actor_name, role=actor_role)
    
    return AdminAgentState(
        messages=[],
        remaining_steps=10,
        current_actor=admin_actor.model_dump(),
        pending_tasks=[],
        completed_tasks=[],
        active_systems={
            "database": {"status": "unknown", "last_check": None},
            "vector_store": {"status": "unknown", "last_check": None},
            "services": {"status": "unknown", "count": 0}
        },
        database_status={
            "connected": False,
            "migrations_current": None,
            "schema_version": None,
            "last_health_check": None
        },
        audit_trail=[{
            "action": "admin_session_started",
            "actor": actor_name,
            "timestamp": datetime.now().isoformat(),
            "details": "HACS Admin Agent session initialized"
        }],
        session_context={
            "session_id": f"admin_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "started": datetime.now().isoformat(),
            "actor": admin_actor.model_dump(),
            "permissions": ["admin:*"],  # Would be set based on actual actor permissions
            "environment": "development"  # Could be: development, staging, production
        }
    )


def add_admin_task(state: AdminAgentState, task: Dict[str, Any]) -> AdminAgentState:
    """
    Add a new admin task to the state.
    
    Args:
        state: Current admin state
        task: Task to add
        
    Returns:
        Updated state
    """
    task_with_metadata = {
        **task,
        "id": f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
        "created": datetime.now().isoformat(),
        "status": "pending"
    }
    
    state["pending_tasks"].append(task_with_metadata)
    return state


def complete_admin_task(
    state: AdminAgentState, 
    task_id: str, 
    result: Dict[str, Any]
) -> AdminAgentState:
    """
    Mark an admin task as completed and move it to completed tasks.
    
    Args:
        state: Current admin state
        task_id: ID of the task to complete
        result: Task completion result
        
    Returns:
        Updated state
    """
    # Find and remove from pending
    task_to_complete = None
    for i, task in enumerate(state["pending_tasks"]):
        if task["id"] == task_id:
            task_to_complete = state["pending_tasks"].pop(i)
            break
    
    if task_to_complete:
        completed_task = {
            **task_to_complete,
            "status": "completed",
            "completed": datetime.now().isoformat(),
            "result": result
        }
        state["completed_tasks"].append(completed_task)
        
        # Add to audit trail
        state["audit_trail"].append({
            "action": "task_completed",
            "task_id": task_id,
            "actor": state["current_actor"]["name"],
            "timestamp": datetime.now().isoformat(),
            "result": result
        })
    
    return state


def update_system_status(
    state: AdminAgentState,
    system: str,
    status: Dict[str, Any]
) -> AdminAgentState:
    """
    Update the status of a system in the admin state.
    
    Args:
        state: Current admin state
        system: Name of the system (e.g., "database", "vector_store")
        status: Status information to update
        
    Returns:
        Updated state
    """
    if system in state["active_systems"]:
        state["active_systems"][system].update(status)
        state["active_systems"][system]["last_updated"] = datetime.now().isoformat()
    else:
        state["active_systems"][system] = {
            **status,
            "last_updated": datetime.now().isoformat()
        }
    
    # Add to audit trail for significant system changes
    if status.get("status") in ["error", "critical", "offline"]:
        state["audit_trail"].append({
            "action": "system_status_change",
            "system": system,
            "status": status,
            "actor": state["current_actor"]["name"],
            "timestamp": datetime.now().isoformat()
        })
    
    return state


def add_audit_entry(
    state: AdminAgentState,
    action: str,
    details: Dict[str, Any] = None
) -> AdminAgentState:
    """
    Add an entry to the audit trail.
    
    Args:
        state: Current admin state
        action: Action being audited
        details: Additional details about the action
        
    Returns:
        Updated state
    """
    audit_entry = {
        "action": action,
        "actor": state["current_actor"]["name"],
        "timestamp": datetime.now().isoformat(),
        "session_id": state["session_context"]["session_id"]
    }
    
    if details:
        audit_entry["details"] = details
    
    state["audit_trail"].append(audit_entry)
    return state 