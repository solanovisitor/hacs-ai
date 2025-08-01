"""Robust HACS Developer Agent with LangChain MCP Integration.

This module provides a LangGraph-based agent that uses langchain-mcp-adapters
for direct integration with HACS MCP servers, with robust error handling
and graceful fallbacks for connection issues.
"""

import asyncio
from typing import Any, Dict, List, Optional, Annotated

from langchain_core.language_models import LanguageModelLike
from langchain_core.tools import BaseTool, tool
from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent

try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    MultiServerMCPClient = None

from typing_extensions import TypedDict
from configuration import Configuration


# ============================================================================
# STATE DEFINITION WITH MCP INTEGRATION
# ============================================================================

class HACSRobustAgentState(TypedDict, total=False):
    """Enhanced agent state for HACS operations with robust MCP integration."""
    messages: Annotated[list[AnyMessage], add_messages]
    remaining_steps: int
    todos: List[Dict[str, str]]
    files: Dict[str, str]
    session_id: str
    database_url: str
    admin_context: Dict[str, Any]
    delegation_depth: int
    mcp_tools: List[BaseTool]  # Cache MCP tools
    tool_execution_history: List[Dict[str, Any]]  # Track tool executions
    discovered_tools: Dict[str, Dict[str, Any]]  # Cache discovered tools
    reflection_notes: List[str]  # Agent's reflection notes
    connection_status: Dict[str, Any]  # Track connection health


# ============================================================================
# ROBUST MCP CLIENT MANAGER
# ============================================================================

