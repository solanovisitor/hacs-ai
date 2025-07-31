"""HACS Deep Agent Tools.

Adapted from the deep agents framework for HACS admin operations.
Includes planning tools, file system tools, and HACS-specific admin tools.
"""

from typing import Annotated, List, Optional
from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langgraph.prebuilt import InjectedState

from state import Todo, HACSDeepAgentState, AdminOperationResult

# Import real HACS admin tools
from tools import (
    run_hacs_database_migration,
    check_hacs_migration_status,
    describe_hacs_database_schema,
    create_admin_hacs_record,
    discover_hacs_resources,
)


# ============================================================================
# PLANNING TOOLS (adapted for HACS admin)
# ============================================================================

@tool(description="""Use this tool to create and manage a structured task list for your current HACS admin work session. 

This helps you track progress, organize complex admin operations, and demonstrate thoroughness.

## When to Use This Tool for HACS Admin:
- Complex database migrations requiring multiple steps
- System setup operations across multiple components
- Resource management tasks involving multiple resources
- Troubleshooting operations requiring systematic approach
- User requests multiple admin operations

## HACS Admin Task Examples:
- "Set up HACS database schema" 
- "Migrate existing data to new schema version"
- "Validate system configuration and connectivity"
- "Create test resources and verify functionality"
- "Generate admin reports and documentation"

## Task States:
- pending: Not yet started
- in_progress: Currently working on (ONLY ONE at a time)
- completed: Successfully finished

Mark tasks complete IMMEDIATELY after finishing. Only have ONE task in_progress at any time.""")
def write_todos(
    todos: List[Todo], 
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """Write or update the admin task list."""
    return Command(
        update={
            "todos": todos,
            "messages": [
                ToolMessage(f"Updated admin task list: {len(todos)} tasks", tool_call_id=tool_call_id)
            ],
        }
    )


# ============================================================================
# FILE SYSTEM TOOLS (adapted for HACS admin)
# ============================================================================

@tool
def ls(state: Annotated[HACSDeepAgentState, InjectedState]) -> List[str]:
    """List all files in the admin workspace."""
    return list(state.get("files", {}).keys())


@tool(description="""Read admin configuration files, scripts, or documentation.

Perfect for:
- Database configuration files
- Migration scripts
- Admin documentation
- Environment files
- Log files
- Schema definitions""")
def read_file(
    file_path: str,
    state: Annotated[HACSDeepAgentState, InjectedState],
    offset: int = 0,
    limit: int = 2000,
) -> str:
    """Read admin file content."""
    files = state.get("files", {})
    if file_path not in files:
        return f"Error: Admin file '{file_path}' not found"

    content = files[file_path]
    if not content or content.strip() == "":
        return "File exists but has empty contents"

    lines = content.splitlines()
    start_idx = offset
    end_idx = min(start_idx + limit, len(lines))

    if start_idx >= len(lines):
        return f"Error: Line offset {offset} exceeds file length ({len(lines)} lines)"

    result_lines = []
    for i in range(start_idx, end_idx):
        line_content = lines[i]
        if len(line_content) > 2000:
            line_content = line_content[:2000]
        line_number = i + 1
        result_lines.append(f"{line_number:6d}\t{line_content}")

    return "\n".join(result_lines)


@tool(description="""Write admin files like configuration, scripts, or documentation.

Common admin files:
- database_config.json - Database connection settings
- migration_script.sql - Custom migration scripts  
- admin_checklist.md - Admin operation checklists
- environment_setup.sh - Environment setup scripts
- backup_config.yaml - Backup configuration
- monitoring_config.json - System monitoring setup""")
def write_file(
    file_path: str,
    content: str,
    state: Annotated[HACSDeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Write content to an admin file."""
    files = state.get("files", {})
    files[file_path] = content
    return Command(
        update={
            "files": files,
            "messages": [
                ToolMessage(f"Created admin file: {file_path}", tool_call_id=tool_call_id)
            ],
        }
    )


@tool(description="""Edit existing admin files with precise string replacement.

Use this to modify:
- Configuration files (update settings)
- Scripts (fix bugs, add features)
- Documentation (update procedures)
- Environment files (change variables)

Always read the file first before editing.""")
def edit_file(
    file_path: str,
    old_string: str,
    new_string: str,
    state: Annotated[HACSDeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    replace_all: bool = False,
) -> Command:
    """Edit admin file with string replacement."""
    files = state.get("files", {})
    
    if file_path not in files:
        return Command(
            update={
                "messages": [
                    ToolMessage(f"Error: Admin file '{file_path}' not found", tool_call_id=tool_call_id)
                ]
            }
        )

    content = files[file_path]

    if old_string not in content:
        return Command(
            update={
                "messages": [
                    ToolMessage(f"Error: String not found in {file_path}: '{old_string}'", tool_call_id=tool_call_id)
                ]
            }
        )

    if not replace_all:
        occurrences = content.count(old_string)
        if occurrences > 1:
            return Command(
                update={
                    "messages": [
                        ToolMessage(f"Error: String '{old_string}' appears {occurrences} times. Use replace_all=True or be more specific.", tool_call_id=tool_call_id)
                    ]
                }
            )

    # Perform replacement
    if replace_all:
        new_content = content.replace(old_string, new_string)
        replacement_count = content.count(old_string)
        msg = f"Replaced {replacement_count} instance(s) in {file_path}"
    else:
        new_content = content.replace(old_string, new_string, 1)
        msg = f"Successfully updated {file_path}"

    files[file_path] = new_content
    return Command(
        update={
            "files": files,
            "messages": [
                ToolMessage(msg, tool_call_id=tool_call_id)
            ],
        }
    )


# ============================================================================
# HACS ADMIN OPERATION TOOLS (wrapped for deep agent)
# ============================================================================

@tool(description="""Run HACS database migration to set up or update database schemas.

This is a REAL admin operation that performs actual database migrations.
Use this for:
- Initial HACS database setup
- Schema updates and migrations
- Database structure validation

IMPORTANT: This operation requires database access and may take time.""")
async def admin_database_migration(
    database_url: Optional[str] = None,
    force_migration: bool = False,
    state: Annotated[HACSDeepAgentState, InjectedState] = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = None,
) -> Command:
    """Execute database migration operation."""
    
    # Use database_url from state if not provided
    if not database_url and state:
        database_url = state.get("database_url")
    
    try:
        result_text = await run_hacs_database_migration(
            database_url=database_url,
            force_migration=force_migration
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
        
        return Command(
            update={
                "last_operation_result": operation_result,
                "messages": [
                    ToolMessage(f"Migration {'completed' if success else 'failed'}: {result_text[:200]}...", tool_call_id=tool_call_id)
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
                    ToolMessage(f"Migration error: {str(e)}", tool_call_id=tool_call_id)
                ],
            }
        )


@tool(description="""Check current HACS database migration status and history.

Use this to:
- Verify database setup status  
- Check migration history
- Validate database connectivity
- Troubleshoot migration issues""")
async def admin_migration_status(
    database_url: Optional[str] = None,
    state: Annotated[HACSDeepAgentState, InjectedState] = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = None,
) -> Command:
    """Check database migration status."""
    
    if not database_url and state:
        database_url = state.get("database_url")
    
    try:
        result_text = await check_hacs_migration_status(database_url=database_url)
        success = "✅" in result_text
        
        operation_result = AdminOperationResult(
            operation_type="migration_status",
            success=success,
            message=result_text,
            data={"operation": "status_check"}
        )
        
        return Command(
            update={
                "last_operation_result": operation_result,
                "messages": [
                    ToolMessage(f"Status check: {result_text[:200]}...", tool_call_id=tool_call_id)
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
                    ToolMessage(f"Status error: {str(e)}", tool_call_id=tool_call_id)
                ],
            }
        )


@tool(description="""Inspect HACS database schema, tables, and structures.

Use this for:
- Database structure analysis
- Schema validation
- Table inspection
- Relationship mapping""")
async def admin_schema_inspection(
    schema_name: str = "hacs_core",
    tool_call_id: Annotated[str, InjectedToolCallId] = None,
) -> Command:
    """Inspect database schema."""
    
    try:
        result_text = await describe_hacs_database_schema(schema_name=schema_name)
        success = "✅" in result_text
        
        operation_result = AdminOperationResult(
            operation_type="schema_inspection",
            success=success,
            message=result_text,
            data={"schema_name": schema_name}
        )
        
        return Command(
            update={
                "last_operation_result": operation_result,
                "messages": [
                    ToolMessage(f"Schema inspection: {result_text[:200]}...", tool_call_id=tool_call_id)
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
                    ToolMessage(f"Schema error: {str(e)}", tool_call_id=tool_call_id)
                ],
            }
        )


@tool(description="""Discover available HACS resource types and their capabilities.

Use this to:
- Explore available HACS resources
- Understand resource schemas  
- Plan resource creation
- Validate resource types""")
async def admin_resource_discovery(
    category_filter: Optional[str] = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = None,
) -> Command:
    """Discover HACS resources."""
    
    try:
        result_text = await discover_hacs_resources(category_filter=category_filter)
        success = "✅" in result_text
        
        operation_result = AdminOperationResult(
            operation_type="resource_discovery",
            success=success,
            message=result_text,
            data={"category_filter": category_filter}
        )
        
        return Command(
            update={
                "last_operation_result": operation_result,
                "messages": [
                    ToolMessage(f"Resource discovery: Found HACS resources", tool_call_id=tool_call_id)
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
                    ToolMessage(f"Discovery error: {str(e)}", tool_call_id=tool_call_id)
                ],
            }
        )


# List of all HACS deep agent tools
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