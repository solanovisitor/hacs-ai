# HACS Quick Start Guide

Get HACS running in 5 minutes with working examples.

## Prerequisites

- **Python 3.11+**
- **[uv](https://github.com/astral-sh/uv)** (recommended) or pip
- **Docker** (for MCP server and database)

## Installation

### Option 1: Individual Packages (Recommended)

```bash
# Core functionality
pip install hacs-core hacs-auth hacs-models

# Add tools and utilities
pip install hacs-tools hacs-utils

# Add persistence (optional)
pip install hacs-persistence[postgresql]
```

### Option 2: Development Setup

```bash
# Clone repository
git clone https://github.com/solanovisitor/hacs-ai.git
cd hacs-ai

# Install UV (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup workspace
uv sync

# Start services (optional)
docker-compose up -d
```

## Basic Usage

### 1. Healthcare Actors

```python
from hacs_auth import Actor, ActorRole

# Create healthcare provider
physician = Actor(
    name="Dr. Sarah Chen",
    role=ActorRole.PHYSICIAN,
    organization="General Hospital"
)

print(f"Created: {physician.name} ({physician.role})")
# Output: Created: Dr. Sarah Chen (physician)
```

### 2. Patient Records

```python
from hacs_models import Patient

# Create patient with healthcare context
patient = Patient(
    full_name="John Smith",
    birth_date="1980-05-15",
    gender="male",
    agent_context={
        "chief_complaint": "Annual physical",
        "preferred_language": "english"
    }
)

print(f"Patient: {patient.full_name} ({patient.id})")
# Output: Patient: John Smith (patient-abc123)
```

### 3. Clinical Observations

```python
from hacs_models import Observation, CodeableConcept, Quantity
from hacs_models.types import ObservationStatus

# Record blood pressure
bp_observation = Observation(
    status=ObservationStatus.FINAL,
    code=CodeableConcept(text="Systolic Blood Pressure"),
    subject=f"Patient/{patient.id}",
    value_quantity=Quantity(value=120.0, unit="mmHg")
)

print(f"BP: {bp_observation.get_value_summary()}")
# Output: BP: 120.0 mmHg
```

### 4. Clinical Memory

```python
from hacs_models import MemoryBlock

# Store clinical memory
clinical_memory = MemoryBlock(
    memory_type="episodic",
    content="Patient reports feeling well. Blood pressure normal. Continue current medications.",
    importance_score=0.8,
    tags=["routine_checkup", "normal_findings"],
    context_metadata={"patient_id": patient.id}
)

print(f"Memory stored: {clinical_memory.id}")
```

## MCP Integration

### Start HACS Services

```bash
# Start PostgreSQL and MCP server
docker-compose up -d

# Verify services
curl http://localhost:8000/
```

### Use Healthcare Tools

```python
import requests

def call_hacs_tool(tool_name, arguments):
    response = requests.post("http://localhost:8000/", json={
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        },
        "id": 1
    })
    return response.json()

# Create patient via MCP
result = call_hacs_tool("create_hacs_record", {
    "resource_type": "Patient",
    "resource_data": {
        "full_name": "Maria Garcia",
        "birth_date": "1985-03-20",
        "gender": "female"
    }
})

print(f"Created patient: {result['result']['resource_id']}")
```

### Search Healthcare Records

```python
# Semantic search
search_result = call_hacs_tool("search_hacs_records", {
    "query": "diabetes patients with elevated HbA1c",
    "resource_types": ["Patient", "Observation"],
    "limit": 10
})

print(f"Found {len(search_result['result']['records'])} matching records")
```

### Memory Operations

```python
# Store clinical memory
memory_result = call_hacs_tool("create_memory", {
    "content": "Patient education provided on diabetes management and medication adherence",
    "memory_type": "episodic",
    "importance_score": 0.9,
    "tags": ["patient_education", "diabetes", "medication_adherence"]
})

# Search memories
search_memories = call_hacs_tool("search_memories", {
    "query": "diabetes education",
    "limit": 5
})

print(f"Found {len(search_memories['result']['memories'])} related memories")
```

## Complete Example

```python
from hacs_auth import Actor, ActorRole
from hacs_models import Patient, Observation, MemoryBlock, CodeableConcept, Quantity
from hacs_models.types import ObservationStatus

def complete_clinical_encounter():
    # 1. Healthcare provider
    provider = Actor(
        name="Dr. Lisa Rodriguez",
        role=ActorRole.PHYSICIAN,
        organization="Downtown Clinic"
    )
    
    # 2. Patient
    patient = Patient(
        full_name="Robert Johnson",
        birth_date="1965-11-30",
        gender="male",
        agent_context={
            "chief_complaint": "Follow-up for hypertension",
            "current_medications": ["lisinopril 10mg daily"]
        }
    )
    
    # 3. Vital signs
    vitals = [
        Observation(
            status=ObservationStatus.FINAL,
            code=CodeableConcept(text="Systolic Blood Pressure"),
            subject=f"Patient/{patient.id}",
            value_quantity=Quantity(value=138.0, unit="mmHg")
        ),
        Observation(
            status=ObservationStatus.FINAL,
            code=CodeableConcept(text="Diastolic Blood Pressure"),
            subject=f"Patient/{patient.id}",
            value_quantity=Quantity(value=86.0, unit="mmHg")
        ),
        Observation(
            status=ObservationStatus.FINAL,
            code=CodeableConcept(text="Heart Rate"),
            subject=f"Patient/{patient.id}",
            value_quantity=Quantity(value=75.0, unit="beats/min")
        )
    ]
    
    # 4. Clinical assessment
    assessment = MemoryBlock(
        memory_type="episodic",
        content=f"Patient {patient.full_name} BP well controlled on current regimen (138/86). Continue lisinopril 10mg daily. Follow-up in 3 months.",
        importance_score=0.85,
        tags=["hypertension", "medication_management", "controlled"],
        context_metadata={
            "patient_id": patient.id,
            "encounter_type": "follow_up"
        }
    )
    
    # Results
    print("✅ Clinical Encounter Complete")
    print(f"👨‍⚕️ Provider: {provider.name}")
    print(f"👤 Patient: {patient.full_name}")
    print(f"📊 Vitals recorded: {len(vitals)}")
    print(f"🧠 Assessment: {assessment.content[:60]}...")
    
    return {
        "provider": provider,
        "patient": patient,
        "vitals": vitals,
        "assessment": assessment
    }

# Run complete example
encounter = complete_clinical_encounter()
```

## Testing Your Setup

Run this validation script:

```python
def validate_hacs_setup():
    """Validate HACS installation and basic functionality."""
    print("🔍 Validating HACS Setup...")
    
    try:
        # Test imports
        from hacs_auth import Actor, ActorRole
        from hacs_models import Patient, Observation
        print("✅ Core imports successful")
        
        # Test basic model creation
        patient = Patient(
            full_name="Test Patient",
            birth_date="1980-01-01",
            gender="male"
        )
        print("✅ Patient model creation works")
        
        # Test actor creation
        actor = Actor(
            name="Test Provider",
            role=ActorRole.PHYSICIAN,
            organization="Test Hospital"
        )
        print("✅ Actor model creation works")
        
        # Test MCP server (optional)
        try:
            import requests
            response = requests.get("http://localhost:8000/", timeout=5)
            print("✅ MCP Server available")
        except:
            print("⚠️  MCP Server not available (run docker-compose up -d)")
        
        print("\n🎉 HACS setup validated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Setup validation failed: {e}")
        return False

# Run validation
validate_hacs_setup()
```

## Next Steps

- **[Healthcare Tools](healthcare-tools.md)** - Complete tool reference
- **[Basic Usage](basic-usage.md)** - Detailed patterns and examples  
- **[Integration Guide](integrations.md)** - Framework integrations
- **[Architecture](architecture/)** - Design and patterns

## Troubleshooting

### Import Errors
```bash
# Ensure packages are installed
pip list | grep hacs

# Re-install if needed
pip install --upgrade hacs-core hacs-auth hacs-models
```

### MCP Server Issues
```bash
# Check services
docker-compose ps

# View logs
docker-compose logs hacs-mcp-server

# Restart services
docker-compose restart
```

### Model Validation Errors
```python
# Check model requirements
from hacs_models import Patient
help(Patient.__init__)

# Use proper FHIR-compliant data
patient = Patient(
    full_name="Valid Name",
    birth_date="1980-01-01",  # YYYY-MM-DD format
    gender="male"             # Use valid enum values
)
```

---

**Need help?** Open an [issue](https://github.com/solanovisitor/hacs-ai/issues) or check [discussions](https://github.com/solanovisitor/hacs-ai/discussions).