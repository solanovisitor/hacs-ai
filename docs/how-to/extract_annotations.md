## Create HACS records from unstructured data

This guide shows how to extract clinical data as typed HACS Resources.

### About AnnotatedDocument, Composition, and Document

- `AnnotatedDocument` is a working container for raw clinical text plus intermediate artifacts (extractions, spans). It’s ideal for grounded extraction and analysis.
- `Composition`/`Document` represent the finalized clinical note. Use them to assemble the human-readable record from validated structured resources and/or grounded spans. The `Composition` holds metadata (title, type, subject, status, confidentiality) and hierarchical sections; `Document` overlays convenience utilities on top of `Composition`.
- Typical flow: start with `AnnotatedDocument` → extract typed models with `extract()` (and citations when needed) → write the final note as a `Document` with sections summarizing or referencing those models.

Prerequisites:

- `uv pip install -U hacs-utils[langchain]`
- An LLM provider (OpenAI, Anthropic, or a client exposing `ainvoke`/`invoke`)

## Extract typed HACS models from AnnotatedDocument

Let's start with the recommended approach: extracting medication information as validated HACS models from clinical text in an AnnotatedDocument.

### Step 1: Import and setup

```python
from dotenv import load_dotenv
load_dotenv()  # Load API keys from .env file

import asyncio
from hacs_models import MedicationRequest, AnnotatedDocument, Observation, Condition
from hacs_models.annotation import FormatType
from hacs_utils.extraction import extract
from hacs_utils.visualization import visualize_annotations, annotations_to_markdown
from langchain_openai import ChatOpenAI
```

### Step 2: Create an AnnotatedDocument

```python
# Start with clinical text in an AnnotatedDocument
clinical_text = """
Patient was prescribed Lisinopril 10mg daily for hypertension management.
Started Metformin 500mg twice daily for type 2 diabetes control.
Continue current Aspirin 81mg daily for cardioprotection.
""".strip()

# Create the annotated document (this could come from a previous annotation step)
annotated_doc = AnnotatedDocument(
    text=clinical_text,
    document_id="clinical_note_001"
)

print(f"✓ Created AnnotatedDocument:")
print(f"  ID: {annotated_doc.document_id}")
print(f"  Text length: {len(annotated_doc.text)} characters")
print(f"  Content preview: \"{annotated_doc.text[:50]}...\"")
```

Output:
```
✓ Created AnnotatedDocument:
  ID: clinical_note_001
  Text length: 196 characters
  Content preview: "Patient was prescribed Lisinopril 10mg daily for h..."
```

### Step 3: Define HACS model schemas and introspect fields

```python
from hacs_utils.visualization import to_markdown

# Use to_markdown to show HACS model specifications with field descriptions
print(to_markdown(MedicationRequest))
```

Output:
```
#### MedicationRequest Specifications

**Scope & Usage**

Order or authorization for supply and administration of medication to a patient. Represents prescriptions, medication orders, and medication authorizations with detailed dosing instructions, quantity, refills, and substitution rules. Supports complex dosing regimens, conditional orders, and medication reconciliation workflows. Includes prescriber information, pharmacy instructions, and administration context.

**Boundaries**

Do not use for actual medication taking/administration (use MedicationStatement/MedicationAdministration), medication definitions (use Medication), or medication dispensing (use MedicationDispense). Focus on the intent/order, not the fulfillment. Do not use for medication history or adherence tracking.

**Relationships**

- References: Patient via subject, Practitioner via requester, Medication via medicationReference, Encounter via encounter
- Based on: CarePlan via basedOn, ServiceRequest via basedOn
- Supports: MedicationDispense.authorizingPrescription, MedicationAdministration.request
- Groups: priorPrescription (medication changes), groupIdentifier (related orders)

**References**

- Patient.subject
- Practitioner.requester
- Medication.medicationReference
- Encounter.encounter

**Tools**

- validate_prescription_tool
- route_prescription_tool
- check_contraindications_tool
- check_drug_interactions_tool

| Field | Type | Description |
|---|---|---|
| status | <enum 'MedicationRequestStatus'> | Status of the medication request (active, completed, cancelled, etc.) |
| intent | <enum 'MedicationRequestIntent'> | Intent of the medication request (proposal, plan, order, etc.) |
| medication_codeable_concept | hacs_models.observation.CodeableConcept | Medication to be taken (coded) |
| dosage_instruction | list[hacs_models.medication_request.Dosage] | How medication should be taken |
| subject | <class 'str'> | Who or group medication request is for |
[... additional fields truncated for brevity ...]
```

