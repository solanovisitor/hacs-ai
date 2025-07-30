# HACS Persistence

**PostgreSQL + pgvector persistence for healthcare data storage**

Database and vector storage adapters optimized for healthcare AI applications.

## 🗄️ **Database Support**

### **PostgreSQL with pgvector**
Primary storage solution for healthcare data:

- **Relational Data** - Patient records, observations, clinical data
- **Vector Storage** - Clinical embeddings via pgvector extension
- **Schema Management** - Automated migrations and versioning
- **Healthcare Compliance** - HIPAA-aware design patterns

## 🏥 **Healthcare Schema**

Optimized database tables for clinical workflows:

```sql
-- Core healthcare tables
patients              -- Patient demographics and clinical context
observations         -- Clinical measurements and findings
actors              -- Healthcare providers with role-based permissions
memory_blocks       -- AI agent episodic/procedural memory
evidence_items     -- Clinical guidelines and research
knowledge_base     -- Structured clinical knowledge

-- Vector storage for AI operations
patient_vectors     -- Patient data embeddings
clinical_vectors    -- Clinical note embeddings
memory_vectors      -- Memory content embeddings
```

## 📦 **Installation**

```bash
pip install hacs-persistence
```

## 🚀 **Quick Start**

### **Setup via HACS**
```bash
# Automatic setup with migrations
python setup.py --mode local

# Database runs on localhost:5432
# Automatic pgvector extension installation
```

### **Direct Usage**
```python
from hacs_persistence import Adapter
from hacs_core import Patient

# Connect to healthcare database
adapter = Adapter(
    database_url="postgresql://hacs:password@localhost:5432/hacs"
)

# Store patient record
patient = Patient(
    full_name="Maria Rodriguez",
    birth_date="1985-03-15",
    gender="female"
)

# Save with automatic validation
saved_patient = adapter.save_resource(patient)
print(f"Saved patient: {saved_patient.id}")
```

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Primary database connection
DATABASE_URL=postgresql://hacs:password@localhost:5432/hacs

# Vector store configuration (uses pgvector by default)
VECTOR_STORE=pgvector

# Optional: External PostgreSQL for production
DATABASE_URL=postgresql://hacs:secure_password@prod-db:5432/hacs_production
```

### **Migration Management**
```bash
# Run database migrations
python -m hacs_persistence.migrations $DATABASE_URL

# Check migration status
python -c "from hacs_persistence import get_migration_status; print(get_migration_status())"
```

## 📊 **Performance**

- **Resource Operations**: <50ms for standard CRUD
- **Vector Queries**: <100ms for similarity search
- **Batch Operations**: 1000+ records per second
- **Memory Footprint**: Minimal overhead

## 🔐 **Security Features**

- **Connection Encryption** - SSL/TLS support
- **Role-based Access** - Healthcare provider permissions
- **Audit Trails** - Complete operation logging
- **Data Isolation** - Organization-specific schemas

## 🛠️ **Advanced Usage**

### **Vector Operations**
```python
# Store clinical embedding
adapter.store_vector(
    resource_id="patient_123",
    embedding=[0.1, 0.2, ...],  # Clinical text embedding
    metadata={"type": "patient", "department": "cardiology"}
)

# Similarity search
similar_patients = adapter.vector_search(
    query_embedding=[0.1, 0.2, ...],
    resource_type="patient",
    top_k=5
)
```

### **Batch Operations**
```python
# Bulk insert for large datasets
patients = [Patient(...) for _ in range(1000)]
results = adapter.bulk_save(patients)
```

## 📄 **License**

Apache-2.0 License - see [LICENSE](../../LICENSE) for details.