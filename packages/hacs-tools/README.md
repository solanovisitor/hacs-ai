# HACS Tools

**25+ Healthcare tools for AI agents via Model Context Protocol**

Production-ready tools for clinical workflows, resource management, and healthcare AI operations.

## 🛠️ **Tool Categories**

### 🔍 **Resource Discovery & Development** (5 tools)
- `discover_hacs_resources` - Explore healthcare resource schemas with metadata
- `analyze_resource_fields` - Field analysis with validation rules
- `compare_resource_schemas` - Schema comparison and integration
- `create_clinical_template` - Generate clinical workflow templates
- `create_model_stack` - Compose complex data structures

### 📋 **Record Management** (8 tools)
- `create_hacs_record` / `get_hacs_record_by_id` / `update_hacs_record` / `delete_hacs_record` - Full CRUD
- `validate_hacs_record_data` - Comprehensive validation
- `list_available_hacs_resources` - Resource schema catalog
- `find_hacs_records` - Advanced semantic search
- `search_hacs_records` - Filtered record search

### 🧠 **Memory Management** (5 tools)
- `create_memory` - Store episodic/procedural/executive memories
- `search_memories` - Semantic memory retrieval
- `consolidate_memories` - Merge related memories
- `retrieve_context` - Context-aware memory access
- `analyze_memory_patterns` - Usage pattern analysis

### ✅ **Validation & Schema** (3 tools)
- `get_hacs_resource_schema` - JSON schema exploration
- `create_view_resource_schema` - Custom view creation
- `suggest_view_fields` - Intelligent field suggestions

### 🎨 **Advanced Tools** (3 tools)
- `optimize_resource_for_llm` - LLM-specific optimizations
- `version_hacs_resource` - Resource versioning and tracking

### 📚 **Knowledge Management** (1 tool)
- `create_knowledge_item` - Clinical guidelines and protocols

## 📦 **Installation**

```bash
pip install hacs-tools
```

## 🚀 **Quick Start**

```python
import requests

def call_hacs_tool(tool_name, arguments):
    """Call HACS MCP tools"""
    response = requests.post('http://localhost:8000/', json={
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        },
        "id": 1
    })
    return response.json()

# Create patient record
patient_result = call_hacs_tool("create_hacs_record", {
    "resource_type": "Patient",
    "resource_data": {
        "full_name": "John Smith",
        "birth_date": "1980-05-15",
        "gender": "male"
    }
})

# Store clinical memory
memory_result = call_hacs_tool("create_memory", {
    "content": "Patient reports improved symptoms after treatment",
    "memory_type": "episodic",
    "importance_score": 0.8
})

# Search for related memories
search_result = call_hacs_tool("search_memories", {
    "query": "treatment response",
    "limit": 5
})
```

## 🏥 **Healthcare Workflows**

### **Clinical Assessment**
```python
# Generate assessment template
template = call_hacs_tool("create_clinical_template", {
    "template_type": "assessment",
    "focus_area": "cardiology",
    "complexity_level": "standard"
})

# Create knowledge item
knowledge = call_hacs_tool("create_knowledge_item", {
    "title": "AHA Guidelines 2024",
    "content": "New recommendations for hypertension management",
    "knowledge_type": "guideline"
})
```

### **Resource Discovery**
```python
# Discover available models
models = call_hacs_tool("discover_hacs_resources", {
    "category_filter": "clinical",
    "include_examples": True
})

# Get schema for specific model
schema = call_hacs_tool("get_hacs_resource_schema", {
    "resource_type": "Patient",
    "include_validation_rules": True
})
```

## 🔗 **Integration**

HACS Tools integrate with:
- **MCP Protocol** - Standard tool calling interface
- **LangGraph** - AI agent workflows
- **PostgreSQL** - Persistent healthcare data storage
- **Healthcare Systems** - FHIR-compliant data exchange

## 📊 **Performance**

- **Tool Execution**: <200ms average response time
- **Memory Search**: <100ms for semantic queries
- **Resource Creation**: <50ms for standard resources
- **Validation**: <10ms for schema validation

## 📄 **License**

Apache-2.0 License - see [LICENSE](../../LICENSE) for details.
