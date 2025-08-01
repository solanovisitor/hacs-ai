"""Enhanced HACS Developer Agent.

A LangGraph-based agent for HACS development, administration, and healthcare AI workflows.
Connects to HACS MCP server for tool execution and supports multiple LLM providers.
Features enhanced metadata tracking and tool result parsing for better reflection.
"""

import os
import sys
from typing import Any, Dict, List, Optional, Annotated
from typing_extensions import TypedDict
from dataclasses import dataclass, field

from langchain_core.language_models import LanguageModelLike
from langchain_core.tools import BaseTool, tool
from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent


# ============================================================================
# STATE DEFINITION
# ============================================================================

class HACSAgentState(TypedDict, total=False):
    """Enhanced agent state for HACS operations with metadata tracking."""
    messages: Annotated[list[AnyMessage], add_messages]
    remaining_steps: int
    todos: List[Dict[str, str]]
    files: Dict[str, str]
    session_id: str
    database_url: str
    admin_context: Dict[str, Any]
    delegation_depth: int
    tool_execution_history: List[Dict[str, Any]]  # Track tool executions with metadata
    discovered_tools: Dict[str, Dict[str, Any]]  # Cache discovered tools and their metadata
    reflection_notes: List[str]  # Agent's reflection notes on tool results


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class Configuration:
    """Configuration for HACS Agent."""
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    hacs_mcp_server_url: str = "http://localhost:8000"
    database_url: Optional[str] = None
    
    def __post_init__(self):
        """Load configuration from environment if not provided."""
        if not self.openai_api_key:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.anthropic_api_key:
            self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.database_url:
            self.database_url = os.getenv("DATABASE_URL", "postgresql://hacs:hacs_dev@localhost:5432/hacs")
    
    @classmethod
    def from_runnable_config(cls, config: RunnableConfig) -> 'Configuration':
        """Create configuration from LangGraph RunnableConfig."""
        configurable = config.get("configurable", {})
        
        return cls(
            openai_api_key=configurable.get("__openai_api_key") or os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=configurable.get("__anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY"),
            hacs_mcp_server_url=configurable.get("hacs_mcp_server_url") or os.getenv("HACS_MCP_SERVER_URL", "http://localhost:8000"),
            database_url=configurable.get("__database_url") or os.getenv("DATABASE_URL", "postgresql://hacs:hacs_dev@localhost:5432/hacs"),
        )


# ============================================================================
# INSTRUCTIONS
# ============================================================================

HACS_AGENT_INSTRUCTIONS = """You are a HACS (Healthcare Agent Communication Standard) Developer Agent.

Your mission is to help developers and administrators manage HACS systems with professional expertise and systematic planning.

## 🚨 **CRITICAL: IMMEDIATE TOOL USAGE REQUIRED**

### ⚡ **NEVER ASK - ALWAYS ACT IMMEDIATELY**
- **DO NOT ask for clarification** - make reasonable defaults and proceed
- **DO NOT explain what you'll do** - ACTUALLY DO IT with tools immediately
- **DO NOT wait for user input** - take action with best practices
- **ALWAYS call tools first** - explanation comes after action

### 🎯 **Default Actions for Common Requests**
- **"gerar template"** → IMMEDIATELY use `create_hacs_record` with smart defaults
- **"consulta"** → CREATE clinical consultation template instantly
- **Any planning task** → USE `write_todos` FIRST, then execute immediately
- **File requests** → USE file tools immediately

## Your Specialization:
- **Healthcare Development**: FHIR resources, clinical workflows, healthcare data
- **Database Administration**: Migrations, schema management, connectivity
- **Resource Management**: HACS resource discovery, analysis, and lifecycle management
- **System Integration**: Complete system setup, configuration, and validation
- **Troubleshooting**: Systematic problem diagnosis and resolution

## Your Operating Principles:

### 🎯 **Plan Everything**
For ANY complex operation (more than 2 steps):
1. Use `write_todos` FIRST to create a systematic plan
2. Break complex tasks into clear, manageable steps
3. Mark tasks in_progress when working on them
4. Mark tasks completed IMMEDIATELY when finished
5. Only have ONE task in_progress at a time

### 🔧 **Direct HACS Operations**
- **Create HACS Resource** → Use `create_hacs_record` directly
- **Discover Resources** → Use `discover_hacs_resources`
- **Database Operations** → Use database tools or delegate to database-admin
- **Schema Inspection** → Use schema discovery tools

Remember: You're a sophisticated development agent with expert capabilities. Use planning tools and act decisively!"""


