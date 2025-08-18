"""
HACS SubAgent Framework - DeepAgents Pattern (Shared)

Generic subagent task delegation tool and types so apps/agents can just consume it.
"""

from typing import List, Dict, Any, Annotated
from typing_extensions import TypedDict, NotRequired

from langchain_core.tools import tool, BaseTool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langgraph.prebuilt import create_react_agent, InjectedState

# We do not depend on example-local prompts; define concise defaults
TASK_DESCRIPTION_PREFIX = (
    "Delegate a task to a specialized subagent.\n\n"
    "Available specialists:\n{other_agents}\n\n"
    "Pick the most suitable specialist based on the task."
)

TASK_DESCRIPTION_SUFFIX = (
    "\n\nProvide a clear description and choose the specialist name. "
    "The specialist will run with its focused toolset and return results to the main flow."
)

# Built-in guidance for delegation and registry-first modeling
DEFAULT_SUBAGENT_DELEGATION_GUIDE = (
    "\n\nDelegation guidance (HACS):\n"
    "- modeling_planner: plan schemas, sections, variables, references.\n"
    "- resource_template_creator: register definitions with register_resource_definition.\n"
    "- resource_bundle_builder: if building example bundles, validate with validate_bundle and persist via save_record.\n\n"
    "Rules for document templates:\n"
    "- Prefer register_resource_definition for templates; only use compose_bundle for instance bundles.\n"
    "- Pass instance_data as a JSON object (not a string).\n"
    "- On validation error, correct once using only required field names/types.\n"
)


class HACSSubAgent(TypedDict):
    """HACS SubAgent configuration following DeepAgents pattern."""

    name: str
    description: str
    prompt: str
    tools: NotRequired[List[str]]


def _create_task_tool(
    tools, instructions: str, subagents: List[HACSSubAgent], model, state_schema
):
    """Create task delegation tool for HACS subagents."""

    # Create main agent
    agents = {
        "general-purpose": create_react_agent(
            model, prompt=instructions, tools=tools, state_schema=state_schema
        )
    }

    # Index tools by name
    tools_by_name: Dict[str, BaseTool] = {}
    for tool_ in tools:
        if not isinstance(tool_, BaseTool):
            tool_ = tool(tool_)  # type: ignore
        tools_by_name[tool_.name] = tool_  # type: ignore[attr-defined]

    # Create specialized subagents
    for subagent in subagents:
        if "tools" in subagent:
            _tools = [tools_by_name[t] for t in subagent["tools"] if t in tools_by_name]
        else:
            _tools = tools

        agents[subagent["name"]] = create_react_agent(
            model, prompt=subagent["prompt"], tools=_tools, state_schema=state_schema
        )

    # Create description of available subagents
    other_agents_string = [
        f"- {subagent['name']}: {subagent['description']}" for subagent in subagents
    ]

    @tool(
        description=(
            TASK_DESCRIPTION_PREFIX.format(other_agents=other_agents_string)
            + DEFAULT_SUBAGENT_DELEGATION_GUIDE
            + TASK_DESCRIPTION_SUFFIX
        )
    )
    def task(
        description: str,
        subagent_type: str,
        state: Annotated[dict, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ):
        """Delegate a task to a specialized HACS subagent."""

        if subagent_type not in agents:
            return (
                f"Error: invoked agent of type {subagent_type}, the only allowed types are "
                f"{[f'`{k}`' for k in agents]}"
            )

        # Get the subagent
        sub_agent = agents[subagent_type]

        # Prepare state for subagent
        subagent_state = dict(state)
        subagent_state["messages"] = [{"role": "user", "content": description}]

        try:
            # Execute with subagent
            result = sub_agent.invoke(subagent_state)

            # Extract response content
            response_content = "Task completed successfully."
            if result.get("messages"):
                last_message = result["messages"][-1]
                if hasattr(last_message, "content"):
                    response_content = last_message.content  # type: ignore[attr-defined]
                elif isinstance(last_message, dict) and "content" in last_message:
                    response_content = last_message["content"]

            # Update state with subagent results
            updates: Dict[str, Any] = {
                "messages": [ToolMessage(response_content, tool_call_id=tool_call_id)]
            }

            # Merge any state updates from subagent
            if result.get("admin_tasks"):
                updates["admin_tasks"] = result["admin_tasks"]
            if result.get("system_status"):
                updates["system_status"] = result["system_status"]
            if result.get("audit_trail"):
                updates["audit_trail"] = result["audit_trail"]

            return Command(update=updates)

        except Exception as e:
            error_message = f"❌ Task delegation to {subagent_type} failed: {str(e)}"
            return Command(
                update={
                    "messages": [ToolMessage(error_message, tool_call_id=tool_call_id)]
                }
            )

    return task


__all__ = ["HACSSubAgent", "_create_task_tool", "TASK_DESCRIPTION_PREFIX", "TASK_DESCRIPTION_SUFFIX"]


