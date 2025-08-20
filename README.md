# 🏥 HACS — Context‑engineering framework for healthcare agents

[![License](https://img.shields.io/github/license/solanovisitor/hacs-ai)](https://github.com/solanovisitor/hacs-ai/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://python.org)
[![PyPI](https://img.shields.io/pypi/v/hacs-core)](https://pypi.org/project/hacs-core/)
[![Docs](https://img.shields.io/badge/docs-latest-blue)](./docs/README.md)

HACS (Healthcare Agent Communication Standard) is a context‑engineering framework for building safe, capable healthcare agents. It operationalizes the four strategies of context engineering — Write, Select, Compress, Isolate — for clinical settings with healthcare‑native models, tools, and security.

## Get started

Install the core packages (uv):

```bash
# Install uv and create a Python 3.11 environment
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv -p 3.11
source .venv/bin/activate

# Install HACS packages into the uv-managed venv
uv pip install -U hacs-core hacs-auth hacs-models hacs-tools hacs-utils hacs-persistence
```

Then follow the Quick Start to run the MCP server and the LangGraph developer agent:
- [Quick Start](./docs/quick-start.md)

### Quickstart (minimal code)

Bind HACS tools directly to an agent (LangGraph):

```python
from langgraph.prebuilt import create_react_agent
from hacs_utils.integrations.langchain.tools import langchain_tools

# Discover HACS tools (LangChain BaseTool) and create an agent that can call them
tools = langchain_tools()
agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",  # or "openai:gpt-4o"
    tools=tools,
    prompt="You are a healthcare assistant using HACS tools."
)

# Ask the agent to use tools (it will decide which to call)
result = agent.invoke({
    "messages": [
        {
            "role": "user",
            "content": "Create a Patient named John Smith (1980-05-15) and summarize current DB health"
        }
    ]
})
print(result)
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
- [HACS Tools reference](./docs/hacs-tools.md)
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
