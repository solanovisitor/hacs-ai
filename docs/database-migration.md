# HACS Database Migration System

The HACS Database Migration system provides comprehensive database schema management for all HACS resources, ensuring proper storage and retrieval of healthcare data.

## Overview

The migration system automatically creates the necessary database structure to support all HACS resources, including:

- **Core Models**: Patient, Observation, Encounter, Resources
- **Clinical Models**: Conditions, Medications, Procedures, Allergies, Goals, etc.
- **Organizational Models**: Organization, OrganizationContact, OrganizationQualification
- **Workflow Models**: PlanDefinition, ActivityDefinition, Tasks, Appointments
- **Knowledge Models**: Libraries, Evidence Variables, Guidance Responses
- **Agent Models**: Memories, Messages
- **Administrative Models**: System Configuration, Audit Trails

## Supported HACS Resources

### Core Healthcare Models
- **Patient**: Patient demographics and contact information
- **Observation**: Clinical observations and measurements
- **Encounter**: Healthcare encounters and visits
- **Condition**: Medical conditions and diagnoses
- **Medication**: Medication information
- **MedicationRequest**: Medication prescriptions and orders
- **Procedure**: Medical procedures performed
- **AllergyIntolerance**: Patient allergies and intolerances
- **Goal**: Patient care goals and objectives
- **ServiceRequest**: Service and diagnostic orders
- **FamilyMemberHistory**: Family medical history
- **RiskAssessment**: Clinical risk assessments

### Organizational Models (New!)
- **Organization**: Healthcare organizations, departments, and institutions
- **OrganizationContact**: Contact information for specific purposes
- **OrganizationQualification**: Certifications, accreditations, and licenses

### Clinical Workflow Models
- **PlanDefinition**: Clinical workflow definitions
- **ActivityDefinition**: Reusable activity definitions
- **Library**: Knowledge libraries and resources
- **GuidanceResponse**: Clinical decision support responses
- **EvidenceVariable**: Evidence-based variable definitions
- **Task**: Workflow tasks and assignments
- **Appointment**: Healthcare appointments and scheduling

### Agent and Knowledge Models
- **Memory**: Agent memory blocks for context retention
- **AgentMessage**: Inter-agent communication messages
- **KnowledgeItem**: Knowledge base items and facts

## Database Schema Structure

### Schema Organization
```
hacs_core/          # Core resources and organizational data
├── resources       # Generic resource storage
├── patients        # Patient demographics
├── observations    # Clinical observations
├── encounters      # Healthcare encounters
├── organizations   # Healthcare organizations
├── organization_contacts      # Organization contact details
└── organization_qualifications # Organization certifications

hacs_clinical/      # Clinical and workflow data
├── conditions      # Medical conditions
├── medications     # Medication information
├── medication_requests # Medication orders
├── procedures      # Medical procedures
├── allergy_intolerances # Allergies and intolerances
├── goals          # Patient care goals
├── service_requests # Service orders
├── family_member_history # Family medical history
├── risk_assessments # Clinical risk assessments
├── plan_definitions # Workflow definitions
├── activity_definitions # Activity templates
├── libraries      # Knowledge libraries
├── guidance_responses # Clinical guidance
├── evidence_variables # Evidence definitions
├── tasks          # Workflow tasks
└── appointments   # Healthcare appointments

hacs_registry/      # Knowledge and template registry
├── knowledge_items # Knowledge base
└── templates      # Reusable templates

hacs_agents/        # Agent-specific data
├── memories       # Agent memories
└── messages       # Agent communications

hacs_admin/         # Administrative data
├── migrations     # Migration history
└── system_config  # System configuration

hacs_audit/         # Audit and change tracking
└── resource_changes # Resource change audit log
```

## Organization Model Support

The new Organization model provides comprehensive support for healthcare organizations:

### Organization Features
- **Hierarchical Structure**: Organizations can be part of other organizations
- **Multiple Identifiers**: NPI, TIN, facility IDs, etc.
- **Contact Management**: Multiple contacts for different purposes
- **Qualifications**: Certifications, accreditations, licenses
- **Address Management**: Primary location with detailed address fields
- **Active Status**: Track active/inactive organizations

### Organization Types Supported
- Healthcare Providers (`prov`)
- Hospital Departments (`dept`)
- Educational Institutions (`edu`)
- Government Agencies (`govt`)
- Insurance Companies (`ins`)
- Community Groups (`cg`)

### Example Organization Data Structure
```json
{
  "id": "org-001",
  "name": "Metro General Hospital",
  "active": true,
  "organization_type": [{"code": "prov", "display": "Healthcare Provider"}],
  "identifier": ["NPI-1234567890", "TIN-12-3456789"],
  "primary_email": "info@metrogeneral.org",
  "primary_phone": "+1-555-0199",
  "city": "Boston",
  "state": "MA",
  "country": "US",
  "contacts": [...],
  "qualifications": [...]
}
```

