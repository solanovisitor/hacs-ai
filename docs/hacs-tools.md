# HACS Tools Reference

A comprehensive guide to the 50+ HACS tools for healthcare AI agents. Build clinical workflows with typed resources, CRUD operations, agent memory, and specialized healthcare tools.

New to HACS? Start with the [Quick Start](quick-start.md).

## How to use HACS tools

HACS tools work in **two modes**:

- **Python API** (in-process): Import and call functions directly. Best for Python applications and testing.
- **MCP API** (out-of-process): JSON-RPC over HTTP/stdio. Best for non-Python agents or sandboxed contexts.

All examples show both patterns where applicable.

## Quick Start: Save and retrieve a patient

### Prerequisites

```bash
# Install HACS with database support
uv pip install -U hacs-tools hacs-persistence

# Set up environment 
export DATABASE_URL="postgresql://user:pass@localhost/hacs"  
export OPENAI_API_KEY="sk-..."  # Optional, for extraction tools
```

### Python API

```python
from dotenv import load_dotenv
load_dotenv()

from hacs_tools.domains.database import save_resource, read_resource
from hacs_tools.domains.modeling import pin_resource
from hacs_models import Patient

# 1. Create a patient resource
patient_data = {
    "full_name": "Jane Doe",
    "birth_date": "1990-01-01", 
    "gender": "female",
    "active": True
}

# 2. Pin the resource (validates and adds metadata)
result = pin_resource("Patient", patient_data)
if result.success:
    patient_resource = result.data["resource"]
    print(f"✓ Created Patient: {patient_resource['id']}")
else:
    print(f"✗ Error: {result.message}")

# Output:
# ✓ Created Patient: patient_a1b2c3d4

# 3. Save to database
save_result = await save_resource(resource=patient_resource)
print(f"✓ Saved: {save_result.data['resource_id']}")

# Output:  
# ✓ Saved: patient_a1b2c3d4

# 4. Read back from database
read_result = await read_resource("Patient", "patient_a1b2c3d4")
if read_result.success:
    retrieved = read_result.data["resource"]
    print(f"Retrieved: {retrieved['full_name']} (DOB: {retrieved['birth_date']})")
else:
    print(f"Error: {read_result.message}")

# Output:
# Retrieved: Jane Doe (DOB: 1990-01-01)
```

### MCP API

Start the MCP server:

```bash
cd /Users/solanotodeschini/Code/hacs-ai
uv run hacs-utils mcp-server --port 8000
```

Call tools via JSON-RPC:

```python
import requests

# 1. List available tools
response = requests.post("http://localhost:8000/", json={
    "jsonrpc": "2.0",
    "method": "tools/list", 
    "id": 1
})
tools = response.json()["result"]["tools"]
print(f"Found {len(tools)} tools")

# Output:
# Found 23 tools

# 2. Save a patient
response = requests.post("http://localhost:8000/", json={
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "pin_resource",
        "arguments": {
            "resource_type": "Patient",
            "resource_data": {
                "full_name": "John Smith",
                "birth_date": "1985-03-15",
                "gender": "male"
            }
        }
    },
    "id": 2
})
result = response.json()["result"]
print(f"✓ Patient ID: {result['data']['resource']['id']}")

# Output:
# ✓ Patient ID: patient_x9y8z7w6
```

## Core Workflow Tools

### 📊 Data Management (20 tools)

Healthcare data persistence, search, and registry operations with full CRUD support.

#### Core CRUD Operations

##### `save_resource`
**Purpose**: Persist HACS resources to typed tables or generic JSONB storage.

```python
from hacs_tools.domains.database import save_resource

# Save with typed table (recommended)
result = await save_resource(
    resource=patient_dict,
    as_typed=True,           # Use strongly-typed Patient table
    index_semantic=True      # Create vector embeddings for search
)

# Example output:
# HACSResult(
#   success=True,
#   message="Resource saved successfully",
#   data={
#     "resource_id": "patient_abc123",
#     "resource_type": "Patient", 
#     "schema": "hacs_clinical",
#     "table": "patient",
#     "semantic_indexed": True
#   }
# )

# Save to generic JSONB (for flexibility)
result = await save_resource(
    resource=custom_resource,
    as_typed=False,          # Use generic jsonb storage
    schema="custom_schema"
)
```

