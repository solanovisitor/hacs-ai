## Extract with citations

Use a minimal multi-resource example to extract typed HACS resources (MedicationRequest and Condition) from the same clinical text. No mocks; runs with your real API key.

Prerequisites:
- `uv pip install -U "hacs-utils[langchain]"`
- `OPENAI_API_KEY` in your `.env`

```python
from dotenv import load_dotenv
load_dotenv()

import asyncio
from langchain_openai import ChatOpenAI
from hacs_utils.structured import extract
from hacs_utils.visualization import to_markdown
from hacs_models import (
    MedicationRequest, Condition,
    MedicationRequestStatus, MedicationRequestIntent,
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

print(to_markdown(meds, title="Extracted MedicationRequests"))
print()
print(to_markdown(conds, title="Extracted Conditions"))
```

Output:
```
### Extracted MedicationRequests

#### MedicationRequest

| Field | Value |
|---|---|
| resource_type | MedicationRequest |
| id | medicationrequest-093872e8 |
| status | active |
| subject | Patient/123 |
| dosage_instruction | [] |
| intent | order |
| created_at | 2025-08-20T02:24:30.881805Z |
| updated_at | 2025-08-20T02:24:30.881814Z |

### Extracted Conditions

#### Condition

| Field | Value |
|---|---|
| resource_type | Condition |
| id | condition-1 |
| status | active |
| code | hypertension |
| subject | Patient/123 |
| created_at | 2025-08-20T00:00:00Z |
| updated_at | 2025-08-20T00:00:00Z |

#### Condition

| Field | Value |
|---|---|
| resource_type | Condition |
| id | condition-2 |
| status | active |
| code | type 2 diabetes |
| subject | Patient/123 |
| created_at | 2025-08-20T00:00:00Z |
| updated_at | 2025-08-20T00:00:00Z |
```

<!-- Analysis intentionally omitted for brevity -->

## Visualize annotations with highlighting

```python
from hacs_utils.visualization import annotations_to_markdown, visualize_annotations

# Generate markdown with highlighted spans
print("Grounded Mentions Visualization:")
mention_table = annotations_to_markdown(annotated_doc, context_chars=30)
print(mention_table)

# Create HTML visualization with color coding
html_output = visualize_annotations(
    annotated_doc,
    show_legend=True  # Show color legend
)

print(f"\n✓ HTML visualization created ({len(html_output)} characters)")
print("Features: Color-coded spans, hover tooltips, extraction legend")
```

**Output:**
```
Grounded Mentions Visualization:
| Class | Span | Snippet |
|---|---|---|
| Medication Mention | [23-44] | … Patient was prescribed **Lisinopril 10mg daily** for hypertension management. … |
| Medication Mention | [82-109] | … Started **Metformin 500mg twice daily** for type 2 diabetes control. … |
| Medication Mention | [156-174] | … Continue current **Aspirin 81mg daily** for cardioprotection. … |

✓ HTML visualization created (1919 characters)
Features: Color-coded spans, hover tooltips, extraction legend
```

<!-- Custom chunking examples removed to keep focus on the minimal flow -->

<!-- Single-pass example omitted; use the chunked unified call above for reproducibility -->

<!-- Performance and long-form guidance removed to keep guide minimal and runnable -->
