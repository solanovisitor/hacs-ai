"""
HACS Admin SubAgent Framework

SubAgent implementation following the deepagents pattern for task delegation
and specialized admin operations.
"""

from typing import List, Dict, Any, Optional, Callable, Union, TypeVar
from dataclasses import dataclass
from langchain_core.tools import BaseTool, tool
from langchain_core.language_models import LanguageModelLike
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langgraph.prebuilt import InjectedState
from langchain_core.tools import InjectedToolCallId
from typing import Annotated
from datetime import datetime

from admin_state import AdminAgentState
from config import ADMIN_SUBAGENT_CONFIGS, AdminAgentConfig


@dataclass
class SubAgent:
    """
    Admin subagent configuration following deepagents pattern.
    """
    name: str
    description: str
    prompt: str
    tools: Optional[List[str]] = None
    max_iterations: int = 5


def get_default_model():
    """Get default language model for admin agents."""
    try:
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model="claude-3-sonnet-20240229")
    except ImportError:
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model="gpt-4")
        except ImportError:
            raise ImportError("Please install either langchain-anthropic or langchain-openai")


def _create_admin_subagents(
    tools: List[Union[BaseTool, Callable]],
    instructions: str,
    subagents: List[SubAgent],
    model: LanguageModelLike,
    state_schema=AdminAgentState
) -> Dict[str, Any]:
    """
    Create admin subagents with specialized tools and prompts.
    
    Args:
        tools: Available tools for subagents
        instructions: Base instructions for subagents
        subagents: List of subagent configurations
        model: Language model to use
        state_schema: State schema for subagents
        
    Returns:
        Dictionary of created subagents
    """
    created_subagents = {}
    tools_by_name = {tool.name: tool for tool in tools if hasattr(tool, 'name')}
    
    for subagent in subagents:
        # Get tools for this subagent
        if subagent.tools:
            subagent_tools = [tools_by_name[tool_name] for tool_name in subagent.tools if tool_name in tools_by_name]
        else:
            subagent_tools = tools
            
        # Create the subagent with react pattern
        created_subagents[subagent.name] = create_react_agent(
            model,
            prompt=subagent.prompt,
            tools=subagent_tools,
            state_schema=state_schema
        )
    
    return created_subagents


