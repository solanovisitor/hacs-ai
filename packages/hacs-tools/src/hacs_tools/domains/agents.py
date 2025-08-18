"""
HACS Agents Tools - Context Engineering for AI Agents

This domain provides tools for agent context engineering including scratchpad management,
todo tracking, memory operations, preferences injection, tool loadout selection,
and state management. These are the context engineering primitives that enable
sophisticated agent behaviors within the healthcare context.

Domain Focus:
- Scratchpad and note-taking for agent working memory
- Todo and task management for agent planning
- Memory storage, retrieval, and context injection
- Actor preference management and injection
- Semantic tool loadout selection
- Context summarization, pruning, and isolation
"""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import uuid

from hacs_models import HACSResult, BaseResource
from hacs_core import Actor
from hacs_models import (
    get_model_registry, AgentScratchpadEntry, ScratchpadTodo, AgentTask,
    MessageDefinition
)
from hacs_utils.memory_utils import gather_memories, merge_memories, filter_memories
from hacs_utils.preferences import merge_preferences, inject_preferences as _inject_preferences
from hacs_utils.semantic_index import semantic_tool_loadout
# Tool domain: agents - Context Engineering for AI Agents

logger = logging.getLogger(__name__)
from hacs_registry.tool_registry import register_tool, VersionStatus
try:
    from pydantic import BaseModel, Field
except Exception:  # pragma: no cover
    class BaseModel:  # type: ignore
        pass
    def Field(*args, **kwargs):  # type: ignore
        return None


# ===== Pydantic input models for agents tools =====
class WriteScratchpadInput(BaseModel):
    content: str
    entry_type: str = Field(default="note")
    session_id: Optional[str] = None
    tags: Optional[List[str]] = None
    messages: Optional[List[Dict[str, Any]]] = None
    config: Optional[Dict[str, Any]] = None
    state: Optional[Dict[str, Any]] = None


class ReadScratchpadInput(BaseModel):
    session_id: Optional[str] = None
    entry_type: Optional[str] = None
    limit: int = 10
    messages: Optional[List[Dict[str, Any]]] = None
    config: Optional[Dict[str, Any]] = None
    state: Optional[Dict[str, Any]] = None


class CreateTodoInput(BaseModel):
    content: Optional[str] = None
    priority: Optional[str | int] = None
    status: Optional[str] = None
    clinical_urgency: Optional[str] = None
    task_description: Optional[str] = None
    category: Optional[str] = None
    due_date: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    messages: Optional[List[Dict[str, Any]]] = None
    config: Optional[Dict[str, Any]] = None
    state: Optional[Dict[str, Any]] = None


class ListTodosInput(BaseModel):
    status: Optional[str] = None
    category: Optional[str] = None
    priority_min: Optional[int] = None
    limit: int = 20
    messages: Optional[List[Dict[str, Any]]] = None
    config: Optional[Dict[str, Any]] = None
    state: Optional[Dict[str, Any]] = None


class CompleteTodoInput(BaseModel):
    todo_id: str
    completion_notes: Optional[str] = None
    messages: Optional[List[Dict[str, Any]]] = None
    config: Optional[Dict[str, Any]] = None
    state: Optional[Dict[str, Any]] = None


class StoreMemoryInput(BaseModel):
    content: str
    memory_type: str = Field(default="episodic")
    actor_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    messages: Optional[List[Dict[str, Any]]] = None
    config: Optional[Dict[str, Any]] = None
    state: Optional[Dict[str, Any]] = None


class RetrieveMemoriesInput(BaseModel):
    query: Optional[str] = None
    actor_id: Optional[str] = None
    memory_type: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = 10
    messages: Optional[List[Dict[str, Any]]] = None
    config: Optional[Dict[str, Any]] = None
    state: Optional[Dict[str, Any]] = None


