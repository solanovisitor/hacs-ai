# 🏥 HACS

**Build healthcare AI agents that actually understand medicine**

[![License](https://img.shields.io/github/license/solanovisitor/hacs-ai)](https://github.com/solanovisitor/hacs-ai/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://python.org)
[![PyPI](https://img.shields.io/pypi/v/hacs-core)](https://pypi.org/project/hacs-core/)

HACS (Healthcare Agent Communication Standard) is the only framework built specifically for healthcare AI. Instead of building medical AI on generic tools, HACS provides healthcare-first infrastructure with FHIR compliance, clinical memory, and 37+ medical tools built-in.

## Why HACS?

Building healthcare AI shouldn't require rebuilding healthcare infrastructure. HACS provides:

- **🏥 Healthcare-Native Models**: FHIR-compliant Patient, Observation, Encounter models with clinical context
- **🧠 Clinical Memory**: Episodic, procedural, and executive memory for medical reasoning  
- **🔒 Healthcare Security**: Actor-based permissions with audit trails for medical compliance
- **🛠️ Medical Tools**: 37+ healthcare tools via MCP for clinical workflows
- **⚡ Instant Setup**: Working healthcare AI in minutes, not months

## Quick Start

```bash
pip install hacs-core hacs-auth hacs-tools hacs-utils
```

**That's it.** You now have healthcare-native AI infrastructure.

## Example: Context Engineering

```python
from hacs_auth import Actor, ActorRole
from hacs_models import Patient, Observation, MemoryBlock, CodeableConcept, Quantity
from hacs_models.types import ObservationStatus

# 1. Create healthcare AI agent with proper permissions
clinical_ai = Actor(
    name="Dr. HACS Assistant",
    role=ActorRole.AGENT,
    organization="General Hospital",
    permissions=["patient:read", "observation:write", "memory:write"]
)

# 2. Patient with rich clinical context
patient = Patient(
    full_name="John Smith", 
    birth_date="1980-01-15",
    agent_context={
        "chief_complaint": "Follow-up for diabetes and hypertension",
        "current_medications": ["metformin 1000mg BID", "lisinopril 10mg daily"],
        "last_hba1c": "7.2%",
        "allergies": ["penicillin"]
    }
)

# 3. Record clinical findings with structured data
bp_obs = Observation(
    status=ObservationStatus.FINAL,
    code=CodeableConcept(text="Blood Pressure"),
    subject=f"Patient/{patient.id}",
    value_quantity=Quantity(value=145.0, unit="mmHg"),
    performer=[f"Practitioner/{clinical_ai.id}"]
)

hba1c_obs = Observation(
    status=ObservationStatus.FINAL,
    code=CodeableConcept(text="Hemoglobin A1c"),
    subject=f"Patient/{patient.id}",
    value_quantity=Quantity(value=6.8, unit="%")
)

# 4. AI clinical reasoning with structured memory
clinical_assessment = MemoryBlock(
    memory_type="episodic",
    content=f"""Patient {patient.full_name} assessment:
    - BP: 145 mmHg (elevated, on lisinopril 10mg)
    - HbA1c: 6.8% (excellent improvement from 7.2%)
    - Diabetes: well-controlled, continue metformin
    - Hypertension: consider increasing lisinopril or adding second agent
    - Next visit: 3 months""",
    importance_score=0.9,
    tags=["diabetes_controlled", "hypertension_management", "medication_adjustment"],
    context_metadata={
        "patient_id": patient.id,
        "provider_id": clinical_ai.id,
        "encounter_type": "follow_up",
        "risk_stratification": "moderate",
        "action_needed": "bp_medication_review"
    }
)

# 5. Results
print(f"🏥 Healthcare AI Assessment Complete")
print(f"👨‍⚕️ Provider: {clinical_ai.name}")
print(f"👤 Patient: {patient.full_name} (Diabetes + Hypertension)")
print(f"📊 Findings: BP {bp_obs.get_value_summary()}, HbA1c {hba1c_obs.get_value_summary()}")
print(f"🧠 Clinical reasoning stored with {len(clinical_assessment.tags)} structured tags")
print(f"⚠️ Action needed: {clinical_assessment.context_metadata['action_needed']}")
```

**Output:**
```
🏥 Healthcare AI Assessment Complete
👨‍⚕️ Provider: Dr. HACS Assistant
👤 Patient: John Smith (Diabetes + Hypertension) 
📊 Findings: BP 145.0 mmHg, HbA1c 6.8 %
🧠 Clinical reasoning stored with 3 structured tags
⚠️ Action needed: bp_medication_review
```

### With LangGraph Integration

Build sophisticated healthcare agents using LangGraph's workflow engine, powered by HACS healthcare models:

```python
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from hacs_utils.integrations.langchain import HACSLangChainAdapter

# Agent state with HACS healthcare models
from hacs_models import Patient, Observation, MemoryBlock, Encounter
from hacs_core.memory import ClinicalMemoryManager
from typing import List, Optional


# Healthcare-aware LLM with HACS tools via local MCP server
llm = HACSLangChainAdapter(
    llm=ChatOpenAI(model="gpt-4"),
    tools_registry="http://localhost:8001"
)

class HealthcareState:
    patient: Optional[Patient] = None
    clinical_findings: List[Observation] = []
    clinical_memories: List[MemoryBlock] = []
    current_encounter: Optional[Encounter] = None
    assessment: Optional[MemoryBlock] = None
    care_plan: dict = {}

def gather_patient_info(state):
    """Search for patient history using HACS infrastructure"""
    # Search for patient using HACS tools
    patient_search = llm.invoke_tool("search_hacs_records", {
        "query": f"patient:{state['patient'].full_name}",
        "resource_types": ["Patient", "Observation", "MemoryBlock"]
    })
    
    # Parse results into HACS models
    for result in patient_search["results"]:
        if result["resource_type"] == "Observation":
            obs = Observation(**result["data"])
            state["clinical_findings"].append(obs)
        elif result["resource_type"] == "MemoryBlock":
            memory = MemoryBlock(**result["data"])
            state["clinical_memories"].append(memory)
    
    return state

def clinical_assessment(state):
    """AI generates clinical assessment using HACS memory"""
    # Build clinical context using efficient HACS data selection
    clinical_context = {
        "patient": state["patient"].model_dump(include={
            "full_name", "birth_date", "gender", "agent_context"
        }),
        "recent_observations": [
            obs.model_dump(include={"status", "code", "value_quantity", "effective_date_time"})
            for obs in state["clinical_findings"][-5:]
        ],
        "relevant_memories": [
            mem.model_dump(include={"content", "importance_score", "tags"})
            for mem in state["clinical_memories"] if mem.importance_score > 0.7
        ]
    }
    
    prompt = f"""
    Patient: {state['patient'].full_name}
    Clinical Context: {clinical_context}
    
    Provide clinical assessment and recommendations.
    """
    
    assessment_content = llm.invoke(prompt)
    
    # Store assessment as HACS MemoryBlock
    assessment_memory = MemoryBlock(
        memory_type="episodic",
        content=assessment_content.content,
        importance_score=0.9,
        tags=["clinical_assessment", "ai_generated"],
        context_metadata={
            "patient_id": state["patient"].id,
            "encounter_id": state["current_encounter"].id if state["current_encounter"] else None
        }
    )
    
    state["assessment"] = assessment_memory
    return state

def create_care_plan(state):
    """Generate structured care plan using HACS tools"""
    care_plan_result = llm.invoke_tool("generate_care_plan", {
        "patient_id": state['patient'].id,
        "patient_summary": state["patient"].get_text_summary(),
        "assessment": state["assessment"].model_dump(include={
            "content", "importance_score", "tags"
        }),
        "clinical_findings": [
            obs.model_dump(include={"status", "code", "value_quantity"})
            for obs in state["clinical_findings"]
        ],
        "goals": ["optimize_diabetes_control", "improve_medication_adherence"]
    })
    
    state["care_plan"] = care_plan_result["plan"]
    return state

# Build healthcare agent workflow  
workflow = StateGraph(HealthcareState)
workflow.add_node("gather_info", gather_patient_info)
workflow.add_node("assess", clinical_assessment)
workflow.add_node("plan", create_care_plan)

workflow.set_entry_point("gather_info")
workflow.add_edge("gather_info", "assess")
workflow.add_edge("assess", "plan")
workflow.add_edge("plan", END)

# Compile and run healthcare agent
healthcare_agent = workflow.compile()

# Initialize with HACS Patient model
patient = Patient(
    full_name="John Smith",
    birth_date="1980-01-15",
    agent_context={
        "chief_complaint": "Diabetes follow-up",
        "current_medications": ["metformin 1000mg BID"],
        "last_hba1c": "7.2%"
    }
)

# Create encounter for this session
encounter = Encounter(
    status="in-progress",
    **{"class": "ambulatory"},  # 'class' is a Python keyword, so use dict unpacking
    subject=f"Patient/{patient.id}"
)

# Execute healthcare agent with HACS models
result = healthcare_agent.invoke({
    "patient": patient,
    "clinical_findings": [],
    "clinical_memories": [],
    "current_encounter": encounter,
    "assessment": None,
    "care_plan": {}
})

print(f"✅ Patient: {result['patient'].full_name}")
print(f"📊 Clinical findings: {len(result['clinical_findings'])} observations")
print(f"🧠 Assessment: {result['assessment'].content[:100]}...")
print(f"📋 Care plan: {len(result['care_plan'])} recommendations")

# Access efficient data summaries for downstream processing
patient_summary = result['patient'].get_text_summary()
essential_data = result['patient'].model_dump(include={
    "full_name", "birth_date", "agent_context"
})
print(f"💡 Efficient access: {patient_summary}, {len(essential_data)} core fields")
```

## Features

### 👨‍⚕️ Healthcare-Native Models

FHIR-compliant models with clinical context built-in:

```python
# Patient with clinical context for AI agents
patient = Patient(
    full_name="John Smith",
    birth_date="1980-01-15", 
    agent_context={
        "chief_complaint": "Diabetes follow-up",
        "current_medications": ["metformin 1000mg BID"],
        "last_hba1c": "7.2%",
        "risk_factors": ["family_history_diabetes"]
    }
)

# Clinical observations with structured data
observation = Observation(
    status=ObservationStatus.FINAL,
    code=CodeableConcept(text="HbA1c"),
    subject=f"Patient/{patient.id}",
    value_quantity=Quantity(value=6.8, unit="%")
)
```

### 🧠 Clinical Memory System

Three types of clinical memory for medical AI reasoning:

```python
# Episodic: Specific patient encounters
episodic_memory = MemoryBlock(
    memory_type="episodic",
    content="Patient reported improved glucose control after medication adjustment",
    context_metadata={"patient_id": patient.id, "encounter_date": "2024-01-15"}
)

# Semantic: Clinical knowledge and guidelines
semantic_memory = MemoryBlock(
    memory_type="semantic", 
    content="For T2DM patients with HbA1c >7%, consider metformin dose optimization per ADA guidelines",
    tags=["diabetes_management", "medication_protocol"]
)

# Working: Active clinical decision making
working_memory = MemoryBlock(
    memory_type="working",
    content="Prioritize medication adherence counseling for patients with suboptimal glucose control",
    importance_score=0.9
)
```

### 🛠️ Medical Tools Registry

37+ healthcare tools with efficient HACS data selection patterns:

```python
from hacs_models import Patient, Observation
from hacs_tools import call_hacs_tool

# Create patient using HACS models
patient = Patient(
    full_name="Maria Garcia",
    birth_date="1985-03-20",
    agent_context={"chief_complaint": "Diabetes management"}
)

# Resource management with efficient HACS data selection
patient_result = call_hacs_tool("create_hacs_record", {
    "resource_type": "Patient",
    "resource_data": patient.model_dump(exclude={
        "text", "contained", "extension", "modifier_extension"
    })
})

# Semantic search with structured output formatting
search_results = call_hacs_tool("search_hacs_records", {
    "query": "diabetes patients with elevated HbA1c",
    "resource_types": ["Patient", "Observation"],
    "filters": {"importance_score": {"min": 0.7}},
    "output_format": "summary"  # Request lightweight summaries
})

# Clinical workflow execution with optimized context
workflow_result = call_hacs_tool("execute_clinical_workflow", {
    "workflow_type": "diabetes_assessment",
    "patient_summary": patient.get_text_summary(),
    "patient_context": patient.model_dump(include={
        "full_name", "birth_date", "agent_context"
    }),
    "clinical_context": {
        "medications": patient.agent_context.get("medications", []),
        "chief_complaint": patient.agent_context.get("chief_complaint")
    }
})

# Memory operations preserving clinical context
memory_result = call_hacs_tool("create_memory", {
    "content": f"Patient {patient.full_name}: Diabetes management plan updated",
    "memory_type": "episodic",
    "context_metadata": {
        "patient_id": patient.id,
        "clinical_specialty": "endocrinology"
    },
    "tags": ["diabetes", "care_plan_update"]
})

# Efficient data selection for API responses
patient_api_response = patient.model_dump(include={
    "id", "full_name", "birth_date", "gender"  # Only essential fields
})

# Text summaries for LLM context
patient_summary_text = patient.get_text_summary()  # "Patient patient-abc123"
```

### ⚡ Efficient Data Selection Patterns

HACS models provide multiple ways to optimize data handling:

```python
# 1. Include only needed fields (reduces token usage)
lightweight_patient = patient.model_dump(include={
    "full_name", "birth_date", "agent_context"
})

# 2. Exclude large/unnecessary fields (faster serialization)  
clean_patient = patient.model_dump(exclude={
    "text", "contained", "extension", "modifier_extension"
})

# 3. Text summaries for efficient LLM context
patient_reference = patient.get_text_summary()  # Just "Patient patient-id"

# 4. Memory-efficient observation handling
essential_vitals = [
    obs.model_dump(include={"status", "code", "value_quantity"})
    for obs in recent_observations
]

# 5. Selective memory context
relevant_memories = [
    mem.model_dump(include={"content", "importance_score"})
    for mem in clinical_memories if mem.importance_score > 0.8
]
```

### 🔒 Healthcare Actor Security

Role-based permissions with audit trails:

```python
# Healthcare professionals with specific permissions
physician = Actor(
    name="Dr. Sarah Chen",
    role=ActorRole.PHYSICIAN,
    organization="General Hospital",
    permissions=["patient:read", "patient:write", "observation:write", "memory:write"]
)

nurse = Actor(
    name="Nurse Johnson", 
    role=ActorRole.NURSE,
    permissions=["patient:read", "observation:read", "vitals:write"]
)

# AI agents with controlled access
clinical_ai = Actor(
    name="Clinical Assistant AI",
    role=ActorRole.AGENT,
    permissions=["patient:read", "memory:read", "analytics:population"]
)
```

### 📋 Clinical Workflows  

```python
from hacs_registry import WorkflowRegistry

workflows = WorkflowRegistry()

# Register diabetes management workflow
workflows.register_workflow("diabetes_visit", {
    "steps": [
        {"action": "search_patient_history", "tools": ["search_hacs_records"]},
        {"action": "record_vitals", "tools": ["create_hacs_record"]},
        {"action": "assess_glucose_control", "tools": ["analyze_trends"]},
        {"action": "update_care_plan", "tools": ["create_care_plan"]}
    ]
})

# Execute workflow
workflow_result = call_hacs_tool("execute_workflow", {
    "workflow_name": "diabetes_visit",
    "patient_id": patient.id,
    "actor": clinical_ai.id
})
```

### 🤖 LangGraph Healthcare Agent

```python
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from hacs_utils.integrations.langchain import HACSLangChainAdapter

# HACS-enabled LLM with healthcare tools
llm = HACSLangChainAdapter(
    llm=ChatOpenAI(model="gpt-4"),
    tools_registry="http://localhost:8001"
)

# Agent state with healthcare context
class HealthcareState:
    patient_data: dict
    clinical_findings: list
    assessment: str
    plan: list

def gather_patient_info(state):
    """Search for patient history and current data"""
    patient_search = llm.invoke_tool("search_hacs_records", {
        "query": f"patient:{state['patient_data']['name']}",
        "resource_types": ["Patient", "Observation", "MemoryBlock"]
    })
    
    state["clinical_findings"] = patient_search["results"]
    return state

def clinical_assessment(state):
    """AI generates clinical assessment"""
    prompt = f"""
    Patient: {state['patient_data']['name']}
    Clinical findings: {state['clinical_findings']}
    
    Provide clinical assessment and recommendations.
    """
    
    assessment = llm.invoke(prompt)
    state["assessment"] = assessment.content
    return state

def create_care_plan(state):
    """Generate structured care plan"""
    care_plan = llm.invoke_tool("create_care_plan", {
        "patient_id": state['patient_data']['id'],
        "assessment": state["assessment"],
        "goals": ["optimize_bp_control", "medication_adherence"]
    })
    
    state["plan"] = care_plan["recommendations"]
    return state

def store_clinical_memory(state):
    """Save encounter to clinical memory"""
    memory_result = llm.invoke_tool("create_memory", {
        "content": f"Clinical encounter: {state['assessment']}. Plan: {state['plan']}",
        "memory_type": "episodic",
        "patient_id": state['patient_data']['id']
    })
    return state

# Build healthcare agent workflow
workflow = StateGraph(HealthcareState)
workflow.add_node("gather_info", gather_patient_info)
workflow.add_node("assess", clinical_assessment)  
workflow.add_node("plan", create_care_plan)
workflow.add_node("store", store_clinical_memory)

workflow.set_entry_point("gather_info")
workflow.add_edge("gather_info", "assess")
workflow.add_edge("assess", "plan")
workflow.add_edge("plan", "store")
workflow.add_edge("store", END)

# Compile and run healthcare agent
healthcare_agent = workflow.compile()

# Execute clinical encounter
result = healthcare_agent.invoke({
    "patient_data": {"name": "John Smith", "id": "patient-123"},
    "clinical_findings": [],
    "assessment": "",
    "plan": []
})

print(f"✅ Healthcare Agent Assessment: {result['assessment'][:100]}...")
print(f"📋 Care Plan: {len(result['plan'])} recommendations")
```

### 🏗️ Production Setup

```python
# docker-compose.yml
services:
  hacs-postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: hacs
      
  hacs-mcp-server:
    image: hacs/mcp-server:latest
    ports:
      - "8000:8000"
      
  hacs-registry:
    image: hacs/registry:latest 
    ports:
      - "8001:8001"
```

```bash
# Start all services
docker-compose up -d

# Verify healthcare tools available
curl http://localhost:8000/  # 37+ healthcare tools
curl http://localhost:8001/  # Registry for customization

# Initialize for your healthcare domain
python -m hacs_registry init --domain=cardiology
```

### 🔗 Integration with Existing AI

```python
# Works with any LLM
import openai
from hacs_models import Patient
from hacs_utils.context import build_clinical_context

patient = Patient(full_name="Jane Doe", birth_date="1985-01-01")
clinical_context = build_clinical_context(patient)

response = openai.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a clinical AI assistant."},
        {"role": "user", "content": f"Context: {clinical_context}\n\nQuestion: What are the treatment options?"}
    ]
)

# HACS provides the healthcare infrastructure, you use any LLM
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                Your Healthcare AI App                   │
├─────────────────────────────────────────────────────────┤
│  🔧 hacs-utils    │  LangChain/OpenAI/Claude adapters   │
│  🏥 hacs-tools    │  37+ healthcare tools (MCP)         │ 
├─────────────────────────────────────────────────────────┤
│  🔒 hacs-auth     │  Healthcare actors + permissions    │
│  💾 hacs-persistence │ FHIR data + vector memory      │
├─────────────────────────────────────────────────────────┤
│  🧠 hacs-core     │  Clinical reasoning protocols       │
│  📋 hacs-models   │  FHIR-compliant healthcare models   │
└─────────────────────────────────────────────────────────┘
```

## Installation

### Quick Start

```bash
pip install hacs-core hacs-auth hacs-models hacs-tools
```

### With Services (Optional)

```bash
# Clone for development or advanced setup
git clone https://github.com/solanovisitor/hacs-ai.git
cd hacs-ai

# Start healthcare infrastructure 
docker-compose up -d  # PostgreSQL + pgvector, MCP server
```

### Framework Integration

```bash
# LangChain integration
pip install hacs-utils[langchain]

# OpenAI integration  
pip install hacs-utils[openai]

# All integrations
pip install hacs-utils[all]
```

## Documentation

- **[Quick Start Guide](docs/quick-start.md)** - Get running in 5 minutes
- **[Healthcare Tools Reference](docs/healthcare-tools.md)** - 37+ medical AI tools
- **[LangGraph Healthcare Agent](examples/hacs_developer_agent/)** - Complete working example
- **[API Reference](docs/api/)** - Comprehensive API documentation

## Community & Support

- **[GitHub Discussions](https://github.com/solanovisitor/hacs-ai/discussions)** - Community Q&A
- **[Issues](https://github.com/solanovisitor/hacs-ai/issues)** - Bug reports and feature requests
- **Enterprise Support**: [solanovisitor@gmail.com](mailto:solanovisitor@gmail.com)

## License

HACS is released under the MIT License. See [LICENSE](LICENSE) for details.

---

<div align="center">

**Ready to build the future of healthcare AI?**

[🚀 Get Started](docs/quick-start.md) • [🤖 See Examples](examples/) • [💬 Join Community](https://github.com/solanovisitor/hacs-ai/discussions)

</div>
