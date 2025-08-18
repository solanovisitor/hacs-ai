# HACS Quick Start Guide

**Build a Healthcare Document Processing Pipeline in 5 Minutes**

Extract structured healthcare data from clinical text and persist to database with proper actor security.

## Prerequisites

- **Python 3.11+**
- **Docker** (for database)

---

## Step 1: Installation and minimal usage

Install with uv and run a minimal in‑process example using HACS models. HACS models are healthcare‑native, FHIR‑aligned typed data structures that form the canonical layer for agents, tools, and persistence. This first step introduces the core types and how resources are constructed and reasoned over in‑process.

```bash
# Install uv and create Python 3.11 environment
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv -p 3.11
source .venv/bin/activate

# Install core HACS packages
uv pip install -U hacs-core hacs-models hacs-auth
```

```python
from hacs_auth import Actor, ActorRole
from hacs_models import Patient, Observation, CodeableConcept, Quantity
from hacs_models.types import ObservationStatus

# Provider (in‑process only)
doctor = Actor(name="Dr. Sarah Chen", role=ActorRole.PHYSICIAN, organization="General Hospital")

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
print("\nObservation record:")
print(resource_to_markdown(bp, include_json=False))
```

```
✅ Minimal example ready:
  Actor: Dr. Sarah Chen physician
  Patient: Maria Rodriguez patient-3bd910dd
  BP: 128.0 mmHg

Patient record:
#### Patient

| Field | Value |
|---|---|
| resource_type | Patient |
| id | patient-3bd910dd |
| status | active |
| full_name | Maria Rodriguez |
| gender | female |
| birth_date | 1985-03-15 |
| created_at | 2025-08-18T22:38:39.046248Z |
| updated_at | 2025-08-18T22:38:39.046248Z |

Observation record:
#### Observation

| Field | Value |
|---|---|
| resource_type | Observation |
| id | observation-93675660 |
| status | final |
| code | Blood Pressure |
| value.quantity | 128.0 mmHg |
| subject | Patient/patient-3bd910dd |
| performer | [] |
| created_at | 2025-08-18T22:38:39.046393Z |
| updated_at | 2025-08-18T22:38:39.046393Z |
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
from hacs_utils.structured import extract
from langchain_openai import ChatOpenAI

PatientInfo = Patient.pick("full_name", "birth_date", "gender")
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
note = "Maria Rodriguez (1985-03-15), female."
subset = extract(llm, prompt=f"Extract demographics.\n\n{note}", output_model=PatientInfo)
print("extracted:", subset.model_dump())
```

See `docs/tutorials/medication_extraction.md` and API reference (structured extraction).

### Database persistence

```python
""" Prereq: uv pip install -U hacs-persistence; set DATABASE_URL """

import os, asyncio, logging
from hacs_persistence import HACSConnectionFactory
from hacs_auth import Actor, ActorRole
from hacs_models import Patient, Observation, CodeableConcept, Quantity
from hacs_models.types import ObservationStatus

logging.basicConfig(level=logging.INFO, format="%(name)s:%(levelname)s:%(message)s")

os.environ["DATABASE_URL"] = os.getenv("DATABASE_URL", "postgresql://hacs:hacs_dev@localhost:5432/hacs")

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
INFO:hacs_persistence.adapter:Resource Patient/patient-d900519e saved successfully
INFO:hacs_persistence.adapter:Resource Observation/observation-87dae782 saved successfully
INFO:hacs_persistence.adapter:Resource Observation/observation-8280d00e saved successfully
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

## Next Steps

### Production Workflows
- **[Complete Context Engineering](tutorials/complete_context_engineering.md)** - All 4 context strategies
- **[Medication Extraction](tutorials/medication_extraction.md)** - Extract medications from clinical notes

### Documentation  
- **[API Reference](api-reference.md)** - Complete API documentation
- **[HACS Tools](hacs-tools.md)** - 20+ healthcare tools reference
- **[Testing Guide](testing.md)** - Testing and validation

### Database setup & migrations
- `packages/hacs-persistence/README.md` — connection strings, schema overview, async migrations (`run_migration()`), guidance for `auto_migrate=True` in quick starts vs. explicit migrations in production
- `docs/index.md` — HACS architecture (models, tools, persistence, integrations) and context‑engineering vision (Write, Select, Compress, Isolate)
