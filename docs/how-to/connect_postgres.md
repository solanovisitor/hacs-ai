# Connect to a database

This guide shows how to set up a production-ready PostgreSQL database for HACS, run migrations, and create clinical resources using authenticated actors.

Prerequisites:
- PostgreSQL database (local or cloud)
- `uv pip install -U hacs-persistence hacs-auth hacs-models`

## Database setup and migrations

### Configure database connection

```python
from dotenv import load_dotenv
load_dotenv()  # Load DATABASE_URL from .env

import os
print("Database URL configured:", bool(os.getenv("DATABASE_URL")))
db_url = os.getenv("DATABASE_URL") or ""
if db_url:
    preview = db_url[:30] + "..." if len(db_url) > 30 else db_url
    print(f"URL preview: {preview}")
else:
    print("URL preview: Not set")
```

**Output:**
```
Database URL configured: True
URL preview: postgresql://hacs:...
```

### Production database configuration

```python
# Production-ready database configuration
production_config = {
    "connection_pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "ssl_mode": "require",
    "application_name": "hacs-production",
    "statement_timeout": 30000,  # 30 seconds
    "idle_in_transaction_session_timeout": 60000,  # 1 minute
}

print("🚀 Production Database Configuration:")
for key, value in production_config.items():
    print(f"  {key}: {value}")

# Security recommendations
security_checklist = [
    "✅ SSL/TLS encryption enabled (sslmode=require)",
    "✅ Connection pooling configured for scalability", 
    "✅ Statement timeouts prevent hanging queries",
    "✅ Idle transaction timeouts prevent lock contention",
    "✅ Application name for connection tracking",
    "✅ Prepared statements for performance"
]

print(f"\n🔒 Security Checklist:")
for item in security_checklist:
    print(f"  {item}")
```

Output:
```
🚀 Production Database Configuration:
  connection_pool_size: 20
  max_overflow: 30
  pool_timeout: 30
  pool_recycle: 3600
  ssl_mode: require
  application_name: hacs-production
  statement_timeout: 30000
  idle_in_transaction_session_timeout: 60000

🔒 Security Checklist:
  ✅ SSL/TLS encryption enabled (sslmode=require)
  ✅ Connection pooling configured for scalability
  ✅ Statement timeouts prevent hanging queries
  ✅ Idle transaction timeouts prevent lock contention
  ✅ Application name for connection tracking
  ✅ Prepared statements for performance
```

### HACS database schema overview

HACS organizes healthcare data into six specialized PostgreSQL schemas for optimal performance and security. The **hacs_core** schema contains foundational resources like patients, observations, and encounters that form the backbone of clinical data. **hacs_clinical** houses specialized clinical data including conditions, medications, procedures, and diagnostic reports. **hacs_registry** manages registered resource definitions, tool versions, and knowledge items for AI agents. **hacs_agents** stores agent messages, memory blocks, and session data for conversational workflows. **hacs_admin** contains system configuration and operational settings. Finally, **hacs_audit** provides comprehensive audit logging and compliance tracking for all system operations. This schema separation enables fine-grained access control, optimized indexing strategies, and clear data governance boundaries essential for healthcare applications.

## Where Postgres fits in HACS

- **Adapters**: HACS provides an async JSONB adapter (`PostgreSQLAdapter`) for universal storage and an optional granular adapter (`GranularPostgreSQLAdapter`) for typed, per-resource tables. Both store full resources and indexes key fields for queries.
- **Schemas**: Data is split across `hacs_core`, `hacs_clinical`, `hacs_registry`, `hacs_agents`, `hacs_admin`, `hacs_audit` for governance and performance.
- **JSONB vs typed tables**: The JSONB adapter writes to `public.hacs_resources` and works for all models. The granular adapter writes to typed tables (e.g., `hacs_core.patients`, `hacs_core.observations`) for faster analytics and joins.
- **Configuration**: Set `DATABASE_URL` (or `HACS_DATABASE_URL`) in your environment; the snippet maps it so the adapter initializes cleanly.

### Run database migrations

```python
import asyncio
from hacs_persistence.migrations import run_migration, get_migration_status

# Check current migration status
print("Checking migration status...")
status = await get_migration_status()

if status.get("error"):
    print(f"❌ Database connection error: {status['error']}")
else:
    print(f"Migration complete: {status['migration_complete']}")
    print(f"Tables found: {status['total_tables']}/{status['expected_tables']}")
    print(f"pgvector enabled: {status['pgvector_enabled']}")
    print("Schema breakdown:", status['schema_breakdown'])

# Run migration if needed
if not status.get("migration_complete", False):
    print("\nRunning database migration...")
    migration_success = await run_migration()
    
    if migration_success:
        print("✅ Migration completed successfully!")
        
        # Verify migration
        new_status = await get_migration_status()
        print(f"Verification: {new_status['total_tables']} tables created")
    else:
        print("❌ Migration failed")
```

Output:
```
Checking migration status...
Migration complete: True
Tables found: 36/23
pgvector enabled: True
Schema breakdown: {'hacs_core': 7, 'hacs_clinical': 21, 'hacs_registry': 2, 'hacs_agents': 3, 'hacs_admin': 1, 'hacs_audit': 1, 'public': 1}
```

## Authentication

This guide focuses on database connectivity. For creating and verifying the authenticated provider and permissions, see [Authenticate Actor](authenticate_actor.md).

## Create and save patient records

