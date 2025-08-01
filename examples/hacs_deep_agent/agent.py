"""
HACS Deep Agent

Main implementation of the healthcare deep agent that can iterate on HACS tool
calls and manage complex clinical workflows using HACS resources and subagents.

This agent provides comprehensive healthcare AI capabilities with specialized
subagents for different clinical domains and workflows.
"""

from typing import Sequence, Union, Callable, Any, Optional, Dict, List
from datetime import datetime

from langchain_core.tools import BaseTool, tool, InjectedToolCallId
from langchain_core.language_models import LanguageModelLike
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage
from langgraph.prebuilt import create_react_agent, InjectedState
from langgraph.types import Command
from typing import Annotated

# Import state and subagent components using absolute imports instead of relative
from state import HACSAgentState, HealthcareWorkflowContext, HACSToolResult, create_initial_hacs_state
from admin_subagents import ADMIN_SUBAGENTS, HACSSubAgent

# Import all HACS tools
from hacs_tools import ALL_HACS_TOOLS
from hacs_core.actor import Actor  # Correct import path
from hacs_core.models import Patient, Observation, Encounter, Condition
from hacs_core.results import HACSResult  # Import from results module

# Import structured prompts using absolute import
from admin_prompts import (
    DELEGATE_ADMIN_TASK_DESCRIPTION,
    MAIN_ADMIN_AGENT_PROMPT
)


