## Extract grounded mentions and annotations from unstructured text

This guide shows how to:

- Use an LLM to extract grounded mentions from text as `Extraction` objects (with character spans)
- Chunk long texts while preserving character offsets for alignment
- Render and preview annotations for QA

For structured output generation into typed HACS models, see [Structured Outputs](structured_outputs.md).

Prerequisites:

- `uv pip install -U hacs-utils[langchain]`
- An LLM provider (OpenAI, Anthropic, or a client exposing `ainvoke`/`invoke`)

### Quick preview: render annotations

```python
from hacs_models import AnnotatedDocument, Extraction, CharInterval
from hacs_utils.visualization import annotations_to_markdown

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

md = annotations_to_markdown(doc)
print(md)
# Output:
# | Class | Span | Snippet |
# |---|---|---|
# | Blood Pressure | [3-9] | … BP **128/82** , HR 72 … |
```

## Grounded mentions with chunked extraction

For long inputs, use chunking to keep prompts within token limits while preserving character offsets.

```python
from hacs_utils.structured import generate_chunked_extractions
from hacs_models import ChunkingPolicy, AnnotatedDocument
from hacs_utils.visualization import visualize_annotations

# Example provider: any client with .chat(...) (OpenAI-like) or ainvoke/invoke
from langchain_openai import ChatOpenAI

text = """
The patient was prescribed Lisinopril 10mg daily for hypertension.
Metformin 500mg twice daily for diabetes was also started.
""".strip()

prompt = (
    "Extract mentions of medications, doses, and frequencies. "
    "Return a list of {extraction_class, extraction_text, attributes?}."
)

llm = ChatOpenAI(model="gpt-5", temperature=0)
extractions = generate_chunked_extractions(
    client=llm,
    text=text,
    base_prompt=prompt,
    policy=ChunkingPolicy(max_chars=1000, chunk_overlap=100),
    provider="openai",  # "anthropic" or "auto" also supported
)

annotated = AnnotatedDocument(text=text, extractions=extractions)

# Example output from the LLM call:
print(f"Found {len(extractions)} extractions:")
for i, ext in enumerate(extractions):
    print(f"  {i+1}. {ext.extraction_class}: \"{ext.extraction_text}\"")
    if ext.char_interval:
        print(f"     Span: [{ext.char_interval.start_pos}-{ext.char_interval.end_pos}]")

# Output:
# Found 4 extractions:
#   1. medication: "Lisinopril"
#      Span: [23-33]
#   2. dose: "10mg"
#      Span: [34-38]
#   3. frequency: "daily"
#      Span: [39-44]
#   4. medication: "Metformin"
#      Span: [76-85]

visualize_annotations(annotated)  # HTML preview
```

### Method and parameters

```python
from hacs_utils.structured import generate_chunked_extractions

def generate_chunked_extractions(
    client: Any,
    text: str,
    *,
    base_prompt: str,
    policy: ChunkingPolicy,
    provider: Literal["openai", "anthropic", "auto"] = "auto",
    model: str | None = None,
    stream: bool = False,
    max_tokens: int = 1024,
    case_insensitive_align: bool = True,
    **kwargs,
) -> list[Extraction]:
    ...
```

- **client**: LLM client. Auto-detected by interface: OpenAI-like (`.chat`), Anthropic (`.messages.create`), or generic (`ainvoke`/`invoke`).
- **text**: Full input text to chunk and extract from.
- **base_prompt**: Instruction used for each chunk (chunk text is appended automatically).
- **policy**: `ChunkingPolicy(max_chars, chunk_overlap, strategy=...)` controls splitting.
- **provider**: Force a provider (`"openai"`, `"anthropic"`) or let the function auto-detect.
- **model, stream, max_tokens, kwargs**: Passed to the underlying client.
- **case_insensitive_align**: If true, align spans ignoring case.

Returns: `list[Extraction]` with optional `CharInterval` and `AlignmentStatus` populated when alignment succeeds.



## Advanced: custom `Annotator` and `Resolver`

Use `Annotator` to drive batched prompting over chunks and a `Resolver` to parse and align outputs.