def _create_task_tool(
    tools: List[Union[BaseTool, Callable]],
    instructions: str,
    subagents: List[SubAgent],
    model: LanguageModelLike,
    state_schema=AdminAgentState
) -> BaseTool:
    """
    Create task delegation tool following deepagents pattern.
    
    Args:
        tools: Available tools for delegation
        instructions: Base instructions
        subagents: Available subagents
        model: Language model
        state_schema: State schema
        
    Returns:
        Task delegation tool
    """
    # Create subagents
    created_subagents = _create_admin_subagents(tools, instructions, subagents, model, state_schema)
    
    @tool(description="""Delegate complex admin tasks to specialized subagents.
    
    Use this tool when you need specialized expertise for:
    - Database operations (use database_admin_specialist)
    - System configuration (use system_config_specialist)
    - Data management (use data_management_specialist) 
    - Vector operations (use vector_store_specialist)
    - DevOps tasks (use devops_specialist)
    
    Provide a clear task description and specify which specialist should handle it.""")
    def delegate_admin_task(
        task_description: str,
        specialist: str,
        priority: str = "normal",
        context: str = "",
        state: Annotated[AdminAgentState, InjectedState] = None,
        tool_call_id: Annotated[str, InjectedToolCallId] = None,
    ) -> Command:
        """
        Delegate an admin task to a specialized subagent.
        
        Args:
            task_description: Detailed description of the admin task
            specialist: Which specialist to delegate to
            priority: Task priority (low, normal, high, critical)
            context: Additional context for the task
            state: Current admin state
            tool_call_id: Tool call identifier
            
        Returns:
            Command with updated state and results
        """
        
        # Validate specialist
        if specialist not in created_subagents:
            available = list(created_subagents.keys())
            error_msg = f"Unknown specialist '{specialist}'. Available: {available}"
            return Command(
                update={
                    "messages": [{"role": "assistant", "content": error_msg}]
                }
            )
        
        # Create task context
        task_context = f"""
Admin Task: {task_description}

Priority: {priority}
Context: {context}

Current System Status:
- Database: {state.get('database_status', {}).get('connected', 'unknown')}
- Active Systems: {len(state.get('active_systems', {}))}
- Session: {state.get('session_context', {}).get('session_id', 'unknown')}

Please complete this administrative task using the appropriate HACS admin tools.
Provide structured results and document any changes made.
"""
        
        # Prepare subagent state
        subagent_state = dict(state)
        subagent_state["messages"] = [{"role": "user", "content": task_context}]
        
        try:
            # Execute with subagent
            subagent = created_subagents[specialist]
            result = subagent.invoke(subagent_state)
            
            # Create task record
            task_record = {
                "task_id": f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "description": task_description,
                "specialist": specialist,
                "priority": priority,
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "result": result["messages"][-1].content if result.get("messages") else "No response"
            }
            
            # Update state
            updated_completed_tasks = state.get("completed_tasks", []) + [task_record]
            updated_audit_trail = state.get("audit_trail", []) + [{
                "action": "task_delegated",
                "specialist": specialist,
                "task_description": task_description,
                "priority": priority,
                "timestamp": datetime.now().isoformat()
            }]
            
            response_message = f"""✅ Task completed by {specialist}

Task: {task_description}
Priority: {priority}
Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Result:
{result["messages"][-1].content if result.get("messages") else "Task completed successfully"}

Task has been logged and results integrated into admin workflow."""
            
            return Command(
                update={
                    "messages": [{"role": "assistant", "content": response_message}],
                    "completed_tasks": updated_completed_tasks,
                    "audit_trail": updated_audit_trail
                }
            )
            
        except Exception as e:
            error_msg = f"❌ Task delegation failed: {str(e)}"
            
            # Log error to audit trail
            updated_audit_trail = state.get("audit_trail", []) + [{
                "action": "task_delegation_failed",
                "specialist": specialist,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }]
            
            return Command(
                update={
                    "messages": [{"role": "assistant", "content": error_msg}],
                    "audit_trail": updated_audit_trail
                }
            )
    
    return delegate_admin_task


def create_admin_subagents_from_config(config: AdminAgentConfig) -> List[SubAgent]:
    """
    Create SubAgent instances from admin configuration.
    
    Args:
        config: Admin agent configuration
        
    Returns:
        List of configured SubAgent instances
    """
    subagents = []
    
    for subagent_name in config.enabled_subagents:
        if subagent_name in ADMIN_SUBAGENT_CONFIGS:
            subagent_config = ADMIN_SUBAGENT_CONFIGS[subagent_name]
            
            # Create specialized prompt for this subagent
            prompt = f"""You are a {subagent_config['name']} for HACS system administration.

{subagent_config['description']}

## Specialized Tools
You have access to these specialized admin tools:
{', '.join(subagent_config['tools'])}

## Your Responsibilities
- Execute admin tasks within your specialty area
- Use appropriate HACS tools for safe operations
- Validate all operations before execution
- Provide clear documentation of changes
- Maintain audit trails for compliance

## Safety Guidelines
1. Always verify permissions before admin operations
2. Test operations in development before production
3. Document all changes and their impact
4. Follow HACS admin best practices
5. Report any errors or concerns immediately

Focus on completing the delegated task efficiently while maintaining system safety and integrity."""
            
            subagent = SubAgent(
                name=subagent_name,
                description=subagent_config['description'],
                prompt=prompt,
                tools=subagent_config['tools'],
                max_iterations=subagent_config.get('max_iterations', 5)
            )
            subagents.append(subagent)
    
    return subagents 