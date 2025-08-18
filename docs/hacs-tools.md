# HACS Tools Reference

Low-level HACS tools for resource modeling, bundles, schema discovery, memory, and minimal workflow modeling. High-level, business-specific tools have been removed; keep prompts/logic in workflows.

New to HACS? Start with the [Quick Start](quick-start.md).

## How to call tools (two modes)

- Python API (in-process): import functions from `hacs_tools.domains.*` and call them directly (sync/async as defined). Best for Python apps/tests.
- MCP API (out-of-process): call `tools/call` over JSON-RPC with the tool `name` and `arguments`. Best for agents, non-Python clients, or sandboxed contexts.

Notes:
- Function names are identical in both modes. Some tools are async in Python (e.g., database); await them when used directly.
- `tools/list` returns a curated set for quick starts. Any registry tool can still be called via `tools/call` by name.

Examples

Python API (Terminology):
```python
from hacs_tools.domains.terminology import get_possible_codes
report = get_possible_codes(composition_doc, query="hypertension")
```

MCP API (CRUD):
```python
import requests
requests.post("http://localhost:8000/", json={
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {"name": "save_record", "arguments": {"resource_type": "Patient", "resource_data": {"full_name": "Jane Doe"}}},
  "id": 1
})
```

## Context Engineering Tool Categories

Each tool category implements specific context engineering strategies optimized for healthcare AI:

### 🔍 Resource Management (8 tools)

**🎯 SELECT + 🔒 ISOLATE Strategies**: Healthcare resource operations with selective data access and compliance boundaries.

Core CRUD operations implementing context selection and isolation for healthcare AI agents:

#### `save_record`
**🎯 SELECT**: Create healthcare resources with selective data extraction

```python
# SELECT: Create patient with only essential clinical context
patient_data = patient.model_dump(exclude={
    "text", "contained", "extension", "modifier_extension"  # Exclude FHIR overhead
})

result = use_tool("save_record", {
    "resource_type": "Patient",
    "resource_data": patient_data  # Optimized clinical context only
})
```

#### `read_record`
Retrieve healthcare resource by ID and type

```python
patient = use_tool("read_record", {
    "resource_type": "Patient", 
    "resource_id": "patient-123"
})
```

#### `update_record`
Update existing healthcare resource

```python
use_tool("update_record", {
    "resource_type": "Patient",
    "resource_id": "patient-123", 
    "resource_data": {
        "agent_context": {
            "insurance_provider": "Blue Cross"
        }
    }
})
```

#### `delete_record`
Remove healthcare resource

```python
use_tool("delete_record", {
    "resource_type": "Patient",
    "resource_id": "patient-123"
})
```

#### `validate_resource`
Validate resource against model constraints

```python
validation = use_tool("validate_resource", {
    "resource_type": "Observation",
    "data": {
        "code_text": "Blood Pressure",
        "value": "120/80",
        "unit": "mmHg"
    }
})
```

#### `list_models`
List available HACS model types

```python
models = use_tool("list_models", {})
```

 

### 🧠 Memory Operations (5 tools)

**🖊️ WRITE + 🎯 SELECT Strategies**: Clinical memory generation and selective retrieval for healthcare AI cognition.

Clinical memory operations implementing context writing and selective memory access:

#### `create_memory`
**🖊️ WRITE**: Generate clinical memories with structured context metadata

```python
# WRITE: Generate clinical context with metadata
memory = use_tool("create_memory", {
    "content": "Patient reports 75% reduction in chest pain after metoprolol initiation. Excellent medication tolerance.",
    "memory_type": "episodic",
    "importance_score": 0.9,  # High clinical significance
    "tags": ["medication_response", "chest_pain", "improvement", "metoprolol"],
    "context_metadata": {
        "patient_id": "patient-123",
        "encounter_type": "follow_up",
        "medication_change": "metoprolol_start",
        "outcome_measure": "symptom_improvement",
        "context_strategies_used": ["write", "select"]  # Track context engineering
    }
})
```

#### `search_memories`
Semantic search across clinical memories

```python
memories = use_tool("search_memories", {
    "query": "medication side effects",
    "memory_type": "episodic", 
    "limit": 5,
    "similarity_threshold": 0.7
})
```

#### `consolidate_memories`
Merge related memories for knowledge synthesis

```python
consolidated = use_tool("consolidate_memories", {
    "memory_ids": ["memory-1", "memory-2", "memory-3"],
    "consolidation_strategy": "thematic_synthesis"
})
```

#### `retrieve_context`
Get relevant clinical context for current task

```python
context = use_tool("retrieve_context", {
    "query": "diabetes management plan",
    "context_type": "clinical",
    "max_memories": 3
})
```

#### `analyze_memory_patterns`
Identify patterns and insights from clinical memories

```python
patterns = use_tool("analyze_memory_patterns", {
    "memory_type": "episodic",
    "analysis_focus": "patient_outcomes",
    "time_window": "last_30_days"
})
```

#### `check_memory`
Collect a filtered set of memories (episodic/procedural) for agent context

```python
context_memories = use_tool("check_memory", {
    "actor_id": actor.id,
    "memory_types": ["episodic", "procedural"],
    "min_importance": 0.6,
    "limit": 20
})
```

### ⚕️ Resource-Specific Tools (examples)

