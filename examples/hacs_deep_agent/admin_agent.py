"""
HACS Admin Agent

Clean implementation following the deepagents pattern for creating admin agents
with configuration-driven setup and lean state management.
"""

from typing import Sequence, Union, Callable, Any, Optional, Type, TypeVar
from langchain_core.tools import BaseTool
from langchain_core.language_models import LanguageModelLike
from langgraph.prebuilt import create_react_agent

from sub_agent import SubAgent, _create_task_tool, get_default_model, create_admin_subagents_from_config
from admin_state import AdminAgentState
from config import AdminAgentConfig, get_admin_config, ADMIN_BASE_PROMPT

# Import HACS admin tools
from hacs_tools import (
    # Admin Operations
    run_database_migration, check_migration_status, describe_database_schema,
    get_table_structure, test_database_connection,
    
    # Resource Management
    create_hacs_record, get_hacs_record, update_hacs_record, delete_hacs_record, search_hacs_records,
    
    # Schema Discovery  
    discover_hacs_resources, get_hacs_resource_schema, analyze_resource_fields, compare_resource_schemas,
    
    # Development Tools
    create_resource_stack, create_clinical_template, optimize_resource_for_llm,
    
    # Vector Search
    store_embedding, vector_similarity_search, vector_hybrid_search, get_vector_collection_stats, optimize_vector_collection
)

StateSchema = TypeVar("StateSchema", bound=AdminAgentState)
StateSchemaType = Type[StateSchema]

# Built-in admin tools - essential for all admin agents
BUILT_IN_ADMIN_TOOLS = [
    run_database_migration,
    check_migration_status, 
    test_database_connection,
    create_hacs_record,
    get_hacs_record,
    search_hacs_records
]

# Base prompt for admin agent
base_prompt = f"""{ADMIN_BASE_PROMPT}

## Task Delegation

You have access to the `delegate_admin_task` tool to leverage specialized admin subagents. Use this tool FREQUENTLY for complex administrative operations that require domain expertise.

Available specialists:
- **database_admin_specialist**: Database migrations, schema management, health monitoring
- **system_config_specialist**: Resource configuration, system optimization, service setup  
- **data_management_specialist**: Data operations, quality assurance, record management
- **vector_store_specialist**: Vector operations, semantic search, embedding management
- **devops_specialist**: Deployment automation, environment setup, infrastructure

## Core Admin Tools

You also have direct access to essential admin tools:
- Database operations: migrations, status checks, connection testing
- Resource management: create, read, update, delete HACS records
- Schema operations: discovery, analysis, optimization
- Vector operations: embedding storage, semantic search

Use delegation for complex multi-step operations and direct tools for simple administrative tasks."""


def create_admin_agent(
    tools: Sequence[Union[BaseTool, Callable, dict[str, Any]]] = None,
    instructions: str = "",
    model: Optional[Union[str, LanguageModelLike]] = None,
    subagents: Optional[list[SubAgent]] = None,
    state_schema: Optional[StateSchemaType] = None,
    config: Optional[AdminAgentConfig] = None,
):
    """Create a HACS admin agent following the deepagents pattern.

    This agent has built-in access to core admin tools and can delegate complex
    tasks to specialized subagents for database, configuration, data management,
    vector operations, and DevOps tasks.

    Args:
        tools: Additional tools the agent should have access to beyond built-in admin tools.
        instructions: Additional instructions for the agent. Will be added to the system prompt.
        model: The model to use. If string, will attempt to load that model.
        subagents: Custom subagents to use. If None, uses default admin subagents from config.
        state_schema: The schema of the admin agent. Should subclass from AdminAgentState.
        config: Admin agent configuration. If None, uses default configuration.

    Returns:
        Configured admin agent ready for HACS administrative operations.
        
    Examples:
        # Basic admin agent
        agent = create_admin_agent()
        
        # Specialized database admin
        agent = create_admin_agent(
            instructions="Focus on database administration and migrations",
            config=get_admin_config(enabled_subagents=["database_admin_specialist"])
        )
        
        # Custom tools and configuration
        agent = create_admin_agent(
            tools=[custom_monitoring_tool, custom_backup_tool],
            instructions="Enhanced monitoring and backup capabilities",
            config=get_admin_config(primary_actor="Enhanced Admin Agent")
        )
    """
    # Set up configuration
    if config is None:
        config = get_admin_config()
    
    # Combine instructions
    full_prompt = instructions + base_prompt if instructions else base_prompt
    
    # Set up built-in admin tools
    built_in_tools = list(BUILT_IN_ADMIN_TOOLS)
    
    # Set up model
    if model is None:
        model = get_default_model()
    elif isinstance(model, str):
        # Handle string model names
        if "claude" in model.lower() or "anthropic" in model.lower():
            from langchain_anthropic import ChatAnthropic
            model = ChatAnthropic(model=model)
        elif "gpt" in model.lower() or "openai" in model.lower():
            from langchain_openai import ChatOpenAI
            model = ChatOpenAI(model=model)
        else:
            model = get_default_model()
    
    # Set up state schema
    state_schema = state_schema or AdminAgentState
    
    # Set up subagents
    if subagents is None:
        subagents = create_admin_subagents_from_config(config)
    
    # Create task delegation tool
    additional_tools = list(tools) if tools else []
    all_available_tools = built_in_tools + additional_tools
    
    task_tool = _create_task_tool(
        all_available_tools,
        instructions,
        subagents,
        model,
        state_schema
    )
    
    # Combine all tools
    all_tools = built_in_tools + additional_tools + [task_tool]
    
    # Create and return the admin agent
    return create_react_agent(
        model,
        prompt=full_prompt,
        tools=all_tools,
        state_schema=state_schema,
    )