class InjectPreferencesInput(BaseModel):
    message: Dict[str, Any]
    actor_id: str
    preference_scope: str = Field(default="response_format")
    messages: Optional[List[Dict[str, Any]]] = None
    config: Optional[Dict[str, Any]] = None
    state: Optional[Dict[str, Any]] = None


class SelectToolsForTaskInput(BaseModel):
    task_description: str
    max_tools: int = 10
    domain_filter: Optional[str] = None
    exclude_tools: Optional[List[str]] = None
    messages: Optional[List[Dict[str, Any]]] = None
    config: Optional[Dict[str, Any]] = None
    state: Optional[Dict[str, Any]] = None


class SummarizeStateInput(BaseModel):
    state_data: Dict[str, Any]
    focus_areas: Optional[List[str]] = None
    compression_ratio: float = 0.3
    messages: Optional[List[Dict[str, Any]]] = None
    config: Optional[Dict[str, Any]] = None
    state: Optional[Dict[str, Any]] = None


class PruneStateInput(BaseModel):
    state_data: Dict[str, Any]
    keep_fields: Optional[List[str]] = None
    max_messages: int = 20
    max_tools: int = 30
    messages: Optional[List[Dict[str, Any]]] = None
    config: Optional[Dict[str, Any]] = None
    state: Optional[Dict[str, Any]] = None


