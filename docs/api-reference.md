# HACS API Reference

**Complete API documentation for HACS (Healthcare Agent Communication Standard)**

This reference covers all HACS packages, tools, and integration patterns for healthcare AI development.

> **📚 Related Documentation:**
> - [Hacs Tools Reference](healthcare-tools.md) - Detailed tool documentation
> - [Basic Usage Guide](basic-usage.md) - Essential patterns and examples
> - [Integration Guide](integrations.md) - Framework integrations
> - [Quick Start Guide](quick-start.md) - Get running in 5 minutes

## 🧬 **Core HACS Packages**

### `hacs-models` - Healthcare Data Models

**FHIR-compliant healthcare models for AI agents**

```python
from hacs_models import Patient, Observation, Actor, MemoryBlock

# Core healthcare models
patient = Patient(
    full_name="John Smith",
    birth_date="1980-01-15",
    gender="male",
    agent_context={"chief_complaint": "routine_checkup"}
)

# Clinical observations
observation = Observation(
    status="final",
    code_text="Blood Pressure", 
    value="120",
    unit="mmHg",
    patient_id=patient.id
)

# Clinical memory for AI agents
memory = MemoryBlock(
    memory_type="episodic",
    content="Patient reports feeling well, no concerns",
    importance_score=0.7,
    tags=["wellness", "routine"]
)
```

**Key Classes:**
- `Patient` - Patient demographics and clinical context
- `Observation` - Clinical measurements and findings
- `Encounter` - Healthcare visits and episodes
- `Actor` - Healthcare providers with permissions
- `MemoryBlock` - AI agent memory structures
- `Evidence` - Clinical guidelines and decision support

### `hacs-tools` - Healthcare Tool Registry

**42+ Hacs Tools for clinical workflows**

```python
from hacs_tools import use_hacs_tool

# Create healthcare records
result = use_hacs_tool("create_hacs_record", {
    "resource_type": "Patient",
    "resource_data": patient.model_dump()
})

# Search clinical records  
search_result = use_hacs_tool("search_hacs_records", {
    "query": "diabetes management",
    "resource_types": ["Patient", "Observation"],
    "limit": 10
})

# Register a stack template
result = use_hacs_tool("register_stack_template", {"template": {"name": "Example", "version": "1.0.0", "layers": [], "variables": {}}})
```

**Tool Categories:**
- **Resource Management** - CRUD operations for healthcare data
- **Memory Operations** - Clinical memory and context management
- **Schema Discovery** - Resource type exploration and analysis
- **Clinical Workflows** - Template generation and protocol execution
- **Vector Search** - Semantic search for medical knowledge

### `hacs-auth` - Healthcare Security

**Actor-based security with role-based permissions**

```python
from hacs_auth import Actor, ActorRole, require_permission

# Healthcare provider with permissions
physician = Actor(
    name="Dr. Sarah Chen",
    role=ActorRole.PHYSICIAN,
    organization="Mount Sinai",
    permissions=["patient:read", "patient:write", "observation:write"]
)

# Permission-protected functions
@require_permission("patient:read")
def get_patient_data(patient_id: str, **kwargs):
    return f"Patient data for {patient_id}"
```

### `hacs-persistence` - Data Storage

**PostgreSQL + pgvector for healthcare data**

```python
from hacs_persistence import HACSConnectionFactory

# Database connection with migrations
factory = HACSConnectionFactory()
adapter = factory.get_adapter(auto_migrate=True)

# Store healthcare resources
saved_patient = adapter.save_resource(patient)

# Vector operations for clinical embeddings
adapter.store_vector(
    resource_id="patient_123",
    embedding=[0.1, 0.2, 0.3],  # Clinical text embedding
    metadata={"type": "patient_summary"}
)
```

### `hacs-utils` - Integration Utilities

**MCP server and framework integrations**

```python
# Start MCP server
from hacs_utils.mcp.cli import run_server
run_server()

# LangChain integration
from hacs_utils.integrations.langchain import get_hacs_tools
tools = get_hacs_tools()

# LangGraph integration
from hacs_utils.integrations.langgraph import get_hacs_agent_tools
agent_tools = get_hacs_agent_tools()
```

## 🛠️ **MCP Server API**

The HACS MCP server provides all tools via JSON-RPC at `HACS_MCP_SERVER_URL`.

### Base Request Format

```python
import requests
import os

def call_mcp_tool(method, params=None):
    server_url = os.getenv('HACS_MCP_SERVER_URL', 'http://127.0.0.1:8000')
    response = requests.post(server_url, json={
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": 1
    })
    return response.json()
```

### Available Endpoints

#### `tools/list` - List Available Tools
```python
tools = call_mcp_tool("tools/list")
print(f"Available tools: {len(tools['result']['tools'])}")
```

#### `tools/call` - Execute Tool
```python
result = call_mcp_tool("tools/call", {
    "name": "create_hacs_record",
    "arguments": {
        "resource_type": "Patient",
        "resource_data": {
            "full_name": "John Smith",
            "birth_date": "1980-01-15"
        }
    }
})
```