def create_database_admin_agent(
    database_url: str = None,
    instructions: str = "",
    model: Optional[LanguageModelLike] = None,
) -> Any:
    """
    Create a specialized database administration agent.
    
    Args:
        database_url: Database URL for operations
        instructions: Additional instructions 
        model: Language model to use
        
    Returns:
        Database admin agent
    """
    db_instructions = """You are specialized in HACS database administration.
    
Focus on:
- Database migrations and schema management
- Database health monitoring and optimization
- Connection testing and troubleshooting
- Schema validation and compliance

Always verify database connectivity before operations and provide detailed status reports."""
    
    config = get_admin_config(
        primary_actor="Database Admin Agent",
        enabled_subagents=["database_admin_specialist"],
        database_url=database_url
    )
    
    full_instructions = f"{db_instructions}\n\n{instructions}" if instructions else db_instructions
    
    return create_admin_agent(
        instructions=full_instructions,
        model=model,
        config=config
    )


def create_devops_admin_agent(
    instructions: str = "",
    model: Optional[LanguageModelLike] = None,
) -> Any:
    """
    Create a specialized DevOps administration agent.
    
    Args:
        instructions: Additional instructions
        model: Language model to use
        
    Returns:
        DevOps admin agent
    """
    devops_instructions = """You are specialized in HACS DevOps and infrastructure management.
    
Focus on:
- Deployment automation and environment setup
- Infrastructure monitoring and management  
- Service configuration and optimization
- System health and performance monitoring

Ensure all deployments follow best practices and maintain system reliability."""
    
    config = get_admin_config(
        primary_actor="DevOps Admin Agent", 
        enabled_subagents=["devops_specialist", "database_admin_specialist"]
    )
    
    full_instructions = f"{devops_instructions}\n\n{instructions}" if instructions else devops_instructions
    
    return create_admin_agent(
        instructions=full_instructions,
        model=model,
        config=config
    )


# Factory function for LangGraph compatibility  
def create_hacs_admin_agent(config_dict: Optional[dict] = None):
    """
    Factory function for LangGraph integration.
    
    Args:
        config_dict: Configuration dictionary from LangGraph
        
    Returns:
        Admin agent compatible with LangGraph
    """
    if config_dict is None:
        config_dict = {}
    
    # Extract configuration
    instructions = config_dict.get("instructions", "")
    model_name = config_dict.get("model", None)
    enabled_subagents = config_dict.get("enabled_subagents", None)
    primary_actor = config_dict.get("primary_actor", "HACS Admin Agent")
    
    # Create config
    config = get_admin_config(
        primary_actor=primary_actor,
        enabled_subagents=enabled_subagents
    )
    
    # Create and return agent
    return create_admin_agent(
        instructions=instructions,
        model=model_name,
        config=config
    ) 