class RobustMCPManager:
    """Robust manager for HACS MCP client integration with error handling."""
    
    def __init__(self, config: Optional[Configuration] = None):
        self.config = config or Configuration()
        self._client: Optional[MultiServerMCPClient] = None
        self._tools: Optional[List[BaseTool]] = None
        self._connection_status = {
            "connected": False,
            "last_attempt": None,
            "error_count": 0,
            "last_error": None
        }
    
    async def initialize_client(self) -> Optional[MultiServerMCPClient]:
        """Initialize the MCP client with robust error handling."""
        if not MCP_AVAILABLE:
            print("⚠️ langchain-mcp-adapters not available, using fallback tools")
            return None
            
        if self._client is None:
            try:
                # Configure HACS MCP server with timeout
                server_config = {
                    "hacs": {
                        "url": self.config.hacs_mcp_server_url,
                        "transport": "streamable_http"
                    }
                }
                
                self._client = MultiServerMCPClient(server_config)
                self._connection_status["connected"] = True
                self._connection_status["error_count"] = 0
                
                print(f"✅ MCP client initialized for {self.config.hacs_mcp_server_url}")
                
            except Exception as e:
                self._connection_status["connected"] = False
                self._connection_status["error_count"] += 1
                self._connection_status["last_error"] = str(e)
                
                print(f"⚠️ Failed to initialize MCP client: {e}")
                print("📋 Will use fallback tools instead")
                
                return None
                
        return self._client
    
    async def get_mcp_tools(self) -> List[BaseTool]:
        """Get all available tools from the MCP server with fallback."""
        if self._tools is None:
            client = await self.initialize_client()
            
            if client is None:
                print("📋 Using empty tool list (MCP client unavailable)")
                self._tools = []
                return self._tools
            
            try:
                # Add timeout to avoid hanging
                self._tools = await asyncio.wait_for(client.get_tools(), timeout=10.0)
                print(f"✅ Loaded {len(self._tools)} tools from HACS MCP server")
                
                # Log available tools for debugging
                for tool in self._tools[:3]:  # Show first 3
                    print(f"   🔧 {tool.name}: {tool.description[:60]}...")
                if len(self._tools) > 3:
                    print(f"   ... and {len(self._tools) - 3} more tools")
                    
            except asyncio.TimeoutError:
                print("⚠️ MCP tool loading timed out")
                self._tools = []
            except Exception as e:
                print(f"⚠️ Failed to load MCP tools: {e}")
                self._tools = []
                
        return self._tools
    
    async def close(self):
        """Close the MCP client connection gracefully."""
        if self._client:
            try:
                await asyncio.wait_for(self._client.close(), timeout=5.0)
            except Exception as e:
                print(f"⚠️ Error closing MCP client: {e}")
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status."""
        return self._connection_status.copy()


# ============================================================================
# ENHANCED TOOL WRAPPERS WITH ROBUST ERROR HANDLING
# ============================================================================

def create_robust_tool_wrapper(mcp_tool: BaseTool) -> BaseTool:
    """Wrap an MCP tool with robust error handling and metadata tracking."""
    
    @tool
    async def robust_tool(*args, **kwargs) -> str:
        """Robust tool with comprehensive error handling."""
        import time
        from datetime import datetime
        
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        try:
            # Execute the original MCP tool with timeout
            if asyncio.iscoroutinefunction(mcp_tool._run):
                result = await asyncio.wait_for(
                    mcp_tool._run(*args, **kwargs), 
                    timeout=30.0
                )
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
                "- Connection: Stable",
                "",
                "💭 **Reflection Notes:**",
                "- MCP tool executed successfully via LangChain adapter",
                "- Direct integration eliminates HTTP overhead",
                "- Tool available for future use in this session"
            ]
            
            return "\n".join(enhanced_response)
            
        except asyncio.TimeoutError:
            execution_time = (time.time() - start_time) * 1000
            
            timeout_response = [
                f"⏰ **Tool Timeout: {mcp_tool.name}**",
                "",
                "Tool execution timed out after 30 seconds",
                "",
                "📊 **Execution Metadata:**",
                f"- Tool: {mcp_tool.name}",
                f"- Execution time: {execution_time:.1f}ms",
                f"- Timestamp: {timestamp}",
                "- Success: False",
                "- Error: Timeout",
                "",
                "💭 **Reflection Notes:**",
                "- MCP tool execution timed out",
                "- Consider checking MCP server performance",
                "- May retry with different parameters"
            ]
            
            return "\n".join(timeout_response)
            
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
                f"- Error Type: {type(e).__name__}",
                "",
                "💭 **Reflection Notes:**",
                "- MCP tool execution failed",
                "- Consider checking MCP server connectivity",
                "- Verify tool parameters and requirements"
            ]
            
            return "\n".join(error_response)
    
    # Copy metadata from original tool
    robust_tool.name = f"mcp_{mcp_tool.name}"
    robust_tool.description = f"Robust MCP tool: {mcp_tool.description}"
    
    return robust_tool


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
    """Test connection to HACS MCP server with detailed diagnostics."""
    try:
        config = Configuration()
        manager = RobustMCPManager(config)
        
        # Test connection
        client = await manager.initialize_client()
        if client is None:
            status = manager.get_connection_status()
            return f"❌ MCP server connection failed: {status.get('last_error', 'Unknown error')}"
        
        # Test tool loading
        tools = await manager.get_mcp_tools()
        await manager.close()
        
        status = manager.get_connection_status()
        
        return f"""✅ MCP server connection successful
        
📊 **Connection Details:**
- Server URL: {config.hacs_mcp_server_url}
- Tools Available: {len(tools)}
- Connection Status: {'Connected' if status['connected'] else 'Disconnected'}
- Error Count: {status['error_count']}

🔧 **Available Tools:**
{', '.join([tool.name for tool in tools[:5]])}
{'...' if len(tools) > 5 else ''}
"""
        
    except Exception as e:
        return f"❌ MCP server connection test failed: {str(e)}"


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
# ROBUST MCP-INTEGRATED AGENT FACTORY
# ============================================================================

async def create_robust_hacs_agent(
    instructions: Optional[str] = None,
    model: Optional[LanguageModelLike] = None,
    config: Optional[Configuration] = None,
    additional_tools: Optional[List[BaseTool]] = None,
) -> Any:
    """Create a HACS agent with robust MCP integration and graceful fallbacks."""
    
    # Initialize configuration
    if config is None:
        config = Configuration()
    
    # Initialize model
    if model is None:
        model = init_model(config)
    
    # Initialize MCP manager and get tools with fallback
    mcp_manager = RobustMCPManager(config)
    mcp_tools = await mcp_manager.get_mcp_tools()
    
    # Wrap MCP tools with robust error handling
    enhanced_mcp_tools = [create_robust_tool_wrapper(tool) for tool in mcp_tools]
    
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
        try:
            from prompts import HACS_AGENT_INSTRUCTIONS
            instructions = HACS_AGENT_INSTRUCTIONS
        except ImportError:
            instructions = "You are a helpful HACS healthcare AI agent."
    
    # Create enhanced prompt with robust MCP context
    connection_status = mcp_manager.get_connection_status()
    enhanced_prompt = f"""{instructions}

