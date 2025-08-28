# HACS Quick Start Guide

**Build a Healthcare Document Processing Pipeline in 5 Minutes**

Extract structured healthcare data from clinical text and persist to database with proper actor security.

## Prerequisites

- **Python 3.11+**
- **Docker** (for database)

---

## Step 1: Minimal in‑process example

Install HACS first (see home page “Install HACS (beta)”). Then run this minimal in‑process example using HACS models. HACS models are healthcare‑native, FHIR‑aligned typed data structures that form the canonical layer for agents, tools, and persistence. This first step introduces the core types and how resources are constructed and reasoned over in‑process.

```python
from hacs_models import Patient, Observation, CodeableConcept, Quantity, Actor
from hacs_models.types import ObservationStatus

# Provider (in‑process only)
doctor = Actor(name="Dr. Sarah Chen", role="physician")

# Typed resources (no DB, no LLM)
patient = Patient(full_name="Maria Rodriguez", birth_date="1985-03-15", gender="female")
bp = Observation(status=ObservationStatus.FINAL, code=CodeableConcept(text="Blood Pressure"), value_quantity=Quantity(value=128.0, unit="mmHg"), subject=f"Patient/{patient.id}")

print("✅ Minimal example ready:")
print("  Actor:", doctor.name, doctor.role)
print("  Patient:", patient.full_name, patient.id)
print("  BP:", bp.value_quantity.value, bp.value_quantity.unit)

# Always visualize structured records
from hacs_utils.visualization import resource_to_markdown
print("\nPatient record:")
print(resource_to_markdown(patient, include_json=False))
```

**Output:**
```
✅ Minimal example ready:
  Actor: Dr. Sarah Chen physician
  Patient: Maria Rodriguez patient-e187c277
  BP: 128.0 mmHg

Patient record:
#### Patient

| Field | Value |
|---|---|
| resource_type | Patient |
| id | patient-e187c277 |
| status | active |
| full_name | Maria Rodriguez |
| gender | female |
| birth_date | 1985-03-15 |
| created_at | 2025-08-26T15:09:06.443077Z |
| updated_at | 2025-08-26T15:09:06.443078Z |
```

_This validates your local environment and demonstrates HACS typed models in‑process._

---

## Step 2: Add capabilities

Add structured extraction and PostgreSQL persistence to the minimal setup.

The following snippets illustrate common extensions to the minimal setup.

### LLM extraction

```python
# Prereq: uv pip install -U hacs-utils[langchain]; set OPENAI_API_KEY

from hacs_models import Patient
from hacs_utils.visualization import to_markdown

# Simulated extraction result (LLM extraction may require additional prompt tuning)
PatientInfo = Patient.pick("full_name", "birth_date", "gender")
extracted_patient = PatientInfo(
    resource_type="Patient",
    full_name="Maria Rodriguez", 
    birth_date="1985-03-15", 
    gender="female"
)

print("Extracted demographics:")
print(to_markdown(extracted_patient, include_json=False))
```

**Output:**
```
Extracted demographics:
#### Patient

| Field | Value |
|---|---|
| resource_type | Patient |
| full_name | Maria Rodriguez |
| gender | female |
| birth_date | 1985-03-15 |
| created_at | 2025-08-26T16:24:08.222005Z |
| updated_at | 2025-08-26T16:24:08.222004Z |
```

See `docs/tutorials/medication_extraction.md` and API reference (structured extraction).

### Production extraction (ExtractionRunner)

```python
# Prereq: uv pip install -U hacs-utils[langchain]; set OPENAI_API_KEY
import asyncio
from langchain_openai import ChatOpenAI
from hacs_utils.extraction import ExtractionRunner, ExtractionConfig

async def run_extraction():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=60)
    config = ExtractionConfig(concurrency_limit=3, window_timeout_sec=45, total_timeout_sec=600, max_extractable_fields=4)
    runner = ExtractionRunner(config)

    text = open("examples/data/pt_transcricao_exemplo.txt", "r", encoding="utf-8").read()
    results = await runner.extract_document(llm, source_text=text)
    print({rtype: len(items) for rtype, items in results.items()})
    return results

results = asyncio.run(run_extraction())
```

**Output:**
```
{'Patient': 0, 'Condition': 1, 'FamilyMemberHistory': 0, 'Observation': 0, 'MedicationStatement': 0, 'ServiceRequest': 0, 'Immunization': 0, 'Practitioner': 0, 'Organization': 0, 'Procedure': 0, 'DiagnosticReport': 0}
```

### One‑step typed multi‑resource extraction (no Stage‑1 gating)

```python
import asyncio
from langchain_openai import ChatOpenAI
from hacs_utils.extraction import extract_citations_multi
from hacs_models import Observation, Patient, MedicationStatement, ServiceRequest, DiagnosticReport, Condition, Immunization, Procedure

async def run_multi_extraction():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=60)
    text = open("examples/data/pt_transcricao_exemplo.txt", "r", encoding="utf-8").read()
    models = [Observation, Patient, MedicationStatement, ServiceRequest, DiagnosticReport, Condition, Immunization, Procedure]
    results = await extract_citations_multi(llm, source_text=text, resource_models=models, max_items_per_type=20)
    print({rtype: len(items) for rtype, items in results.items()})
    return results

results = asyncio.run(run_multi_extraction())
```

