"""HACS Deep Agent Tools.

Adapted from the deep agents framework for HACS admin operations.
Includes planning tools, file system tools, and HACS-specific admin tools.
"""

from typing import Annotated, List, Optional

from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool, StructuredTool, InjectedToolArg, InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from state import AdminOperationResult, HACSDeepAgentState, Todo

# Import real HACS admin tools
from tools import (
    check_hacs_migration_status,
    describe_hacs_database_schema,
    discover_hacs_resources,
    run_hacs_database_migration,
)


# ============================================================================
# PLANNING TOOLS (adapted for HACS admin)
# ============================================================================

@tool
def write_todos(
    todos: List[Todo],
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """Use this tool to create and manage a structured task list for 
your current HACS admin work session.

This helps you track progress, organize complex admin operations, and demonstrate thoroughness."""
    return Command(
        update={
            "todos": todos,
            "messages": [
                ToolMessage(
                    f"Updated admin task list: {len(todos)} tasks", 
                    tool_call_id=tool_call_id
                )
            ],
        }
    )




# ============================================================================
# FILE SYSTEM TOOLS (adapted for HACS admin)
# ============================================================================

def ls(state: Annotated[HACSDeepAgentState, InjectedState]) -> List[str]:
    """List all files in the admin workspace."""
    return list(state.get("files", {}).keys())


@tool
def read_file(
    file_path: str,
    state: Annotated[HACSDeepAgentState, InjectedState],
    offset: int = 0,
    limit: int = 2000,
) -> str:
    """Read admin configuration files, scripts, or documentation.

Perfect for:
- Database configuration files
- Migration scripts
- Admin documentation
- Environment files
- Log files
- Schema definitions"""
    files = state.get("files", {})
    if file_path not in files:
        return f"Error: Admin file '{file_path}' not found"

    content = files[file_path]
    if not content or content.strip() == "":
        return "File exists but has empty contents"

    if offset or limit != 2000:
        # Handle offset and limit for large files
        lines = content.split('\n')
        selected_lines = lines[offset:offset + limit] if limit > 0 else lines[offset:]
        return '\n'.join(selected_lines)

    return content


@tool
def write_file(
    file_path: str,
    content: str,
    state: Annotated[HACSDeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Write admin configuration files, scripts, or documentation to the workspace.

Perfect for creating:
- Database configuration files
- Migration scripts
- Admin procedures and runbooks
- Environment setup files
- System documentation
- Deployment scripts"""
    # Get existing files and add the new one
    files = state.get("files", {}).copy() if state.get("files") else {}
    files[file_path] = content
    return Command(
        update={
            "files": files,
            "messages": [
                ToolMessage(
                    f"Updated file {file_path}",
                    tool_call_id=tool_call_id
                )
            ],
        }
    )


async def _edit_file(
    file_path: str,
    content: str,
    state: Annotated[HACSDeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Edit existing admin file content."""
    files = state.get("files", {})

    if file_path not in files:
        # File doesn't exist, create it
        action = "Created new"
    else:
        action = "Updated"

    return Command(
        update={
            "files": {file_path: content},
            "messages": [
                ToolMessage(
                    f"{action} admin file: {file_path} ({len(content)} chars)", 
                    tool_call_id=tool_call_id
                )
            ],
        }
    )

edit_file = StructuredTool.from_function(
    _edit_file,
    name="edit_file",
    description="""Edit existing admin configuration files, scripts, or 
documentation.

Useful for:
- Updating database connection strings
- Modifying migration scripts
- Updating admin procedures
- Editing configuration files
- Updating documentation""",
    coroutine=_edit_file
)


# ============================================================================
# HACS ADMIN OPERATION TOOLS
# ============================================================================

async def _admin_database_migration(
    database_url: Optional[str] = None,
    force_migration: bool = False,
    state: Annotated[HACSDeepAgentState, InjectedState] = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = None,
    config: Annotated[RunnableConfig, InjectedToolArg] = None,
) -> Command:
    """Execute database migration operation."""

    # Use database_url from state if not provided
    if not database_url and state:
        database_url = state.get("database_url")

    try:
        result_text = await run_hacs_database_migration(
            database_url=database_url,
            force_migration=force_migration,
            config=config
        )

        success = "✅" in result_text
        operation_result = AdminOperationResult(
            operation_type="database_migration",
            success=success,
            message=result_text,
            data={
                "database_url_provided": bool(database_url),
                "force_migration": force_migration
            }
        )

        migration_status = "completed" if success else "failed"
        return Command(
            update={
                "last_operation_result": operation_result,
                "messages": [
                    ToolMessage(
                        f"Migration {migration_status}: {result_text[:200]}...", 
                        tool_call_id=tool_call_id
                    )
                ],
            }
        )

    except Exception as e:
        error_result = AdminOperationResult(
            operation_type="database_migration",
            success=False,
            message=f"Migration failed: {str(e)}",
            error=str(e)
        )

        return Command(
            update={
                "last_operation_result": error_result,
                "messages": [
                    ToolMessage(f"Migration failed: {str(e)}", tool_call_id=tool_call_id)
                ],
            }
        )

admin_database_migration = StructuredTool.from_function(
    _admin_database_migration,
    name="admin_database_migration",
    description="""Run HACS database migration to set up or update database schemas.

This is a critical admin operation that:
- Sets up required database tables and indexes
- Applies schema migrations for HACS components
- Validates database connectivity and permissions
- Updates schema version tracking

IMPORTANT: This operation requires database access and may take time.""",
    coroutine=_admin_database_migration
)


async def _admin_migration_status(
    database_url: Optional[str] = None,
    state: Annotated[HACSDeepAgentState, InjectedState] = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = None,
    config: Annotated[RunnableConfig, InjectedToolArg] = None,
) -> Command:
    """Check database migration status."""

    # Use database_url from state if not provided
    if not database_url and state:
        database_url = state.get("database_url")

    try:
        result_text = await check_hacs_migration_status(
            database_url=database_url,
            config=config
        )

        operation_result = AdminOperationResult(
            operation_type="migration_status",
            success=True,
            message=result_text,
            data={"database_url_provided": bool(database_url)}
        )

        return Command(
            update={
                "last_operation_result": operation_result,
                "messages": [
                    ToolMessage(
                        f"Migration status: {result_text[:150]}...", 
                        tool_call_id=tool_call_id
                    )
                ],
            }
        )

    except Exception as e:
        error_result = AdminOperationResult(
            operation_type="migration_status",
            success=False,
            message=f"Status check failed: {str(e)}",
            error=str(e)
        )

        return Command(
            update={
                "last_operation_result": error_result,
                "messages": [
                    ToolMessage(f"Status check failed: {str(e)}", tool_call_id=tool_call_id)
                ],
            }
        )

admin_migration_status = StructuredTool.from_function(
    _admin_migration_status,
    name="admin_migration_status",
    description="""Check the current database migration status and schema version.

This admin operation:
- Checks database connectivity
- Reports current schema version
- Lists pending migrations
- Validates database health
- Reports any migration issues""",
    coroutine=_admin_migration_status
)


async def _admin_schema_inspection(
    database_url: Optional[str] = None,
    table_filter: Optional[str] = None,
    state: Annotated[HACSDeepAgentState, InjectedState] = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = None,
    config: Annotated[RunnableConfig, InjectedToolArg] = None,
) -> Command:
    """Inspect database schema."""

    # Use database_url from state if not provided
    if not database_url and state:
        database_url = state.get("database_url")

    try:
        result_text = await describe_hacs_database_schema(
            database_url=database_url,
            table_filter=table_filter,
            config=config
        )

        operation_result = AdminOperationResult(
            operation_type="schema_inspection",
            success=True,
            message=result_text,
            data={
                "database_url_provided": bool(database_url),
                "table_filter": table_filter
            }
        )

        return Command(
            update={
                "last_operation_result": operation_result,
                "messages": [
                    ToolMessage(
                        f"Schema inspection: {len(result_text)} chars of schema info", 
                        tool_call_id=tool_call_id
                    )
                ],
            }
        )

    except Exception as e:
        error_result = AdminOperationResult(
            operation_type="schema_inspection",
            success=False,
            message=f"Schema inspection failed: {str(e)}",
            error=str(e)
        )

        return Command(
            update={
                "last_operation_result": error_result,
                "messages": [
                    ToolMessage(
                        f"Schema inspection failed: {str(e)}", 
                        tool_call_id=tool_call_id
                    )
                ],
            }
        )

admin_schema_inspection = StructuredTool.from_function(
    _admin_schema_inspection,
    name="admin_schema_inspection",
    description="""Inspect the current database schema and get detailed schema 
information.

This admin operation:
- Lists all database tables and columns
- Shows indexes and constraints
- Reports table relationships
- Provides schema documentation
- Helps with troubleshooting and planning""",
    coroutine=_admin_schema_inspection
)


async def _admin_resource_discovery(
    category_filter: Optional[str] = None,
    state: Annotated[HACSDeepAgentState, InjectedState] = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = None,
    config: Annotated[RunnableConfig, InjectedToolArg] = None,
) -> Command:
    """Discover HACS resources."""

    try:
        result_text = await discover_hacs_resources(
            category_filter=category_filter,
            config=config
        )

        operation_result = AdminOperationResult(
            operation_type="resource_discovery",
            success=True,
            message=result_text,
            data={
                "category_filter": category_filter,
            }
        )

        return Command(
            update={
                "last_operation_result": operation_result,
                "messages": [
                    ToolMessage(
                        f"Resource discovery: {result_text[:150]}...", 
                        tool_call_id=tool_call_id
                    )
                ],
            }
        )

    except Exception as e:
        error_result = AdminOperationResult(
            operation_type="resource_discovery",
            success=False,
            message=f"Resource discovery failed: {str(e)}",
            error=str(e)
        )

        return Command(
            update={
                "last_operation_result": error_result,
                "messages": [
                    ToolMessage(
                        f"Resource discovery failed: {str(e)}", 
                        tool_call_id=tool_call_id
                    )
                ],
            }
        )

admin_resource_discovery = StructuredTool.from_function(
    _admin_resource_discovery,
    name="admin_resource_discovery",
    description="Discover and analyze HACS resource schemas and models. This admin operation scans for available HACS resource schemas, reports model types and categories, shows model capabilities and structure, helps with understanding available HACS models, and supports filtering by category. Available categories: clinical, administrative, reasoning. Common model types: Patient, Observation, Condition, Medication, etc.",
    coroutine=_admin_resource_discovery
)


# ============================================================================
# EXPORTED TOOLS LIST
# ============================================================================

HACS_DEEP_AGENT_TOOLS = [
    # Planning tools
    write_todos,

    # File system tools
    ls,
    read_file,
    write_file,
    edit_file,

    # HACS admin operation tools
    admin_database_migration,
    admin_migration_status,
    admin_schema_inspection,
    admin_resource_discovery,
] 