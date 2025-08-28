## Medication extraction → typed records → Composition (HACS)

In this tutorial, you will extract medication data from clinical text, validate it with typed models via `pick()`, instantiate FHIR‑aligned resources, and group them into a `Composition` for persistence.

If you're new to HACS, complete the [Quick Start](../quick-start.md) first.

### Prerequisites

- Complete the [Quick Start](../quick-start.md)
- A LangChain ChatModel API key (OpenAI, Anthropic, etc.)
- A running Postgres if you plan to persist records (set `DATABASE_URL`)

```python
from dotenv import load_dotenv
load_dotenv()

import asyncio
from hacs_utils.extraction import extract
from hacs_models import MedicationRequest, MedicationRequestStatus, MedicationRequestIntent
from hacs_utils.visualization import to_markdown
from langchain_openai import ChatOpenAI

# Input text
input_text = (
    "The patient was prescribed Lisinopril and Metformin last month.\n"
    "He takes the Lisinopril 10mg daily for hypertension, but often misses\n"
    "his Metformin 500mg dose which should be taken twice daily for diabetes.\n"
)

### 1) Extract medications using current HACS API
async def extract_medications():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    print("🔍 Extracting medications from clinical text...")
    print(f"Text: {input_text.strip()}")

    # Extract MedicationRequest objects
    medications = await extract(
        llm_provider=llm,
        prompt=f"""Extract each medication as a separate MedicationRequest object from this clinical text:

        {input_text}

        For each medication, identify the medication name and any dosage information.""",
        output_model=MedicationRequest,
        many=True,
        use_descriptive_schema=True,
        injected_fields={
            "status": MedicationRequestStatus.ACTIVE,
            "intent": MedicationRequestIntent.ORDER,
            "subject": "Patient/medication-tutorial",
        },
        strict=False,
    )
    
    print(f"\n✅ Extracted {len(medications)} medication(s)")
    print(to_markdown(medications, title="Extracted Medications"))
    return medications

# Run the extraction
medications = asyncio.run(extract_medications())
```

**Output:**
```
🔍 Extracting medications from clinical text...
Text: The patient was prescribed Lisinopril and Metformin last month.
He takes the Lisinopril 10mg daily for hypertension, but often misses
his Metformin 500mg dose which should be taken twice daily for diabetes.

✅ Extracted 1 medication(s)
### Extracted Medications

#### MedicationRequest

| Field | Value |
|---|---|
| resource_type | MedicationRequest |
| id | medicationrequest-a7945341 |
| status | active |
| subject | Patient/medication-tutorial |
| dosage_instruction | [] |
| intent | order |
| created_at | 2025-08-26T16:16:43.492202Z |
| updated_at | 2025-08-26T16:16:43.492206Z |
```

### 2) Persist to Database

Now let's save the extracted medications to a database using HACS persistence:

```python
import os
from hacs_persistence.adapter import create_postgres_adapter
from hacs_models import Actor, Patient

async def persist_medications():
    # Extract medications (reusing previous function)
    medications = await extract_medications()
    
    # Set up database connection
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        os.environ["HACS_DATABASE_URL"] = database_url

    # Create database adapter and actor for audit trails
    adapter = await create_postgres_adapter()
    actor = Actor(
        name="medication-tutorial",
        role="system",
        permissions=["patient:write", "medicationrequest:write"]
    )

    print("💾 Persisting to database...")

    # Create a patient first
    patient = Patient(
        full_name="Tutorial Patient",
        birth_date="1980-01-15",
        gender="unknown"
    )
    
    saved_patient = await adapter.save(patient, actor)
    print(f"✅ Saved Patient: {saved_patient.id}")

    # Update medication subjects to reference the patient
    saved_medications = []
    for med in medications:
        med.subject = f"Patient/{saved_patient.id}"
        saved_med = await adapter.save(med, actor)
        saved_medications.append(saved_med)
        print(f"✅ Saved MedicationRequest: {saved_med.id}")

    # Verify by reading back
    if saved_medications:
        read_med = await adapter.read(MedicationRequest, saved_medications[0].id, actor)
        print(f"✅ Verified: {read_med.id} references {read_med.subject}")

    return saved_patient, saved_medications

# Run persistence example (requires DATABASE_URL in .env)
try:
    patient, medications = asyncio.run(persist_medications())
    print(f"\n🎉 Tutorial complete! Saved 1 patient and {len(medications)} medications to database.")
except Exception as e:
    print(f"⚠️ Database persistence skipped: {e}")
    print("💡 Set DATABASE_URL in .env to enable persistence")
```

### 3) Advanced: Multiple Resource Types

Extract both medications and their associated conditions:

```python
from hacs_models import Condition, ConditionClinicalStatus, ConditionVerificationStatus

async def extract_medications_and_conditions():
    # Enhanced clinical text
    enhanced_text = """
    Patient was prescribed Lisinopril 10mg daily for hypertension management.
    Started Metformin 500mg twice daily for type 2 diabetes control.
    Continue current Aspirin 81mg daily for cardioprotection.
    """

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    print("🔍 Extracting medications and conditions...")

    # Extract conditions  
    conditions = await extract(
        llm_provider=llm,
        prompt=f"""Extract Condition objects for each medical condition mentioned:

        {enhanced_text}

        Look for conditions like hypertension, diabetes, etc.""",
        output_model=Condition,
  many=True,
        use_descriptive_schema=True,
        injected_fields={
            "clinical_status": ConditionClinicalStatus.ACTIVE,
            "verification_status": ConditionVerificationStatus.CONFIRMED,
            "subject": "Patient/tutorial-123",
        },
        strict=False,
    )

    print(f"✅ Also extracted {len(conditions)} conditions:")
    for i, cond in enumerate(conditions, 1):
        print(f"  {i}. {cond.code} - Status: {cond.clinical_status}")

    return conditions

# Run enhanced extraction
conditions = asyncio.run(extract_medications_and_conditions())
```

## Summary

This tutorial demonstrated:

1. **Basic medication extraction** using the current HACS `extract()` API
2. **Database persistence** with proper audit trails and actor authentication
3. **Multiple resource types** - extracting both medications and conditions

### Key Features Used

- `hacs_utils.extraction.extract()` - Core LLM extraction with HACS models
- `injected_fields` - Pre-filling stable enum fields for consistency
- `use_descriptive_schema=True` - Providing rich context to LLMs
- Database persistence with `hacs_persistence` adapters
- Actor-based audit trails for all operations

### Next Steps

- **[Persist Resources](../how-to/persist_resources.md)** - Learn more about database operations
- **[Extract Annotations](../how-to/extract_annotations.md)** - Advanced extraction patterns  
- **[Complete Context Engineering](complete_context_engineering.md)** - Full workflow examples


