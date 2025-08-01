`# HACS Examples

This directory contains comprehensive examples and implementations demonstrating how to use HACS (Healthcare Agent Communication Standard) for various healthcare AI applications and workflows.

## 🏥 Available Examples

### 1. HACS Developer Agent (`hacs_developer_agent/`)

A production-ready LangGraph agent specialized for HACS system administration and database management:

- **Real Database Operations** - Migrations, schema inspection, connection testing
- **Administrative Tools** - Resource management, system monitoring, configuration
- **Deep Agent Framework** - Planning tools, file system, specialized sub-agents
- **Healthcare Template Generation** - Clinical consultation templates
- **Simplified State Architecture** - Developer-focused interface

**Key Features:**
- 🗄️ Database Administration - Real HACS database operations
- 🔧 Resource Management - HACS record creation and management  
- 📋 Template Generation - Clinical consultation templates
- 🎯 Planning Tools - Systematic task management
- 📁 File Operations - Configuration and documentation management
- 🔐 Security & Audit - Proper permissions and audit trails

**Use Cases:**
- HACS system setup and administration
- Database migration and schema management
- Clinical template generation and management
- System monitoring and troubleshooting
- Developer workflow automation

[View HACS Developer Agent Documentation →](hacs_developer_agent/README.md)

### 2. HACS Deep Agent (`hacs_deep_agent/`)

A comprehensive LangGraph-based healthcare AI agent that demonstrates advanced HACS capabilities:

- **37+ HACS Healthcare Tools** across 9 comprehensive domains
- **7 Specialized Clinical Subagents** for domain expertise
- **Healthcare Workflow Management** with clinical context preservation
- **HACS Resource State Management** using structured healthcare data
- **Iterative Tool Execution** for complex healthcare scenarios

**Key Features:**
- 🏥 Resource Management - Patient records, clinical data, healthcare operations
- 🧠 Clinical Workflows - Decision support, protocols, evidence-based care
- 💭 Memory Operations - Clinical knowledge, institutional learning
- 🔍 Vector Search - Medical knowledge retrieval, semantic search
- 📊 Healthcare Analytics - Quality measures, population health
- 🏥 FHIR Integration - Healthcare interoperability, standards compliance
- 🤖 AI/ML Integration - Healthcare AI deployment, clinical inference

**Use Cases:**
- Clinical care coordination across multiple providers
- Evidence-based clinical decision support
- Population health analytics and quality reporting
- Healthcare AI model deployment and management
- FHIR compliance and healthcare interoperability

[View HACS Deep Agent Documentation →](hacs_deep_agent/README.md)

## 🚀 Getting Started

### Prerequisites

1. **HACS Installation**: Ensure HACS packages are installed in your environment
2. **Python Dependencies**: Install required dependencies for the examples you want to run
3. **API Keys**: Set up appropriate API keys for AI models (Anthropic, OpenAI, etc.)

### Basic Setup

```bash
# Navigate to HACS project root
cd hacs-fresh

# Install HACS packages with uv
uv sync

# Activate the environment
source .venv/bin/activate  # or use uv shell

# Navigate to examples
cd examples
```

### Running Examples

#### HACS Developer Agent Example

```bash
cd hacs_developer_agent

# Install dependencies
uv sync

# Set up environment variables
export ANTHROPIC_API_KEY="your-api-key"
export DATABASE_URL="postgresql://user:pass@localhost:5432/hacs"

# Run the LangGraph development server
uv run langgraph dev --allow-blocking

# Access via browser at http://127.0.0.1:2024
# Or interact via LangGraph Studio
```

#### HACS Deep Agent Example

```bash
cd hacs_deep_agent

# Install additional dependencies for LangGraph agent
pip install langchain langgraph langchain-anthropic

# Set up API key
export ANTHROPIC_API_KEY="your-api-key"