#### Event
```python
from hacs_tools.domains.resource_tools import (
  create_event_tool, update_event_status_tool, add_event_performer_tool, schedule_event_tool, summarize_event_tool
)

# Create and schedule an event
evt = create_event_tool(subject="Patient/patient-123", code_text="physiotherapy_session", when="2025-02-01T10:00:00Z")
if evt.success:
  evt2 = schedule_event_tool(evt.data.get("event"), start="2025-02-01T10:00:00Z", end="2025-02-01T11:00:00Z")
  summary = summarize_event_tool((evt2.data or {}).get("event") or evt.data.get("event"))
```

#### Appointment
```python
from hacs_tools.domains.resource_tools import (
  schedule_appointment, reschedule_appointment, cancel_appointment, check_appointment_conflicts, send_appointment_reminders
)

appt = schedule_appointment("Patient/p1", "Practitioner/pr1", "2025-02-02T09:00:00Z", "2025-02-02T09:30:00Z")
conflicts = check_appointment_conflicts((appt.data or {}).get("appointment"), existing=[])
```

#### CarePlan / CareTeam / Goal
```python
from hacs_tools.domains.resource_tools import (
  create_care_plan, update_care_plan_progress, coordinate_care_activities, track_care_plan_goals,
  assemble_care_team, assign_team_roles, coordinate_team_communication, track_team_responsibilities,
  update_team_membership, track_goal_progress, update_goal_status, measure_goal_achievement, link_goal_to_careplan
)

cp = create_care_plan("Patient/p1", title="Diabetes care plan")
track_goal_progress({"description": "reduce A1C to <7%"}, current_value=7.5)
```

#### NutritionOrder
```python
from hacs_tools.domains.resource_tools import (
  create_therapeutic_diet_order, manage_nutrition_restrictions, calculate_nutritional_requirements, coordinate_feeding_protocols
)

diet = create_therapeutic_diet_order("Patient/p1", diet_text="low_sodium")
reqs = calculate_nutritional_requirements(80.0, 175.0, 45, "male")
```

### 🧬 Terminology (optional)

High-level terminology tools help agents understand and align clinical codes without mutating resources directly.

#### Visualize resources and annotations
```python
from hacs_utils.visualization import visualize_resource, visualize_annotations
from hacs_models import Patient, AnnotatedDocument, Extraction, CharInterval

# Resource card
p = Patient(full_name="Jane Doe", birth_date="1990-01-01", gender="female")
visualize_resource(p)

# Annotations highlighting
doc = AnnotatedDocument(text="BP 128/82, HR 72", extractions=[
    Extraction(extraction_class="blood_pressure", extraction_text="128/82", char_interval=CharInterval(start_pos=3, end_pos=9))
])
visualize_annotations(doc)
```

#### Summarize codable concepts in a document
```python
from hacs_tools.domains.terminology import summarize_codable_concepts

summary = summarize_codable_concepts(composition_doc, query="hypertension", top_k=3)
print(summary.data["summary"])  # human-readable summary for prompts
```

#### Annotate document codings (single artifact)
```python
from hacs_tools.domains.terminology import get_possible_codes

report = get_possible_codes(composition_doc, query="blood pressure", top_k=2)
# report.data = {resource_id, summary, candidates, umls}

### Markdown visualization helpers (static docs)

```python
from hacs_utils.visualization import resource_to_markdown, annotations_to_markdown
from hacs_models import Patient, AnnotatedDocument, Extraction, CharInterval

p = Patient(full_name="Jane Doe")
print(resource_to_markdown(p, include_json=False))

doc = AnnotatedDocument(text="BP 128/82, HR 72", extractions=[
  Extraction(extraction_class="blood_pressure", extraction_text="128/82", char_interval=CharInterval(start_pos=3, end_pos=9))
])
print(annotations_to_markdown(doc))
```
```

#### Map codes between systems (e.g., SNOMED → LOINC)
```python
from hacs_tools.domains.terminology import map_terminology

mappings = map_terminology(
    composition_doc,
    source="SNOMED",
    target="LOINC",
    top_k=3
)
```

### 📚 Evidence

Use dedicated search for literature evidence.

```python
evidence = use_tool("search_evidence", {
    "query": "ACE inhibitor contraindications",
    "top_k": 5
})
```

 

### ⚕️ Schema Discovery (5 tools)

Healthcare resource schema exploration and analysis.

#### `describe_models`
Describe HACS model definitions

```python
resources = use_tool("describe_models", {
    "resource_types": ["Patient", "Observation"],
    "include_examples": True
})
```

#### `list_model_fields`
List fields for a resource type

```python
schema = use_tool("list_model_fields", {
    "resource_type": "Patient"
})
```

#### `plan_bundle_schema`
Plan a bundle schema across resource types

```python
plan = use_tool("plan_bundle_schema", {
    "resource_types": ["Patient", "Document", "Encounter"]
})
```

#### `analyze_model_fields`
Analyze fields in healthcare model

```python
analysis = use_tool("analyze_model_fields", {
    "resource_name": "Observation", 
    "analysis_type": "comprehensive"
})
```

#### `suggest_model_fields`
Get field suggestions for models

```python
suggestions = use_tool("suggest_model_fields", {
    "resource_name": "Patient",
    "use_case": "diabetes_management"
})
```

 

 

 

 

## 

## Tool Discovery

- MCP (curated):
```python
import requests
resp = requests.post("http://localhost:8000/", json={"jsonrpc":"2.0","method":"tools/list","id":1})
print(resp.json()["result"]["tools"])  # curated list
```

- Python (full registry):
```python
from hacs_registry import get_global_tool_registry
reg = get_global_tool_registry()
all_tools = [t.name for t in reg.get_all_tools()]  # complete catalog
```

---

For more examples and integration patterns, see the [Quick Start](quick-start.md). Integration-specific docs have been consolidated into package READMEs.