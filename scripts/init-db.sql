-- HACS Database Initialization Script
-- This script sets up the PostgreSQL database with pgvector extension for HACS

-- Enable pgvector extension for vector operations
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable other useful extensions for healthcare data
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Create HACS schema for organized table structure
CREATE SCHEMA IF NOT EXISTS hacs_core;
CREATE SCHEMA IF NOT EXISTS hacs_data;
CREATE SCHEMA IF NOT EXISTS hacs_vectors;

-- Set search path to include HACS schemas
ALTER DATABASE hacs SET search_path TO hacs_core, hacs_data, hacs_vectors, public;

-- Create vector dimensions constants (commonly used in healthcare AI)
-- These can be adjusted based on the embedding model used
DO $$ 
BEGIN
    -- Common embedding dimensions
    -- 384 for sentence-transformers/all-MiniLM-L6-v2 (lightweight)
    -- 768 for OpenAI text-embedding-ada-002 (standard)
    -- 1536 for OpenAI text-embedding-3-small (newer)
    -- 3072 for OpenAI text-embedding-3-large (high-quality)
    
    -- Store embedding configuration
    CREATE TABLE IF NOT EXISTS hacs_core.embedding_config (
        id SERIAL PRIMARY KEY,
        model_name VARCHAR(255) NOT NULL UNIQUE,
        dimensions INTEGER NOT NULL,
        description TEXT,
        is_active BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    -- Insert default embedding configurations
    INSERT INTO hacs_core.embedding_config (model_name, dimensions, description, is_active) VALUES
    ('text-embedding-ada-002', 1536, 'OpenAI Ada 002 embeddings', TRUE),
    ('text-embedding-3-small', 1536, 'OpenAI Text Embedding 3 Small', FALSE),
    ('text-embedding-3-large', 3072, 'OpenAI Text Embedding 3 Large', FALSE),
    ('all-MiniLM-L6-v2', 384, 'Sentence Transformers lightweight model', FALSE)
    ON CONFLICT (model_name) DO NOTHING;
    
EXCEPTION
    WHEN duplicate_table THEN
        RAISE NOTICE 'Tables already exist, skipping creation';
END $$;

-- Create audit trail table for HACS operations
CREATE TABLE IF NOT EXISTS hacs_core.audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    operation VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    actor_id VARCHAR(255),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT
);

