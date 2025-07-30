"""
Human-in-the-Loop (HIL) utilities for HACS LangGraph agents.

This module provides reusable abstractions for implementing human interrupts
and interactions in LangGraph workflows, specifically designed for healthcare
agent interactions with HACS resources.
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from langgraph.types import Command, interrupt


class HACSResourceAction(BaseModel):
    """Represents a CRUD action on a HACS resource."""

    action: Literal["create", "read", "update", "delete", "search"] = Field(
        description="Type of CRUD operation to perform"
    )
    resource_type: str = Field(
        description="Type of HACS resource (e.g., 'Patient', 'Observation')"
    )
    resource_id: Optional[str] = Field(
        default=None, description="Resource ID for read/update/delete operations"
    )
    resource_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Resource data for create/update operations"
    )
    search_filters: Optional[Dict[str, Any]] = Field(
        default=None, description="Search filters for search operations"
    )
    reason: str = Field(
        description="Human-readable reason for this action"
    )
    impact_assessment: str = Field(
        description="Assessment of what this action will affect"
    )


class HACSUserConfirmation(BaseModel):
    """User confirmation response for HACS operations."""

    approved: bool = Field(description="Whether the user approved the action")
    feedback: Optional[str] = Field(
        default=None, description="Optional user feedback or modifications"
    )
    modified_action: Optional[HACSResourceAction] = Field(
        default=None, description="Modified action if user requested changes"
    )


class HACSHumanInput(BaseModel):
    """General human input request for HACS workflows."""

    prompt: str = Field(description="Question or prompt for the human")
    input_type: Literal["confirmation", "clarification", "data_input", "decision"] = Field(
        description="Type of input being requested"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Additional context for the prompt"
    )
    options: Optional[List[str]] = Field(
        default=None, description="Available options for multiple choice questions"
    )
    required: bool = Field(
        default=True, description="Whether this input is required to continue"
    )


def request_resource_confirmation(
    action: HACSResourceAction,
    additional_context: Optional[Dict[str, Any]] = None
) -> HACSUserConfirmation:
    """
    Request human confirmation for a sensitive HACS resource operation.

    This function creates a human interrupt that asks for explicit confirmation
    before performing potentially sensitive CRUD operations on healthcare data.

    Args:
        action: The HACS resource action to confirm
        additional_context: Optional additional context for the confirmation

    Returns:
        User confirmation response
    """
    # Create a detailed confirmation prompt
    prompt = f"""🏥 **HACS Resource Operation Confirmation Required**

**Action**: {action.action.upper()} {action.resource_type}
**Reason**: {action.reason}
**Impact**: {action.impact_assessment}

"""

    if action.resource_id:
        prompt += f"**Resource ID**: `{action.resource_id}`\n"

    if action.resource_data:
        prompt += f"**Data**: {_format_resource_data(action.resource_data)}\n"

    if action.search_filters:
        prompt += f"**Search Filters**: {action.search_filters}\n"

    if additional_context:
        prompt += f"\n**Additional Context**: {additional_context}\n"

    prompt += """
**⚠️ This operation will modify healthcare data. Please review carefully.**

