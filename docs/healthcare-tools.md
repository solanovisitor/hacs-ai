# HACS Healthcare Tools Reference

Complete reference for all 37+ healthcare tools available through HACS MCP server.

## Tool Categories

### 🔍 Resource Management (8 tools)

Core CRUD operations for healthcare resources with FHIR compliance.

#### `create_hacs_record`
Create new healthcare resources (Patient, Observation, Encounter, etc.)

```python
# Create patient
result = call_tool("create_hacs_record", {
    "resource_type": "Patient",
    "resource_data": {
        "full_name": "Maria Garcia",
        "birth_date": "1990-03-20",
        "gender": "female"
    }
})
```

#### `get_resource`
Retrieve healthcare resource by ID and type

```python
patient = call_tool("get_resource", {
    "resource_type": "Patient", 
    "resource_id": "patient-123"
})
```

#### `update_resource`
Update existing healthcare resource

```python
call_tool("update_resource", {
    "resource_type": "Patient",
    "resource_id": "patient-123", 
    "resource_data": {
        "agent_context": {
            "insurance_provider": "Blue Cross"
        }
    }
})
```

#### `delete_resource`
Remove healthcare resource

```python
call_tool("delete_resource", {
    "resource_type": "Patient",
    "resource_id": "patient-123"
})
```

#### `validate_resource_data`
Validate resource data against FHIR schemas

```python
validation = call_tool("validate_resource_data", {
    "resource_type": "Observation",
    "data": {
        "code_text": "Blood Pressure",
        "value": "120/80",
        "unit": "mmHg"
    }
})
```

#### `list_available_resources`
Get list of all available HACS resource types

```python
resources = call_tool("list_available_resources", {})
```

#### `find_resources`
Semantic search across healthcare resources

```python
results = call_tool("find_resources", {
    "resource_type": "Patient",
    "search_criteria": {
        "semantic_query": "diabetes patients with poor glucose control"
    },
    "limit": 10
})
```

#### `search_hacs_records`
Advanced filtered search with multiple criteria

```python
records = call_tool("search_hacs_records", {
    "query": "hypertension medication",
    "resource_types": ["Patient", "Observation"],
    "filters": {
        "date_range": {
            "start": "2024-01-01", 
            "end": "2024-12-31"
        }
    }
})
```

### 🧠 Memory Operations (5 tools)

Clinical memory management for AI agent cognition.

#### `create_memory`
Store clinical memories with context

```python
memory = call_tool("create_memory", {
    "content": "Patient reports improved sleep after medication adjustment",
    "memory_type": "episodic",
    "importance_score": 0.8,
    "tags": ["medication", "sleep", "improvement"],
    "context_metadata": {
        "patient_id": "patient-123",
        "encounter_type": "follow_up"
    }
})
```

#### `search_memories`
Semantic search across clinical memories

```python
memories = call_tool("search_memories", {
    "query": "medication side effects",
    "memory_type": "episodic", 
    "limit": 5,
    "similarity_threshold": 0.7
})
```

#### `consolidate_memories`
Merge related memories for knowledge synthesis

```python
consolidated = call_tool("consolidate_memories", {
    "memory_ids": ["memory-1", "memory-2", "memory-3"],
    "consolidation_strategy": "thematic_synthesis"
})
```

#### `retrieve_context`
Get relevant clinical context for current task

```python
context = call_tool("retrieve_context", {
    "query": "diabetes management plan",
    "context_type": "clinical",
    "max_memories": 3
})
```

#### `analyze_memory_patterns`
Identify patterns and insights from clinical memories

```python
patterns = call_tool("analyze_memory_patterns", {
    "memory_type": "episodic",
    "analysis_focus": "patient_outcomes",
    "time_window": "last_30_days"
})
```

### 📊 Clinical Workflows (4 tools)

Structured clinical protocols and decision support.

#### `execute_clinical_workflow`
Run predefined clinical workflow protocols

```python
workflow = call_tool("execute_clinical_workflow", {
    "workflow_type": "diabetes_assessment",
    "patient_context": {
        "hba1c": "8.2%",
        "current_medications": ["metformin"]
    },
    "assessment_goals": ["glucose_control", "medication_optimization"]
})
```

