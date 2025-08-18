# Extend and customize Resources

Create subsets with `pick()`, add extensions, and generate references.

```python
from hacs_models import Patient
from hacs_tools.domains.modeling import add_extension_to_resource, make_reference

patient = Patient(full_name="Jane Doe", birth_date="1990-01-01", gender="female")

# Always visualize created records
from hacs_utils.visualization import resource_to_markdown
print("Patient record:")
print(resource_to_markdown(patient, include_json=False))

# Add an extension
res = add_extension_to_resource(patient.model_dump(), url="http://example.org/consent", value={"consent":"granted"})
print("extended has_extension:", True if (res.data or {}).get("resource", {}).get("extension") else False)

# Make a FHIR-style reference string
ref = make_reference(resource=patient.model_dump())
print("reference:", ref.data.get("reference"))

# Lightweight subset model for prompts/APIs using pick()
Demographics = Patient.pick("full_name", "birth_date")
subset = Demographics(resource_type="Patient", full_name=patient.full_name, birth_date=patient.birth_date)
print("subset keys:", list(subset.model_dump().keys()))
```

```
Patient record:
#### Patient

| Field | Value |
|---|---|
| resource_type | Patient |
| id | patient-da4c4a85 |
| status | active |
| full_name | Jane Doe |
| gender | female |
| birth_date | 1990-01-01 |
| created_at | 2025-08-18T22:39:15.087461Z |
| updated_at | 2025-08-18T22:39:15.087462Z |

extended has_extension: False
reference: Patient/patient-da4c4a85
subset keys: ['id', 'created_at', 'birth_date', 'full_name', 'updated_at', 'resource_type']
```
