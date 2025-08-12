# HACS CLI

**Command-line interface for Healthcare Agent Communication Standard**

*Currently in development - use MCP server for full functionality*

## 🚧 **Development Status**

The HACS CLI is **under development**. Current healthcare operations are available through:

1. **MCP Server** - 25+ healthcare tools via JSON-RPC (Port 8000)
2. **Setup Script** - `python setup.py` for deployment and configuration
3. **LangGraph Agent** - Interactive AI workflows (Port 8001)

## 🚀 **Current Functionality**

### **Deployment & Setup**
```bash
# Interactive setup (primary interface)
python setup.py

# Deployment modes
python setup.py --mode local     # Full development environment
python setup.py --mode minimal   # Essential services only
python setup.py --mode cloud     # Production configuration

# Specialized operations
python setup.py --migrate-only   # Database migration only
python setup.py --validate-only  # Validate existing setup
```

### **Service Management**
```bash
# Docker Compose operations
docker-compose up -d              # Start all services
docker-compose down               # Stop services
docker-compose logs hacs-mcp-server  # View logs

# Health checks
curl http://localhost:8000/       # MCP server
curl http://localhost:8001/       # LangGraph agent
```

## 🛠️ **MCP Server Interface**

All healthcare operations use the **Model Context Protocol** server:

```bash
# List available healthcare tools (25 tools)
curl -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}' \
  http://localhost:8000/

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
  http://localhost:8000/
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

def call_hacs_tool(tool_name, arguments):
    """Call HACS healthcare tools"""
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

# Clinical memory management
memory_result = call_hacs_tool("create_memory", {
    "content": "Patient shows improvement after medication adjustment",
    "memory_type": "episodic",
    "importance_score": 0.8
})

# Search clinical memories
search_result = call_hacs_tool("search_memories", {
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
