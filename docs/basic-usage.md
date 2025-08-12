# HACS Basic Usage Guide

This guide covers the essential patterns for working with HACS in healthcare environments. Learn how to use the core HACS packages and the **42+ Hacs Tools** available for clinical workflows.

> **📚 Related Documentation:**
> - [Hacs Tools Reference](healthcare-tools.md) - Complete tool documentation
> - [Integration Guide](integrations.md) - Connect to external systems  
> - [LangGraph Agent Example](../examples/hacs_developer_agent/README.md) - Working agent implementation
> - [Testing Guide](testing.md) - Validation and testing procedures

## 🏥 **Core Healthcare Models**

HACS provides healthcare-specific models optimized for AI agent communication:

```python
from hacs_models import Patient, Observation
from hacs_core import Actor, MemoryBlock, Evidence

# Healthcare provider with role-based permissions
physician = Actor(
    name="Dr. Emily Rodriguez",
    role="PHYSICIAN",
    organization="Mount Sinai Health System",
    permissions=["patient:*", "observation:*", "memory:*"],
    is_active=True
)

# Patient record with clinical context
patient = Patient(
    full_name="Sarah Johnson",
    birth_date="1985-06-15",
    gender="female",
    active=True,
    agent_context={
        "preferred_language": "english",
        "primary_concerns": ["diabetes_management", "hypertension"]
    }
)

# Clinical observation with structured data
blood_pressure = Observation(
    status="final",
    code_text="Systolic Blood Pressure",
    value="145",
    unit="mmHg",
    patient_id=patient.id,
    agent_context={
        "alert_level": "high",
        "requires_followup": True
    }
)
```

## 🛠️ **Using HACS Tools**

HACS provides Hacs Tools that can be used directly in Python or through the **optional MCP Server** add-on. The MCP Server makes all tools available via JSON-RPC at the configured `HACS_MCP_SERVER_URL`.

### **Option A: Direct Python Usage (Core Packages)**

```python
from hacs_tools import create_hacs_record, get_resource
from hacs_models import Patient

# Create a patient record directly
patient = create_hacs_record(
    resource_type="Patient",
    resource_data={
        "full_name": "Maria Garcia",
        "birth_date": "1990-03-20",
        "gender": "female"
    }
)

# Use the created patient
print(f"Created patient: {patient.id}")
```

### **Option B: Via MCP Server Add-on**

The MCP server provides HTTP access to all HACS tools with built-in authentication and audit logging.

#### **Development Setup**
```bash
# 1. Configure environment (add to your .env file - development only)
echo "HACS_MCP_SERVER_URL=http://localhost:8000" >> .env
echo "HACS_ENVIRONMENT=development" >> .env
echo "HACS_DEV_MODE=true" >> .env

# 2. Generate secure API key for testing
uv run python -m hacs_utils.mcp.cli --generate-api-key

# 3. Start infrastructure
docker-compose up -d postgres qdrant

# 4. Load environment and start MCP server
source .env
export PYTHONPATH="packages/hacs-models/src:packages/hacs-core/src:packages/hacs-tools/src:packages/hacs-auth/src:packages/hacs-persistence/src:packages/hacs-registry/src:packages/hacs-utils/src:packages/hacs-infrastructure/src"
uv run python -m hacs_utils.mcp.cli

# ✅ Secure server running at $HACS_MCP_SERVER_URL with 42 tools
```

#### **Production Setup**
```bash
# 1. Generate secure API keys
uv run python -c "import secrets; print(secrets.token_urlsafe(32))" > /secrets/HACS_API_KEY.txt

# 2. Configure production environment
export HACS_ENVIRONMENT=production
export HACS_MCP_SERVER_URL=https://your-domain.com:8000
export HACS_API_KEY_FILE=/secrets/HACS_API_KEY.txt
export HACS_ALLOWED_ORIGINS=https://your-frontend.com,https://your-admin.com
export HACS_ALLOWED_HOSTS=your-domain.com
export HACS_RATE_LIMIT_PER_MINUTE=120

# 3. Start with production security
uv run python -m hacs_utils.mcp.cli
```

