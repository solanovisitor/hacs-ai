"""HACS Specialized Subagents with MCP Tool Integration.

Specialized subagents for different aspects of HACS development and administration.
Each subagent has focused expertise and access to specific HACS MCP tools for their domain.
"""

import asyncio
from typing import List, Dict, Any, Optional, Annotated

from langchain_core.language_models import LanguageModelLike
from langchain_core.tools import BaseTool
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent
from typing_extensions import TypedDict

from prompts import (
    CLINICAL_OPERATIONS_PROMPT,
    RESOURCE_MANAGEMENT_PROMPT, 
    SEARCH_DISCOVERY_PROMPT,
    MEMORY_KNOWLEDGE_PROMPT,
    SYSTEM_ADMIN_PROMPT
)


# ============================================================================
# SUBAGENT STATE AND CONFIGURATION
# ============================================================================

class SubAgentState(TypedDict, total=False):
    """State for HACS subagents."""
    messages: Annotated[list[AnyMessage], add_messages]
    context: Dict[str, Any]
    domain_expertise: str
    available_tools: List[str]
    execution_history: List[Dict[str, Any]]


# ============================================================================
# TOOL ORGANIZATION BY DOMAIN
# ============================================================================

CLINICAL_OPERATIONS_TOOLS = [
    # Patient and clinical data management
    "hacs_create_resource",           # Create clinical resources
    "hacs_get_resource",              # Retrieve patient/clinical data
    "hacs_update_resource",           # Update clinical records
    "hacs_delete_resource",           # Remove clinical data
    "hacs_validate_resource_data",    # Validate clinical data
    "hacs_create_clinical_template",  # Generate clinical templates
    "hacs_find_resources",            # Search clinical resources
]

RESOURCE_MANAGEMENT_TOOLS = [
    # Resource lifecycle and schema management
    "hacs_list_available_resources",  # List available resource types
    "hacs_get_hacs_resource_schema",  # Get resource schemas
    "hacs_get_resource_schema",       # Get detailed schemas
    "hacs_analyze_resource_fields",   # Analyze resource fields
    "hacs_compare_resource_schemas",  # Compare schemas
    "hacs_validate_resource_data",    # Validate resource data
    "hacs_version_hacs_resource",     # Version management
    "hacs_create_model_stack",        # Build complex models
]

SEARCH_DISCOVERY_TOOLS = [
    # Discovery and search capabilities  
    "hacs_discover_hacs_resources",   # Discover available models
    "hacs_search_hacs_records",       # Search HACS records
    "hacs_find_resources",            # Advanced resource search
    "hacs_optimize_resource_for_llm", # Optimize for LLM use
    "hacs_suggest_view_fields",       # Suggest optimal fields
    "hacs_create_view_resource_schema", # Create custom views
]

MEMORY_KNOWLEDGE_TOOLS = [
    # Memory and knowledge management
    "hacs_create_memory",             # Store knowledge blocks
    "hacs_search_memories",           # Search stored memories
    "hacs_consolidate_memories",      # Merge related memories
    "hacs_retrieve_context",          # Get relevant context
    "hacs_analyze_memory_patterns",   # Analyze memory usage
    "hacs_create_knowledge_item",     # Create structured knowledge
]

SYSTEM_ADMIN_TOOLS = [
    # System administration and monitoring
    "hacs_list_available_resources",  # System resource inventory
    "hacs_get_hacs_resource_schema",  # System schema management
    "hacs_validate_resource_data",    # System validation
    "hacs_analyze_resource_fields",   # System analysis
    "hacs_version_hacs_resource",     # Version control
]


# ============================================================================
# SUBAGENT DEFINITIONS
# ============================================================================

class SubAgentDefinition:
    """Definition for a specialized HACS subagent."""
    
    def __init__(self, name: str, description: str, prompt: str, tools: List[str]):
        self.name = name
        self.description = description
        self.prompt = prompt
        self.tools = tools


