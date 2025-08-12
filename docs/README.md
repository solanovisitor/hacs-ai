# HACS Documentation

Welcome to the **Healthcare Agent Communication Standard (HACS)** documentation. HACS is a production-ready platform for deploying healthcare AI agents with structured memory, clinical reasoning, and FHIR compliance.

## 🚀 **Getting Started**

Start here to get HACS running in your healthcare organization:

- **[Quick Start Guide](quick-start.md)** - Get HACS deployed in 5 minutes
- **[Basic Usage](basic-usage.md)** - Core patterns and healthcare workflows
- **[Integration Guide](integrations.md)** - Connect to external systems

## 🏥 **Healthcare Focus**

HACS is purpose-built for healthcare AI:

- **Clinical Models**: Patient, Observation, Encounter data structures
- **Memory Systems**: Episodic, procedural, and executive memory for AI agents
- **Evidence Management**: Structured clinical reasoning with confidence scoring
- **FHIR Compliance**: Full compatibility with healthcare standards

## 🛠️ **Technical Documentation**

### Core System
- **[MCP Tools Reference](mcp-tools.md)** - Complete guide to 25+ healthcare tools
- **[Database Setup](database-migration.md)** - PostgreSQL + pgvector configuration
- **[Deployment Guide](deployment.md)** - Production deployment options

### Implementation Guides
- **[PGVector Integration](pgvector-integration.md)** - Vector storage for clinical data
- **[CLI Reference](cli.md)** - Command-line tools and utilities

## 🏗️ **Architecture Overview**

HACS consists of three main components:

1. **MCP Server** (Port 8000) - Provides 25+ healthcare tools via JSON-RPC
2. **LangGraph Agent** (Port 8001) - AI agent with memory and reasoning
3. **PostgreSQL + pgvector** (Port 5432) - Clinical data and vector storage

## 📊 **Key Features**

- **25+ Healthcare Tools**: Specialized tools for clinical workflows
- **Production Ready**: Sub-100ms response times for healthcare operations
- **FHIR Compliant**: Standards-based healthcare data models
- **Secure**: Actor-based permissions with comprehensive audit trails
- **Memory Enabled**: Structured memory for AI clinical reasoning

## 🎯 **Use Cases**

HACS enables healthcare organizations to:

- **Clinical Documentation**: Structure and store patient encounters
- **Evidence-Based Reasoning**: Track clinical guidelines and research
- **Memory Management**: Build AI agents with clinical context
- **Workflow Automation**: Standardize healthcare AI communications

## 🤝 **Contributing**

HACS is open source and welcomes contributions:

- **[GitHub Repository](https://github.com/solanovisitor/hacs-ai)** - Source code and issues
- **[Contributing Guidelines](../CONTRIBUTING.md)** - How to contribute
- **[Community Discussions](https://github.com/solanovisitor/hacs-ai/discussions)** - Q&A and support

---

**Ready to get started?** Follow the [Quick Start Guide](quick-start.md) to deploy HACS in your healthcare environment.