## 📋 **Complete Tool Reference**

### Resource Management Tools

#### `create_hacs_record`
Create new healthcare resources with FHIR compliance.

```python
result = use_hacs_tool("create_hacs_record", {
    "resource_type": "Patient",  # Required: Resource type
    "resource_data": {           # Required: Resource data
        "full_name": "John Smith",
        "birth_date": "1980-01-15",
        "gender": "male"
    }
})
```

#### `get_hacs_record_by_id`
Retrieve healthcare resource by ID.

```python
patient = use_hacs_tool("get_hacs_record_by_id", {
    "resource_type": "Patient",  # Required: Resource type
    "resource_id": "patient-123" # Required: Resource ID
})
```

#### `update_hacs_record`
Update existing healthcare resource.

```python
result = use_hacs_tool("update_hacs_record", {
    "resource_type": "Patient",    # Required: Resource type
    "resource_id": "patient-123",  # Required: Resource ID
    "resource_data": {             # Required: Updated data
        "agent_context": {
            "primary_care_provider": "Dr. Johnson"
        }
    }
})
```

#### `delete_hacs_record`
Remove healthcare resource.

```python
result = use_hacs_tool("delete_hacs_record", {
    "resource_type": "Patient",    # Required: Resource type
    "resource_id": "patient-123"   # Required: Resource ID
})
```

#### `search_hacs_records`
Advanced search with filters and semantic queries.

```python
results = use_hacs_tool("search_hacs_records", {
    "query": "diabetes patients",        # Required: Search query
    "resource_types": ["Patient"],       # Optional: Resource types
    "filters": {                         # Optional: Additional filters
        "date_range": {
            "start": "2024-01-01",
            "end": "2024-12-31"
        }
    },
    "limit": 10                          # Optional: Result limit
})
```

### Memory Operations Tools

#### `create_hacs_memory`
Store clinical memories for AI agents.

```python
memory = use_hacs_tool("create_hacs_memory", {
    "content": "Patient reports improvement after treatment",  # Required
    "memory_type": "episodic",                               # Required: episodic, semantic, working
    "importance_score": 0.8,                                 # Optional: 0.0-1.0
    "tags": ["treatment", "improvement"],                    # Optional: List of tags
    "context_metadata": {                                    # Optional: Additional context
        "patient_id": "patient-123",
        "encounter_id": "encounter-456"
    }
})
```

#### `search_hacs_memories`
Semantic search of clinical memories.

```python
memories = use_hacs_tool("search_hacs_memories", {
    "query": "medication response",      # Required: Search query
    "memory_type": "episodic",           # Optional: Memory type filter
    "limit": 5,                          # Optional: Result limit
    "similarity_threshold": 0.7          # Optional: Minimum similarity
})
```

### Clinical Workflow Tools

#### Template registration and instantiation
Register templates and instantiate stacks.

```python
result = use_hacs_tool("register_stack_template", {"template": {"name": "Example", "version": "1.0.0", "layers": [], "variables": {}}})
```

#### `execute_clinical_workflow`
Execute structured clinical protocols.

```python
workflow = use_hacs_tool("execute_clinical_workflow", {
    "workflow_type": "diabetes_assessment",  # Required: Workflow type
    "patient_id": "patient-123",            # Required: Patient ID
    "template_id": "template-456",          # Optional: Template to use
    "actor_id": "physician-789"             # Required: Executing provider
})
```

### Discovery and Schema Tools

#### `discover_hacs_resources`
Explore available healthcare resource types.

```python
resources = use_hacs_tool("discover_hacs_resources", {
    "category_filter": "clinical",       # Optional: Filter by category
    "include_examples": True,            # Optional: Include example data
    "include_validation_rules": True     # Optional: Include validation info
})
```

#### `get_hacs_resource_schema`
Get JSON schema for healthcare resources.

```python
schema = use_hacs_tool("get_hacs_resource_schema", {
    "resource_type": "Patient",          # Required: Resource type
    "include_validation_rules": True,    # Optional: Include validation
    "format": "json_schema"              # Optional: Output format
})
```

## 🔗 **Framework Integrations**

### LangChain Integration (deprecated)

The LangChain adapter is deprecated and has been removed. Use LangGraph integration below.

### LangGraph Integration

```python
from langgraph.graph import StateGraph, END
from hacs_utils.integrations.langgraph import get_hacs_agent_tools

# Get HACS tools for LangGraph
tools = get_hacs_agent_tools()

# Create healthcare workflow
workflow = StateGraph(state_schema)
workflow.add_node("agent", agent_with_tools)
workflow.add_edge("agent", END)

healthcare_agent = workflow.compile()
```

### CrewAI Integration

```python
from crewai import Agent, Task, Crew
from hacs_utils.integrations.langchain import get_hacs_tools_by_category

# Create specialized healthcare agents
clinical_agent = Agent(
    role="Clinical Specialist",
    goal="Provide clinical decision support",
    tools=get_hacs_tools_by_category("clinical_workflows")
)

research_agent = Agent(
    role="Medical Researcher", 
    goal="Analyze clinical evidence",
    tools=get_hacs_tools_by_category("memory_operations")
)
```