#### MCP Streamable HTTP (FastMCP) for MCP Adapters

Use this option when connecting MCP-native clients (e.g., `langchain-mcp-adapters`) that expect a streamable HTTP endpoint at `/mcp/`.

```bash
# Start FastMCP wrapper (serves MCP at http://127.0.0.1:8000/mcp/)
# Note: Uses default port 8000. Stop any server already bound to :8000 first.
pkill -f hacs_utils.mcp.cli || true

# Run FastMCP
uv run --with mcp --with langchain-mcp-adapters python -m hacs_utils.mcp.fastmcp_server

# Client configuration (examples)
export HACS_MCP_SERVER_URL=http://127.0.0.1:8000  # client will normalize to /mcp/
export HACS_MCP_TRANSPORT=streamable_http
```

Security note: The FastMCP wrapper is primarily for development and adapter compatibility. For production, use the secure JSON-RPC server (`python -m hacs_utils.mcp.cli`) with API key enforcement and network policies.

#### **Using the MCP API**
```python
import requests
import os

# Get MCP server configuration from environment
mcp_url = os.getenv('HACS_MCP_SERVER_URL', 'http://localhost:8000')
api_key = os.getenv('HACS_API_KEY')  # Your API key

# Set up headers for authentication
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {api_key}'  # or use 'X-HACS-API-Key': api_key
}

# Retrieve patient data via MCP server
get_response = requests.post(f'{mcp_url}/', headers=headers, json={
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "get_resource",
        "arguments": {
            "resource_type": "Patient",
            "resource_id": "patient-123"
        }
    },
    "id": 2
})

# Validate clinical data
validation_response = requests.post(f'{mcp_url}/', headers=headers, json={
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "validate_resource_data",
        "arguments": {
            "resource_type": "Observation",
            "data": {
                "code_text": "Heart Rate",
                "value": "72",
                "unit": "bpm"
            }
        }
    },
    "id": 3
})
```

### **Memory Management**

```python
# Store clinical memory (with actor authentication)
memory_response = requests.post(f'{mcp_url}/', headers=headers, json={
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "create_hacs_memory",
        "arguments": {
            "actor_name": "Dr. Rodriguez",
            "memory_content": "Patient reports improved sleep after medication adjustment. Continue current regimen.",
            "memory_type": "episodic",
            "clinical_context": "sleep_disorders",
            "confidence_score": 0.9
        }
    },
    "id": 4
})

# Search memories semantically
search_response = requests.post(f'{mcp_url}/', headers=headers, json={
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "search_memories",
        "arguments": {
            "query": "medication side effects",
            "memory_type": "episodic",
            "limit": 5,
            "similarity_threshold": 0.7
        }
    },
    "id": 5
})

# Retrieve clinical context
context_response = requests.post(f'{mcp_url}/', headers=headers, json={
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "retrieve_context",
        "arguments": {
            "query": "diabetes management plan",
            "context_type": "clinical",
            "max_memories": 3
        }
    },
    "id": 6
})
```

### **Clinical Templates**

```python
# Generate clinical assessment template
template_response = requests.post(f'{mcp_url}/', headers=headers, json={
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "create_clinical_template",
        "arguments": {
            "template_type": "assessment",
            "focus_area": "cardiology",
            "complexity_level": "standard"
        }
    },
    "id": 7
})

# Create knowledge item for clinical guidelines
knowledge_response = requests.post(f'{mcp_url}/', headers=headers, json={
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "create_knowledge_item",
        "arguments": {
            "title": "Hypertension Management Guidelines",
            "content": "For Stage 1 hypertension (140-159/90-99 mmHg), initiate lifestyle modifications and consider ACE inhibitors.",
            "knowledge_type": "guideline",
            "tags": ["hypertension", "cardiovascular", "medication"]
        }
    },
    "id": 8
})
```

