# HACS Tools

**42+ Hacs Tools for healthcare agents**

Production-ready tools for clinical workflows, resource management, and healthcare AI operations. HACS tools can be used directly from agent frameworks (e.g., LangGraph, LangChain) or exposed over MCP via `hacs-utils`.

## 🛠️ **Tool Categories**

### 🔍 **Resource Discovery & Development** (5+ tools)
- `discover_hacs_resources` - Explore healthcare resource schemas with metadata
- `analyze_resource_fields` - Field analysis with validation rules
- `compare_resource_schemas` - Schema comparison and integration
- `create_clinical_template` - Generate clinical workflow templates
- `create_model_stack` - Compose complex data structures

### 📋 **Record Management** (8+ tools)
- `create_hacs_record` / `get_hacs_record_by_id` / `update_hacs_record` / `delete_hacs_record` - Full CRUD
- `validate_hacs_record_data` -validation
- `list_available_hacs_resources` - Resource schema catalog
- `find_hacs_records` - Advanced semantic search
- `search_hacs_records` - Filtered record search

### 🧠 **Memory Management** (5+ tools)
- `create_hacs_memory` - Store episodic/procedural/executive memories
- `search_hacs_memories` - Semantic memory retrieval
- `consolidate_memories` - Merge related memories
- `retrieve_context` - Context-aware memory access
- `analyze_memory_patterns` - Usage pattern analysis

### ✅ **Validation & Schema** (3+ tools)
- `get_hacs_resource_schema` - JSON schema exploration
- `create_view_resource_schema` - Custom view creation
- `suggest_view_fields` - Intelligent field suggestions

### 🎨 **Advanced Tools** (Multiple tools)
- `optimize_resource_for_llm` - LLM-specific optimizations
- `version_hacs_resource` - Resource versioning and tracking
- `execute_clinical_workflow` - Clinical protocol execution

### 📚 **Knowledge Management** (Multiple tools)
- `create_knowledge_item` - Clinical guidelines and protocols
- `search_knowledge_base` - Medical knowledge retrieval

## 📦 **Installation**

```bash
pip install hacs-tools
```

## 🚀 **Quick Start (bind tools to an agent)**

```python
from langgraph.prebuilt import create_react_agent
from hacs_utils.integrations.langgraph.hacs_agent_tools import get_hacs_agent_tools

tools = get_hacs_agent_tools()
agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=tools,
    prompt="You are a healthcare assistant using HACS tools."
)

agent.invoke({
    "messages": [{
        "role": "user",
        "content": "Create a Patient Jane Doe (1990-01-15) and return their id"
    }]
})
```

## 🏥 **Healthcare Workflows**

### **Clinical Assessment**
```python
# Generate assessment template
template = use_hacs_tool("create_clinical_template", {
    "template_type": "assessment",
    "focus_area": "cardiology",
    "complexity_level": "standard"
})

# Create knowledge item
knowledge = use_hacs_tool("create_knowledge_item", {
    "title": "AHA Guidelines 2024",
    "content": "New recommendations for hypertension management",
    "knowledge_type": "guideline"
})
```

### **Resource Discovery**
```python
# Discover available models
models = use_hacs_tool("discover_hacs_resources", {
    "category_filter": "clinical",
    "include_examples": True
})

# Get schema for specific model
schema = use_hacs_tool("get_hacs_resource_schema", {
    "resource_type": "Patient",
    "include_validation_rules": True
})
```

## 🔗 **Integration**

HACS Tools integrate with:
- **LangGraph / LangChain** — bind tools directly to models/agents
- **MCP Protocol (via hacs-utils)** — expose tools over JSON‑RPC / streamable HTTP
- **PostgreSQL (via hacs-persistence)** — persistent healthcare data storage
- **Healthcare Systems** — FHIR‑compliant data exchange

## 📊 **Performance**

- **Tool Execution**: <200ms average response time
- **Memory Search**: <100ms for semantic queries
- **Resource Creation**: <50ms for standard resources
- **Validation**: <10ms for schema validation

## 📄 **License**

Apache-2.0 License - see [LICENSE](../../LICENSE) for details.
