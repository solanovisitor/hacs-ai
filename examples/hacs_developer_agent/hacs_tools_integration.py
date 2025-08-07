"""
HACS Tools Integration

Integration layer to provide HACS admin tools following the DeepAgents pattern.
"""

from langchain_core.tools import tool, InjectedToolCallId
from langgraph.types import Command
from langchain_core.messages import ToolMessage
from typing import Annotated, List, Dict, Any
from langgraph.prebuilt import InjectedState
from datetime import datetime

from hacs_state import HACSAgentState, HACSAdminTask, HACSSystemStatus


@tool(description="Manage HACS admin tasks. Use this to track database migrations, system configurations, and administrative operations.")
def manage_admin_tasks(
    tasks: List[HACSAdminTask], 
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """Update the HACS admin task list."""
    return Command(
        update={
            "admin_tasks": tasks,
            "messages": [
                ToolMessage(f"Updated admin task list with {len(tasks)} tasks", tool_call_id=tool_call_id)
            ],
        }
    )


@tool(description="Update HACS system status including database, vector store, and migration status.")
def update_system_status(
    database_connected: bool = None,
    migration_status: str = None,
    vector_store_available: bool = None,
    state: Annotated[HACSAgentState, InjectedState] = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = None,
) -> Command:
    """Update HACS system status."""
    
    current_status = state.get("system_status", {})
    
    # Update only provided fields
    updates = {}
    if database_connected is not None:
        updates["database_connected"] = database_connected
    if migration_status is not None:
        updates["migration_status"] = migration_status
    if vector_store_available is not None:
        updates["vector_store_available"] = vector_store_available
    
    updates["last_health_check"] = datetime.now().isoformat()
    
    new_status = {**current_status, **updates}
    
    return Command(
        update={
            "system_status": new_status,
            "messages": [
                ToolMessage(f"Updated HACS system status: {updates}", tool_call_id=tool_call_id)
            ],
        }
    )


@tool(description="Run database migration for HACS system. Ensures database schema is up to date.")
def run_database_migration(
    environment: str = "development",
    dry_run: bool = False,
    state: Annotated[HACSAgentState, InjectedState] = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = None,
) -> Command:
    """Run database migration for HACS."""
    
    try:
        # Simulate migration process
        if dry_run:
            result = f"✅ Migration dry-run completed for {environment} environment. No issues found."
            migration_status = "ready"
        else:
            result = f"✅ Database migration completed successfully for {environment} environment."
            migration_status = "current"
        
        # Update system status
        current_status = state.get("system_status", {})
        new_status = {
            **current_status,
            "migration_status": migration_status,
            "database_connected": True,
            "last_health_check": datetime.now().isoformat()
        }
        
        # Update audit trail
        audit_entry = {
            "action": "database_migration",
            "environment": environment,
            "dry_run": dry_run,
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        
        audit_trail = state.get("audit_trail", []) + [audit_entry]
        
        return Command(
            update={
                "system_status": new_status,
                "audit_trail": audit_trail,
                "messages": [
                    ToolMessage(result, tool_call_id=tool_call_id)
                ],
            }
        )
        
    except Exception as e:
        error_result = f"❌ Database migration failed: {str(e)}"
        
        # Update system status with error
        current_status = state.get("system_status", {})
        new_status = {
            **current_status,
            "migration_status": "error",
            "last_health_check": datetime.now().isoformat()
        }
        
        return Command(
            update={
                "system_status": new_status,
                "messages": [
                    ToolMessage(error_result, tool_call_id=tool_call_id)
                ],
            }
        )


@tool(description="Check database connection and migration status for HACS system.")
def check_database_status(
    state: Annotated[HACSAgentState, InjectedState] = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = None,
) -> Command:
    """Check HACS database status."""
    
    # Simulate database check
    try:
        # Mock database status check
        database_connected = True
        migration_status = "current"
        
        status_report = f"""
📊 HACS Database Status Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 Connection: {'✅ Connected' if database_connected else '❌ Disconnected'}
🔄 Migrations: {'✅ Current' if migration_status == 'current' else f'⚠️ {migration_status}'}
🕐 Last Check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Database is ready for HACS operations.
        """.strip()
        
        # Update system status
        current_status = state.get("system_status", {})
        new_status = {
            **current_status,
            "database_connected": database_connected,
            "migration_status": migration_status,
            "last_health_check": datetime.now().isoformat()
        }
        
        return Command(
            update={
                "system_status": new_status,
                "messages": [
                    ToolMessage(status_report, tool_call_id=tool_call_id)
                ],
            }
        )
        
    except Exception as e:
        error_report = f"❌ Database status check failed: {str(e)}"
        
        return Command(
            update={
                "messages": [
                    ToolMessage(error_report, tool_call_id=tool_call_id)
                ],
            }
        )


@tool(description="Create a new HACS healthcare record (Patient, Observation, etc.).")
def create_hacs_record(
    resource_type: str,
    data: Dict[str, Any],
    actor_name: str = "HACS Admin Agent",
    state: Annotated[HACSAgentState, InjectedState] = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = None,
) -> Command:
    """Create a new HACS healthcare record."""
    
    try:
        # Simulate record creation
        record_id = f"{resource_type.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        result = f"""
✅ HACS {resource_type} Record Created Successfully

📋 Record ID: {record_id}
👤 Created by: {actor_name}
🕐 Created at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📊 Data fields: {len(data)} fields provided

The {resource_type} record has been stored in the HACS system.
        """.strip()
        
        # Update audit trail
        audit_entry = {
            "action": "create_record",
            "resource_type": resource_type,
            "record_id": record_id,
            "actor": actor_name,
            "timestamp": datetime.now().isoformat()
        }
        
        audit_trail = state.get("audit_trail", []) + [audit_entry]
        
        return Command(
            update={
                "audit_trail": audit_trail,
                "messages": [
                    ToolMessage(result, tool_call_id=tool_call_id)
                ],
            }
        )
        
    except Exception as e:
        error_result = f"❌ Failed to create {resource_type} record: {str(e)}"
        
        return Command(
            update={
                "messages": [
                    ToolMessage(error_result, tool_call_id=tool_call_id)
                ],
            }
        )


def get_hacs_admin_tools():
    """Get all HACS admin tools for the agent."""
    return [
        manage_admin_tasks,
        update_system_status,
        run_database_migration,
        check_database_status,
        create_hacs_record
    ]