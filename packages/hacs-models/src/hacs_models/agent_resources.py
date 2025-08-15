from __future__ import annotations

"""
Agent-facing HACS resources for tasks and working memory.

Canonical, concise names with compatibility aliases for legacy imports.
"""

from typing import Any, Dict, List, Optional, Literal
from datetime import datetime
from pydantic import Field, model_validator

from .base_resource import BaseResource


class AgentTodo(BaseResource):
    """Lightweight actionable item for agent workflows."""

    resource_type: Literal["AgentTodo"] = Field(default="AgentTodo")

    content: str = Field(description="Actionable item content")
    status: str = Field(default="pending", description="Todo status")
    priority: str = Field(default="medium", description="Priority level")
    clinical_urgency: str = Field(default="routine", description="Clinical urgency")

    assigned_actor: Optional[str] = Field(default=None, description="Responsible agent/user")
    patient_id: Optional[str] = Field(default=None, description="Associated patient ID")
    encounter_id: Optional[str] = Field(default=None, description="Associated encounter ID")

    estimated_duration_minutes: Optional[int] = Field(default=None)
    required_permissions: List[str] = Field(default_factory=list)
    clinical_context: Dict[str, Any] = Field(default_factory=dict)

    due_date: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    notes: Optional[str] = Field(default=None, description="Additional notes (<=1000 chars)", max_length=1000)

    @model_validator(mode="before")
    @classmethod
    def _coerce_enums(cls, values):  # type: ignore[override]
        if isinstance(values, dict):
            for k in ("status", "priority", "clinical_urgency"):
                v = values.get(k)
                if hasattr(v, "value"):
                    values[k] = getattr(v, "value")
        return values


class ScratchpadEntry(BaseResource):
    """Generic working-memory entry for agent reasoning."""

    resource_type: Literal["ScratchpadEntry"] = Field(default="ScratchpadEntry")

    entry_type: str = Field(description="Type of entry, e.g., observation, plan, note")
    content: str = Field(description="Entry content")
    agent_id: str = Field(description="ID of the creating agent")

    context_reference: Optional[str] = Field(default=None, description="Related resource reference")
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentTask(BaseResource):
    """Structured task definition with parameters and lifecycle."""

    resource_type: Literal["AgentTask"] = Field(default="AgentTask")

    task_name: str = Field(description="Task name/title")
    task_type: str = Field(description="Task type/category")
    description: str = Field(description="Detailed task description")

    status: str = Field(default="pending", description="Task status")
    priority: str = Field(default="medium", description="Task priority")

    assigned_agent: Optional[str] = Field(default=None, description="Assigned agent/user")
    input_parameters: Dict[str, Any] = Field(default_factory=dict)
    expected_output: Optional[Dict[str, Any]] = Field(default=None)
    execution_context: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)

    estimated_duration_minutes: Optional[int] = Field(default=None)
    max_retries: int = Field(default=3)

    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)

    @model_validator(mode="before")
    @classmethod
    def _coerce_enums(cls, values):  # type: ignore[override]
        if isinstance(values, dict):
            for k in ("status", "priority"):
                v = values.get(k)
                if hasattr(v, "value"):
                    values[k] = getattr(v, "value")
        return values


# ---------------------------------------------------------------------------
# Compatibility aliases for legacy names
# ---------------------------------------------------------------------------

ScratchpadTodo = AgentTodo
AgentScratchpadEntry = ScratchpadEntry


