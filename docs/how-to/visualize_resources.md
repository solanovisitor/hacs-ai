## Visualize HACS models and documents

This guide shows how to create rich visualizations of HACS resources, annotated documents, and extraction results.

Prerequisites:
- Extracted HACS models (see [Extract Annotations](extract_annotations.md))
- `uv pip install -U hacs-utils[visualization]`

## Visualize individual resources

Using the `medication_requests` from the extraction guide:

```python
# Visualize the structured HACS models
from hacs_utils.visualization import resource_to_markdown, to_markdown

print("Generating HACS model visualizations...")

for i, med_request in enumerate(medication_requests, 1):
    print(f"\n--- MedicationRequest {i} Visualization ---")
    markdown_view = resource_to_markdown(med_request, include_json=False)
    print(markdown_view)
```

**Output:**
```
Generating HACS model visualizations...

--- MedicationRequest 1 Visualization ---
#### MedicationRequest

| Field | Value |
|---|---|
| resource_type | MedicationRequest |
| id | medreq-lisinopril-1 |
| status | active |
| subject | Patient/unknown |
| medication_codeable_concept | Lisinopril 10 mg oral tablet |
| dosage_instruction | Take 10 mg orally once daily. |
| priority | routine |
| intent | order |
| created_at | 2025-08-19T00:00:00Z |
| updated_at | 2025-08-19T00:00:00Z |

--- MedicationRequest 2 Visualization ---
#### MedicationRequest

| Field | Value |
|---|---|
| resource_type | MedicationRequest |
| id | medreq-metformin-1 |
| status | active |
| subject | Patient/unknown |
| medication_codeable_concept | Metformin 500 mg oral tablet |
| dosage_instruction | Take 500 mg orally twice daily (morning and evening). |
| priority | routine |
| intent | order |
| created_at | 2025-08-19T00:00:00Z |
| updated_at | 2025-08-19T00:00:00Z |
```

## Create extraction summaries

```python
# Create a summary document showing the extraction results
print("Creating extraction summary...")

summary_text = f"""
Extraction Summary for Document: {annotated_doc.document_id}

Source text length: {len(annotated_doc.text)} characters
Extracted {len(medication_requests)} MedicationRequest objects:

"""

for i, mr in enumerate(medication_requests, 1):
    med_name = mr.medication_codeable_concept.text if hasattr(mr.medication_codeable_concept, 'text') else 'Unknown'
    summary_text += f"{i}. {med_name} ({mr.status}) - {mr.intent}\n"

print(summary_text)

# Also create a structured table summary
print("Structured HACS Models Summary:")
print("| Medication | Status | Intent | Dosage |")
print("|---|---|---|---|")

for mr in medication_requests:
    med_name = mr.medication_codeable_concept.text if hasattr(mr.medication_codeable_concept, 'text') else 'Unknown'
    dosage_text = "No dosage"
    if mr.dosage_instruction:
        dosage_text = mr.dosage_instruction[0].text if hasattr(mr.dosage_instruction[0], 'text') else str(mr.dosage_instruction[0])
    
    print(f"| {med_name} | {mr.status} | {mr.intent} | {dosage_text} |")
```

**Output:**
```
Creating extraction summary...

Extraction Summary for Document: clinical_note_001

Source text length: 196 characters
Extracted 3 MedicationRequest objects:

1. Lisinopril 10 mg oral tablet (active) - order
2. Metformin 500 mg oral tablet (active) - order
3. Aspirin 81 mg oral tablet (active) - order

Structured HACS Models Summary:
| Medication | Status | Intent | Dosage |
|---|---|---|---|
| Lisinopril 10 mg oral tablet | active | order | Take 10 mg orally once daily. |
| Metformin 500 mg oral tablet | active | order | Take 500 mg orally twice daily (morning and evening). |
| Aspirin 81 mg oral tablet | active | order | Take 81 mg orally once daily. |
```

## Document-resource linking visualization