# Run comprehensive examples
python example_usage.py
```

## 📋 Example Categories

### 🏥 Clinical Workflows
Examples demonstrating healthcare-specific workflows:
- Patient care coordination
- Clinical decision support
- Care plan management
- Quality improvement initiatives

### 📊 Healthcare Analytics
Examples showing population health and quality analytics:
- HEDIS quality measure calculation
- Population health analysis
- Clinical dashboard generation
- Risk stratification and predictive analytics

### 🔄 Healthcare Interoperability
Examples of healthcare data exchange and standards:
- FHIR resource conversion and validation
- Healthcare terminology lookup
- Bulk healthcare data operations
- Standards compliance validation

### 🤖 Healthcare AI/ML
Examples of AI/ML integration in healthcare:
- Healthcare AI model deployment
- Clinical inference and predictions
- Medical data preprocessing
- AI-powered clinical decision support

### 💭 Clinical Knowledge Management
Examples of healthcare knowledge organization:
- Clinical memory storage and retrieval
- Medical knowledge semantic search
- Healthcare best practices consolidation
- Evidence-based information access

## 🛠️ Development

### Adding New Examples

To contribute new examples:

1. **Create Example Directory**: Create a new directory under `examples/`
2. **Follow Structure**: Use consistent structure with README, main implementation, and usage examples
3. **Use HACS Resources**: Leverage HACS healthcare resources for state management
4. **Document Thoroughly**: Provide comprehensive documentation and usage examples
5. **Include Tests**: Add basic functionality tests where appropriate

### Example Structure Template

```
examples/
├── your_example/
│   ├── README.md                 # Comprehensive documentation
│   ├── __init__.py              # Package initialization
│   ├── main_implementation.py   # Core implementation
│   ├── example_usage.py         # Usage examples and demos
│   ├── healthcare_workflows.py  # Healthcare-specific workflows
│   └── tests/                   # Optional tests
│       └── test_basic.py
```

### Best Practices

1. **Healthcare Focus**: Always maintain healthcare domain focus with clinical use cases
2. **HACS Integration**: Use HACS tools and resources extensively
3. **Clinical Safety**: Prioritize patient safety and clinical best practices
4. **FHIR Compliance**: Ensure healthcare standards compliance where applicable
5. **Documentation**: Provide clear documentation with healthcare context
6. **Real-world Scenarios**: Use realistic healthcare scenarios and workflows

## 🏥 Healthcare Domains Covered

The examples cover comprehensive healthcare domains:

### Primary Care
- Patient registration and management
- Clinical assessment and documentation
- Preventive care and wellness tracking
- Care plan creation and follow-up

### Specialty Care
- Multi-specialty care coordination
- Complex clinical decision support
- Treatment plan optimization
- Specialist consultation workflows

### Population Health
- Quality measure calculation and reporting
- Population health trend analysis
- Health disparity identification
- Public health intervention planning

### Healthcare Operations
- Clinical workflow optimization
- Healthcare data management
- Regulatory compliance monitoring
- Performance improvement initiatives

### Healthcare Technology
- EHR integration and interoperability
- Healthcare AI deployment
- Clinical data analytics
- Digital health platform development

## 📚 Learning Path

### Beginner
1. Start with basic HACS tool usage examples
2. Understand HACS resource models (Patient, Observation, etc.)
3. Learn healthcare workflow patterns
4. Practice with simple clinical scenarios

### Intermediate
1. Explore HACS Deep Agent capabilities
2. Understand specialized clinical subagents
3. Learn healthcare-specific state management
4. Practice with multi-step healthcare workflows

### Advanced
1. Build custom healthcare AI applications
2. Integrate with external healthcare systems
3. Develop specialized clinical AI agents
4. Contribute to HACS ecosystem development

## 🤝 Contributing

We welcome contributions to the HACS examples:

1. **New Examples**: Submit new healthcare use case examples
2. **Improvements**: Enhance existing examples with better practices
3. **Documentation**: Improve documentation and tutorials
4. **Bug Fixes**: Report and fix issues in examples

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed contribution guidelines.

## 📄 License

All examples are licensed under the Apache-2.0 License - allowing both commercial and non-commercial use in healthcare environments.

## 🆘 Support

- **Issues**: Report problems with examples in the main HACS repository
- **Discussions**: Join healthcare AI discussions in the community forum
- **Documentation**: Refer to main HACS documentation for detailed API reference

---

**🎉 Ready to build healthcare AI?**

These examples provide comprehensive starting points for healthcare AI development with HACS. Each example demonstrates real-world healthcare scenarios with production-ready patterns.

*Built with ❤️ for healthcare AI developers* 