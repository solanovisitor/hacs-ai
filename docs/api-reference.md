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
from hacs_utils.visualization import to_markdown

pat = Patient(full_name="Maria Rodriguez", birth_date="1985-03-15", gender="female")
obs = Observation(status=ObservationStatus.FINAL,
                  code=CodeableConcept(text="Blood Pressure"),
                  value_quantity=Quantity(value=128, unit="mmHg"),
                  subject=f"Patient/{pat.id}")

# Render concise Markdown summaries for any resource
print(to_markdown(pat, include_json=False))
print(to_markdown(obs, include_json=False))
```

**Output:**
```
#### Patient

| Field | Value |
|---|---|
| resource_type | Patient |
| id | patient-bb965f5b |
| status | active |
| full_name | Maria Rodriguez |
| gender | female |
| birth_date | 1985-03-15 |
| created_at | 2025-08-26T15:06:57.752748Z |
| updated_at | 2025-08-26T15:06:57.752753Z |

#### Observation

| Field | Value |
|---|---|
| resource_type | Observation |
| id | observation-efbf295e |
| status | final |
| code | Blood Pressure |
| value.quantity | 128.0 mmHg |
| subject | Patient/patient-bb965f5b |
| performer | [] |
| created_at | 2025-08-26T15:06:57.752956Z |
| updated_at | 2025-08-26T15:06:57.752957Z |
```

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
from hacs_utils.visualization import to_markdown

patient = Patient(full_name="John Smith", birth_date="1980-01-15", gender="male")
obs = Observation(status=ObservationStatus.FINAL,
                  code=CodeableConcept(text="Blood Pressure"),
                  value_quantity=Quantity(value=120, unit="mmHg"),
                  subject=f"Patient/{patient.id}")

# Always visualize created records
print("Patient record:")
print(to_markdown(patient, include_json=False))
print("\nObservation record:")
print(to_markdown(obs, include_json=False))
```

Markdown visualization (for static docs):

```python
# Markdown visualization for any resource
from hacs_utils.visualization import to_markdown, annotations_to_markdown
from hacs_models import AnnotatedDocument, Extraction, CharInterval

print(to_markdown(patient, include_json=False))
print(to_markdown(obs, include_json=False))

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

## 🧠 AgentContext

Standardized context for agent tools to resolve model/provider, generation params, and conversational messages.

- Location: `hacs_tools.common.AgentContext`
- Builder: `hacs_tools.common.runnable_context(...) -> AgentContext`
- Fields:
  - `provider: Optional[str]`
  - `model: Optional[str]`
  - `params: Dict[str, Any]` (e.g., temperature, max_tokens)
  - `messages: List[MessageDefinition]` (typed chat history)

Resolution rules (when using `runnable_context`):
- Provider/model/params are derived from `config.models` if present; explicit overrides win.
- Messages resolve in priority: explicit `messages` → `state.messages` → `[]`; dicts are coerced to `MessageDefinition`.

Usage:

```python
from hacs_tools.common import runnable_context

# Typically, tools receive config/state via HACSCommonInput (injected by tool loader)
ctx = runnable_context(config=my_hacs_config, state=my_hacs_state)

# Convert to provider-native messages when needed (example for OpenAI):
from hacs_utils.annotation.conversations import to_openai_messages
client = SomeLLMClient(model=ctx.model)
result = client.chat(messages=to_openai_messages(ctx.messages), **ctx.params)
```

Notes:
- Prefer `HACSCommonInput` for tool inputs; do not expose `config/state` in public schemas.
- Tools should not accept messages directly; they must read them from injected `state`.
- For messages-only resolution, use `get_messages_from_state(config, state, overrides)`.

### `hacs-tools` - Healthcare Tools (4 domains)

Low-level, LLM-friendly tools organized into 4 domains: modeling, extraction, database, agents.

```python
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env", override=True)

from hacs_utils.integrations.common.tool_loader import get_sync_tools, set_injected_params
from hacs_core.config import get_settings
from hacs_models import Actor

# Set up actor context for tools
actor = Actor(name='api-user', role='system', permissions=['*:write','*:read'])
settings = get_settings()
settings.current_actor = actor
set_injected_params({'config': settings})

# Load tools for your framework (langgraph or mcp)
tools = get_sync_tools(framework='langgraph')
print('tool_count:', len(tools))
print('sample:', [t.name for t in tools[:8]])
```

**Output (real):**
```
tool_count: 41
sample: ['pin_resource', 'compose_bundle', 'validate_resource', 'diff_resources', 'validate_bundle', 'add_entries', 'list_models', 'describe_model']
```

**Tool Categories (low-level only):**
- **Resource Management** - CRUD, modeling, bundles
- **Memory Operations** - Clinical memory and context management
- **Schema Discovery** - Resource type exploration and analysis
- **Workflow Modeling** - ActivityDefinition, PlanDefinition, Task adapters

### `hacs-auth` - Healthcare Security

**Actor-based security with role-based permissions**

```python
from hacs_models import Actor
from hacs_core.config import get_current_actor, configure_hacs

