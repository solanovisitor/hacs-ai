# HACS Utils

**MCP server and essential utilities for Healthcare Agent Communication Standard**

Provides the Model Context Protocol server and core utilities for healthcare AI agent integration.

## 🌐 **MCP Server**

The core HACS MCP server provides **25+ healthcare tools** via JSON-RPC:

- **Port**: 8000 (default)
- **Protocol**: Model Context Protocol (MCP)
- **Interface**: JSON-RPC 2.0
- **Tools**: Healthcare-specific operations

### **Tool Categories**
- 🔍 **Resource Discovery** - Explore healthcare resources and schemas
- 📋 **Record Management** - Full CRUD for clinical records
- 🧠 **Memory Management** - Clinical memory and context
- ✅ **Validation & Schema** - Data validation and schema tools
- 🎨 **Advanced Tools** - LLM optimization and versioning
- 📚 **Knowledge Management** - Clinical guidelines and protocols

## 🔗 **Core Integrations**

### **Database Storage**
- **PostgreSQL** - Primary database with healthcare schema
- **pgvector** - Vector storage for clinical embeddings
- **Migration Support** - Automated schema management

### **LLM Providers**
- **Anthropic Claude** - Healthcare-optimized AI (recommended)
- **OpenAI GPT** - General purpose AI models
- **Environment-based** - Auto-configuration from API keys

### **Agent Frameworks**
- **LangGraph** - AI agent workflows with memory
- **MCP Protocol** - Standard tool calling interface

## 📦 **Installation**

```bash
pip install hacs-utils
```

## 🚀 **Quick Start**

### **Start MCP Server**
```bash
# Via HACS setup
python setup.py --mode local

# MCP server runs on http://localhost:8000
curl http://localhost:8000/
```

### **Use Healthcare Tools**
```python
import requests

def call_tool(tool_name, arguments):
    """Call HACS MCP tools"""
    response = requests.post('http://localhost:8000/', json={
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        },
        "id": 1
    })
    return response.json()

# List all available tools
tools = call_tool("tools/list", {})
print(f"Available tools: {len(tools['result']['tools'])}")

# Create patient record
patient = call_tool("create_hacs_record", {
    "resource_type": "Patient",
    "resource_data": {
        "full_name": "Sarah Johnson",
        "birth_date": "1985-03-15",
        "gender": "female"
    }
})
```

## 🏥 **Healthcare Workflow Integration**

### **Clinical Memory Management**
```python
# Store clinical memory
memory_result = call_tool("create_memory", {
    "content": "Patient reports significant improvement in symptoms after medication adjustment",
    "memory_type": "episodic",
    "importance_score": 0.9,
    "tags": ["medication_response", "symptom_improvement"]
})

# Search memories
search_result = call_tool("search_memories", {
    "query": "medication adjustment outcomes",
    "memory_type": "episodic",
    "limit": 5
})
```

### **Clinical Templates**
```python
# Generate assessment template
template = call_tool("create_clinical_template", {
    "template_type": "assessment",
    "focus_area": "cardiology",
    "complexity_level": "comprehensive"
})
```

## ⚙️ **Configuration**

### **Environment Variables**
```bash
# Database
DATABASE_URL=postgresql://hacs:password@localhost:5432/hacs

# LLM Provider (choose one)
ANTHROPIC_API_KEY=sk-ant-...  # Recommended for healthcare
OPENAI_API_KEY=sk-...         # Alternative

# Vector Store
VECTOR_STORE=pgvector  # Recommended for healthcare compliance

# Organization
HACS_ORGANIZATION=your_health_system
HEALTHCARE_SYSTEM_NAME=Your Health System
```

### **MCP Server Configuration**
```python
# MCP server automatically starts with HACS setup
# Provides healthcare tools via JSON-RPC
# No additional configuration needed
```

## 🧠 **LangGraph Integration**

The optional LangGraph agent provides AI workflows with clinical memory:

```bash
# Start LangGraph agent (optional)
cd apps/hacs_developer_agent
uv run langgraph dev

# Agent runs on http://localhost:8001
# Automatically connects to MCP tools
```

## 📊 **Performance**

- **MCP Tools**: <200ms average response time
- **Memory Search**: <100ms for semantic queries
- **Record Operations**: <50ms for CRUD operations
- **Tool Discovery**: <10ms for tool listing

## 🔐 **Security Features**

- **Actor-based Security** - Role-based access control
- **Audit Trails** - Complete operation logging
- **Session Management** - Secure authentication
- **Healthcare Compliance** - HIPAA-aware design

## 🛠️ **Development**

### **Health Checks**
```bash
# Check MCP server
curl http://localhost:8000/

# List available tools
curl -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}' \
  http://localhost:8000/
```

### **Custom Tool Development**
```python
# Tools are implemented in hacs_utils/mcp/tools.py
# Follow MCP protocol standards
# Focus on healthcare-specific functionality
```

## 📄 **License**

Apache-2.0 License - see [LICENSE](../../LICENSE) for details.