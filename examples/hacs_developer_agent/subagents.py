"""HACS Agent Sub-Agents.

Specialized sub-agents for different aspects of HACS development and administration.
Each sub-agent has focused expertise and tools for specific domains.
"""

from typing import List, Dict, Any, Optional, Union, Annotated
from typing_extensions import TypedDict, NotRequired

from langchain_core.language_models import LanguageModelLike
from langchain_core.tools import BaseTool, tool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langgraph.prebuilt import create_react_agent, InjectedState

from prompts import (
    DATABASE_ADMIN_PROMPT,
    RESOURCE_ADMIN_PROMPT,
    SYSTEM_INTEGRATION_PROMPT,
    TROUBLESHOOTING_PROMPT,
    DOCUMENTATION_PROMPT
)


class SubAgent(TypedDict):
    """Sub-agent definition for HACS operations."""
    name: str
    description: str
    prompt: str
    tools: NotRequired[List[str]]


# ============================================================================
# SUB-AGENT DEFINITIONS
# ============================================================================

def get_subagents() -> List[SubAgent]:
    """Get all available HACS sub-agents."""
    return [
        {
            "name": "database-admin",
            "description": "Database operations, migrations, and schema management",
            "prompt": DATABASE_ADMIN_PROMPT,
            "tools": [
                "write_todos",
                "write_file", 
                "read_file", 
                "edit_file",
                "discover_hacs_resources",
                "get_resource_schema",
                "create_hacs_record"
            ]
        },
        {
            "name": "resource-admin", 
            "description": "HACS resource management, schema analysis, and FHIR compliance",
            "prompt": RESOURCE_ADMIN_PROMPT,
            "tools": [
                "write_todos",
                "write_file",
                "read_file", 
                "edit_file",
                "discover_hacs_resources",
                "get_resource_schema", 
                "create_hacs_record",
                "validate_resource_data",
                "find_resources",
                "create_clinical_template"
            ]
        },
        {
            "name": "system-integration",
            "description": "Complete system setup, integration, and operational readiness", 
            "prompt": SYSTEM_INTEGRATION_PROMPT,
            # Uses all available tools
        },
        {
            "name": "troubleshooting",
            "description": "Problem diagnosis, error analysis, and solution development",
            "prompt": TROUBLESHOOTING_PROMPT,
            # Uses all available tools for comprehensive troubleshooting
        },
        {
            "name": "documentation",
            "description": "Knowledge management, procedure documentation, and training materials",
            "prompt": DOCUMENTATION_PROMPT,
            "tools": [
                "write_todos",
                "write_file",
                "read_file",
                "edit_file",
                "discover_hacs_resources",
                "get_resource_schema"
            ]
        }
    ]


# ============================================================================
# TASK DELEGATION TOOL
# ============================================================================

def create_task_delegation_tool(
    tools: List[BaseTool],
    instructions: str,
    subagents: List[SubAgent],
    model: LanguageModelLike,
    state_schema: Any
) -> BaseTool:
    """Create the task delegation tool for HACS sub-agents."""
    
    # Create sub-agent instances
    agents = {
        "general-purpose": create_react_agent(
            model, 
            prompt=instructions, 
            tools=tools,
            state_schema=state_schema
        )
    }
    
    # Map tools by name for sub-agent tool selection
    tools_by_name = {}
    for tool_ in tools:
        if not isinstance(tool_, BaseTool):
            tool_ = tool(tool_)
        tools_by_name[tool_.name] = tool_
    
    # Create specialized sub-agents
    for subagent in subagents:
        if "tools" in subagent:
            # Use only specified tools for this sub-agent
            sub_tools = [tools_by_name[t] for t in subagent["tools"] if t in tools_by_name]
        else:
            # Use all available tools
            sub_tools = tools
            
        agents[subagent["name"]] = create_react_agent(
            model,
            prompt=subagent["prompt"],
            tools=sub_tools,
            state_schema=state_schema
        )
    
    # Create other agents string for documentation
    other_agents_string = [
        f"- {subagent['name']}: {subagent['description']}" for subagent in subagents
    ]
    
    task_description = f"""Launch a specialized HACS sub-agent to handle complex, multi-step tasks.

Available HACS sub-agents:
- general-purpose: General-purpose HACS agent for basic operations and coordination
{chr(10).join(other_agents_string)}

## When to Use HACS Sub-Agents:

**database-admin**: Use for all database-related operations
- Database migrations and schema updates
- Database connectivity troubleshooting
- Schema inspection and validation
- Database performance issues

**resource-admin**: Use for HACS resource management
- Resource discovery and exploration
- Resource schema analysis
- Resource template creation
- FHIR compliance validation

**system-integration**: Use for complete system setup
- Full HACS system installation and configuration  
- Multi-component integration workflows
- Environment preparation and validation
- Operational procedure development

**troubleshooting**: Use for problem diagnosis
- Systematic issue investigation
- Error analysis and resolution
- Problem documentation and solutions
- Diagnostic procedure development

**documentation**: Use for knowledge management
- Administrative procedure documentation
- Configuration guides and runbooks
- Training materials and knowledge bases
- Procedure organization and structure

**general-purpose**: Use for basic coordination and simple operations

## Usage Guidelines:
1. Choose the most specialized sub-agent for the task domain
2. Provide detailed task descriptions for autonomous execution
3. Specify exactly what information you need back
4. Sub-agents can create files, run tools, and plan systematically
5. Each sub-agent has expertise-focused tools and approaches

## Example Usage:
- "Set up a new HACS database" → use **system-integration**
- "Troubleshoot migration failures" → use **troubleshooting**  
- "Create admin documentation" → use **documentation**
- "Explore available resources" → use **resource-admin**
- "Create a clinical template" → use **resource-admin**"""

    @tool(description=task_description)
    def task(
        description: str,
        subagent_type: str,
        state: Annotated[Any, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ):
        """Delegate tasks to specialized HACS sub-agents."""
        
        if subagent_type not in agents:
            allowed_types = list(agents.keys())
            return f"Error: Unknown sub-agent type '{subagent_type}'. Available types: {allowed_types}"
        
        # Prevent infinite recursion by limiting delegation depth
        current_depth = state.get("delegation_depth", 0)
        if current_depth >= 3:
            return "Error: Maximum delegation depth reached. Please perform the task directly or simplify the request."
        
        # Get the specialized sub-agent
        sub_agent = agents[subagent_type]
        
        # Prepare clean state for sub-agent to prevent recursion
        sub_state = {
            "messages": [{"role": "user", "content": description}],
            "files": state.get("files", {}),
            "delegation_depth": current_depth + 1,
            "remaining_steps": 10  # Limit sub-agent steps
        }
        
        try:
            result = sub_agent.invoke(sub_state)
            return Command(
                update={
                    "files": {**state.get("files", {}), **result.get("files", {})},
                    "messages": [
                        ToolMessage(
                            result["messages"][-1].content if result.get("messages") else "Sub-agent completed task.",
                            tool_call_id=tool_call_id
                        )
                    ],
                }
            )
        except Exception as e:
            return f"Error: Sub-agent failed: {str(e)}. Please try performing the task directly."
    
    return task