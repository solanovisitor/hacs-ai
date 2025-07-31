# HACS Admin Agent

**Production-ready LangGraph agent for HACS system administration and database management**

A specialized admin assistant that provides direct access to HACS administrative operations through real tools, not mocks. Built with a simplified state architecture focused on developer interaction.

## 🎯 **Purpose**

This agent is designed for **HACS system administrators** and **developers** who need to:
- Set up and manage HACS database systems
- Perform database migrations and schema inspections
- Manage HACS resources and records
- Monitor system health and configuration

## ✨ **Key Features**

### 🗄️ **Real Database Operations**
- **Database Migrations**: Initialize or update HACS database schemas
- **Migration Status**: Check current migration state and history
- **Schema Inspection**: Detailed database table and structure analysis
- **Connection Testing**: Verify database connectivity and health

### 🔧 **Production-Ready Tools**
- **Real HACS Integration**: Direct integration with `hacs-tools` package
- **Actor-Based Security**: Proper permission checking and audit trails  
- **No Mocks**: All operations use real HACS persistence layer
- **Error Handling**: Graceful handling of database and network issues

### 🧠 **Simplified Architecture**
- **Clean State**: Only developer-relevant data in state (3 fields vs 25+)
- **Private Tracking**: Internal operations handled privately
- **Focused Interface**: Clear separation between user input and internal logic
- **Conversation-Centric**: Designed around natural language interaction

### 🔐 **Security & Audit**
- **Admin Permissions**: Proper HACS Actor system integration
- **Operation Confirmations**: Automatic confirmation for dangerous operations
- **Audit Logging**: Complete audit trails for compliance
- **Safe Defaults**: Conservative security settings by default

## 🚀 **Quick Start**

### Prerequisites
- HACS packages available in workspace (`hacs-core`, `hacs-tools`, `hacs-persistence`)
- PostgreSQL database (for real operations)
- API keys for LLM providers

### Installation & Setup

```bash
# Navigate to the admin agent
cd examples/hacs_developer_agent

# Set up environment
cp env.example .env
# Edit .env with your API keys and database URL

# Install dependencies (handled by workspace)
uv sync

# Start the admin agent
uv run langgraph dev
```

### Configuration

Set these environment variables in `.env`:

```bash
# Required: LLM API Key
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Database URL (can be provided per operation)
DATABASE_URL=postgresql://user:password@localhost:5432/hacs_db

# Optional: LangSmith tracing
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_TRACING=true
```

## 🎯 **Available Operations**

### Database Management
- **"Run database migration"** - Initialize or update HACS schemas
- **"Check migration status"** - View current database state
- **"Describe database schema"** - Inspect tables and structures

### Resource Management  
- **"Discover available resources"** - Find HACS resource types
- **"Create a Patient record"** - Create HACS resources with validation

### System Information
- **"Help"** or **"What can you do?"** - List available operations

## 🏗️ **Architecture**

### Simplified State Design

```python
# Developer Input (what you provide)
class InputState:
    admin_operation_type: str        # "migration", "schema", etc.
    operation_params: Dict           # Operation parameters
    database_url: Optional[str]      # Optional database URL

# Conversation State (minimal)
class State:
    session_id: str                  # Session tracking
    last_operation_result: Result    # Last operation result
    last_error: Optional[str]        # Simple error context

# Agent Output (what you get back)
class OutputState:
    operation_result: Result         # Operation result with success/error
    recommended_next_steps: List     # Suggested next actions
```

### Private Implementation

Internal operation details are handled privately:
- Database connection state
- Operation progress tracking  
- Retry logic and error handling
- Security and permission checks

## 🛠️ **Usage Examples**

### Database Setup
```
User: "Set up the HACS database"
Agent: Runs database migration, provides detailed results
```

### Schema Inspection
```  
User: "Show me the database tables"
Agent: Describes all HACS schemas, tables, and structures
```

### Resource Discovery
```
User: "What HACS resources are available?"
Agent: Lists all available HACS resource types with descriptions
```

### Status Checking
```
User: "Check migration status"
Agent: Provides current migration state and history
```

## ⚙️ **Configuration Options**

### Admin Settings
- `max_admin_operations: 3` - Max operations per session
- `require_confirmation: true` - Confirm dangerous operations
- `enable_audit_logging: true` - Enable audit trails
- `migration_timeout: 300` - Migration timeout (seconds)

### Security Settings
- `enable_fhir_validation: true` - Validate FHIR resources
- `max_resource_results: 50` - Limit result sizes
- Automatic admin permission assignment
- Dangerous operation detection

## 🔒 **Security Model**

### Actor-Based Permissions
```python
# Automatic admin actor creation
admin_actor = Actor(
    name="Developer Agent Admin",
    role=ActorRole.ADMINISTRATOR,
    permissions=["admin:*", "database:*", "migration:*"]
)
```

### Operation Safety
- **Dangerous Operations**: Require confirmation
  - Database migrations
  - Schema modifications  
  - Bulk deletions
- **Safe Operations**: Run immediately
  - Status checks
  - Schema inspection
  - Resource discovery

## 📊 **Development**

### Project Structure
```
hacs_developer_agent/
├── state.py           # Simplified state classes (73 lines)
├── graph.py           # LangGraph workflow (213 lines)  
├── configuration.py   # Config and private settings (161 lines)
├── tools.py           # Real HACS admin tools (2239 lines)
├── utils.py           # Utility functions (148 lines)
├── langgraph.json     # LangGraph configuration
└── README.md          # This documentation
```

### Key Design Principles
1. **Developer-Focused**: State contains only what developers interact with
2. **Production-Ready**: Real tools, proper error handling, security
3. **Admin-Specialized**: Focused on database and system operations
4. **Conversation-Driven**: Natural language interface for all operations

## 🧪 **Testing**

### Manual Testing
```bash
# Test imports and configuration
uv run python -c "import graph, state, configuration; print('✅ All modules imported')"

# Test agent startup
uv run langgraph dev
# Should start without errors and display LangGraph UI
```

### Operation Testing
1. Start the agent: `uv run langgraph dev`
2. Open LangGraph Studio UI
3. Test operations:
   - "Help" - Should list available operations
   - "Check migration status" - Should check database (may show error without DB)
   - "Discover resources" - Should list HACS resource types

## 📝 **Migration from Previous Version**

### What Changed
- **State Simplified**: 25+ complex fields → 3 essential fields
- **Real Tools**: Mock HTTP calls → Real HACS tool integration
- **Admin Focus**: General development → Database administration
- **Private Tracking**: State bloat → Private variables for internal logic
- **Production Ready**: Development mocks → Real database operations

### Upgrade Notes
- State structure completely changed (breaking change)
- Tool calls now use real HACS persistence layer
- Configuration focused on admin operations
- Requires database setup for full functionality

## 🤝 **Contributing**

This agent demonstrates production-ready patterns for:
- LangGraph agent design with simplified state
- Real tool integration without mocks
- Admin operation workflows
- Security and permission handling

## 📄 **License**

Licensed under the Apache-2.0 License - see main project LICENSE file.

---

**🎯 Ready for HACS system administration!**

This agent provides a clean, focused interface for HACS database and system management operations with production-ready tools and proper security. 