**Parameters**:
- `resource` (dict): Resource data to save
- `as_typed` (bool): Use typed table (True) or generic JSONB (False) 
- `schema` (str, optional): Schema name override
- `index_semantic` (bool): Create vector embeddings for search

**Returns**: `HACSResult` with resource ID and storage details

##### `read_resource`
**Purpose**: Retrieve resources by type and ID.

```python
from hacs_tools.domains.database import read_resource

# Read from typed table
result = await read_resource("Patient", "patient_abc123")
if result.success:
    patient = result.data["resource"] 
    print(f"Name: {patient['full_name']}")
    print(f"DOB: {patient['birth_date']}")

# Example output:
# Name: Jane Doe
# DOB: 1990-01-01
# 
# HACSResult.data = {
#   "resource": {
#     "id": "patient_abc123",
#     "resource_type": "Patient",
#     "full_name": "Jane Doe",
#     "birth_date": "1990-01-01",
#     "created_at": "2024-01-15T10:30:00Z",
#     ...
#   },
#   "metadata": {
#     "table": "patient",
#     "schema": "hacs_clinical"
#   }
# }

# Read from generic storage
result = await read_resource("CustomType", "custom_123", as_typed=False)
```

**Parameters**:
- `resource_type` (str): HACS resource type name
- `resource_id` (str): Resource ID to retrieve  
- `as_typed` (bool): Read from typed table (True) or generic (False)
- `schema` (str, optional): Schema name override

##### `update_resource`
**Purpose**: Apply partial updates to existing resources.

```python
from hacs_tools.domains.database import update_resource

# Update specific fields
result = await update_resource(
    resource_type="Patient",
    resource_id="patient_abc123",
    patch={
        "active": False,
        "telecom": [{"system": "phone", "value": "555-1234"}],
        "updated_reason": "Phone number updated"
    }
)

# Example output:
# HACSResult(
#   success=True,
#   message="Resource updated successfully", 
#   data={
#     "resource": {
#       "id": "patient_abc123",
#       "full_name": "Jane Doe",  # unchanged
#       "active": False,          # updated
#       "telecom": [...],         # updated
#       "updated_at": "2024-01-15T15:45:00Z"  # auto-updated
#     }
#   }
# )
```

##### `delete_resource`
**Purpose**: Remove resources from storage.

```python
from hacs_tools.domains.database import delete_resource

result = await delete_resource("Patient", "patient_abc123")
if result.success:
    print("✓ Patient deleted successfully")

# Example output: 
# ✓ Patient deleted successfully
#
# HACSResult(
#   success=True,
#   message="Resource deleted successfully",
#   data={
#     "resource_id": "patient_abc123",
#     "resource_type": "Patient",
#     "deleted_at": "2024-01-15T16:00:00Z"
#   }
# )
```

#### Search Operations

##### `search_memories`
**Purpose**: Vector-based search of agent memories with database filters.

```python
from hacs_tools.domains.database import search_memories

# Semantic search with actor filter
result = await search_memories(
    actor_id="dr_chen",
    query="patient blood pressure management",
    filters={"memory_type": "episodic"},
    top_k=5
)

for memory in result.data["memories"]:
    print(f"• {memory['content'][:100]}...")
    print(f"  Relevance: {memory['score']:.3f}")

# Example output:
# • Discussed BP management with Patient Jane Doe. Recommended lifestyle changes and monitoring...
#   Relevance: 0.892
# • Patient reported difficulty with medication adherence. Suggested pill organizer and...
#   Relevance: 0.847
```

##### `search_knowledge_items`
**Purpose**: Search clinical knowledge base using vector similarity.