Do you want to proceed? (yes/no)
You can also provide feedback or request modifications.
"""

    # Request human input using LangGraph's interrupt mechanism
    response = interrupt(prompt)

    # Parse the response
    if isinstance(response, str):
        response_lower = response.lower().strip()
        if response_lower in ['yes', 'y', 'approve', 'confirmed', 'proceed']:
            return HACSUserConfirmation(approved=True)
        elif response_lower in ['no', 'n', 'deny', 'cancel', 'abort']:
            return HACSUserConfirmation(approved=False)
        else:
            # Treat as feedback
            return HACSUserConfirmation(approved=False, feedback=response)

    # Handle structured response
    if isinstance(response, dict):
        return HACSUserConfirmation(**response)

    # Default to not approved for safety
    return HACSUserConfirmation(approved=False, feedback=str(response))


def request_human_clarification(
    question: str,
    context: Optional[Dict[str, Any]] = None,
    options: Optional[List[str]] = None,
    required: bool = True
) -> str:
    """
    Request clarification from a human user during agent execution.

    Args:
        question: The question to ask the human
        context: Optional context information
        options: Optional list of predefined options
        required: Whether the input is required to continue

    Returns:
        Human response as a string
    """
    prompt = "❓ **Clarification Needed**\n\n" + question + "\n"

    if context:
        prompt += f"\n**Context**: {context}\n"

    if options:
        prompt += "\n**Options**:\n"
        for i, option in enumerate(options, 1):
            prompt += f"{i}. {option}\n"

    if not required:
        prompt += "\n*Note: You can skip this by typing 'skip' or leaving empty.*"

    response = interrupt(prompt)
    return str(response) if response is not None else ""


def request_data_input(
    field_name: str,
    field_type: str,
    description: str,
    required: bool = True,
    validation_rules: Optional[List[str]] = None
) -> Any:
    """
    Request specific data input from a human user.

    Args:
        field_name: Name of the field being requested
        field_type: Type of data expected (string, number, date, etc.)
        description: Description of what this field represents
        required: Whether this field is required
        validation_rules: Optional validation rules to display

    Returns:
        User input, type-converted based on field_type
    """
    prompt = "📝 **Data Input Required**\n\n"
    prompt += f"**Field**: {field_name}\n"
    prompt += f"**Type**: {field_type}\n"
    prompt += f"**Description**: {description}\n"

    if validation_rules:
        prompt += "\n**Validation Rules**:\n"
        for rule in validation_rules:
            prompt += f"• {rule}\n"

    if required:
        prompt += "\n**⚠️ This field is required to continue.**"

    prompt += f"\nPlease enter the {field_name}:"

    response = interrupt(prompt)

    # Type conversion based on field_type
    if field_type.lower() in ['int', 'integer', 'number']:
        try:
            return int(response)
        except (ValueError, TypeError):
            return response
    elif field_type.lower() in ['float', 'decimal']:
        try:
            return float(response)
        except (ValueError, TypeError):
            return response
    elif field_type.lower() in ['bool', 'boolean']:
        if isinstance(response, str):
            return response.lower() in ['true', 'yes', 'y', '1', 'on']
        return bool(response)

    return str(response) if response is not None else ""


def create_approval_workflow_node(
    action: HACSResourceAction,
    context: Optional[Dict[str, Any]] = None
):
    """
    Create a LangGraph node function for resource approval workflow.

    This creates a reusable node that can be added to any LangGraph workflow
    to request human approval for HACS resource operations.

    Args:
        action: The resource action to approve
        context: Optional additional context

    Returns:
        A function that can be used as a LangGraph node
    """
    def approval_node(state):
        """LangGraph node for human approval of HACS resource operations."""
        print("---🏥 HACS Resource Approval Required---")

        # Store the action in state for later reference
        approval_state = {
            "pending_action": action.model_dump(),
            "approval_context": context
        }

        # Request confirmation
        confirmation = request_resource_confirmation(action, context)

        # Create response based on approval
        if confirmation.approved:
            print("✅ Action approved by user")
            return {
                "approval_result": "approved",
                "approved_action": action.model_dump(),
                "user_feedback": confirmation.feedback,
                **approval_state
            }
        else:
            print("❌ Action denied by user")
            return {
                "approval_result": "denied",
                "denied_action": action.model_dump(),
                "user_feedback": confirmation.feedback,
                "modified_action": (
                    confirmation.modified_action.model_dump()
                    if confirmation.modified_action else None
                ),
                **approval_state
            }

    return approval_node


def create_human_input_node(
    input_request: HACSHumanInput
):
    """
    Create a LangGraph node function for general human input.

    Args:
        input_request: The human input request configuration

    Returns:
        A function that can be used as a LangGraph node
    """
    def human_input_node(state):
        """LangGraph node for requesting human input."""
        print(f"---❓ Human Input Required: {input_request.input_type}---")

        if input_request.input_type == "confirmation":
            response = request_human_clarification(
                input_request.prompt,
                input_request.context,
                input_request.options,
                input_request.required
            )
            return {"human_response": response, "input_type": "confirmation"}

        elif input_request.input_type == "clarification":
            response = request_human_clarification(
                input_request.prompt,
                input_request.context,
                input_request.options,
                input_request.required
            )
            return {"human_response": response, "input_type": "clarification"}

        elif input_request.input_type == "data_input":
            # For data input, we expect specific field information in context
            field_info = input_request.context
            response = request_data_input(
                field_info.get("field_name", "input"),
                field_info.get("field_type", "string"),
                input_request.prompt,
                input_request.required,
                field_info.get("validation_rules")
            )
            return {"human_input": response, "input_type": "data_input"}

        else:  # decision
            response = request_human_clarification(
                input_request.prompt,
                input_request.context,
                input_request.options,
                input_request.required
            )
            return {"human_decision": response, "input_type": "decision"}

    return human_input_node


def _format_resource_data(data: Dict[str, Any]) -> str:
    """Format resource data for human-readable display."""
    if not data:
        return "No data"

    formatted = "```json\n"
    import json
    formatted += json.dumps(data, indent=2, default=str)
    formatted += "\n```"
    return formatted


# Utility functions for common patterns
def create_crud_interrupt_routing(state) -> str:
    """
    Routing function to determine if CRUD operations need human approval.

    Returns:
        - "human_approval" if action needs approval
        - "execute_directly" if action can proceed without approval
    """
    # Check if there's a pending action that needs approval
    pending_action = state.get("pending_crud_action")

    if not pending_action:
        return "execute_directly"

    action_type = pending_action.get("action", "").lower()
    resource_type = pending_action.get("resource_type", "").lower()

    # Define actions that always require approval
    high_risk_actions = ["delete", "update"]
    sensitive_resources = ["patient", "medication", "diagnosis"]

    # Require approval for high-risk actions or sensitive resources
    if (action_type in high_risk_actions or
        resource_type in sensitive_resources or
        pending_action.get("requires_approval", False)):
        return "human_approval"

    return "execute_directly"


def resume_with_approval(approved: bool = True, feedback: str = "") -> Command:
    """
    Helper function to resume execution after human approval.

    Args:
        approved: Whether the action was approved
        feedback: Optional feedback from the human

    Returns:
        Command object to resume the graph execution
    """
    return Command(
        resume=HACSUserConfirmation(
            approved=approved,
            feedback=feedback if feedback else None
        ).model_dump()
    )