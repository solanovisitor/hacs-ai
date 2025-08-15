# HACS Integrations Guide

Integrate HACS packages into your healthcare AI applications. HACS provides **core packages** that integrate with AI frameworks, plus **optional service add-ons** for convenience.

> **📚 Related Documentation:**
> - [Hacs Tools Reference](healthcare-tools.md) - Complete tool documentation
> - [Basic Usage Guide](basic-usage.md) - Essential patterns and examples
> - [Quick Start Guide](quick-start.md) - Get running in 5 minutes
- LangGraph MCP examples: see `examples/hacs_developer_agent/mcp_graph.py`
> - [Developer Agent Example](../examples/hacs_developer_agent/README.md) - Complete LangGraph implementation
> - [Package Documentation](README.md#core-hacs-framework) - Individual package guides

## 🎯 **Integration Philosophy**

HACS integrates with healthcare AI systems through:

### **🧬 Core Package Integrations**
- **LangGraph**: Native tool integrations for AI agents (LangChain adapter deprecated)
- **CrewAI**: Multi-agent healthcare workflows
- **OpenAI/Anthropic**: Direct LLM provider integrations
- **Custom Frameworks**: Protocol-based integration patterns

### **⚡ Optional Service Add-ons**
- **MCP Server**: JSON-RPC interface for any language/framework
- **PostgreSQL + pgvector**: Plug-and-play persistence layer
- **Docker Services**: Quick development environment

## 🤖 **LLM Provider Integration**

HACS supports leading LLM providers with automatic configuration:

### **Anthropic Claude (Recommended)**
Claude Sonnet 4.0 is optimized for healthcare use cases:

```bash
# Configuration
export ANTHROPIC_API_KEY="sk-ant-..."
```

```python
# Usage in healthcare workflows
import requests

# Use Claude through HACS MCP tools
response = requests.post('http://localhost:8000/', json={
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "register_stack_template",
        "arguments": {
            "template_type": "assessment",
            "focus_area": "cardiology",
            "complexity_level": "comprehensive"
        }
    },
    "id": 1
})
```

### **OpenAI GPT Models**
```bash
# Configuration
export OPENAI_API_KEY="sk-..."
```

### **Model Selection for Healthcare**

| Model | Best For | HACS Support |
|-------|----------|--------------|
| **Claude Sonnet 4.0** | Clinical reasoning, complex medical analysis | ✅ Recommended |
| **GPT-4 Turbo** | General healthcare tasks, rapid responses | ✅ Supported |
| **GPT-4o** | Multimodal medical data analysis | ✅ Supported |

## 🗄️ **Database Integration**

HACS uses **PostgreSQL with pgvector** for healthcare data storage:

### **Local Development Setup**
```bash
# Automatic setup via HACS
python setup.py --mode local

# Verify database connection
docker-compose exec postgres pg_isready -U hacs
```

### **Production Configuration**
```bash
# External PostgreSQL with healthcare compliance
export DATABASE_URL="postgresql://hacs:secure_password@prod-db:5432/hacs_production"

# Enable pgvector extension
psql -d hacs_production -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### **Healthcare Data Schema**
HACS automatically creates healthcare-optimized tables:

```sql
-- Core healthcare tables
patients              -- Patient demographics and context
observations         -- Clinical measurements and findings
actors              -- Healthcare providers and permissions
memory_blocks       -- AI agent episodic/procedural memory
evidence_items     -- Clinical guidelines and research
knowledge_base     -- Structured clinical knowledge

-- Vector storage for AI operations
patient_vectors     -- Patient data embeddings
clinical_vectors    -- Clinical note embeddings
```

## 🧠 **Vector Store Integration**

HACS supports healthcare-compliant vector storage:

### **pgvector (Recommended)**
Built into PostgreSQL, ideal for healthcare compliance:

```bash
# Configuration
export VECTOR_STORE=pgvector
export DATABASE_URL="postgresql://hacs:password@localhost:5432/hacs"
```

### **Qdrant (Optional)**
For advanced vector operations:

```bash
# Configuration
export QDRANT_URL="http://localhost:6333"
export QDRANT_API_KEY="your-api-key"
```

## 🔄 **MCP Server Integration**

The **Model Context Protocol** is HACS's core integration layer:

### JSON-RPC server (secure)

- Start: `uv run python -m hacs_utils.mcp.cli`
- URL: `HACS_MCP_SERVER_URL` (e.g., `http://localhost:8000/`)
- Features: API key auth, host/CORS validation, rate limiting, health endpoints
- Clients: HTTP JSON-RPC clients, simple integrations

Note: The legacy FastMCP wrapper has been removed. Prefer the secure JSON-RPC server.

### **Available Hacs Tools (25 total)**

```python
import requests

# List all available tools
tools_response = requests.post('http://localhost:8000/', json={
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 1
})

print(f"Available tools: {len(tools_response.json()['result']['tools'])}")

# Categories of tools:
# 🔍 Resource Discovery & Development (5 tools)
# 📋 Resource Management (8 tools)
# 🧠 Memory Management (5 tools)
# ✅ Validation & Schema (3 tools)
# 🎨 Advanced Tools (3 tools)
# 📚 Knowledge Management (1 tool)
```

### **MCP Client Integration**
```python
# Integrate HACS tools with any MCP-compatible client
from hacs_utils.mcp import HacsMCPClient

client = HacsMCPClient("http://localhost:8000")

# Use Hacs Tools programmatically
patient_result = await client.call_tool("create_resource", {
    "resource_type": "Patient",
    "resource_data": {
        "full_name": "John Smith",
        "birth_date": "1980-05-15",
        "gender": "male"
    }
})
```

## 🚀 **LangGraph Agent Integration**

HACS includes a pre-built LangGraph agent for healthcare workflows:

### **Setup & Configuration**
```bash
# Navigate to agent directory
cd apps/hacs_developer_agent

# Configure for your organization
export ANTHROPIC_API_KEY="sk-ant-..."
export HACS_MCP_SERVER_URL="http://localhost:8000"
export HEALTHCARE_SYSTEM_NAME="Your Health System"

# Start agent with healthcare context
uv run langgraph dev
```

### **Healthcare Agent Capabilities**
```python
# The LangGraph agent provides:
# - Clinical memory management
# - Evidence-based reasoning
# - FHIR-compliant data handling
# - Multi-turn patient conversations
# - Structured clinical documentation

# Agent runs on http://localhost:8001
# Automatically connects to HACS MCP tools
```

## 🏥 **Healthcare System Integration**

### **Electronic Health Records (EHR)**
```python
# FHIR R4/R5 compatibility for EHR integration
from hacs_models import Patient, Observation

# Import from existing FHIR systems
fhir_patient = {
    "resourceType": "Patient",
    "name": [{"given": ["John"], "family": "Smith"}],
    "birthDate": "1980-05-15"
}

# Convert to HACS format via MCP tools
conversion_result = requests.post('http://localhost:8000/', json={
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "create_resource",
        "arguments": {
            "resource_type": "Patient",
            "resource_data": fhir_patient
        }
    },
    "id": 1
})
```

### **Clinical Decision Support Systems (CDSS)**
```python
# Integrate clinical guidelines and evidence
knowledge_result = requests.post('http://localhost:8000/', json={
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "create_knowledge_item",
        "arguments": {
            "title": "AHA Hypertension Guidelines 2024",
            "content": "For Stage 1 hypertension, initiate lifestyle modifications...",
            "knowledge_type": "guideline",
            "tags": ["hypertension", "cardiology", "aha_guidelines"]
        }
    },
    "id": 1
})
```

### **Laboratory Information Systems (LIS)**
```python
# Structure lab results for AI processing
lab_result = requests.post('http://localhost:8000/', json={
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "create_resource",
        "arguments": {
            "resource_type": "Observation",
            "resource_data": {
                "code_text": "Hemoglobin A1C",
                "value": "7.2",
                "unit": "%",
                "status": "final",
                "reference_range": "4.0-6.0"
            }
        }
    },
    "id": 1
})
```

## 📊 **Monitoring & Observability**

### **LangSmith Integration**
```bash
# Enable comprehensive AI tracing
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY="lsv2_..."
export LANGSMITH_PROJECT="healthcare_ai_system"
```

### **Health Checks**
```bash
# Monitor HACS service health
curl http://localhost:8000/  # MCP server
curl http://localhost:8001/  # LangGraph agent
docker-compose exec postgres pg_isready -U hacs  # Database
```

### **Performance Monitoring**
```python
# Built-in performance metrics via MCP tools
metrics_response = requests.post('http://localhost:8000/', json={
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "analyze_memory_patterns",
        "arguments": {
            "analysis_type": "comprehensive",
            "time_window_days": 30
        }
    },
    "id": 1
})
```

## 🔐 **Security Integration**

### **Healthcare Compliance**
```python
# Actor-based security for healthcare roles
security_config = {
    "PHYSICIAN": {
        "permissions": ["patient:*", "observation:*", "memory:*"],
        "audit_level": "full",
        "data_retention": "7_years"
    },
    "NURSE": {
        "permissions": ["patient:read", "observation:*", "memory:read"],
        "audit_level": "standard",
        "data_retention": "3_years"
    }
}
```

### **Audit Trail Integration**
```bash
# All HACS operations are automatically audited
# Logs include: actor, timestamp, operation, data_hash
# Compatible with healthcare audit requirements
```

## 🌐 **API Integration Patterns**

### **RESTful Health APIs**
```python
# Integrate with existing health APIs
import httpx

async def sync_with_ehr(patient_id: str):
    # Pull from EHR
    ehr_response = await httpx.get(f"https://ehr.hospital.com/patients/{patient_id}")

    # Store in HACS via MCP
    hacs_response = requests.post('http://localhost:8000/', json={
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "create_resource",
            "arguments": {
                "resource_type": "Patient",
                "resource_data": ehr_response.json()
            }
        },
        "id": 1
    })

    return hacs_response.json()
```

### **Webhook Integration**
```python
# Receive real-time updates from healthcare systems
from fastapi import FastAPI

app = FastAPI()

@app.post("/webhooks/lab_results")
async def handle_lab_result(lab_data: dict):
    # Process lab result through HACS
    result = requests.post('http://localhost:8000/', json={
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "create_resource",
            "arguments": {
                "resource_type": "Observation",
                "resource_data": lab_data
            }
        },
        "id": 1
    })
    return {"status": "processed", "hacs_id": result.json()["result"]["id"]}
```

## 🚀 **Production Deployment**

### **Healthcare-Ready Configuration**
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  hacs-mcp-server:
    environment:
      - DATABASE_URL=postgresql://hacs:${SECURE_PASSWORD}@prod-db:5432/hacs
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - HEALTHCARE_SYSTEM_NAME=${ORGANIZATION_NAME}
      - AUDIT_LEVEL=full
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### **Scaling Considerations**
- **Database**: Use read replicas for high query loads
- **MCP Server**: Deploy multiple instances behind load balancer
- **Vector Store**: Consider dedicated vector database for large datasets
- **Monitoring**: Implement comprehensive health checks and alerting

## 🎯 **Integration Checklist**

For healthcare organizations deploying HACS:

- [ ] **Database**: PostgreSQL with pgvector configured
- [ ] **LLM Provider**: API keys for Claude/GPT configured
- [ ] **Security**: Actor roles and permissions defined
- [ ] **Monitoring**: LangSmith tracing enabled (optional)
- [ ] **Compliance**: Audit logging configured
- [ ] **EHR Integration**: FHIR mapping tested
- [ ] **Backup**: Data backup and recovery procedures
- [ ] **Documentation**: Integration documented for your team

---

**HACS integrations are designed for healthcare environments** - secure, compliant, and optimized for clinical workflows. Start with the basic setup and add integrations as your AI capabilities grow.