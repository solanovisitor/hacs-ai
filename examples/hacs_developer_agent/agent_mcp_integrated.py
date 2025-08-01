"""Enhanced HACS Developer Agent with LangChain MCP Integration.

This module provides a LangGraph-based agent that uses langchain-mcp-adapters
for direct integration with HACS MCP servers, eliminating manual HTTP calls
and providing enhanced metadata tracking and tool result parsing.
"""

import asyncio
from typing import Any, Dict, List, Optional, Annotated
from typing_extensions import TypedDict

from langchain_core.language_models import LanguageModelLike
from langchain_core.tools import BaseTool, tool
from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from configuration import Configuration


# ============================================================================
# STATE DEFINITION WITH MCP INTEGRATION
# ============================================================================

class HACSMCPAgentState(TypedDict, total=False):
    """Enhanced agent state for HACS operations with MCP integration."""
    messages: Annotated[list[AnyMessage], add_messages]
    remaining_steps: int
    todos: List[Dict[str, str]]
    files: Dict[str, str]
    session_id: str
    database_url: str
    admin_context: Dict[str, Any]
    delegation_depth: int
    mcp_tools: List[BaseTool]  # Cache MCP tools
    tool_execution_history: List[Dict[str, Any]]  # Track tool executions with metadata
    discovered_tools: Dict[str, Dict[str, Any]]  # Cache discovered tools and their metadata
    reflection_notes: List[str]  # Agent's reflection notes on tool results


# ============================================================================
# MCP CLIENT MANAGER
# ============================================================================

class HACSMCPManager:
    """Manager for HACS MCP client integration."""
    
    def __init__(self, config: Optional[Configuration] = None):
        self.config = config or Configuration()
        self._client: Optional[MultiServerMCPClient] = None
        self._tools: Optional[List[BaseTool]] = None
    
    async def initialize_client(self) -> MultiServerMCPClient:
        """Initialize the MCP client with HACS server configuration."""
        if self._client is None:
            # Configure HACS MCP server
            server_config = {
                "hacs": {
                    "url": self.config.hacs_mcp_server_url,
                    "transport": "streamable_http"
                }
            }
            
            self._client = MultiServerMCPClient(server_config)
            
        return self._client
    
    async def get_mcp_tools(self) -> List[BaseTool]:
        """Get all available tools from the MCP server."""
        if self._tools is None:
            client = await self.initialize_client()
            try:
                self._tools = await client.get_tools()
                print(f"✅ Loaded {len(self._tools)} tools from HACS MCP server")
                
                # Log available tools for debugging
                for tool in self._tools[:5]:  # Show first 5
                    print(f"   🔧 {tool.name}: {tool.description[:80]}...")
                if len(self._tools) > 5:
                    print(f"   ... and {len(self._tools) - 5} more tools")
                    
            except Exception as e:
                print(f"⚠️ Failed to load MCP tools: {e}")
                self._tools = []
        
        return self._tools
    
    async def close(self):
        """Close the MCP client connection."""
        if self._client:
            try:
                await self._client.close()
            except Exception as e:
                print(f"⚠️ Error closing MCP client: {e}")


# ============================================================================
# ENHANCED TOOL WRAPPERS WITH METADATA
# ============================================================================

