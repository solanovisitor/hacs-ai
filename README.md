# HACS: Healthcare Agent Communication Standard

<div align="center">

![License](https://img.shields.io/github/license/solanovisitor/hacs-ai)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)

**🏥 Production-ready framework for healthcare AI agents**

*FHIR-compliant • Memory-enabled • Protocol-first*

[**🚀 Quick Start**](#quick-start) • [**📚 Examples**](#examples) • [**🛠️ Tools**](#healthcare-tools) • [**📖 Docs**](docs/)

</div>

---

## What is HACS?

HACS enables healthcare AI systems with **structured memory**, **clinical reasoning**, and **FHIR compliance**. Built with protocol-first architecture, HACS provides **37+ healthcare tools** across 9 domains for patient data, clinical workflows, and evidence-based reasoning.

### Why HACS?

- **✅ Healthcare-First**: FHIR-compliant models designed for clinical environments
- **✅ Memory-Enabled**: Episodic, procedural & executive memory for AI agents  
- **✅ Protocol-Based**: Clean abstractions for maximum framework flexibility
- **✅ Production-Ready**: Actor-based security with audit trails
- **✅ MCP Integration**: 37+ healthcare tools via Model Context Protocol

## Quick Start

### Installation

```bash
# Install HACS packages
pip install hacs-core hacs-auth hacs-tools hacs-utils

# Or install specific packages
pip install hacs-models hacs-persistence hacs-registry
```

### Basic Usage

```python
from hacs_auth import Actor, ActorRole
from hacs_models import Patient, Observation, CodeableConcept, Quantity
from hacs_models.types import ObservationStatus

# Create healthcare provider
physician = Actor(
    name="Dr. Sarah Chen",
    role=ActorRole.PHYSICIAN,
    organization="General Hospital"
)

# Create patient record
patient = Patient(
    full_name="John Doe",
    birth_date="1980-01-15",
    gender="male"
)

# Record clinical observation
bp_observation = Observation(
    status=ObservationStatus.FINAL,
    code=CodeableConcept(text="Systolic Blood Pressure"),
    subject=f"Patient/{patient.id}",
    value_quantity=Quantity(value=145.0, unit="mmHg")
)

print(f"Patient: {patient.full_name}")
print(f"Observation: {bp_observation.get_value_summary()}")
```

### With MCP Tools

```bash
# Start HACS services
docker-compose up -d

# Use healthcare tools via HTTP
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call", 
    "params": {
      "name": "create_hacs_record",
      "arguments": {
        "resource_type": "Patient",
        "resource_data": {
          "full_name": "Maria Garcia",
          "birth_date": "1990-03-20",
          "gender": "female"
        }
      }
    },
    "id": 1
  }'
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Your Healthcare AI                   │
├─────────────────────────────────────────────────────────┤
│  🔧 hacs-utils    │  Framework integrations & adapters  │
│  🏥 hacs-tools    │  37+ healthcare-specific tools      │ 
│  📊 hacs-registry │  Resource & tool discovery          │
├─────────────────────────────────────────────────────────┤
│  💾 hacs-persistence │ Database & vector operations    │
│  🔒 hacs-auth        │ Actor-based security & sessions │
│  🏗️ hacs-infrastructure │ DI container & monitoring  │
├─────────────────────────────────────────────────────────┤
│  🧠 hacs-core     │  Base protocols & infrastructure    │
│  📋 hacs-models   │  FHIR-compliant data models        │
└─────────────────────────────────────────────────────────┘
```

## Healthcare Tools

**37+ tools across 9 domains:**

| Domain | Tools | Purpose |
|--------|-------|---------|
| **🔍 Resource Management** | 8 tools | Patient records, CRUD operations, search |
| **🧠 Memory Operations** | 5 tools | Clinical memory, context retrieval |
| **📊 Clinical Workflows** | 4 tools | Assessment protocols, decision support |
| **🔍 Vector Search** | 3 tools | Semantic healthcare record search |
| **⚕️ Schema Discovery** | 5 tools | Resource exploration, field analysis |
| **🛠️ Development Tools** | 4 tools | Templates, model composition |
| **🔗 FHIR Integration** | 3 tools | Standards compliance, validation |
| **📈 Healthcare Analytics** | 3 tools | Quality measures, population health |
| **🤖 AI Integrations** | 2 tools | Model deployment, optimization |

## Examples

### Complete Clinical Encounter

```python
from hacs_models import Patient, Observation, MemoryBlock
from hacs_models.types import ObservationStatus
from hacs_auth import Actor, ActorRole

# Healthcare provider  
provider = Actor(
    name="Dr. Maria Santos",
    role=ActorRole.PHYSICIAN,
    organization="Downtown Medical"
)

# Patient with context
patient = Patient(
    full_name="Roberto Silva",
    birth_date="1975-08-12", 
    gender="male",
    agent_context={
        "chief_complaint": "Follow-up for diabetes",
        "current_medications": ["metformin 1000mg BID"]
    }
)

# Clinical observations
hba1c = Observation(
    status=ObservationStatus.FINAL,
    code=CodeableConcept(text="Hemoglobin A1c"),
    subject=f"Patient/{patient.id}",
    value_quantity=Quantity(value=8.1, unit="%")
)

# Clinical memory
episodic_memory = MemoryBlock(
    memory_type="episodic",
    content=f"Patient {patient.full_name} HbA1c improved from 9.2% to 8.1% after medication adjustment.",
    importance_score=0.85,
    tags=["diabetes", "medication_adherence", "improvement"],
    context_metadata={"patient_id": patient.id}
)

print(f"✅ Encounter: {patient.full_name}")
print(f"📊 HbA1c: {hba1c.get_value_summary()}")
print(f"🧠 Memory: {episodic_memory.content[:50]}...")
```

### LangChain Integration

```python
from langchain_openai import ChatOpenAI
from hacs_utils.integrations.langchain import HACSLangChainAdapter

# Wrap any LLM for HACS compatibility
llm = ChatOpenAI(model="gpt-4")
hacs_llm = HACSLangChainAdapter(llm)

# Get healthcare tools
tools = hacs_llm.get_healthcare_tools()
print(f"Available tools: {len(tools)}")
```

### Memory Management

```python
from hacs_models import MemoryBlock

# Different memory types for clinical reasoning
memories = [
    MemoryBlock(
        memory_type="episodic",
        content="Patient reported chest pain during morning rounds",
        importance_score=0.9,
        tags=["chest_pain", "urgent"]
    ),
    MemoryBlock(
        memory_type="procedural", 
        content="Chest pain protocol: 1) Assess vitals 2) ECG 3) Cardiac enzymes",
        importance_score=0.85,
        tags=["protocol", "chest_pain"]
    ),
    MemoryBlock(
        memory_type="working",
        content="Currently analyzing patient symptoms for differential diagnosis",
        importance_score=0.7,
        task_context="patient_assessment"
    )
]

for memory in memories:
    print(f"{memory.memory_type}: {memory.content[:40]}...")
```

## Packages

All packages available on PyPI:

| Package | Purpose | Install |
|---------|---------|---------|
| **hacs-models** | FHIR data models | `pip install hacs-models` |
| **hacs-auth** | Actor-based security | `pip install hacs-auth` |
| **hacs-core** | Base protocols | `pip install hacs-core` |
| **hacs-tools** | Healthcare tools | `pip install hacs-tools` |
| **hacs-utils** | Framework integrations | `pip install hacs-utils` |
| **hacs-persistence** | Database operations | `pip install hacs-persistence` |
| **hacs-registry** | Resource discovery | `pip install hacs-registry` |
| **hacs-infrastructure** | DI & monitoring | `pip install hacs-infrastructure` |
| **hacs-cli** | Command-line tools | `pip install hacs-cli` |

## Development

```bash
# Clone repository
git clone https://github.com/solanovisitor/hacs-ai.git
cd hacs-ai

# Install with UV
uv sync

# Run tests
uv run pytest

# Start services
docker-compose up -d

# Validate installation
python examples/validated_hacs_examples.py
```

## Documentation

- **[Quick Start](docs/quick-start.md)** - Get up and running
- **[Basic Usage](docs/basic-usage.md)** - Core patterns and examples
- **[Healthcare Tools](docs/healthcare-tools.md)** - Complete tool reference
- **[Integration Guide](docs/integrations.md)** - Framework integrations
- **[Architecture](docs/architecture/)** - Design decisions and patterns

## Enterprise Support

For enterprise deployments, custom healthcare AI solutions, and consulting:

📧 [solanovisitor@gmail.com](mailto:solanovisitor@gmail.com)

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ for Healthcare AI**

[GitHub](https://github.com/solanovisitor/hacs-ai) • [Documentation](docs/) • [Issues](https://github.com/solanovisitor/hacs-ai/issues)

</div>