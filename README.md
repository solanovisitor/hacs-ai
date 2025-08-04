# HACS: Healthcare Agent Communication Standard

<div align="center">

![License](https://img.shields.io/github/license/solanovisitor/hacs-ai)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)

**🏥 The only framework built specifically for healthcare AI agents**

*Stop building healthcare AI on generic tools. Start with purpose-built infrastructure.*

[**🚀 Quick Start**](#quick-start) • [**🎯 Use Cases**](#use-cases) • [**📖 Docs**](docs/) • [**🛠️ Tools**](#healthcare-tools)

</div>

---

## The Healthcare AI Problem

**Current Reality**: Healthcare AI systems are built on generic frameworks that don't understand medical workflows, clinical reasoning, or healthcare compliance requirements.

**The Result**: 
- 🚫 Patient data scattered across incompatible formats
- 🚫 AI agents that can't remember clinical context between interactions  
- 🚫 No built-in understanding of medical protocols or evidence-based reasoning
- 🚫 Security and audit trails bolted on as an afterthought
- 🚫 Every team rebuilds the same healthcare patterns from scratch

## HACS Solution: Healthcare-First AI Infrastructure

HACS is the **only framework designed from the ground up for healthcare AI agents**. Instead of adapting generic tools, you get purpose-built infrastructure that understands:

✅ **Clinical Memory**: Episodic (patient encounters), procedural (protocols), executive (decisions)  
✅ **Healthcare Data**: FHIR-compliant models with clinical validation  
✅ **Medical Reasoning**: Evidence scoring, confidence tracking, clinical context  
✅ **Healthcare Security**: Actor-based permissions, audit trails, HIPAA patterns  
✅ **Clinical Workflows**: 37+ specialized tools for healthcare operations  

## Use Cases

### 🩺 Clinical Documentation AI
**Problem**: Physicians spend 2+ hours daily on documentation  
**HACS Solution**: AI agents that understand clinical context and maintain episodic memory across patient encounters

```python
from hacs_models import Patient, Observation, MemoryBlock
from hacs_auth import Actor, ActorRole

# AI agent with clinical memory
clinical_ai = Actor(
    name="Clinical Documentation Assistant",
    role=ActorRole.AGENT,
    permissions=["patient:read", "observation:write", "memory:write"]
)

# Patient encounter with context
patient = Patient(
    full_name="Sarah Johnson",
    birth_date="1985-06-15",
    agent_context={
        "chief_complaint": "Follow-up diabetes, reports improved glucose control",
        "last_hba1c": "7.2%",
        "medication_changes": "Increased metformin to 1000mg BID last visit"
    }
)

# AI remembers previous encounters
episodic_memory = MemoryBlock(
    memory_type="episodic",
    content="Patient previously struggled with medication adherence. Switching to morning-only dosing improved compliance significantly.",
    importance_score=0.9,
    context_metadata={"patient_id": patient.id, "intervention": "dosing_schedule"}
)

# AI can now provide contextual documentation
print(f"AI Context: Patient has history of adherence issues, current strategy working well")
```

### 🔬 Medical Research Assistant  
**Problem**: Researchers need AI that understands medical literature and clinical data patterns  
**HACS Solution**: Semantic memory for medical knowledge with evidence-based reasoning

```python
# AI agent with medical knowledge base
research_ai = Actor(
    name="Medical Research Assistant", 
    role=ActorRole.AGENT,
    permissions=["knowledge:read", "memory:search", "analytics:read"]
)

# Semantic memory for medical knowledge
medical_knowledge = MemoryBlock(
    memory_type="semantic",
    content="ACE inhibitors show 20% reduction in cardiovascular events in diabetic patients with proteinuria. Evidence level: High (multiple RCTs)",
    tags=["diabetes", "cardiovascular", "ace_inhibitors", "evidence_based"],
    confidence_score=0.95
)

# AI can find relevant research patterns
search_result = search_memories({
    "query": "diabetes cardiovascular protection medications",
    "memory_type": "semantic",
    "min_confidence": 0.8
})
```

### 🏥 Hospital Operations AI
**Problem**: Healthcare operations need AI that understands clinical workflows and resource management  
**HACS Solution**: Procedural memory for protocols with healthcare-specific tools

```python
# AI agent for clinical workflows
operations_ai = Actor(
    name="Hospital Operations AI",
    role=ActorRole.AGENT,
    permissions=["workflow:execute", "resource:read", "analytics:write"]
)

# Procedural memory for clinical protocols
protocol_memory = MemoryBlock(
    memory_type="procedural",
    content="Chest pain protocol: 1) Immediate vitals 2) 12-lead ECG within 10min 3) Cardiac enzymes 4) Aspirin unless contraindicated 5) Cardiology consult if STEMI",
    tags=["emergency_protocol", "chest_pain", "cardiology"],
    importance_score=1.0
)

# AI executes healthcare workflows
workflow_result = execute_clinical_workflow({
    "workflow_type": "emergency_chest_pain",
    "patient_context": {"age": 65, "symptoms": "crushing chest pain", "duration": "30min"},
    "priority": "critical"
})
```

### 💊 Medication Management AI
**Problem**: Medication errors and interactions need AI with pharmaceutical knowledge  
**HACS Solution**: Clinical decision support with drug interaction checking

```python
# AI with pharmaceutical expertise
med_ai = Actor(
    name="Medication Management AI",
    role=ActorRole.AGENT,
    permissions=["medication:analyze", "interaction:check", "alert:create"]
)

# Patient with complex medication regimen
medication_context = {
    "current_medications": [
        {"name": "warfarin", "dose": "5mg daily", "indication": "atrial_fibrillation"},
        {"name": "metformin", "dose": "1000mg BID", "indication": "diabetes"}
    ],
    "proposed_addition": {"name": "fluconazole", "dose": "200mg daily", "indication": "fungal_infection"}
}

# AI identifies critical interaction
interaction_alert = analyze_drug_interactions(medication_context)
# Result: "CRITICAL: Fluconazole increases warfarin levels 2-3x. Monitor INR closely or consider alternative antifungal."
```

## Why Not Just Use LangChain/OpenAI/Claude?

| **Generic AI Frameworks** | **HACS** |
|---------------------------|----------|
| ❌ No clinical memory types | ✅ Episodic, procedural, executive memory |
| ❌ Generic JSON data models | ✅ FHIR-compliant healthcare models |
| ❌ No medical reasoning patterns | ✅ Evidence scoring, clinical confidence |
| ❌ Basic role-based security | ✅ Healthcare actor permissions & audit |
| ❌ Build tools from scratch | ✅ 37+ healthcare-specific tools |
| ❌ No clinical workflow support | ✅ Medical protocols & decision support |
| ❌ Compliance as afterthought | ✅ HIPAA patterns built-in |

**Bottom Line**: Generic frameworks make you build healthcare infrastructure. HACS gives you healthcare infrastructure so you can build healthcare solutions.

## Quick Start

### Installation

```bash
# Core healthcare AI infrastructure
pip install hacs-core hacs-auth hacs-models

# Add specialized tools  
pip install hacs-tools hacs-utils

# Add persistence for production
pip install hacs-persistence[postgresql]
```

### Your First Healthcare AI Agent

```python
from hacs_auth import Actor, ActorRole
from hacs_models import Patient, Observation, CodeableConcept, Quantity, MemoryBlock
from hacs_models.types import ObservationStatus

# 1. Create healthcare AI agent
clinical_ai = Actor(
    name="Dr. HACS Assistant",
    role=ActorRole.AGENT,
    organization="General Hospital",
    permissions=["patient:read", "observation:write", "memory:read"]
)

# 2. Patient with clinical context
patient = Patient(
    full_name="John Smith",
    birth_date="1980-01-15",
    gender="male",
    agent_context={
        "chief_complaint": "Annual physical exam",
        "risk_factors": ["family_history_diabetes", "obesity"]
    }
)

# 3. Record clinical findings
bp_reading = Observation(
    status=ObservationStatus.FINAL,
    code=CodeableConcept(text="Blood Pressure"),
    subject=f"Patient/{patient.id}",
    value_quantity=Quantity(value=145.0, unit="mmHg")
)

# 4. AI clinical reasoning with memory
clinical_assessment = MemoryBlock(
    memory_type="episodic",
    content=f"Patient {patient.full_name} BP elevated at 145 mmHg. Given family history of diabetes and obesity, recommend lifestyle counseling and 3-month follow-up.",
    importance_score=0.8,
    tags=["hypertension", "risk_stratification", "preventive_care"],
    context_metadata={
        "patient_id": patient.id,
        "risk_level": "moderate",
        "follow_up_needed": True
    }
)

print(f"🏥 Healthcare AI Assessment Complete")
print(f"👤 Patient: {patient.full_name}")
print(f"📊 BP: {bp_reading.get_value_summary()}")
print(f"🧠 AI Reasoning: {clinical_assessment.content[:60]}...")
print(f"⚠️  Follow-up required: {clinical_assessment.context_metadata['follow_up_needed']}")
```

**Output:**
```
🏥 Healthcare AI Assessment Complete
👤 Patient: John Smith  
📊 BP: 145.0 mmHg
🧠 AI Reasoning: Patient John Smith BP elevated at 145 mmHg. Given family...
⚠️  Follow-up required: True
```

## Architecture: Built for Healthcare

```
┌─────────────────────────────────────────────────────────┐
│                Your Healthcare AI Application           │
├─────────────────────────────────────────────────────────┤
│  🔧 hacs-utils    │  LangChain, OpenAI, Claude adapters │
│  🏥 hacs-tools    │  37+ healthcare-specific tools      │ 
│  📊 hacs-registry │  Clinical resource discovery        │
├─────────────────────────────────────────────────────────┤
│  💾 hacs-persistence │ Medical data + vector storage   │
│  🔒 hacs-auth        │ Healthcare actor permissions    │
│  🏗️ hacs-infrastructure │ Clinical service management │
├─────────────────────────────────────────────────────────┤
│  🧠 hacs-core     │  Clinical reasoning protocols       │
│  📋 hacs-models   │  FHIR-compliant healthcare models   │
└─────────────────────────────────────────────────────────┘
```

**Key Differentiators:**
- **Healthcare Models**: FHIR-compliant Patient, Observation, Encounter, Medication models
- **Clinical Memory**: Episodic (encounters), Procedural (protocols), Executive (decisions)  
- **Medical Tools**: Drug interactions, clinical workflows, evidence assessment
- **Healthcare Security**: Actor-based permissions with audit trails
- **Clinical Reasoning**: Confidence scoring, evidence tracking, medical context

## Healthcare Tools (37+ Specialized)

Instead of building healthcare tools from scratch, use purpose-built ones:

| **Category** | **Tools** | **Use Cases** |
|-------------|-----------|---------------|
| **🔍 Resource Management** | 8 tools | Patient records, clinical CRUD, medical search |
| **🧠 Memory Operations** | 5 tools | Clinical memory, encounter context, medical knowledge |
| **📊 Clinical Workflows** | 4 tools | Medical protocols, care plans, clinical decisions |
| **🔍 Medical Search** | 3 tools | Semantic clinical search, similar cases, medical literature |
| **⚕️ Schema Discovery** | 5 tools | FHIR exploration, medical model analysis |
| **🛠️ Development Tools** | 4 tools | Clinical templates, medical test data, model optimization |
| **🔗 FHIR Integration** | 3 tools | Standards compliance, healthcare interoperability |
| **📈 Healthcare Analytics** | 3 tools | Quality measures, population health, risk stratification |
| **🤖 Medical AI** | 2 tools | Healthcare model deployment, clinical AI evaluation |

### Example: Drug Interaction Checking

```python
# Generic AI Framework Approach (you build everything)
def check_drug_interactions(medications):
    # You need to:
    # 1. Build drug database
    # 2. Create interaction rules  
    # 3. Implement severity scoring
    # 4. Handle contraindications
    # 5. Format clinical alerts
    # ... 200+ lines of medical logic
    pass

# HACS Approach (healthcare infrastructure included)
interaction_result = call_hacs_tool("analyze_drug_interactions", {
    "medications": ["warfarin_5mg", "fluconazole_200mg"],
    "patient_context": {"age": 72, "renal_function": "normal"}
})
# Returns: Clinical-grade interaction analysis with severity, alternatives, monitoring recommendations
```

## Integration with Your Existing AI Stack

HACS works with your existing AI tools:

```python
# With LangChain
from langchain_openai import ChatOpenAI
from hacs_utils.integrations.langchain import HACSLangChainAdapter

llm = ChatOpenAI(model="gpt-4")
hacs_llm = HACSLangChainAdapter(llm)
healthcare_tools = hacs_llm.get_healthcare_tools()  # 37+ medical tools

# With direct API calls  
import openai
from hacs_models import Patient, MemoryBlock

# Your existing AI logic + HACS healthcare infrastructure
patient_context = Patient(full_name="...", agent_context={"symptoms": "..."})
clinical_memory = MemoryBlock(memory_type="episodic", content="...")

# AI gets healthcare context automatically
ai_response = openai.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "system", "content": f"Patient context: {patient_context.agent_context}"}]
)
```

## Production Healthcare AI

```bash
# Start HACS healthcare infrastructure
docker-compose up -d  # PostgreSQL + pgvector + MCP server

# Use 37+ healthcare tools via API
curl -X POST http://localhost:8000/ -d '{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "create_hacs_record",
    "arguments": {
      "resource_type": "Patient", 
      "resource_data": {"full_name": "Patient Name", "birth_date": "1980-01-01"}
    }
  }
}'

# Healthcare tools available immediately:
# - create_hacs_record, search_hacs_records, validate_resource_data
# - create_memory, search_memories, retrieve_context  
# - execute_clinical_workflow, create_clinical_template
# - analyze_drug_interactions, calculate_quality_measures
# - + 27 more healthcare-specific tools
```

## Enterprise Healthcare AI

**Compliance-Ready:**
- ✅ HIPAA-compliant patterns built-in
- ✅ Audit trails for all healthcare operations  
- ✅ Actor-based permissions (Physician, Nurse, AI Agent roles)
- ✅ FHIR R4 compliance for healthcare interoperability

**Production-Tested:**
- ✅ Used in clinical documentation systems
- ✅ Healthcare research platforms
- ✅ Hospital operations optimization
- ✅ Medical education applications

## Documentation & Support

- **[5-Minute Quick Start](docs/quick-start.md)** - Get running immediately
- **[Healthcare Tools Reference](docs/healthcare-tools.md)** - All 37+ tools documented
- **[Clinical Examples](examples/)** - Real healthcare AI scenarios
- **[Integration Guide](docs/integrations.md)** - Connect with existing systems
- **[Architecture](docs/architecture/)** - Design principles & patterns

**Enterprise Support:** [solanovisitor@gmail.com](mailto:solanovisitor@gmail.com)

## License

MIT License - Use HACS to build the future of healthcare AI.

---

<div align="center">

**Stop rebuilding healthcare infrastructure. Start building healthcare solutions.**

[🚀 Get Started](docs/quick-start.md) • [🏥 Examples](examples/) • [🛠️ Tools](docs/healthcare-tools.md) • [💬 Discussions](https://github.com/solanovisitor/hacs-ai/discussions)

**Built with ❤️ for Healthcare AI**

</div>