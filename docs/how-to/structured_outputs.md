## Generate structured outputs from unstructured text

This guide shows how to use LLMs to extract data directly into typed HACS models using `pick()` and `extract()`.

For grounded mention extraction with character spans, see [Extract Annotations](extract_annotations.md).

Prerequisites:

- `uv pip install -U hacs-utils[langchain]`
- An LLM provider (OpenAI, Anthropic, or a client exposing `ainvoke`/`invoke`)

## Core approach: pick() + extract()

Use a subset of a HACS model with `pick()` to define your schema, then ask the LLM to populate it. This yields Pydantic-validated instances you can persist.

```python
import asyncio
from hacs_models import MedicationRequest
from hacs_models.annotation import FormatType
from hacs_utils.structured import extract
from langchain_openai import ChatOpenAI

# Define a minimal schema for extraction
MedicationRequestInfo = MedicationRequest.pick(
    "status", "intent", "medication_codeable_concept", "dosage_instruction"
)

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

async def run():
    text = (
        "Started Lisinopril 10mg daily; Metformin 500mg twice daily for diabetes."
    )
    prompt = (
        "From the text, extract medication requests with status, intent, "
        "medication_codeable_concept, and dosage_instruction.\n\nTEXT:\n" + text
    )
    items = await extract(
        llm_provider=llm,
        prompt=prompt,
        output_model=MedicationRequestInfo,
        many=True,
        max_items=10,
        format_type=FormatType.JSON,
        fenced_output=True,
        max_retries=1,
        strict=True,
    )
    return items

mr_list = asyncio.run(run())
for mr in mr_list:
    print(mr.model_dump())

# Example output:
# {
#   'id': None,
#   'resource_type': 'MedicationRequest', 
#   'created_at': '2024-01-15T10:30:00Z',
#   'updated_at': '2024-01-15T10:30:00Z',
#   'status': 'active',
#   'intent': 'order',
#   'medication_codeable_concept': {
#     'text': 'Lisinopril',
#     'coding': [{'system': 'http://www.nlm.nih.gov/research/umls/rxnorm', 
#                 'code': '29046', 'display': 'Lisinopril'}]
#   },
#   'dosage_instruction': [{
#     'text': '10mg daily',
#     'timing': {'repeat': {'frequency': 1, 'period': 1, 'periodUnit': 'd'}}
#   }]
# }
# {
#   'id': None,
#   'resource_type': 'MedicationRequest',
#   'status': 'active', 
#   'intent': 'order',
#   'medication_codeable_concept': {
#     'text': 'Metformin',
#     'coding': [{'system': 'http://www.nlm.nih.gov/research/umls/rxnorm',
#                 'code': '6809', 'display': 'Metformin'}]
#   },
#   'dosage_instruction': [{
#     'text': '500mg twice daily for diabetes',
#     'timing': {'repeat': {'frequency': 2, 'period': 1, 'periodUnit': 'd'}}
#   }]
# }
```

## API reference: extract()

```python
from hacs_utils.structured import extract

async def extract(
    llm_provider: Any,
    prompt: str,
    output_model: Type[T],
    *,
    many: bool = False,
    max_items: int = 10,
    format_type: FormatType = FormatType.JSON,
    fenced_output: bool = True,
    max_retries: int = 1,
    strict: bool = True,
    **kwargs,
) -> T | list[T]:
    ...
```

- **llm_provider**: Object exposing `ainvoke(prompt)` or `invoke(prompt)` (e.g., LangChain `ChatOpenAI`).
- **prompt**: Full instruction including any input text.
- **output_model**: Pydantic class (e.g., `MedicationRequest.pick(...)`).
- **many / max_items**: Return a list up to `max_items`, otherwise a single instance.
- **format_type / fenced_output**: Expect JSON or YAML, optionally fenced with triple backticks.
- **max_retries**: Repair passes if parsing fails.
- **strict**: When true, raise if parsing still fails after retries.

## Working with pick()

The `pick()` method creates a subset Pydantic model containing only specified fields:

```python
from hacs_models import Patient, Observation

# Create lightweight schemas for extraction
PatientInfo = Patient.pick("full_name", "birth_date", "gender")
VitalSigns = Observation.pick("value_quantity", "code", "status")

# Use in prompts
async def extract_demographics(text: str):
    prompt = f"Extract patient demographics from: {text}"
    return await extract(llm, prompt, PatientInfo)

async def extract_vitals(text: str):  
    prompt = f"Extract vital signs measurements from: {text}"
    return await extract(llm, prompt, VitalSigns, many=True)

# Example usage
patient = await extract_demographics("Jane Doe, DOB 1990-01-01, female")
vitals = await extract_vitals("BP 120/80, HR 72 bpm, temp 98.6°F")

print(patient.model_dump())
# {
#   'id': None,
#   'resource_type': 'Patient',
#   'created_at': '2024-01-15T10:30:00Z',
#   'updated_at': '2024-01-15T10:30:00Z', 
#   'full_name': 'Jane Doe',
#   'birth_date': '1990-01-01',
#   'gender': 'female'
# }

for vital in vitals:
    print(vital.model_dump())
# {
#   'id': None,
#   'resource_type': 'Observation',
#   'value_quantity': {'value': 120, 'unit': 'mmHg'},
#   'code': {'text': 'Systolic blood pressure'},
#   'status': 'final'
# }
```