```python
from hacs_tools.domains.database import search_knowledge_items

# Search evidence with reranking
result = await search_knowledge_items(
    query="hypertension treatment guidelines ACE inhibitors",
    top_k=3,
    filters={"source": "pubmed", "year_min": 2020},
    rerank=True
)

for item in result.data["items"]:
    print(f"Title: {item['title']}")
    print(f"Source: {item['source']} ({item['year']})")
    print(f"Relevance: {item['relevance_score']:.3f}\n")

# Example output:
# Title: ACE Inhibitors in Hypertension Management: 2023 Guidelines
# Source: pubmed (2023)  
# Relevance: 0.934
#
# Title: Comparative Effectiveness of ACE Inhibitors vs ARBs
# Source: pubmed (2022)
# Relevance: 0.891
```

#### Registry Operations

##### `register_model_version`
**Purpose**: Register model schemas in the HACS registry for versioning.

```python
from hacs_tools.domains.database import register_model_version

# Register a custom patient extension
result = await register_model_version(
    resource_name="ExtendedPatient",
    version="1.2.0", 
    schema_def={
        "type": "object",
        "properties": {
            "full_name": {"type": "string"},
            "birth_date": {"type": "string", "format": "date"},
            "genetic_markers": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["full_name", "birth_date"]
    },
    tags=["patient", "genomics", "extended"]
)

print(f"✓ Registered: {result.data['registry_id']}")

# Example output:
# ✓ Registered: extended_patient_v1.2.0_abc123
```

#### Database Administration

##### `run_migrations`
**Purpose**: Execute database schema migrations to ensure consistency.

```python
from hacs_tools.domains.database import run_migrations

# Run all pending migrations
result = await run_migrations()
print(f"Applied {len(result.data['applied'])} migrations:")
for migration in result.data['applied']:
    print(f"  • {migration['name']} - {migration['description']}")

# Example output:
# Applied 3 migrations:
#   • 20240115_001_patient_telecom - Add telecom fields to patient table
#   • 20240115_002_observation_index - Add semantic index to observation table  
#   • 20240115_003_memory_schema - Update memory table schema
```

##### `get_db_status`
**Purpose**: Check database connection and migration state.

```python
from hacs_tools.domains.database import get_db_status

result = await get_db_status()
status = result.data

print(f"Connection: {'✓' if status['connected'] else '✗'}")
print(f"Schema version: {status['schema_version']}")
print(f"Pending migrations: {status['pending_migrations']}")

# Example output:
# Connection: ✓
# Schema version: 2.1.3
# Pending migrations: 0
```

### 🏗️ Resource Modeling (5 tools)

Tools for creating, validating, and composing HACS resources with proper metadata and type safety.

#### `pin_resource`
**Purpose**: Create and validate HACS resources with proper metadata.

```python
from hacs_tools.domains.modeling import pin_resource

# Create a medication request
med_data = {
    "status": "active",
    "intent": "order", 
    "medication_codeable_concept": {
        "text": "Lisinopril 10mg",
        "coding": [{
            "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
            "code": "314077"
        }]
    },
    "subject": {"reference": "Patient/patient_abc123"},
    "dosage_instruction": [{
        "text": "Take one tablet daily"
    }]
}

result = pin_resource("MedicationRequest", med_data)
if result.success:
    resource = result.data["resource"]
    print(f"✓ Created MedicationRequest: {resource['id']}")
    print(f"Status: {resource['status']}")
    print(f"Medication: {resource['medication_codeable_concept']['text']}")

# Example output:
# ✓ Created MedicationRequest: medreq_def456
# Status: active
# Medication: Lisinopril 10mg
```

#### `compose_bundle`
**Purpose**: Combine multiple resources into a FHIR Bundle.

