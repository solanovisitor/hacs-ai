# HACS Resource Gallery

Quick visual previews for common HACS resources. These render best in notebooks; otherwise the functions return raw HTML strings you can embed.

## Prereq

```bash
uv pip install -U hacs-utils
```

## Patient

```python
from hacs_models import Patient
from hacs_utils.visualization import resource_to_markdown
patient = Patient(full_name="Jane Doe", birth_date="1990-01-01", gender="female")
print(resource_to_markdown(patient, include_json=False))
```

### Patient

| Field | Value |
|---|---|
| resource_type | Patient |
| id | patient-… |
| status | active |
| created_at | … |
| updated_at | … |

## Observation

```python
from hacs_models import Observation, CodeableConcept, Quantity
from hacs_models.types import ObservationStatus
from hacs_utils.visualization import resource_to_markdown
obs = Observation(status=ObservationStatus.FINAL, code=CodeableConcept(text="Blood Pressure"), value_quantity=Quantity(value=128.0, unit="mmHg"), subject="Patient/p1")
print(resource_to_markdown(obs, include_json=False))
```

### Observation

| Field | Value |
|---|---|
| resource_type | Observation |
| id | observation-… |
| status | final |
| subject | Patient/p1 |
| created_at | … |
| updated_at | … |
| code.text | Blood Pressure |

## DiagnosticReport

```python
from hacs_models import DiagnosticReport, CodeableConcept
from hacs_utils.visualization import resource_to_markdown
report = DiagnosticReport(status="final", code=CodeableConcept(text="Chest X-Ray"), subject="Patient/p1")
print(resource_to_markdown(report, include_json=False))
```

### DiagnosticReport

| Field | Value |
|---|---|
| resource_type | DiagnosticReport |
| id | diagnosticreport-… |
| status | final |
| subject | Patient/p1 |
| created_at | … |
| updated_at | … |
| code.text | Chest X-Ray |

## Annotated Document

```python
from hacs_models import AnnotatedDocument
from hacs_utils.visualization import resource_to_markdown
doc = AnnotatedDocument(text="BP 128/82, HR 72", document_id="vital_signs_001")
print(resource_to_markdown(doc, include_json=False))
```

### AnnotatedDocument

| Field | Value |
|---|---|
| resource_type | AnnotatedDocument |