### Step 4: Configure the LLM

```python
# Initialize the language model for HACS model extraction
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini")

print("✓ LLM configured for HACS model extraction")
print(f"Model: gpt-4o-mini")
```

Output:
```
✓ LLM configured for HACS model extraction
Model: gpt-4o-mini
```

### Step 5: Extract structured HACS models

```python
from hacs_utils.visualization import to_markdown

# One-call structured extraction using LangChain with descriptive schema context
medication_requests = asyncio.run(extract(
    llm_provider=llm,
    prompt=f"Extract MedicationRequest objects from this clinical text:\n\n{annotated_doc.text}",
    output_model=MedicationRequest,
    many=True,
    max_items=5,
    format_type=FormatType.JSON,
    strict=False,
    max_retries=3,
    use_descriptive_schema=True,
))

print(to_markdown(medication_requests, title="Example Extraction Record"))
```

Output:

```markdown
### Example Extraction Record

#### MedicationRequest

| Field | Value |
|---|---|
| resource_type | MedicationRequest |
| id | medicationrequest-c921d3cc |
| status | active |
| subject | Patient/UNKNOWN |
| medication_codeable_concept | Lisinopril 10mg |
| dosage_instruction | Take 10mg daily for hypertension management. |
| intent | order |
| created_at | 2025-08-23T18:07:02.401678Z |
| updated_at | 2025-08-23T18:07:02.401689Z |

#### MedicationRequest

| Field | Value |
|---|---|
| resource_type | MedicationRequest |
| id | medicationrequest-4c3f55dc |
| status | active |
| subject | Patient/UNKNOWN |
| medication_codeable_concept | Metformin 500mg |
| dosage_instruction | Take 500mg twice daily for type 2 diabetes control. |
| intent | order |
| created_at | 2025-08-23T18:07:02.401940Z |
| updated_at | 2025-08-23T18:07:02.401941Z |

#### MedicationRequest

| Field | Value |
|---|---|
| resource_type | MedicationRequest |
| id | medicationrequest-22d00c68 |
| status | active |
| subject | Patient/UNKNOWN |
| medication_codeable_concept | Aspirin 81mg |
| dosage_instruction | Continue taking 81mg daily for cardioprotection. |
| intent | order |
| created_at | 2025-08-23T18:07:02.401974Z |
| updated_at | 2025-08-23T18:07:02.401974Z |
```

**What happens during HACS model extraction:**

1. HACS descriptive schema provides field descriptions, enum values, and examples to the LLM
2. LangChain's structured output (function calling) ensures strict schema adherence
3. The AnnotatedDocument text is processed with rich schema context
4. LLM returns valid HACS model instances with proper enum values (status=active, intent=order)
5. Each instance has full BaseResource functionality and FHIR compliance
6. Result is a list of validated HACS resources ready for persistence

**Provider integrations**: This example uses LangChain with OpenAI. For other approaches and adapters, see the [Use & Register Tools](use_register_tools.md) guide.

### Extract multiple resource types

You can call `extract()` multiple times to build a bundle of different resource types from the same text. Example for `MedicationRequest` and `Condition`:

```python
from hacs_models import (
    MedicationRequest, Condition,
    MedicationRequestStatus, MedicationRequestIntent,
)
from hacs_models.types import ConditionClinicalStatus, ConditionVerificationStatus

med_prompt = f"""
Extract MedicationRequest objects for each medication order in the text.
- Set medication_codeable_concept.text and dosage_instruction[0].text
- Do not invent fields you cannot infer.
Text:
{annotated_doc.text}
""".strip()

cond_prompt = f"""
Extract Condition objects for each condition mentioned.
- Set code.text (e.g., "hypertension")
- Set clinical_status and verification_status
Text:
{annotated_doc.text}
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

print(to_markdown(meds, title="Extracted MedicationRequests"))
print()
print(to_markdown(conds, title="Extracted Conditions"))
```

