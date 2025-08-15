"""
HACS Workflow Tools

Thin adapters around hacs_models workflow resources. No embedded business logic.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from hacs_models import HACSResult
from hacs_models import (
    WorkflowActivityDefinition,
    WorkflowPlanDefinition,
    WorkflowPlanDefinitionAction,
    WorkflowTaskResource,
    WorkflowStatus,
    WorkflowActivityDefinitionKind,
)
from hacs_core.tool_protocols import hacs_tool, ToolCategory


@hacs_tool(
    name="create_activity_definition",
    description="Create a Workflow ActivityDefinition (adapter)",
    category=ToolCategory.CLINICAL_WORKFLOWS,
    domains=["workflows"]
)
def create_activity_definition(
    actor_name: str,
    name: str,
    title: Optional[str] = None,
    status: str = "active",
    kind: str = "task",
    code: Optional[str] = None,
    description: Optional[str] = None,
    purpose: Optional[str] = None,
    participants: Optional[List[Dict[str, Any]]] = None,
) -> HACSResult:
    try:
        wf_status = WorkflowStatus(status) if isinstance(status, str) else status
        wf_kind = WorkflowActivityDefinitionKind(kind.upper()) if isinstance(kind, str) else kind
        ad = WorkflowActivityDefinition(
            name=name,
            title=title,
            status=wf_status,
            kind=wf_kind,
            code=code,
            description=description,
            purpose=purpose,
            participant=(participants or []),
        )
        return HACSResult(success=True, message="ActivityDefinition created", data=ad.model_dump(), actor_id=actor_name)
    except Exception as e:
        return HACSResult(success=False, message="Failed to create ActivityDefinition", error=str(e), actor_id=actor_name)


@hacs_tool(
    name="create_plan_definition",
    description="Create a Workflow PlanDefinition (adapter)",
    category=ToolCategory.CLINICAL_WORKFLOWS,
    domains=["workflows"]
)
def create_plan_definition(
    actor_name: str,
    name: str,
    title: Optional[str] = None,
    status: str = "active",
    description: Optional[str] = None,
    type: Optional[str] = None,
    goals: Optional[List[Dict[str, Any]]] = None,
    actions: Optional[List[Dict[str, Any]]] = None,
) -> HACSResult:
    try:
        wf_status = WorkflowStatus(status) if isinstance(status, str) else status
        pd = WorkflowPlanDefinition(name=name, title=title, status=wf_status, description=description, type=type)
        for g in (goals or []):
            pd.add_goal(g.get("description", ""), g.get("category"), g.get("priority"))
        for a in (actions or []):
            pd.add_action(a.get("title"), a.get("code"), a.get("description"), a.get("definition_canonical"))
        return HACSResult(success=True, message="PlanDefinition created", data=pd.model_dump(), actor_id=actor_name)
    except Exception as e:
        return HACSResult(success=False, message="Failed to create PlanDefinition", error=str(e), actor_id=actor_name)


@hacs_tool(
    name="create_task_from_activity",
    description="Create a Task from an ActivityDefinition (adapter)",
    category=ToolCategory.CLINICAL_WORKFLOWS,
    domains=["workflows"]
)
def create_task_from_activity(
    actor_name: str,
    activity_definition: Dict[str, Any],
    subject: Optional[str] = None,
    requester: Optional[str] = None,
) -> HACSResult:
    try:
        ad = WorkflowActivityDefinition(**activity_definition)
        task = ad.create_task(subject=subject, requester=requester)
        return HACSResult(success=True, message="Task created", data=task.model_dump(), actor_id=actor_name)
    except Exception as e:
        return HACSResult(success=False, message="Failed to create Task", error=str(e), actor_id=actor_name)


@hacs_tool(
    name="complete_task",
    description="Complete a Task with outputs (adapter)",
    category=ToolCategory.CLINICAL_WORKFLOWS,
    domains=["workflows"]
)
def complete_task(actor_name: str, task: Dict[str, Any], outputs: Dict[str, Any]) -> HACSResult:
    try:
        t = WorkflowTaskResource(**task)
        t.complete(outputs)
        return HACSResult(success=True, message="Task completed", data=t.model_dump(), actor_id=actor_name)
    except Exception as e:
        return HACSResult(success=False, message="Failed to complete Task", error=str(e), actor_id=actor_name)


@hacs_tool(
    name="fail_task",
    description="Fail a Task with a message (adapter)",
    category=ToolCategory.CLINICAL_WORKFLOWS,
    domains=["workflows"]
)
def fail_task(actor_name: str, task: Dict[str, Any], error_message: str) -> HACSResult:
    try:
        t = WorkflowTaskResource(**task)
        t.fail(error_message)
        return HACSResult(success=True, message="Task failed", data=t.model_dump(), actor_id=actor_name)
    except Exception as e:
        return HACSResult(success=False, message="Failed to fail Task", error=str(e), actor_id=actor_name)


__all__ = [
    "create_activity_definition",
    "create_plan_definition",
    "create_task_from_activity",
    "complete_task",
    "fail_task",
]


