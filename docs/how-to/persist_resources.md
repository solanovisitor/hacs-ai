## Persist HACS models to PostgreSQL

This guide saves real HACS resources (extracted via LLM) to a PostgreSQL database using the async adapter. No mocks.

Prerequisites:
- `uv pip install -U hacs-persistence hacs-auth hacs-models "hacs-utils[langchain]"`
- `DATABASE_URL` in your `.env` (or `HACS_DATABASE_URL`)

### 1) Extract resources (MedicationRequest and Condition)

```python
from dotenv import load_dotenv
load_dotenv()

import asyncio
from langchain_openai import ChatOpenAI
from hacs_utils.structured import extract
from hacs_models import (
    MedicationRequest, Condition,
    MedicationRequestStatus, MedicationRequestIntent,
)
from hacs_models.types import (
    ConditionClinicalStatus, ConditionVerificationStatus,
)

clinical_text = (
    "Patient was prescribed Lisinopril 10mg daily for hypertension management.\n"
    "Started Metformin 500mg twice daily for type 2 diabetes control.\n"
    "Continue current Aspirin 81mg daily for cardioprotection."
)

llm = ChatOpenAI(model="gpt-5-mini-2025-08-07")

med_prompt = f"""
Extract MedicationRequest objects for each medication order in the text.
- Set medication_codeable_concept.text and dosage_instruction[0].text
- Do not invent fields you cannot infer.
Text:
{clinical_text}
""".strip()

cond_prompt = f"""
Extract Condition objects for each condition mentioned.
- Set code.text (e.g., "hypertension")
- Set clinical_status and verification_status
Text:
{clinical_text}
""".strip()

meds = asyncio.run(extract(
    llm_provider=llm,
    prompt=med_prompt,
    output_model=MedicationRequest,
    many=True,
    use_descriptive_schema=True,
    injected_fields={
        "status": MedicationRequestStatus.ACTIVE,
        "intent": MedicationRequestIntent.ORDER,
        "subject": "Patient/123",
    },
    strict=False,
))

conds = asyncio.run(extract(
    llm_provider=llm,
    prompt=cond_prompt,
    output_model=Condition,
    many=True,
    use_descriptive_schema=True,
    injected_fields={
        "clinical_status": ConditionClinicalStatus.ACTIVE,
        "verification_status": ConditionVerificationStatus.CONFIRMED,
        "subject": "Patient/123",
    },
    strict=False,
))

print(f"Extracted: {len(meds)} MedicationRequest, {len(conds)} Condition")
```

Output:
```
Extracted: 1 MedicationRequest, 2 Condition
```

### 2) Connect and persist

```python
import os, asyncio
from dotenv import load_dotenv, dotenv_values
from hacs_persistence.adapter import create_postgres_adapter
from hacs_models import Actor

# Map DATABASE_URL -> HACS_DATABASE_URL for adapter using dotenv
load_dotenv()
kv = dotenv_values()
os.environ.setdefault("HACS_DATABASE_URL", kv.get("DATABASE_URL", ""))

async def persist_all():
    adapter = await create_postgres_adapter()
    author = Actor(name="db-writer", role="system", permissions=[
        "medicationrequest:write", "condition:write"
    ])  # type: ignore[arg-type]

    saved_ids = []
    for mr in meds:
        saved = await adapter.save(mr, author)
        saved_ids.append(saved.id)
        print("Saved MedicationRequest:", saved.id)

    for c in conds:
        saved = await adapter.save(c, author)
        saved_ids.append(saved.id)
        print("Saved Condition:", saved.id)

    # Read one back
    read_med = await adapter.read(MedicationRequest, meds[0].id, author)
    print("Read back MedicationRequest:", read_med.id)
    return saved_ids

ids = asyncio.run(persist_all())
print("✓ Persisted IDs:", ids)
```

Example output:
```
Saved MedicationRequest: medicationrequest-093872e8
Saved Condition: condition-1
Saved Condition: condition-2
Read back MedicationRequest: medicationrequest-093872e8
✓ Persisted IDs: ['medicationrequest-093872e8', 'condition-1', 'condition-2']
```

### 3) Search and verify

```python
from datetime import datetime

async def verify_one():
    adapter = await create_postgres_adapter()
    author = Actor(name="db-reader", role="system", permissions=["medicationrequest:read"])  # type: ignore[arg-type]
    got = await adapter.read(MedicationRequest, meds[0].id, author)
    print("Verified:", got.id, got.intent, got.status, datetime.now().isoformat())

asyncio.run(verify_one())
```

Example output:
```
Verified: medicationrequest-093872e8 MedicationRequestIntent.ORDER MedicationRequestStatus.ACTIVE 2025-08-20T02:29:10.000000
```

## Notes
- Use the adapter directly for audited writes/reads with a valid `Actor`.
- Ensure `.env` provides a reachable PostgreSQL `DATABASE_URL` (pgvector enabled).
- For initial setup and migrations, see [Connect to a database](connect_postgres.md).