#### `create_clinical_template`
Generate clinical assessment templates

```python
template = call_tool("create_clinical_template", {
    "template_type": "assessment",
    "focus_area": "cardiology", 
    "complexity_level": "intermediate"
})
```

#### `validate_clinical_protocol`
Ensure clinical protocols meet standards

```python
validation = call_tool("validate_clinical_protocol", {
    "protocol_data": {
        "name": "Hypertension Management",
        "steps": ["assess_bp", "lifestyle_counseling", "medication_if_needed"]
    }
})
```

#### `generate_care_plan`
Create personalized care plans

```python
care_plan = call_tool("generate_care_plan", {
    "patient_id": "patient-123",
    "primary_conditions": ["diabetes", "hypertension"],
    "goals": ["hba1c_reduction", "bp_control"]
})
```

### 🔍 Vector Search (3 tools)

Semantic search across healthcare knowledge.

#### `semantic_search_records`
Search healthcare records by semantic similarity

```python
results = call_tool("semantic_search_records", {
    "query": "patients with uncontrolled diabetes",
    "resource_types": ["Patient", "Observation"],
    "similarity_threshold": 0.8,
    "limit": 20
})
```

#### `find_similar_cases`
Find clinically similar patient cases

```python
similar = call_tool("find_similar_cases", {
    "reference_patient_id": "patient-123",
    "similarity_criteria": ["diagnosis", "demographics", "medications"],
    "limit": 5
})
```

#### `search_clinical_knowledge`
Search clinical knowledge base

```python
knowledge = call_tool("search_clinical_knowledge", {
    "query": "ACE inhibitor contraindications",
    "knowledge_types": ["guidelines", "contraindications"],
    "evidence_level": "high"
})
```

### ⚕️ Schema Discovery (5 tools)

Healthcare resource schema exploration and analysis.

#### `discover_hacs_resources`
Explore available healthcare resources

```python
resources = call_tool("discover_hacs_resources", {
    "category_filter": "clinical",
    "include_examples": True
})
```

#### `get_hacs_resource_schema`
Get detailed schema for resource type

```python
schema = call_tool("get_hacs_resource_schema", {
    "resource_type": "Patient",
    "include_validation_rules": True
})
```

#### `compare_resource_schemas`
Compare schemas between resource types

```python
comparison = call_tool("compare_resource_schemas", {
    "model_names": ["Patient", "Observation"],
    "comparison_focus": "fields"
})
```

#### `analyze_model_fields`
Analyze fields in healthcare model

```python
analysis = call_tool("analyze_model_fields", {
    "model_name": "Observation", 
    "analysis_type": "comprehensive"
})
```

#### `suggest_model_fields`
Get field suggestions for models

```python
suggestions = call_tool("suggest_model_fields", {
    "model_name": "Patient",
    "use_case": "diabetes_management"
})
```

### 🛠️ Development Tools (4 tools)

Tools for developing with HACS models and resources.

#### `create_model_stack`
Compose complex healthcare data structures

```python
stack = call_tool("create_model_stack", {
    "primary_model": "Patient",
    "related_models": ["Observation", "Encounter"],
    "composition_type": "clinical_episode"
})
```

#### `generate_test_data`
Generate realistic test data for healthcare models

```python
test_data = call_tool("generate_test_data", {
    "resource_type": "Patient",
    "count": 10,
    "demographics": "diverse",
    "include_conditions": ["diabetes", "hypertension"]
})
```

#### `validate_model_composition`
Validate complex model relationships

```python
validation = call_tool("validate_model_composition", {
    "composition_data": {
        "patient": {...},
        "observations": [...],
        "encounter": {...}
    }
})
```

#### `optimize_model_for_llm`
Optimize models for LLM consumption

```python
optimized = call_tool("optimize_model_for_llm", {
    "model_data": {...},
    "optimization_target": "token_efficiency",
    "preserve_clinical_context": True
})
```

### 🔗 FHIR Integration (3 tools)

FHIR standards compliance and interoperability.

#### `validate_fhir_compliance`
Ensure FHIR standard compliance

```python
compliance = call_tool("validate_fhir_compliance", {
    "resource_data": {...},
    "fhir_version": "R4",
    "strict_validation": True
})
```

