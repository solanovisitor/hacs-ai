# HACS API Reference

Lightweight, developer-first reference to core packages and integrations. See How-to’s for step-by-step tasks.

> **📚 Related Documentation:**
>
> - [Quick Start Guide](quick-start.md)
> - [How-to’s](how-to/authenticate_actor.md)
> - [HACS Tools Reference](hacs-tools.md)
> - [Complete Context Engineering](tutorials/complete_context_engineering.md)
> - [Medication Extraction](tutorials/medication_extraction.md)

## 🧬 **Core HACS Packages**

### `hacs-models` - Healthcare Data Models
#### Visualize resources and their definitions

```python
from hacs_models import Patient, Observation, CodeableConcept, Quantity
from hacs_models.types import ObservationStatus
from hacs_utils.visualization import resource_to_markdown, resource_docs_to_markdown

pat = Patient(full_name="Maria Rodriguez", birth_date="1985-03-15", gender="female")
obs = Observation(status=ObservationStatus.FINAL,
                  code=CodeableConcept(text="Blood Pressure"),
                  value_quantity=Quantity(value=128, unit="mmHg"),
                  subject=f"Patient/{pat.id}")

# Render concise Markdown summaries for any resource
print(resource_to_markdown(pat, include_json=False))
print(resource_to_markdown(obs, include_json=False))

# Render model definition docs (scope, boundaries, relationships)
print(resource_docs_to_markdown(Patient))
print(resource_docs_to_markdown(Observation))
```

```
### Patient

| Field | Value |
|---|---|
| resource_type | Patient |
| id | patient-... |
| status | active |
| created_at | 2025-... |
| updated_at | 2025-... |

### Observation

| Field | Value |
|---|---|
| resource_type | Observation |
| id | observation-... |
| status | final |
| code.text | Blood Pressure |
| subject | Patient/patient-... |
| created_at | 2025-... |
| updated_at | 2025-... |

### Patient Definition

**Scope & Usage**

Demographics and administrative information for a person or animal receiving care…

**Boundaries**

Patient resources do not contain clinical findings…

**Relationships**
- Referenced by: Observation.subject, Encounter.subject, …

**References**
- Document.subject
- Encounter.subject

### Observation Definition

**Scope & Usage**

Measurements and simple assertions…

**Boundaries**

Do not use for diagnoses/problems…
```

**FHIR-aligned healthcare models**

```python
from hacs_models import Patient, Observation, CodeableConcept, Quantity
from hacs_models.types import ObservationStatus
from hacs_utils.visualization import resource_to_markdown

patient = Patient(full_name="John Smith", birth_date="1980-01-15", gender="male")
obs = Observation(status=ObservationStatus.FINAL,
                  code=CodeableConcept(text="Blood Pressure"),
                  value_quantity=Quantity(value=120, unit="mmHg"),
                  subject=f"Patient/{patient.id}")

# Always visualize created records
print("Patient record:")
print(resource_to_markdown(patient, include_json=False))
print("\nObservation record:")
print(resource_to_markdown(obs, include_json=False))
```

Markdown visualization (for static docs):

```python
# Markdown visualization for any resource
from hacs_utils.visualization import resource_to_markdown, annotations_to_markdown
from hacs_models import AnnotatedDocument, Extraction, CharInterval

print(resource_to_markdown(patient, include_json=False))
print(resource_to_markdown(obs, include_json=False))

doc = AnnotatedDocument(text="BP 128/82, HR 72",
                        extractions=[Extraction(extraction_class="blood_pressure",
                                                extraction_text="128/82",
                                                char_interval=CharInterval(start_pos=3, end_pos=9))])
print(annotations_to_markdown(doc))
```

```
### Patient

| Field | Value |
|---|---|
| resource_type | Patient |
| id | patient-... |
| status | active |
| created_at | 2025-... |
| updated_at | 2025-... |

### Observation

| Field | Value |
|---|---|
| resource_type | Observation |
| id | observation-... |
| status | final |
| code.text | Blood Pressure |
| subject | Patient/patient-... |
| created_at | 2025-... |
| updated_at | 2025-... |

### DiagnosticReport

| Field | Value |
|---|---|
| resource_type | DiagnosticReport |
| id | diagnosticreport-... |
| status | final |
| code.text | Complete Blood Count |
| subject | Patient/patient-... |
| created_at | 2025-... |
| updated_at | 2025-... |

| Class | Span | Snippet |
|---|---|---|
| Blood Pressure | [3-9] | … BP **128/82** , HR 72 … |
```