## 🔍 **Resource Discovery**

Explore available healthcare resources and their schemas:

```python
# Discover all HACS resources
models_response = requests.post(f'{mcp_url}/', headers=headers, json={
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "discover_hacs_resources",
        "arguments": {
            "category_filter": "clinical",
            "include_examples": True
        }
    },
    "id": 9
})

# Get detailed schema for Patient resource
schema_response = requests.post(f'{mcp_url}/', headers=headers, json={
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "get_hacs_resource_schema",
        "arguments": {
            "resource_type": "Patient",
            "include_validation_rules": True
        }
    },
    "id": 10
})

# Compare schemas between resources
comparison_response = requests.post(f'{mcp_url}/', headers=headers, json={
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "compare_resource_schemas",
        "arguments": {
            "model_names": ["Patient", "Observation"],
            "comparison_focus": "fields"
        }
    },
    "id": 11
})
```

## 🏥 **Complete Clinical Workflow**

Here's a complete example of a clinical encounter workflow:

```python
import requests
import os
from datetime import datetime

base_url = os.getenv('HACS_MCP_SERVER_URL', 'http://localhost:8000/')
api_key = os.getenv('HACS_API_KEY')

def use_tool(tool_name, arguments):
    """Helper function to call MCP tools"""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    response = requests.post(base_url, headers=headers, json={
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        },
        "id": 1
    })
    return response.json()

# 1. Create patient
patient_data = {
    "resource_type": "Patient",
    "resource_data": {
        "full_name": "Robert Chen",
        "birth_date": "1975-09-12",
        "gender": "male"
    }
}
patient_result = use_tool("create_resource", patient_data)
patient_id = patient_result["result"]["resource_id"]

# 2. Record vital signs
vitals_data = {
    "resource_type": "Observation",
    "resource_data": {
        "code_text": "Blood Pressure",
        "value": "150/95",
        "unit": "mmHg",
        "patient_id": patient_id,
        "status": "final"
    }
}
vitals_result = use_tool("create_resource", vitals_data)

# 3. Store clinical assessment
assessment_memory = {
    "content": f"Patient {patient_id} presents with elevated BP (150/95). Stage 1 hypertension. Recommended lifestyle modifications and follow-up in 2 weeks.",
    "memory_type": "episodic",
    "importance_score": 0.9,
    "tags": ["hypertension", "assessment", "follow_up_needed"]
}
memory_result = use_tool("create_memory", assessment_memory)

# 4. Create clinical knowledge
guideline_knowledge = {
    "title": "Stage 1 Hypertension Management",
    "content": "For patients with Stage 1 hypertension, initial treatment should focus on lifestyle modifications including diet, exercise, and stress management.",
    "knowledge_type": "guideline",
    "tags": ["hypertension", "stage_1", "lifestyle"]
}
knowledge_result = use_tool("create_knowledge_item", guideline_knowledge)

# 5. Search for related cases
search_result = use_tool("search_memories", {
    "query": "hypertension management",
    "memory_type": "episodic",
    "limit": 3
})

print("✅ Complete clinical workflow executed successfully!")
print(f"📋 Patient ID: {patient_id}")
print(f"🧠 Memory stored: {memory_result['result']['memory_id']}")
print(f"📚 Knowledge created: {knowledge_result['result']['knowledge_id']}")
```

## 📊 **Available Tool Categories**

HACS provides **25 Hacs Tools** organized into categories:

### 🔍 **Resource Discovery & Development** (5 tools)
- `discover_hacs_resources` - Explore healthcare resources
- `analyze_model_fields` - Field analysis and validation
- `compare_model_schemas` - Schema comparison
- `create_clinical_template` - Clinical workflow templates
- `create_model_stack` - Complex data composition

