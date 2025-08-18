# Extract Annotations and structured outputs

Two common paths: LLM extraction into typed models, and annotation visualization.

```python
# Prereq: uv pip install -U hacs-utils[langchain]
from hacs_models import AnnotatedDocument, Extraction, CharInterval
from hacs_utils.visualization import annotations_to_markdown

# Annotation preview (Markdown)
doc = AnnotatedDocument(
    text="BP 128/82, HR 72",
    extractions=[Extraction(extraction_class="blood_pressure", extraction_text="128/82", char_interval=CharInterval(start_pos=3, end_pos=9))]
)
print(annotations_to_markdown(doc).splitlines()[0])
```

```
| Class | Span | Snippet |
```
