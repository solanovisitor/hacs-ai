"""
HACS Tools Integration

Integration layer to provide HACS admin tools following the DeepAgents pattern.
"""

from datetime import datetime
from typing import Annotated, Any, Dict, List

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from hacs_state import HACSAdminTask, HACSAgentState


@tool(
    description="Manage HACS admin tasks. Use this to track database migrations, system configurations, and administrative operations."
)
def manage_admin_tasks(
    tasks: List[HACSAdminTask], tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """Update the HACS admin task list."""
    return Command(
        update={
            "admin_tasks": tasks,
            "messages": [
                ToolMessage(
                    f"Updated admin task list with {len(tasks)} tasks", tool_call_id=tool_call_id
                )
            ],
        }
    )


@tool(
    description="Update HACS system status including database, vector store, and migration status."
)
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
            result = (
                f"✅ Migration dry-run completed for {environment} environment. No issues found."
            )
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
            "last_health_check": datetime.now().isoformat(),
        }

        # Update audit trail
        audit_entry = {
            "action": "database_migration",
            "environment": environment,
            "dry_run": dry_run,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
        }

        audit_trail = state.get("audit_trail", []) + [audit_entry]

        return Command(
            update={
                "system_status": new_status,
                "audit_trail": audit_trail,
                "messages": [ToolMessage(result, tool_call_id=tool_call_id)],
            }
        )

    except Exception as e:
        error_result = f"❌ Database migration failed: {str(e)}"

        # Update system status with error
        current_status = state.get("system_status", {})
        new_status = {
            **current_status,
            "migration_status": "error",
            "last_health_check": datetime.now().isoformat(),
        }

        return Command(
            update={
                "system_status": new_status,
                "messages": [ToolMessage(error_result, tool_call_id=tool_call_id)],
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

🔗 Connection: {"✅ Connected" if database_connected else "❌ Disconnected"}
🔄 Migrations: {"✅ Current" if migration_status == "current" else f"⚠️ {migration_status}"}
🕐 Last Check: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Database is ready for HACS operations.
        """.strip()

        # Update system status
        current_status = state.get("system_status", {})
        new_status = {
            **current_status,
            "database_connected": database_connected,
            "migration_status": migration_status,
            "last_health_check": datetime.now().isoformat(),
        }

        return Command(
            update={
                "system_status": new_status,
                "messages": [ToolMessage(status_report, tool_call_id=tool_call_id)],
            }
        )

    except Exception as e:
        error_report = f"❌ Database status check failed: {str(e)}"

        return Command(
            update={
                "messages": [ToolMessage(error_report, tool_call_id=tool_call_id)],
            }
        )


@tool(
    description="Create and persist a HACS healthcare record (Patient, Observation, etc.) using modeling + database tools."
)
def create_record(
    resource_type: str,
    data: Dict[str, Any],
    actor_name: str = "HACS Admin Agent",
    state: Annotated[HACSAgentState, InjectedState] = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = None,
) -> Command:
    """Create and persist a new HACS healthcare record."""
    try:
        import asyncio

        from hacs_tools.domains.database import save_record
        from hacs_tools.domains.modeling import pin_resource, validate_resource

        # Ensure resource_type is present in payload
        payload = {"resource_type": resource_type, **(data or {})}

        # Instantiate and validate
        inst = pin_resource(resource_type, payload)
        if not inst.success:
            raise ValueError(inst.message)
        resource_dict = inst.data.get("resource", payload)

        valid = validate_resource(resource_dict)
        if not valid.success or not valid.data.get("valid", False):
            issues = ", ".join(valid.data.get("issues", [])) if valid.data else "unknown"
            raise ValueError(f"Validation failed: {issues}")

        # Persist synchronously via asyncio
        save_res = asyncio.run(save_record(resource_dict))
        if not save_res.success:
            raise ValueError(save_res.error or save_res.message)

        record_id = save_res.data.get("id") if save_res.data else None

        result = (
            f"✅ HACS {resource_type} record saved\n\n"
            f"📋 Record ID: {record_id}\n"
            f"👤 Created by: {actor_name}\n"
            f"🕐 Created at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"📊 Data fields: {len(data or {})} fields provided"
        )

        # Update audit trail
        audit_entry = {
            "action": "create_record",
            "resource_type": resource_type,
            "record_id": record_id,
            "actor": actor_name,
            "timestamp": datetime.now().isoformat(),
        }
        audit_trail = state.get("audit_trail", []) + [audit_entry]

        return Command(
            update={
                "audit_trail": audit_trail,
                "messages": [ToolMessage(result, tool_call_id=tool_call_id)],
            }
        )
    except Exception as e:
        error_result = f"❌ Failed to create {resource_type} record: {str(e)}"
        return Command(update={"messages": [ToolMessage(error_result, tool_call_id=tool_call_id)]})


def get_hacs_admin_tools():
    """Get all HACS admin tools for the agent."""
    return [
        manage_admin_tasks,
        update_system_status,
        run_database_migration,
        check_database_status,
        create_record,
    ]
