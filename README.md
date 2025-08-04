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

### 1. Install HACS

```bash
pip install hacs-core hacs-auth hacs-tools hacs-utils hacs-registry
```

### 2. Start Healthcare Infrastructure

```bash
# Start PostgreSQL + pgvector + MCP server + Registry
docker-compose up -d

# Verify services
curl http://localhost:8000/  # MCP server with 37+ healthcare tools
curl http://localhost:8001/  # HACS registry for customization
```

### 3. Complete Healthcare AI Agent

*Actor creation → Tool customization → Clinical workflow → Memory persistence → Registry integration*

```python
from hacs_auth import Actor, ActorRole
from hacs_models import Patient, Observation, MemoryBlock, CodeableConcept, Quantity
from hacs_models.types import ObservationStatus
from hacs_registry import HACSToolRegistry, WorkflowRegistry
from hacs_utils.mcp.tools import call_hacs_tool

# 1. Create healthcare AI agent with specialized permissions
clinical_ai = Actor(
    name="Clinical Documentation AI",
    role=ActorRole.AGENT,
    organization="General Hospital",
    permissions=[
        "patient:read", "patient:write", 
        "observation:write", "memory:write",
        "workflow:execute", "tools:customize"
    ]
)

# 2. Register custom clinical prompt templates
tool_registry = HACSToolRegistry()
tool_registry.register_prompt_template("clinical_assessment", {
    "system_prompt": """You are a clinical documentation AI. Focus on:
    - Clinical reasoning and differential diagnosis
    - Evidence-based recommendations
    - Risk stratification and follow-up needs
    - Medication adherence and side effects""",
    "user_template": "Patient: {patient_name}, Chief complaint: {chief_complaint}, Findings: {clinical_findings}",
    "output_schema": {
        "assessment": "string",
        "plan": "array",
        "risk_level": "enum:low,moderate,high",
        "follow_up_needed": "boolean"
    }
})

# 3. Create custom clinical workflow
workflow_registry = WorkflowRegistry()
workflow_registry.register_workflow("diabetes_documentation", {
    "steps": [
        {"action": "search_patient_history", "tools": ["search_hacs_records"]},
        {"action": "analyze_glucose_trends", "tools": ["analyze_time_series"]},
        {"action": "assess_medication_adherence", "tools": ["search_memories"]},
        {"action": "generate_clinical_note", "tools": ["clinical_assessment"]},
        {"action": "create_follow_up_plan", "tools": ["create_care_plan"]}
    ],
    "memory_integration": True,
    "fhir_compliance": True
})

# 4. Execute customized healthcare workflow
patient = Patient(
    full_name="Maria Rodriguez",
    birth_date="1975-08-20",
    agent_context={
        "chief_complaint": "Diabetes follow-up, reports better glucose control",
        "last_hba1c": "7.1%",
        "medications": ["metformin 1000mg BID", "glipizide 5mg daily"]
    }
)

# Search patient history with custom filters
history_result = call_hacs_tool("search_hacs_records", {
    "query": f"patient:{patient.full_name} diabetes glucose",
    "resource_types": ["Observation", "MemoryBlock"],
    "date_range": {"last_months": 6},
    "actor": clinical_ai.id
})

# Record new clinical findings
hba1c_obs = Observation(
    status=ObservationStatus.FINAL,
    code=CodeableConcept(text="Hemoglobin A1c"),
    subject=f"Patient/{patient.id}",
    value_quantity=Quantity(value=6.8, unit="%"),
    performer=[f"Practitioner/{clinical_ai.id}"]
)

# Execute custom diabetes documentation workflow
workflow_result = call_hacs_tool("execute_workflow", {
    "workflow_name": "diabetes_documentation",
    "context": {
        "patient_id": patient.id,
        "current_hba1c": 6.8,
        "previous_hba1c": 7.1,
        "medication_list": patient.agent_context["medications"]
    },
    "actor": clinical_ai.id
})

# Generate AI clinical assessment using custom prompt
assessment_result = call_hacs_tool("generate_structured_output", {
    "prompt_template": "clinical_assessment",
    "context": {
        "patient_name": patient.full_name,
        "chief_complaint": patient.agent_context["chief_complaint"],
        "clinical_findings": f"HbA1c improved from 7.1% to 6.8%, patient reports good adherence"
    },
    "actor": clinical_ai.id
})

# Create episodic memory with clinical reasoning
clinical_memory = MemoryBlock(
    memory_type="episodic",
    content=f"Patient {patient.full_name}: HbA1c excellent improvement 7.1% → 6.8%. Target achieved (<7%). Continue current regimen. Patient demonstrates excellent adherence and glucose monitoring.",
    importance_score=0.9,
    tags=["diabetes_success", "target_achieved", "medication_adherence"],
    context_metadata={
        "patient_id": patient.id,
        "provider_id": clinical_ai.id,
        "outcome": "target_achieved",
        "next_visit": "3_months"
    }
)

# Persist all clinical data
results = {
    "observation": call_hacs_tool("create_hacs_record", {
        "resource_type": "Observation",
        "resource_data": hba1c_obs.model_dump(),
        "actor": clinical_ai.id
    }),
    "memory": call_hacs_tool("create_memory", clinical_memory.model_dump()),
    "workflow": workflow_result,
    "assessment": assessment_result
}

print(f"✅ Healthcare AI workflow complete for {patient.full_name}")
print(f"📊 HbA1c: {hba1c_obs.get_value_summary()}")
print(f"🧠 Clinical reasoning: {assessment_result.get('assessment', 'Generated')}")
print(f"📋 Follow-up: {assessment_result.get('follow_up_needed', False)}")
```