**Output:**
```
{'Observation': 5, 'Patient': 0, 'MedicationStatement': 0, 'ServiceRequest': 0, 'DiagnosticReport': 2, 'Condition': 2, 'Immunization': 0, 'Procedure': 1}
```

### Facade-based extraction (focused subsets)

```python
# Prereq: uv pip install -U hacs-utils[langchain]; set OPENAI_API_KEY
import asyncio
from langchain_openai import ChatOpenAI
from hacs_utils.extraction.api import extract_facade
from hacs_models import Patient, Condition

async def run_facade_extraction():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # Extract only patient demographics
    patient = await extract_facade(
        llm_provider=llm,
        model_cls=Patient,
        facade_key="info",
        source_text="João Silva, masculino, 45 anos, hipertenso"
    )
    
    # Extract only condition summary  
    condition = await extract_facade(
        llm_provider=llm,
        model_cls=Condition,
        facade_key="summary", 
        source_text="João Silva, masculino, 45 anos, hipertenso"
    )
    
    return patient, condition

patient, condition = asyncio.run(run_facade_extraction())
print(f"Patient: {patient.full_name}, {patient.gender}, {patient.age}")
print(f"Condition: {condition.code}")
```

**Output:**
```
Patient: João Silva, male, 45
Condition: {'text': 'hipertenso'}
```

Available facades (actual):
- Patient: `info`, `address`, `telecom`, `identifiers`, `contacts`
- Condition: `summary`, `timing`, `body_site`, `evidence`
- Observation: `core`, `components`, `method_body_site`
- MedicationRequest: `medication`, `dosage`, `intent`, `authorship`
- Procedure: `core`, `body_site`, `outcome`
- Encounter: `basic`, `timing`, `participants`, `clinical`, `complete`
- Organization: `info`, `contact`, `hierarchy`, `identity`

See [Facade Guide](how-to/facade_extraction.md).

### CLI (hacs‑tools)

```bash
# Prereq: uv pip install -e packages/hacs-tools
hacs-tools extract --model gpt-4o-mini --transcript examples/data/pt_transcricao_exemplo.txt --out-dir ./outputs
hacs-tools registry --list-extractables
```

Example output:

```
Extracting from transcript (1834 chars) using gpt-4o-mini

✓ Extraction completed successfully!
  Total records: 8
  Resource types: ['Observation', 'Condition', 'Procedure']
  Output: outputs/extraction_results.json
  Duration: 12.83s
  Citations found: 10
```

### Database persistence

```python
""" Prereq: uv pip install -U hacs-persistence; set DATABASE_URL """

import os, asyncio, logging
from hacs_persistence import HACSConnectionFactory
from hacs_auth import Actor, ActorRole
from hacs_models import Patient, Observation, CodeableConcept, Quantity
from hacs_models.types import ObservationStatus

logging.basicConfig(level=logging.INFO, format="%(name)s:%(levelname)s:%(message)s")

from dotenv import load_dotenv, dotenv_values
load_dotenv()
kv = dotenv_values()
os.environ["DATABASE_URL"] = kv.get("DATABASE_URL", "postgresql://hacs:hacs_dev@localhost:5432/hacs")

adapter = HACSConnectionFactory.get_adapter(auto_migrate=False)
doctor = Actor(name="Dr. Sarah Chen", role=ActorRole.PHYSICIAN, organization="General Hospital")
patient = Patient(full_name="Maria Rodriguez", birth_date="1985-03-15", gender="female")
bp_obs = Observation(status=ObservationStatus.FINAL, code=CodeableConcept(text="Blood Pressure"), value_quantity=Quantity(value=128.0, unit="mmHg"), subject=f"Patient/{patient.id}")
hr_obs = Observation(status=ObservationStatus.FINAL, code=CodeableConcept(text="Heart Rate"), value_quantity=Quantity(value=72.0, unit="bpm"), subject=f"Patient/{patient.id}")

async def run():
    sp = await adapter.save(patient, doctor)
    bp_obs.subject = f"Patient/{sp.id}"
    hr_obs.subject = f"Patient/{sp.id}"
    await adapter.save(bp_obs, doctor)
    await adapter.save(hr_obs, doctor)
    print("✅ Persisted Patient and Observations")

asyncio.run(run())
```

```
INFO:hacs_persistence.adapter:PostgreSQLAdapter (Async) configured for schema 'public'
INFO:hacs_persistence.connection_factory:Created database adapter for schema 'public'
INFO:hacs_persistence.adapter:HACS resources table checked/created successfully
INFO:hacs_persistence.adapter:Async connection pool established and tables initialized.
INFO:hacs_persistence.adapter:Resource Patient/patient-aae1b354 saved successfully
INFO:hacs_persistence.adapter:Resource Observation/observation-f3a4d92e saved successfully
INFO:hacs_persistence.adapter:Resource Observation/observation-1d79fbd7 saved successfully
✅ Persisted Patient and Observations
```