## Running Migrations

### Command Line Usage
```bash
# Run migration
python -m hacs_persistence.migrations

# Check migration status
python -m hacs_persistence.migrations --status

# Use specific database URL
python -m hacs_persistence.migrations --database-url postgresql://user:pass@host:port/db
```

### Programmatic Usage
```python
from hacs_persistence.migrations import run_migration, get_migration_status

# Run migration
success = run_migration("postgresql://user:pass@host:port/db")

# Check status
status = get_migration_status("postgresql://user:pass@host:port/db")
print(f"Migration complete: {status['migration_complete']}")
```

### Environment Variables
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/hacs_db"
export TEST_DATABASE_URL="postgresql://user:password@localhost:5432/hacs_test"
```

## Docker Integration

The HACS migration system is designed to work seamlessly with Docker containers and Docker Compose.

### Automatic Migrations with Docker Compose

The migration system is integrated into the Docker Compose configuration and runs automatically:

```yaml
# docker-compose.yml includes a migration service
services:
  hacs-migration:
    build:
      context: .
      dockerfile: Dockerfile.migration
    environment:
      - DATABASE_URL=postgresql://hacs:password@postgres:5432/hacs
    depends_on:
      postgres:
        condition: service_healthy
    restart: no  # Run once and exit
```

### Deployment Options

#### Option 1: Automatic Deployment Script
```bash
# Use the provided deployment script
./scripts/deploy-with-migrations.sh production

# For development
./scripts/deploy-with-migrations.sh development
```

#### Option 2: Manual Docker Compose
```bash
# Start PostgreSQL first
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
docker-compose exec postgres sh -c 'until pg_isready -U hacs; do sleep 2; done'

# Run migrations
docker-compose run --rm hacs-migration

# Start all services
docker-compose up -d
```

#### Option 3: Run Migrations in Existing Container
```bash
# Run migrations in the MCP server container
docker-compose exec hacs-mcp-server /app/scripts/run-migrations.sh
```

## Testing the Migration

Use the provided test script to verify migration completeness:

```bash
cd packages/hacs-persistence
python test_migration.py
```

The test script will:
1. Check current migration status
2. Run the migration process
3. Verify all schemas and tables are created
4. Confirm support for all HACS resources
5. Report overall success/failure

## Migration Features

### Automatic Schema Management
- **Schema Creation**: Automatically creates all required schemas
- **Table Creation**: Creates tables for all HACS resources
- **Index Creation**: Optimizes query performance with strategic indexes
- **Constraint Management**: Enforces data integrity constraints
- **Trigger Setup**: Maintains updated_at timestamps automatically

### Performance Optimizations
- **Strategic Indexing**: Indexes on frequently queried fields
- **JSONB Support**: Efficient storage and querying of complex data
- **Foreign Key Constraints**: Maintains referential integrity
- **Audit Trail**: Tracks all resource changes

### Data Integrity
- **FHIR Constraints**: Enforces FHIR-compliant data rules
- **Email Validation**: Validates email format in contact fields
- **Date Validation**: Ensures proper date ordering in periods
- **Required Field Checks**: Enforces required field constraints

## Migration Status Verification

The system tracks migration completeness through:

- **Schema Count**: Ensures all 6 schemas are created
- **Table Count**: Verifies minimum of 25+ tables across all schemas
- **Migration Table**: Tracks migration history and status
- **Constraint Verification**: Confirms all constraints are applied

### Expected Metrics
```json
{
  "schemas_found": ["hacs_core", "hacs_clinical", "hacs_registry", "hacs_agents", "hacs_admin", "hacs_audit"],
  "total_schemas": 6,
  "total_tables": 25+,
  "migration_table_exists": true,
  "migration_complete": true
}
```

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```bash
   pip install psycopg2-binary
   ```

2. **Database Connection Issues**
   - Verify DATABASE_URL format
   - Check database server is running
   - Confirm user permissions

3. **Partial Migration**
   - Check database logs for constraint violations
   - Verify sufficient disk space
   - Re-run migration (it's idempotent)

### Migration Recovery
The migration system is idempotent - you can safely re-run it multiple times. It uses `CREATE TABLE IF NOT EXISTS` and similar constructs to avoid conflicts.

## Future Extensions

The migration system is designed to be extensible:

- **New Model Support**: Easily add new HACS resources
- **Schema Evolution**: Support for schema version upgrades
- **Data Migration**: Tools for migrating existing data
- **Custom Indexes**: Application-specific performance optimizations

## Security Considerations

- **SQL Injection Prevention**: Uses parameterized queries
- **Access Control**: Respects database user permissions
- **Audit Logging**: Tracks all schema changes
- **Backup Friendly**: Migration preserves existing data