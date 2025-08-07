# HACS Quick Start Guide

**Build Healthcare AI in 5 Minutes**

Install HACS packages and learn the four context engineering strategies—**Write**, **Select**, **Compress**, **Isolate**—with working healthcare AI examples.

## Prerequisites

- **Python 3.11+**
- **[uv](https://github.com/astral-sh/uv)** (recommended) or pip
- **Docker** (optional - for service add-ons: MCP server and database)

## Installation

### Option 1: Core HACS Packages (Recommended for Integration)

```bash
# Essential HACS framework
pip install hacs-core hacs-models hacs-registry

# Add tools and AI framework integrations
pip install hacs-tools hacs-utils

# Add persistence layer (optional)
pip install hacs-persistence[postgresql]
```

### Option 2: Development Setup with Service Add-ons

```bash
# Clone repository for full development environment
git clone https://github.com/solanovisitor/hacs-ai.git
cd hacs-ai

# Install UV (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup workspace with all packages
uv sync

# Start optional service add-ons
docker-compose up -d  # PostgreSQL + MCP Server
```

## Core Package Usage

The HACS framework provides healthcare-specific building blocks for AI applications. Here are the four core context engineering strategies implemented in the packages:

### 🔒 **ISOLATE Context** - Healthcare Actor Security

Create healthcare AI agents with scoped permissions and audit trails:

```python
from hacs_auth import Actor, ActorRole

# ISOLATE: Create healthcare AI with specific medical permissions
clinical_ai = Actor(
    name="Clinical Documentation AI",
    role=ActorRole.AGENT,
    organization="General Hospital",
    permissions=["patient:read", "observation:write", "memory:write"]  # Scoped permissions
)

print(f"🔒 Isolated Context: {clinical_ai.name} with {len(clinical_ai.permissions)} scoped permissions")
# Output: 🔒 Isolated Context: Clinical Documentation AI with 3 scoped permissions
```

### 🎯 **SELECT Context** - Efficient Clinical Data Selection

Choose only relevant clinical information for AI processing:

```python
from hacs_models import Patient

# Create patient with comprehensive clinical context
patient = Patient(
    full_name="John Smith",
    birth_date="1980-05-15",
    gender="male",
    agent_context={
        "chief_complaint": "Annual physical exam",
        "current_medications": ["metformin 1000mg BID"],
        "allergies": ["penicillin", "sulfa"],
        "social_history": "non-smoker, occasional alcohol",
        "family_history": ["diabetes", "hypertension"]
    }
)

# SELECT: Extract only essential clinical context for AI
essential_context = patient.model_dump(include={
    "full_name", "birth_date", "agent_context"  # Core patient data only
})

print(f"🎯 Selected Context: {len(essential_context)} core fields from complete patient record")
# Output: 🎯 Selected Context: 3 core fields from complete patient record
```

### 🗜️ **COMPRESS Context** - Medical Intelligence Summarization

Generate compressed clinical summaries for efficient LLM consumption:

```python
from hacs_models import Observation, CodeableConcept, Quantity
from hacs_models.types import ObservationStatus

# Create clinical observations
bp_obs = Observation(
    status=ObservationStatus.FINAL,
    code=CodeableConcept(text="Blood Pressure"),
    subject=f"Patient/{patient.id}",
    value_quantity=Quantity(value=138.0, unit="mmHg")
)

hba1c_obs = Observation(
    status=ObservationStatus.FINAL,
    code=CodeableConcept(text="HbA1c"),
    subject=f"Patient/{patient.id}",
    value_quantity=Quantity(value=7.1, unit="%")
)

# COMPRESS: Generate efficient clinical summaries
patient_summary = patient.get_text_summary()  # "Patient patient-abc123"
vitals_summary = f"BP: {bp_obs.get_value_summary()}, HbA1c: {hba1c_obs.get_value_summary()}"

print(f"🗜️ Compressed Context: {patient_summary} | {vitals_summary}")
# Output: 🗜️ Compressed Context: Patient patient-abc123 | BP: 138.0 mmHg, HbA1c: 7.1 %
```

### 🖊️ **WRITE Context** - Clinical Memory Generation

Actively generate and store clinical context during healthcare interactions:

```python
from hacs_models import MemoryBlock

# WRITE: Generate clinical context with structured memory
clinical_assessment = MemoryBlock(
    memory_type="episodic",
    content=f"Patient {patient.full_name}: BP elevated (138 mmHg), diabetes suboptimal (HbA1c 7.1%). Recommend: lifestyle counseling, consider medication adjustment.",
    importance_score=0.9,
    tags=["hypertension", "diabetes_suboptimal", "medication_review"],
    context_metadata={
        "patient_id": patient.id,
        "clinical_significance": "moderate_risk", 
        "context_strategies_used": ["isolate", "select", "compress", "write"],
        "follow_up_needed": True
    }
)

print(f"🖊️ Written Context: Clinical memory {clinical_assessment.id} with {clinical_assessment.importance_score} significance")
# Output: 🖊️ Written Context: Clinical memory memory-def456 with 0.9 significance
```

## Context Engineering with MCP Tools

HACS tools implement context engineering strategies through the MCP protocol:

### Start HACS Services

```bash
# Start PostgreSQL and MCP server
docker-compose up -d

# Verify services
curl http://localhost:8000/
```

### Context Engineering Tool Operations

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

# 🎯 SELECT: Create patient with selective data extraction
result = call_hacs_tool("create_hacs_record", {
    "resource_type": "Patient",
    "resource_data": patient.model_dump(exclude={
        "text", "contained", "extension"  # SELECT: Exclude unnecessary FHIR fields
    })
})

print(f"🎯 Selected Context: Patient created with essential fields only")
```

### 🔍 Context-Aware Search Operations

```python
# 🎯 SELECT + 🗜️ COMPRESS: Semantic search with compression
search_result = call_hacs_tool("search_hacs_records", {
    "query": "diabetes patients with elevated HbA1c",
    "resource_types": ["Patient", "Observation"],
    "importance_threshold": 0.7,  # SELECT high-importance only
    "output_format": "summary",   # COMPRESS results
    "limit": 10
})

print(f"🔍 Context-Aware Search: {len(search_result['result']['records'])} compressed results")
```

### 🖊️ Clinical Memory Context Operations

```python
# 🖊️ WRITE: Store clinical context with metadata
memory_result = call_hacs_tool("create_memory", {
    "content": clinical_assessment.content,
    "memory_type": "episodic", 
    "importance_score": 0.9,
    "tags": clinical_assessment.tags,
    "context_metadata": {
        **clinical_assessment.context_metadata,
        "context_engineering_applied": True
    }
})

# 🎯 SELECT: Search memories with relevance filtering
search_memories = call_hacs_tool("search_memories", {
    "query": "diabetes medication management",
    "similarity_threshold": 0.8,  # SELECT highly relevant only
    "limit": 5
})

print(f"🖊️ Context Memory: {len(search_memories['result']['memories'])} relevant memories")
```

## Complete Context Engineering Example

Healthcare AI workflow demonstrating all four context engineering strategies:

```python
from hacs_auth import Actor, ActorRole
from hacs_models import Patient, Observation, MemoryBlock, CodeableConcept, Quantity
from hacs_models.types import ObservationStatus

def healthcare_context_engineering_demo():
    """Demonstrate all four context engineering strategies in healthcare AI"""
    
    # 🔒 ISOLATE: Create healthcare AI with scoped permissions
    clinical_ai = Actor(
        name="Clinical Context AI",
        role=ActorRole.AGENT,
        organization="Context Engineering Hospital",
        permissions=["patient:read", "observation:write", "memory:write", "analytics:clinical"]
    )
    
    # Create patient with comprehensive clinical data
    patient = Patient(
        full_name="Sarah Martinez",
        birth_date="1975-08-20",
        gender="female",
        agent_context={
            "chief_complaint": "Diabetes follow-up with family history concerns",
            "current_medications": ["metformin 1000mg BID", "lisinopril 5mg daily"],
            "allergies": ["penicillin", "shellfish"],
            "social_history": "non-smoker, moderate exercise, family support",
            "family_history": ["diabetes", "cardiovascular_disease", "stroke"],
            "insurance": "Medicare Advantage",
            "preferred_language": "bilingual_english_spanish"
        }
    )
    
    # Clinical observations with full context
    observations = [
        Observation(
            status=ObservationStatus.FINAL,
            code=CodeableConcept(text="Blood Pressure"),
            subject=f"Patient/{patient.id}",
            value_quantity=Quantity(value=142.0, unit="mmHg")
        ),
        Observation(
            status=ObservationStatus.FINAL,
            code=CodeableConcept(text="HbA1c"),
            subject=f"Patient/{patient.id}",
            value_quantity=Quantity(value=7.8, unit="%")
        ),
        Observation(
            status=ObservationStatus.FINAL,
            code=CodeableConcept(text="BMI"),
            subject=f"Patient/{patient.id}",
            value_quantity=Quantity(value=28.5, unit="kg/m2")
        )
    ]
    
    # 🎯 SELECT: Extract essential clinical context only
    selected_context = {
        "patient_core": patient.model_dump(include={
            "full_name", "birth_date", "agent_context"
        }),
        "recent_vitals": [
            obs.model_dump(include={"status", "code", "value_quantity"})
            for obs in observations
        ],
        "risk_factors": patient.agent_context.get("family_history", [])
    }
    
    # 🗜️ COMPRESS: Generate compressed clinical summaries
    patient_summary = patient.get_text_summary()
    vitals_summary = " | ".join([obs.get_value_summary() for obs in observations])
    risk_summary = f"Family Hx: {', '.join(selected_context['risk_factors'])}"
    
    compressed_clinical_context = {
        "patient": patient_summary,
        "vitals": vitals_summary,
        "risks": risk_summary,
        "context_size": len(str(selected_context))  # Track compression efficiency
    }
    
    # 🖊️ WRITE: Generate clinical context through structured memory
    clinical_assessment = MemoryBlock(
        memory_type="episodic",
        content=f"""Patient {patient.full_name}: Diabetes suboptimal control (HbA1c 7.8%, target <7%). 
        Hypertension on treatment (BP 142, on lisinopril 5mg). 
        BMI elevated (28.5). Strong family history DM/CVD. 
        Recommendations: Increase metformin, consider BP med optimization, 
        lifestyle counseling, diabetes education. Follow-up 8 weeks.""",
        importance_score=0.95,
        tags=["diabetes_suboptimal", "hypertension", "obesity", "family_risk", "medication_optimization"],
        context_metadata={
            "patient_id": patient.id,
            "provider_id": clinical_ai.id,
            "context_strategies_applied": ["isolate", "select", "compress", "write"],
            "clinical_complexity": "high",
            "risk_stratification": "moderate_high",
            "follow_up_interval": "8_weeks",
            "context_efficiency_ratio": 0.25  # Compressed to 25% of original
        }
    )
    
    # Results demonstrating context engineering
    print("🏥 Healthcare Context Engineering Demo Complete")
    print(f"🔒 ISOLATE: {clinical_ai.name} with {len(clinical_ai.permissions)} scoped permissions")
    print(f"🎯 SELECT: {len(selected_context)} context categories from comprehensive patient data")
    print(f"🗜️ COMPRESS: {compressed_clinical_context['patient']} | {compressed_clinical_context['vitals']}")
    print(f"🖊️ WRITE: Clinical memory {clinical_assessment.id} with {clinical_assessment.importance_score} significance")
    print(f"⚡ Context Efficiency: {clinical_assessment.context_metadata['context_efficiency_ratio']*100}% of original size")
    print(f"🎯 Next Actions: {len(clinical_assessment.tags)} clinical priorities identified")
    
    return {
        "clinical_ai": clinical_ai,
        "patient": patient,
        "observations": observations,
        "selected_context": selected_context,
        "compressed_context": compressed_clinical_context,
        "clinical_assessment": clinical_assessment
    }

# Run complete context engineering demo
context_demo = healthcare_context_engineering_demo()

# Show context engineering metrics
print(f"\n📊 Context Engineering Metrics:")
print(f"Original patient data: {len(str(context_demo['patient']))} characters")
print(f"Selected context: {len(str(context_demo['selected_context']))} characters")
print(f"Compressed context: {len(str(context_demo['compressed_context']))} characters")
print(f"Clinical memory generated: {len(context_demo['clinical_assessment'].content)} characters")
print(f"Compression ratio: {len(str(context_demo['compressed_context'])) / len(str(context_demo['patient'])):.2%}")
```

## Testing Context Engineering Setup

Validate your HACS context engineering installation:

```python
def validate_context_engineering_setup():
    """Validate HACS context engineering capabilities."""
    print("🔍 Validating HACS Context Engineering Setup...")
    
    try:
        # Test core imports
        from hacs_auth import Actor, ActorRole
        from hacs_models import Patient, Observation, MemoryBlock
        print("✅ Core context engineering imports successful")
        
        # Test 🔒 ISOLATE: Actor creation with permissions
        test_ai = Actor(
            name="Test Context AI",
            role=ActorRole.AGENT,
            organization="Test Hospital",
            permissions=["test:read", "test:write"]
        )
        print(f"✅ 🔒 ISOLATE: Actor with {len(test_ai.permissions)} scoped permissions")
        
        # Test healthcare models with context
        patient = Patient(
            full_name="Test Patient",
            birth_date="1980-01-01",
            gender="male",
            agent_context={"test_context": "context_data"}
        )
        print("✅ Healthcare models with agent context")
        
        # Test 🎯 SELECT: Efficient data selection
        selected_data = patient.model_dump(include={
            "full_name", "birth_date", "agent_context"
        })
        print(f"✅ 🎯 SELECT: Extracted {len(selected_data)} essential fields")
        
        # Test 🗜️ COMPRESS: Context compression
        patient_summary = patient.get_text_summary()
        print(f"✅ 🗜️ COMPRESS: Patient summary generated: {patient_summary}")
        
        # Test 🖊️ WRITE: Memory creation with context
        test_memory = MemoryBlock(
            memory_type="episodic",
            content="Test clinical context generated successfully",
            importance_score=0.8,
            tags=["test", "context_engineering"],
            context_metadata={"test_validation": True}
        )
        print(f"✅ 🖊️ WRITE: Clinical memory created with context metadata")
        
        # Test MCP server (optional)
        try:
            import requests
            response = requests.get("http://localhost:8000/", timeout=3)
            print("✅ MCP Context Engineering Tools available")
        except:
            print("⚠️  MCP Server not available (optional - run docker-compose up -d)")
        
        print("\n🎉 HACS Context Engineering validated successfully!")
        print("🏥 Ready for healthcare AI development with context engineering!")
        return True
        
    except Exception as e:
        print(f"❌ Context engineering validation failed: {e}")
        return False

# Run context engineering validation
validate_context_engineering_setup()
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