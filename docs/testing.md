# HACS Testing Guide

This guide coverstesting for HACS, including the new Phase 2 persistence, security, and vector integration features.

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ (for local testing)
- **UV package manager** (required): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Environment variables configured in `.env` file (see root directory)

### Running Tests

#### 1. Using the Test Runner Script (Recommended)

We provide a convenient test runner script:

```bash
# Validate environment setup
./run_tests.sh validate

# Run local unit tests
./run_tests.sh local unit

# Run Phase 2 integration tests (persistence, security, vector)
./run_tests.sh local phase2

# Run all local tests
./run_tests.sh local all

# Run full Docker test suite
./run_tests.sh docker
```

#### 2. Direct Docker Testing

Run the complete test suite with Docker:

```bash
# Start all services and runtests
docker-compose --profile test up --build

# View test results
docker logs hacs-test-runner
```

#### 3. Local Testing (Development)

For local development and debugging:

```bash
# Set up Python path
export PYTHONPATH="$PWD/packages/hacs-models/src:$PWD/packages/hacs-core/src:$PWD/packages/hacs-tools/src:$PWD/packages/hacs-auth/src:$PWD/packages/hacs-persistence/src:$PWD/packages/hacs-registry/src:$PWD/packages/hacs-utils/src:$PYTHONPATH"

# Install test dependencies with UV
uv pip install pytest pytest-asyncio

# Run specific test categories
python -m pytest tests/test_ci_essential.py -v                # Essential CI tests
python -m pytest tests/test_phase2_integration.py -v         # Phase 2 integration tests
python -m pytest tests/test_integration_end_to_end.py -v     # End-to-end tests

# Run specific domain tests
python -m pytest tests/test_hacs_tools_comprehensive.py::TestResourceManagement -v
```

#### 3. Manual MCP Integration Test

For debugging MCP server integration:

```bash
# Start MCP server
docker-compose up postgres qdrant hacs-mcp-server

# Run manual integration test
cd tests
python test_hacs_tools_comprehensive.py --mcp
```

## Test Architecture

### Test Categories

1. **Unit Tests**: Test tool definitions and basic functionality
2. **MCP Integration Tests**: Test tools via MCP server protocol
3. **End-to-End Tests**: Test complete workflows across multiple tools
4. **Performance Tests**: Test tool execution timing and resource usage

### Test Data

The test suite usestest data including:

- **Patients**: 3 test patients with complete demographics
- **Observations**: Blood pressure, vital signs, and clinical measurements
- **Encounters**: Ambulatory and emergency department visits
- **Conditions**: Hypertension, diabetes, and other chronic conditions
- **Memory Blocks**: Episodic, procedural, and executive memories
- **Vector Data**: Embeddings for semantic search testing
- **Organizations**: Healthcare systems and provider organizations

### Tool Coverage

The test suite covers all 42 HACS tools across 10 domains:

#### 🏥 Resource Management (5 tools)
- `create_hacs_record` - Create healthcare resources
- `get_hacs_record` - Retrieve resources by ID
- `update_hacs_record` - Update existing resources
- `delete_hacs_record` - Delete resources (soft/hard)
- `search_hacs_records` - Search with advanced filtering

#### 🩺 Clinical Workflows (4 tools)
- `execute_clinical_workflow` - Run clinical protocols
- `get_clinical_guidance` - Evidence-based recommendations
- `query_with_datarequirement` - Data-driven queries
- `validate_clinical_protocol` - Protocol validation

#### 🧠 Memory Operations (5 tools)
- `create_hacs_memory` - Store clinical memories
- `search_hacs_memories` - Semantic memory search
- `consolidate_memories` - Memory consolidation
- `retrieve_context` - Context-aware retrieval
- `analyze_memory_patterns` - Memory pattern analysis

#### 🔍 Vector Search (5 tools)
- `store_embedding` - Store vector embeddings
- `vector_similarity_search` - Semantic similarity search
- `vector_hybrid_search` - Hybrid text/vector search
- `get_vector_collection_stats` - Collection statistics
- `optimize_vector_collection` - Performance optimization

#### 📊 Schema Discovery (4 tools)
- `discover_hacs_resources` - Resource type discovery
- `get_hacs_resource_schema` - Schema introspection
- `analyze_resource_fields` - Field analysis
- `compare_resource_schemas` - Schema comparison

#### 🛠️ Development Tools (3 tools)
- `create_resource_stack` - Resource composition
- Template tools (preferred): `register_stack_template`, `generate_stack_template_from_markdown`, `instantiate_stack_template`

#### 🏥 FHIR Integration (4 tools)
- `convert_to_fhir` - HACS to FHIR conversion
- `validate_fhir_compliance` - FHIR validation
- `process_fhir_bundle` - Bundle processing
- `lookup_fhir_terminology` - Terminology lookup

#### 📈 Healthcare Analytics (4 tools)
- `calculate_quality_measures` - Quality metrics
- `analyze_population_health` - Population analysis
- `generate_clinical_dashboard` - Dashboard generation
- `perform_risk_stratification` - Risk assessment

