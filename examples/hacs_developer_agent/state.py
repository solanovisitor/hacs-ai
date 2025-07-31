"""State definitions for HACS Admin Agent.

Simplified state focused on developer interaction only.
Internal operation details are handled privately by the agent.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from langgraph.graph import MessagesState
from pydantic import BaseModel, Field


class AdminOperationResult(BaseModel):
    """Result of an admin operation for the developer."""
    operation_type: str = Field(description="Type of admin operation performed")
    success: bool = Field(description="Whether the operation succeeded")
    message: str = Field(description="Human-readable result message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Operation result data")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class InputState(MessagesState):
    """Input state for HACS Admin Agent - what developers provide."""

    admin_operation_type: Optional[str] = Field(
        default=None,
        description="Type of admin operation requested (migration, schema, resource, etc.)"
    )

    operation_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Parameters for the admin operation"
    )

    database_url: Optional[str] = Field(
        default=None,
        description="Database URL (optional, can use environment variable)"
    )


class State(MessagesState):
    """Main state for HACS Admin Agent - conversation and results only."""

    # Only store what's relevant to the developer conversation
    session_id: Optional[str] = Field(
        default=None,
        description="Session identifier for conversation tracking"
    )

    last_operation_result: Optional[AdminOperationResult] = Field(
        default=None,
        description="Result of the most recent admin operation"
    )

    # Simple error tracking for conversation context
    last_error: Optional[str] = Field(
        default=None,
        description="Last error for conversation context"
    )


class OutputState(MessagesState):
    """Output state for admin operations - what developers get back."""

    operation_result: AdminOperationResult = Field(
        description="Result of the admin operation"
    )

    recommended_next_steps: Optional[List[str]] = Field(
        default=None,
        description="Suggested next admin actions"
    )