-- Create index for audit log queries
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON hacs_core.audit_log (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_operation ON hacs_core.audit_log (operation);
CREATE INDEX IF NOT EXISTS idx_audit_log_resource ON hacs_core.audit_log (resource_type, resource_id);

-- Create HACS memory table with vector embeddings
CREATE TABLE IF NOT EXISTS hacs_data.hacs_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content TEXT NOT NULL,
    memory_type VARCHAR(50) DEFAULT 'episodic',
    session_id VARCHAR(255),
    actor_id VARCHAR(255),
    importance_score FLOAT DEFAULT 0.5 CHECK (importance_score >= 0.0 AND importance_score <= 1.0),
    tags TEXT[],
    metadata JSONB,
    
    -- Vector embedding for semantic search (adaptive size)
    embedding vector(1536),  -- Default to OpenAI ada-002 dimensions
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for memory table
CREATE INDEX IF NOT EXISTS idx_memories_type ON hacs_data.hacs_memories (memory_type);
CREATE INDEX IF NOT EXISTS idx_memories_session ON hacs_data.hacs_memories (session_id);
CREATE INDEX IF NOT EXISTS idx_memories_importance ON hacs_data.hacs_memories (importance_score DESC);
CREATE INDEX IF NOT EXISTS idx_memories_created ON hacs_data.hacs_memories (created_at DESC);

-- Create vector similarity index for fast retrieval
CREATE INDEX IF NOT EXISTS idx_memories_embedding ON hacs_data.hacs_memories 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create HACS resources table with vector search capabilities
CREATE TABLE IF NOT EXISTS hacs_data.hacs_resources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resource_type VARCHAR(100) NOT NULL,
    resource_data JSONB NOT NULL,
    
    -- Vector embeddings for different aspects
    content_embedding vector(1536),        -- For main content/description
    metadata_embedding vector(1536),       -- For structured metadata
    clinical_embedding vector(1536),       -- For clinical/medical concepts
    
    -- Standard fields
    name VARCHAR(255),
    description TEXT,
    tags TEXT[],
    version VARCHAR(50) DEFAULT '1.0.0',
    status VARCHAR(50) DEFAULT 'active',
    
    -- FHIR compliance
    fhir_version VARCHAR(20),
    fhir_profile VARCHAR(255),
    
    -- Audit fields
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by VARCHAR(255),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for resources table
CREATE INDEX IF NOT EXISTS idx_resources_type ON hacs_data.hacs_resources (resource_type);
CREATE INDEX IF NOT EXISTS idx_resources_status ON hacs_data.hacs_resources (status);
CREATE INDEX IF NOT EXISTS idx_resources_created ON hacs_data.hacs_resources (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_resources_name ON hacs_data.hacs_resources (name);

-- Create vector indexes for resource embeddings
CREATE INDEX IF NOT EXISTS idx_resources_content_embedding ON hacs_data.hacs_resources 
USING ivfflat (content_embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_resources_metadata_embedding ON hacs_data.hacs_resources 
USING ivfflat (metadata_embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_resources_clinical_embedding ON hacs_data.hacs_resources 
USING ivfflat (clinical_embedding vector_cosine_ops) WITH (lists = 100);

-- Create GIN index for JSONB data
CREATE INDEX IF NOT EXISTS idx_resources_data_gin ON hacs_data.hacs_resources USING GIN (resource_data);
CREATE INDEX IF NOT EXISTS idx_resources_tags ON hacs_data.hacs_resources USING GIN (tags);

-- Create vector collections table for organized vector management
CREATE TABLE IF NOT EXISTS hacs_vectors.collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    embedding_model VARCHAR(255) NOT NULL,
    dimensions INTEGER NOT NULL,
    distance_metric VARCHAR(50) DEFAULT 'cosine',
    
    -- Collection metadata
    total_vectors BIGINT DEFAULT 0,
    metadata JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_hacs_memories_updated_at BEFORE UPDATE ON hacs_data.hacs_memories 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_hacs_resources_updated_at BEFORE UPDATE ON hacs_data.hacs_resources 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_collections_updated_at BEFORE UPDATE ON hacs_vectors.collections 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions to hacs user
GRANT USAGE ON SCHEMA hacs_core TO hacs;
GRANT USAGE ON SCHEMA hacs_data TO hacs;
GRANT USAGE ON SCHEMA hacs_vectors TO hacs;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA hacs_core TO hacs;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA hacs_data TO hacs;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA hacs_vectors TO hacs;

GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA hacs_core TO hacs;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA hacs_data TO hacs;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA hacs_vectors TO hacs;

-- Insert initial data for development
INSERT INTO hacs_vectors.collections (name, description, embedding_model, dimensions) VALUES
('clinical_memories', 'Clinical and medical memory storage', 'text-embedding-ada-002', 1536),
('resource_schemas', 'HACS resource schema embeddings', 'text-embedding-ada-002', 1536),
('patient_data', 'Patient-related data embeddings', 'text-embedding-ada-002', 1536)
ON CONFLICT (name) DO NOTHING;

-- Insert test data for comprehensive tool testing
INSERT INTO hacs_data.hacs_resources (id, resource_type, resource_data, created_by) VALUES
-- Test patients for resource management tools
('patient-test-001', 'Patient', '{"full_name": "John Doe Test", "birth_date": "1990-01-15", "gender": "male", "phone": "+1-555-123-4567", "email": "john.doe.test@example.com", "active": true}', 'test_system'),
('patient-test-002', 'Patient', '{"full_name": "Jane Smith Test", "birth_date": "1985-06-20", "gender": "female", "phone": "+1-555-987-6543", "email": "jane.smith.test@example.com", "active": true}', 'test_system'),
('patient-test-003', 'Patient', '{"full_name": "Bob Johnson Test", "birth_date": "1975-12-03", "gender": "male", "phone": "+1-555-456-7890", "email": "bob.johnson.test@example.com", "active": true}', 'test_system'),

-- Test observations for clinical workflow tools
('obs-test-001', 'Observation', '{"code": {"coding": [{"code": "85354-9", "system": "http://loinc.org", "display": "Blood pressure"}]}, "value_quantity": {"value": 120, "unit": "mmHg", "system": "http://unitsofmeasure.org"}, "status": "final", "subject": "patient-test-001", "effective_datetime": "2024-01-15T10:00:00Z"}', 'test_system'),
('obs-test-002', 'Observation', '{"code": {"coding": [{"code": "33747-0", "system": "http://loinc.org", "display": "General appearance"}]}, "value_string": "Well-appearing", "status": "final", "subject": "patient-test-001", "effective_datetime": "2024-01-15T10:05:00Z"}', 'test_system'),

-- Test encounters
('enc-test-001', 'Encounter', '{"status": "finished", "class": {"code": "AMB", "display": "ambulatory"}, "subject": "patient-test-001", "period": {"start": "2024-01-15T09:00:00Z", "end": "2024-01-15T10:30:00Z"}, "reason_code": [{"coding": [{"code": "Z00.00", "system": "http://hl7.org/fhir/sid/icd-10", "display": "Routine health examination"}]}]}', 'test_system'),

-- Test conditions for clinical analysis
('cond-test-001', 'Condition', '{"code": {"coding": [{"code": "I10", "system": "http://hl7.org/fhir/sid/icd-10", "display": "Essential hypertension"}]}, "subject": "patient-test-001", "clinical_status": {"coding": [{"code": "active", "system": "http://terminology.hl7.org/CodeSystem/condition-clinical"}]}, "verification_status": {"coding": [{"code": "confirmed", "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status"}]}}', 'test_system'),

-- Test organizations for admin tools
('org-test-001', 'Organization', '{"name": "Test Healthcare System", "type": [{"coding": [{"code": "prov", "system": "http://terminology.hl7.org/CodeSystem/organization-type", "display": "Healthcare Provider"}]}], "active": true, "contact": [{"purpose": {"coding": [{"code": "ADMIN", "system": "http://terminology.hl7.org/CodeSystem/contactentity-type"}]}, "telecom": [{"system": "phone", "value": "+1-555-TEST-ORG"}]}]}', 'test_system')

ON CONFLICT (id) DO NOTHING;

-- Insert test memory blocks for memory operations tools
INSERT INTO hacs_core.memories (id, content, memory_type, context_metadata, tags, actor_id, vector_id) VALUES
('mem-test-001', 'Patient shows significant improvement in blood pressure control with current medication regimen', 'episodic', '{"patient_id": "patient-test-001", "encounter_id": "enc-test-001", "clinical_context": "hypertension_management"}', ARRAY['hypertension', 'improvement', 'medication_compliance'], 'Dr. Test Physician', 'vec-mem-001'),
('mem-test-002', 'Standard procedure for chest pain assessment includes ECG, cardiac enzymes, and risk stratification', 'procedural', '{"domain": "cardiology", "procedure_type": "assessment_protocol"}', ARRAY['chest_pain', 'cardiology', 'assessment', 'protocol'], 'Dr. Test Physician', 'vec-mem-002'),
('mem-test-003', 'Emergency department protocol requires immediate triage for patients with chest pain symptoms', 'executive', '{"department": "emergency", "priority": "high", "workflow": "triage_protocol"}', ARRAY['emergency', 'triage', 'chest_pain', 'protocol'], 'Nurse Test Manager', 'vec-mem-003')
ON CONFLICT (id) DO NOTHING;

-- Insert test vector collection data
INSERT INTO hacs_vectors.vector_data (id, collection_name, content_hash, metadata, text_content) VALUES
('vec-mem-001', 'clinical_memories', 'hash-mem-001', '{"memory_id": "mem-test-001", "memory_type": "episodic", "patient_id": "patient-test-001"}', 'Patient shows significant improvement in blood pressure control with current medication regimen'),
('vec-mem-002', 'clinical_memories', 'hash-mem-002', '{"memory_id": "mem-test-002", "memory_type": "procedural", "domain": "cardiology"}', 'Standard procedure for chest pain assessment includes ECG, cardiac enzymes, and risk stratification'),
('vec-mem-003', 'clinical_memories', 'hash-mem-003', '{"memory_id": "mem-test-003", "memory_type": "executive", "department": "emergency"}', 'Emergency department protocol requires immediate triage for patients with chest pain symptoms'),

-- Test resource schema embeddings for schema discovery tools
('vec-schema-001', 'resource_schemas', 'hash-schema-patient', '{"resource_type": "Patient", "version": "1.0"}', 'Patient resource schema with demographics, contact information, and clinical identifiers'),
('vec-schema-002', 'resource_schemas', 'hash-schema-observation', '{"resource_type": "Observation", "version": "1.0"}', 'Observation resource schema for clinical measurements, vital signs, and laboratory results'),
('vec-schema-003', 'resource_schemas', 'hash-schema-condition', '{"resource_type": "Condition", "version": "1.0"}', 'Condition resource schema for diagnoses, clinical status, and verification information')
ON CONFLICT (id) DO NOTHING;

-- Insert test audit log entries for admin operations testing
INSERT INTO hacs_core.audit_log (operation, resource_type, actor_id, metadata) VALUES
('create', 'Patient', 'test_system', '{"test_data": true, "resource_id": "patient-test-001", "action": "test_data_creation"}'),
('create', 'Observation', 'test_system', '{"test_data": true, "resource_id": "obs-test-001", "action": "test_data_creation"}'),
('create', 'Encounter', 'test_system', '{"test_data": true, "resource_id": "enc-test-001", "action": "test_data_creation"}'),
('test_migration', 'system', 'test_system', '{"message": "Test data migration completed", "tables_created": 6, "test_records_inserted": 12}');

-- Log successful initialization
INSERT INTO hacs_core.audit_log (operation, resource_type, actor_id, metadata) VALUES
('database_init', 'system', 'postgres', '{"message": "HACS database initialized with pgvector support and test data", "timestamp": "' || NOW()::text || '", "test_data_included": true}');

-- Display initialization summary
DO $$
BEGIN
    RAISE NOTICE '====================================';
    RAISE NOTICE 'HACS Database Initialization Complete';
    RAISE NOTICE '====================================';
    RAISE NOTICE 'Schemas created: hacs_core, hacs_data, hacs_vectors';
    RAISE NOTICE 'Extensions enabled: vector, uuid-ossp, btree_gin, btree_gist';
    RAISE NOTICE 'Tables ready for: memories, resources, audit logs, vector collections';
    RAISE NOTICE 'Vector dimensions configured for OpenAI embeddings (1536)';
    RAISE NOTICE 'Ready for HACS agent operations!';
    RAISE NOTICE '====================================';
END $$;