# HACS Tools

**4-domain HACS tools for healthcare agents**

Production-ready tools for clinical workflows, resource management, and healthcare AI operations. HACS tools can be used directly from agent frameworks (e.g., LangGraph, LangChain) or exposed over MCP via `hacs-utils`.

## 🛠️ **Tool Categories**

### ✅ Canonical domains
- **Modeling**: instantiate/validate resources, compose bundles, references, graph traversal
- **Extraction**: synthesize mapping, extract variables from text, apply mapping, context summarization
- **Database**: typed/generic CRUD, registry definitions, migrations/status
- **Agents**: todos, delegation, preferences/memory utilities

## 📦 **Installation**

```bash
pip install hacs-tools
```

## 🚀 **Quick Start**

```python
from langgraph.prebuilt import create_react_agent
from hacs_utils.integrations.langchain.tools import langchain_tools

tools = langchain_tools()
agent = create_react_agent(
    model="provider:model-name",  # OpenAI, Anthropic, Google, Azure, Bedrock, etc.
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
- **LangChain / LangGraph** — single tool set, reused across frameworks
- **MCP Protocol (via hacs-utils)** — JSON‑RPC / streamable HTTP tool access
- **PostgreSQL (via hacs-persistence)** — typed and JSONB storage with pgvector option

## 📊 **Performance**

- **Tool Execution**: <200ms average response time
- **Memory Search**: <100ms for semantic queries
- **Resource Creation**: <50ms for standard resources
- **Validation**: <10ms for schema validation

## 📄 **License**

Apache-2.0 License - see [LICENSE](../../LICENSE) for details.