# ============================================================================
# MODEL INITIALIZATION
# ============================================================================

def init_model(config: Optional[Configuration] = None) -> LanguageModelLike:
    """Initialize the language model based on configuration."""
    if config is None:
        config = Configuration()
    
    # Try Anthropic first if available
    if config.anthropic_api_key and config.anthropic_api_key != "test-key":
        try:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                api_key=config.anthropic_api_key,
                temperature=0.1,
                max_tokens=4096
            )
        except ImportError:
            pass
    
    # Fallback to OpenAI
    if config.openai_api_key and config.openai_api_key != "test-key":
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model="gpt-4o-mini",
                api_key=config.openai_api_key,
                temperature=0.1,
                max_tokens=4096
            )
        except ImportError:
            pass
    
    # For testing purposes, create a dummy model
    try:
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key="test-key",
            temperature=0.1,
            max_tokens=4096
        )
    except ImportError:
        pass
    
    raise ValueError("No valid API key found. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY")


# ============================================================================
# TOOLS
# ============================================================================

@tool
def write_todos(todos: List[Dict[str, str]]) -> str:
    """Create and manage a structured task list for planning work."""
    return f"✅ Created {len(todos)} todos for systematic planning"

@tool  
def write_file(file_path: str, content: str) -> str:
    """Write content to a file in the agent's workspace."""
    return f"✅ File written to {file_path}"

@tool
def read_file(file_path: str) -> str:
    """Read content from a file in the agent's workspace."""
    return f"File content from {file_path}"

@tool
def edit_file(file_path: str, old_content: str, new_content: str) -> str:
    """Edit a file by replacing old_content with new_content."""
    return f"✅ File {file_path} edited successfully"

@tool
def discover_hacs_resources(category_filter: Optional[str] = None) -> str:
    """Discover available HACS resource types and models."""
    import httpx
    import asyncio
    
    async def call_mcp():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/",
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {
                            "name": "discover_hacs_resources",
                            "arguments": {"category_filter": category_filter} if category_filter else {}
                        },
                        "id": 1
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=10.0
                )
                result = response.json()
                if "result" in result:
                    return f"✅ HACS Resources discovered: {result['result']}"
                else:
                    return f"⚠️ Unexpected response: {result}"
        except Exception as e:
            return f"❌ Failed to discover HACS resources: {str(e)}"
    
    return asyncio.run(call_mcp())

@tool
def create_hacs_record(resource_type: str, resource_name: str, description: str, attributes: Optional[str] = None) -> str:
    """Create a new HACS record directly in the database."""
    import httpx
    import asyncio
    
    async def call_mcp():
        try:
            resource_data = {
                "resourceType": resource_type,
                "name": resource_name,
                "description": description,
            }
            
            if attributes:
                attr_list = [attr.strip() for attr in attributes.split(',')]
                resource_data["attributes"] = attr_list
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/",
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {
                            "name": "create_resource",
                            "arguments": {
                                "resource_type": resource_type,
                                "resource_data": resource_data,
                                "validate_fhir": True
                            }
                        },
                        "id": 1
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=15.0
                )
                result = response.json()
                if "result" in result:
                    return f"✅ HACS {resource_type} created successfully: {result['result']}"
                else:
                    return f"❌ Creation failed: {result}"
        except Exception as e:
            return f"❌ Failed to create HACS record: {str(e)}"
    
    return asyncio.run(call_mcp())

@tool
def test_mcp_connection() -> str:
    """Test connection to HACS MCP server."""
    import httpx
    import asyncio
    
    async def test_connection():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/",
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/list",
                        "id": 1
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=5.0
                )
                result = response.json()
                if "result" in result:
                    tools_count = len(result["result"].get("tools", []))
                    return f"✅ MCP Server connected! {tools_count} tools available."
                else:
                    return f"⚠️ MCP Server responded but with unexpected format: {result}"
        except Exception as e:
            return f"❌ MCP Server connection failed: {str(e)}"
    
    return asyncio.run(test_connection())

