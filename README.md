# HACS: Healthcare Agent Communication Standard

<div align="center">

![License](https://img.shields.io/github/license/solanovisitor/hacs-ai)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)

**🏥 The only framework built specifically for healthcare AI agents**

*Stop building healthcare AI on generic tools. Start with purpose-built infrastructure.*

[**🚀 Quick Start**](#quick-start) • [**📖 Docs**](docs/) • [**🛠️ Tools**](docs/healthcare-tools.md)

</div>

---

## The Problem

Healthcare AI systems built on **generic frameworks** (LangChain, OpenAI APIs) require rebuilding the same infrastructure:
- 🚫 Custom FHIR models and validation
- 🚫 Clinical memory and reasoning patterns  
- 🚫 Healthcare-specific security and audit
- 🚫 Medical workflows and decision support tools

## HACS Solution

**Healthcare-first infrastructure** with clinical memory, FHIR compliance, and 37+ medical tools built-in.

| **Generic AI** | **HACS** |
|----------------|----------|
| ❌ Build FHIR models | ✅ FHIR-compliant out of box |
| ❌ Custom clinical memory | ✅ Episodic/procedural/executive memory |
| ❌ Basic permissions | ✅ Healthcare actor security + audit |
| ❌ Build medical tools | ✅ 37+ healthcare tools via MCP |

## Quick Start

```bash
pip install hacs-core hacs-auth hacs-tools hacs-utils
```

## Healthcare AI Examples

### 🩺 Clinical Documentation Agent
*Actor validation → Patient search → Clinical reasoning → Memory persistence*

```python
from hacs_auth import Actor, ActorRole
from hacs_models import Patient, Observation, MemoryBlock, CodeableConcept, Quantity
from hacs_models.types import ObservationStatus

# 1. Create & validate healthcare actor
physician = Actor(
    name="Dr. Sarah Chen",
    role=ActorRole.PHYSICIAN,
    organization="General Hospital",
    permissions=["patient:read", "observation:write", "memory:write"]
)

# 2. Search for patient (via MCP tool)
search_result = call_hacs_tool("search_hacs_records", {
    "query": "John Smith diabetes",
    "resource_types": ["Patient"],
    "actor": physician.id
})

# 3. Get patient with clinical context
patient = Patient(
    full_name="John Smith",
    birth_date="1980-01-15", 
    agent_context={
        "last_visit": "2024-06-15",
        "current_medications": ["metformin 1000mg BID"],
        "hba1c_trend": "7.8% → 7.2% → 6.9%"
    }
)

# 4. Record structured clinical observation
bp_obs = Observation(
    status=ObservationStatus.FINAL,
    code=CodeableConcept(text="Blood Pressure"),
    subject=f"Patient/{patient.id}",
    value_quantity=Quantity(value=128.0, unit="mmHg"),
    performer=[f"Practitioner/{physician.id}"]
)

# 5. AI clinical reasoning with episodic memory
clinical_memory = MemoryBlock(
    memory_type="episodic",
    content=f"Patient {patient.full_name}: BP improved to 128 mmHg, HbA1c trending down to 6.9%. Continue current regimen, excellent diabetes control.",
    importance_score=0.85,
    tags=["diabetes_management", "bp_control", "medication_adherence"],
    context_metadata={
        "patient_id": patient.id,
        "provider_id": physician.id,
        "outcome": "improved_control"
    }
)

# 6. Persist to database (via MCP)
memory_result = call_hacs_tool("create_memory", clinical_memory.model_dump())
obs_result = call_hacs_tool("create_hacs_record", {
    "resource_type": "Observation",
    "resource_data": bp_obs.model_dump(),
    "actor": physician.id
})

print(f"✅ Clinical encounter documented for {patient.full_name}")
print(f"📊 BP: {bp_obs.get_value_summary()}")
print(f"🧠 Memory stored: {memory_result['memory_id']}")
```

### 🔬 Medical Research Agent  
*Knowledge retrieval → Evidence analysis → Semantic search → Research synthesis*

```python
# 1. Research agent with specialized permissions
research_ai = Actor(
    name="Medical Research AI",
    role=ActorRole.AGENT,
    permissions=["knowledge:search", "memory:semantic", "analytics:population"]
)

# 2. Search medical knowledge base
knowledge_search = call_hacs_tool("search_clinical_knowledge", {
    "query": "ACE inhibitors cardiovascular outcomes diabetes",
    "evidence_level": "high",
    "limit": 10,
    "actor": research_ai.id
})

# 3. Analyze population data patterns  
population_analysis = call_hacs_tool("generate_population_insights", {
    "population_criteria": {
        "conditions": ["diabetes", "hypertension"],
        "medications": ["ace_inhibitor"]
    },
    "analysis_type": "outcome_correlation",
    "actor": research_ai.id
})

# 4. Create semantic memory with evidence scoring
research_memory = MemoryBlock(
    memory_type="semantic",
    content="ACE inhibitors reduce cardiovascular events by 22% in diabetic patients (95% CI: 15-28%). Strongest benefit in patients with proteinuria. NNT=45 over 3 years.",
    confidence_score=0.92,
    tags=["ace_inhibitors", "diabetes", "cardiovascular_outcomes", "evidence_based"],
    context_metadata={
        "evidence_level": "1A",
        "study_count": 8,
        "total_patients": 15420,
        "nnt": 45
    }
)

# 5. Persist research findings
research_result = call_hacs_tool("create_memory", research_memory.model_dump())

print(f"🔬 Research synthesis complete: {research_result['memory_id']}")
print(f"📈 Evidence strength: {research_memory.confidence_score}")
```

### 🏥 Clinical Workflow Agent
*Protocol retrieval → Patient risk assessment → Workflow execution → Quality monitoring*

```python
# 1. Clinical workflow agent
workflow_ai = Actor(
    name="Clinical Protocol AI",
    role=ActorRole.AGENT,
    permissions=["workflow:execute", "risk:assess", "quality:monitor"]
)

# 2. Retrieve procedural memory for chest pain protocol
protocol_search = call_hacs_tool("search_memories", {
    "query": "emergency chest pain protocol",
    "memory_type": "procedural",
    "actor": workflow_ai.id
})

# 3. Execute clinical workflow with patient context
workflow_result = call_hacs_tool("execute_clinical_workflow", {
    "workflow_type": "emergency_chest_pain", 
    "patient_context": {
        "age": 58,
        "symptoms": "crushing chest pain 45min",
        "risk_factors": ["diabetes", "smoking", "family_hx"]
    },
    "priority": "critical",
    "actor": workflow_ai.id
})

# 4. Risk stratification analysis
risk_assessment = call_hacs_tool("risk_stratification", {
    "patient_data": {
        "age": 58,
        "conditions": ["diabetes"],
        "presenting_symptoms": ["chest_pain"]
    },
    "risk_model": "cardiac_risk_score",
    "actor": workflow_ai.id
})

# 5. Generate structured care plan
care_plan = {
    "immediate_actions": ["12-lead ECG", "cardiac_enzymes", "aspirin 325mg"],
    "monitoring": ["continuous_telemetry", "serial_enzymes"],
    "risk_level": risk_assessment.get("risk_category", "high"),
    "disposition": "cardiac_unit_admission"
}

# 6. Create executive memory for clinical decision
decision_memory = MemoryBlock(
    memory_type="executive",
    content=f"High-risk chest pain patient: Age 58, diabetic. Executed emergency protocol. Risk score: {risk_assessment.get('score', 'high')}. Plan: {care_plan['immediate_actions']}",
    importance_score=0.95,
    tags=["emergency_protocol", "chest_pain", "high_risk", "clinical_decision"],
    context_metadata={
        "risk_score": risk_assessment.get("score"),
        "protocol_executed": "emergency_chest_pain",
        "decision_support": True
    }
)

print(f"🏥 Clinical workflow executed: {workflow_result['workflow_id']}")
print(f"⚠️ Risk level: {risk_assessment.get('risk_category')}")
```

### 💊 Pharmacy Intelligence Agent
*Drug interaction analysis → Clinical validation → Alert generation → Monitoring recommendations*

```python
# 1. Pharmacy AI with medication permissions
pharmacy_ai = Actor(
    name="Pharmacy Intelligence AI",
    role=ActorRole.PHARMACIST,
    permissions=["medication:analyze", "interaction:check", "alert:clinical"]
)

# 2. Analyze complex medication regimen
medication_analysis = call_hacs_tool("analyze_drug_interactions", {
    "current_medications": [
        {"name": "warfarin", "dose": "5mg daily", "indication": "atrial_fibrillation"},
        {"name": "metformin", "dose": "1000mg BID", "indication": "diabetes"}
    ],
    "proposed_medication": {
        "name": "fluconazole", 
        "dose": "200mg daily", 
        "indication": "fungal_infection"
    },
    "patient_context": {"age": 72, "renal_function": "normal"},
    "actor": pharmacy_ai.id
})

# 3. Generate clinical alert if interaction found
if medication_analysis.get("severity") == "critical":
    alert_result = call_hacs_tool("create_clinical_alert", {
        "alert_type": "drug_interaction",
        "severity": "critical",
        "message": "CRITICAL: Fluconazole increases warfarin levels 2-3x. Monitor INR daily.",
        "recommendations": [
            "Consider alternative antifungal (terbinafine)",
            "If fluconazole required: Reduce warfarin dose 50%",
            "Monitor INR daily x 7 days"
        ],
        "actor": pharmacy_ai.id
    })

# 4. Create procedural memory for future reference
pharmacy_memory = MemoryBlock(
    memory_type="procedural",
    content="Warfarin-fluconazole interaction protocol: Fluconazole inhibits CYP2C9, increasing warfarin levels 2-3x. Reduce warfarin 50%, monitor INR daily. Alternative: terbinafine (no interaction).",
    importance_score=0.9,
    tags=["drug_interaction", "warfarin", "fluconazole", "cyp2c9"],
    context_metadata={
        "interaction_mechanism": "CYP2C9_inhibition",
        "monitoring_required": "INR_daily",
        "alternative_drug": "terbinafine"
    }
)

# 5. Persist pharmacy intelligence
pharmacy_result = call_hacs_tool("create_memory", pharmacy_memory.model_dump())

print(f"💊 Drug interaction analysis complete")
print(f"⚠️ Severity: {medication_analysis.get('severity')}")
print(f"📋 Recommendations: {len(medication_analysis.get('recommendations', []))}")
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                Your Healthcare AI App                   │
├─────────────────────────────────────────────────────────┤
│  🔧 hacs-utils    │  LangChain/OpenAI/Claude adapters   │
│  🏥 hacs-tools    │  37+ healthcare tools (MCP server)  │ 
├─────────────────────────────────────────────────────────┤
│  🔒 hacs-auth     │  Healthcare actors + permissions    │
│  💾 hacs-persistence │ FHIR data + vector memory      │
├─────────────────────────────────────────────────────────┤
│  🧠 hacs-core     │  Clinical reasoning protocols       │
│  📋 hacs-models   │  FHIR-compliant healthcare models   │
└─────────────────────────────────────────────────────────┘
```

## Healthcare Tools (37+)

| **Domain** | **Examples** |
|------------|-------------|
| **🔍 Resource Management** | `create_hacs_record`, `search_hacs_records`, `validate_resource_data` |
| **🧠 Memory Operations** | `create_memory`, `search_memories`, `retrieve_context` |
| **📊 Clinical Workflows** | `execute_clinical_workflow`, `create_clinical_template` |
| **💊 Drug Intelligence** | `analyze_drug_interactions`, `check_contraindications` |
| **📈 Healthcare Analytics** | `calculate_quality_measures`, `risk_stratification` |

[**Complete Tools Reference →**](docs/healthcare-tools.md)

## Production Setup

```bash
# Start HACS infrastructure
docker-compose up -d  # PostgreSQL + pgvector + MCP server

# Healthcare tools available at http://localhost:8000/
curl -X POST http://localhost:8000/ -d '{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "create_hacs_record",
    "arguments": {"resource_type": "Patient", "resource_data": {...}}
  }
}'
```

## Integration

Works with your existing AI stack:

```python
# LangChain
from hacs_utils.integrations.langchain import HACSLangChainAdapter
hacs_llm = HACSLangChainAdapter(ChatOpenAI(model="gpt-4"))

# Direct API
import openai
from hacs_models import Patient
patient_context = Patient(full_name="...", agent_context={...})
# Use patient_context in your AI prompts
```

## Enterprise Ready

- ✅ **HIPAA Compliance**: Built-in patterns and audit trails
- ✅ **FHIR R4**: Healthcare interoperability standards  
- ✅ **Actor Security**: Role-based permissions (Physician, Nurse, AI Agent)
- ✅ **Production Tested**: Used in clinical documentation and research platforms

## Documentation

- **[5-Minute Quick Start](docs/quick-start.md)** 
- **[Complete Tools Reference](docs/healthcare-tools.md)**
- **[Integration Guide](docs/integrations.md)**

**Enterprise Support:** [solanovisitor@gmail.com](mailto:solanovisitor@gmail.com)

---

<div align="center">

**Stop rebuilding healthcare infrastructure. Start building healthcare solutions.**

[🚀 Get Started](docs/quick-start.md) • [🛠️ Tools](docs/healthcare-tools.md) • [💬 Discussions](https://github.com/solanovisitor/hacs-ai/discussions)

</div>