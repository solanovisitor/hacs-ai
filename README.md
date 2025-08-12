# 🏥 HACS — Healthcare Context Engineering for AI Agents

[![License](https://img.shields.io/github/license/solanovisitor/hacs-ai)](https://github.com/solanovisitor/hacs-ai/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://python.org)
[![PyPI](https://img.shields.io/pypi/v/hacs-core)](https://pypi.org/project/hacs-core/)
[![Docs](https://img.shields.io/badge/docs-latest-blue)](./docs/README.md)

HACS (Healthcare Agent Communication Standard) is a protocol‑first framework for building healthcare AI agents. It provides healthcare‑native models, tools, and security to implement the four essential strategies of context engineering — Write, Select, Compress, Isolate — safely and efficiently.

## Get started

```bash
pip install -U hacs-core hacs-auth hacs-models hacs-tools hacs-utils hacs-persistence
```

- Try the runnable LangGraph developer agent: `examples/hacs_developer_agent/`
- Use `docker-compose.yml` to start the MCP server and PostgreSQL (with pgvector)

## Core benefits

- Healthcare context engineering: built‑in patterns to write clinical memory, select essential data, compress safely, and isolate per regulatory boundaries
- Actor‑based security: roles, permissions, and audit trails designed for PHI and compliance
- FHIR‑aligned models: type‑safe Pydantic models for Patient, Observation, Encounter, and more
- Protocol‑first tools (MCP): 40+ tools exposed via Model Context Protocol, usable from any agent framework
- Framework integrations: Works with LangGraph/LangChain and any LLM provider (Anthropic, OpenAI, etc.)

## Packages at a glance

- `hacs-core`: Clinical protocols and foundational abstractions
- `hacs-models`: Pure, FHIR‑aligned healthcare data models
- `hacs-tools`: 40+ HACS tools for clinical workflows and data operations
- `hacs-utils`: Integrations, MCP server, and developer utilities
- `hacs-persistence`: PostgreSQL + pgvector adapters and repositories
- `hacs-registry`: Resource and tool registration, validation, and versioning
- `hacs-auth`: Authentication, actors, permissions, and audit logging

See package READMEs and the docs for details.

## Optional services

- MCP Server: expose HACS tools via JSON‑RPC and streamable HTTP
- PostgreSQL + pgvector: persistence and vector search for clinical embeddings
- LangGraph Developer Agent: a ready‑to‑run agent for local development

## Documentation

- Quick start: `docs/quick-start.md`
- Hacs Tools reference: `docs/healthcare-tools.md`
- Using MCP with LangGraph: `docs/mcp_langgraph.md`
- API reference: `docs/api-reference.md`

## Community & support

- Issues: https://github.com/solanovisitor/hacs-ai/issues
- Discussions: https://github.com/solanovisitor/hacs-ai/discussions

## License

MIT — see `LICENSE`.
