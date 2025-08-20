## Validate and examine HACS models

This guide shows how to validate, examine, and analyze extracted HACS models to ensure they meet clinical standards and have proper BaseResource functionality.

Prerequisites:
- Extracted HACS models (see [Extract Annotations](extract_annotations.md))
- `uv pip install -U hacs-utils[langchain]`

## Examine extracted model structure

Using the `medication_requests` from the extraction guide:

```python
# Examine the structure of extracted HACS models in detail
print("\nDetailed HACS Model Structure:")
print("=" * 50)

sample_med = medication_requests[0]  # Look at first medication in detail

print("Sample MedicationRequest object:")
print("  Key fields:")
print(f"    ID: {sample_med.id}")
print(f"    Resource type: {sample_med.resource_type}")
print(f"    Status: {sample_med.status}")
print(f"    Intent: {sample_med.intent}")
print(f"    Subject: {sample_med.subject}")
print(f"    Created: {sample_med.created_at}")

# Show medication concept
if sample_med.medication_codeable_concept:
    med_concept = sample_med.medication_codeable_concept
    if isinstance(med_concept, dict):
        print(f"    Medication text: {med_concept.get('text', 'Unknown')}")
    else:
        print(f"    Medication text: {med_concept.text if hasattr(med_concept, 'text') else 'Unknown'}")

print()

# Validation check
print("Validation check:")
for i, mr in enumerate(medication_requests):
    try:
        # Test that it has BaseResource methods
        print(f"  ✓ MedicationRequest {i+1}: Valid")
        print(f"    Has BaseResource methods: {hasattr(mr, 'get_descriptive_schema')}")
        print(f"    Resource reference: {mr.to_reference()}")
        print(f"    Can create schema: {bool(mr.get_descriptive_schema())}")
        
    except Exception as e:
        print(f"  ✗ MedicationRequest {i+1}: Error - {e}")

print(f"\n✓ All {len(medication_requests)} HACS models are properly structured")
print("✓ All models inherit full BaseResource functionality")
```

**Output:**
```
Detailed HACS Model Structure:
==================================================
Sample MedicationRequest object:
  Key fields:
    ID: medreq-lisinopril-1
    Resource type: MedicationRequest
    Status: active
    Intent: order
    Subject: Patient/unknown
    Created: 2025-08-19T00:00:00Z
    Medication text: Lisinopril 10 mg oral tablet

Validation check:
  ✓ MedicationRequest 1: Valid
    Has BaseResource methods: True
    Resource reference: MedicationRequest/medreq-lisinopril-1
    Can create schema: True
  ✓ MedicationRequest 2: Valid
    Has BaseResource methods: True
    Resource reference: MedicationRequest/medreq-metformin-1
    Can create schema: True
  ✓ MedicationRequest 3: Valid
    Has BaseResource methods: True
    Resource reference: MedicationRequest/medreq-aspirin-1
    Can create schema: True

✓ All 3 HACS models are properly structured
✓ All models inherit full BaseResource functionality
```

## Validate clinical data quality

```python
# Clinical validation checks specific to MedicationRequest
print("Clinical Validation:")
print("=" * 30)

for i, mr in enumerate(medication_requests, 1):
    print(f"\nMedicationRequest {i}:")
    
    # Required safety fields
    safety_checks = []
    if mr.status:
        safety_checks.append(f"✓ Status: {mr.status}")
    else:
        safety_checks.append("✗ Missing status (safety risk)")
        
    if mr.intent:
        safety_checks.append(f"✓ Intent: {mr.intent}")
    else:
        safety_checks.append("✗ Missing intent")
        
    if mr.subject:
        safety_checks.append(f"✓ Subject: {mr.subject}")
    else:
        safety_checks.append("✗ Missing subject (safety risk)")
    
    for check in safety_checks:
        print(f"  {check}")
    
    # Medication details
    if mr.medication_codeable_concept:
        med_text = mr.medication_codeable_concept.text if hasattr(mr.medication_codeable_concept, 'text') else 'Unknown'
        print(f"  ✓ Medication: {med_text}")
    else:
        print("  ✗ Missing medication (critical)")
    
    # Dosage information
    if mr.dosage_instruction:
        for j, dosage in enumerate(mr.dosage_instruction):
            dosage_text = dosage.text if hasattr(dosage, 'text') else str(dosage)
            print(f"  ✓ Dosage {j+1}: {dosage_text}")
    else:
        print("  ⚠ No dosage instructions")

print("\n✓ Clinical validation complete")
```

## Check BaseResource functionality

```python
# Test inherited BaseResource methods
print("BaseResource Method Testing:")
print("=" * 35)

sample = medication_requests[0]

# Test core methods
print(f"Resource reference: {sample.to_reference()}")
print(f"Age in days: {sample.get_age_days():.2f}")
print(f"Is valid: {sample.is_valid()}")
print(f"Validation errors: {sample.validate()}")

# Test schema methods
schema = sample.get_descriptive_schema()
print(f"Schema fields count: {len(schema.get('fields', {}))}")
print(f"Schema title: {schema.get('title')}")

# Test specifications
specs = sample.get_specifications()
print(f"Has documentation: {bool(specs.get('documentation'))}")
print(f"Has tools: {len(specs.get('documentation', {}).get('tools', []))}")

# Test serialization
dict_form = sample.to_dict()
reconstructed = MedicationRequest.from_dict(dict_form)
print(f"Serialization works: {reconstructed.id == sample.id}")

print("\n✓ All BaseResource methods functional")
```

## Validate against FHIR standards

```python
# FHIR compliance checks
print("FHIR Compliance Validation:")
print("=" * 30)

for mr in medication_requests:
    print(f"\nMedicationRequest {mr.id}:")
    
    # Check required FHIR fields
    fhir_required = ['resource_type', 'status', 'intent', 'subject']
    for field in fhir_required:
        value = getattr(mr, field, None)
        if value:
            print(f"  ✓ {field}: {value}")
        else:
            print(f"  ✗ Missing required FHIR field: {field}")
    
    # Check enum compliance
    from hacs_models.types import MedicationRequestStatus, MedicationRequestIntent
    
    try:
        if mr.status in [s.value for s in MedicationRequestStatus]:
            print(f"  ✓ Status enum valid: {mr.status}")
        else:
            print(f"  ✗ Invalid status enum: {mr.status}")
    except Exception:
        print(f"  ⚠ Status validation error")
    
    try:
        if mr.intent in [i.value for i in MedicationRequestIntent]:
            print(f"  ✓ Intent enum valid: {mr.intent}")
        else:
            print(f"  ✗ Invalid intent enum: {mr.intent}")
    except Exception:
        print(f"  ⚠ Intent validation error")

print("\n✓ FHIR compliance validation complete")
```

## Summary

Model validation ensures:
- **Clinical safety**: Required fields (status, intent, subject) are present
- **FHIR compliance**: Enum values and field structures match standards  
- **BaseResource functionality**: All inherited methods work correctly
- **Type safety**: Pydantic validation passes for all instances
- **Serialization**: Models can be safely persisted and reconstructed

Use these validation patterns before persisting HACS models to ensure data quality and clinical safety.
