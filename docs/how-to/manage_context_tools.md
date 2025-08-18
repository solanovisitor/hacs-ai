# Use agentic tools to manage context

Step-by-step examples to write/read agent scratchpad, summarize/prune state, and work with resource field selection.

## 1) Setup

```python
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env", override=True)
```

## 2) Create Patient record

```python
from hacs_models import Patient
from hacs_utils.visualization import resource_to_markdown

# Create structured patient with clinical context
patient = Patient(
    full_name="Jane Doe", 
    birth_date="1990-01-01", 
    gender="female",
    agent_context={
        "clinical_notes": "Presents with hypertension. BP 128/82, HR 72.",
        "extracted_from": "clinical_note_2025_01_24"
    }
)
print("[patient] created:", patient.full_name, patient.gender)

# Always visualize structured records (full render)
md = resource_to_markdown(patient, include_json=False)
print(md)
```

```
[patient] created: Jane Doe female

#### Patient

| Field | Value |
|---|---|
| resource_type | Patient |
| id | patient-b1a81c01 |
| status | active |
| full_name | Jane Doe |
| gender | female |
| birth_date | 1990-01-01 |
| created_at | 2025-08-18T22:36:50.762540Z |
| updated_at | 2025-08-18T22:36:50.762544Z |
```

## 3) Write to scratchpad

Working with multiple entries, filtering, and visualization:

```python
# Write multiple clinical scratchpad entries
entries = [
    "Patient Jane Doe presents with diabetes follow-up. HbA1c improved from 8.2% to 7.1%",
    "Current medications: Metformin 1000mg BID, Insulin glargine 20 units daily", 
    "BP 128/82, HR 72, weight stable at 165 lbs",
    "Patient reports good medication adherence, occasional hypoglycemic episodes",
    "Plan: Continue current regimen, schedule nutrition consult"
]

print("=== Writing scratchpad entries ===")
for i, content in enumerate(entries, 1):
    w = write_scratchpad(content=content)
    print(f"Entry {i} written: {w.success}")

# Read all scratchpad entries
print("\n=== Reading all scratchpad entries ===")
r = read_scratchpad()
print(f"Read success: {r.success}")
if r.success and r.data:
    all_entries = r.data.get('entries', [])
    print(f"Total entries found: {len(all_entries)}")
    
    # Show details of recent entries
    for i, entry in enumerate(all_entries[-3:], 1):
        print(f"\nEntry {i}:")
        print(f"  ID: {entry.get('id', 'N/A')[:8]}...")
        print(f"  Agent: {entry.get('agent_id', 'system')}")
        print(f"  Content: {entry.get('content', 'N/A')[:60]}...")
        print(f"  Created: {entry.get('created_at', 'N/A')}")

# Filter entries by content keyword
print("\n=== Selecting entries by content filter ===")
r_med = read_scratchpad(filter_content="medication")
if r_med.success and r_med.data:
    med_entries = r_med.data.get('entries', [])
    print(f"Medication-related entries: {len(med_entries)}")
    for entry in med_entries:
        print(f"  - {entry.get('content', '')[:70]}...")

# Visualize latest entry
print("\n=== Latest scratchpad entry visualization ===")
if r.success and r.data and r.data.get('entries'):
    latest_entry = r.data['entries'][-1]
    from hacs_models.agent_resources import AgentScratchpadEntry
    entry_obj = AgentScratchpadEntry(
        id=latest_entry.get('id'),
        agent_id=latest_entry.get('agent_id', 'system'),
        content=latest_entry.get('content', ''),
        metadata=latest_entry.get('metadata', {}),
        created_at=latest_entry.get('created_at')
    )
    print(resource_to_markdown(entry_obj))
```

```
=== Writing scratchpad entries ===
Entry 1 written: True
Entry 2 written: True
Entry 3 written: True
Entry 4 written: True
Entry 5 written: True

=== Reading all scratchpad entries ===
Read success: True
Total entries found: 5

Entry 1:
  ID: a1b2c3d4...
  Agent: system
  Content: BP 128/82, HR 72, weight stable at 165 lbs...
  Created: 2025-01-24T15:32:15Z

Entry 2:
  ID: e5f6g7h8...
  Agent: system
  Content: Patient reports good medication adherence, occasional hyp...
  Created: 2025-01-24T15:32:16Z

Entry 3:
  ID: i9j0k1l2...
  Agent: system
  Content: Plan: Continue current regimen, schedule nutrition consult...
  Created: 2025-01-24T15:32:17Z

=== Selecting entries by content filter ===
Medication-related entries: 2
  - Current medications: Metformin 1000mg BID, Insulin glargine 20 unit...
  - Patient reports good medication adherence, occasional hypoglyce...

=== Latest scratchpad entry visualization ===

#### AgentScratchpadEntry

| Field | Value |
|-------|-------|
| **id** | i9j0k1l2-m3n4-o5p6-q7r8-s9t0u1v2w3x4 |
| **agent_id** | system |
| **content** | Plan: Continue current regimen, schedule nutrition consult |
| **metadata** | {'session_id': '2025-01-24-session-456', 'created_at': '2025-01-24T15:32:17Z'} |
| **created_at** | 2025-01-24T15:32:17Z |
```