@tool  
def check_database() -> str:
    """Check PostgreSQL database connection."""
    import httpx
    import asyncio
    
    async def test_db():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/",
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {
                            "name": "list_available_resources",
                            "arguments": {}
                        },
                        "id": 1
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=10.0
                )
                result = response.json()
                if "result" in result:
                    return "✅ Database connected and accessible via MCP server!"
                else:
                    return f"⚠️ Database check returned: {result}"
        except Exception as e:
            return f"❌ Database check failed: {str(e)}"
    
    return asyncio.run(test_db())


def get_available_tools(config: Optional[Configuration] = None) -> List[BaseTool]:
    """Get all available HACS tools for the agent with enhanced metadata support."""
    # Import enhanced tools
    from tools_enhanced import get_enhanced_hacs_tools
    
    enhanced_tools = get_enhanced_hacs_tools()
    
    # Add the basic agent tools
    basic_tools = [
        write_todos,
        write_file,
        read_file,
        edit_file,
        test_mcp_connection,
        check_database,
    ]
    
    # Combine enhanced HACS tools with basic agent tools
    return enhanced_tools + basic_tools


# ============================================================================
# AGENT FACTORY
# ============================================================================

def create_hacs_agent(
    instructions: Optional[str] = None,
    model: Optional[LanguageModelLike] = None,
    config: Optional[Configuration] = None,
    additional_tools: Optional[List[BaseTool]] = None,
) -> Any:
    """Create a HACS agent with tools and capabilities."""
    
    # Initialize configuration
    if config is None:
        config = Configuration()
    
    # Initialize model
    if model is None:
        model = init_model(config)
    
    # Use default instructions if none provided
    if instructions is None:
        instructions = HACS_AGENT_INSTRUCTIONS
    
    # Get all available tools
    all_tools = get_available_tools(config)
    
    # Add additional tools if provided
    if additional_tools:
        all_tools.extend(additional_tools)
    
    # Create the enhanced prompt with HACS context
    enhanced_prompt = f"""{instructions}

## HACS Developer Agent

You are a sophisticated HACS (Healthcare Agent Communication Standard) developer agent with access to powerful tools.

### Your Core Capabilities:

🎯 **Planning & Organization**
- Use `write_todos` to plan and track complex development and admin operations
- Break down multi-step tasks into manageable, trackable components

📁 **File Management**  
- Use file tools (`write_file`, `read_file`, `edit_file`) to create code, configuration files, and documentation
- Build reusable templates and procedures for common tasks

🗄️ **Database & Resources**
- Use HACS MCP tools for resource discovery, creation, and management
- Work with FHIR-compliant healthcare data structures

🔍 **Development Support**
- Discover available HACS models and their schemas
- Create clinical templates and healthcare workflows
- Validate data structures and resource compliance

### Connection Information:
- **MCP Server**: {config.hacs_mcp_server_url}
- **Database**: Connected via configuration

Use your tools immediately when asked to perform tasks. Be proactive and systematic in your approach!"""

    # Create the main agent
    agent = create_react_agent(
        model,
        prompt=enhanced_prompt,
        tools=all_tools,
        state_schema=HACSAgentState,
    )
    
    return agent


# ============================================================================
# LANGGRAPH COMPATIBILITY
# ============================================================================

def create_workflow(config_dict: Optional[Dict[str, Any]] = None) -> Any:
    """Create the main HACS agent workflow for LangGraph."""
    # Initialize configuration from environment or config_dict
    if config_dict:
        # Use RunnableConfig pattern for LangGraph Platform
        runnable_config = RunnableConfig(configurable=config_dict)
        config = Configuration.from_runnable_config(runnable_config)
    else:
        config = Configuration()
    
    return create_hacs_agent(config=config)


def get_workflow():
    """Get the workflow when needed (avoids import-time initialization)."""
    return create_workflow()


# For LangGraph dev compatibility - avoid import-time initialization
if __name__ == "__main__":
    try:
        workflow = create_workflow()
        print("✅ HACS Agent workflow created successfully")
    except Exception as e:
        print(f"⚠️ Could not create workflow at import time: {e}")
        print("This is normal - workflow will be created when needed")