## Sync helpers for specific providers

When using concrete clients, sync helpers are available:

```python
from hacs_utils.structured import (
    generate_structured_output_openai,
    generate_structured_output_anthropic,
)

# OpenAI client (hacs_utils integration)
from hacs_utils.integrations.openai import OpenAIClient
client = OpenAIClient()
result = generate_structured_output_openai(
    client, "Extract patient: John Smith, 45 years old", PatientInfo
)

# Anthropic client  
import anthropic
client = anthropic.Anthropic()
result = generate_structured_output_anthropic(
    client, "Extract patient: John Smith, 45 years old", PatientInfo
)
```

## Format types and validation

Control the expected output format:

```python
from hacs_models.annotation import FormatType

# JSON (default)
result = await extract(llm, prompt, PatientInfo, format_type=FormatType.JSON)

# YAML
result = await extract(llm, prompt, PatientInfo, format_type=FormatType.YAML)

# With/without fenced code blocks
result = await extract(llm, prompt, PatientInfo, fenced_output=True)   # Expects ```json
result = await extract(llm, prompt, PatientInfo, fenced_output=False)  # Raw JSON
```

## Error handling and retries

The `extract()` function includes built-in repair logic:

```python
try:
    result = await extract(
        llm, prompt, PatientInfo,
        max_retries=2,    # Try to repair invalid JSON/YAML
        strict=True       # Raise on final failure
    )
except ValueError as e:
    print(f"Could not parse structured output: {e}")
    # Handle fallback logic

# Non-strict mode returns fallback instances
result = await extract(
    llm, prompt, PatientInfo,
    strict=False  # Returns default instance on parse failure
)
```

## Integration with persistence and modeling

Once you have typed records, use modeling helpers to persist them:

```python
from hacs_tools.domains.modeling import pin_resource, set_reference
from hacs_tools.domains.database import save_record

# Extract and persist patient
patient_data = await extract(llm, prompt, PatientInfo)
patient_resource = pin_resource("Patient", patient_data.model_dump())
patient_dict = patient_resource.data["resource"]
save_record(resource=patient_dict)

# Extract medications and link to patient
medications = await extract(llm, prompt, MedicationRequestInfo, many=True)
for med_data in medications:
    med_resource = pin_resource("MedicationRequest", med_data.model_dump())
    med_dict = med_resource.data["resource"]
    
    # Set patient reference
    med_with_ref = set_reference(
        med_dict, field="subject", 
        reference=patient_dict["id"]
    ).data["resource"]
    
    save_record(resource=med_with_ref)
```

## Complex extraction patterns

### Multi-step extraction

```python
async def extract_clinical_summary(text: str):
    # Step 1: Extract patient
    patient = await extract(llm, f"Extract patient from: {text}", PatientInfo)
    
    # Step 2: Extract conditions  
    conditions = await extract(
        llm, f"Extract medical conditions from: {text}", 
        ConditionInfo, many=True
    )
    
    # Step 3: Extract medications
    medications = await extract(
        llm, f"Extract medications from: {text}",
        MedicationRequestInfo, many=True  
    )
    
    return {
        "patient": patient,
        "conditions": conditions, 
        "medications": medications
    }
```

### Attribute-based grouping

```python
async def extract_with_grouping(text: str):
    # Include grouping instructions in prompt
    prompt = f"""
    Extract medications with grouping attributes:
    1. Each entity must have a 'medication_group' attribute
    2. Group related information by medication name
    
    TEXT: {text}
    """
    
    items = await extract(llm, prompt, MedicationRequestInfo, many=True)
    
    # Group by attributes (if your model includes them)
    grouped = {}
    for item in items:
        if hasattr(item, 'attributes') and item.attributes:
            group = item.attributes.get('medication_group', 'unknown')
            grouped.setdefault(group, []).append(item)
    
    return grouped
```

## Types reference

- **`FormatType`**: Enum with `JSON` and `YAML` values
- **`pick()`**: Class method on `BaseResource` that creates subset models
- **`extract()`**: Async function returning typed instances or lists
- **Provider detection**: Auto-detects OpenAI (`.chat`), Anthropic (`.messages.create`), or generic (`ainvoke`/`invoke`)

## Next steps

- **Validation**: Extracted instances are fully validated Pydantic models
- **Persistence**: Use `pin_resource()` and `save_record()` to persist  
- **Visualization**: Use `resource_to_markdown()` to preview results
- **Grounded extraction**: For character spans and alignment, see [Extract Annotations](extract_annotations.md)

This completes the workflow from unstructured text → typed HACS models → validated records.