Output (MedicationRequest):

```markdown
### Extracted MedicationRequests

#### MedicationRequest

| Field | Value |
|---|---|
| resource_type | MedicationRequest |
| id | medicationrequest-54fe2fc5 |
| status | active |
| subject | Patient/123 |
| medication_codeable_concept | Lisinopril |
| dosage_instruction | 10mg daily |
| intent | order |
| created_at | 2025-08-23T18:07:26.327782Z |
| updated_at | 2025-08-23T18:07:26.327786Z |

#### MedicationRequest

| Field | Value |
|---|---|
| resource_type | MedicationRequest |
| id | medicationrequest-b9211585 |
| status | active |
| subject | Patient/123 |
| medication_codeable_concept | Metformin |
| dosage_instruction | 500mg twice daily |
| intent | order |
| created_at | 2025-08-23T18:07:26.327883Z |
| updated_at | 2025-08-23T18:07:26.327884Z |

#### MedicationRequest

| Field | Value |
|---|---|
| resource_type | MedicationRequest |
| id | medicationrequest-2653a3d8 |
| status | active |
| subject | Patient/123 |
| medication_codeable_concept | Aspirin |
| dosage_instruction | 81mg daily |
| intent | order |
| created_at | 2025-08-23T18:07:26.327915Z |
| updated_at | 2025-08-23T18:07:26.327915Z |
```

Output (Condition):

```markdown
### Extracted Conditions

#### Condition

| Field | Value |
|---|---|
| resource_type | Condition |
| id | condition-5ad26285 |
| status | active |
| code | hypertension |
| subject | Patient/123 |
| created_at | 2025-08-23T18:07:28.884472Z |
| updated_at | 2025-08-23T18:07:28.884475Z |

#### Condition

| Field | Value |
|---|---|
| resource_type | Condition |
| id | condition-56b673eb |
| status | active |
| code | type 2 diabetes |
| subject | Patient/123 |
| created_at | 2025-08-23T18:07:28.884555Z |
| updated_at | 2025-08-23T18:07:28.884556Z |

#### Condition

| Field | Value |
|---|---|
| resource_type | Condition |
| id | condition-9358471e |
| status | active |
| code | cardioprotection |
| subject | Patient/123 |
| created_at | 2025-08-23T18:07:28.884567Z |
| updated_at | 2025-08-23T18:07:28.884568Z |
```

## Create a clinical document from extracted resources

Once you have extracted HACS models, assemble them into a structured clinical document:

```python
from hacs_models import Document
from hacs_models.types import DocumentType, DocumentStatus, ConfidentialityLevel

# Create a structured clinical document (preliminary until sections are added)
clinical_doc = Document(
    title="Medication Review Note",
    document_type=DocumentType.PROGRESS_NOTE,
    status=DocumentStatus.PRELIMINARY,
    subject_name="Patient",
    confidentiality=ConfidentialityLevel.NORMAL
)

# Add a medications section summarizing the extracted data
med_summary = f"Extracted {len(medication_requests)} medication orders:"
for mr in medication_requests:
    med_name = mr.medication_codeable_concept.text if hasattr(mr.medication_codeable_concept, 'text') else 'Unknown'
    dosage = mr.dosage_instruction[0].text if mr.dosage_instruction and hasattr(mr.dosage_instruction[0], 'text') else 'No dosage specified'
    med_summary += f"\n- {med_name}: {dosage} ({mr.status})"

clinical_doc.add_section(
    title="Current Medications",
    text=med_summary,
    code="10160-0",  # LOINC code for medication list
    metadata={"extracted_resource_count": len(medication_requests)}
)

# Update status to final after adding sections
clinical_doc.status = DocumentStatus.FINAL

print(f"✓ Created clinical document: {clinical_doc.title}")
print(f"  Status: {clinical_doc.status}")
print(f"  Sections: {len(clinical_doc.sections)}")
print(f"  Word count: {clinical_doc.get_word_count()}")
```

Output:
```
✓ Created clinical document: Medication Review Note
  Status: DocumentStatus.FINAL
  Sections: 1
  Word count: 47
```

