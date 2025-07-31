"""Simplified LangGraph workflow for HACS Admin Agent."""

import os
import sys
from typing import Any, Dict

# Add current directory to path for imports FIRST
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph.graph import START, StateGraph

# Import simplified state classes
from state import State, AdminOperationResult
from configuration import PrivateConfig

# Import essential admin tools
from tools import (
    # Real HACS admin tools
    run_hacs_database_migration,
    check_hacs_migration_status,
    describe_hacs_database_schema,
    create_admin_hacs_record,
    # Keep some essential discovery tools
    discover_hacs_resources,
)

# ============================================================================
# PRIVATE OPERATION TRACKING (not in state)
# ============================================================================

# Private variables for internal operation tracking
_current_operation = None
_operation_in_progress = False
_database_connected = False
_retry_count = 0

# ============================================================================
# SIMPLIFIED ADMIN OPERATION NODES
# ============================================================================

def initialize_admin_state(state: State) -> Dict[str, Any]:
    """Initialize basic conversation state only."""
    global _current_operation, _operation_in_progress, _retry_count
    
    # Reset private tracking variables
    _current_operation = None
    _operation_in_progress = False
    _retry_count = 0
    
    return {
        "session_id": state.get("session_id", "admin_session"),
        "last_operation_result": None,
        "last_error": None
    }


async def admin_operation_router(state: State) -> Dict[str, Any]:
    """Route to appropriate admin operation based on messages."""
    global _current_operation, _operation_in_progress
    
    # Get the last message to determine operation type
    messages = state.get("messages", [])
    if not messages:
        return {"last_error": "No operation specified"}
    
    last_message = messages[-1].content.lower()
    
    # Determine operation type from user message
    if any(word in last_message for word in ["migration", "migrate", "setup", "initialize"]):
        operation_type = "database_migration"
    elif any(word in last_message for word in ["status", "check", "migration status"]):
        operation_type = "migration_status"
    elif any(word in last_message for word in ["schema", "describe", "tables", "structure"]):
        operation_type = "schema_inspection"
    elif any(word in last_message for word in ["create", "record", "resource"]):
        operation_type = "create_resource"
    elif any(word in last_message for word in ["discover", "find", "available"]):
        operation_type = "discover_resources"
    else:
        operation_type = "general_help"
    
    # Set private tracking variables
    _current_operation = operation_type
    _operation_in_progress = True
    
    return {}  # No state changes, just private tracking


async def execute_admin_operation(state: State) -> Dict[str, Any]:
    """Execute the determined admin operation."""
    global _current_operation, _operation_in_progress, _retry_count
    
    if not _operation_in_progress or not _current_operation:
        return {
            "last_error": "No operation in progress",
            "last_operation_result": None
        }
    
    try:
        # Get database URL from input state or environment
        database_url = None
        if hasattr(state, 'database_url') and state.database_url:
            database_url = state.database_url
        
        if _current_operation == "database_migration":
            result_text = await run_hacs_database_migration(database_url=database_url)
            success = "✅" in result_text
            operation_result = AdminOperationResult(
                operation_type="database_migration",
                success=success,
                message=result_text,
                data={"operation": "migration", "database_url_provided": bool(database_url)}
            )
            
        elif _current_operation == "migration_status":
            result_text = await check_hacs_migration_status(database_url=database_url)
            success = "✅" in result_text
            operation_result = AdminOperationResult(
                operation_type="migration_status",
                success=success,
                message=result_text,
                data={"operation": "status_check"}
            )
            
        elif _current_operation == "schema_inspection":
            result_text = await describe_hacs_database_schema()
            success = "✅" in result_text
            operation_result = AdminOperationResult(
                operation_type="schema_inspection",
                success=success,
                message=result_text,
                data={"operation": "schema_description"}
            )
            
        elif _current_operation == "discover_resources":
            result_text = await discover_hacs_resources()
            success = "✅" in result_text
            operation_result = AdminOperationResult(
                operation_type="discover_resources",
                success=success,
                message=result_text,
                data={"operation": "resource_discovery"}
            )
            
        else:  # general_help
            available_ops = PrivateConfig.AVAILABLE_OPERATIONS
            help_message = f"""Available HACS admin operations:

• **Database Migration**: Set up or update HACS database schemas
• **Migration Status**: Check current database migration status  
• **Schema Inspection**: View database tables and structures
• **Resource Discovery**: Find available HACS resource types
• **Create Resource**: Create new HACS records

Supported operations: {', '.join(available_ops)}"""
            
            operation_result = AdminOperationResult(
                operation_type="general_help",
                success=True,
                message=help_message,
                data={"available_operations": available_ops}
            )
    
    except Exception as e:
        operation_result = AdminOperationResult(
            operation_type=_current_operation or "unknown",
            success=False,
            message=f"Operation failed: {str(e)}",
            error=str(e),
            data={"retry_count": _retry_count}
        )
    
    # Reset private tracking
    _operation_in_progress = False
    _current_operation = None
    
    return {
        "last_operation_result": operation_result,
        "last_error": operation_result.error if not operation_result.success else None
    }


# ============================================================================
# SIMPLIFIED GRAPH CONSTRUCTION
# ============================================================================

def create_hacs_admin_graph():
    """Create the simplified admin graph."""
    
    # Create the graph with simplified State
    graph = StateGraph(State)
    
    # Add nodes
    graph.add_node("initialize", initialize_admin_state)
    graph.add_node("router", admin_operation_router)
    graph.add_node("execute", execute_admin_operation)
    
    # Set entry point
    graph.add_edge(START, "initialize")
    graph.add_edge("initialize", "router")
    graph.add_edge("router", "execute")
    graph.add_edge("execute", "__end__")
    
    return graph.compile()


# Create the main graph
workflow = create_hacs_admin_graph()
workflow.name = "HACSAdminAgent"

# Export for compatibility
graph = workflow
