# HACS Developer Agent

A LangGraph-based agent for HACS development, administration, and healthcare AI workflows. The agent connects to a HACS MCP server for tool execution and supports multiple LLM providers.

## 🚀 Quick Start

### 1. Prerequisites

- **Python 3.11+** with UV package manager
- **Running HACS Services**: PostgreSQL database and HACS MCP server
- **API Keys**: At least one LLM provider (OpenAI or Anthropic)

### 2. Start HACS Infrastructure

From the project root:

```bash
# Start PostgreSQL + HACS MCP Server
docker-compose up -d postgres hacs-mcp-server

# Verify services are healthy
docker-compose ps
curl http://localhost:8000/ -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

Required environment variables:
```bash
# At least one LLM API key
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# HACS MCP Server (should match docker-compose)
HACS_MCP_SERVER_URL=http://localhost:8000

# Database (optional - uses MCP server's database by default)
DATABASE_URL=postgresql://hacs:hacs_dev@localhost:5432/hacs
```

### 4. Run the Agent

Choose your preferred mode:

#### **A. Interactive Development Mode**
```bash
cd examples/hacs_developer_agent
uv run langgraph dev --host 0.0.0.0 --port 8001 --allow-blocking
```

#### **B. Python Script Mode**
```python
# Create run_agent.py
from agent import create_hacs_agent

agent = create_hacs_agent()
result = agent.invoke({"messages": [{"role": "user", "content": "Create a clinical consultation template"}]})
print(result)
```

#### **C. Production API Mode**
```bash
uv run langgraph start --host 0.0.0.0 --port 8001
```

### 5. Test the Agent

Open [http://localhost:8001](http://localhost:8001) and try:

- **"Create a geriatric consultation template"**
- **"Explore available HACS resources"**
- **"Setup database migration"**
- **"Create documentation for HACS setup"**

## 🏗️ Architecture

### Core Components

- **agent.py**: Main agent factory and LangGraph workflow
- **state.py**: Agent state management and TypedDict definitions
- **tools.py**: All available tools including HACS MCP integration
- **subagents.py**: Specialized sub-agents for domain expertise
- **prompts.py**: Agent instructions and sub-agent prompts
- **configuration.py**: Environment and API key management

### Agent Capabilities

🎯 **Planning & Organization**
- Systematic task planning with `write_todos`
- Multi-step workflow management
- Progress tracking and completion

📁 **File Management**
- Create, read, and edit files in workspace
- Build configuration files and documentation
- Generate reusable templates

🗄️ **HACS Operations**
- Discover healthcare resource types
- Create clinical templates and workflows
- Validate FHIR-compliant data structures
- Manage database migrations

👥 **Sub-Agent Delegation**
- **database-admin**: Database operations and troubleshooting
- **resource-admin**: HACS resource management and analysis
- **system-integration**: Complete system setup and configuration
- **troubleshooting**: Problem diagnosis and resolution
- **documentation**: Knowledge management and procedure creation

## 🔧 Configuration Options

### LLM Providers

The agent supports multiple LLM providers with automatic fallback:

```python
# Priority order: Anthropic → OpenAI
config = Configuration()
config.anthropic_api_key = "your_key"  # Preferred
config.openai_api_key = "your_key"     # Fallback
```

### Database & Vector Store

Choose your backend services:

```bash
# Local PostgreSQL with pgvector (default)
DATABASE_URL=postgresql://hacs:hacs_dev@localhost:5432/hacs

# Remote PostgreSQL
DATABASE_URL=postgresql://user:pass@remote-host:5432/hacs

# Alternative vector stores via configuration
QDRANT_URL=http://localhost:6333
PINECONE_API_KEY=your_pinecone_key
```

### HACS MCP Server

Configure the tool execution backend:

```bash
# Local MCP server (default)
HACS_MCP_SERVER_URL=http://localhost:8000

# Remote MCP server
HACS_MCP_SERVER_URL=https://your-hacs-api.com

# Custom authentication
HACS_API_KEY=your_custom_key
```

## 📚 Usage Examples

### Creating Healthcare Templates

```python
# The agent automatically uses planning and delegation
user_input = "Create a comprehensive cardiology consultation template"

# Agent will:
# 1. Plan the task with write_todos
# 2. Delegate to resource-admin sub-agent
# 3. Use HACS tools to discover cardiology resources
# 4. Generate FHIR-compliant template
# 5. Document the process
```

### Database Administration

```python
user_input = "Set up a new HACS database with all migrations"

# Agent will:
# 1. Plan database setup steps
# 2. Delegate to database-admin sub-agent  
# 3. Run migration tools via MCP server
# 4. Validate schema integrity
# 5. Create admin documentation
```

### System Integration

```python
user_input = "Configure complete HACS environment for production"

# Agent will:
# 1. Create comprehensive integration plan
# 2. Delegate to system-integration sub-agent
# 3. Setup database, MCP server, and vector store
# 4. Validate all components
# 5. Generate deployment documentation
```

## 🐛 Troubleshooting

### Common Issues

**MCP Server Connection Failed**
```bash
# Check if MCP server is running
curl http://localhost:8000/

# Restart MCP server
docker-compose restart hacs-mcp-server
```

**No LLM API Key**
```bash
# Verify environment variables
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Update .env file
nano .env
```

**Database Connection Issues**
```bash
# Check PostgreSQL status
docker-compose ps postgres

# Test database connection
docker exec hacs-postgres psql -U hacs -d hacs -c "SELECT 1;"
```

**Agent Performance Issues**
- Reduce context window with simpler prompts
- Use sub-agent delegation for complex tasks
- Check MCP server health and response times

### Debug Mode

Enable detailed logging:

```bash
# Set debug environment
export LOG_LEVEL=DEBUG
export LANGCHAIN_TRACING_V2=true

# Run with verbose output
uv run langgraph dev --verbose
```

## 🔄 Development Workflow

### Adding New Tools

1. Add tool function to `tools.py`
2. Include in `get_available_tools()` list
3. Update relevant sub-agent tool lists in `subagents.py`
4. Test with MCP server integration

### Customizing Sub-Agents

1. Add new prompts to `prompts.py`
2. Define sub-agent in `subagents.py`
3. Specify tool access and capabilities
4. Update task delegation logic

### Extending Configuration

1. Add new config fields to `configuration.py`
2. Update environment variable loading
3. Add validation and fallback logic
4. Document in README and .env.example

## 📈 Production Deployment

### LangGraph Platform

Deploy to LangGraph Cloud:

```bash
# Configure for production
langgraph deploy --config langgraph.json

# Use runtime secrets for API keys
langgraph secrets set OPENAI_API_KEY=your_key
```

### Custom Deployment

Run as a service:

```bash
# Create systemd service
sudo systemctl enable hacs-agent
sudo systemctl start hacs-agent

# Monitor logs
journalctl -u hacs-agent -f
```

## 🤝 Contributing

1. Follow the simplified file structure
2. Keep core functionality in designated files
3. Use sub-agent delegation for specialized tasks
4. Add comprehensive tests for new features
5. Update documentation and examples

## 📄 License

Part of the HACS (Healthcare Agent Communication Standard) project.