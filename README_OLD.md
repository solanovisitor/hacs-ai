# HACS: Healthcare Agent Communication Standard

<div align="center">

![CI](https://img.shields.io/github/actions/workflow/status/solanovisitor/hacs-ai/ci.yml?branch=main)
![License](https://img.shields.io/github/license/solanovisitor/hacs-ai)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)

**🏥 The definitive framework for healthcare AI agents**

*FHIR-compliant • Memory-enabled • Protocol-first*

[**🚀 Quick Start**](#-quick-start) • [**📚 Documentation**](docs/) • [**🛠️ Tools**](#-healthcare-tools) • [**🤝 Contributing**](CONTRIBUTING.md)

</div>

---

## 🎯 What is HACS?

HACS (Healthcare Agent Communication Standard) is a **production-ready framework** that enables healthcare AI systems with structured memory, clinical reasoning, and FHIR compliance. Built with **protocol-first architecture**, HACS provides **25+ specialized healthcare tools** across 9 comprehensive domains for patient data management, clinical workflows, and evidence-based reasoning.

### 🌟 Why HACS?

| Challenge | Traditional Approach | **HACS Solution** |
|-----------|---------------------|-------------------|
| **Clinical Memory** | Unstructured text storage | ✅ Episodic, procedural & executive memory types |
| **Healthcare Data** | Generic JSON schemas | ✅ FHIR-compliant models with clinical validation |
| **Evidence Tracking** | Manual documentation | ✅ Structured evidence with confidence scoring |
| **Agent Integration** | Custom implementations | ✅ MCP standard with healthcare tools |
| **Compliance** | Ad-hoc security | ✅ Actor-based permissions with audit trails |

> **🏥 Built for Healthcare**: HACS extends FHIR standards specifically for AI agent cognition and communication in clinical environments.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager
- Docker & Docker Compose (for services)

### Installation & Setup

```bash
# 1. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone and setup HACS workspace
git clone https://github.com/solanovisitor/hacs-ai.git
cd hacs-ai

# 3. Install all packages
uv sync

# 4. Start services (PostgreSQL + MCP Server)
docker-compose up -d

# 5. Test the installation
uv run python -c "from hacs_auth import Actor, ActorRole; print('✅ HACS installed successfully')"
```

### First Healthcare Agent

```python
from hacs_auth import Actor, ActorRole
from hacs_core import get_llm_provider
from hacs_utils.mcp.tools import execute_hacs_tool

# Create a healthcare actor
physician = Actor(
    name="Dr. Sarah Chen",
    role=ActorRole.PHYSICIAN,
    organization="General Hospital"
)

# Execute healthcare workflows
result = await execute_hacs_tool(
    "create_resource",
    {
        "resource_type": "Patient",
        "resource_data": {
            "full_name": "John Doe",
            "date_of_birth": "1980-01-01"
        }
    },
    actor=physician
)
```

## 🏗️ Architecture

HACS follows **SOLID principles** with a **protocol-first design**:

```
┌─────────────────────────────────────────────────────────┐
│                    Your Healthcare AI                   │
├─────────────────────────────────────────────────────────┤
│  🔧 hacs-utils    │  Framework integrations & adapters  │
│  🏥 hacs-tools    │  25+ healthcare-specific tools      │
│  📊 hacs-registry │  Resource & tool discovery          │
├─────────────────────────────────────────────────────────┤
│  💾 hacs-persistence │ Database & vector operations    │
│  🔒 hacs-auth        │ Actor-based security & sessions │
│  🏗️ hacs-infrastructure │ DI container & monitoring  │
├─────────────────────────────────────────────────────────┤
│  🧠 hacs-core     │  Base protocols & infrastructure    │
│  📋 hacs-models   │  FHIR-compliant data models        │
└─────────────────────────────────────────────────────────┘
```

### Key Design Principles

- **Protocol-First**: All components implement clean protocols for maximum flexibility
- **Actor-Based Security**: Unified security model for humans and AI agents
- **FHIR Compliance**: Healthcare interoperability standards throughout
- **Memory-Centric**: Structured memory types for clinical reasoning
- **Framework Agnostic**: Works with LangChain, OpenAI, Anthropic, etc.

## 🛠️ Healthcare Tools

HACS provides **25+ healthcare tools** organized into 9 domains:

### 🔍 **Model Discovery & Development** (5 tools)
- Resource schema discovery and analysis
- Clinical template generation
- Model composition and validation

### 📋 **Registry & CRUD Operations** (6 tools)  
- Patient, Observation, Encounter management
- FHIR-compliant resource operations
- Clinical data validation

### 🔍 **Search & Discovery** (2 tools)
- Semantic healthcare record search
- Clinical knowledge retrieval

### 🧠 **Memory Management** (5 tools)
- Episodic memory for patient interactions
- Procedural memory for clinical protocols
- Executive memory for decision-making
- Memory consolidation and context retrieval

### ✅ **Validation & Schema** (3 tools)
- Clinical data validation
- FHIR compliance checking
- Healthcare schema analysis

### 🎨 **Advanced Model Tools** (3 tools)
- LLM-optimized model generation
- Clinical view creation
- Field suggestion systems

### 📚 **Knowledge Management** (1 tool)
- Clinical decision support knowledge

## 📦 Package Structure

HACS is organized as a **UV workspace** with 9 core packages:

| Package | Purpose | PyPI Status |
|---------|---------|-------------|
| **hacs-models** | FHIR-compliant data models | 🚀 Ready |
| **hacs-core** | Base protocols & infrastructure | 🚀 Ready |
| **hacs-auth** | Actor-based security & sessions | 🚀 Ready |
| **hacs-infrastructure** | Dependency injection & monitoring | 🚀 Ready |
| **hacs-persistence** | Database & vector operations | 🚀 Ready |
| **hacs-tools** | Healthcare-specific tools | 🚀 Ready |
| **hacs-registry** | Resource & tool discovery | 🚀 Ready |
| **hacs-utils** | Framework integrations | 🚀 Ready |
| **hacs-cli** | Command-line interface | 🚀 Ready |

Each package can be installed independently:

```bash
pip install hacs-core hacs-auth hacs-tools  # Core functionality
pip install hacs-utils[langchain]           # LangChain integration
pip install hacs-persistence[postgresql]    # Database support
```

## 🏥 Healthcare Compliance

### FHIR Compliance
- ✅ FHIR R4 resource models
- ✅ Clinical terminologies (SNOMED, LOINC)
- ✅ Healthcare interoperability standards

### Security & Privacy
- ✅ Actor-based authentication
- ✅ Role-based access control (RBAC)
- ✅ Comprehensive audit trails
- ✅ HIPAA-compliant patterns

### Clinical Features
- ✅ Evidence-based reasoning
- ✅ Clinical decision support
- ✅ Structured clinical memory
- ✅ Confidence scoring

## 🔧 Integration Examples

### Using with LangChain

```python
from langchain_openai import ChatOpenAI
from hacs_utils.integrations.langchain import HACSLangChainAdapter

# Wrap any LLM for HACS compatibility
llm = ChatOpenAI(model="gpt-4")
hacs_llm = HACSLangChainAdapter(llm)

# Use with HACS tools
tools = hacs_llm.get_healthcare_tools()
agent = create_react_agent(hacs_llm, tools)
```

### MCP Server Integration

```bash
# Start HACS MCP Server
docker-compose up -d hacs-mcp-server

# Available at http://localhost:8000 with 25+ healthcare tools
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

### Direct Tool Usage

```python
from hacs_tools.domains import clinical_workflows

# Execute clinical workflow
result = await clinical_workflows.execute_clinical_workflow(
    workflow_type="patient_assessment",
    patient_id="patient_123",
    clinical_data={...},
    actor=physician
)
```

## 📊 Running Example

See the complete **Healthcare Developer Agent** in [`examples/hacs_developer_agent/`](examples/hacs_developer_agent/):

```bash
cd examples/hacs_developer_agent
uv run langgraph dev  # Starts interactive agent with HACS tools
```

## 🧪 Testing

```bash
# Run core tests
uv run pytest tests/ -v

# Run integration tests
uv run pytest tests/test_integration_end_to_end.py -v

# Run with coverage
uv run pytest --cov=packages --cov-report=html
```

## 📚 Documentation

- [**Quick Start Guide**](docs/quick-start.md) - Get up and running
- [**Basic Usage**](docs/basic-usage.md) - Core concepts and patterns
- [**CLI Reference**](docs/cli.md) - Command-line tools
- [**Integration Guide**](docs/integrations.md) - Framework integrations
- [**Testing Guide**](docs/testing.md) - Testing patterns

### Architecture Documentation
- [**ADR-001**: SOLID Principles Compliance](docs/architecture/ADR-001-SOLID-principles-compliance.md)
- [**ADR-002**: Actor-Based Security](docs/architecture/ADR-002-actor-based-security.md)
- [**ADR-003**: Protocol-First Design](docs/architecture/ADR-003-protocol-first-design.md)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/yourusername/hacs-ai.git
cd hacs-ai

# Install development dependencies
uv sync --all-extras --dev

# Run pre-commit hooks
pre-commit install

# Run tests
uv run pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=solanovisitor/hacs-ai&type=Date)](https://star-history.com/#solanovisitor/hacs-ai&Date)

## 💪 Enterprise Support

For enterprise deployments, consulting, and custom healthcare AI solutions, contact [solanovisitor@gmail.com](mailto:solanovisitor@gmail.com).

---

<div align="center">

**Built with ❤️ for Healthcare AI**

[GitHub](https://github.com/solanovisitor/hacs-ai) • [Documentation](docs/) • [Issues](https://github.com/solanovisitor/hacs-ai/issues) • [Discussions](https://github.com/solanovisitor/hacs-ai/discussions)

</div>