## Customizing HACS for Your Healthcare Domain

### Tool Customization

```python
from hacs_registry import HACSToolRegistry

registry = HACSToolRegistry()

# Register custom healthcare tool
registry.register_tool("calculate_cardiac_risk", {
    "description": "Calculate 10-year cardiovascular risk using Framingham score",
    "parameters": {
        "age": {"type": "integer", "required": True},
        "gender": {"type": "string", "enum": ["male", "female"]},
        "cholesterol": {"type": "number", "unit": "mg/dL"},
        "hdl": {"type": "number", "unit": "mg/dL"},
        "blood_pressure": {"type": "number", "unit": "mmHg"},
        "diabetes": {"type": "boolean"},
        "smoking": {"type": "boolean"}
    },
    "implementation": "custom_cardiac_calculator",
    "output_schema": {
        "risk_percentage": "number",
        "risk_category": "enum:low,intermediate,high",
        "recommendations": "array"
    },
    "fhir_mappings": ["RiskAssessment"]
})

# Customize existing tool behavior
registry.customize_tool("search_hacs_records", {
    "default_filters": ["active_patients_only"],
    "enhanced_ranking": "clinical_relevance",
    "memory_integration": True
})
```

### Clinical Workflow Templates

```python
from hacs_registry import WorkflowRegistry

workflows = WorkflowRegistry()

# Register specialty-specific workflow
workflows.register_workflow("cardiology_consult", {
    "specialty": "cardiology",
    "steps": [
        {
            "name": "gather_cardiac_history",
            "tools": ["search_memories", "search_hacs_records"],
            "filters": ["cardiovascular", "chest_pain", "dyspnea"]
        },
        {
            "name": "calculate_risk_scores", 
            "tools": ["calculate_cardiac_risk", "assess_heart_failure_risk"],
            "parallel": True
        },
        {
            "name": "generate_recommendations",
            "tools": ["clinical_decision_support"],
            "depends_on": ["gather_cardiac_history", "calculate_risk_scores"]
        }
    ],
    "memory_types": ["episodic", "procedural"],
    "quality_measures": ["door_to_balloon_time", "guideline_adherence"]
})
```

### Prompt Engineering for Healthcare

```python
from hacs_registry import PromptRegistry

prompts = PromptRegistry()

# Clinical documentation prompts
prompts.register_template("soap_note", {
    "system": """Generate SOAP note format for clinical documentation.
    Focus on clinical reasoning, differential diagnosis, and evidence-based plans.""",
    "user": """Patient: {patient_name}
    Chief Complaint: {chief_complaint}
    History: {history}
    Physical Exam: {physical_exam}
    Labs/Studies: {diagnostic_results}
    
    Generate structured SOAP note.""",
    "schema": {
        "subjective": "detailed patient history and complaints",
        "objective": "physical exam findings and vital signs", 
        "assessment": "clinical reasoning and differential diagnosis",
        "plan": "evidence-based treatment and follow-up plan"
    }
})

# Medication counseling prompts
prompts.register_template("medication_counseling", {
    "system": """You are a clinical pharmacist providing medication counseling.
    Focus on safety, adherence, side effects, and drug interactions.""",
    "context_enrichment": ["patient_allergies", "current_medications", "renal_function"],
    "safety_checks": ["drug_interactions", "contraindications", "dosing_appropriateness"]
})
```

### Healthcare Memory Patterns

```python
from hacs_core.memory import MemoryManager

memory_manager = MemoryManager()

# Configure clinical memory patterns
memory_manager.configure_patterns({
    "episodic_retention": {
        "critical_events": "permanent",
        "routine_visits": "2_years", 
        "medication_changes": "5_years"
    },
    "semantic_knowledge": {
        "clinical_guidelines": "update_on_revision",
        "drug_information": "continuous_update",
        "patient_preferences": "permanent"
    },
    "procedural_protocols": {
        "emergency_protocols": "high_priority_cache",
        "routine_procedures": "standard_cache",
        "specialty_protocols": "context_dependent"
    }
})

# Custom memory consolidation
memory_manager.register_consolidation_rule("diabetes_management", {
    "trigger": "patient_encounter",
    "consolidate": ["glucose_trends", "medication_adherence", "lifestyle_factors"],
    "output_format": "clinical_summary",
    "importance_weighting": "outcome_based"
})
```

