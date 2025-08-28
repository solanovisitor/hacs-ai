# Robust Supabase Connection with HACS

This guide shows how to configure robust PostgreSQL connections to Supabase using psycopg3 async patterns and proper environment variable handling across all HACS packages.

## Prerequisites

- Supabase project with PostgreSQL database
- Python 3.11+ with `uv` package manager
- HACS packages: `hacs-persistence`, `hacs-core`, `hacs-tools`, `hacs-utils`

## Environment Configuration

### 1. Set up .env file

Create a `.env` file in your project root with your Supabase connection details:

```bash
# Supabase PostgreSQL Connection (direct connection recommended)
DATABASE_URL=postgresql://postgres:your_password@db.your_project.supabase.co:5432/postgres?sslmode=require

# Alternative environment variable names (HACS supports multiple)
# HACS_DATABASE_URL=postgresql://postgres:your_password@db.your_project.supabase.co:5432/postgres?sslmode=require
# POSTGRES_URL=postgresql://postgres:your_password@db.your_project.supabase.co:5432/postgres?sslmode=require

# API Keys for LLM providers (optional)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### 2. Environment variable precedence

HACS packages check environment variables in this order:

1. `DATABASE_URL` (standard PostgreSQL convention)
2. `HACS_DATABASE_URL` (HACS-specific)
3. `POSTGRES_URL` (alternative standard)
4. `HACS_POSTGRES_URL` (HACS-specific alternative)

## Connection Patterns

### 1. Using dotenv (User Preference)

HACS respects the user preference for dotenv-based environment loading:

```python
from dotenv import dotenv_values, load_dotenv
import os

# Load environment variables from .env files
for env_file in ['.env', '.env.local']:
    if os.path.exists(env_file):
        load_dotenv(env_file, override=False)
        vals = dotenv_values(env_file)
        # Update environment with non-None values
        os.environ.update({k: v for k, v in vals.items() if v is not None})
        break
```

**Output:**
```
✓ Loaded environment from .env
✓ DATABASE_URL loaded: postgresql://postgres:****@db.auygqzlhostnliyzkrhf.supabase.co:5432/postgres?sslmode=require
```

### 2. Direct psycopg3 async connection (Best Practice)

For direct database operations, use psycopg3's async connection pattern:

```python
import asyncio
import psycopg

async def test_connection():
    database_url = os.getenv("DATABASE_URL")
    
    # Use async connection with proper context management
    async with await psycopg.AsyncConnection.connect(
        database_url,
        autocommit=True  # For DDL operations
    ) as conn:
        async with conn.cursor() as cur:
            # Test connection
            await cur.execute("SELECT version(), current_database()")
            version, db_name = await cur.fetchone()
            print(f"Connected to {db_name}: {version.split()[0]} {version.split()[1]}")
            
            # Preferred: use HACS helper instead of raw SQL
            from hacs_persistence.migrations import get_migration_status
            status = await get_migration_status()
            print("HACS schemas:", status.get('schema_breakdown'))

asyncio.run(test_connection())
```

**Output:**
```
Connected to postgres: PostgreSQL 17.4
HACS schemas: {'hacs_clinical': 22, 'hacs_core': 7, 'hacs_registry': 2}
```

### 3. HACS Adapter Pattern

For HACS resource operations, use the adapter factory:

```python
import asyncio
import os
from dotenv import dotenv_values, load_dotenv
from hacs_persistence.adapter import create_postgres_adapter
from hacs_models import Patient, Actor

# Load environment and map to HACS_DATABASE_URL
for env_file in ['.env', '.env.local']:
    if os.path.exists(env_file):
        load_dotenv(env_file, override=False)
        vals = dotenv_values(env_file)
        os.environ.update({k: v for k, v in vals.items() if v is not None})
        break

database_url = os.getenv("DATABASE_URL")
if database_url:
    os.environ["HACS_DATABASE_URL"] = database_url

async def test_hacs_adapter():
    # Factory automatically uses HACS_DATABASE_URL from environment
    adapter = await create_postgres_adapter()
    print("✓ HACS adapter created successfully")
    
    # Create actor for audit trails (required for HACS operations)
    author = Actor(
        name="app-user",
        role="system", 
        permissions=["*:write", "*:read"]
    )
    
    # Create and save a patient
    patient = Patient(
        full_name="Test Patient",
        birth_date="1990-01-01",
        gender="female"
    )
    
    saved_patient = await adapter.save(patient, author)
    print(f"Saved patient: {saved_patient.id}")
    print(f"Patient successfully persisted to database")

asyncio.run(test_hacs_adapter())
```

**Output:**
```
INFO:hacs_persistence.adapter:PostgreSQLAdapter (Async) configured for schema 'public'
INFO:hacs_persistence.adapter:HACS resources table checked/created successfully
INFO:hacs_persistence.adapter:Async connection pool established and tables initialized.
✓ HACS adapter created successfully
INFO:hacs_persistence.adapter:Resource Patient/patient-e1daa061 saved successfully
Saved patient: patient-e1daa061
Patient successfully persisted to database
```

### 4. HACS Tools with Actor Context

For HACS tools, use the new actor context pattern:

```python
import asyncio
import os
from dotenv import dotenv_values, load_dotenv
from hacs_tools.domains.modeling import pin_resource
from hacs_tools.domains.database import save_resource
from hacs_core.config import configure_hacs
from hacs_models import Actor