```python
from hacs_tools.domains.modeling import compose_bundle

# Create a bundle with patient and observations
resources = [patient_resource, bp_observation, hr_observation]

result = compose_bundle(
    bundle_type="collection",
    title="Patient Visit Summary",
    resources=resources
)

bundle = result.data["bundle"]
print(f"✓ Bundle contains {bundle['total']} resources")
for entry in bundle["entry"]:
    resource = entry["resource"]
    print(f"  • {resource['resource_type']}: {resource['id']}")

# Example output:
# ✓ Bundle contains 3 resources
#   • Patient: patient_abc123
#   • Observation: obs_bp_789
#   • Observation: obs_hr_456
```

#### `validate_resource`
**Purpose**: Validate resources against HACS schemas and business rules.

```python
from hacs_tools.domains.modeling import validate_resource

# Validate with comprehensive checking
result = validate_resource(
    resource=medication_request,
    check_references=True,    # Validate reference integrity
    check_business_rules=True # Apply clinical validation rules  
)

if result.success:
    print("✓ Resource is valid")
    if result.data.get("warnings"):
        for warning in result.data["warnings"]:
            print(f"⚠ Warning: {warning}")
else:
    print("✗ Validation failed:")
    for error in result.data["errors"]:
        print(f"  • {error['field']}: {error['message']}")

# Example output:
# ✓ Resource is valid
# ⚠ Warning: dosage_instruction[0] missing timing information
```

### 🤖 Agent Operations (10 tools)

Tools for agent working memory, task planning, long-term memory, and context management.

#### Working Memory (Scratchpad)

##### `write_scratchpad`
**Purpose**: Record observations, decisions, and working notes.

```python
from hacs_tools.domains.agents import write_scratchpad

# Record a clinical observation
result = write_scratchpad(
    content="Patient reports 7/10 chest pain, onset 2 hours ago. No radiation to arms. Vital signs stable.",
    entry_type="observation",
    session_id="visit_20240115",
    tags=["chest_pain", "assessment"]
)

print(f"✓ Recorded entry: {result.data['entry_id']}")

# Example output:
# ✓ Recorded entry: scratchpad_ghi789
```

##### `read_scratchpad`
**Purpose**: Retrieve working memory entries for context.

```python
from hacs_tools.domains.agents import read_scratchpad

# Get recent observations for this session
result = read_scratchpad(
    session_id="visit_20240115",
    entry_type="observation", 
    limit=5
)

for entry in result.data["entries"]:
    print(f"[{entry['created_at']}] {entry['content'][:80]}...")

# Example output:
# [2024-01-15T14:30:00Z] Patient reports 7/10 chest pain, onset 2 hours ago. No radiation to arms...
# [2024-01-15T14:25:00Z] Reviewed patient history: 3 prior ED visits for chest pain, all negative...
```

#### Task Planning

##### `create_todo`
**Purpose**: Create structured task items for clinical workflows.

```python
from hacs_tools.domains.agents import create_todo

# Create urgent clinical task
result = create_todo(
    content="Order cardiac enzymes and chest X-ray for patient with chest pain",
    priority="high",
    clinical_urgency="urgent",
    due_date="2024-01-15T16:00:00Z",
    context={
        "patient_id": "patient_abc123",
        "session_id": "visit_20240115"
    }
)

print(f"✓ Created todo: {result.data['todo_id']}")

# Example output:
# ✓ Created todo: todo_urgent_jkl012
```

##### `list_todos`
**Purpose**: Retrieve and filter task lists.

```python
from hacs_tools.domains.agents import list_todos

# Get high-priority pending tasks
result = list_todos(
    status="pending",
    priority_min=3,  # High priority and above
    limit=10
)

print(f"Found {len(result.data['todos'])} high-priority tasks:")
for todo in result.data["todos"]:
    print(f"• [{todo['priority']}] {todo['content'][:60]}...")
    if todo.get('clinical_urgency'):
        print(f"  Clinical urgency: {todo['clinical_urgency']}")

# Example output:
# Found 3 high-priority tasks:
# • [high] Order cardiac enzymes and chest X-ray for patient with chest...
#   Clinical urgency: urgent
# • [high] Review medication interactions for patient on multiple...
#   Clinical urgency: moderate
```

