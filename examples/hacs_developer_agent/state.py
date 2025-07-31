"""State definitions for HACS Deep Admin Agent.

Built on the deep agents framework with HACS-specific admin functionality.
Includes planning tools, file system, and specialized sub-agents.
"""

from typing import Any, Dict, List, Optional, Literal, Annotated, NotRequired
from typing_extensions import TypedDict

from langgraph.graph import MessagesState
from langgraph.prebuilt.chat_agent_executor import AgentState
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


def file_reducer(left, right):
    """Reducer for file system state."""
    if left is None:
        return right
    elif right is None:
        return left
    else:
        return {**left, **right}


class HACSDeepAgentState(AgentState):
    """Deep agent state for HACS admin operations.

    Extends LangGraph's AgentState with HACS-specific admin functionality:
    - Planning through todos
    - File system for configs/scripts
    - Admin operation tracking
    - Sub-agent coordination

    Inherits from AgentState to ensure compatibility with create_react_agent.
    """

    # Deep Agent Framework Components
    todos: NotRequired[List[Todo]]
    files: Annotated[NotRequired[Dict[str, str]], file_reducer]

    # HACS Admin-Specific State (all optional)
    session_id: NotRequired[Optional[str]]
    database_url: NotRequired[Optional[str]]
    last_operation_result: NotRequired[Optional[AdminOperationResult]]
    admin_context: NotRequired[Optional[Dict[str, Any]]]


# Simplified input/output states for external API
class InputState(MessagesState):
    """Input state for HACS Deep Admin Agent - what developers provide."""

    admin_operation_type: Optional[str] = Field(
        default=None,
        description="Type of admin operation requested"
    )

    operation_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Parameters for the admin operation"
    )

    database_url: Optional[str] = Field(
        default=None,
        description="Database URL (optional, can use environment variable)"
    )


class OutputState(MessagesState):
    """Output state for admin operations - what developers get back."""

    operation_result: AdminOperationResult = Field(
        description="Result of the admin operation"
    )

    todos_completed: Optional[List[str]] = Field(
        default=None,
        description="List of completed admin tasks"
    )

    files_created: Optional[List[str]] = Field(
        default=None,
        description="List of files created during operation"
    )

    recommended_next_steps: Optional[List[str]] = Field(
        default=None,
        description="Suggested next admin actions"
    )