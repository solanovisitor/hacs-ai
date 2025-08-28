# Facade-Based Extraction Guide

## Overview

HACS facades provide a structured approach to extraction by focusing on specific subsets of fields within models. Instead of extracting entire complex models at once, facades allow you to extract focused, well-defined portions that match common clinical workflows.

## What are Facades?

A facade is a predefined subset of fields with:

- **Focused fields**: Only the fields relevant to a specific use case
- **Custom hints**: Field-specific guidance for LLMs  
- **Validation rules**: Required fields and validation logic
- **Post-processing**: Optional transformations (e.g., terminology coding)

> Note
> Synthetic fallback facades (like implicit "core" or "extractable") were removed. Always use explicitly defined facades for each model (e.g., `Patient.info`, `Encounter.basic`). For quick views in code, `resource.to_facade("extractable")` still returns the extractable field view but is not an extraction facade.

## Available Facades

### Patient Facades

**Patient.info** - Core demographics
```python
fields = ["full_name", "gender", "age", "birth_date", "anonymous"]
required = ["anonymous"]
```

**Patient.address** - Address information  
```python
fields = ["address", "address_text", "anonymous"]
required = ["anonymous"]
```

**Patient.telecom** - Contact information
```python
fields = ["telecom", "phone", "email", "anonymous"] 
required = ["anonymous"]
```

### Condition Facades

**Condition.summary** - Core condition identification
```python
fields = ["code", "clinical_status", "verification_status", "category", "severity"]
required = ["code"]
```

**Condition.timing** - Onset and resolution timing
```python
fields = ["onset_date_time", "onset_age", "onset_period", "onset_string", "abatement_date_time", "abatement_age", "abatement_string"]
required = []
```

### Observation Facades

**Observation.core** - Essential measurements
```python
fields = ["code", "value_quantity", "value_string", "effective_date_time", "status", "interpretation"]
required = ["code"]
```

**Observation.components** - Multi-component observations (e.g., blood pressure)
```python
fields = ["component", "value_quantity", "value_string"]
many = True, max_items = 5
```

**Observation.method_body_site** - Method and bodySite hints
```python
fields = ["method", "body_site", "interpretation"]
required = []
```

## Basic Usage

### Using the Generic API

```python
from hacs_utils.extraction.api import extract_facade
from hacs_models import Patient
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini")

# Extract patient demographics only
patient = await extract_facade(
    llm_provider=llm,
    model_cls=Patient,
    facade_key="info", 
    source_text="João Silva, masculino, 45 anos, hipertenso"
)

print(patient.full_name)  # "João Silva"
print(patient.gender)     # "male"  
print(patient.age)        # 45

# Actual output from real LLM extraction:
# Name: João Silva
# Gender: male
# Age: 45
# Anonymous: False
```

### Using Convenience Functions

```python
from hacs_utils.extraction.api import extract_patient_info

# This uses the Patient.info facade internally
patient = await extract_patient_info(
    llm_provider=llm,
    source_text="Maria Santos, 32 anos, feminino"
)
```

## Advanced Usage

### Overriding Facade Parameters

```python
# Override required fields and hints
patient = await extract_facade(
    llm_provider=llm,
    model_cls=Patient,
    facade_key="info",
    source_text="Paciente de 67 anos",
    overrides={
        "required_fields": ["age", "anonymous"],
        "field_hints": {
            "age": "SEMPRE extraia a idade quando mencionada",
            "anonymous": "Defina como true se não houver nome"
        }
    }
)
```

### Iterative Validation

```python
# Increase validation rounds for complex text
condition = await extract_facade(
    llm_provider=llm,
    model_cls=Condition,
    facade_key="summary",
    source_text="Paciente apresenta quadro de hipertensão arterial não controlada",
    validation_rounds=3  # More attempts for better accuracy
)
```

### Debug Mode

```python
# Enable debug output
patient = await extract_facade(
    llm_provider=llm,
    model_cls=Patient,
    facade_key="info",
    source_text="Dr. Carlos Mendes, 50 anos",
    debug_dir="./debug",
    debug_prefix="patient_extraction"
)
# Creates files: patient_extraction_attempt_1.txt, patient_extraction_result.json, etc.
```

## Creating Custom Facades

### Define Facades in Your Model

```python
from hacs_models.base_resource import DomainResource, FacadeSpec

class MyModel(DomainResource):
    # ... model fields ...
    
    @classmethod
    def get_facades(cls) -> dict[str, FacadeSpec]:
        return {
            "basic": FacadeSpec(
                fields=["name", "code", "status"],
                required_fields=["name"],
                field_hints={
                    "name": "Nome em português",
                    "code": "Código se disponível", 
                    "status": "Status atual (active/inactive)"
                },
                description="Basic identification",
                strict=False
            ),
            
            "detailed": FacadeSpec(
                fields=["name", "code", "description", "notes", "metadata"],
                required_fields=["name", "description"],
                field_hints={
                    "description": "Descrição detalhada obrigatória",
                    "notes": "Notas clínicas adicionais"
                },
                description="Detailed information extraction",
                strict=True,  # Stricter validation
                many=False
            )
        }
```

### Using Custom Facades

```python
result = await extract_model_facade(
    llm_provider=llm,
    model_cls=MyModel,
    facade_key="basic",
    source_text="Nome: Sistema XYZ, status ativo"
)
```

## Best Practices

### 1. Choose the Right Facade

