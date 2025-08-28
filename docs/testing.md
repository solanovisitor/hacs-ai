# HACS Testing Guide

This guide covers testing for HACS, including the new Phase 2 persistence, security, and vector integration features.

For environment setup basics, see the [Quick Start](quick-start.md).

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
scripts/scripts/run_tests.sh validate

# Run local unit tests
scripts/scripts/run_tests.sh local unit

# Run Phase 2 integration tests (persistence, security, vector)
scripts/scripts/run_tests.sh local phase2

# Run all local tests
scripts/scripts/run_tests.sh local all

# Run full Docker test suite
scripts/scripts/run_tests.sh docker
```

#### 2. Direct Docker Testing

Run the complete test suite with Docker:

```bash
# Start all services and run tests
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
python -m pytest tests/test_facades.py -v                   # Facade API tests
python -m pytest tests/test_integration_end_to_end.py -v     # End-to-end tests

# Run specific domain tests
python -m pytest tests/test_hacs_tools_schema.py::TestModeling -v
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

The test suite uses test data including:

- **Patients**: 3 test patients with complete demographics
- **Observations**: Blood pressure, vital signs, and clinical measurements
- **Encounters**: Ambulatory and emergency department visits
- **Conditions**: Hypertension, diabetes, and other chronic conditions
- **Memory Blocks**: Episodic, procedural, and executive memories
- **Vector Data**: Embeddings for semantic search testing
- **Organizations**: Healthcare systems and provider organizations

### Tool Coverage (4 domains)

- Modeling: `describe_models`, `list_model_fields`, `plan_bundle_schema`, `validate_resource`, `add_bundle_entries`
- Extraction: `suggest_mapping`, `extract_values`, `apply_mapping`, `summarize_context`
- Database (records): `save_record`, `read_record`, `update_record`, `delete_record`, `search_records`
- Agents: `write_scratchpad`, `inject_preferences`, `store_memory`, `retrieve_memories`, `select_tools_for_task`

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

# Run tests
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
🚀 HACS Tools Test Suite
=====================================

✅ MCP Server Health Check
   Server Status: ✅ Online
   MCP Endpoint: ✅ Ready
   Available Tools: 41

📊 Test Results Summary:
   Total Tools: 20
   Successful: 40
   Failed: 0
   Skipped: 1
   Success Rate: 97.5%
   Duration: 32.8 seconds

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
- **Integration Tests**: All tools must have at least one integration test

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