### Visualization

Render compact HTML cards for resources and highlight extractions in notebooks.

```python
# Prereq: uv pip install -U hacs-utils
from hacs_utils.visualization import visualize_resource, visualize_annotations
from hacs_models import AnnotatedDocument, Extraction, CharInterval

visualize_resource(patient)

doc = AnnotatedDocument(
    text="BP 128/82, HR 72",
    extractions=[
        Extraction(
            extraction_class="blood_pressure",
            extraction_text="128/82",
            char_interval=CharInterval(start_pos=3, end_pos=9),
        )
    ],
)
visualize_annotations(doc)

# For static docs (Markdown), use:
#   from hacs_utils.visualization import resource_to_markdown, annotations_to_markdown
# See rendered example below.
```

<!-- removed noisy HTML-type/length logs -->

Rendered (Markdown):

### Patient

| Field | Value |
|---|---|
| resource_type | Patient |
| id | patient-5a82a2cb |
| status | active |
| created_at | 2025-08-17T23:33:58.656558Z |
| updated_at | 2025-08-17T23:33:58.656563Z |

Annotations preview:

| Class | Span | Snippet |
|---|---|---|
| Blood Pressure | [3-9] | … BP  **128/82** , HR 72 … |

---

## Step 3: Integrate

Bind HACS tools to an agent.

You can now bind HACS tools to an agent. Refer to the API reference and tools guide for details.

```python
from langgraph.prebuilt import create_react_agent
from hacs_utils.integrations.langchain.tools import langchain_tools

tools = langchain_tools()
agent = create_react_agent(model="anthropic:claude-3-7-sonnet-latest", tools=tools, prompt="You are a healthcare assistant using HACS tools.")
```

---

## 🎯 What You Built

✅ **Healthcare Document Processor** - Extract structured data from clinical text  
✅ **FHIR-Compliant Database** - PostgreSQL with healthcare schemas  
✅ **Actor-Based Security** - Role-based permissions for providers  
✅ **AI-Ready Pipeline** - Integrated with LangGraph and 20+ healthcare tools  

## 📊 Real Tool Execution Examples

Here are actual outputs from validated HACS tools running with `gpt-4o-mini`:

### Modeling Tools
```python
# pin_resource: Create validated Patient resource
result = pin_resource("Patient", {
    "full_name": "Jane Doe", "birth_date": "1990-01-01", 
    "gender": "female", "active": True
})
# ✅ Success: "Successfully instantiated Patient"
# 🆔 ID: "patient-e240e20d"
```

### Agent Tools  
```python
# write_scratchpad: Record clinical observations
result = write_scratchpad(
    content="Patient reports 7/10 chest pain, onset 2 hours ago...",
    entry_type="observation", session_id="visit_20240115"
)
# ✅ Success: "Successfully wrote to scratchpad"
# 🆔 Entry ID: "scratchpadentry-b99d1846"

# create_todo: Create urgent clinical tasks
result = create_todo(
    content="Order cardiac enzymes and chest X-ray for patient with chest pain",
    priority="high", clinical_urgency="urgent"
)
# ✅ Success: "Successfully created todo item"  
# 🆔 Todo ID: "agenttodo-4552c76f"
```

### Facade Extraction
```python
# extract_facade: Extract Patient demographics
patient = await extract_facade(llm, Patient, "info", 
    "João Silva, masculino, 45 anos, hipertenso")
# ✅ Name: "João Silva", Gender: "male", Age: 45

# extract_facade: Extract Condition details
condition = await extract_facade(llm, Condition, "summary",
    "Paciente apresenta quadro de hipertensão arterial não controlada")
# ✅ Code: "hipertensão arterial não controlada"
# ✅ Status: "active", Verification: "confirmed"
```

## Next Steps

### Production Workflows
- **[Complete Context Engineering](tutorials/complete_context_engineering.md)** - All 4 context strategies
- **[Medication Extraction](tutorials/medication_extraction.md)** - Extract medications from clinical notes
- **[Facade-Based Extraction](how-to/facade_extraction.md)** - Focused extraction with predefined field subsets

### Documentation  
- **[API Reference](api-reference.md)** - Complete API documentation
- **[HACS Tools](hacs-tools.md)** - 20+ healthcare tools reference
- **[Testing Guide](testing.md)** - Testing and validation

### Database setup & migrations
- `packages/hacs-persistence/README.md` — connection strings, schema overview, async migrations (`run_migration()`), guidance for `auto_migrate=True` in quick starts vs. explicit migrations in production
- `docs/index.md` — HACS architecture (models, tools, persistence, integrations) and context‑engineering vision (Write, Select, Compress, Isolate)
