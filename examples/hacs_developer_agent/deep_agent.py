"""HACS Deep Agent Factory.

Creates sophisticated HACS admin agents using the deep agent framework.
Includes planning tools, file system, sub-agents, and task coordination.
"""

from typing import Optional, Union, List, Dict, Any, Annotated
from langchain_core.language_models import LanguageModelLike
from langchain_core.tools import BaseTool, tool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langgraph.prebuilt import create_react_agent, InjectedState

from state import HACSDeepAgentState
from deep_tools import HACS_DEEP_AGENT_TOOLS
from sub_agents import SubAgent, HACS_ADMIN_SUBAGENTS
from utils import init_model


# ============================================================================
# TASK COORDINATION TOOL (for sub-agent delegation)
# ============================================================================

def _create_hacs_task_tool(
    tools: List[BaseTool],
    instructions: str,
    subagents: List[SubAgent],
    model: LanguageModelLike,
    state_schema=HACSDeepAgentState
):
    """Create the task delegation tool for HACS admin sub-agents."""
    
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
    
    # Create sub-agent descriptions for the main agent
    subagent_descriptions = []
    for subagent in subagents:
        subagent_descriptions.append(f"- {subagent['name']}: {subagent['description']}")
    
    task_description = f"""Launch a specialized HACS admin sub-agent to handle complex, multi-step administrative tasks.

Available HACS admin sub-agents:
- general-purpose: General-purpose HACS admin agent for basic operations and coordination
{chr(10).join(subagent_descriptions)}

## When to Use HACS Admin Sub-Agents:

**database-admin**: Use for all database-related operations
- Database migrations and schema updates
- Database connectivity troubleshooting
- Schema inspection and validation
- Database performance issues

**resource-admin**: Use for HACS resource management
- Resource discovery and exploration
- Resource schema analysis
- Resource lifecycle management
- Resource template creation

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
- "Run a specific migration" → use **database-admin**"""

    @tool(description=task_description)
    def task(
        description: str,
        subagent_type: str,
        state: Annotated[HACSDeepAgentState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ):
        """Delegate admin tasks to specialized HACS sub-agents."""
        
        if subagent_type not in agents:
            allowed_types = list(agents.keys())
            return f"Error: Unknown sub-agent type '{subagent_type}'. Available types: {allowed_types}"
        
        # Get the specialized sub-agent
        sub_agent = agents[subagent_type]
        
        # Prepare state for sub-agent (inherit context)
        sub_state = dict(state)
        sub_state["messages"] = [{"role": "user", "content": description}]
        
        # Execute sub-agent
        try:
            result = sub_agent.invoke(sub_state)
            
            # Extract response and update state
            response_content = result["messages"][-1].content if result.get("messages") else "Sub-agent completed task."
            
            return Command(
                update={
                    "files": result.get("files", {}),
                    "todos": result.get("todos", []),
                    "last_operation_result": result.get("last_operation_result"),
                    "messages": [
                        ToolMessage(
                            f"Sub-agent '{subagent_type}' completed task:\n{response_content}",
                            tool_call_id=tool_call_id
                        )
                    ],
                }
            )
            
        except Exception as e:
            return Command(
                update={
                    "messages": [
                        ToolMessage(
                            f"Sub-agent '{subagent_type}' failed: {str(e)}",
                            tool_call_id=tool_call_id
                        )
                    ],
                }
            )
    
    return task


# ============================================================================
# HACS DEEP AGENT FACTORY
# ============================================================================

def create_hacs_deep_admin_agent(
    instructions: str,
    model: Optional[Union[str, LanguageModelLike]] = None,
    subagents: List[SubAgent] = None,
    additional_tools: List[Union[BaseTool, Dict[str, Any]]] = None,
    database_url: Optional[str] = None,
):
    """Create a HACS Deep Admin Agent with specialized sub-agents and planning capabilities.

    This creates a sophisticated HACS admin agent with:
    - Planning tools (todos) for systematic task management
    - File system tools for configuration and documentation
    - Real HACS admin tools for database and resource operations
    - Specialized sub-agents for different admin domains
    - Task delegation and coordination capabilities

    Args:
        instructions: Main agent instructions and context
        model: Language model to use (defaults to configured model)
        subagents: Additional custom sub-agents (adds to built-in HACS admin sub-agents)
        additional_tools: Extra tools beyond the built-in HACS admin tools
        database_url: Default database URL for admin operations

    Returns:
        LangGraph agent ready for HACS admin operations
    """
    
    # Initialize model
    if model is None:
        model = init_model()
    elif isinstance(model, str):
        # TODO: Add model initialization from string
        model = init_model()
    
    # Combine built-in HACS admin sub-agents with any additional ones
    all_subagents = HACS_ADMIN_SUBAGENTS.copy()
    if subagents:
        all_subagents.extend(subagents)
    
    # Combine built-in HACS tools with any additional ones
    all_tools = HACS_DEEP_AGENT_TOOLS.copy()
    if additional_tools:
        all_tools.extend(additional_tools)
    
    # Create the task delegation tool
    task_tool = _create_hacs_task_tool(
        all_tools,
        instructions,
        all_subagents,
        model,
        HACSDeepAgentState
    )
    
    # Add task tool to the tool list
    all_tools.append(task_tool)
    
    # Create the main agent instruction with HACS admin context
    base_prompt = f"""{instructions}

## HACS Deep Admin Agent

You are a sophisticated HACS (Healthcare Agent Communication Standard) administrator with access to powerful tools and specialized sub-agents.

### Your Core Capabilities:

🎯 **Planning & Organization**
- Use `write_todos` to plan and track complex admin operations systematically
- Break down multi-step tasks into manageable, trackable components
- Always mark tasks as completed when finished

📁 **Configuration Management**  
- Use file tools (`write_file`, `read_file`, `edit_file`) to create configuration files, scripts, and documentation
- Build reusable templates and procedures for common admin tasks
- Document all operations for future reference

🗄️ **Database Administration**
- Use `admin_database_migration` for real database migrations and schema updates
- Use `admin_migration_status` to check database state and migration history
- Use `admin_schema_inspection` to analyze database structures

🔍 **Resource Management**
- Use `admin_resource_discovery` to explore available HACS resource types
- Understand resource schemas and relationships
- Plan resource lifecycle management

👥 **Sub-Agent Delegation**
- Use the `task` tool to delegate specialized work to expert sub-agents
- Choose the right sub-agent for each domain (database-admin, resource-admin, system-integration, troubleshooting, documentation)
- Provide clear, detailed task descriptions for autonomous execution

### Your Approach:
1. **Plan First** - Always use `write_todos` for complex operations
2. **Delegate Wisely** - Use specialized sub-agents for domain expertise
3. **Document Everything** - Create files for procedures, configurations, and findings
4. **Validate Thoroughly** - Check results and verify operations completed successfully
5. **Think Systematically** - Break complex admin tasks into logical steps

### Available Sub-Agents:
- **database-admin**: Database operations and troubleshooting
- **resource-admin**: HACS resource management and analysis  
- **system-integration**: Complete system setup and configuration
- **troubleshooting**: Problem diagnosis and resolution
- **documentation**: Knowledge management and procedure creation

Use your planning tools frequently and delegate to specialized sub-agents when you need domain expertise!"""

    # Create the main deep admin agent
    agent = create_react_agent(
        model,
        prompt=base_prompt,
        tools=all_tools,
        state_schema=HACSDeepAgentState,
    )
    
    return agent


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_hacs_database_admin_agent(
    model: Optional[Union[str, LanguageModelLike]] = None,
    database_url: Optional[str] = None
):
    """Create a HACS admin agent specialized for database operations."""
    
    instructions = """You are a HACS Database Administrator. Focus on database migrations, schema management, and database operations.
    
Your primary responsibilities:
- Database setup and migration management
- Schema inspection and validation  
- Database connectivity troubleshooting
- Database operational procedures"""
    
    return create_hacs_deep_admin_agent(
        instructions=instructions,
        model=model,
        database_url=database_url
    )


def create_hacs_system_admin_agent(
    model: Optional[Union[str, LanguageModelLike]] = None,
    database_url: Optional[str] = None
):
    """Create a HACS admin agent specialized for complete system administration."""
    
    instructions = """You are a HACS System Administrator. Focus on complete system setup, integration, and operational management.
    
Your primary responsibilities:
- Complete HACS system setup and configuration
- System integration and validation
- Operational procedure development
- System health monitoring and maintenance"""
    
    return create_hacs_deep_admin_agent(
        instructions=instructions,
        model=model,
        database_url=database_url
    ) 