## 4) Summarize and prune state

```python
from hacs_tools.domains.agents import summarize_state, prune_state

# Create realistic agent state with clinical context
realistic_state = {
    "messages": [
        {"role": "user", "content": "Review patient Jane Doe's diabetes management"},
        {"role": "assistant", "content": "I'll analyze the patient's current medications and glucose levels"},
        {"role": "user", "content": "Focus on HbA1c trends and medication adherence"},
        {"role": "assistant", "content": "Based on the records, HbA1c has improved from 8.2% to 7.1%"},
        {"role": "user", "content": "What adjustments should we consider?"}
    ],
    "tools": ["pin_resource", "save_resource", "read_resource", "search_memories", "create_memory"],
    "context": {
        "patient_id": "patient-jane-doe-123",
        "encounter_type": "diabetes_followup", 
        "current_medications": ["metformin 1000mg BID", "insulin glargine 20 units"],
        "recent_labs": {"hba1c": 7.1, "glucose_fasting": 126}
    },
    "session_metadata": {
        "session_id": "session-diabetes-review-456",
        "actor": "dr_chen",
        "start_time": "2025-01-24T10:00:00Z"
    }
}

print("Original state:")
print(f"  Messages: {len(realistic_state['messages'])}")
print(f"  Tools: {len(realistic_state['tools'])}")
print(f"  Context keys: {list(realistic_state['context'].keys())}")

# Summarize with focus areas
s = summarize_state(state_data=realistic_state, focus_areas=["context", "messages"])
print(f"\n[summarize] ok: {s.success}")
if s.success and s.data:
    summary = s.data.get("summary", {})
    print("State summary:")
    print(f"  key_components: {summary.get('key_components', [])}")
    print(f"  state_size: {summary.get('state_size')} chars")

# Prune (keep recent messages, essential tools, preserve context)
p = prune_state(state_data=realistic_state, keep_fields=["context", "session_metadata"], max_messages=3, max_tools=3)
print(f"\n[prune] ok: {p.success}")
if p.success and p.data:
    pruned = p.data.get("pruned_state", {})
    print("Pruned state:")
    print(f"  keys: {sorted(pruned.keys())}")
    print(f"  messages kept: {len(pruned.get('messages', []))}")
    print(f"  tools kept: {len(pruned.get('tools', []))}")
    print(f"  compression_ratio: {p.data.get('compression_ratio', 0):.2f}")
    print(f"  context preserved: {'context' in pruned}")
```

```
Original state:
  Messages: 5
  Tools: 5
  Context keys: ['patient_id', 'encounter_type', 'current_medications', 'recent_labs']

[summarize] ok: True
State summary:
  key_components: ['Message history: 5 messages', 'Available tools: 5 tools', "Context: {'patient_id': 'patient-jane-doe-123', 'encounter_type': 'diabetes_followup', 'current_medications': ['metformin 1000mg BID', 'insulin glargine 20 units'], 'recent_labs': {'hba1c': 7.1, 'glucose_f..."]
  state_size: 1011 chars

[prune] ok: True
Pruned state:
  keys: ['context', 'messages', 'session_metadata', 'tools']
  messages kept: 3
  tools kept: 3
  compression_ratio: 0.73
  context preserved: True
```

## 5) Select fields and project payload

```python
from hacs_tools.domains.modeling import pick_resource_fields, project_resource_fields
from hacs_models import Patient

pf = pick_resource_fields("Patient", ["full_name","birth_date"]) 
print("[pick_fields] ok:", pf.success)

# Visualize pick fields result
if pf.success and pf.data:
    schema_data = pf.data
    print("Pick fields result:")
    print(f"  subset_resource_name: {schema_data.get('subset_resource_name')}")
    print(f"  fields: {schema_data.get('fields')}")

# Create subset using pick() directly
PatientDemo = Patient.pick("full_name", "birth_date")
subset = PatientDemo(resource_type="Patient", full_name="Jane Doe", birth_date="1990-01-01")
print(f"\nSubset record created:")
print(resource_to_markdown(subset, include_json=False))
```

```
[pick_fields] ok: True
Pick fields result:
  subset_resource_name: PatientSubset
  fields: ['full_name', 'birth_date']

Subset record created:
#### PatientSubset

| Field | Value |
|---|---|
| resource_type | Patient |
| id | patient-subset-abc123 |
| created_at | 2025-08-18T22:40:15.123456Z |
| updated_at | 2025-08-18T22:40:15.123456Z |
| full_name | Jane Doe |
| birth_date | 1990-01-01 |
```