## Next steps

Now that you have extracted HACS models and assembled a clinical document, you can:

- **[Validate models](validate_hacs_models.md)**: Examine structure and verify clinical data quality
- **[Persist resources](persist_resources.md)**: Save models to database with proper validation
- **[Visualize data](visualize_resources.md)**: Create rich visualizations and reports
- **[Extract citations](grounded_extraction.md)**: Extract mentions with character positions for text analysis

## Alternative approaches

### Extract with citations

For cases where you need precise character positions instead of structured models, see the [Extract with citations guide](grounded_extraction.md).

## Guide LLM outputs with injected fields (highly recommended)

Most healthcare resources have required enums and references. To keep the model focused on clinical content while guaranteeing validity, use `injected_fields` to pre‑fill stable fields and let the LLM fill the rest.

- What it does: merges your fields into the LLM result, then re‑validates the object
- Priority: injected_instance > injected_fields > LLM generated values
- Unknown keys are ignored by validation
- Works for both single and list outputs

Common examples:

```python
# 1) MedicationRequest: lock status, intent, and patient reference
meds = asyncio.run(extract(
    llm_provider=llm,
    prompt=med_prompt,
    output_model=MedicationRequest,
    many=True,
    injected_fields={
        "status": MedicationRequestStatus.ACTIVE,
        "intent": MedicationRequestIntent.ORDER,
        "subject": f"Patient/{patient_id}",
    },
    strict=False,
))

# 2) Condition: ensure clinical and verification statuses are valid
conds = asyncio.run(extract(
    llm_provider=llm,
    prompt=cond_prompt,
    output_model=Condition,
    many=True,
    injected_fields={
        "clinical_status": ConditionClinicalStatus.ACTIVE,
        "verification_status": ConditionVerificationStatus.CONFIRMED,
        "subject": f"Patient/{patient_id}",
    },
    strict=False,
))
```

Notes:
- Prefer enums from `hacs_models` for clarity and validation.
- You can inject any field the model supports (strings, enums, nested structures).
- This is the easiest way to fix flaky enum/literal fields while keeping the LLM’s job simple.

### Injecting larger templates (advanced)

You can also pass a partial object via `injected_instance` when you already have a resource to merge from. Use this when you want to carry forward system‑generated IDs or shared metadata.

```python
# Example: carry an existing subject reference and intent from a prior step
base_fields = {"subject": f"Patient/{patient_id}", "intent": MedicationRequestIntent.ORDER}
meds = asyncio.run(extract(
    llm_provider=llm,
    prompt=med_prompt,
    output_model=MedicationRequest,
    many=True,
    injected_fields=base_fields,
    strict=False,
))
```

---

## Structure resources directly (no long text extraction)

Use `structure()` when you want the model to produce a typed object from concise instructions and context (not chunking). This is useful for generating plans, orders, or summaries given known values.

```python
from hacs_utils.extraction import structure
from hacs_models import CarePlan

patient_ref = f"Patient/{patient_id}"
ctx = "Patient has hypertension; reduce BP over 3 months with medication and lifestyle changes."

cp = asyncio.run(structure(
    llm=llm,
    prompt=(
        "Generate a CarePlan object.\n"
        f"Subject: {patient_ref}.\n"
        "Include: title, description_text, at least one activity_text item, and one goal_refs placeholder.\n"
        f"Context: {ctx}"
    ),
    output_model=CarePlan,
    strict=False,
))
```

Synchronous convenience wrappers are also available for scripts/CLI:

```python
from hacs_utils import extract_sync, structure_sync

subset = extract_sync(llm, prompt="Extract: Jane Doe (1985-03-20)", output_model=Patient.pick("full_name","birth_date"), strict=False)
plan = structure_sync(llm, prompt="Return a CarePlan for Patient/123 with a title and one activity_text", output_model=CarePlan, strict=False)
```

Implementation details:
- Descriptive schema is enabled by default; field descriptions and allowed values are injected into prompts.
- Provider‑native structured outputs (OpenAI Responses.parse, Anthropic tool JSON) are preferred when available; otherwise LangChain function calling is used.
- Injected fields are merged after parsing, then the object is re‑validated.