SUBAGENT_DEFINITIONS = [
    SubAgentDefinition(
        name="clinical_operations",
        description="Patient data management, clinical workflows, and healthcare operations",
        prompt=CLINICAL_OPERATIONS_PROMPT,
        tools=CLINICAL_OPERATIONS_TOOLS
    ),
    SubAgentDefinition(
        name="resource_management", 
        description="Resource lifecycle, schema management, and model optimization",
        prompt=RESOURCE_MANAGEMENT_PROMPT,
        tools=RESOURCE_MANAGEMENT_TOOLS
    ),
    SubAgentDefinition(
        name="search_discovery",
        description="Advanced search, resource discovery, and data analysis",
        prompt=SEARCH_DISCOVERY_PROMPT,
        tools=SEARCH_DISCOVERY_TOOLS
    ),
    SubAgentDefinition(
        name="memory_knowledge",
        description="Memory management, knowledge creation, and context retrieval",
        prompt=MEMORY_KNOWLEDGE_PROMPT,
        tools=MEMORY_KNOWLEDGE_TOOLS
    ),
    SubAgentDefinition(
        name="system_admin",
        description="System administration, monitoring, and maintenance",
        prompt=SYSTEM_ADMIN_PROMPT,
        tools=SYSTEM_ADMIN_TOOLS
    )
]


# ============================================================================
# SUBAGENT FACTORY
# ============================================================================

async def create_subagent(
    definition: SubAgentDefinition,
    model: LanguageModelLike,
    available_tools: List[BaseTool]
) -> Any:
    """Create a specialized subagent with domain-specific tools."""
    
    # Filter tools for this subagent's domain
    subagent_tools = []
    for tool in available_tools:
        if any(tool.name == domain_tool for domain_tool in definition.tools):
            subagent_tools.append(tool)
    
    # Enhanced prompt with domain context
    enhanced_prompt = f"""{definition.prompt}

## 🎯 **Domain Expertise: {definition.name.title()}**

### 🛠️ **Available Domain Tools:**
{chr(10).join([f"- **{tool.name}**: {getattr(tool, 'description', 'HACS tool')[:60]}..." for tool in subagent_tools[:10]])}
{f"- ... and {len(subagent_tools) - 10} more tools" if len(subagent_tools) > 10 else ""}

### 📋 **Your Role:**
{definition.description}

### 🔧 **Tool Usage Guidelines:**
- Use domain-specific tools for optimal results
- Provide comprehensive metadata and reflection
- Leverage your specialized expertise for complex tasks
- Coordinate with other subagents when needed

### 💡 **Key Capabilities:**
- {len(subagent_tools)} specialized HACS tools
- Domain-optimized workflows
- Intelligent error handling and fallbacks
- Rich metadata tracking for all operations

Focus on your domain expertise and use the appropriate tools for each task!"""

    # Create specialized subagent
    subagent = create_react_agent(
        model,
        prompt=enhanced_prompt,
        tools=subagent_tools,
        state_schema=SubAgentState,
    )
    
    # Add metadata
    subagent._domain = definition.name
    subagent._description = definition.description
    subagent._tool_count = len(subagent_tools)
    
    return subagent


# ============================================================================
# SUBAGENT REGISTRY
# ============================================================================