## ⚙️ **Configuration**

### Environment Variables

```bash
# Required - Database
DATABASE_URL=postgresql://hacs:password@localhost:5432/hacs

# Required - LLM Provider (choose one)
ANTHROPIC_API_KEY=sk-ant-...     # Recommended for healthcare
OPENAI_API_KEY=sk-...            # Alternative

# Optional - MCP Server
HACS_MCP_SERVER_URL=http://127.0.0.1:8000
HACS_ENVIRONMENT=development     # development, staging, production
HACS_DEV_MODE=true              # Bypass some security in dev

# Optional - Organization
HACS_ORGANIZATION=your_health_system
HEALTHCARE_SYSTEM_NAME=Your Health System

# Optional - Security
HACS_API_KEY=key1,key2         # Comma-separated API keys
HACS_API_KEY_FILE=/path/to/keys.txt
```

### Docker Configuration

```yaml
# docker-compose.yml
services:
  hacs-postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: hacs
      POSTGRES_USER: hacs
      POSTGRES_PASSWORD: hacs_dev
      
  hacs-mcp-server:
    build: .
    ports:
      - "${HACS_MCP_PORT:-8000}:8000"
    environment:
      - DATABASE_URL=postgresql://hacs:hacs_dev@postgres:5432/hacs
      - HACS_ENVIRONMENT=development
```

## 🔐 **Security Reference**

### Actor-Based Permissions

```python
from hacs_auth import Actor, ActorRole

# Healthcare roles with different permissions
physician = Actor(
    role=ActorRole.PHYSICIAN,
    permissions=[
        "patient:read", "patient:write",
        "observation:read", "observation:write", 
        "memory:read", "memory:write"
    ]
)

nurse = Actor(
    role=ActorRole.NURSE,
    permissions=[
        "patient:read",
        "observation:read", "vitals:write"
    ]
)

ai_agent = Actor(
    role=ActorRole.AGENT,
    permissions=[
        "patient:read",
        "memory:read", "analytics:population"
    ]
)
```

### Session Management

```python
# Start actor session
physician.start_session("session_123")

# Check session status
if physician.has_active_session():
    print("Session is active")

# Session timeout (default 8 hours)
if physician.is_session_expired(timeout_minutes=480):
    print("Session expired, need to re-authenticate")
```

## 📊 **Performance Guidelines**

### Optimal Tool Usage

```python
# ✅ GOOD: Use selective data extraction
patient_data = patient.model_dump(include={
    "full_name", "birth_date", "agent_context"
})

# ❌ AVOID: Full serialization with unnecessary fields
patient_data = patient.model_dump()  # Includes FHIR overhead

# ✅ GOOD: Use text summaries for LLM context
summary = patient.get_text_summary()  # "Patient patient-123"

# ✅ GOOD: Batch operations
results = use_hacs_tool("search_hacs_records", {
    "query": "diabetes",
    "limit": 50  # Process multiple records efficiently
})
```

### Memory Management

```python
# ✅ GOOD: Set importance scores for relevance filtering
memory = MemoryBlock(
    content="Clinical finding",
    importance_score=0.9,  # High importance
    memory_type="episodic"
)

# ✅ GOOD: Use tags for efficient retrieval
memory.tags = ["cardiology", "urgent", "followup_needed"]

# ✅ GOOD: Include relevant context metadata
memory.context_metadata = {
    "patient_id": "patient-123",
    "clinical_domain": "cardiology",
    "urgency_level": "high"
}
```

## 🚨 **Error Handling**

### Common Error Patterns

```python
def safe_hacs_tool_call(tool_name, arguments):
    """Robust HACS tool calling with error handling"""
    try:
        result = use_hacs_tool(tool_name, arguments)
        
        if "error" in result:
            print(f"Tool error: {result['error']}")
            return None
            
        return result.get("result")
        
    except requests.exceptions.ConnectionError:
        print("MCP server not available")
        return None
        
    except requests.exceptions.Timeout:
        print("Tool call timed out")
        return None
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
```

### Validation Patterns

```python
# Validate before creating resources
validation = use_hacs_tool("validate_hacs_record_data", {
    "resource_type": "Patient",
    "data": patient_data
})

if validation["result"]["is_valid"]:
    # Proceed with creation
    result = use_hacs_tool("create_hacs_record", {
        "resource_type": "Patient",
        "resource_data": patient_data
    })
else:
    print(f"Validation errors: {validation['result']['errors']}")
```

## 📞 **Support and Resources**

- **[GitHub Repository](https://github.com/solanovisitor/hacs-ai)** - Source code and issues
- **[Documentation Hub](README.md)** - Complete documentation index
- **[Quick Start Guide](quick-start.md)** - Get running in 5 minutes
- **[Healthcare Tools](healthcare-tools.md)** - Detailed tool documentation
- **[Integration Examples](integrations.md)** - Framework integration patterns

---

*This API reference is maintained as part of the HACS project. For the latest updates, see the [GitHub repository](https://github.com/solanovisitor/hacs-ai).*
