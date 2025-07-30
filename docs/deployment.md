# HACS Deployment Guide

This guide explains how to deploy HACS with automatic database migrations in various environments.

## 🚀 Quick Start

The easiest way to deploy HACS with automatic migrations:

```bash
# Clone the repository
git clone <hacs-repo>
cd hacs

# Deploy with automatic migrations
./scripts/deploy-with-migrations.sh production
```

## 📋 Prerequisites

- Docker & Docker Compose
- Environment variables configured (see below)
- PostgreSQL access (provided by Docker)

## 🔧 Environment Configuration

Create a `.env` file in the project root:

```bash
# Database Configuration
POSTGRES_PASSWORD=your_secure_password

# API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
HACS_API_KEY=your_hacs_api_key

# Optional: LangSmith Tracing
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
```

## 🏗️ Migration System Architecture

HACS includes an automatic migration system that ensures your database schema is always up-to-date:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │  HACS Migration │    │   HACS Services │
│   Container     │───▶│    Service      │───▶│   (MCP, Agent)  │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
      ↓ init.sql              ↓ run-migrations.sh       ↓ depends_on
   Extensions &           Complete Schema            Service Ready
   Basic Setup            Migration                 for Requests
```

### Migration Components

1. **`init.sql`** - Basic PostgreSQL setup (extensions, logging)
2. **`Dockerfile.migration`** - Specialized container for running migrations
3. **`scripts/run-migrations.sh`** - Migration execution script
4. **`hacs-migration` service** - Docker Compose service that runs migrations
5. **Service dependencies** - Other services wait for migrations to complete

## 🎯 Deployment Methods

### Method 1: Automatic Script (Recommended)

```bash
# Production deployment
./scripts/deploy-with-migrations.sh production

# Development deployment
./scripts/deploy-with-migrations.sh development

# Simple deployment (minimal services)
./scripts/deploy-with-migrations.sh simple
```

**What the script does:**
1. Stops existing services
2. Builds fresh Docker images
3. Starts PostgreSQL and waits for health check
4. Runs database migrations
5. Verifies migration status
6. Starts all HACS services
7. Displays service status and URLs

### Method 2: Manual Docker Compose

```bash
# Step 1: Start PostgreSQL
docker-compose up -d postgres

# Step 2: Wait for PostgreSQL to be ready
docker-compose exec postgres sh -c 'until pg_isready -U hacs; do sleep 2; done'

# Step 3: Run migrations
docker-compose run --rm hacs-migration

# Step 4: Start all services
docker-compose up -d

# Step 5: Check status
docker-compose ps
```

### Method 3: Development Mode

```bash
# Use development compose file with hot reloading
docker-compose -f docker-compose-dev.yml up --build
```

## 🔍 Migration Verification

### Check Migration Status

```bash
# View migration logs
docker-compose logs hacs-migration

# Check database schema
docker-compose exec postgres psql -U hacs -d hacs -c "
SELECT schemaname, tablename
FROM pg_tables
WHERE schemaname LIKE 'hacs_%'
ORDER BY schemaname, tablename;
"

# Check migration history
docker-compose exec postgres psql -U hacs -d hacs -c "
SELECT * FROM hacs_init_log ORDER BY timestamp DESC;
"
```

### Manual Migration Re-run

```bash
# Re-run migrations if needed
docker-compose run --rm hacs-migration

# Or run in existing MCP container
docker-compose exec hacs-mcp-server /app/scripts/run-migrations.sh
```

## 🏢 Production Deployment Considerations

### Security

```bash
# Use strong passwords
export POSTGRES_PASSWORD=$(openssl rand -base64 32)

# Restrict network access
# Configure firewall rules for only necessary ports
```

### Performance

```bash
# Scale services
docker-compose up -d --scale hacs-mcp-server=3

# Monitor resource usage
docker stats
```

### Backup

```bash
# Backup database
docker-compose exec postgres pg_dump -U hacs hacs > backup.sql

# Restore database
docker-compose exec -T postgres psql -U hacs hacs < backup.sql
```

## 🐛 Troubleshooting

### Common Issues

**Migration Failed:**
```bash
# Check logs
docker-compose logs hacs-migration

# Check PostgreSQL connectivity
docker-compose exec postgres pg_isready -U hacs

# Manual migration retry
docker-compose run --rm hacs-migration
```

**Service Startup Issues:**
```bash
# Check service dependencies
docker-compose ps

# Restart specific service
docker-compose restart hacs-mcp-server

# View detailed logs
docker-compose logs -f hacs-mcp-server
```

**Database Connection Issues:**
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U hacs -d hacs -c "SELECT 1;"

# Check environment variables
docker-compose exec hacs-mcp-server env | grep DATABASE_URL
```

### Log Locations

```bash
# Service logs
docker-compose logs [service-name]

# Migration logs
docker-compose logs hacs-migration

# PostgreSQL logs
docker-compose logs postgres

# All logs
docker-compose logs
```

## 📊 Monitoring

### Health Checks

All services include health checks that you can monitor:

```bash
# Check health status
docker-compose ps

# Test service endpoints
curl http://localhost:8000/  # MCP Server
curl http://localhost:8001/  # LangGraph Agent
curl http://localhost:6333/health  # Qdrant
```

### Service URLs

After successful deployment, access these endpoints:

- **MCP Server**: http://localhost:8000
- **LangGraph Agent**: http://localhost:8001
- **PostgreSQL**: localhost:5432
- **Qdrant Vector Store**: http://localhost:6333
- **LangGraph Studio** (dev only): http://localhost:8123

## 🔄 Updates and Maintenance

### Updating HACS

```bash
# Pull latest changes
git pull origin main

# Rebuild and redeploy with migrations
./scripts/deploy-with-migrations.sh production
```

### Schema Updates

When HACS resources are updated, the migration system automatically handles schema changes:

1. Update is deployed
2. Migration service detects schema changes
3. Database is automatically updated
4. Services restart with new schema

### Manual Schema Inspection

```bash
# Connect to database
docker-compose exec postgres psql -U hacs -d hacs

# List all HACS tables
\dt hacs_*.*

# Describe specific table
\d hacs_core.patients

# Check table counts
SELECT
  schemaname,
  tablename,
  (SELECT COUNT(*) FROM "'"||schemaname||'"."'"||tablename||'"') as row_count
FROM pg_tables
WHERE schemaname LIKE 'hacs_%'
ORDER BY schemaname, tablename;
```

## 🚨 Emergency Procedures

### Quick Recovery

```bash
# Stop all services
docker-compose down

# Remove problematic containers
docker-compose rm -f

# Full reset (WARNING: Data loss)
docker-compose down -v
docker-compose up --build
```

### Data Recovery

```bash
# If you have a backup
docker-compose exec -T postgres psql -U hacs hacs < backup.sql

# If migration fails, check the logs and retry
docker-compose run --rm hacs-migration
```