#### Long-term Memory

##### `store_memory`
**Purpose**: Persist important information for future reference.

```python
from hacs_tools.domains.agents import store_memory

# Store procedural knowledge
result = store_memory(
    content="When evaluating chest pain in young patients, always consider anxiety/panic disorder if cardiac workup is negative. Patient education about anxiety symptoms is crucial.",
    memory_type="procedural",
    actor_id="dr_chen", 
    tags=["chest_pain", "anxiety", "young_patients"],
    context={"domain": "emergency_medicine", "evidence_level": "clinical_experience"}
)

print(f"✓ Stored memory: {result.data['memory_id']}")

# Example output:
# ✓ Stored memory: memory_mno345
```

##### `retrieve_memories`
**Purpose**: Find relevant memories using semantic search.

```python
from hacs_tools.domains.agents import retrieve_memories

# Retrieve relevant clinical knowledge
result = retrieve_memories(
    query="chest pain young patient anxiety",
    actor_id="dr_chen",
    memory_type="procedural",
    limit=3
)

for memory in result.data["memories"]:
    print(f"• {memory['content'][:100]}...")
    print(f"  Relevance: {memory['relevance_score']:.3f}")
    print(f"  Tags: {', '.join(memory.get('tags', []))}\n")

# Example output:
# • When evaluating chest pain in young patients, always consider anxiety/panic disorder if...
#   Relevance: 0.924
#   Tags: chest_pain, anxiety, young_patients
```

#### Context Management

##### `inject_preferences`
**Purpose**: Apply actor preferences to messages and responses.

```python
from hacs_tools.domains.agents import inject_preferences

# Apply communication preferences
message = {
    "role": "assistant",
    "content": "The patient should start on ACE inhibitor therapy."
}

result = inject_preferences(
    message=message,
    actor_id="dr_chen",
    preference_scope="communication_style"
)

enhanced_message = result.data["message"]
print(f"Enhanced: {enhanced_message['content']}")

# Example output:
# Enhanced: Based on current guidelines, I recommend initiating ACE inhibitor therapy for this patient. Please consider starting with lisinopril 5mg daily, with close monitoring of blood pressure and renal function. Would you like me to provide patient education materials about this medication?
```

##### `select_tools_for_task`
**Purpose**: Choose relevant tools using semantic matching.

```python
from hacs_tools.domains.agents import select_tools_for_task

# Get tools for clinical documentation
result = select_tools_for_task(
    task_description="Create comprehensive discharge summary for patient with heart failure",
    max_tools=8,
    domain_filter="modeling"
)

for tool in result.data["selected_tools"]:
    print(f"• {tool['name']}: {tool['description'][:60]}...")
    print(f"  Relevance: {tool['relevance_score']:.3f}")

# Example output:  
# • pin_resource: Create and validate HACS resources with proper metadata...
#   Relevance: 0.887
# • compose_bundle: Combine multiple resources into a FHIR Bundle...
#   Relevance: 0.823
```

### 🔍 Advanced Features (Optional)

#### Extraction Tools (LLM-dependent)

These tools require LLM integration and are optional based on your setup.

##### `extract_variables`
**Purpose**: Extract structured data from clinical text using LLMs.

```python
from hacs_tools.domains.extraction import extract_variables

# Extract vital signs from clinical notes  
result = extract_variables(
    text="Patient presents with BP 140/90, HR 88, temp 98.6F, O2 sat 97% on room air",
    variables=["systolic_bp", "diastolic_bp", "heart_rate", "temperature", "oxygen_saturation"],
    provider="openai"
)

if result.success:
    extracted = result.data["variables"]
    print("Extracted variables:")
    for var, value in extracted.items():
        print(f"  {var}: {value}")

# Example output:
# Extracted variables:
#   systolic_bp: 140
#   diastolic_bp: 90  
#   heart_rate: 88
#   temperature: 98.6
#   oxygen_saturation: 97
```