```python
from hacs_utils.visualization import to_markdown

# Create summary metadata linking the structured models to the source document
model_metadata = []
for med_request in medication_requests:
    med_concept = med_request.medication_codeable_concept
    med_name = med_concept.text if hasattr(med_concept, 'text') else 'Unknown'
    model_metadata.append({
        "source_document": annotated_doc.document_id,
        "resource_type": med_request.resource_type,
        "resource_id": med_request.id,
        "extracted_medication": med_name,
        "extraction_timestamp": med_request.created_at
    })

# Render a consolidated document summary
print(to_markdown(annotated_doc, resources=medication_requests, show_annotations=False))
```

## Interactive HTML visualization

```python
from hacs_utils.visualization import visualize_resource, resource_to_html_widget

# Create interactive HTML widgets for notebook environments
for i, mr in enumerate(medication_requests[:2], 1):  # Show first 2
    print(f"\n=== Interactive Widget {i} ===")
    
    # Rich HTML widget with tabs (Rendered/JSON/YAML/Schema)
    widget_html = resource_to_html_widget(
        mr, 
        title=f"MedicationRequest {i}",
        default_view="rendered"
    )
    
    print("HTML widget created with tabs:")
    print("- Rendered: Human-readable table")
    print("- JSON: Raw JSON representation") 
    print("- YAML: YAML representation")
    print("- Schema: Model schema documentation")
    print(f"Widget size: {len(widget_html)} characters")

# Simple HTML card for individual resources
html_card = visualize_resource(
    medication_requests[0],
    title="Sample MedicationRequest",
    show_json=True
)
print(f"\nHTML card generated: {len(html_card)} characters")
print("Includes: Resource table + JSON view + styling")
```

## Batch visualization utilities

```python
# Visualize all resources at once using unified to_markdown
print("=== Unified Visualization ===")

# All resources in one view
all_resources_md = to_markdown(
    medication_requests, 
    title="All Extracted MedicationRequests",
    include_json=False
)
print(all_resources_md)

# Document + resources combined
document_summary = to_markdown(
    annotated_doc,
    resources=medication_requests,
    show_annotations=False,
    title="Clinical Note with Extracted Medications"
)
print("\n" + document_summary)
```

## Export visualizations

```python
import json
from datetime import datetime

# Create a comprehensive report
report = {
    "extraction_report": {
        "document_id": annotated_doc.document_id,
        "extraction_timestamp": datetime.now().isoformat(),
        "source_text_length": len(annotated_doc.text),
        "extracted_count": len(medication_requests),
        "resources": [
            {
                "id": mr.id,
                "type": mr.resource_type,
                "medication": mr.medication_codeable_concept.text if hasattr(mr.medication_codeable_concept, 'text') else 'Unknown',
                "status": mr.status,
                "intent": mr.intent,
                "dosage": mr.dosage_instruction[0].text if mr.dosage_instruction and hasattr(mr.dosage_instruction[0], 'text') else 'No dosage'
            }
            for mr in medication_requests
        ]
    }
}

# Save report
with open("extraction_report.json", "w") as f:
    json.dump(report, f, indent=2)

print("✓ Extraction report saved to extraction_report.json")
print(f"Report contains {len(report['extraction_report']['resources'])} resource summaries")

# Create markdown report
markdown_report = f"""# Extraction Report

**Document:** {annotated_doc.document_id}  
**Extracted:** {len(medication_requests)} MedicationRequest objects  
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Resources

{to_markdown(medication_requests, include_json=False)}

## Source Text

```
{annotated_doc.text}
```
"""

with open("extraction_report.md", "w") as f:
    f.write(markdown_report)

print("✓ Markdown report saved to extraction_report.md")
```

## Summary

Visualization tools provide:
- **Resource tables**: Clean, readable field-value presentations
- **Interactive widgets**: Multi-format views (HTML/JSON/YAML/Schema)
- **Document summaries**: Combined document + extracted resources
- **Export formats**: JSON and Markdown reports for documentation
- **Batch operations**: Visualize multiple resources efficiently

Use these patterns to create comprehensive documentation and reports of your extraction workflows.