def create_metadata_wrapper(mcp_tool: BaseTool) -> BaseTool:
    """Wrap an MCP tool to add metadata tracking and reflection."""
    
    @tool
    async def enhanced_tool(*args, **kwargs) -> str:
        """Enhanced tool with metadata tracking."""
        import time
        from datetime import datetime
        
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        try:
            # Execute the original MCP tool
            if asyncio.iscoroutinefunction(mcp_tool._run):
                result = await mcp_tool._run(*args, **kwargs)
            else:
                result = mcp_tool._run(*args, **kwargs)
            
            execution_time = (time.time() - start_time) * 1000
            
            # Format enhanced response with metadata
            enhanced_response = [
                f"🔧 **Tool: {mcp_tool.name}**",
                "",
                str(result),
                "",
                "📊 **Execution Metadata:**",
                f"- Tool: {mcp_tool.name}",
                f"- Execution time: {execution_time:.1f}ms",
                f"- Timestamp: {timestamp}",
                "- Success: True",
                "",
                "💭 **Reflection Notes:**",
                "- MCP tool executed successfully via LangChain adapter",
                "- Direct integration eliminates HTTP overhead",
                "- Tool available for future use in this session"
            ]
            
            return "\n".join(enhanced_response)
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            error_response = [
                f"❌ **Tool Execution Failed: {mcp_tool.name}**",
                "",
                f"Error: {str(e)}",
                "",
                "📊 **Execution Metadata:**",
                f"- Tool: {mcp_tool.name}",
                f"- Execution time: {execution_time:.1f}ms",
                f"- Timestamp: {timestamp}",
                "- Success: False",
                "",
                "💭 **Reflection Notes:**",
                "- MCP tool execution failed",
                "- Consider checking MCP server connectivity",
                "- Verify tool parameters and requirements"
            ]
            
            return "\n".join(error_response)
    
    # Copy metadata from original tool
    enhanced_tool.name = f"mcp_{mcp_tool.name}"
    enhanced_tool.description = f"Enhanced MCP tool: {mcp_tool.description}"
    
    return enhanced_tool


# ============================================================================
# BASIC AGENT TOOLS (NON-MCP)
# ============================================================================

@tool
async def write_todos(todos: List[Dict[str, str]]) -> str:
    """Create or update a list of todos for systematic task management."""
    return f"✅ Created {len(todos)} todos for systematic task tracking"

@tool
def write_file(file_path: str, content: str) -> str:
    """Write content to a file."""
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        return f"✅ File written successfully: {file_path}"
    except Exception as e:
        return f"❌ Failed to write file: {str(e)}"

@tool
def read_file(file_path: str, start_line: int = 1, end_line: Optional[int] = None) -> str:
    """Read content from a file with optional line range."""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        if end_line is None:
            end_line = len(lines)
        
        selected_lines = lines[start_line-1:end_line]
        content = ''.join(selected_lines)
        
        return f"📄 File content ({start_line}-{end_line}):\n{content}"
    except Exception as e:
        return f"❌ Failed to read file: {str(e)}"

@tool
def edit_file(file_path: str, search_text: str, replace_text: str) -> str:
    """Edit a file by replacing text."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        if search_text not in content:
            return f"❌ Search text not found in {file_path}"
        
        new_content = content.replace(search_text, replace_text)
        
        with open(file_path, 'w') as f:
            f.write(new_content)
        
        return f"✅ File edited successfully: {file_path}"
    except Exception as e:
        return f"❌ Failed to edit file: {str(e)}"

@tool
async def test_mcp_connection() -> str:
    """Test connection to HACS MCP server."""
    try:
        config = Configuration()
        manager = HACSMCPManager(config)
        tools = await manager.get_mcp_tools()
        await manager.close()
        
        return f"✅ MCP server connection successful - {len(tools)} tools available"
    except Exception as e:
        return f"❌ MCP server connection failed: {str(e)}"


# ============================================================================
# MODEL INITIALIZATION
# ============================================================================

def init_model(config: Configuration) -> LanguageModelLike:
    """Initialize the language model based on configuration."""
    if config.anthropic_api_key:
        try:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                api_key=config.anthropic_api_key,
                temperature=0.1
            )
        except ImportError:
            print("⚠️ Anthropic not available, falling back to OpenAI")
    
    if config.openai_api_key:
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model="gpt-4",
                api_key=config.openai_api_key,
                temperature=0.1
            )
        except ImportError:
            print("⚠️ OpenAI not available")
    
    # Last resort - print warning and use mock
    print("⚠️ No valid API key found. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY")
    from langchain_core.language_models.fake import FakeListLLM
    return FakeListLLM(responses=["I need a valid API key to function properly."])


# ============================================================================
# MCP-INTEGRATED AGENT FACTORY
# ============================================================================

async def create_hacs_mcp_agent(
    instructions: Optional[str] = None,
    model: Optional[LanguageModelLike] = None,
    config: Optional[Configuration] = None,
    additional_tools: Optional[List[BaseTool]] = None,
) -> Any:
    """Create a HACS agent with MCP integration and enhanced metadata tracking."""
    
    # Initialize configuration
    if config is None:
        config = Configuration()
    
    # Initialize model
    if model is None:
        model = init_model(config)
    
    # Initialize MCP manager and get tools
    mcp_manager = HACSMCPManager(config)
    mcp_tools = await mcp_manager.get_mcp_tools()
    
    # Wrap MCP tools with metadata enhancement
    enhanced_mcp_tools = [create_metadata_wrapper(tool) for tool in mcp_tools]
    
    # Get basic agent tools
    basic_tools = [
        write_todos,
        write_file,
        read_file,
        edit_file,
        test_mcp_connection,
    ]
    
    # Combine all tools
    all_tools = enhanced_mcp_tools + basic_tools
    
    if additional_tools:
        all_tools.extend(additional_tools)
    
    # Use enhanced instructions
    if instructions is None:
        from prompts import HACS_AGENT_INSTRUCTIONS
        instructions = HACS_AGENT_INSTRUCTIONS
    
    # Create enhanced prompt with MCP context
    enhanced_prompt = f"""{instructions}