#### Terminology Tools (Optional)

Clinical coding and terminology management tools.

##### `search_umls`
**Purpose**: Search UMLS terminology for clinical codes.

```python  
from hacs_tools.domains.terminology import search_umls

# Find codes for hypertension
result = search_umls(
    query="essential hypertension",
    source_vocabularies=["SNOMEDCT_US", "ICD10CM"],
    max_results=5
)

for concept in result.data["concepts"]:
    print(f"• {concept['preferred_name']}")
    print(f"  Code: {concept['code']} ({concept['vocabulary']})")
    print(f"  Definition: {concept['definition'][:80]}...\n")

# Example output:
# • Essential hypertension
#   Code: 59621000 (SNOMEDCT_US)
#   Definition: Hypertension that occurs without apparent cause; idiopathic...
```

## Error Handling and Patterns

### HACSResult Pattern

All HACS tools return a consistent `HACSResult` object:

```python
from hacs_models import HACSResult

# Always check success before using data
result = await some_tool(parameters...)

if result.success:
    data = result.data
    print(f"✓ {result.message}")
    # Use data safely
else:
    print(f"✗ Error: {result.message}")
    if result.error:
        print(f"Details: {result.error}")
        # Handle error gracefully
```

### Async/Sync Patterns

Most database tools are async; agent tools are typically sync:

```python
# Database tools (async)
await save_resource(resource)
await search_memories(query="...")

# Agent tools (sync)  
write_scratchpad(content="...")
result = create_todo(content="...")

# Check tool documentation for async status
from hacs_tools import get_tool
tool = get_tool("save_resource") 
print(f"Async: {tool.is_async}")  # True
```

### Authentication Requirements

Tools that require actor authentication:

```python
# Tools requiring authentication inject actor automatically
from hacs_utils.integrations.common.tool_loader import set_injected_params

set_injected_params({"actor_name": "dr_chen"})

# Now all authenticated tools use this actor
result = store_memory(content="...")  # Automatically uses dr_chen
result = create_todo(content="...")   # Automatically uses dr_chen
```

## Discovery and Registry

### List All Available Tools

```python
# Python API - get all tools
from hacs_registry import get_global_tool_registry

registry = get_global_tool_registry()
all_tools = registry.get_all_tools()

for tool in all_tools:
    print(f"{tool.name} ({tool.domain}) - {tool.description[:60]}...")

# MCP API - get curated tools
import requests
response = requests.post("http://localhost:8000/", json={
    "jsonrpc": "2.0", 
    "method": "tools/list",
    "id": 1
})

tools = response.json()["result"]["tools"]
print(f"MCP exposes {len(tools)} tools")
```

### Search Tools by Domain  

```python
# Find all modeling tools
modeling_tools = registry.get_tools_by_domain("modeling")

for tool in modeling_tools:
    print(f"• {tool.name}: {tool.description}")

# Example output:
# • pin_resource: Create and validate HACS resources with proper metadata
# • compose_bundle: Combine multiple resources into a FHIR Bundle
# • validate_resource: Validate resources against HACS schemas
# • diff_resources: Compare two resources and show differences
# • validate_bundle: Validate bundle structure and resource references
```

### Tool Categories Summary

| Domain | Tools | Purpose |
|--------|--------|---------|
| **📊 Database** | 20 | CRUD, search, registry, admin |
| **🤖 Agents** | 10 | Memory, tasks, context, preferences |
| **🏗️ Modeling** | 5 | Resource creation, validation, bundles |
| **🔍 Extraction** | 4 | LLM-based data extraction (optional) |
| **🧬 Terminology** | 5 | Clinical coding, UMLS search (optional) |
| **🏥 Resource-specific** | 15+ | Specialized tools for Patient, Observation, etc. |

For implementation examples and integration patterns, see the [Quick Start](quick-start.md) guide.

---

*This reference covers all 50+ HACS tools with real examples and outputs. For the latest tool additions, check the registry with `get_all_tools()`.*