**Key Classes:**
- `Patient` - Patient demographics and clinical context
- `Observation` - Clinical measurements and findings
- `Encounter` - Healthcare visits and episodes
- `Actor` - Healthcare providers with permissions
- `MemoryBlock` - AI agent memory structures
- `Evidence` - Clinical guidelines and decision support

### `hacs-tools` - Healthcare Tools (4 domains)

Low-level, LLM-friendly tools organized into 4 domains: modeling, extraction, database, agents.

```python
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env", override=True)

from hacs_utils.integrations.common.tool_loader import get_all_hacs_tools_sync, set_injected_params
set_injected_params({"actor_name": "llm-agent-docs"})

tools = get_all_hacs_tools_sync(framework='langchain')
print('tool_count:', len(tools))
print('sample:', [t.name for t in tools[:8]])
```

**Tool Categories (low-level only):**
- **Resource Management** - CRUD, modeling, bundles
- **Memory Operations** - Clinical memory and context management
- **Schema Discovery** - Resource type exploration and analysis
- **Workflow Modeling** - ActivityDefinition, PlanDefinition, Task adapters

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

print(f"👩‍⚕️ Healthcare Provider Created:")
print(f"   Actor ID: {physician.id}")
print(f"   Name: {physician.name}")
print(f"   Role: {physician.role}")
print(f"   Organization: {physician.organization}")
print(f"   Permissions: {physician.permissions}")
print(f"   Active Session: {physician.has_active_session()}")

# Test permission checks
print(f"\n🔐 Permission Checks:")
print(f"   Can read patients: {physician.has_permission('patient:read')}")
print(f"   Can write medications: {physician.has_permission('medication:write')}")
print(f"   Can write observations: {physician.has_permission('observation:write')}")

# Permission-protected functions
@require_permission("patient:read")
def get_patient_data(patient_id: str, **kwargs):
    token_data = kwargs.get("token_data", {})
    actor_name = token_data.get("actor_name", "Unknown")
    return f"Patient data for {patient_id} accessed by {actor_name}"

print(f"\n🛡️ Protected Function Created:")
print(f"   Function: get_patient_data")
print(f"   Required Permission: patient:read")

# Simulate function call with proper permissions
try:
    # In real usage, this would be handled by the authentication middleware
    mock_token_data = {"actor_name": physician.name, "permissions": physician.permissions}
    result = get_patient_data("patient-123", token_data=mock_token_data)
    print(f"   ✅ Access granted: {result}")
except Exception as e:
    print(f"   ❌ Access denied: {e}")
```

**Expected Output:**
```
👩‍⚕️ Healthcare Provider Created:
   Actor ID: actor-dr-sarah-chen-physician-uuid
   Name: Dr. Sarah Chen
   Role: ActorRole.PHYSICIAN
   Organization: Mount Sinai
   Permissions: ['patient:read', 'patient:write', 'observation:write']
   Active Session: False

🔐 Permission Checks:
   Can read patients: True
   Can write medications: False
   Can write observations: True

🛡️ Protected Function Created:
   Function: get_patient_data
   Required Permission: patient:read

   ✅ Access granted: Patient data for patient-123 accessed by Dr. Sarah Chen
```

### `hacs-persistence` - Data Storage

**PostgreSQL + pgvector for healthcare data**

```python
from hacs_persistence import HACSConnectionFactory
import time

# Database connection with migrations
factory = HACSConnectionFactory()
print("🔧 Creating database adapter...")
adapter = factory.get_adapter(auto_migrate=True)

print(f"📊 Database Adapter Created:")
print(f"   Factory: {type(factory).__name__}")
print(f"   Adapter: {type(adapter).__name__}")
print(f"   Auto-migrate: True")

# Store healthcare resources (using patient from previous example)
print(f"\n💾 Storing Healthcare Resource:")
start_time = time.time()
saved_patient = adapter.save_record(patient)
save_time = (time.time() - start_time) * 1000