#### `convert_to_fhir`
Convert HACS models to FHIR format

```python
fhir_resource = call_tool("convert_to_fhir", {
    "hacs_resource": {...},
    "target_fhir_version": "R4"
})
```

#### `import_from_fhir`
Import FHIR resources into HACS

```python
hacs_resource = call_tool("import_from_fhir", {
    "fhir_resource": {...},
    "enhance_for_agents": True
})
```

### 📈 Healthcare Analytics (3 tools)

Population health and quality measures.

#### `calculate_quality_measures`
Calculate healthcare quality indicators

```python
measures = call_tool("calculate_quality_measures", {
    "measure_set": "diabetes_care",
    "patient_population": "all_diabetes_patients",
    "time_period": "last_12_months"
})
```

#### `generate_population_insights`
Analyze population health trends

```python
insights = call_tool("generate_population_insights", {
    "population_criteria": {
        "conditions": ["diabetes"],
        "age_range": [18, 65]
    },
    "analysis_type": "outcome_trends"
})
```

#### `risk_stratification`
Stratify patients by risk levels

```python
stratification = call_tool("risk_stratification", {
    "patient_cohort": "diabetes_patients",
    "risk_factors": ["hba1c", "blood_pressure", "medications"],
    "stratification_model": "clinical_guidelines"
})
```

### 🤖 AI Integrations (2 tools)

Healthcare AI model deployment and optimization.

#### `deploy_healthcare_model`
Deploy AI models for healthcare workflows

```python
deployment = call_tool("deploy_healthcare_model", {
    "model_type": "clinical_prediction",
    "model_config": {...},
    "deployment_target": "production"
})
```

#### `evaluate_model_performance`
Evaluate healthcare AI model performance

```python
evaluation = call_tool("evaluate_model_performance", {
    "model_id": "clinical-model-123",
    "evaluation_metrics": ["accuracy", "sensitivity", "specificity"],
    "test_dataset": "validation_set"
})
```

## Usage Patterns

### Error Handling

```python
def call_tool_safely(tool_name, arguments):
    try:
        result = call_mcp_tool(tool_name, arguments)
        if result and "error" not in result:
            return result
        else:
            print(f"Tool error: {result.get('error', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"Call failed: {e}")
        return None
```

### Batch Operations

```python
# Create multiple resources efficiently
resources_to_create = [
    {"resource_type": "Patient", "resource_data": patient1_data},
    {"resource_type": "Patient", "resource_data": patient2_data},
    {"resource_type": "Observation", "resource_data": obs_data}
]

created_resources = []
for resource_req in resources_to_create:
    result = call_tool("create_hacs_record", resource_req)
    if result:
        created_resources.append(result)
```

### Clinical Workflow Integration

```python
# Complete clinical documentation workflow
def document_patient_encounter(patient_id, encounter_data):
    # 1. Create encounter
    encounter = call_tool("create_hacs_record", {
        "resource_type": "Encounter",
        "resource_data": encounter_data
    })
    
    # 2. Record observations
    observations = []
    for vital in encounter_data.get("vitals", []):
        obs = call_tool("create_hacs_record", {
            "resource_type": "Observation",
            "resource_data": {
                **vital,
                "patient_id": patient_id,
                "encounter_id": encounter["resource_id"]
            }
        })
        observations.append(obs)
    
    # 3. Store clinical memory
    memory = call_tool("create_memory", {
        "content": encounter_data["clinical_notes"],
        "memory_type": "episodic", 
        "context_metadata": {
            "patient_id": patient_id,
            "encounter_id": encounter["resource_id"]
        }
    })
    
    return {
        "encounter": encounter,
        "observations": observations,
        "memory": memory
    }
```

## Tool Discovery

Get complete tool information programmatically:

```python
# List all available tools
tools = call_tool("list_tools", {})

# Get tool details
tool_info = call_tool("get_tool_info", {
    "tool_name": "create_hacs_record"
})

# Search tools by category
category_tools = call_tool("search_tools", {
    "category": "memory_operations"
})
```

---

For more examples and integration patterns, see [Basic Usage Guide](basic-usage.md) and [Integration Guide](integrations.md).