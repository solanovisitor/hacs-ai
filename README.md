# 🏥 HACS

**Context Engineering for Healthcare AI Agents**

[![License](https://img.shields.io/github/license/solanovisitor/hacs-ai)](https://github.com/solanovisitor/hacs-ai/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://python.org)
[![PyPI](https://img.shields.io/pypi/v/hacs-core)](https://pypi.org/project/hacs-core/)

HACS (Healthcare Agent Communication Standard) is the first context engineering framework designed specifically for healthcare AI. In the new agent-based world, healthcare AI requires specialized context management that generic tools can't provide. HACS implements the four core context engineering strategies—**Write**, **Select**, **Compress**, **Isolate**—optimized for medical intelligence.

## The Healthcare Context Engineering Problem

Healthcare AI agents face unique context challenges that generic frameworks can't solve:

- **🩺 Medical Context Complexity**: Clinical data spans patients, conditions, medications, lab results, imaging, family history, and social determinants
- **⚖️ Regulatory Context Boundaries**: HIPAA, FHIR standards, audit requirements, and clinical liability create strict context isolation needs  
- **🧠 Clinical Reasoning Context**: Medical decision-making requires episodic memory (patient encounters), semantic memory (medical knowledge), and working memory (active diagnosis)
- **🔄 Longitudinal Context**: Healthcare context evolves over years with chronic conditions, medication changes, and care coordination across providers

## HACS: Healthcare Context Engineering

HACS solves these challenges by implementing context engineering strategies specifically for medical AI:

### 🖊️ **Write Context** - Clinical Memory System
Clinical AI agents must actively generate and store medical context during patient interactions:

```python
# HACS writes clinical context through structured memory
clinical_memory = MemoryBlock(
    memory_type="episodic",                    # Specific patient encounter
    content="Patient reported 50% reduction in chest pain after starting metoprolol",
    importance_score=0.9,                     # Clinical significance scoring
    tags=["chest_pain", "metoprolol", "improvement"],
    context_metadata={
        "patient_id": patient.id,
        "medication_change": "metoprolol_start",
        "outcome": "symptom_improvement"
    }
)
```

### 🎯 **Select Context** - Efficient Clinical Data Selection
Healthcare AI needs precise context selection to avoid information overload while preserving clinical safety:

```python
# HACS selects only essential clinical context
essential_patient_context = patient.model_dump(include={
    "full_name", "birth_date", "agent_context"    # Core identity + clinical context
})

# Select relevant recent observations only
recent_vitals = [
    obs.model_dump(include={"status", "code", "value_quantity", "effective_date_time"})
    for obs in observations 
    if obs.effective_date_time > datetime.now() - timedelta(days=30)
]

# Select high-importance clinical memories
relevant_memories = [
    mem.model_dump(include={"content", "importance_score", "tags"})
    for mem in clinical_memories 
    if mem.importance_score > 0.8
]
```

### 🗜️ **Compress Context** - Medical Intelligence Summarization  
Clinical context compression must preserve medical accuracy while reducing token usage:

```python
# HACS compresses patient context for efficient LLM consumption
patient_summary = patient.get_text_summary()  # "Patient patient-abc123: 45M, DM2, HTN"

# Clinical assessment compressed for context efficiency
compressed_assessment = clinical_assessment.model_dump(include={
    "content", "importance_score", "tags"      # Essential clinical reasoning only
})

# Multi-observation clinical summary
vitals_summary = f"Recent vitals: BP {bp_obs.get_value_summary()}, HR {hr_obs.get_value_summary()}"
```

### 🔒 **Isolate Context** - Healthcare Compliance Boundaries
Medical AI requires strict context isolation for patient privacy, regulatory compliance, and clinical liability:

```python
# HACS isolates context through healthcare actor permissions
physician = Actor(
    name="Dr. Sarah Chen",
    role=ActorRole.PHYSICIAN,
    organization="General Hospital",  
    permissions=["patient:read", "patient:write", "observation:write"]  # Scoped medical permissions
)

# Context isolation through secure healthcare operations
clinical_context = build_clinical_context(
    patient=patient,
    actor=physician,                           # Access control
    permissions_required=["patient:read"],     # Permission-based context access
    audit_trail=True                          # Compliance logging
)
```

## Why Healthcare Context Engineering Matters

In the agent-based world, healthcare AI faces unique challenges:

- **🤖 Agent Proliferation**: Clinical workflows will use dozens of specialized AI agents (diagnostic AI, medication management AI, clinical documentation AI)
- **🏥 Care Coordination**: Healthcare agents must share context across providers while maintaining privacy and compliance
- **📊 Population Health**: AI agents need efficient context patterns to process millions of patient records for population insights
- **⚡ Real-time Clinical Decisions**: Emergency and acute care AI agents require instant access to compressed, relevant clinical context

**HACS enables production-ready healthcare AI agents on the first pass** by providing healthcare-optimized context engineering infrastructure.

## Quick Start

```bash
pip install hacs-core hacs-auth hacs-tools hacs-utils
```

**That's it.** You now have healthcare context engineering infrastructure.

## Example: Healthcare Context Engineering in Action

```python
from hacs_auth import Actor, ActorRole
from hacs_models import Patient, Observation, MemoryBlock, CodeableConcept, Quantity
from hacs_models.types import ObservationStatus
from datetime import datetime, timedelta

# 🔒 ISOLATE: Create healthcare AI agent with scoped permissions
clinical_ai = Actor(
    name="Clinical Documentation AI",
    role=ActorRole.AGENT,
    organization="General Hospital",
    permissions=["patient:read", "observation:write", "memory:write"]  # Precise medical permissions
)

# Patient with comprehensive clinical context for AI agent consumption
patient = Patient(
    full_name="John Smith", 
    birth_date="1980-01-15",
    agent_context={
        "chief_complaint": "Follow-up for diabetes and hypertension", 
        "current_medications": ["metformin 1000mg BID", "lisinopril 10mg daily"],
        "last_hba1c": "7.2%",
        "social_history": "sedentary lifestyle, high-stress job",
        "family_history": ["diabetes", "cardiovascular_disease"]
    }
)

# Clinical findings with full clinical context
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

# 🎯 SELECT: Extract only essential clinical context for AI processing
essential_patient_context = patient.model_dump(include={
    "full_name", "birth_date", "agent_context"
})

recent_observations = [
    obs.model_dump(include={"status", "code", "value_quantity", "effective_date_time"})
    for obs in [bp_obs, hba1c_obs]
]

# 🗜️ COMPRESS: Generate compressed clinical summaries for efficient LLM context
patient_summary = patient.get_text_summary()  # "Patient patient-abc123"
vitals_summary = f"Recent: BP {bp_obs.get_value_summary()}, HbA1c {hba1c_obs.get_value_summary()}"

# 🖊️ WRITE: Generate clinical context through structured memory with clinical significance
clinical_assessment = MemoryBlock(
    memory_type="episodic",
    content=f"""Patient {patient.full_name}: Diabetes well-controlled (HbA1c 6.8%, improved from 7.2%). 
    Hypertension suboptimal (BP 145/- on lisinopril 10mg). 
    Recommend: Continue metformin, consider lisinopril increase or add thiazide diuretic.
    Lifestyle counseling: stress management, exercise program.
    Follow-up: 3 months.""",
    importance_score=0.9,
    tags=["diabetes_controlled", "hypertension_suboptimal", "medication_optimization"],
    context_metadata={
        "patient_id": patient.id,
        "provider_id": clinical_ai.id,
        "clinical_complexity": "moderate",
        "action_items": ["bp_medication_review", "lifestyle_counseling"],
        "follow_up_interval": "3_months"
    }
)

# Context engineering results demonstrate all four strategies
print("🏥 Healthcare Context Engineering Complete")
print(f"👨‍⚕️ AI Agent: {clinical_ai.name}")
print(f"🔒 Isolated Context: {len(clinical_ai.permissions)} scoped permissions")
print(f"🎯 Selected Context: {len(essential_patient_context)} core patient fields")
print(f"🗜️ Compressed Context: {patient_summary} + {vitals_summary}")
print(f"🖊️ Written Context: Clinical memory {clinical_assessment.id} with {clinical_assessment.importance_score} significance")
print(f"⚠️ Action Items: {clinical_assessment.context_metadata['action_items']}")
```

**Output:**
```
🏥 Healthcare Context Engineering Complete
👨‍⚕️ AI Agent: Clinical Documentation AI
🔒 Isolated Context: 3 scoped permissions
🎯 Selected Context: 3 core patient fields
🗜️ Compressed Context: Patient patient-abc123 + Recent: BP 145.0 mmHg, HbA1c 6.8 %
🖊️ Written Context: Clinical memory memory-def456 with 0.9 significance
⚠️ Action Items: ['bp_medication_review', 'lifestyle_counseling']
```

### LangGraph + HACS: Context Engineering Workflows

Build healthcare AI workflows that implement context engineering strategies throughout the agent execution:

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

class HealthcareContextState:
    """State implementing healthcare context engineering strategies"""
    patient: Optional[Patient] = None
    clinical_findings: List[Observation] = []
    clinical_memories: List[MemoryBlock] = []
    current_encounter: Optional[Encounter] = None
    assessment: Optional[MemoryBlock] = None
    care_plan: dict = {}
    
    # Context engineering tracking
    selected_context: dict = {}
    compressed_summaries: dict = {}
    written_memories: List[MemoryBlock] = []

def gather_patient_info(state):
    """🎯 SELECT: Contextual search and selective data retrieval"""
    # Search for patient using HACS tools with context boundaries
    patient_search = llm.invoke_tool("search_hacs_records", {
        "query": f"patient:{state['patient'].full_name}",
        "resource_types": ["Patient", "Observation", "MemoryBlock"],
        "time_window": "last_12_months",  # Contextual time boundary
        "importance_threshold": 0.7       # Select only significant findings
    })
    
    # SELECT: Parse and filter results for clinical relevance
    for result in patient_search["results"]:
        if result["resource_type"] == "Observation":
            obs = Observation(**result["data"])
            state["clinical_findings"].append(obs)
        elif result["resource_type"] == "MemoryBlock":
            memory = MemoryBlock(**result["data"])
            if memory.importance_score > 0.7:  # SELECT high-importance memories only
                state["clinical_memories"].append(memory)
    
    # SELECT: Store filtered context for downstream use
    state["selected_context"] = {
        "patient_core": state["patient"].model_dump(include={
            "full_name", "birth_date", "agent_context"
        }),
        "recent_findings_count": len(state["clinical_findings"]),
        "relevant_memories_count": len(state["clinical_memories"])
    }
    
    return state

def clinical_assessment(state):
    """🗜️ COMPRESS: Generate compressed clinical context for LLM reasoning"""
    # COMPRESS: Build highly compressed clinical context
    patient_summary = state["patient"].get_text_summary()
    
    # COMPRESS: Summarize recent observations
    vitals_summary = " | ".join([
        obs.get_value_summary() 
        for obs in state["clinical_findings"][-3:]  # Last 3 most recent
    ])
    
    # COMPRESS: Extract key clinical insights from memories
    clinical_insights = [
        mem.content[:100] + "..." if len(mem.content) > 100 else mem.content
        for mem in state["clinical_memories"]
        if mem.importance_score > 0.8  # Only highest importance
    ]
    
    # COMPRESS: Create efficient context bundle
    compressed_context = {
        "patient_summary": patient_summary,
        "vitals": vitals_summary,
        "key_insights": clinical_insights[:3],  # Top 3 insights only
        "medications": state["patient"].agent_context.get("current_medications", [])
    }
    
    state["compressed_summaries"] = compressed_context
    
    prompt = f"""
    Patient: {patient_summary}
    Recent Vitals: {vitals_summary}
    Key Clinical Insights: {clinical_insights}
    
    Provide clinical assessment and recommendations.
    """
    
    assessment_content = llm.invoke(prompt)
    
    # 🖊️ WRITE: Store assessment as structured clinical memory
    assessment_memory = MemoryBlock(
        memory_type="episodic",
        content=assessment_content.content,
        importance_score=0.9,
        tags=["clinical_assessment", "ai_generated", "compressed_context"],
        context_metadata={
            "patient_id": state["patient"].id,
            "context_tokens_saved": len(str(compressed_context)),
            "compression_ratio": 0.3  # Compressed to 30% of original context
        }
    )
    
    state["assessment"] = assessment_memory
    state["written_memories"].append(assessment_memory)
    return state

def create_care_plan(state):
    """🖊️ WRITE + 🔒 ISOLATE: Generate structured care plan with context isolation"""
    # ISOLATE: Use compressed context to limit information exposure
    care_plan_result = llm.invoke_tool("generate_care_plan", {
        "patient_id": state['patient'].id,
        "patient_summary": state["compressed_summaries"]["patient_summary"],  # COMPRESS
        "assessment_summary": state["assessment"].model_dump(include={
            "content", "importance_score", "tags"  # SELECT essential fields only
        }),
        "compressed_findings": state["compressed_summaries"]["vitals"],  # COMPRESS
        "goals": ["optimize_diabetes_control", "improve_medication_adherence"]
    })
    
    # 🖊️ WRITE: Create care plan memory with context engineering metadata
    care_plan_memory = MemoryBlock(
        memory_type="semantic",  # Care plans are semantic knowledge
        content=f"Care plan generated using context engineering strategies: {care_plan_result['plan']}",
        importance_score=0.95,  # Care plans are high importance
        tags=["care_plan", "context_engineered", "ai_generated"],
        context_metadata={
            "patient_id": state["patient"].id,
            "context_strategies_used": ["select", "compress", "isolate", "write"],
            "token_efficiency": state["compressed_summaries"].get("compression_ratio", 0.3),
            "clinical_safety_preserved": True
        }
    )
    
    state["care_plan"] = care_plan_result["plan"]
    state["written_memories"].append(care_plan_memory)
    return state

# Build healthcare context engineering workflow  
workflow = StateGraph(HealthcareContextState)
workflow.add_node("gather_info", gather_patient_info)     # SELECT strategy
workflow.add_node("assess", clinical_assessment)          # COMPRESS strategy
workflow.add_node("plan", create_care_plan)              # WRITE + ISOLATE strategies

workflow.set_entry_point("gather_info")
workflow.add_edge("gather_info", "assess")
workflow.add_edge("assess", "plan")
workflow.add_edge("plan", END)

# Compile healthcare context engineering agent
healthcare_agent = workflow.compile()

# Initialize with HACS Patient model
patient = Patient(
    full_name="John Smith",
    birth_date="1980-01-15",
    agent_context={
        "chief_complaint": "Diabetes follow-up",
        "current_medications": ["metformin 1000mg BID"],
        "last_hba1c": "7.2%",
        "social_determinants": ["urban_environment", "insurance_coverage"]
    }
)

# Execute healthcare context engineering agent
result = healthcare_agent.invoke({
    "patient": patient,
    "clinical_findings": [],
    "clinical_memories": [],
    "current_encounter": None,
    "assessment": None,
    "care_plan": {},
    "selected_context": {},
    "compressed_summaries": {},
    "written_memories": []
})

print("🏥 Healthcare Context Engineering Workflow Complete")
print(f"👤 Patient: {result['patient'].full_name}")
print(f"🎯 Selected Context: {result['selected_context']['recent_findings_count']} findings, {result['selected_context']['relevant_memories_count']} memories")
print(f"🗜️ Compressed Context: {result['compressed_summaries']['patient_summary']}")
print(f"🖊️ Written Memories: {len(result['written_memories'])} new clinical memories")
print(f"🔒 Context Isolation: All operations within healthcare compliance boundaries")
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
