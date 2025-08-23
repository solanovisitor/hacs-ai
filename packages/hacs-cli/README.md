# HACS CLI

**Command-line interface for Healthcare Agent Communication Standard**

*Currently in development - use MCP server for full functionality*

## 🚧 **Development Status**

The HACS CLI is **under development**. Current healthcare operations are available through:

1. **MCP Server** - HACS tools via JSON-RPC
2. **Docker Compose** - Infrastructure deployment and configuration
3. **LangGraph Agent** - Interactive AI workflows via examples

## 🚀 **Current Functionality**

### **Deployment & Setup**
```bash
# Start infrastructure with Docker Compose
docker-compose up -d

# Manual MCP server startup
python -m hacs_utils.mcp.cli

# FastMCP server for streamable HTTP
python -m hacs_utils.mcp.fastmcp_server

# Environment configuration (choose providers you use)
export HACS_MCP_SERVER_URL=http://127.0.0.1:8000
export DATABASE_URL=postgresql://hacs:hacs_dev@localhost:5432/hacs
export OPENAI_API_KEY=...
export ANTHROPIC_API_KEY=...
```

### **Service Management**
```bash
# Docker Compose operations
docker-compose up -d              # Start all services
docker-compose down               # Stop services
docker-compose logs hacs-mcp-server  # View logs

# Health checks
curl $HACS_MCP_SERVER_URL         # MCP server
curl http://localhost:8001/       # LangGraph agent (if running)
```

## 🛠️ **MCP Server Interface**

All healthcare operations use the **Model Context Protocol** server:

```bash
# List available HACS tools
curl -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}' \
  $HACS_MCP_SERVER_URL

# Create patient record
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "create_resource",
      "arguments": {
        "resource_type": "Patient",
        "resource_data": {
          "full_name": "John Smith",
          "birth_date": "1980-05-15",
          "gender": "male"
        }
      }
    },
    "id": 1
  }' \
  $HACS_MCP_SERVER_URL
```

## 📋 **Planned CLI Features**

Future development will include:

- `hacs validate` - Resource validation
- `hacs convert` - Format conversion (HACS ↔ FHIR)
- `hacs memory` - Memory management commands
- `hacs evidence` - Evidence and knowledge operations
- `hacs auth` - Authentication and permissions
- `hacs export` - Data export utilities

## 🏥 **Healthcare Workflows**

Use Python requests for programmatic access:

```python
import requests

def use_hacs_tool(tool_name, arguments):
    """Call HACS tools"""
    import os
    server_url = os.getenv('HACS_MCP_SERVER_URL', 'http://127.0.0.1:8000')
    response = requests.post(server_url, json={
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        },
        "id": 1
    })
    return response.json()

# Clinical memory management
memory_result = use_hacs_tool("create_memory", {
    "content": "Patient shows improvement after medication adjustment",
    "memory_type": "episodic",
    "importance_score": 0.8
})

# Search clinical memories
search_result = use_hacs_tool("search_memories", {
    "query": "medication response",
    "limit": 5
})
```

## ⚙️ **Configuration**

### **Environment Setup**
```bash
# Healthcare organization configuration
export HACS_ORGANIZATION="your_health_system"
export HEALTHCARE_SYSTEM_NAME="Your Health System"
export DATABASE_URL="postgresql://hacs:password@localhost:5432/hacs"

# LLM Provider (for AI operations)
export ANTHROPIC_API_KEY="sk-ant-..."  # Recommended for healthcare
export OPENAI_API_KEY="sk-..."         # Alternative
```

### **Virtual Environment**
```bash
# Activate HACS environment
source .venv/bin/activate

# Check environment status
which python
pip list | grep hacs
```

## 🔍 **Troubleshooting**

### **Common Issues**
```bash
# Check MCP server status
curl http://localhost:8000/

# View server logs
docker-compose logs hacs-mcp-server

# Restart services
docker-compose restart hacs-mcp-server
```

### **Health Checks**
```bash
# Complete system health check
echo "📡 MCP Server:"
curl -s http://localhost:8000/ && echo "✅ Running" || echo "❌ Not responding"

echo "🗄️ PostgreSQL:"
docker-compose exec postgres pg_isready -U hacs && echo "✅ Ready" || echo "❌ Not ready"
```

## 📊 **Current Tool Categories**

Available via MCP server:

- 🔍 **Resource Discovery & Development** (5 tools)
- 📋 **Record Management** (8 tools)
- 🧠 **Memory Management** (5 tools)
- ✅ **Validation & Schema** (3 tools)
- 🎨 **Advanced Tools** (3 tools)
- 📚 **Knowledge Management** (1 tool)

## 📄 **License**

Apache-2.0 License - see [LICENSE](../../LICENSE) for details.

---

**For immediate healthcare AI development, use the MCP server interface** - it provides complete access to all HACS functionality through a standardized protocol.