# Load environment and map to HACS_DATABASE_URL
for env_file in ['.env', '.env.local']:
    if os.path.exists(env_file):
        load_dotenv(env_file, override=False)
        vals = dotenv_values(env_file)
        os.environ.update({k: v for k, v in vals.items() if v is not None})
        break

database_url = os.getenv("DATABASE_URL")
if database_url:
    os.environ["HACS_DATABASE_URL"] = database_url

async def test_hacs_tools():
    # Configure actor context for tools (injected automatically)
    actor = Actor(
        name="tools-user",
        role="physician",
        permissions=["patient:read", "patient:write"]
    )
    configure_hacs(current_actor=actor)
    print("✓ Actor context configured for tools")
    
    # Create resource (uses injected actor)
    pin_result = pin_resource("Patient", {
        "full_name": "Tools Patient",
        "birth_date": "1985-03-15",
        "gender": "male"
    })
    
    if pin_result.success:
        print("✓ pin_resource succeeded")
        # Save to typed table (uses injected actor)
        save_result = await save_resource(
            resource=pin_result.data["resource"],
            as_typed=True  # Use hacs_core.patients table
        )
        
        if save_result.success:
            print("✓ Saved via tools: Resource saved successfully")

asyncio.run(test_hacs_tools())
```

**Output:**
```
INFO:hacs_registry.tool_registry:Plugin discovery complete: 62 plugins found
INFO:hacs_registry.tool_registry:Auto-discovery complete: 62 total tools registered
✓ Actor context configured for tools
✓ pin_resource succeeded
INFO:hacs_persistence.adapter:PostgreSQLAdapter (Async) configured for schema 'public'
INFO:hacs_persistence.adapter:HACS resources table checked/created successfully
INFO:hacs_persistence.adapter:Async connection pool established and tables initialized.
WARNING:hacs_tools.domains.database:Typed adapter not available, using generic storage
INFO:hacs_persistence.adapter:Resource Patient/patient-589e7f34 saved successfully
✓ Saved via tools: Resource saved successfully
```

## Migration and Schema Setup

### 1. Run migrations

Ensure your Supabase database has the correct HACS schemas:

```python
import asyncio
from hacs_persistence.migrations import get_migration_status

async def setup_database():
    # Check current status
    status = await get_migration_status()
    print(f"Migration complete: {status.get('migration_complete')}")
    print(f"Tables: {status.get('total_tables')}/{status.get('expected_tables')}")
    print(f"pgvector enabled: {status.get('pgvector_enabled')}")
    print("Schema breakdown:", status.get('schema_breakdown'))

asyncio.run(setup_database())
```

**Output:**
```
Migration complete: True
Tables: 36/23
pgvector enabled: True
Schema breakdown: {'hacs_admin': 1, 'hacs_agents': 3, 'hacs_audit': 1, 'hacs_clinical': 22, 'hacs_core': 7, 'hacs_registry': 2}
```

### 2. Verify schemas

Check that HACS schemas were created properly using HACS utilities:

```python
import asyncio
from hacs_persistence import check_hacs_tables_exist

async def verify_schemas():
    result = await check_hacs_tables_exist()
    
    if "error" in result:
        print(f"Error: {result['error']}")
        return
    
    print("HACS schemas in Supabase:")
    schemas_found = result.get("schemas_found", {})
    for schema_name, tables in schemas_found.items():
        print(f"  - {schema_name}: {len(tables)} tables")
    
    missing = result.get("missing_schemas", [])
    if missing:
        print(f"Missing schemas: {missing}")
    
    print(f"Total tables: {result.get('total_tables', 0)}")

asyncio.run(verify_schemas())
```

**Output:**
```
HACS schemas in Supabase:
  - hacs_admin: 1 tables
  - hacs_agents: 3 tables
  - hacs_audit: 1 tables
  - hacs_clinical: 22 tables
  - hacs_core: 7 tables
  - hacs_registry: 2 tables
Total tables: 36
```

## Connection Factory Pattern

HACS uses a connection factory for robust connection management:

```python
from hacs_persistence import HACSConnectionFactory

# Get adapter with automatic migration and pooling
adapter = HACSConnectionFactory.get_adapter(
    database_url=None,  # Uses DATABASE_URL from environment
    auto_migrate=False,  # Skip migration for this example
    pool_size=10        # Connection pool size
)