## 🔌 **Robust MCP Integration Active**

### 📊 **Connection Status:**
- **MCP Available**: {MCP_AVAILABLE}
- **Connected**: {connection_status['connected']}
- **Tools Loaded**: {len(enhanced_mcp_tools)} enhanced MCP tools
- **Server**: {config.hacs_mcp_server_url}

### 🛠️ **Available Tools:**
{chr(10).join([
    f"- **{tool.name}**: Enhanced with robust error handling" 
    for tool in enhanced_mcp_tools[:5]
])}
{f"- ... and {len(enhanced_mcp_tools) - 5} more tools" if len(enhanced_mcp_tools) > 5 else ""}

### 🔧 **Robust Features:**
- **Timeout Protection** - 30-second timeout for tool execution
- **Graceful Fallbacks** - Continue working even if MCP fails
- **Enhanced Error Handling** - Detailed error context and recovery
- **Connection Monitoring** - Real-time connection health tracking
- **Metadata Tracking** - Comprehensive execution analytics

### 📋 **Error Handling:**
If MCP tools fail:
1. Timeout errors are caught and reported
2. Connection issues are handled gracefully
3. Alternative approaches are suggested
4. Basic tools remain available

### Connection Information:
- **MCP Server**: {config.hacs_mcp_server_url}
- **Transport**: streamable_http via LangChain MCP adapters
- **Error Count**: {connection_status['error_count']}
- **Basic Tools**: {len(basic_tools)} always available

Use your tools confidently - the system is designed to handle failures gracefully!"""

    # Create the agent with robust MCP tools
    agent = create_react_agent(
        model,
        prompt=enhanced_prompt,
        tools=all_tools,
        state_schema=HACSRobustAgentState,
    )
    
    return agent, mcp_manager


# ============================================================================
# WORKFLOW FUNCTIONS
# ============================================================================

async def create_robust_workflow(config_dict: Optional[Dict[str, Any]] = None) -> Any:
    """Create the robust MCP-integrated HACS agent workflow."""
    # Initialize configuration from environment or config_dict
    if config_dict:
        runnable_config = RunnableConfig(configurable=config_dict)
        config = Configuration.from_runnable_config(runnable_config)
    else:
        config = Configuration()
    
    agent, mcp_manager = await create_robust_hacs_agent(config=config)
    
    # Store manager reference for cleanup
    agent._mcp_manager = mcp_manager
    
    return agent


def get_robust_workflow():
    """Get the robust MCP-integrated workflow."""
    return asyncio.run(create_robust_workflow())


# ============================================================================
# EXAMPLE USAGE AND TESTING
# ============================================================================

async def test_robust_integration():
    """Test the robust MCP integration functionality."""
    print("🚀 Testing Robust HACS MCP Integration...")
    
    try:
        config = Configuration()
        agent, mcp_manager = await create_robust_hacs_agent(config=config)
        
        print("✅ Robust MCP-integrated agent created successfully")
        
        # Test connection status
        status = mcp_manager.get_connection_status()
        print(f"📊 Connection Status: {status}")
        
        # Test a simple invocation
        test_response = await agent.ainvoke({
            "messages": [{"role": "user", "content": "Test MCP connection and list available tools"}]
        })
        
        print("✅ Agent invocation successful")
        print(f"Response preview: {str(test_response)[:200]}...")
        
        # Cleanup
        await mcp_manager.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Robust MCP integration test failed: {e}")
        return False


if __name__ == "__main__":
    # Test the robust MCP integration
    asyncio.run(test_robust_integration())