## Production Healthcare Services

### Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'
services:
  hacs-postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: hacs
      POSTGRES_USER: hacs_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      
  hacs-mcp-server:
    image: hacs/mcp-server:latest
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://hacs_user:${DB_PASSWORD}@hacs-postgres:5432/hacs
      HEALTHCARE_DOMAIN: ${HEALTHCARE_DOMAIN}
      
  hacs-registry:
    image: hacs/registry:latest
    ports:
      - "8001:8001"
    volumes:
      - ./custom_tools:/app/custom_tools
      - ./workflows:/app/workflows
      
  hacs-vector-search:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_data:/qdrant/storage
```

### Environment Configuration

```bash
# .env
DATABASE_URL=postgresql://hacs_user:secure_password@localhost:5432/hacs
HEALTHCARE_DOMAIN=general_medicine
ORGANIZATION_NAME=Your Healthcare System

# LLM Providers (choose one or more)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Healthcare compliance
AUDIT_LOGGING=true
HIPAA_COMPLIANCE=true
ENCRYPTION_AT_REST=true

# Custom tool paths
CUSTOM_TOOLS_PATH=./healthcare_tools
WORKFLOW_TEMPLATES_PATH=./clinical_workflows
PROMPT_TEMPLATES_PATH=./clinical_prompts
```

### Launch Healthcare Development Environment

```bash
# 1. Start all HACS services
docker-compose up -d

# 2. Initialize healthcare registry
python -m hacs_registry init --domain=cardiology --templates=clinical

# 3. Load custom tools and workflows
python -m hacs_registry load --path=./custom_healthcare_tools

# 4. Verify setup
python -c "
from hacs_utils.mcp.tools import call_hacs_tool
result = call_hacs_tool('list_tools', {})
print(f'Available tools: {len(result[\"tools\"])}')
"

# 5. Start developing your healthcare AI
python your_healthcare_agent.py
```

## Integration Examples

### LangChain Integration

```python
from langchain_openai import ChatOpenAI
from hacs_utils.integrations.langchain import HACSLangChainAdapter

# Wrap LLM with HACS healthcare capabilities
llm = ChatOpenAI(model="gpt-4")
hacs_llm = HACSLangChainAdapter(
    llm=llm,
    tools_registry="http://localhost:8001",
    healthcare_domain="cardiology"
)

# Get healthcare-specific tools
healthcare_tools = hacs_llm.get_healthcare_tools()
# Returns: 37+ tools customized for your healthcare domain
```

### Direct API Integration

```python
import openai
from hacs_models import Patient, MemoryBlock
from hacs_utils.context import HealthcareContextBuilder

# Build rich healthcare context
context_builder = HealthcareContextBuilder()
clinical_context = context_builder.build_context(
    patient=patient,
    recent_memories=recent_clinical_memories,
    relevant_guidelines=clinical_guidelines
)

# Use with any LLM
response = openai.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a clinical AI assistant."},
        {"role": "user", "content": f"Clinical context: {clinical_context}\n\nQuestion: {user_question}"}
    ]
)
```

## Enterprise Healthcare Deployment

- ✅ **HIPAA Compliance**: Built-in patterns, audit trails, encryption
- ✅ **FHIR R4**: Healthcare interoperability standards
- ✅ **Multi-tenant**: Organization-level isolation and customization  
- ✅ **Scalable**: Microservices architecture with container orchestration
- ✅ **Monitoring**: Healthcare-specific metrics and alerting

## Documentation

- **[5-Minute Quick Start](docs/quick-start.md)** - Get running immediately
- **[Healthcare Tools Reference](docs/healthcare-tools.md)** - All 37+ tools
- **[Registry & Customization](docs/registry.md)** - Tool and workflow customization
- **[Clinical Workflows](docs/workflows.md)** - Specialty-specific patterns
- **[Integration Guide](docs/integrations.md)** - Connect with existing systems

**Enterprise Support:** [solanovisitor@gmail.com](mailto:solanovisitor@gmail.com)

---

<div align="center">

**Stop rebuilding healthcare infrastructure. Start building healthcare solutions.**

[🚀 Get Started](docs/quick-start.md) • [🛠️ Customize Tools](docs/registry.md) • [💬 Discussions](https://github.com/solanovisitor/hacs-ai/discussions)

</div>