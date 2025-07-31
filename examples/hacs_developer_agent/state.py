"""State definitions for HACS Deep Admin Agent.

Built on the deep agents framework with HACS-specific admin functionality.
Includes planning tools, file system, and specialized sub-agents.
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


class HACSDeepAgentState(TypedDict, total=False):
    """Deep agent state for HACS admin operations.
    
    Following deepagents framework pattern with proper LangGraph message handling.
    """
    
    # Core LangGraph state (required fields)
    messages: Annotated[list[AnyMessage], add_messages]
    remaining_steps: int  # Required by create_react_agent
    
    # Deep Agent Framework Components (optional with total=False)
    todos: List[Todo]
    files: Dict[str, str]
    
    # HACS Admin-Specific State (optional with total=False)
    session_id: str
    database_url: str
    last_operation_result: AdminOperationResult
    admin_context: Dict[str, Any]
