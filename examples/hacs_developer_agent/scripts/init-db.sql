-- HACS Database Initialization Script
-- This script sets up the basic database structure for HACS

-- Enable the pgvector extension for vector operations
CREATE EXTENSION IF NOT EXISTS vector;

-- Create basic HACS schema
CREATE SCHEMA IF NOT EXISTS hacs;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON SCHEMA hacs TO hacs;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA hacs TO hacs;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA hacs TO hacs;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA hacs GRANT ALL ON TABLES TO hacs;
ALTER DEFAULT PRIVILEGES IN SCHEMA hacs GRANT ALL ON SEQUENCES TO hacs;

-- Log successful initialization
\echo 'HACS database initialized successfully with pgvector extension'