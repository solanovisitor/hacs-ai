# 🏥 HACS — Context‑engineering framework for healthcare agents

[![License](https://img.shields.io/github/license/solanovisitor/hacs-ai)](https://github.com/solanovisitor/hacs-ai/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://python.org)
[![PyPI](https://img.shields.io/pypi/v/hacs-core)](https://pypi.org/project/hacs-core/)
[![Docs](https://img.shields.io/badge/docs-latest-blue)](./docs/README.md)

HACS (Healthcare Agent Communication Standard) is a protocol‑first, context‑engineering framework for building safe, capable healthcare agents. It operationalizes the four strategies of context engineering — Write, Select, Compress, Isolate — for clinical settings with healthcare‑native models, tools, and security.

## Get started

Install the core packages:

```bash
pip install -U hacs-core hacs-auth hacs-models hacs-tools hacs-utils hacs-persistence
```

Then follow the Quick Start to run the MCP server and the LangGraph developer agent:
- [Quick Start](./docs/quick-start.md)

### Quickstart (minimal code)

Start the MCP server (in a separate terminal):

```bash
python -m hacs_utils.mcp.fastmcp_server
```

Call a HACS tool over MCP (JSON-RPC) to create a Patient record:

```python
import os, requests

url = os.getenv("HACS_MCP_SERVER_URL", "http://127.0.0.1:8000")

payload = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "create_hacs_record",
        "arguments": {
            "resource_type": "Patient",
            "resource_data": {
                "full_name": "John Smith",
                "birth_date": "1980-05-15",
                "gender": "male"
            }
        }
    },
    "id": 1,
}

print(requests.post(url, json=payload).json())
```

## Why HACS

- **Context engineering for healthcare**: Write clinical memory; Select essential data; Compress safely; Isolate by regulatory boundaries.
- **Protocol‑first tools (MCP)**: 40+ tools via Model Context Protocol; usable from any agent framework.
- **Healthcare‑native models**: FHIR‑aligned, type‑safe Pydantic models for core clinical entities.
- **Actor‑based security**: Roles, permissions, sessions, and audit trails for PHI and compliance.
- **Ecosystem‑ready**: Works with LangGraph/LangChain and common LLM providers (Anthropic, OpenAI, etc.).

## Components (high‑level)

- Models & protocols: `hacs-core`, `hacs-models`
- Tools & registry: `hacs-tools`, `hacs-registry`
- Integrations & MCP server: `hacs-utils`
- Persistence adapters: `hacs-persistence` (PostgreSQL + pgvector)
- Security & IAM: `hacs-auth`

Note: Package‑level docs evolve; use the links below for the most up‑to‑date guidance.

## Architecture at a glance

| Layer | Package(s) | Purpose | Interfaces |
| --- | --- | --- | --- |
| Models & Protocols | `hacs-core`, `hacs-models` | Clinical data models and protocol contracts | Pydantic models, protocol utils |
| Tools & Registry | `hacs-tools`, `hacs-registry` | Healthcare tools and resource/Tool registry | MCP Tools, registry APIs |
| Integrations & MCP | `hacs-utils` | MCP server and framework adapters | JSON-RPC, streamable HTTP, adapters |
| Persistence | `hacs-persistence` | PostgreSQL + pgvector adapters and repositories | DB adapters, migrations |
| Security & IAM | `hacs-auth` | Actor model, permissions, sessions, audit | Decorators, token utilities |

## Learn more

- [Quick Start](./docs/quick-start.md)
- [HACS Tools reference](./docs/healthcare-tools.md)
- [Use MCP with LangGraph](./docs/mcp_langgraph.md)
- [Integrations overview](./docs/integrations.md)
- [Testing and CI](./docs/testing.md)
- [API reference (selected)](./docs/api-reference.md)

## Optional services

- MCP Server — expose HACS tools via JSON‑RPC and streamable HTTP
- PostgreSQL + pgvector — persistence and vector search for clinical embeddings
- LangGraph Developer Agent — a ready‑to‑run agent for local development (`examples/hacs_developer_agent/`)

## Community & support

- Issues: https://github.com/solanovisitor/hacs-ai/issues
- Discussions: https://github.com/solanovisitor/hacs-ai/discussions

## License

MIT — see `LICENSE`.
