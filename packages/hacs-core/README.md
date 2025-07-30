# HACS Core

**Foundation models for Healthcare Agent Communication Standard**

Core Pydantic models and base classes that define the healthcare AI communication protocol.

## 🏥 **Healthcare Models**

Essential healthcare data structures optimized for AI agent communication:

- **Patient** - Demographics, contact info, clinical context
- **Observation** - Clinical measurements, lab results, vital signs
- **Encounter** - Healthcare visits, episodes of care
- **Actor** - Healthcare providers with role-based permissions
- **MemoryBlock** - Structured memory for AI clinical reasoning
- **Evidence** - Clinical guidelines, research, decision support

## 🎯 **Key Features**

- **FHIR Compatible** - Full alignment with healthcare standards
- **AI Optimized** - Structured for LLM processing and tool calling
- **Validation Built-in** - Healthcare-specific validation rules
- **Actor Security** - Role-based access control for clinical data
- **Memory System** - Episodic, procedural, and executive memory types

## 📦 **Installation**

```bash
pip install hacs-core
```

## 🚀 **Quick Start**

```python
from hacs_core import Patient, Observation, Actor, MemoryBlock

# Healthcare provider
physician = Actor(
    name="Dr. Sarah Chen",
    role="PHYSICIAN",
    organization="Mount Sinai Health System"
)

# Patient record
patient = Patient(
    full_name="Maria Rodriguez",
    birth_date="1985-03-15",
    gender="female",
    active=True
)

# Clinical observation
bp_reading = Observation(
    code_text="Blood Pressure",
    value="145/90",
    unit="mmHg",
    status="final",
    patient_id=patient.id
)

# Clinical memory
memory = MemoryBlock(
    content="Patient presents with elevated BP, discussed lifestyle modifications",
    memory_type="episodic",
    importance_score=0.8
)
```

## 🔗 **Integration**

HACS Core models work seamlessly with:
- **MCP Tools** - 25+ healthcare tools via Model Context Protocol
- **LangGraph** - AI agent workflows with clinical memory
- **PostgreSQL** - Persistent storage with pgvector
- **FHIR Systems** - Healthcare standards compliance

## 📄 **License**

Apache-2.0 License - see [LICENSE](../../LICENSE) for details.
