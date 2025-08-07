# HACS Documentation

Welcome to the **Healthcare Agent Communication Standard (HACS)** documentation. HACS is a modular framework of Python packages for building healthcare AI applications with structured memory, clinical reasoning, and FHIR compliance.

## 🚀 **Getting Started**

Start here to get HACS integrated into your healthcare AI projects:

- **[Quick Start Guide](quick-start.md)** - Install HACS packages and build your first agent
- **[Basic Usage](basic-usage.md)** - Core patterns and healthcare workflows
- **[Integration Guide](integrations.md)** - Connect to AI frameworks and external systems

## 🏥 **Healthcare Focus**

HACS is purpose-built for healthcare AI:

- **Clinical Models**: Patient, Observation, Encounter data structures
- **Memory Systems**: Episodic, procedural, and executive memory for AI agents
- **Evidence Management**: Structured clinical reasoning with confidence scoring
- **FHIR Compliance**: Full compatibility with healthcare standards

## 🛠️ **Technical Documentation**

### Core System
- **[Healthcare Tools](healthcare-tools.md)** - Complete guide to 42+ healthcare tools
- **[Testing Guide](testing.md)** - Testing and validation procedures
- **[CLI Reference](cli.md)** - Command-line tools and utilities

### Implementation Guides
- **[Integration Guide](integrations.md)** - Connect to external systems
- **[Branch Management](branch-management.md)** - Development workflow

## 🏗️ **Architecture Overview**

HACS is structured as **core packages** with **optional service add-ons**:

### **🧬 Core HACS Framework**
1. **`hacs-core`** - Protocols, interfaces, and core abstractions
2. **`hacs-models`** - FHIR-compliant healthcare data models
3. **`hacs-registry`** - Resource registration and lifecycle management
4. **`hacs-persistence`** - Data storage abstractions and repositories
5. **`hacs-tools`** - Healthcare-specific AI tools and workflows
6. **`hacs-utils`** - Integrations and utilities for AI frameworks

### **⚡ Optional Service Add-ons**
- **MCP Server** (Port 8000) - Makes tools accessible via JSON-RPC
- **PostgreSQL + pgvector** (Port 5432) - Convenient persistence implementation
- **LangGraph Agent** - Ready-to-use AI agent for development

> **💡 Key Distinction**: The HACS **packages** are the framework - you can use them in any Python application. The **services** are optional convenience tools that make development easier but aren't required.

## 📊 **Key Features**

- **42+ Healthcare Tools**: Specialized tools for clinical workflows
- **Production Ready**: Sub-100ms response times for healthcare operations
- **FHIR Compliant**: Standards-based healthcare data models
- **Secure**: Actor-based permissions with comprehensive audit trails
- **Memory Enabled**: Structured memory for AI clinical reasoning

## 🎯 **Use Cases**

HACS packages enable developers to build:

- **Healthcare AI Agents**: LangChain/LangGraph agents with medical knowledge
- **Clinical Workflows**: CrewAI multi-agent systems for healthcare teams
- **FHIR Applications**: Standards-compliant healthcare data processing
- **Medical Chatbots**: Context-aware AI with structured clinical memory
- **Research Tools**: Evidence-based reasoning with confidence scoring

## 🤝 **Contributing**

HACS is open source and welcomes contributions:

- **[GitHub Repository](https://github.com/solanovisitor/hacs-ai)** - Source code and issues
- **[Contributing Guidelines](../CONTRIBUTING.md)** - How to contribute
- **[Community Discussions](https://github.com/solanovisitor/hacs-ai/discussions)** - Q&A and support

---

**Ready to get started?** Follow the [Quick Start Guide](quick-start.md) to deploy HACS in your healthcare environment.