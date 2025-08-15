# HACS Tools Reference

Low-level HACS tools for resource modeling, bundles, schema discovery, memory, and minimal workflow modeling. High-level, business-specific tools have been removed; keep prompts/logic in workflows.

## Context Engineering Tool Categories

Each tool category implements specific context engineering strategies optimized for healthcare AI:

### 🔍 Resource Management (8 tools)

**🎯 SELECT + 🔒 ISOLATE Strategies**: Healthcare resource operations with selective data access and compliance boundaries.

Core CRUD operations implementing context selection and isolation for healthcare AI agents:

#### `create_hacs_record`
**🎯 SELECT**: Create healthcare resources with selective data extraction

```python
# SELECT: Create patient with only essential clinical context
patient_data = patient.model_dump(exclude={
    "text", "contained", "extension", "modifier_extension"  # Exclude FHIR overhead
})

result = use_tool("create_hacs_record", {
    "resource_type": "Patient",
    "resource_data": patient_data  # Optimized clinical context only
})
```

#### `get_resource`
Retrieve healthcare resource by ID and type

```python
patient = use_tool("get_resource", {
    "resource_type": "Patient", 
    "resource_id": "patient-123"
})
```

#### `update_resource`
Update existing healthcare resource

```python
use_tool("update_resource", {
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
use_tool("delete_resource", {
    "resource_type": "Patient",
    "resource_id": "patient-123"
})
```

#### `validate_resource_data`
Validate resource data against FHIR schemas

```python
validation = use_tool("validate_resource_data", {
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
resources = use_tool("list_available_resources", {})
```

#### `find_resources`
Semantic search across healthcare resources