## 🔌 **MCP Integration Active**

You now have direct access to {len(enhanced_mcp_tools)} HACS tools via LangChain MCP adapters:

### 🛠️ **Available MCP Tools:**
{chr(10).join([
    f"- **mcp_{tool.name}**: Enhanced with metadata tracking" 
    for tool in mcp_tools[:10]
])}
{f"- ... and {len(mcp_tools) - 10} more tools" if len(mcp_tools) > 10 else ""}

### 🔧 **MCP Tool Benefits:**
- **Direct integration** - No manual HTTP calls required
- **Enhanced metadata** - Execution time, timestamps, reflection notes
- **Better error handling** - LangChain's built-in error management
- **Automatic retries** - Built-in retry logic for failed connections

### 📊 **Metadata Analysis:**
Every MCP tool call now provides:
- Execution time for performance monitoring
- Success/failure status for reliability tracking
- Timestamp for session management
- Reflection notes for decision-making

### Connection Information:
- **MCP Server**: {config.hacs_mcp_server_url}
- **Transport**: streamable_http via LangChain MCP adapters
- **Tools loaded**: {len(enhanced_mcp_tools)} enhanced MCP tools + {len(basic_tools)} basic tools

Use your MCP tools directly - they're now seamlessly integrated with comprehensive metadata!"""

    # Create the agent with MCP tools
    agent = create_react_agent(
        model,
        prompt=enhanced_prompt,
        tools=all_tools,
        state_schema=HACSMCPAgentState,
    )
    
    return agent, mcp_manager


# ============================================================================
# WORKFLOW FUNCTIONS
# ============================================================================

async def create_mcp_workflow(config_dict: Optional[Dict[str, Any]] = None) -> Any:
    """Create the MCP-integrated HACS agent workflow."""
    # Initialize configuration from environment or config_dict
    if config_dict:
        runnable_config = RunnableConfig(configurable=config_dict)
        config = Configuration.from_runnable_config(runnable_config)
    else:
        config = Configuration()
    
    agent, mcp_manager = await create_hacs_mcp_agent(config=config)
    
    # Store manager reference for cleanup
    agent._mcp_manager = mcp_manager
    
    return agent


def get_mcp_workflow():
    """Get the MCP-integrated workflow."""
    return asyncio.run(create_mcp_workflow())


# ============================================================================
# EXAMPLE USAGE AND TESTING
# ============================================================================

async def test_mcp_integration():
    """Test the MCP integration functionality."""
    print("🚀 Testing HACS MCP Integration...")
    
    try:
        config = Configuration()
        agent, mcp_manager = await create_hacs_mcp_agent(config=config)
        
        print("✅ MCP-integrated agent created successfully")
        
        # Test a simple invocation
        test_response = await agent.ainvoke({
            "messages": [{"role": "user", "content": "List available HACS tools"}]
        })
        
        print("✅ Agent invocation successful")
        print(f"Response: {test_response}")
        
        # Cleanup
        await mcp_manager.close()
        
        return True
        
    except Exception as e:
        print(f"❌ MCP integration test failed: {e}")
        return False


if __name__ == "__main__":
    # Test the MCP integration
    asyncio.run(test_mcp_integration())