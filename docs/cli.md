# HACS CLI Reference

The HACS CLI is currently **in development**. Most HACS functionality is available through the **MCP server** and interactive setup process.

## 🚀 **Primary Interface: MCP Server**

HACS operations are primarily performed through the **Model Context Protocol (MCP)** server, which provides 42+ Hacs Tools via JSON-RPC.

### **Setup and Deployment**
```bash
# Interactive setup (recommended)
python setup.py

# Specific deployment modes
python setup.py --mode local     # Full development environment
python setup.py --mode minimal   # Essential services only
python setup.py --mode cloud     # Production configuration

# Specialized operations
python setup.py --migrate-only   # Database migration only
python setup.py --validate-only  # Validate existing setup
```

### **Service Management**
```bash
# Start/stop services
docker-compose up -d              # Start all services
docker-compose down               # Stop all services
docker-compose logs hacs-mcp-server  # View MCP server logs

# Health checks
curl http://localhost:8000/       # MCP server status
curl http://localhost:8001/       # LangGraph agent status
docker-compose exec postgres pg_isready -U hacs  # Database status
```

## 🛠️ **MCP Tools Interface**

All healthcare operations are available through MCP tools. Use HTTP requests or the Python client:

### **Resource Management**
```bash
# Create a patient record
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

# List available tools
curl -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}' \
  http://localhost:8000/
```

### **Memory Operations**
```bash
# Store clinical memory
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "create_memory",
      "arguments": {
        "content": "Patient reports improved sleep after medication adjustment",
        "memory_type": "episodic",
        "importance_score": 0.8
      }
    },
    "id": 1
  }' \
  http://localhost:8000/

# Search memories
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "search_memories",
      "arguments": {
        "query": "medication side effects",
        "limit": 5
      }
    },
    "id": 1
  }' \
  http://localhost:8000/
```

### **Clinical Templates**
```bash
# Generate clinical assessment template
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "register_stack_template",
      "arguments": {
        "template_type": "assessment",
        "focus_area": "cardiology"
      }
    },
    "id": 1
  }' \
  http://localhost:8000/
```

## 🐍 **Python Interface**

For programmatic access, use the Python requests library:

```python
import requests

def use_hacs_tool(tool_name, arguments):
    """Helper function to call HACS MCP tools"""
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

# Example usage
patient_result = use_hacs_tool("create_resource", {
    "resource_type": "Patient",
    "resource_data": {
        "full_name": "Maria Rodriguez",
        "birth_date": "1985-03-20",
        "gender": "female"
    }
})

memory_result = use_hacs_tool("create_memory", {
    "content": "Patient reports no adverse reactions to new medication",
    "memory_type": "episodic",
    "importance_score": 0.7
})
```

## 📋 **Available Tools by Category**

HACS provides **42 Hacs Tools** organized into functional categories:

### 🔍 **Resource Discovery & Development** (5 tools)
- `discover_hacs_resources` - Explore available healthcare resources
- `analyze_model_fields` - Analyze model field structure
- `compare_model_schemas` - Compare multiple model schemas
- Template tools: `register_stack_template`, `generate_stack_template_from_markdown`, `instantiate_stack_template`
- `create_model_stack` - Compose complex data structures

### 📋 **Resource Management** (8 tools)
- `create_resource` - Create new healthcare resources
- `get_resource` - Retrieve existing resources
- `update_resource` - Modify existing resources
- `delete_resource` - Remove resources
- `validate_resource_data` - Validate resource data
- `list_available_resources` - List resource types
- `find_resources` - Search for specific resources
- `search_hacs_records` - Advanced record search

### 🧠 **Memory Management** (5 tools)
- `create_memory` - Store clinical memories
- `search_memories` - Search stored memories
- `consolidate_memories` - Merge related memories
- `retrieve_context` - Get relevant context
- `analyze_memory_patterns` - Analyze memory usage

### ✅ **Validation & Schema** (3 tools)
- `get_resource_schema` - Get schema information
- `create_view_model_schema` - Create custom views
- `suggest_view_fields` - Get field suggestions

### 🎨 **Advanced Tools** (3 tools)
- `optimize_model_for_llm` - Optimize for LLM usage
- `version_hacs_model` - Manage model versions

### 📚 **Knowledge Management** (1 tool)
- `create_knowledge_item` - Store clinical knowledge

## 🛠️ **Environment Management**

### **Virtual Environment**
```bash
# Activate HACS environment
source .venv/bin/activate

# Check environment status
which python
pip list | grep hacs
```

