# Quick Start Guide

Get up and running with HACS in minutes using UV workspace.

## Prerequisites

- **Python 3.11+** - HACS requires modern Python
- **[uv](https://github.com/astral-sh/uv)** - Fast Python package manager
- **Docker & Docker Compose** - For MCP server and database

## Installation

### 1. Install UV

```bash
# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

### 2. Setup HACS Workspace

```bash
# Clone repository
git clone https://github.com/solanovisitor/hacs-ai.git
cd hacs

# Sync UV workspace (installs all packages)
uv sync

# Activate environment
source .venv/bin/activate
```

### 3. Start Services

```bash
# Start all HACS services with Docker
docker-compose up -d

# Verify MCP server is running
curl http://localhost:8000/
```

## Basic Usage

### Python API

```python
# Use UV to run Python with HACS environment
uv run python

# Import HACS components
from hacs_core import Patient, Observation, Actor
from hacs_tools import create_hacs_record

# Create a patient
patient = Patient(
    full_name="John Doe",
    birth_date="1980-01-01",
    gender="male"
)

print(f"Created patient: {patient.id}")
```

### MCP Tools via HTTP

```bash
# List available healthcare tools
curl -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}' \
  http://localhost:8000/

# Create patient record
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "create_hacs_record",
      "arguments": {
        "resource_type": "Patient",
        "resource_data": {
          "full_name": "Jane Smith",
          "birth_date": "1985-05-15",
          "gender": "female"
        }
      }
    },
    "id": 1
  }' \
  http://localhost:8000/
```

## Development Workflow

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_core.py

# Run with coverage
uv run pytest --cov=packages
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Type checking
uv run mypy packages/
```

### Adding Dependencies

```bash
# Add workspace dependency
uv add requests

# Add development dependency
uv add --dev pytest-mock

# Add to specific package
cd packages/hacs-core
uv add pydantic-extra-types
```

## Troubleshooting

### Common Issues

**Import errors after installation:**
```bash
# Ensure UV environment is active
source .venv/bin/activate

# Re-sync workspace
uv sync
```

**MCP server not responding:**
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs hacs-mcp-server

# Restart services
docker-compose restart
```

**Database connection issues:**
```bash
# Check PostgreSQL is running
docker-compose logs postgres

# Verify environment variables
echo $DATABASE_URL
```

## Next Steps

- **[Basic Usage](basic-usage.md)** - Learn core HACS patterns
- **[Integration Guide](integrations.md)** - Connect external services
- **[CLI Reference](cli.md)** - Command-line tools
- **[API Documentation](api-reference.md)** - Complete API reference

---

**Need help?** Check our [GitHub Discussions](https://github.com/solanovisitor/hacs-ai/discussions) or [open an issue](https://github.com/solanovisitor/hacs-ai/issues).