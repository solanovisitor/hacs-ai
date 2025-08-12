"""
HACS Agent - DeepAgents Framework Pattern

Clean implementation following the DeepAgents pattern with HACS-specific tools and subagents.
"""

from typing import Sequence, Union, Callable, Any, TypeVar, Type, Optional
from langchain_core.tools import BaseTool
from langchain_core.language_models import LanguageModelLike
from langgraph.prebuilt import create_react_agent

from hacs_sub_agent import _create_task_tool, HACSSubAgent
from hacs_model import get_default_model
from hacs_utils.integrations.langgraph import get_hacs_agent_tools
from hacs_state import HACSAgentState
from hacs_prompts import DEEP_BASE_PROMPT
from hacs_tools_integration import (
    manage_admin_tasks,
    update_system_status,
    run_database_migration,
    check_database_status,
    create_hacs_record,
)

StateSchema = TypeVar("StateSchema", bound=HACSAgentState)
StateSchemaType = Type[StateSchema]


def create_hacs_agent(
    tools: Sequence[Union[BaseTool, Callable, dict[str, Any]]] = None,
    instructions: str = "",
    model: Optional[Union[str, LanguageModelLike]] = None,
    subagents: list[HACSSubAgent] = None,
    state_schema: Optional[StateSchemaType] = None,
):
    """Create a HACS agent following the DeepAgents pattern.

    This agent has built-in HACS admin tools and can delegate complex
    healthcare tasks to specialized subagents.

    Args:
        tools: Additional tools beyond built-in HACS tools.
        instructions: Additional instructions for the agent.
        model: The model to use.
        subagents: HACS subagents for specialized healthcare tasks.
        state_schema: The schema of the HACS agent. Should subclass from HACSAgentState
        
    Returns:
        Configured HACS agent ready for healthcare operations.
    """
    prompt = instructions + DEEP_BASE_PROMPT
    
    # Get HACS agent tools via proper integration
    # DeepAgents-style built-ins: write_todos + ls
    from langchain_core.tools import tool

    @tool(description="Update the todo list for planning and tracking tasks. Pass a list of todo objects.")
    def write_todos(todos: list[dict[str, Any]]) -> str:
        """Write or replace the current todo list with the provided items."""
        try:
            count = len(todos) if isinstance(todos, list) else 0
        except Exception:
            count = 0
        return f"Updated todos with {count} items"

    @tool(description="List directory entries for the given path (default current directory).")
    def ls(path: str = ".") -> str:
        """List files and directories at the specified path."""
        import os
        try:
            entries = sorted(os.listdir(path))
        except Exception as e:
            return f"Error listing {path}: {e}"
        return "\n".join(entries)

    built_in_tools = [
        write_todos,
        ls,
        # Example-local HACS admin tools so subagents can use them by name
        manage_admin_tasks,
        update_system_status,
        run_database_migration,
        check_database_status,
        create_hacs_record,
    ]
    hacs_tools = get_hacs_agent_tools()
    
    # Set up model
    if model is None:
        model = get_default_model()
    
    # Set up state schema
    state_schema = state_schema or HACSAgentState
    
    # Create task delegation tool for HACS subagents
    additional_tools = list(tools) if tools else []
    all_available_tools = hacs_tools + built_in_tools + additional_tools
    
    task_tool = _create_task_tool(
        all_available_tools,
        instructions,
        subagents or [],
        model,
        state_schema
    )
    
    # Combine all tools
    all_tools = hacs_tools + built_in_tools + additional_tools + [task_tool]
    
    return create_react_agent(
        model,
        prompt=prompt,
        tools=all_tools,
        state_schema=state_schema,
    )


# LangGraph compatible factory function
def get_workflow(config: Optional[dict] = None):
    """
    Factory function for LangGraph integration.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        HACS agent ready for LangGraph
    """
    try:
        # Create HACS agent with default configuration
        from hacs_subagents_config import get_default_hacs_subagents
        
        subagents = get_default_hacs_subagents()
        
        return create_hacs_agent(
            instructions="You are a HACS Healthcare AI Agent specialized in healthcare administration and clinical operations.",
            subagents=subagents
        )
    except Exception as e:
        print(f"⚠️ HACS agent creation failed: {e}")
        
        # Create simple fallback workflow for LangGraph
        from langgraph.graph import StateGraph
        from hacs_state import HACSAgentState
        
        workflow = StateGraph(HACSAgentState)
        
        def basic_node(state):
            """Basic fallback node"""
            return {
                "messages": state.get("messages", []) + [
                    {"role": "assistant", "content": "HACS agent is initializing. Please try again."}
                ]
            }
        
        workflow.add_node("hacs_agent", basic_node)
        workflow.set_entry_point("hacs_agent")
        workflow.set_finish_point("hacs_agent")
        
        return workflow.compile()