"""State definitions for HACS Agent.

State management for HACS development and administration workflows.
Includes planning tools, file system, and task tracking.
"""

from typing import Any, Dict, List, Optional, Literal, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class Todo(TypedDict):
    """Todo item for tracking admin tasks."""
    content: str
    status: Literal["pending", "in_progress", "completed"]


class AdminOperationResult(BaseModel):
    """Result of an admin operation for the developer."""
    operation_type: str = Field(description="Type of admin operation performed")
    success: bool = Field(description="Whether the operation succeeded")
    message: str = Field(description="Human-readable result message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Operation result data")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class HACSAgentState(TypedDict, total=False):
    """Agent state for HACS operations.
    
    Core state management for HACS development and administration workflows.
    """
    
    # Core LangGraph state (required fields)
    messages: Annotated[list[AnyMessage], add_messages]
    remaining_steps: int  # Required by create_react_agent
    
    # Agent Framework Components (optional with total=False)
    todos: List[Todo]
    files: Dict[str, str]
    
    # HACS-Specific State (optional with total=False)
    session_id: str
    database_url: str
    last_operation_result: AdminOperationResult
    admin_context: Dict[str, Any]
    delegation_depth: int  # For sub-agent recursion prevention


# Alias for backward compatibility
HACSDeepAgentState = HACSAgentState