#### 🤖 AI/ML Integration (3 tools)
- `deploy_healthcare_ai_model` - Model deployment
- `run_clinical_inference` - AI inference
- `preprocess_medical_data` - Data preprocessing

#### ⚙️ Admin Operations (5 tools)
- `run_database_migration` - Schema migrations
- `check_migration_status` - Migration status
- `describe_database_schema` - Schema description
- `get_table_structure` - Table introspection
- `test_database_connection` - Connection testing

## Configuration

### Environment Variables

Set these environment variables for testing:

```bash
# Database Configuration
DATABASE_URL=postgresql://hacs:hacs_dev@localhost:5432/hacs

# Vector Store Configuration  
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=""

# API Keys (optional for basic tests)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# MCP Server Configuration
MCP_SERVER_URL=http://localhost:8000
```

### Test Profiles

Use Docker Compose profiles to run different test scenarios:

```bash
# Basic services only
docker-compose up

# Include Qdrant vector store
docker-compose --profile with-qdrant up

# Run database migrations
docker-compose --profile migration up

# Runtests
docker-compose --profile test up
```

## Test Results

### Output Formats

Test results are available in multiple formats:

1. **Console Output**: Real-time test execution logs
2. **JSON Reports**: Detailed test results in `test_results/` directory
3. **Coverage Reports**: Code coverage analysis
4. **Performance Metrics**: Tool execution timing and resource usage

### Result Interpretation

- ✅ **Pass**: Tool executed successfully with expected results
- ❌ **Fail**: Tool execution failed or returned unexpected results
- ⏭️ **Skip**: Test skipped (e.g., MCP integration disabled)
- ⚠️ **Warning**: Tool executed but with warnings or performance issues

### Example Test Output

```
🚀 HACS ToolsTest Suite
=====================================

✅ MCP Server Health Check
   Server Status: ✅ Online
   MCP Endpoint: ✅ Ready
   Available Tools: 42

📊 Test Results Summary:
   Total Tools: 42
   Successful: 38
   Failed: 2
   Skipped: 2
   Success Rate: 90.5%
   Duration: 45.2 seconds

📁 Detailed results saved to: test_results/hacs_tools_test_results_20241215_143022.json
```

## Troubleshooting

### Common Issues

#### MCP Server Not Accessible
```bash
# Check if services are running
docker-compose ps

# View MCP server logs
docker logs hacs-mcp-server

# Test MCP server health
curl http://localhost:8000/health
```

#### Database Connection Issues
```bash
# Check database logs
docker logs hacs-postgres

# Test database connection
docker-compose exec postgres pg_isready -U hacs -d hacs

# Run migration manually
docker-compose --profile migration up
```

#### Tool Import Errors
```bash
# Check Python path configuration
docker-compose exec hacs-mcp-server python -c "import sys; print(sys.path)"

# Test tool imports
docker-compose exec hacs-mcp-server python -c "from hacs_tools.tools import ALL_HACS_TOOLS; print(len(ALL_HACS_TOOLS))"
```

### Performance Optimization

For better test performance:

1. **Use Local Database**: Set up PostgreSQL locally instead of Docker
2. **Parallel Testing**: Use pytest-xdist for parallel execution
3. **Test Caching**: Cache test data between runs
4. **Selective Testing**: Run only changed domains during development

```bash
# Parallel execution
python -m pytest tests/test_hacs_tools_comprehensive.py -n auto

# Selective testing
python -m pytest tests/test_hacs_tools_comprehensive.py -k "ResourceManagement or AdminOperations"

# Fast feedback loop
python -m pytest tests/test_hacs_tools_comprehensive.py --ff --tb=short
```

## Continuous Integration

### GitHub Actions Integration

The test suite integrates with GitHub Actions for CI/CD:

```yaml
# .github/workflows/test-hacs-tools.yml
name: HACS Tools Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run HACS Tools Tests
        run: |
          docker-compose --profile test up --build --abort-on-container-exit
```

### Test Coverage Requirements

- **Minimum Coverage**: 85% for all tool domains
- **Critical Tools**: 95% coverage for resource management and clinical workflows
- **Integration Tests**: All 42 tools must have at least one integration test

## Contributing

### Adding New Tests

1. **Add Test Data**: Update `examples/hacs_developer_agent/scripts/init-db.sql` with relevant test data
2. **Create Test Cases**: Add test methods to appropriate test classes
3. **Update Documentation**: Document new test scenarios in this guide
4. **Verify Coverage**: Ensure new tools havetest coverage

### Test Development Guidelines

- **Use Descriptive Names**: Test method names should clearly indicate what is being tested
- **Include Error Cases**: Test both success and failure scenarios
- **Validate Results**: Assert on specific result values, not just success/failure
- **Performance Aware**: Include timing assertions for performance-critical tools

## Support

For testing support:

1. **Documentation**: Refer to tool-specific documentation in `packages/hacs-tools/`
2. **Issues**: Report test failures as GitHub issues with full logs
3. **Discussions**: Use GitHub Discussions for test strategy questions
4. **Development**: Join the HACS development community for real-time support