### 📋 **Resource Management** (8 tools)
- `create_resource` / `get_resource` / `update_resource` / `delete_resource` - Full CRUD
- `validate_resource_data` - Data validation
- `list_available_resources` - Resource catalog
- `find_resources` - Semantic search
- `search_hacs_records` - Filtered search

### 🧠 **Memory Management** (5 tools)
- `create_memory` - Store clinical memories
- `search_memories` - Semantic memory search
- `consolidate_memories` - Memory consolidation
- `retrieve_context` - Context retrieval
- `analyze_memory_patterns` - Pattern analysis

### ✅ **Validation & Schema** (3 tools)
- `get_resource_schema` - Schema exploration
- `create_view_model_schema` - Custom views
- `suggest_view_fields` - Field suggestions

### 🎨 **Advanced Tools** (3 tools)
- `optimize_model_for_llm` - LLM optimization
- `version_hacs_model` - Model versioning

### 📚 **Knowledge Management** (1 tool)
- `create_knowledge_item` - Clinical guidelines

## 🔐 **Security & Authentication**

HACS implements comprehensive security for healthcare environments:

### **API Authentication**
```bash
# Generate secure API keys
uv run python -m hacs_utils.mcp.cli --generate-api-key

# Use Bearer token authentication
curl -X POST "$HACS_MCP_SERVER_URL/" \
  -H "Authorization: Bearer your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'

# Alternative: X-HACS-API-Key header
curl -X POST "$HACS_MCP_SERVER_URL/" \
  -H "X-HACS-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

### **Environment-Based Security**
```bash
# Development (relaxed security)
export HACS_ENVIRONMENT=development
export HACS_DEV_MODE=true  # Optional auth, permissive CORS

# Production (strict security)
export HACS_ENVIRONMENT=production
export HACS_API_KEY_FILE=/secrets/api_keys.txt  # Required auth
export HACS_ALLOWED_ORIGINS=https://your-app.com  # CORS restrictions
export HACS_ALLOWED_HOSTS=your-domain.com  # Host validation
export HACS_RATE_LIMIT_PER_MINUTE=120  # Rate limiting
```

### **Health & Monitoring**
```bash
# Health check (no auth required)
curl "$HACS_MCP_SERVER_URL/health"

# Readiness check (no auth required)
curl "$HACS_MCP_SERVER_URL/ready"
```

### **Actor-Based Permissions**
```python
# Define healthcare roles with specific permissions
roles = {
    "PHYSICIAN": {
        "permissions": ["patient:*", "observation:*", "memory:*", "evidence:*"],
        "audit_level": "full"
    },
    "NURSE": {
        "permissions": ["patient:read", "observation:*", "memory:read"],
        "audit_level": "standard"
    },
    "TECHNICIAN": {
        "permissions": ["observation:create", "observation:read"],
        "audit_level": "basic"
    }
}

# All operations are audited and tracked
actor = Actor(
    name="Dr. Sarah Kim",
    role="PHYSICIAN",
    organization="Mount Sinai Health System",
    session_id="session-2024-001"
)
```

## 🚀 **Performance Considerations**

HACS is optimized for healthcare workloads:

- **Resource Operations**: <50ms average response time
- **Memory Search**: <100ms for semantic queries
- **Tool Execution**: <200ms for complex operations
- **Validation**: <10ms for schema validation

For high-throughput scenarios, consider:
- Batch operations for multiple resources
- Async requests for non-blocking workflows
- Connection pooling for database operations
- Caching for frequently accessed schemas

## 📈 **Next Steps**

1. **Integration**: Connect HACS to your existing healthcare systems
2. **Customization**: Create organization-specific clinical templates
3. **Scaling**: Deploy in production with external PostgreSQL
4. **LangGraph**: Build AI agents using the LangGraph integration

For production deployment, see the [Integration Guide](integrations.md) and [Testing Guide](testing.md) documentation.