class HACSDeepAgent:
    """
    HACS Admin Deep Agent with HACS tool integration and admin subagents.
    
    This agent can iterate on HACS tool calls, manage admin workflows,
    and leverage specialized admin subagents for comprehensive HACS system management.
    """
    
    def __init__(
        self,
        model: LanguageModelLike,
        additional_tools: List[Union[BaseTool, Callable]] = None,
        subagents: List[HACSSubAgent] = None,
        primary_actor: str = "HACS Admin Agent"
    ):
        """
        Initialize the HACS Admin Deep Agent.
        
        Args:
            model: Language model to use for the agent
            additional_tools: Additional tools beyond HACS tools
            subagents: Admin subagents to include
            primary_actor: Name of the primary admin actor
        """
        self.model = model
        self.primary_actor = primary_actor
        self.additional_tools = additional_tools or []
        self.subagents = subagents or ADMIN_SUBAGENTS
        
        # Initialize HACS tools and create tool mapping
        self.hacs_tools = ALL_HACS_TOOLS
        self.tools_by_name = {tool.name: tool for tool in self.hacs_tools}
        
        # Add additional tools to mapping
        for tool in self.additional_tools:
            if not isinstance(tool, BaseTool):
                tool = tool(tool)
            self.tools_by_name[tool.name] = tool
        
        # Create subagents
        self.clinical_agents = self._create_admin_subagents()
        
        # Create the task delegation tool
        self.task_tool = self._create_hacs_task_tool()
        
        # Create the main agent
        self.agent = self._create_main_agent()
    
    def _create_admin_subagents(self) -> Dict[str, Any]:
        """Create specialized admin subagents with HACS tools."""
        agents = {}
        
        # Add general purpose agent with all HACS tools
        agents["general_admin"] = create_react_agent(
            self.model,
            prompt="You are a general HACS admin AI agent with access to comprehensive HACS admin tools. Use these tools to support database administration, system management, and HACS operations.",
            tools=list(self.hacs_tools) + self.additional_tools,
            state_schema=HACSAgentState
        )
        
        # Create specialized admin subagents
        for subagent_config in self.subagents:
            # Get tools for this subagent
            if "tools" in subagent_config:
                subagent_tools = [self.tools_by_name[tool_name] for tool_name in subagent_config["tools"]]
            else:
                subagent_tools = list(self.hacs_tools)
            
            # Add additional tools
            subagent_tools.extend(self.additional_tools)
            
            # Create the subagent
            agents[subagent_config["name"]] = create_react_agent(
                self.model,
                prompt=subagent_config["prompt"],
                tools=subagent_tools,
                state_schema=HACSAgentState
            )
        
        return agents
    
    def _create_hacs_task_tool(self) -> BaseTool:
        """Create the task delegation tool for HACS clinical workflows."""
        
        # Generate descriptions of available clinical subagents
        subagent_descriptions = [
            f"- {subagent['name']}: {subagent['description']}"
            for subagent in self.subagents
        ]
        
        @tool(description=DELEGATE_ADMIN_TASK_DESCRIPTION)
        def delegate_admin_task(
            task_description: str,
            admin_specialty: str,
            system_context: str = "",
            task_priority: str = "routine",
            state: Annotated[HACSAgentState, InjectedState] = None,
            tool_call_id: Annotated[str, InjectedToolCallId] = None,
        ) -> Command:
            """
            Delegate an admin task to a specialized admin subagent.
            
            Args:
                task_description: Detailed description of the admin task
                admin_specialty: Admin specialty/domain for the task
                system_context: Additional system context if relevant
                task_priority: Priority level (routine, urgent, critical)
                state: Current HACS agent state
                tool_call_id: Tool call identifier
                
            Returns:
                Command with updated state and task results
            """
            
            # Validate admin specialty
            if admin_specialty not in self.clinical_agents:
                available_specialties = list(self.clinical_agents.keys())
                error_msg = f"Error: Unknown admin specialty '{admin_specialty}'. Available: {available_specialties}"
                return Command(
                    update={
                        "messages": [ToolMessage(error_msg, tool_call_id=tool_call_id)]
                    }
                )
            
            # Prepare task context for the subagent
            task_context = f"""
Admin Task: {task_description}

System Context: {system_context}

Task Priority: {task_priority}

Current Admin Context:
- Active Systems: {len(state.get('active_systems', {}))}
- Pending Tasks: {len(state.get('pending_admin_tasks', []))}
- Session Actor: {state.get('current_actor', {}).get('name', 'Unknown')}

Please use appropriate HACS admin tools to complete this task and provide
structured results that can be integrated into the broader admin workflow.
"""
            
            # Execute the task with the specialized subagent
            subagent = self.clinical_agents[admin_specialty]
            
            # Prepare subagent state
            subagent_state = dict(state)
            subagent_state["messages"] = [{"role": "user", "content": task_context}]
            
            # Add task to audit trail
            task_audit = {
                "action": "task_delegated",
                "specialty": admin_specialty,
                "task_description": task_description,
                "actor": state.get('current_actor', {}).get('name', 'System'),
                "timestamp": datetime.now().isoformat(),
                "priority": task_priority
            }
            
            # Execute the subagent
            try:
                result = subagent.invoke(subagent_state)
                
                # Create structured task result
                task_result = HACSToolResult(
                    tool_name="delegate_admin_task",
                    actor_name=state.get('current_actor', {}).get('name', 'System'),
                    success=True,
                    result_data={
                        "specialty": admin_specialty,
                        "task_description": task_description,
                        "subagent_response": result["messages"][-1].content,
                        "task_priority": task_priority
                    },
                    clinical_significance=task_priority,
                    requires_follow_up=task_priority in ["urgent", "critical"]
                )
                
                # Update audit trail
                audit_trail = state.get('audit_trail', [])
                audit_trail.append(task_audit)
                audit_trail.append({
                    "action": "task_completed",
                    "specialty": admin_specialty,
                    "success": True,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Update completed tasks
                completed_tasks = state.get('completed_admin_tasks', [])
                completed_tasks.append({
                    "task_id": f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "specialty": admin_specialty,
                    "description": task_description,
                    "completed_at": datetime.now().isoformat(),
                    "result": task_result.model_dump()
                })
                
                response_message = f"""
✅ Admin Task Completed by {admin_specialty}

Task: {task_description}
Priority: {task_priority}
Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Results:
{result["messages"][-1].content}

The task has been successfully completed and results have been integrated into the admin workflow.
"""
                
                return Command(
                    update={
                        # Merge any updates from the subagent
                        **{k: v for k, v in result.items() if k not in ["messages"]},
                        "messages": [ToolMessage(response_message, tool_call_id=tool_call_id)],
                        "completed_admin_tasks": completed_tasks,
                        "audit_trail": audit_trail,
                        "admin_context": {
                            **state.get('admin_context', {}),
                            "last_task_completed": datetime.now().isoformat(),
                            "last_specialty_used": admin_specialty
                        }
                    }
                )
                
            except Exception as e:
                # Handle task execution error
                error_audit = {
                    "action": "task_failed",
                    "specialty": admin_specialty,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                
                audit_trail = state.get('audit_trail', [])
                audit_trail.append(task_audit)
                audit_trail.append(error_audit)
                
                error_message = f"❌ Admin task failed in {admin_specialty}: {str(e)}"
                
                return Command(
                    update={
                        "messages": [ToolMessage(error_message, tool_call_id=tool_call_id)],
                        "audit_trail": audit_trail
                    }
                )
        
        return delegate_admin_task
    
    def _create_main_agent(self) -> Any:
        """Create the main HACS deep agent with admin capabilities."""
        
        # Use the structured main prompt
        main_prompt = MAIN_ADMIN_AGENT_PROMPT.format(primary_actor=self.primary_actor)

        # Combine all tools for the main agent
        all_tools = list(self.hacs_tools) + self.additional_tools + [self.task_tool]
        
        return create_react_agent(
            self.model,
            prompt=main_prompt,
            tools=all_tools,
            state_schema=HACSAgentState
        )
    
    def invoke(self, input_message: str, initial_state: HACSAgentState = None) -> HACSAgentState:
        """
        Invoke the HACS deep agent with a healthcare-related input.
        
        Args:
            input_message: Healthcare task or question
            initial_state: Initial HACS agent state
            
        Returns:
            Updated HACS agent state with results
        """
        if initial_state is None:
            initial_state = create_initial_hacs_state(self.primary_actor)
        
        # Add the input message to state
        initial_state["messages"] = [HumanMessage(content=input_message)]
        
        # Execute the agent
        result = self.agent.invoke(initial_state)
        
        return result
    
    def create_healthcare_workflow(
        self,
        workflow_type: str,
        patient_id: str = None,
        workflow_config: Dict[str, Any] = None
    ) -> HealthcareWorkflowContext:
        """
        Create a structured healthcare workflow context.
        
        Args:
            workflow_type: Type of clinical workflow
            patient_id: Primary patient ID if applicable
            workflow_config: Additional workflow configuration
            
        Returns:
            Structured healthcare workflow context
        """
        from hacs_core.models import Patient
        
        workflow_config = workflow_config or {}
        
        # Create primary actor
        primary_actor = Actor(name=self.primary_actor, role="SYSTEM")
        
        # Create workflow context
        workflow_context = HealthcareWorkflowContext(
            workflow_id=f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            workflow_type=workflow_type,
            primary_actor=primary_actor,
            current_step="initialization",
            next_actions=["gather_patient_context", "assess_clinical_requirements"]
        )
        
        # Add patient context if provided
        if patient_id:
            # In a real implementation, this would fetch the patient record
            mock_patient = Patient(
                id=patient_id,
                full_name=f"Patient {patient_id}",
                birth_date="1980-01-01",
                gender="unknown"
            )
            workflow_context.primary_patient = mock_patient
        
        return workflow_context


def create_hacs_deep_agent(
    config: Optional[Dict[str, Any]] = None
):
    """
    Create a HACS Deep Agent with admin capabilities.
    
    This function creates a comprehensive HACS admin AI agent with access to all
    HACS tools, specialized admin subagents, and admin workflow management.
    
    Args:
        config: Configuration dictionary with optional parameters:
            - additional_tools: Additional tools beyond the comprehensive HACS toolkit
            - admin_instructions: Additional admin-specific instructions
            - model: Language model to use (defaults to appropriate model)
            - admin_subagents: Specialized admin subagents to include
            - primary_actor: Name of the primary admin actor
        
    Returns:
        Configured LangGraph agent ready for admin workflows
        
    Examples:
        # Create basic admin agent
        agent = create_hacs_deep_agent()
        
        # Create specialized agent for database management
        agent = create_hacs_deep_agent({
            "admin_instructions": "Focus on database administration and system health",
            "primary_actor": "Database Admin Team"
        })
        
        # Invoke the agent
        result = agent.invoke("Run database migration and validate schemas")
    """
    
    # Parse config parameters
    config = config or {}
    additional_tools = config.get("additional_tools")
    admin_instructions = config.get("admin_instructions", "")
    model = config.get("model")
    admin_subagents = config.get("admin_subagents")
    primary_actor = config.get("primary_actor", "HACS Admin Agent")
    
    # Set default model if not provided
    if model is None:
        try:
            from langchain_anthropic import ChatAnthropic
            model = ChatAnthropic(model="claude-3-sonnet-20240229")
        except ImportError:
            try:
                from langchain_openai import ChatOpenAI
                model = ChatOpenAI(model="gpt-4.1-mini")
            except ImportError:
                raise ImportError("Please install either langchain-anthropic or langchain-openai")
    
    # Use default admin subagents if not provided
    if admin_subagents is None:
        admin_subagents = ADMIN_SUBAGENTS
    
    # Convert additional tools to list
    additional_tools_list = list(additional_tools) if additional_tools else []
    
    # Create the HACS deep agent wrapper
    deep_agent = HACSDeepAgent(
        model=model,
        additional_tools=additional_tools_list,
        subagents=admin_subagents,
        primary_actor=primary_actor
    )
    
    # Return the actual LangGraph agent
    return deep_agent.agent 