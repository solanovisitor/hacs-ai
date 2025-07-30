# HACS Registry

**Versioned healthcare model and template management**

Domain models for managing versioned healthcare AI resources, clinical templates, and workflow definitions.

## 🏥 **Healthcare Registry**

### **Resource Definitions**
Versioned healthcare resource schemas:
- **Patient Resources** - Custom patient schemas with validation
- **Clinical Resources** - Observation, encounter, diagnostic resources
- **Workflow Resources** - Clinical process definitions

### **Clinical Templates**
Healthcare-specific templates:
- **Assessment Templates** - Structured clinical assessments
- **Care Plans** - Treatment and care workflow templates
- **Documentation Templates** - Clinical note and report formats

### **Knowledge Base**
Versioned clinical knowledge:
- **Clinical Guidelines** - Treatment protocols and standards
- **Evidence Base** - Research findings and best practices
- **Decision Support** - Clinical reasoning frameworks

## 📦 **Installation**

```bash
pip install hacs-registry
```

## 🚀 **Quick Start**

```python
from hacs_registry import ResourceDefinition, TemplateDefinition

# Custom patient resource with additional fields
patient_resource = ResourceDefinition(
    name="ExtendedPatient",
    version="1.0.0",
    description="Patient resource with custom clinical fields",
    schema_definition={
        "type": "object",
        "properties": {
            "full_name": {"type": "string"},
            "primary_diagnosis": {"type": "string"},
            "risk_factors": {"type": "array", "items": {"type": "string"}}
        }
    },
    category="clinical",
    tags=["patient", "extended"]
)

# Clinical assessment template
assessment_template = TemplateDefinition(
    name="cardiac_assessment",
    version="2.1.0",
    description="Comprehensive cardiac assessment template",
    template_content={
        "sections": ["history", "examination", "diagnostics", "plan"],
        "required_fields": ["heart_rate", "blood_pressure", "ecg_findings"]
    },
    category="assessment",
    tags=["cardiology", "assessment"]
)

# Publish for use
patient_resource.publish()
assessment_template.publish()
```

## 🎯 **Key Features**

- **Semantic Versioning** - Standard version management (1.0.0, 1.1.0, 2.0.0)
- **Lifecycle Management** - Draft → Published → Deprecated status flow
- **Clinical Categorization** - Healthcare-specific tagging and classification
- **Template System** - Reusable clinical workflow templates
- **Validation Rules** - Healthcare data validation schemas

## 🏗️ **Registry Management**

```python
# Version management
resource.update_version("1.1.0")  # Increment version
resource.deprecate()              # Mark as deprecated
resource.get_version_history()    # View all versions

# Clinical categorization
resource.add_tag("cardiology")
resource.set_category("diagnostic")
resource.filter_by_tags(["patient", "cardiology"])

# Template usage
template.instantiate(patient_data)  # Create instance from template
template.validate_instance(data)    # Validate against template
```

## 🔗 **Integration**

HACS Registry integrates with:
- **MCP Tools** - Resource discovery and schema generation
- **Clinical Workflows** - Template-based clinical processes
- **HACS Core** - Base healthcare resources and validation
- **Version Control** - Semantic versioning for clinical assets

## 📊 **Usage Patterns**

### **Clinical Resource Development**
```python
# Define custom clinical resource
diabetes_resource = ResourceDefinition(
    name="DiabetesPatient",
    version="1.0.0",
    schema_definition={
        "properties": {
            "a1c_level": {"type": "number", "minimum": 4.0, "maximum": 14.0},
            "medication_regimen": {"type": "string"},
            "last_eye_exam": {"type": "string", "format": "date"}
        }
    },
    category="specialized_patient"
)
```

### **Template Management**
```python
# Create reusable clinical template
intake_template = TemplateDefinition(
    name="patient_intake",
    version="1.0.0",
    template_content={
        "workflow": ["registration", "triage", "assessment", "assignment"],
        "required_data": ["demographics", "insurance", "chief_complaint"],
        "optional_data": ["emergency_contact", "medical_history"]
    }
)
```

## 📄 **License**

Apache-2.0 License - see [LICENSE](../../LICENSE) for details.