- Use **narrow facades** (e.g., `Patient.info`) for focused extraction
- Use **broad facades** when you need comprehensive data
- Combine multiple facade calls for complex documents

### 2. Compose with validation and persistence

```python
from hacs_utils.extraction.api import extract_facade
from hacs_tools.domains.modeling import validate_resource
from hacs_tools.domains.database import save_resource
from hacs_models import Patient

patient = await extract_facade(llm, Patient, "info", source_text=text)
vres = validate_resource(patient.model_dump())
if not vres.success:
    # Use vres.data.get('plan') for actionable steps
    raise RuntimeError(vres.message)

sres = await save_resource(vres.data["resource"])  # Persist after validation
```

### 2. Iterative Extraction for Quality

```python
# First pass: basic info
patient = await extract_facade(llm, Patient, "info", text)

# Second pass: address if mentioned
if "endereço" in text.lower():
    address_patient = await extract_facade(llm, Patient, "address", text)
    # Merge results as needed
```

### 3. Field Hints for Complex Cases

```python
# Custom hints for domain-specific terminology
overrides = {
    "field_hints": {
        "code": "Procure por códigos CID-10 ou terminologia médica específica",
        "severity": "Classifique como: leve, moderada, grave"
    }
}
```

### 4. Post-Processing with Terminology

```python
def add_umls_coding(resource):
    """Add UMLS coding to CodeableConcept fields"""
    # Custom terminology enhancement
    return enhanced_resource

custom_facade = FacadeSpec(
    fields=["code", "status"],
    post_process=add_umls_coding  # Applied after extraction
)
```

## Error Handling

```python
try:
    result = await extract_facade(llm, Patient, "info", text)
except ValueError as e:
    if "not found" in str(e):
        print(f"Facade not available: {e}")
        # Fall back to available facades
        available = Patient.list_facade_keys()
        print(f"Available: {available}")
        # Actual available facades: ['info', 'address', 'telecom', 'identifiers', 'contacts']
except Exception as e:
    print(f"Extraction failed: {e}")
```

## Real Extraction Results

Based on actual LLM calls with `gpt-4o-mini`:

```python
# Patient info facade extraction
source_text = "João Silva, masculino, 45 anos, hipertenso"
patient = await extract_facade(llm, Patient, "info", source_text)
# ✅ Results: name="João Silva", gender="male", age=45, anonymous=False

# Condition summary facade extraction
source_text = "Paciente apresenta quadro de hipertensão arterial não controlada"  
condition = await extract_facade(llm, Condition, "summary", source_text)
# ✅ Results: code="hipertensão arterial não controlada", 
#            clinical_status="active", verification_status="confirmed"
```

## Performance Tips

### 1. Facade Selection

- Smaller facades = faster extraction
- Fewer required fields = higher success rate
- Use `many=True` facades for lists of similar items

### 2. Batch Processing

```python
# Process multiple texts with the same facade
texts = ["Paciente 1...", "Paciente 2...", "Paciente 3..."]

results = []
for text in texts:
    result = await extract_model_facade(llm, Patient, "info", text)
    results.append(result)
```

### 3. Caching LLM Providers

```python
# Reuse LLM provider across calls
llm = ChatOpenAI(model="gpt-4o-mini")

for facade_key in ["info", "address", "telecom"]:
    result = await extract_model_facade(llm, Patient, facade_key, text)
    # Same provider, different facades
```

## Migration from Legacy Extraction

### Before (Manual Field Selection)
```python
result = await extract(
    llm, 
    prompt="Extract patient name and age",
    output_model=Patient,
    many=False,
    strict=False,
    # Manual field management
)
```

### After (Facade-Based)
```python
result = await extract_facade(
    llm, 
    Patient, 
    "info",  # Predefined field set + hints
    source_text=text
)
```

## Available Models with Facades

| Model | Facades | Description |
|-------|---------|-------------|
| **Patient** | `info`, `address`, `telecom`, `identifiers`, `contacts` | Demographics and contact info |
| **Condition** | `summary`, `timing`, `body_site`, `evidence` | Clinical conditions and diagnoses |  
| **Observation** | `core`, `components`, `method_body_site` | Measurements and findings |
| **MedicationRequest** | `medication`, `dosage`, `intent`, `authorship` | Prescriptions and orders |
| **Procedure** | `core`, `body_site`, `outcome` | Medical procedures |
| **Encounter** | `basic`, `timing`, `participants`, `clinical`, `complete` | Visits and episodes |
| **Organization** | `info`, `contact`, `hierarchy`, `identity` | Provider organizations |

More models with facades coming soon: DiagnosticReport, ServiceRequest, Goal, CarePlan, etc.

## Troubleshooting

### Common Issues

**Empty Results**
- Check if facade key exists: `Model.list_facade_keys()`
- Verify required fields can be extracted from text
- Try less strict facades first

**Validation Errors**  
- Increase `validation_rounds` parameter
- Use `strict=False` for relaxed validation
- Check field hints match your input text language

**Wrong Facade Selection**
- List available facades: `Model.get_facades()`  
- Check facade field lists and requirements
- Use more specific facades for better results

### Debug Information

```python
# Get facade details
spec = Patient.get_facade_spec("info")
print(f"Fields: {spec.fields}")
print(f"Required: {spec.required_fields}")
print(f"Hints: {spec.field_hints}")

# Check all facades for a model
facades = Patient.get_facades()
for key, spec in facades.items():
    print(f"{key}: {spec.description}")
```
