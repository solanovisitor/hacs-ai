## Extract with citations (concise, end‑to‑end)

Minimal example that extracts type-only citations, then typed resources with spans from the same text. No mocks; runs with your real API key.

Prerequisites:
- `uv pip install -U "hacs-utils[langchain]"`
- `OPENAI_API_KEY` in your `.env`

```python
from dotenv import load_dotenv
load_dotenv()

import asyncio
from langchain_openai import ChatOpenAI
from hacs_utils.extraction import (
    extract_type_citations,
    extract_citations,
)
from hacs_utils.visualization import to_markdown, annotations_to_markdown
from hacs_models import MedicationRequest, Condition, AnnotatedDocument, Extraction, CharInterval

text = (
    "Patient was prescribed Lisinopril 10mg daily for hypertension management.\n"
    "Started Metformin 500mg twice daily for type 2 diabetes control.\n"
    "Continue current Aspirin 81mg daily for cardioprotection."
)

llm = ChatOpenAI(model="gpt-4o-mini")

# 1) Find type-only citations across the text
type_cites = asyncio.run(extract_type_citations(
    llm,
    source_text=text,
    max_items=10,
))

print("Type-only citations (first 3):")
print(type_cites[:3])

# 2) Extract typed resources with citations/spans
meds = asyncio.run(extract_citations(
    llm,
    source_text=text,
    resource_model=MedicationRequest,
    injected_fields={"status": "active", "intent": "order", "subject": "Patient/123"},
    max_items=5,
))

conds = asyncio.run(extract_citations(
    llm,
    source_text=text,
    resource_model=Condition,
    injected_fields={"clinical_status": "active", "verification_status": "confirmed", "subject": "Patient/123"},
    max_items=5,
))

print(to_markdown([m["record"] for m in meds], title="MedicationRequest (first)"))
print("\nCitation:", meds[0]["citation"])  # literal snippet
print("Span:", meds[0]["char_interval"])   # start/end positions

print(to_markdown([c["record"] for c in conds], title="Condition (first)"))
print("\nCitation:", conds[0]["citation"])  # literal snippet
print("Span:", conds[0]["char_interval"])   # start/end positions

# 3) Optional: Build an AnnotatedDocument for visualization
annotations = [
    Extraction(
        extraction_class=it["record"].resource_type,
        extraction_text=it["citation"],
        char_interval=CharInterval(
            start_pos=it["char_interval"]["start_pos"],
            end_pos=it["char_interval"]["end_pos"],
        ),
    )
    for it in (meds + conds)
]

annotated = AnnotatedDocument(text=text, extractions=annotations)
print("\nMentions table (±30 chars):")
print(annotations_to_markdown(annotated, context_chars=30))
```

**Example output:**
```
Type-only citations (first 3):
[
  {"resource_type": "MedicationRequest", "citation": "Lisinopril 10mg daily", "start_pos": 24, "end_pos": 44},
  {"resource_type": "Condition", "citation": "hypertension", "start_pos": 49, "end_pos": 61},
  {"resource_type": "MedicationRequest", "citation": "Metformin 500mg twice daily", "start_pos": 82, "end_pos": 109}
]

### MedicationRequest (first)

#### MedicationRequest

| Field | Value |
|---|---|
| resource_type | MedicationRequest |
| id | medicationrequest-... |
| status | active |
| intent | order |
| subject | Patient/123 |
| medication_codeable_concept | Lisinopril |
| dosage_instruction | 10mg daily |

Citation: Lisinopril 10mg daily
Span: {'start_pos': 24, 'end_pos': 44}

### Condition (first)

#### Condition

| Field | Value |
|---|---|
| resource_type | Condition |
| id | condition-... |
| clinical_status | active |
| verification_status | confirmed |
| code | hypertension |
| subject | Patient/123 |

Citation: hypertension
Span: {'start_pos': 49, 'end_pos': 61}

Mentions table (±30 chars):
| Class | Span | Snippet |
|---|---|---|
| MedicationRequest | [24-44] | … prescribed **Lisinopril 10mg daily** for hyper… |
| Condition | [49-61] | … 10mg daily for **hypertension** management. Sta… |
| MedicationRequest | [82-109] | … Started **Metformin 500mg twice daily** for typ… |
| MedicationRequest | [156-174] | … current **Aspirin 81mg daily** for cardioprotec… |
```

> Tip: `injected_fields` pre‑fills enums and references (status, intent, subject), letting the model focus on clinical content while keeping outputs valid.
