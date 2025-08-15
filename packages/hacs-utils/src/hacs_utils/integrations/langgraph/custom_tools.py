"""
HACS Custom Tools for LangGraph Integration

This module provides LangGraph-specific custom tools that are not available
in the centralized hacs-tools system. These include:

- Agent-specific scratchpad and todo management
- Healthcare file operations with context
- Agent delegation tools
- HACS integration validation tools

These tools complement the centralized HACS tools and provide LangGraph-specific
functionality for healthcare AI agents.
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

# HACS Core imports
from hacs_models import HACSResult
from hacs_utils.agent_types import (
    ScratchpadTodo, AgentScratchpadEntry, AgentTask,
    TodoPriority, TodoStatus, ClinicalUrgency
)
from hacs_core.tool_protocols import hacs_tool, ToolCategory

# LangGraph specific imports
try:
    from langchain_core.tools import BaseTool
    from langchain_core.language_models import LanguageModelLike
    from langgraph.prebuilt import create_react_agent
    _has_langchain = True
except ImportError:
    _has_langchain = False
    BaseTool = Any
    LanguageModelLike = Any

# Registry imports for model access
try:
    from hacs_models import get_model_registry
    _has_models = True
except ImportError:
    _has_models = False

# === SCRATCHPAD AND TODO MANAGEMENT TOOLS ===

@hacs_tool(
    name="create_scratchpad_todo",
    description="Create a healthcare todo using proper HACS ScratchpadTodo type",
    category=ToolCategory.MEMORY_OPERATIONS,
    domains=["agent_memory", "task_management"]
)
async def create_scratchpad_todo(
    content: str,
    priority: str = "medium",
    clinical_urgency: str = "routine",
    patient_id: Optional[str] = None,
    assigned_actor: Optional[str] = None
) -> HACSResult:
    """Create a healthcare todo using proper HACS ScratchpadTodo type."""
    todo = ScratchpadTodo(
        content=content,
        priority=TodoPriority(priority),
        clinical_urgency=ClinicalUrgency(clinical_urgency),
        patient_id=patient_id,
        assigned_actor=assigned_actor or "system",
        status=TodoStatus.PENDING
    )

    return HACSResult(
        success=True,
        message="Healthcare Todo Created Successfully",
        data={
            "id": todo.id,
            "content": todo.content,
            "priority": todo.priority.value if hasattr(todo.priority, 'value') else str(todo.priority),
            "clinical_urgency": todo.clinical_urgency.value if hasattr(todo.clinical_urgency, 'value') else str(todo.clinical_urgency),
            "status": todo.status.value if hasattr(todo.status, 'value') else str(todo.status),
            "assigned_actor": todo.assigned_actor,
            "patient_id": todo.patient_id,
            "created_at": str(todo.created_at)
        }
    )


@hacs_tool(
    name="create_scratchpad_entry",
    description="Create an agent scratchpad entry using HACS AgentScratchpadEntry type",
    category=ToolCategory.MEMORY_OPERATIONS,
    domains=["cognitive_systems", "agent_memory"]
)
async def create_scratchpad_entry(
    entry_type: str,
    content: str,
    context: Optional[Dict[str, Any]] = None,
    patient_id: Optional[str] = None
) -> HACSResult:
    """Create an agent scratchpad entry using HACS AgentScratchpadEntry type."""
    entry = AgentScratchpadEntry(
        entry_type=entry_type,
        content=content,
        context=context or {},
        patient_id=patient_id,
        created_by="hacs_agent",
        created_at=datetime.now()
    )

    return HACSResult(
        success=True,
        message="Agent Scratchpad Entry Created Successfully",
        data={
            "id": entry.id,
            "entry_type": entry.entry_type,
            "content": entry.content,
            "context": entry.context,
            "patient_id": entry.patient_id,
            "created_by": entry.created_by,
            "created_at": str(entry.created_at)
        }
    )


@hacs_tool(
    name="create_agent_task",
    description="Create a healthcare agent task using HACS AgentTask type",
    category=ToolCategory.MEMORY_OPERATIONS,
    domains=["task_management", "workflow_coordination"]
)
async def create_agent_task(
    task_type: str,
    description: str,
    priority: str = "medium",
    assigned_to: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> HACSResult:
    """Create a healthcare agent task using HACS AgentTask type."""
    task = AgentTask(
        task_type=task_type,
        description=description,
        priority=TodoPriority(priority),
        assigned_to=assigned_to or "system",
        context=context or {},
        status=TodoStatus.PENDING,
        created_at=datetime.now()
    )

    return HACSResult(
        success=True,
        message="Healthcare Agent Task Created Successfully",
        data={
            "id": task.id,
            "task_type": task.task_type,
            "description": task.description,
            "priority": task.priority.value if hasattr(task.priority, 'value') else str(task.priority),
            "assigned_to": task.assigned_to,
            "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
            "context": task.context,
            "created_at": str(task.created_at)
        }
    )


# === HEALTHCARE RESOURCE TOOLS ===

@hacs_tool(
    name="create_healthcare_resource",
    description="Create a healthcare resource using HACS models",
    category=ToolCategory.RESOURCE_MANAGEMENT,
    domains=["resource_creation"]
)
async def create_healthcare_resource(
    resource_type: str,
    resource_data: Dict[str, Any]
) -> HACSResult:
    """Create a healthcare resource using HACS models."""
    if not _has_models:
        return HACSResult(
            success=False,
            message="HACS models not available",
            data={"error": "hacs_models package not installed"}
        )

    try:
        model_registry = get_model_registry()
        model_class = model_registry[resource_type]

        healthcare_resource = model_class(**resource_data)

        return HACSResult(
            success=True,
            message=f"Healthcare {resource_type} created successfully",
            data={
                "resource_type": resource_type,
                "resource_id": healthcare_resource.id,
                "resource_data": healthcare_resource.model_dump()
            }
        )
    except Exception as e:
        return HACSResult(
            success=False,
            message=f"Failed to create healthcare resource: {str(e)}",
            data={"error": str(e), "resource_type": resource_type}
        )


@hacs_tool(
    name="get_healthcare_resource_schema",
    description="Get the JSON schema for a healthcare resource type",
    category=ToolCategory.SCHEMA_DISCOVERY,
    domains=["schema_analysis", "resource_discovery"]
)
async def get_healthcare_resource_schema(
    resource_type: str
) -> HACSResult:
    """Get the JSON schema for a healthcare resource type."""
    if not _has_models:
        return HACSResult(
            success=False,
            message="HACS models not available",
            data={"error": "hacs_models package not installed"}
        )

    try:
        model_registry = get_model_registry()
        model_class = model_registry[resource_type]
        schema = model_class.model_json_schema()

        return HACSResult(
            success=True,
            message=f"Schema retrieved for {resource_type}",
            data={
                "resource_type": resource_type,
                "schema": schema
            }
        )
    except Exception as e:
        return HACSResult(
            success=False,
            message=f"Failed to get schema: {str(e)}",
            data={"error": str(e), "resource_type": resource_type}
        )


@hacs_tool(
    name="create_resource_subset",
    description="Create a subset model with selected fields",
    category=ToolCategory.RESOURCE_MANAGEMENT,
    domains=["resource_filtering", "data_projection"]
)
async def create_resource_subset(
    resource_type: str,
    fields: List[str]
) -> HACSResult:
    """Create a subset model with selected fields."""
    if not _has_models:
        return HACSResult(
            success=False,
            message="HACS models not available",
            data={"error": "hacs_models package not installed"}
        )

    try:
        model_registry = get_model_registry()
        model_class = model_registry[resource_type]

        if not hasattr(model_class, 'pick'):
            return HACSResult(
                success=False,
                message=f"{resource_type} does not support field picking",
                data={"resource_type": resource_type}
            )

        subset_model = model_class.pick(*fields)

        return HACSResult(
            success=True,
            message=f"Subset model created for {resource_type}",
            data={
                "resource_type": resource_type,
                "selected_fields": fields,
                "subset_schema": subset_model.model_json_schema()
            }
        )
    except Exception as e:
        return HACSResult(
            success=False,
            message=f"Failed to create subset: {str(e)}",
            data={"error": str(e), "resource_type": resource_type, "fields": fields}
        )


# === FILE OPERATION TOOLS ===

@hacs_tool(
    name="write_file",
    description="Write content to a file. Pass file_path and content.",
    category=ToolCategory.DEVELOPMENT_TOOLS,
    domains=["file_management", "documentation"]
)
def write_file(
    file_path: str,
    content: str,
    clinical_metadata: Optional[Dict[str, Any]] = None
) -> HACSResult:
    """Write content to a file."""
    try:
        with open(file_path, 'w') as f:
            f.write(content)

        return HACSResult(
            success=True,
            message="Healthcare file written successfully",
            data={
                "file_path": file_path,
                "content_length": len(content),
                "clinical_metadata": clinical_metadata or {},
                "operation": "file_write"
            }
        )
    except Exception as e:
        return HACSResult(
            success=False,
            message=f"Failed to write file: {str(e)}",
            data={"error": str(e), "file_path": file_path}
        )


@hacs_tool(
    name="read_file",
    description="Read content from a file. Optional start_line and end_line.",
    category=ToolCategory.DEVELOPMENT_TOOLS,
    domains=["file_management", "documentation"]
)
def read_file(
    file_path: str,
    start_line: int = 1,
    end_line: Optional[int] = None
) -> HACSResult:
    """Read content from a file."""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()

        if end_line is None:
            end_line = len(lines)

        # Convert to 0-based indexing
        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), end_line)

        selected_lines = lines[start_idx:end_idx]
        content = ''.join(selected_lines)

        return HACSResult(
            success=True,
            message="Healthcare file read successfully",
            data={
                "file_path": file_path,
                "content": content,
                "lines_read": len(selected_lines),
                "total_lines": len(lines),
                "start_line": start_line,
                "end_line": end_line,
                "operation": "file_read"
            }
        )
    except Exception as e:
        return HACSResult(
            success=False,
            message=f"Failed to read file: {str(e)}",
            data={"error": str(e), "file_path": file_path}
        )


@hacs_tool(
    name="edit_file",
    description="Replace a specific line in a file. Pass file_path, line_number, new_content.",
    category=ToolCategory.DEVELOPMENT_TOOLS,
    domains=["file_management", "documentation"]
)
def edit_file(
    file_path: str,
    line_number: int,
    new_content: str,
    clinical_metadata: Optional[Dict[str, Any]] = None
) -> HACSResult:
    """Edit a specific line in a file."""
    try:
        # Read existing content
        with open(file_path, 'r') as f:
            lines = f.readlines()

        # Convert to 0-based indexing
        line_idx = line_number - 1

        if line_idx < 0 or line_idx >= len(lines):
            return HACSResult(
                success=False,
                message=f"Line number {line_number} out of range",
                data={"file_path": file_path, "line_number": line_number, "total_lines": len(lines)}
            )

        # Make the edit
        old_content = lines[line_idx].rstrip()
        lines[line_idx] = new_content + '\n'

        # Write back
        with open(file_path, 'w') as f:
            f.writelines(lines)

        return HACSResult(
            success=True,
            message="Healthcare file edited successfully",
            data={
                "file_path": file_path,
                "line_number": line_number,
                "old_content": old_content,
                "new_content": new_content,
                "clinical_metadata": clinical_metadata or {},
                "operation": "file_edit"
            }
        )
    except Exception as e:
        return HACSResult(
            success=False,
            message=f"Failed to edit file: {str(e)}",
            data={"error": str(e), "file_path": file_path, "line_number": line_number}
        )


# === INTEGRATION AND VALIDATION TOOLS ===

@hacs_tool(
    name="validate_hacs_integration",
    description="Validate HACS component integration and health",
    category=ToolCategory.ADMIN_OPERATIONS,
    domains=["system_validation", "integration_testing"]
)
async def validate_hacs_integration() -> HACSResult:
    """Validate HACS component integration and health."""
    validation_results = {
        "hacs_models": _has_models,
        "langchain_integration": _has_langchain,
        "timestamp": str(datetime.now())
    }

    # Test model registry access if available
    if _has_models:
        try:
            model_registry = get_model_registry()
            validation_results["available_models"] = list(model_registry.keys())[:5]  # First 5 models
            validation_results["model_registry_health"] = True
        except Exception as e:
            validation_results["model_registry_health"] = False
            validation_results["model_registry_error"] = str(e)

    overall_health = validation_results["hacs_models"] and validation_results["langchain_integration"]

    return HACSResult(
        success=overall_health,
        message="HACS integration validation completed",
        data=validation_results
    )


@hacs_tool(
    name="discover_available_tools",
    description="Discover and list all available HACS tools with categorization",
    category=ToolCategory.ADMIN_OPERATIONS,
    domains=["tool_discovery", "system_introspection"]
)
async def discover_available_tools() -> HACSResult:
    """Discover and list all available HACS tools with categorization."""
    # Get local custom tools
    local_tools = [
        create_scratchpad_todo,
        create_scratchpad_entry,
        create_agent_task,
        create_healthcare_resource,
        get_healthcare_resource_schema,
        create_resource_subset,
        write_file,
        read_file,
        edit_file,
        validate_hacs_integration,
        discover_available_tools
    ]

    tool_info = []
    for tool in local_tools:
        tool_info.append({
            "name": getattr(tool, 'name', tool.__name__),
            "description": getattr(tool, 'description', tool.__doc__),
            "category": getattr(tool, 'category', 'unknown'),
            "type": "local_custom_tool"
        })

    return HACSResult(
        success=True,
        message=f"Discovered {len(tool_info)} local custom tools",
        data={
            "total_tools": len(tool_info),
            "tools": tool_info,
            "discovery_timestamp": str(datetime.now())
        }
    )


# === SUBAGENT DELEGATION TOOL ===

@hacs_tool(
    name="delegate_to_subagent",
    description="Delegate a complex healthcare task to a specialized subagent",
    category=ToolCategory.AI_INTEGRATIONS,
    domains=["task_delegation", "specialized_processing"]
)
async def delegate_to_subagent(
    task_description: str,
    subagent_type: str = "general",
    context: Optional[Dict[str, Any]] = None,
    priority: str = "medium"
) -> HACSResult:
    """Delegate a complex healthcare task to a specialized subagent."""
    # This is a placeholder implementation
    # In a real system, this would integrate with actual subagent infrastructure

    delegation_data = {
        "task_id": f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "task_description": task_description,
        "subagent_type": subagent_type,
        "context": context or {},
        "priority": priority,
        "status": "delegated",
        "created_at": str(datetime.now())
    }

    return HACSResult(
        success=True,
        message=f"Task delegated to {subagent_type} subagent",
        data=delegation_data
    )


# === EXPORT ALL CUSTOM TOOLS ===

CUSTOM_LANGGRAPH_TOOLS = [
    create_scratchpad_todo,
    create_scratchpad_entry,
    create_agent_task,
    create_healthcare_resource,
    get_healthcare_resource_schema,
    create_resource_subset,
    write_file,
    read_file,
    edit_file,
    validate_hacs_integration,
    discover_available_tools,
    delegate_to_subagent
]

__all__ = [
    "CUSTOM_LANGGRAPH_TOOLS",
    "create_scratchpad_todo",
    "create_scratchpad_entry",
    "create_agent_task",
    "create_healthcare_resource",
    "get_healthcare_resource_schema",
    "create_resource_subset",
    "write_file",
    "read_file",
    "edit_file",
    "validate_hacs_integration",
    "discover_available_tools",
    "delegate_to_subagent"
]