class SubAgentRegistry:
    """Registry for managing HACS subagents."""
    
    def __init__(self):
        self._subagents: Dict[str, Any] = {}
        self._initialized = False
    
    async def initialize(self, model: LanguageModelLike, available_tools: List[BaseTool]):
        """Initialize all subagents with available tools."""
        if self._initialized:
            return
        
        for definition in SUBAGENT_DEFINITIONS:
            subagent = await create_subagent(definition, model, available_tools)
            self._subagents[definition.name] = subagent
        
        self._initialized = True
    
    def get_subagent(self, name: str) -> Optional[Any]:
        """Get a subagent by name."""
        return self._subagents.get(name)
    
    def list_subagents(self) -> List[Dict[str, Any]]:
        """List all available subagents."""
        result = []
        for definition in SUBAGENT_DEFINITIONS:
            subagent = self._subagents.get(definition.name)
            result.append({
                "name": definition.name,
                "description": definition.description,
                "tool_count": getattr(subagent, '_tool_count', 0) if subagent else 0,
                "available": subagent is not None
            })
        return result
    
    def get_tools_by_domain(self, domain: str) -> List[str]:
        """Get tools available for a specific domain."""
        domain_map = {
            "clinical_operations": CLINICAL_OPERATIONS_TOOLS,
            "resource_management": RESOURCE_MANAGEMENT_TOOLS,
            "search_discovery": SEARCH_DISCOVERY_TOOLS,
            "memory_knowledge": MEMORY_KNOWLEDGE_TOOLS,
            "system_admin": SYSTEM_ADMIN_TOOLS,
        }
        return domain_map.get(domain, [])


# Global registry instance
_subagent_registry = SubAgentRegistry()


# ============================================================================
# PUBLIC API
# ============================================================================

async def initialize_subagents(model: LanguageModelLike, available_tools: List[BaseTool]):
    """Initialize all HACS subagents."""
    await _subagent_registry.initialize(model, available_tools)


async def get_subagent_executor(subagent_name: str) -> Optional[Any]:
    """Get a subagent executor by name."""
    return _subagent_registry.get_subagent(subagent_name)


def list_available_subagents() -> List[Dict[str, Any]]:
    """List all available subagents and their capabilities."""
    return _subagent_registry.list_subagents()


def get_domain_tools(domain: str) -> List[str]:
    """Get tools available for a specific domain."""
    return _subagent_registry.get_tools_by_domain(domain)


async def delegate_task(subagent_name: str, task: str, context: Optional[Dict] = None) -> str:
    """Delegate a task to a specific subagent."""
    try:
        subagent = await get_subagent_executor(subagent_name)
        if not subagent:
            return f"❌ Subagent '{subagent_name}' not found"
        
        # Execute task
        result = await subagent.ainvoke({
            "messages": [{"role": "user", "content": task}],
            "context": context or {},
            "domain_expertise": subagent_name,
        })
        
        return f"""✅ **Subagent '{subagent_name}' Task Complete**

🎯 **Task**: {task}

📋 **Result**: 
{result.get('output', result)}

🔧 **Domain**: {subagent_name.replace('_', ' ').title()}
💭 **Tools Used**: {subagent._tool_count} domain-specific tools available"""
        
    except Exception as e:
        return f"❌ Subagent '{subagent_name}' execution failed: {str(e)}"


# ============================================================================
# TESTING AND VALIDATION
# ============================================================================

async def test_subagent_integration() -> bool:
    """Test subagent integration and tool availability."""
    try:
        # Check if subagents are initialized
        subagents = list_available_subagents()
        
        if not subagents:
            print("⚠️ No subagents available - need initialization")
            return False
        
        print(f"✅ Found {len(subagents)} subagents:")
        for subagent in subagents:
            status = "✅" if subagent['available'] else "❌"
            print(f"   {status} {subagent['name']}: {subagent['tool_count']} tools")
        
        return all(s['available'] for s in subagents)
        
    except Exception as e:
        print(f"❌ Subagent integration test failed: {e}")
        return False


async def test_domain_tools():
    """Test domain tool organization."""
    print("🔧 Testing domain tool organization...")
    
    domains = ["clinical_operations", "resource_management", "search_discovery", 
               "memory_knowledge", "system_admin"]
    
    for domain in domains:
        tools = get_domain_tools(domain)
        print(f"📋 {domain}: {len(tools)} tools")
        for tool in tools[:3]:  # Show first 3
            print(f"   • {tool}")
        if len(tools) > 3:
            print(f"   ... and {len(tools) - 3} more")
    
    return True


if __name__ == "__main__":
    # Test subagent functionality
    asyncio.run(test_domain_tools())