@register_tool(name="write_scratchpad", domain="agents", tags=["domain:agents"], status=VersionStatus.ACTIVE)
def write_scratchpad(
    content: str,
    entry_type: str = "note",
    session_id: Optional[str] = None,
    tags: Optional[List[str]] = None,
    messages: Optional[List[Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None,
    state: Optional[Dict[str, Any]] = None,
) -> HACSResult:
    """
    Write an entry to the agent's scratchpad for working memory.
    
    Args:
        content: The content to write to scratchpad
        entry_type: Type of entry ("note", "observation", "decision", "question")
        session_id: Optional session ID for grouping entries
        tags: Optional tags for categorization
        
    Returns:
        HACSResult with entry ID and confirmation
    """
    try:
        # Create scratchpad entry
        entry = AgentScratchpadEntry(
            entry_type=entry_type,
            content=content,
            agent_id="system",  # Default agent_id since it's required
            tags=tags or [],
            metadata={
                "session_id": session_id,
                "created_at": datetime.now().isoformat()
            }
        )
        
        return HACSResult(
            success=True,
            message="Successfully wrote to scratchpad",
            data={
                "entry_id": entry.id,
                "content": content,
                "entry_type": entry_type
            }
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message="Failed to write to scratchpad",
            error=str(e)
        )

# Attach args
write_scratchpad._tool_args = WriteScratchpadInput  # type: ignore[attr-defined]


@register_tool(name="read_scratchpad", domain="agents", tags=["domain:agents"], status=VersionStatus.ACTIVE)
def read_scratchpad(
    session_id: Optional[str] = None,
    entry_type: Optional[str] = None,
    limit: int = 10,
    messages: Optional[List[Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None,
    state: Optional[Dict[str, Any]] = None,
) -> HACSResult:
    """
    Read entries from the agent's scratchpad.
    
    Args:
        session_id: Optional session ID to filter entries
        entry_type: Optional entry type to filter by
        limit: Maximum number of entries to return
        
    Returns:
        HACSResult with scratchpad entries
    """
    try:
        # In a real implementation, this would query persistent storage
        # For now, return a sample structure
        entries = []
        
        # This would be replaced with actual scratchpad storage query
        sample_entry = {
            "id": str(uuid.uuid4()),
            "entry_type": entry_type or "note",
            "content": "Sample scratchpad entry",
            "context": {"session_id": session_id},
            "created_at": datetime.now().isoformat()
        }
        
        if session_id or entry_type:
            # Apply filters in real implementation
            pass
            
        entries = [sample_entry][:limit]
        
        return HACSResult(
            success=True,
            message=f"Retrieved {len(entries)} scratchpad entries",
            data={"entries": entries}
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message="Failed to read scratchpad",
            error=str(e)
        )

read_scratchpad._tool_args = ReadScratchpadInput  # type: ignore[attr-defined]


@register_tool(name="create_todo", domain="agents", tags=["domain:agents"], status=VersionStatus.ACTIVE)
def create_todo(
    # Canonical fields (align with AgentTodo model)
    content: Optional[str] = None,
    priority: Optional[Union[str, int]] = None,
    status: Optional[str] = None,
    clinical_urgency: Optional[str] = None,
    # Convenience aliases (LLM-friendly fallbacks). Will be mapped to canonical fields
    task_description: Optional[str] = None,
    category: Optional[str] = None,
    due_date: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    messages: Optional[List[Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None,
    state: Optional[Dict[str, Any]] = None,
) -> HACSResult:
    """
    Create a todo item for agent task planning.
    
    Args:
        content: Actionable item content (preferred). If not provided, falls back to task_description.
        priority: Priority level as string (preferred) or int (will be coerced to string).
        status: Todo status (e.g., "pending", "in_progress", "completed"). Defaults to "pending".
        clinical_urgency: Clinical urgency level (e.g., "routine"). Optional.
        task_description: Deprecated alias for content. If provided and content is None, will be used.
        category: Deprecated; ignored.
        due_date: Optional due date (ISO format). Stored in clinical_context.
        context: Optional additional context info. Stored in clinical_context.
        
    Returns:
        HACSResult with created todo ID
    """
    try:
        # Resolve canonical fields
        resolved_content = content or task_description
        if not resolved_content:
            return HACSResult(
                success=False,
                message="Failed to create todo",
                error="Missing required field: content"
            )

        # Coerce priority to string as required by AgentTodo
        if priority is None:
            resolved_priority = "medium"
        else:
            resolved_priority = str(priority)

        resolved_status = status or "pending"

        # Build clinical context payload and include legacy fields for traceability
        clinical_context: Dict[str, Any] = {}
        if context:
            clinical_context.update(context)
        if due_date:
            clinical_context["due_date"] = due_date
        if category is not None:
            clinical_context["legacy_category"] = category

        # Create todo item aligned with AgentTodo
        todo = ScratchpadTodo(
            content=resolved_content,
            status=resolved_status,
            priority=resolved_priority,
            clinical_urgency=clinical_urgency or "routine",
            clinical_context=clinical_context,
        )
        
        return HACSResult(
            success=True,
            message="Successfully created todo item",
            data={
                "todo_id": todo.id,
                "content": resolved_content,
                "priority": resolved_priority,
                "status": resolved_status,
            }
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message="Failed to create todo",
            error=str(e)
        )

create_todo._tool_args = CreateTodoInput  # type: ignore[attr-defined]


@register_tool(name="list_todos", domain="agents", tags=["domain:agents"], status=VersionStatus.ACTIVE)
def list_todos(
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority_min: Optional[int] = None,
    limit: int = 20,
    messages: Optional[List[Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None,
    state: Optional[Dict[str, Any]] = None,
) -> HACSResult:
    """
    List agent todo items with optional filtering.
    
    Args:
        status: Optional status filter ("pending", "in_progress", "completed")
        category: Optional category filter
        priority_min: Optional minimum priority level
        limit: Maximum number of todos to return
        
    Returns:
        HACSResult with filtered todo list
    """
    try:
        # In a real implementation, this would query persistent storage
        # For now, return sample todos
        todos = []
        
        # This would be replaced with actual todo storage query
        sample_todos = [
            {
                "id": str(uuid.uuid4()),
                "task_description": "Review patient records",
                "priority": 7,
                "category": "clinical",
                "status": "pending",
                "created_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "task_description": "Update medication list",
                "priority": 5,
                "category": "documentation",
                "status": "in_progress",
                "created_at": datetime.now().isoformat()
            }
        ]
        
        # Apply filters
        filtered_todos = sample_todos
        if status:
            filtered_todos = [t for t in filtered_todos if t["status"] == status]
        if category:
            filtered_todos = [t for t in filtered_todos if t["category"] == category]
        if priority_min:
            filtered_todos = [t for t in filtered_todos if t["priority"] >= priority_min]
            
        todos = filtered_todos[:limit]
        
        return HACSResult(
            success=True,
            message=f"Retrieved {len(todos)} todo items",
            data={"todos": todos}
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message="Failed to list todos",
            error=str(e)
        )

list_todos._tool_args = ListTodosInput  # type: ignore[attr-defined]


@register_tool(name="complete_todo", domain="agents", tags=["domain:agents"], status=VersionStatus.ACTIVE)
def complete_todo(todo_id: str, completion_notes: Optional[str] = None, messages: Optional[List[Dict[str, Any]]] = None, config: Optional[Dict[str, Any]] = None, state: Optional[Dict[str, Any]] = None) -> HACSResult:
    """
    Mark a todo item as completed.
    
    Args:
        todo_id: ID of the todo item to complete
        completion_notes: Optional notes about completion
        
    Returns:
        HACSResult with completion confirmation
    """
    try:
        # In a real implementation, this would update persistent storage
        # For now, return success
        
        return HACSResult(
            success=True,
            message="Successfully completed todo item",
            data={
                "todo_id": todo_id,
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "completion_notes": completion_notes
            }
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message="Failed to complete todo",
            error=str(e)
        )

complete_todo._tool_args = CompleteTodoInput  # type: ignore[attr-defined]


@register_tool(name="store_memory", domain="agents", tags=["domain:agents"], status=VersionStatus.ACTIVE)
def store_memory(
    content: str,
    memory_type: str = "episodic",
    actor_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
    messages: Optional[List[Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None,
    state: Optional[Dict[str, Any]] = None,
) -> HACSResult:
    """
    Store a memory for long-term agent context.
    
    Args:
        content: Memory content
        memory_type: Type of memory ("episodic", "procedural", "semantic")
        actor_id: Optional actor ID associated with memory
        context: Optional context information
        tags: Optional tags for categorization
        
    Returns:
        HACSResult with stored memory ID
    """
    try:
        # Create memory entry
        memory_entry = {
            "id": str(uuid.uuid4()),
            "content": content,
            "memory_type": memory_type,
            "actor_id": actor_id,
            "context": context or {},
            "tags": tags or [],
            "created_at": datetime.now().isoformat()
        }
        
        # In a real implementation, this would be stored persistently
        # and potentially indexed for semantic search
        
        return HACSResult(
            success=True,
            message="Successfully stored memory",
            data={
                "memory_id": memory_entry["id"],
                "memory_type": memory_type,
                "content_preview": content[:100] + "..." if len(content) > 100 else content
            }
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message="Failed to store memory",
            error=str(e)
        )

store_memory._tool_args = StoreMemoryInput  # type: ignore[attr-defined]


@register_tool(name="retrieve_memories", domain="agents", tags=["domain:agents"], status=VersionStatus.ACTIVE)
def retrieve_memories(
    query: Optional[str] = None,
    actor_id: Optional[str] = None,
    memory_type: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 10,
    messages: Optional[List[Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None,
    state: Optional[Dict[str, Any]] = None,
) -> HACSResult:
    """
    Retrieve relevant memories based on query and context.
    
    Args:
        query: Optional semantic query for memory retrieval
        actor_id: Optional actor ID to filter memories
        memory_type: Optional memory type filter
        tags: Optional tags to filter by
        limit: Maximum number of memories to return
        
    Returns:
        HACSResult with retrieved memories
    """
    try:
        # Use memory utilities for retrieval
        filters = {}
        if actor_id:
            filters["actor_id"] = actor_id
        if memory_type:
            filters["memory_type"] = memory_type
        if tags:
            filters["tags"] = tags
        
        # Gather memories using utility functions
        raw_memories = gather_memories(
            query=query,
            filters=filters,
            limit=limit
        )
        
        # Merge and filter memories
        merged_memories = merge_memories(raw_memories)
        filtered_memories = filter_memories(
            merged_memories,
            relevance_threshold=0.5,
            max_memories=limit
        )
        
        return HACSResult(
            success=True,
            message=f"Retrieved {len(filtered_memories)} memories",
            data={"memories": filtered_memories}
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message="Failed to retrieve memories",
            error=str(e)
        )

retrieve_memories._tool_args = RetrieveMemoriesInput  # type: ignore[attr-defined]


@register_tool(name="inject_preferences", domain="agents", tags=["domain:agents"], status=VersionStatus.ACTIVE)
def inject_preferences(
    message: Dict[str, Any],
    actor_id: str,
    preference_scope: str = "response_format",
    messages: Optional[List[Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None,
    state: Optional[Dict[str, Any]] = None,
) -> HACSResult:
    """
    Inject actor preferences into a message or context.
    
    Args:
        message: Message object to inject preferences into
        actor_id: Actor ID to get preferences for
        preference_scope: Scope of preferences to inject
        
    Returns:
        HACSResult with preference-injected message
    """
    try:
        # Merge preferences for the actor
        preferences = merge_preferences(
            actor_id=actor_id,
            scope=preference_scope
        )
        
        # Create message definition
        message_def = MessageDefinition(**message)
        
        # Inject preferences
        injected_message = _inject_preferences(message_def, preferences)
        
        return HACSResult(
            success=True,
            message="Successfully injected preferences",
            data={
                "message": injected_message.model_dump(),
                "preferences_applied": len(preferences),
                "scope": preference_scope
            }
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message="Failed to inject preferences",
            error=str(e)
        )

inject_preferences._tool_args = InjectPreferencesInput  # type: ignore[attr-defined]


@register_tool(name="select_tools_for_task", domain="agents", tags=["domain:agents"], status=VersionStatus.ACTIVE)
def select_tools_for_task(
    task_description: str,
    max_tools: int = 10,
    domain_filter: Optional[str] = None,
    exclude_tools: Optional[List[str]] = None,
    messages: Optional[List[Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None,
    state: Optional[Dict[str, Any]] = None,
) -> HACSResult:
    """
    Select relevant tools for a task using semantic tool loadout.
    
    Args:
        task_description: Description of the task to select tools for
        max_tools: Maximum number of tools to select
        domain_filter: Optional domain to filter tools by
        exclude_tools: Optional list of tool names to exclude
        
    Returns:
        HACSResult with selected tools
    """
    try:
        # Use semantic tool loadout
        selected_tools = semantic_tool_loadout(
            query=task_description,
            max_tools=max_tools,
            domain_filter=domain_filter
        )
        
        # Apply exclusions
        if exclude_tools:
            selected_tools = [
                tool for tool in selected_tools 
                if tool.get("name") not in exclude_tools
            ]
        
        return HACSResult(
            success=True,
            message=f"Selected {len(selected_tools)} tools for task",
            data={
                "tools": selected_tools,
                "task_description": task_description,
                "selection_method": "semantic"
            }
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message="Failed to select tools",
            error=str(e)
        )

select_tools_for_task._tool_args = SelectToolsForTaskInput  # type: ignore[attr-defined]


@register_tool(name="summarize_state", domain="agents", tags=["domain:agents"], status=VersionStatus.ACTIVE)
def summarize_state(
    state_data: Dict[str, Any],
    focus_areas: Optional[List[str]] = None,
    compression_ratio: float = 0.3,
    messages: Optional[List[Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None,
    state: Optional[Dict[str, Any]] = None,
) -> HACSResult:
    """
    Summarize agent state for context compression.
    
    Args:
        state_data: Current agent state to summarize
        focus_areas: Optional areas to focus on in summary
        compression_ratio: Target compression ratio (0.1-1.0)
        
    Returns:
        HACSResult with state summary
    """
    try:
        # Extract key components from state
        key_components = []
        
        # Extract messages if present
        if "messages" in state_data:
            messages = state_data["messages"]
            key_components.append(f"Message history: {len(messages)} messages")
            
        # Extract tools if present
        if "tools" in state_data:
            tools = state_data["tools"]
            key_components.append(f"Available tools: {len(tools)} tools")
            
        # Extract context if present
        if "context" in state_data:
            context = state_data["context"]
            key_components.append(f"Context: {str(context)[:200]}...")
        
        # Focus on specific areas if requested
        if focus_areas:
            focused_components = []
            for area in focus_areas:
                if area in state_data:
                    focused_components.append(f"{area}: {str(state_data[area])[:100]}...")
            if focused_components:
                key_components.extend(focused_components)
        
        # Create summary
        summary = {
            "key_components": key_components,
            "state_size": len(str(state_data)),
            "compression_applied": compression_ratio,
            "summary_created_at": datetime.now().isoformat()
        }
        
        return HACSResult(
            success=True,
            message="Successfully summarized agent state",
            data={"summary": summary}
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message="Failed to summarize state",
            error=str(e)
        )

summarize_state._tool_args = SummarizeStateInput  # type: ignore[attr-defined]


@register_tool(name="prune_state", domain="agents", tags=["domain:agents"], status=VersionStatus.ACTIVE)
def prune_state(
    state_data: Dict[str, Any],
    keep_fields: Optional[List[str]] = None,
    max_messages: int = 20,
    max_tools: int = 30,
    messages: Optional[List[Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None,
    state: Optional[Dict[str, Any]] = None,
) -> HACSResult:
    """
    Prune agent state by removing low-priority elements.
    
    Args:
        state_data: Current agent state to prune
        keep_fields: Fields that should always be kept
        max_messages: Maximum number of messages to keep
        max_tools: Maximum number of tools to keep
        
    Returns:
        HACSResult with pruned state
    """
    try:
        pruned_state = {}
        
        # Always keep specified fields
        if keep_fields:
            for field in keep_fields:
                if field in state_data:
                    pruned_state[field] = state_data[field]
        
        # Prune messages (keep most recent)
        if "messages" in state_data:
            messages = state_data["messages"]
            if len(messages) > max_messages:
                pruned_state["messages"] = messages[-max_messages:]
            else:
                pruned_state["messages"] = messages
        
        # Prune tools (keep highest priority)
        if "tools" in state_data:
            tools = state_data["tools"]
            if len(tools) > max_tools:
                # Sort by priority if available, otherwise keep first N
                if isinstance(tools, list) and tools and isinstance(tools[0], dict):
                    sorted_tools = sorted(
                        tools,
                        key=lambda t: t.get("priority", 5),
                        reverse=True
                    )
                    pruned_state["tools"] = sorted_tools[:max_tools]
                else:
                    pruned_state["tools"] = tools[:max_tools]
            else:
                pruned_state["tools"] = tools
        
        # Keep other essential fields
        essential_fields = ["actor_id", "session_id", "current_task", "context"]
        for field in essential_fields:
            if field in state_data and field not in pruned_state:
                pruned_state[field] = state_data[field]
        
        return HACSResult(
            success=True,
            message="Successfully pruned agent state",
            data={
                "pruned_state": pruned_state,
                "original_size": len(str(state_data)),
                "pruned_size": len(str(pruned_state)),
                "compression_ratio": len(str(pruned_state)) / len(str(state_data)) if state_data else 1
            }
        )
        
    except Exception as e:
        return HACSResult(
            success=False,
            message="Failed to prune state",
            error=str(e)
        )

prune_state._tool_args = PruneStateInput  # type: ignore[attr-defined]


# Export canonical tool names (without _tool suffix)
__all__ = [
    "write_scratchpad",
    "read_scratchpad",
    "create_todo",
    "list_todos", 
    "complete_todo",
    "store_memory",
    "retrieve_memories",
    "inject_preferences",
    "select_tools_for_task",
    "summarize_state",
    "prune_state"
]