print(f"Adapter created: {type(adapter).__name__}")
print(f"Adapter schema: {adapter.schema_name}")
print(f"Connection pool configured with 10 connections")
```

**Output:**
```
INFO:hacs_persistence.adapter:PostgreSQLAdapter (Async) configured for schema 'public'
INFO:hacs_persistence.connection_factory:Created database adapter for schema 'public'
Adapter created: PostgreSQLAdapter
Adapter schema: public
Connection pool configured with 10 connections
```

## Error Handling and Troubleshooting

### Common Connection Issues

### Comprehensive Environment Verification

Use the new database utilities for complete environment and connection verification:

```python
import asyncio
from hacs_persistence import verify_database_environment

async def check_environment():
    result = await verify_database_environment()
    
    print("🔧 Environment Variables:")
    for var, status in result["environment_variables"].items():
        print(f"  {var}: {status}")
    
    if result["database_url_source"]:
        print(f"\n📊 Using database URL from: {result['database_url_source']}")
    
    connection = result.get("connection_test", {})
    if "error" not in connection:
        print(f"\n✅ Database Connection:")
        print(f"  Status: {connection['status']}")
        print(f"  PostgreSQL: {connection['postgresql_version']}")
        print(f"  Database: {connection['database_name']}")
        print(f"  Host: {connection['connection']['host']}")
        print(f"  SSL: {connection['connection']['ssl_mode']}")
    else:
        print(f"\n❌ Connection Error: {connection['error']}")
    
    schemas = result.get("hacs_schemas", {})
    if schemas and "error" not in schemas:
        print(f"\n🏥 HACS Schemas:")
        for schema, count in schemas["hacs_schemas"].items():
            print(f"  - {schema}: {count} tables")
        print(f"  Migration complete: {schemas['migration_complete']}")
        print(f"  pgvector enabled: {schemas['pgvector_enabled']}")
    
    if result["recommendations"]:
        print(f"\n💡 Recommendations:")
        for rec in result["recommendations"]:
            print(f"  - {rec}")

asyncio.run(check_environment())
```

**Output:**
```
🔧 Environment Variables:
  DATABASE_URL: ✓ Set
  HACS_DATABASE_URL: ✗ Not set
  POSTGRES_URL: ✗ Not set
  HACS_POSTGRES_URL: ✗ Not set

📊 Using database URL from: DATABASE_URL

✅ Database Connection:
  Status: connected
  PostgreSQL: PostgreSQL 17.4
  Database: postgres
  Host: db.auygqzlhostnliyzkrhf.supabase.co
  SSL: require

🏥 HACS Schemas:
  - hacs_admin: 1 tables
  - hacs_agents: 3 tables
  - hacs_audit: 1 tables
  - hacs_clinical: 22 tables
  - hacs_core: 7 tables
  - hacs_registry: 2 tables
  Migration complete: True
  pgvector enabled: True
```

2. **SSL Connection Issues**:
```bash
# Ensure your DATABASE_URL includes sslmode=require for Supabase
DATABASE_URL=postgresql://postgres:password@db.project.supabase.co:5432/postgres?sslmode=require
```

3. **Schema Not Found**:
```python
# Run migrations to create HACS schemas
from hacs_persistence.migrations import run_migration
import asyncio

asyncio.run(run_migration())
```

### Validation Script

Use the provided validation script to test your connection:

```bash
cd /path/to/hacs-ai
uv run scripts/validate_supabase_connection.py
```

This script tests:
- Direct psycopg3 connection
- HACS adapter functionality
- HACS tools integration
- Data persistence verification

## Best Practices

### 1. Environment Management

- Use `.env` files for local development
- Set environment variables directly in production
- Never commit sensitive credentials to version control
- Use multiple fallback environment variable names

### 2. Connection Patterns

- Use async connections for better performance
- Always use context managers (`async with`) for connections
- Enable autocommit for DDL operations
- Use connection pooling for production applications

### 3. Actor Authentication

- Always provide an Actor for HACS operations
- Use specific permissions for security
- Configure actor context once and let tools inject automatically
- Use system actors for automated operations

### 4. Error Handling

- Check connection status before operations
- Handle migration failures gracefully
- Validate environment variables early
- Use proper logging for debugging

## Security Considerations

### 1. Supabase Security

- Use direct database connections for better performance
- Enable SSL with `sslmode=require`
- Rotate database passwords regularly
- Use connection pooling to limit concurrent connections

### 2. HACS Security

- Configure proper Actor permissions
- Use audit trails for all operations
- Validate resource data before persistence
- Enable dev_mode only in development

## Production Deployment

### 1. Environment Variables

Set these in your production environment:

```bash
DATABASE_URL=postgresql://postgres:secure_password@db.project.supabase.co:5432/postgres?sslmode=require
HACS_ENVIRONMENT=production
HACS_DEV_MODE=false
```

### 2. Connection Pooling

Configure appropriate pool sizes:

```python
adapter = HACSConnectionFactory.get_adapter(
    pool_size=20,     # Adjust based on your needs
    auto_migrate=False  # Run migrations separately in production
)
```

### 3. Monitoring

Monitor your connections:

```python
from hacs_persistence.migrations import get_migration_status

status = await get_migration_status()
print("Database health:", status.get('migration_complete'))
```

This guide ensures robust, secure, and performant connections between HACS and Supabase using modern async patterns and proper environment management.