print(f"   Resource Type: Patient")
print(f"   Patient ID: {saved_patient.get('id', 'N/A')}")
print(f"   Save Time: {save_time:.1f}ms")
print(f"   Status: ✅ Saved successfully")

# Vector operations for clinical embeddings
print(f"\n🔍 Vector Operations:")
clinical_embedding = [0.1, 0.2, 0.3, -0.1, 0.5, 0.8, -0.3, 0.4]  # 8-dimensional example
start_time = time.time()

adapter.store_vector(
    resource_id="patient_123",
    embedding=clinical_embedding,
    metadata={"type": "patient_summary", "dimension": len(clinical_embedding)}
)

vector_time = (time.time() - start_time) * 1000

print(f"   Resource ID: patient_123")
print(f"   Embedding Dimension: {len(clinical_embedding)}")
print(f"   Metadata: {{'type': 'patient_summary', 'dimension': {len(clinical_embedding)}}}")
print(f"   Store Time: {vector_time:.1f}ms")
print(f"   Status: ✅ Vector stored successfully")

# Test vector similarity search
print(f"\n🔎 Vector Similarity Search:")
query_embedding = [0.15, 0.18, 0.25, -0.08, 0.52, 0.75, -0.28, 0.35]
start_time = time.time()

similar_records = adapter.vector_search(
    query_embedding=query_embedding,
    resource_type="patient", 
    top_k=3
)

search_time = (time.time() - start_time) * 1000

print(f"   Query Dimension: {len(query_embedding)}")
print(f"   Resource Type: patient")
print(f"   Top K: 3")
print(f"   Search Time: {search_time:.1f}ms")
print(f"   Results Found: {len(similar_records)}")

if similar_records:
    for i, record in enumerate(similar_records[:2], 1):
        similarity = record.get('similarity_score', 'N/A')
        print(f"   {i}. ID: {record.get('resource_id', 'N/A')} (similarity: {similarity})")
```

**Expected Output:**
```
🔧 Creating database adapter...
📊 Database Adapter Created:
   Factory: HACSConnectionFactory
   Adapter: PostgreSQLAdapter
   Auto-migrate: True

💾 Storing Healthcare Resource:
   Resource Type: Patient
   Patient ID: patient-john-smith-1980-01-15-uuid
   Save Time: 23.4ms
   Status: ✅ Saved successfully

🔍 Vector Operations:
   Resource ID: patient_123
   Embedding Dimension: 8
   Metadata: {'type': 'patient_summary', 'dimension': 8}
   Store Time: 15.2ms
   Status: ✅ Vector stored successfully

🔎 Vector Similarity Search:
   Query Dimension: 8
   Resource Type: patient
   Top K: 3
   Search Time: 8.7ms
   Results Found: 1
   1. ID: patient_123 (similarity: 0.987)
```

### `hacs-utils` - Integration Utilities

**MCP server and framework integrations**

```python
# Visualization helpers available in all environments
from hacs_utils.visualization import visualize_resource, visualize_annotations
html_card = visualize_resource(patient)        # HTML widget (notebook) or str
html_ann = visualize_annotations(doc)          # HTML widget (notebook) or str
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

#### `tools/list` - List Available Tools (with domains and tags)
```python
tools = call_mcp_tool("tools/list")
print(f"Available tools: {len(tools['result']['tools'])}")
# Example tool metadata: {"name": "save_record", "domain": "database", "tags": ["save", "record", "domain:database", "records"]}
```

#### `tools/call` - Execute Tool
```python
result = call_mcp_tool("tools/call", {
    "name": "save_record",
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

Use the database domain for records CRUD:

```python
result = use_hacs_tool("save_record", {
    "resource_type": "Patient",
    "resource_data": {
        "full_name": "John Smith",
        "birth_date": "1980-01-15",
        "gender": "male"
    }
})

patient = use_hacs_tool("read_record", {"resource_type": "Patient", "resource_id": "patient-123"})

result = use_hacs_tool("update_record", {"resource_type": "Patient", "resource_id": "patient-123", "patch": {"agent_context": {"primary_care_provider": "Dr. Johnson"}}})

