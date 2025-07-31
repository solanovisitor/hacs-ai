# HACS Admin Agent

A comprehensive LangGraph-based admin agent specialized for HACS (Healthcare Agent Communication Standard) system administration and database management.

## 🎯 Overview

The HACS Admin Agent is a production-ready AI agent that helps HACS developers and administrators manage their HACS services, including:

- **Database Administration** - Migrations, schema management, and database health monitoring
- **System Configuration** - Resource management, schema optimization, and service setup  
- **Data Management** - Record operations, data quality assurance, and bulk operations
- **Vector Store Management** - Embedding operations, semantic search, and vector optimization
- **DevOps Operations** - Deployment automation, environment management, and infrastructure

## 🏗️ Architecture

The agent uses a specialized subagent architecture with 5 admin-focused subagents:

- **Database Admin Specialist** - Database migrations, schema management, DB health
- **System Config Specialist** - HACS resource configuration and service optimization
- **Data Management Specialist** - Data operations, quality assurance, record management
- **Vector Store Specialist** - Vector operations, semantic search, embedding management
- **DevOps Specialist** - Deployment automation, environment setup, infrastructure

## 🚀 Quick Start

### Prerequisites

1. **Python 3.11+** with `uv` package manager
2. **HACS packages** installed in the workspace
3. **LangGraph CLI** for development server

### Installation

```bash
# Navigate to the agent directory
cd examples/hacs_deep_agent

# Install dependencies (will use uv.lock)
uv sync

# Verify installation
uv run python -c "from agent import create_hacs_deep_agent; print('✅ Agent loads successfully')"
```

### Running the Agent

#### Option 1: LangGraph Studio (Recommended)

```bash
# Start the LangGraph development server with Studio UI
uv run langgraph dev

# Access the Studio UI at:
# 🎨 Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
# 📚 API Docs: http://127.0.0.1:2024/docs
```

The Studio UI provides a visual interface to:
- Create and manage conversations
- Monitor agent execution steps
- View tool calls and results
- Debug agent behavior

#### Option 2: Direct Python Usage

```python
from agent import create_hacs_deep_agent

# Create the admin agent
agent = create_hacs_deep_agent()

# Use it directly
result = agent.invoke({
    "messages": [{"role": "user", "content": "Check the database migration status"}]
})
```

#### Option 3: API Server

```bash
# Start just the API server (no browser UI)
uv run langgraph dev --no-browser --port 8123

# Then use curl or any HTTP client
curl -X POST "http://localhost:8123/threads" -H "Content-Type: application/json" -d '{}'
```

## 🛠️ Admin Operations

### Database Management

```bash
# Example queries you can ask the agent:
"Run database migration for development environment"
"Check migration status and validate all schemas"
"Show me the Patient table structure"
"Test database connectivity"
```

### System Configuration

```bash
"Discover available HACS resources"
"Create a resource stack for clinical workflows"
"Optimize the Observation resource schema"
"Compare Patient and Practitioner resource schemas"
```

### Data Operations

```bash
"Create a new patient record for testing"
"Search for observations from the last week"
"Validate data quality for all patient records"
"Export patient data in FHIR format"
```

### Vector Store Management

```bash
"Set up vector store for semantic search"
"Optimize vector collection performance"
"Store embeddings for clinical notes"
"Search for similar patient cases"
```

## 🔧 Configuration

### Environment Variables

```bash
# Required for database operations
export DATABASE_URL="postgresql://user:pass@localhost:5432/hacs_db"

# Optional: Configure AI model provider
export ANTHROPIC_API_KEY="your-api-key"  # For Claude models
export OPENAI_API_KEY="your-api-key"     # For OpenAI models
```

### Custom Configuration

```python
# Create agent with custom configuration
config = {
    "primary_actor": "Database Admin Team",
    "admin_instructions": "Focus on database administration and system health",
    "additional_tools": [custom_tool1, custom_tool2]
}

agent = create_hacs_deep_agent(config)
```

## 📊 Available Admin Tools

### Database Operations
- `run_database_migration` - Execute database schema migrations
- `check_migration_status` - Validate migration state and readiness
- `describe_database_schema` - Inspect database schemas and tables  
- `get_table_structure` - Get detailed table definitions
- `test_database_connection` - Verify database connectivity

### Resource Management
- `create_hacs_record` - Create new HACS resources
- `get_hacs_record` - Retrieve existing resources
- `update_hacs_record` - Modify resource data
- `delete_hacs_record` - Remove resources
- `search_hacs_records` - Query and filter resources

### Schema Operations
- `discover_hacs_resources` - Find available resource types
- `get_hacs_resource_schema` - Get resource schema definitions
- `analyze_resource_fields` - Analyze field usage and patterns
- `compare_resource_schemas` - Compare different resource types

### Vector Operations
- `store_embedding` - Store semantic embeddings
- `vector_similarity_search` - Find similar content
- `vector_hybrid_search` - Combined keyword and semantic search
- `get_vector_collection_stats` - Monitor vector store health
- `optimize_vector_collection` - Optimize search performance

## 🔒 Security & Permissions

The agent implements Actor-based authorization with granular permissions:

- **`admin:*`** - Full administrative access
- **`admin:migration`** - Database migration operations
- **`admin:schema`** - Schema inspection and analysis
- **`admin:database`** - Database administration
- **`admin:config`** - System configuration management

## 🐛 Troubleshooting

### Common Issues

1. **"Module not found" errors**
   ```bash
   # Ensure you're in the correct directory and dependencies are installed
   cd examples/hacs_deep_agent
   uv sync
   ```

2. **Database connection errors**
   ```bash
   # Verify DATABASE_URL is set and database is accessible
   echo $DATABASE_URL
   # Test connection: uv run python -c "import psycopg; print('DB accessible')"
   ```

3. **Permission errors**
   ```bash
   # Ensure the Actor has proper admin permissions
   # Check that actor.has_permission("admin:*") returns True
   ```

4. **LangGraph server issues**
   ```bash
   # Clean restart the server
   uv run langgraph dev --no-reload
   ```

### Debug Mode

```bash
# Enable detailed logging
uv run langgraph dev --server-log-level DEBUG

# Enable debugging with IDE integration
uv run langgraph dev --debug-port 5678 --wait-for-client
```

## 📈 Performance Optimization

- **Database**: Use connection pooling and prepared statements
- **Vector Search**: Optimize embedding dimensions and index settings
- **Memory**: Monitor state size and implement state pruning
- **Concurrency**: Configure `n-jobs-per-worker` based on system resources

## 🤝 Contributing

1. Follow the existing agent patterns and subagent structure
2. Add comprehensive permission checks to new admin tools
3. Include proper error handling and audit logging
4. Write tests for new functionality
5. Update documentation for new features

## 📝 License

Apache 2.0 - See LICENSE file for details. 