```python
from datetime import date, datetime
from dotenv import load_dotenv
import os
from hacs_models import Patient, HumanName, ContactPoint, Address, Actor, Observation, CodeableConcept, Quantity
from hacs_persistence.adapter import create_postgres_adapter

# Ensure environment is loaded and mapped for HACS
load_dotenv()
os.environ.setdefault("HACS_DATABASE_URL", os.getenv("DATABASE_URL", ""))

async def save_patient_and_observation() -> dict:
    # Build resources
    patient = Patient(
        full_name="Carlos Miguel Fernandez",
        name=[HumanName(use="official", family="Fernandez", given=["Carlos", "Miguel"])],
        gender="male",
        birth_date=date(1978, 12, 3),
        active=True,
        telecom=[ContactPoint(system="phone", value="+1-555-0198", use="mobile")],
        address=[Address(use="home", line=["456 Pine Avenue"], city="Houston", state="TX", postal_code="77001")],
    )

    observation = Observation(
        status="final",
        category=[CodeableConcept(text="Vital Signs", coding=[{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs", "display": "Vital Signs"}])],
        code=CodeableConcept(text="Blood Pressure", coding=[{"system": "http://loinc.org", "code": "85354-9", "display": "Blood pressure panel"}]),
        subject=f"Patient/{patient.id}",
        effective_date_time=datetime.now(),
    )
    observation.set_quantity_value(118, "mmHg", system="http://unitsofmeasure.org")
    observation.add_note("Systolic 118 mmHg; Diastolic 76 mmHg")

    # Save using async adapter with a valid audit actor
    adapter = await create_postgres_adapter()
    author = Actor(name="db-writer", role="system", permissions=["patient:write", "observation:write"])  # type: ignore[arg-type]

    saved_patient = await adapter.save(patient, author)
    saved_obs = await adapter.save(observation, author)

    # Read back patient to confirm
    read_back = await adapter.read(Patient, saved_patient.id, author)

    return {
        "patient_id": saved_patient.id,
        "observation_id": saved_obs.id,
        "patient_name": read_back.full_name,
        "saved_at": saved_patient.created_at.isoformat(),
    }

import asyncio
result = asyncio.run(save_patient_and_observation())
print("✅ Patient & Observation persisted:")
print(f"  Patient ID: {result['patient_id']}")
print(f"  Observation ID: {result['observation_id']}")
print(f"  Name: {result['patient_name']}")
print(f"  Timestamp: {result['saved_at']}")
```

Output:
```
✅ Patient & Observation persisted:
  Patient ID: patient-704ac73d
  Observation ID: observation-f7db7a5d
  Name: Carlos Miguel Fernandez
  Timestamp: 2025-08-19T19:38:00.292553+00:00
```

## Query patient records

```python
from hacs_tools.domains.database import read_resource

@require_permission("patient:read")
async def get_patient_by_id(patient_id: str, **kwargs) -> dict:
    """Retrieve patient record with authentication check."""
    # Query database using HACS tools
    read_result = read_resource(
        resource_id=patient_id,
        resource_type="Patient",
        actor_id=kwargs.get("claims", {}).get("user_id")
    )
    
    if not read_result.success:
        raise Exception(f"Failed to read patient {patient_id}: {read_result.message}")
    
    patient_data = read_result.data["resource"]
    
    return {
        "id": patient_data["id"],
        "resource_type": patient_data["resource_type"],
        "full_name": patient_data["full_name"],
        "gender": patient_data["gender"],
        "birth_date": str(patient_data["birth_date"]),
        "active": patient_data["active"],
        "retrieved_at": datetime.now().isoformat(),
        "retrieved_by": kwargs.get("claims", {}).get("user_id"),
        "version": patient_data.get("version", "1.0.0")
    }

# Retrieve the patient
patient_record = await get_patient_by_id(
    patient_result["patient_id"],
    token=provider_token,
    claims=provider_claims
)

print("✅ Patient Retrieved:")
print(f"  ID: {patient_record['id']}")
print(f"  Name: {patient_record['full_name']}")
print(f"  Retrieved by: {patient_record['retrieved_by']}")
print(f"  Active: {patient_record['active']}")
```

Output:
```
✅ Patient Retrieved:
  ID: patient-demo-80200
  Name: Carlos Miguel Fernandez
  Retrieved by: dr_martinez
  Version: 1.0.0
  Active: True
``` 

## Database Inspection Utilities

HACS provides high-level utilities to inspect your database without writing raw SQL:

```python
import asyncio
from hacs_persistence import verify_database_environment, get_generic_table_status

async def inspect_database():
    # Comprehensive environment check
    env_result = await verify_database_environment()
    
    print("🔧 Environment Status:")
    print(f"  Database URL source: {env_result.get('database_url_source', 'Not found')}")
    
    connection = env_result.get("connection_test", {})
    if "error" not in connection:
        print(f"  PostgreSQL: {connection['postgresql_version']}")
        print(f"  Database: {connection['database_name']}")
    
    # Check generic HACS table
    generic_status = await get_generic_table_status()
    if generic_status.get("table_exists"):
        print(f"\n📊 Generic HACS Table:")
        print(f"  Total resources: {generic_status['total_resources']}")
        print(f"  Resource types: {generic_status['resource_types_count']}")
        
        breakdown = generic_status.get("resource_breakdown", {})
        for resource_type, count in list(breakdown.items())[:5]:  # Top 5
            print(f"    - {resource_type}: {count}")

asyncio.run(inspect_database())
```

**Output:**
```
🔧 Environment Status:
  Database URL source: DATABASE_URL
  PostgreSQL: PostgreSQL 17.4
  Database: postgres

📊 Generic HACS Table:
  Total resources: 6
  Resource types: 1
    - Patient: 6
```

## Next steps

Now that you have a configured database with authenticated actors, you can:

- **[Extract Structured HACS Models](extract_annotations.md)**: Use LLM extraction to create clinical resources from text
- **[Validate HACS Models](validate_hacs_models.md)**: Ensure clinical data quality and FHIR compliance
- **[Visualize Resources](visualize_resources.md)**: Create rich visualizations of patient data and clinical records