```python
from hacs_utils.annotation import Annotator
from hacs_utils.annotation.prompting import PromptTemplateStructured
from hacs_utils.annotation.resolver import Resolver
from hacs_utils.annotation.inference import OpenAILanguageModel
from hacs_models.annotation import FormatType

tmpl = PromptTemplateStructured(
    template_text=(
        "Extract clinical entities as a list of objects with fields: "
        "extraction_class, extraction_text, and optional attributes."
    ),
    variables=[],
    format_type=FormatType.JSON,
    fenced_output=True,
)

lm = OpenAILanguageModel()  # assumes environment configuration
annotator = Annotator(language_model=lm, prompt_template=tmpl)
doc = annotator.annotate_text(
    text="BP 128/82, HR 72",
    resolver=Resolver(),
    max_char_buffer=4000,
    chunk_overlap=0,
    batch_length=4,
    variables=None,
)

print(f"Extracted {len(doc.extractions or [])} entities:")
for ext in doc.extractions or []:
    print(f"- {ext.extraction_class}: '{ext.extraction_text}'")
    if ext.char_interval:
        print(f"  Position: {ext.char_interval.start_pos}-{ext.char_interval.end_pos}")

# Example output:
# Extracted 2 entities:
# - blood_pressure: '128/82'
#   Position: 3-9
# - heart_rate: '72'
#   Position: 14-16
```

### Methods and parameters

- `Annotator.annotate_text(text, resolver, max_char_buffer=4000, chunk_overlap=0, batch_length=4, variables=None)`
  - **text**: Input text
  - **resolver**: A `Resolver` implements `parse(output)`, `resolve(parsed)`, and optional `align(extractions, chunk_text, char_offset=0, case_insensitive=True)`
  - **max_char_buffer / chunk_overlap / batch_length**: Chunking and batching controls
  - **variables**: Optional dict used when rendering the prompt template

- `Resolver`
  - `parse(output: str) -> Any`: Parses fenced JSON/YAML based on `FormatType`
  - `resolve(parsed: Any) -> list[Extraction]`: Maps parsed data to `Extraction`
  - `align(extractions, chunk_text, char_offset=0, case_insensitive=True) -> list[Extraction]`: Adds `CharInterval` and `AlignmentStatus`

## Annotation types reference

- **`Extraction`**: `{ extraction_class: str, extraction_text: str, char_interval?: CharInterval, alignment_status?, attributes?: dict }`
- **`CharInterval`**: `{ start_pos?: int, end_pos?: int }`
- **`AlignmentStatus`**: enum with values like `MATCH_EXACT`, `MATCH_FUZZY`, `NO_MATCH`
- **`AnnotatedDocument`**: `{ document_id: str, text?: str, extractions?: list[Extraction] }`
- **`ChunkingPolicy`**: `{ strategy: "char"|"token"|"recursive"|..., max_chars: int, chunk_overlap: int, sentence_aware: bool }`

## Visualize and QA

```python
from hacs_utils.visualization import annotations_to_markdown, visualize_annotations
from hacs_models import AnnotatedDocument

annotated = AnnotatedDocument(text=text, extractions=extractions)
print(annotations_to_markdown(annotated))
# Output:
# | Class | Span | Snippet |
# |---|---|---|
# | Medication | [23-33] | … prescribed **Lisinopril** 10mg daily … |
# | Dose | [34-38] | … Lisinopril **10mg** daily for … |
# | Frequency | [39-44] | … 10mg **daily** for hypertension … |
# | Medication | [76-85] | … diabetes was also started with **Metformin** 500mg … |

visualize_annotations(annotated)  # Renders interactive HTML with color-coded highlights
```

## Next steps

- **Structured outputs**: For typed model generation, see [Structured Outputs](structured_outputs.md)
- **Persistence**: Use `pin_resource()` and `save_record()` to persist extracted data (see Medication extraction tutorial)
- **Terminology**: Use terminology tools to align extracted mentions with clinical codes

This completes the workflow from unstructured text → grounded mentions with character spans.