# Healthcare provider with permissions
physician = Actor(
    name="Dr. Sarah Chen",
    role="physician",
    permissions=["patient:read", "patient:write", "observation:read", "observation:write", "memory:read", "memory:write"]
)

# Configure HACS with custom actor
configure_hacs(current_actor=physician)
current = get_current_actor()

print(f"👩‍⚕️ Healthcare Provider Created:")
print(f"   Name: {current.name}")
print(f"   Role: {current.role}")
print(f"   Permissions: {current.permissions}")

# Test permission checks
print(f"\n🔐 Permission Checks:")
print(f"   Can read patients: {'patient:read' in current.permissions}")
print(f"   Can write medications: {'medication:write' in current.permissions}")
print(f"   Can write observations: {'observation:write' in current.permissions}")

# Show how tools access current actor via config
from hacs_core.config import get_settings
settings = get_settings()
print(f"\n🛡️ Actor Context for Tools:")
print(f"   Current actor in settings: {settings.current_actor.name if settings.current_actor else 'None'}")
print(f"   Tools can access via config.current_actor")
```

**Output (real):**
```
👩‍⚕️ Healthcare Provider Created:
   Name: Dr. Sarah Chen
   Role: physician
   Permissions: ['patient:read', 'patient:write', 'observation:read', 'observation:write', 'memory:read', 'memory:write']

🔐 Permission Checks:
   Can read patients: True
   Can write medications: False
   Can write observations: True

🛡️ Actor Context for Tools:
   Current actor in settings: Dr. Sarah Chen
   Tools can access via config.current_actor
```

### `hacs-persistence` - Data Storage

**PostgreSQL + pgvector for healthcare data**

```python
from hacs_persistence import HACSConnectionFactory
from hacs_models import Patient
import time

# Database connection factory
factory = HACSConnectionFactory()
print("🔧 Creating database adapter...")

print(f"📊 Database Factory Created:")
print(f"   Factory: {type(factory).__name__}")
print(f"   Available: ✅")

# Example patient resource creation
patient = Patient(full_name="Test Patient", birth_date="1990-01-01", gender="female")

print(f"\n💾 Example Healthcare Resource:")
print(f"   Resource Type: Patient")
print(f"   Patient ID: {patient.id}")
print(f"   Full Name: Test Patient")
print(f"   Status: ✅ Created successfully")

# Vector operations example (conceptual)
print(f"\n🔍 Vector Operations Concept:")
clinical_embedding = [0.1, 0.2, 0.3, -0.1, 0.5, 0.8, -0.3, 0.4]  # 8-dimensional example

print(f"   Resource ID: patient_123")
print(f"   Embedding Dimension: {len(clinical_embedding)}")
print(f"   Metadata: {'{'}'type': 'patient_summary', 'dimension': {len(clinical_embedding)}{'}'}")
print(f"   Status: ✅ Vector operations supported")

# Search concept
print(f"\n🔎 Vector Similarity Search Concept:")
query_embedding = [0.15, 0.18, 0.25, -0.08, 0.52, 0.75, -0.28, 0.35]

print(f"   Query Dimension: {len(query_embedding)}")
print(f"   Resource Type: patient")
print(f"   Top K: 3")
print(f"   Status: ✅ Search capabilities available")
```

**Output:**
```
🔧 Creating database adapter...
📊 Database Factory Created:
   Factory: HACSConnectionFactory
   Available: ✅

💾 Example Healthcare Resource:
   Resource Type: Patient
   Patient ID: patient-d1110cfa
   Full Name: Test Patient
   Status: ✅ Created successfully

🔍 Vector Operations Concept:
   Resource ID: patient_123
   Embedding Dimension: 8
   Metadata: {'type': 'patient_summary', 'dimension': 8}
   Status: ✅ Vector operations supported

🔎 Vector Similarity Search Concept:
   Query Dimension: 8
   Resource Type: patient
   Top K: 3
   Status: ✅ Search capabilities available
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
        "name": "pin_resource",
        "arguments": {
            "resource_type": "Patient",
            "resource_data": {
                "full_name": "John Smith",
                "birth_date": "1980-01-15"
            }
        }
    }
})
```

## 📋 **Complete Tool Reference**

### Resource Management Tools

Use the database domain for records CRUD:

```python
from hacs_tools.domains.modeling import pin_resource

# Create and validate a patient resource
result = pin_resource("Patient", {
    "full_name": "John Smith",
    "birth_date": "1980-01-15",
    "gender": "male"
})

print(f"Create result: {result.success}")
if result.success:
    patient = result.data["resource"]
    print(f"Patient ID: {patient['id']}")
    print(f"Full Name: {patient['full_name']}")
```

**Output:**
```
Create result: True
Patient ID: patient-d9799e7f
Full Name: John Smith
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

### LangGraph Integration

```python
from langgraph.graph import StateGraph, END
from hacs_utils.integrations.common.tool_loader import get_sync_tools

# Get HACS tools for LangGraph
lc_tools = get_sync_tools(framework='langgraph')

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
from hacs_utils.integrations.common.tool_loader import get_sync_tools
lc_tools = get_sync_tools(framework='langchain')
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
- Integration guides: LangGraph (see package README), MCP (see package README)

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