```python
results = use_tool("find_resources", {
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
records = use_tool("search_hacs_records", {
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

**🖊️ WRITE + 🎯 SELECT Strategies**: Clinical memory generation and selective retrieval for healthcare AI cognition.

Clinical memory operations implementing context writing and selective memory access:

#### `create_memory`
**🖊️ WRITE**: Generate clinical memories with structured context metadata

```python
# WRITE: Generate clinical context withmetadata
memory = use_tool("create_memory", {
    "content": "Patient reports 75% reduction in chest pain after metoprolol initiation. Excellent medication tolerance.",
    "memory_type": "episodic",
    "importance_score": 0.9,  # High clinical significance
    "tags": ["medication_response", "chest_pain", "improvement", "metoprolol"],
    "context_metadata": {
        "patient_id": "patient-123",
        "encounter_type": "follow_up",
        "medication_change": "metoprolol_start",
        "outcome_measure": "symptom_improvement",
        "context_strategies_used": ["write", "select"]  # Track context engineering
    }
})
```

#### `search_memories`
Semantic search across clinical memories

```python
memories = use_tool("search_memories", {
    "query": "medication side effects",
    "memory_type": "episodic", 
    "limit": 5,
    "similarity_threshold": 0.7
})
```

#### `consolidate_memories`
Merge related memories for knowledge synthesis

```python
consolidated = use_tool("consolidate_memories", {
    "memory_ids": ["memory-1", "memory-2", "memory-3"],
    "consolidation_strategy": "thematic_synthesis"
})
```

#### `retrieve_context`
Get relevant clinical context for current task

```python
context = use_tool("retrieve_context", {
    "query": "diabetes management plan",
    "context_type": "clinical",
    "max_memories": 3
})
```

#### `analyze_memory_patterns`
Identify patterns and insights from clinical memories

```python
patterns = use_tool("analyze_memory_patterns", {
    "memory_type": "episodic",
    "analysis_focus": "patient_outcomes",
    "time_window": "last_30_days"
})
```

#### `check_memory`
Collect a filtered set of memories (episodic/procedural) for agent context

```python
context_memories = use_tool("check_memory", {
    "actor_id": actor.id,
    "memory_types": ["episodic", "procedural"],
    "min_importance": 0.6,
    "limit": 20
})
```

### 🧩 Workflow Modeling (low-level)

Adapters for creating and using `ActivityDefinition`, `PlanDefinition`, and `Task` instances.

```python
workflow = use_tool("execute_clinical_workflow", {
    "workflow_type": "diabetes_assessment",
    "patient_context": {
        "hba1c": "8.2%",
        "current_medications": ["metformin"]
    },
    "assessment_goals": ["glucose_control", "medication_optimization"]
})
```

#### Template registration and instantiation
Register and instantiate stack templates for clinical workflows

```python
result = use_tool("register_stack_template", {
    "template": {"name": "Example", "version": "1.0.0", "layers": [], "variables": {}}
})
```

#### `create_activity_definition`
Create an `ActivityDefinition` instance (adapter)

```python
validation = use_tool("validate_clinical_protocol", {
    "protocol_data": {
        "name": "Hypertension Management",
        "steps": ["assess_bp", "lifestyle_counseling", "medication_if_needed"]
    }
})
```

#### `create_plan_definition`
Create a `PlanDefinition` and add goals/actions

```python
care_plan = use_tool("generate_care_plan", {
    "patient_id": "patient-123",
    "primary_conditions": ["diabetes", "hypertension"],
    "goals": ["hba1c_reduction", "bp_control"]
})
```

### 📚 Knowledge Management (Evidence)

Context-specific tools for literature evidence. Prefer these over generic vector tools.

#### `index_evidence`
Index literature evidence with citation and content; returns structured `Evidence` with embedding reference

```python
result = use_tool("index_evidence", {
    "citation": "Smith J. Hypertension Management. NEJM (2024)",
    "content": "Guideline recommends initial therapy with ...",
    "evidence_type": "guideline",
    "tags": ["hypertension", "guideline"],
})
```

#### `check_evidence`
Retrieve semantically relevant evidence for a query

```python
evidence = use_tool("check_evidence", {
    "query": "ACE inhibitor contraindications",
    "limit": 5
})
```

> Note: Generic vector tools are deprecated in favor of context-specific tools.

### ⚕️ Schema Discovery (5 tools)

Healthcare resource schema exploration and analysis.

#### `discover_hacs_resources`
Explore available healthcare resources

```python
resources = use_tool("discover_hacs_resources", {
    "category_filter": "clinical",
    "include_examples": True
})
```

#### `get_hacs_resource_schema`
Get detailed schema for resource type

```python
schema = use_tool("get_hacs_resource_schema", {
    "resource_type": "Patient",
    "include_validation_rules": True
})
```

#### `compare_resource_schemas`
Compare schemas between resource types

```python
comparison = use_tool("compare_resource_schemas", {
    "model_names": ["Patient", "Observation"],
    "comparison_focus": "fields"
})
```

#### `analyze_model_fields`
Analyze fields in healthcare model

```python
analysis = use_tool("analyze_model_fields", {
    "model_name": "Observation", 
    "analysis_type": "comprehensive"
})
```

#### `suggest_model_fields`
Get field suggestions for models

```python
suggestions = use_tool("suggest_model_fields", {
    "model_name": "Patient",
    "use_case": "diabetes_management"
})
```

### 🛠️ Development Tools (4 tools)

Tools for developing with HACS models and resources.

#### `create_model_stack`
Compose complex healthcare data structures

```python
stack = use_tool("create_model_stack", {
    "primary_model": "Patient",
    "related_models": ["Observation", "Encounter"],
    "composition_type": "clinical_episode"
})
```

#### `generate_test_data`
Generate realistic test data for healthcare models

```python
test_data = use_tool("generate_test_data", {
    "resource_type": "Patient",
    "count": 10,
    "demographics": "diverse",
    "include_conditions": ["diabetes", "hypertension"]
})
```

#### `validate_model_composition`
Validate complex model relationships

```python
validation = use_tool("validate_model_composition", {
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
optimized = use_tool("optimize_model_for_llm", {
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
compliance = use_tool("validate_fhir_compliance", {
    "resource_data": {...},
    "fhir_version": "R4",
    "strict_validation": True
})
```

#### `convert_to_fhir`
Convert HACS models to FHIR format

```python
fhir_resource = use_tool("convert_to_fhir", {
    "hacs_resource": {...},
    "target_fhir_version": "R4"
})
```

#### `import_from_fhir`
Import FHIR resources into HACS

```python
hacs_resource = use_tool("import_from_fhir", {
    "fhir_resource": {...},
    "enhance_for_agents": True
})
```

### 📈 Healthcare Analytics (3 tools)

Population health and quality measures.

#### `calculate_quality_measures`
Calculate healthcare quality indicators

```python
measures = use_tool("calculate_quality_measures", {
    "measure_set": "diabetes_care",
    "patient_population": "all_diabetes_patients",
    "time_period": "last_12_months"
})
```

#### `generate_population_insights`
Analyze population health trends

```python
insights = use_tool("generate_population_insights", {
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
stratification = use_tool("risk_stratification", {
    "patient_cohort": "diabetes_patients",
    "risk_factors": ["hba1c", "blood_pressure", "medications"],
    "stratification_model": "clinical_guidelines"
})
```

### 🤖 AI Integrations

Removed to keep the toolset low-level and business-agnostic. Integrate AI models within workflows using hacs-utils and direct provider SDKs.

#### `deploy_healthcare_model`
Deploy AI models for healthcare workflows

```python
deployment = use_tool("deploy_healthcare_model", {
    "model_type": "clinical_prediction",
    "model_config": {...},
    "deployment_target": "production"
})
```

#### `evaluate_model_performance`
Evaluate healthcare AI model performance

```python
evaluation = use_tool("evaluate_model_performance", {
    "model_id": "clinical-model-123",
    "evaluation_metrics": ["accuracy", "sensitivity", "specificity"],
    "test_dataset": "validation_set"
})
```

## Context Engineering Usage Patterns

### Multi-Strategy Context Engineering

Combine multiple context engineering strategies for optimal healthcare AI performance:

```python
def context_engineered_clinical_workflow(patient_id, clinical_query):
    """Demonstrate all four context engineering strategies in tool usage"""
    
    # 🔒 ISOLATE: Setup healthcare AI with scoped permissions
    clinical_context = {
        "actor_permissions": ["patient:read", "observation:write", "memory:write"],
        "compliance_boundaries": ["hipaa_compliant", "audit_logged"]
    }
    
    # 🎯 SELECT: Search with selective criteria
    search_results = use_tool("search_hacs_records", {
        "query": clinical_query,
        "resource_types": ["Patient", "Observation", "MemoryBlock"],
        "importance_threshold": 0.7,  # SELECT high-importance only
        "time_window": "last_12_months",  # SELECT relevant timeframe
        "limit": 10
    })
    
    # 🗜️ COMPRESS: Generate compressed clinical context
    for result in search_results["results"]:
        if result["resource_type"] == "Patient":
            # COMPRESS: Use text summary instead of full patient data
            patient_summary = result["data"]["text_summary"]
            
            # SELECT: Extract only essential observations
            recent_obs = [
                obs for obs in result.get("related_observations", [])
                if obs.get("importance_score", 0) > 0.8
            ]
            
            # COMPRESS: Generate clinical summary
            clinical_summary = f"{patient_summary} | Recent: {len(recent_obs)} significant findings"
    
    # 🖊️ WRITE: Generate clinical context withmetadata
    clinical_memory = use_tool("create_memory", {
        "content": f"Clinical analysis for {clinical_query}: {clinical_summary}",
        "memory_type": "episodic",
        "importance_score": 0.9,
        "tags": ["context_engineered", "clinical_analysis", "ai_generated"],
        "context_metadata": {
            "patient_id": patient_id,
            "context_strategies_applied": ["isolate", "select", "compress", "write"],
            "query_complexity": "multi_resource",
            "clinical_significance": "high",
            "compression_efficiency": 0.3  # Reduced to 30% of original context
        }
    })
    
    return {
        "selected_results": search_results,
        "compressed_summary": clinical_summary,
        "written_context": clinical_memory,
        "context_isolation": clinical_context
    }
```

### Context Strategy Selection Guide

Choose appropriate context engineering strategies based on your healthcare AI use case:

| **Use Case** | **Primary Strategy** | **Secondary Strategy** | **Tool Examples** |
|--------------|---------------------|----------------------|-------------------|
| **Clinical Documentation** | 🖊️ WRITE | 🎯 SELECT | `create_memory`, `create_hacs_record` |
| **Patient Search** | 🎯 SELECT | 🗜️ COMPRESS | `search_hacs_records`, `find_similar_cases` |
| **Real-time Clinical Decision** | 🗜️ COMPRESS | 🎯 SELECT | `semantic_search_records`, `retrieve_context` |
| **Population Health Analytics** | 🗜️ COMPRESS | 🔒 ISOLATE | `calculate_quality_measures`, `risk_stratification` |
| **Care Plan Generation** | 🖊️ WRITE | 🗜️ COMPRESS | `generate_care_plan`, `execute_clinical_workflow` |
| **Regulatory Compliance** | 🔒 ISOLATE | 🎯 SELECT | `validate_fhir_compliance`, `create_hacs_record` |

### Error Handling

```python
def use_tool_safely(tool_name, arguments):
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
    result = use_tool("create_hacs_record", resource_req)
    if result:
        created_resources.append(result)
```

### Clinical Workflow Integration

```python
# Complete clinical documentation workflow
def document_patient_encounter(patient_id, encounter_data):
    # 1. Create encounter
    encounter = use_tool("create_hacs_record", {
        "resource_type": "Encounter",
        "resource_data": encounter_data
    })
    
    # 2. Record observations
    observations = []
    for vital in encounter_data.get("vitals", []):
        obs = use_tool("create_hacs_record", {
            "resource_type": "Observation",
            "resource_data": {
                **vital,
                "patient_id": patient_id,
                "encounter_id": encounter["resource_id"]
            }
        })
        observations.append(obs)
    
    # 3. Store clinical memory
    memory = use_tool("create_memory", {
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
tools = use_tool("list_tools", {})

# Get tool details
tool_info = use_tool("get_tool_info", {
    "tool_name": "create_hacs_record"
})

# Search tools by category
category_tools = use_tool("search_tools", {
    "category": "memory_operations"
})
```

---

For more examples and integration patterns, see [Basic Usage Guide](basic-usage.md) and [Integration Guide](integrations.md).