result = use_hacs_tool("delete_record", {"resource_type": "Patient", "resource_id": "patient-123"})
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

#### `check_memory`
Gather and filter memories for agent context construction.

```python
ctx = use_hacs_tool("check_memory", {
    "actor_id": actor.id,
    "memory_types": ["episodic", "procedural"],
    "min_importance": 0.5,
    "limit": 20
})
```

### Workflow Modeling Tools

#### Template registration and instantiation
Register templates and instantiate stacks.

```python
result = use_hacs_tool("register_stack_template", {"template": {"name": "Example", "version": "1.0.0", "layers": [], "variables": {}}})
```

#### `create_activity_definition`, `create_plan_definition`, `create_task_from_activity`, `complete_task`, `fail_task`
Low-level adapters for workflow resources; keep business logic in workflows.

### Modeling and Schema Tools

#### `describe_models`
Explore available healthcare model types and get summaries.

```python
resources = use_hacs_tool("describe_models", {
    "resource_types": ["Patient", "Observation"],
    "include_examples": True
})
```

#### `list_model_fields`
List fields for a healthcare model.

```python
schema = use_hacs_tool("list_model_fields", {
    "resource_type": "Patient"
})
```

## 🔗 **Framework Integrations**

### LangChain Integration

LangChain packaging is provided via `hacs-utils` integrations. Install extras when needed:

```bash
uv pip install -U hacs-utils[langchain]
```

```
tool_count: 47
sample: ['pin_resource', 'compose_bundle', 'validate_resource', 'diff_resources', 'validate_bundle', 'list_models', 'describe_model', 'describe_models']
```

### LangGraph Integration

```python
from langgraph.graph import StateGraph, END
from hacs_utils.integrations.langchain.tools import langchain_tools

# Get HACS tools for LangGraph
tools = langchain_tools()

# Create healthcare workflow
workflow = StateGraph(state_schema)
workflow.add_node("agent", agent_with_tools)
workflow.add_edge("agent", END)

healthcare_agent = workflow.compile()
```

### Knowledge Management (Evidence)

```python
evidence = use_hacs_tool("search_evidence", {"query": "beta-blockers in heart failure", "top_k": 5})
```

### CrewAI Integration

```python
from crewai import Agent, Task, Crew
from hacs_utils.integrations.langchain.tools import langchain_tools
tools = langchain_tools()
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
summary = patient.summary()  # "Patient patient-123"

# ✅ GOOD: Batch operations (use your own query adapter or DB filtering)
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
validation = use_hacs_tool("validate_record_data", {
    "resource_type": "Patient",
    "data": patient_data
})

if validation["result"]["is_valid"]:
    # Proceed with creation
    result = use_hacs_tool("create_record", {
        "resource_type": "Patient",
        "resource_data": patient_data
    })
else:
    print(f"Validation errors: {validation['result']['errors']}")
```

## 📞 **Support and Resources**

- **[GitHub Repository](https://github.com/solanovisitor/hacs-ai)** - Source code and issues
- **[Documentation Hub](index.md)** - Complete documentation index
- **[Quick Start Guide](quick-start.md)** - Get running in 5 minutes
- **[Healthcare Tools](hacs-tools.md)** - Detailed tool documentation
- Integration guides: LangGraph (see package README), LangChain (see package README), MCP (see package README)

---

*This API reference is maintained as part of the HACS project. For the latest updates, see the [GitHub repository](https://github.com/solanovisitor/hacs-ai).*


## Rendering and Data Views

- Render any HACS resource as an interactive widget with a selector for Rendered / JSON / YAML / Schema:

```python
from hacs_models import Patient
from hacs_utils.visualization import resource_to_html_widget

p = Patient(full_name="Maria Rodriguez", gender="female")
print(resource_to_html_widget(p))
```

- Convert resources across formats in code:

```python
from hacs_utils.visualization import resource_to_json_str, resource_to_yaml_str, resource_to_schema_json_str

print(resource_to_json_str(p))      # JSON string
print(resource_to_yaml_str(p))      # YAML string (falls back to JSON if PyYAML missing)
print(resource_to_schema_json_str(Patient))  # JSON schema for the model
```