### **Docker Services**
```bash
# Check service status
docker-compose ps

# View logs for specific service
docker-compose logs hacs-mcp-server
docker-compose logs postgres
docker-compose logs qdrant  # if using Qdrant

# Restart services
docker-compose restart hacs-mcp-server
```

### **Database Management**
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U hacs -d hacs

# Check database tables
docker-compose exec postgres psql -U hacs -d hacs -c "\dt"

# Run database migrations manually
python -m hacs_persistence.migrations $DATABASE_URL
```

## 🔍 **Troubleshooting**

### **Common Issues**

**MCP Server Not Responding**
```bash
# Check if server is running
curl http://localhost:8000/

# Check server logs
docker-compose logs hacs-mcp-server

# Restart server
docker-compose restart hacs-mcp-server
```

**Database Connection Issues**
```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready -U hacs

# View database logs
docker-compose logs postgres

# Reset database
docker-compose down -v
python setup.py --mode local
```

**Port Conflicts**
```bash
# Check what's using ports
lsof -i :8000  # MCP server
lsof -i :8001  # LangGraph agent
lsof -i :5432  # PostgreSQL

# Kill processes using ports
kill -9 $(lsof -t -i:8000)
```

### **Health Check Commands**
```bash
# Complete system health check
echo "🔍 HACS System Health Check"
echo "=========================="

echo "📡 MCP Server:"
curl -s http://localhost:8000/ && echo "✅ Running" || echo "❌ Not responding"

echo "🤖 LangGraph Agent:"
curl -s http://localhost:8001/ && echo "✅ Running" || echo "❌ Not responding"

echo "🗄️ PostgreSQL:"
docker-compose exec postgres pg_isready -U hacs && echo "✅ Ready" || echo "❌ Not ready"

echo "🐳 Docker Services:"
docker-compose ps
```

## 📊 **Performance Monitoring**

### **MCP Tool Performance**
```bash
# Time a simple tool call
time curl -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}' \
  http://localhost:8000/

# Monitor tool execution
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "analyze_memory_patterns",
      "arguments": {"analysis_type": "comprehensive"}
    },
    "id": 1
  }' \
  http://localhost:8000/
```

### **Database Performance**
```bash
# Check database statistics
docker-compose exec postgres psql -U hacs -d hacs -c "
SELECT
  schemaname,
  tablename,
  n_tup_ins as inserts,
  n_tup_upd as updates,
  n_tup_del as deletes
FROM pg_stat_user_tables;"
```

## 🚀 **Development Workflow**

### **Typical Development Session**
```bash
# 1. Start HACS services
python setup.py --mode local

# 2. Activate environment
source .venv/bin/activate

# 3. Test MCP server
curl http://localhost:8000/

# 4. Work with healthcare data
# Use MCP tools via HTTP or Python

# 5. Monitor logs
docker-compose logs -f hacs-mcp-server

# 6. Stop services when done
docker-compose down
```

### **Organization Setup**
```bash
# Configure for your healthcare organization
export HACS_ORGANIZATION="your_health_system"
export HEALTHCARE_SYSTEM_NAME="Your Health System Name"
export DATABASE_URL="postgresql://hacs:password@localhost:5432/hacs_your_org"

# Run setup with organization context
python setup.py --mode local
```

## 📚 **CLI Development Status**

### **Current Status**
The traditional HACS CLI (`hacs` command) is under development. Current functionality includes:

- ✅ **Setup & Deployment**: `python setup.py` with multiple modes
- ✅ **MCP Server**: 42+ Hacs Tools via HTTP/JSON-RPC
- ✅ **Service Management**: Docker Compose integration
- ✅ **Environment**: UV-based package management

### **Planned CLI Features**
Future CLI development will include:

- `hacs validate` - Resource validation
- `hacs convert` - Format conversion (HACS ↔ FHIR)
- `hacs memory` - Memory management commands
- `hacs evidence` - Evidence and knowledge management
- `hacs auth` - Authentication and permissions

### **Alternative Access Methods**
Until the CLI is complete, use these alternatives:

1. **MCP Tools**: Full functionality via HTTP requests
2. **Python API**: Direct integration with HACS packages
3. **LangGraph Agent**: Interactive healthcare AI workflows
4. **Web Interface**: (Planned) browser-based management

---

**For immediate healthcare AI development, use the MCP server interface** - it provides complete access to all HACS functionality through a standardized protocol.