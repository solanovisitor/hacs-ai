## Medication extraction → typed records → Composition (HACS)

In this tutorial, you will extract medication data from clinical text, validate it with typed models via `pick()`, instantiate FHIR‑aligned resources, and group them into a `Composition` for persistence.

If you're new to HACS, complete the [Quick Start](../quick-start.md) first.

### Prerequisites

- Complete the [Quick Start](../quick-start.md)
- A LangChain ChatModel API key (OpenAI, Anthropic, etc.)
- A running Postgres if you plan to persist records (set `DATABASE_URL`)

```python
from hacs_utils.structured import generate_chunked_extractions
from hacs_models import ChunkingPolicy
from langchain_openai import ChatOpenAI  # or any ChatModel

# Input text
input_text = (
    "The patient was prescribed Lisinopril and Metformin last month.\n"
    "He takes the Lisinopril 10mg daily for hypertension, but often misses\n"
    "his Metformin 500mg dose which should be taken twice daily for diabetes.\n"
)

# Prompt with grouping rule
prompt = (
    "Extract medications with their details, using attributes to group related information:\n\n"
    "1. Extract entities in the order they appear in the text\n"
    "2. Each entity must have a 'medication_group' attribute linking it to its medication\n"
    "3. All details about a medication should share the same medication_group value\n"
)

### 1) Grounded mentions (optional)
# Run extraction with source grounding and chunk alignment to see mentions and spans
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
extractions = generate_chunked_extractions(
    client=llm,
    text=input_text,
    base_prompt=prompt,
    policy=ChunkingPolicy(max_chars=1000, overlap=100),
    provider="openai",
)

# Group by medication_group attribute
med_groups: dict[str, list] = {}
for e in extractions:
    attrs = getattr(e, "attributes", None) or {}
    group = attrs.get("medication_group")
    if not group:
        print(f"Warning: Missing medication_group for {e.extraction_text}")
        continue
    med_groups.setdefault(group, []).append(e)

print(f"Input text: {input_text.strip()}\n")
print("Extracted Medications:")
for med, items in med_groups.items():
    print(f"\n* {med}")
    for e in items:
        pos = ""
        if e.char_interval and e.char_interval.start_pos is not None and e.char_interval.end_pos is not None:
            pos = f" (pos: {e.char_interval.start_pos}-{e.char_interval.end_pos})"
        print(f"  • {e.extraction_class.capitalize()}: {e.extraction_text}{pos}")

# Visualize extractions
from hacs_utils.visualization import visualize_annotations
from hacs_models import AnnotatedDocument
annotated = AnnotatedDocument(text=input_text, extractions=extractions)
visualize_annotations(annotated)

```
[Visualization] annotations HTML type: str
[Visualization] annotations HTML length: 1555
```

Rendered (Markdown):

Annotations preview:

| Class | Span | Snippet |
|---|---|---|
| Blood Pressure | [3-9] | … BP  **128/82** , HR 72 … |

### 2) Structured records (typed) with pick() + persist
from hacs_models import MedicationRequest, Patient
from hacs_utils.structured import extract
from hacs_tools.domains.modeling import pin_resource, make_reference, set_reference
from hacs_tools.domains.database import save_record
from hacs_models.composition import Composition

# Define a subset schema for MedicationRequest (typed)
MedicationRequestInfo = MedicationRequest.pick("status", "intent", "medication_codeable_concept", "dosage_instruction")

# Extract a list of medication requests from text (typed, many=True)
mr_list = extract(
  llm,
  prompt=(
    "From the text, extract medication requests with status, intent, medication_codeable_concept, and dosage_instruction.\n"
    "Use the medication name as displayed in the text."
    f"\n\nTEXT:\n{input_text}"
  ),
  output_model=MedicationRequestInfo,
  many=True,
)

# Instantiate and persist Patient and MedicationRequests
patient_res = pin_resource("Patient", {"full_name": "Eve Everywoman"})
pat_dict = (patient_res.data or {}).get("resource", {})

# Always visualize created records
from hacs_utils.visualization import resource_to_markdown
print("Created Patient:")
print(resource_to_markdown(pat_dict, include_json=False))

save_record(resource=pat_dict)

pat_ref = make_reference(resource=pat_dict).data["reference"]
persisted_mrs = []
for mri in mr_list:
  mr_res = pin_resource("MedicationRequest", mri.model_dump())
  mr_dict = (mr_res.data or {}).get("resource", {})
  
  # Always visualize created medication records
  print(f"Created MedicationRequest:")
  print(resource_to_markdown(mr_dict, include_json=False))
  
  # Set subject reference to patient
  mr_with_subject = set_reference(mr_dict, field="subject", reference=pat_ref).data["resource"]
  save_record(resource=mr_with_subject)
  persisted_mrs.append(mr_with_subject)

### 3) Build a Composition with a medications section and persist
comp = Composition(title="Medications on Discharge")
lines = []
for group, items in med_groups.items():
  details = ", ".join(e.extraction_text for e in items if e.extraction_class != "medication")
  lines.append(f"{group}: {details}")
comp.add_section(title="Medications", text="\n".join(lines))
save_record(resource=comp.model_dump())
```

Notes:
- `generate_chunked_extractions` performs chunking, extraction, alignment, and best‑effort deduplication, mirroring LangExtract’s approach.
- For large texts, increase `extraction_passes` by calling the function per pass and merging results.


