"""
LangGraph Functional API workflows for HACS HF ingestion.

Provides two entrypoints:
- register_template_from_instruction: discovers models via MCP, generates and registers a StackTemplate from markdown.
- instantiate_and_persist_stack: fills a registered template with context, instantiates resources, and persists them.
"""

from __future__ import annotations

import os
import asyncio
from typing import Any, Dict, List, Optional

from langgraph.func import entrypoint, task
from langgraph.checkpoint.memory import InMemorySaver

from hacs_utils.agents.mcp_client import HACSMCPClient
from hacs_models import StackTemplate, LayerSpec
from hacs_registry import instantiate_registered_stack, get_global_registry
from hacs_persistence.adapter import PostgreSQLAdapter
from hacs_core import Actor


# ===== MCP tasks =====

async def _get_mcp_langchain_tools() -> Dict[str, Any]:
    """Load MCP tools via langchain-mcp-adapters to satisfy streamable_http requirements."""
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
    except Exception:
        return {}

    base_url = os.getenv("HACS_MCP_SERVER_URL", "http://127.0.0.1:8000")
    url = base_url.rstrip("/")
    if not url.endswith("/mcp") and not url.endswith("/mcp/"):
        url = f"{url}/mcp/"
    headers: Dict[str, str] = {"Accept": "application/json, text/event-stream"}
    token = os.getenv("HACS_API_KEY")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    client = MultiServerMCPClient({
        "hacs-mcp": {"url": url, "transport": "streamable_http", "headers": headers}
    })
    tools = await client.get_tools()
    return {getattr(t, "name", getattr(t, "lc_namespace", "tool")): t for t in tools}


def _as_dict(result: Any) -> Dict[str, Any]:
    if isinstance(result, dict):
        return result
    try:
        import json
        return json.loads(str(result))
    except Exception:
        return {"result": str(result)}


@task
async def mcp_discover_resources() -> Dict[str, Any]:
    # Only use streamable_http client
    tools = await _get_mcp_langchain_tools()
    tool = tools.get("discover_hacs_resources")
    if tool is None:
        return {"success": False, "error": "MCP tools not available"}
    return _as_dict(await tool.ainvoke({}))


@task
async def mcp_get_schema(resource_type: str) -> Dict[str, Any]:
    tools = await _get_mcp_langchain_tools()
    tool = tools.get("get_hacs_resource_schema")
    if tool is None:
        return {"success": False, "error": "MCP tools not available"}
    return _as_dict(await tool.ainvoke({"resource_type": resource_type, "include_validation_rules": True}))


@task
async def mcp_generate_template_from_markdown(template_markdown: str, template_name: Optional[str]) -> Dict[str, Any]:
    tools = await _get_mcp_langchain_tools()
    tool = tools.get("generate_stack_template_from_markdown")
    if tool is None:
        return {"success": False, "error": "MCP tools not available"}
    args: Dict[str, Any] = {"template_markdown": template_markdown}
    if template_name:
        args["template_name"] = template_name
    return _as_dict(await tool.ainvoke(args))


@task
async def mcp_instantiate_from_context(template_name: str, context_text: str, use_llm: bool = False) -> Dict[str, Any]:
    tools = await _get_mcp_langchain_tools()
    tool = tools.get("instantiate_stack_from_context")
    if tool is None:
        return {"success": False, "error": "MCP tools not available"}
    args = {"template_name": template_name, "context": context_text, "use_llm": bool(use_llm)}
    return _as_dict(await tool.ainvoke(args))


# ===== Workflows =====

@entrypoint(checkpointer=InMemorySaver())
async def register_template_from_instruction(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inputs: { instruction_md: str, template_name?: str, fetch_schemas_for?: list[str] }
    Returns: { template_name, template_schema, discovered_resources, schemas_by_type }
    """
    instruction_md: str = inputs.get("instruction_md", "")
    template_name: Optional[str] = inputs.get("template_name")
    types_to_fetch: List[str] = inputs.get(
        "fetch_schemas_for",
        [
            "Patient",
            "Observation",
            "Condition",
            "Procedure",
            "MedicationRequest",
            "DiagnosticReport",
            "FamilyMemberHistory",
            "ServiceRequest",
            "Goal",
            "MedicationStatement",
            "DocumentReference",
            "Practitioner",
            "Organization",
            "Encounter",
            "Immunization",
        ],
    )

    # Propagate session id to client via env for server that requires it
    os.environ.setdefault("HACS_SESSION_ID", inputs.get("session_id", f"sess-{os.getpid()}"))
    discovered = await mcp_discover_resources()
    gen_res = await mcp_generate_template_from_markdown(instruction_md, template_name)

    # Fallback to local tool if MCP tools not available or failed
    if (not gen_res) or (not gen_res.get("success", False)):
        try:
            from hacs_tools.domains.development_tools import generate_stack_template_from_markdown_tool
            local_res = generate_stack_template_from_markdown_tool(
                template_markdown=instruction_md,
                template_name=template_name,
            )
            gen_res = getattr(local_res, "model_dump", lambda: {})() if hasattr(local_res, "model_dump") else (local_res or {})
        except Exception:
            pass

    schemas_by_type: Dict[str, Any] = {}
    for t in types_to_fetch:
        try:
            schemas_by_type[t] = await mcp_get_schema(t)
        except Exception as _:
            schemas_by_type[t] = {"success": False}

    return {
        "template_name": gen_res.get("template_name") or template_name,
        "template_schema": gen_res.get("template_schema", {}),
        "discovered_resources": discovered,
        "schemas_by_type": schemas_by_type,
        "message": gen_res.get("message"),
    }


@task
async def _persist_stack(database_url: str, stack: Dict[str, Any]) -> Dict[str, Any]:
    adapter = PostgreSQLAdapter(database_url=database_url)
    await adapter.connect()
    actor = Actor(id="hf-ingestion", name="HF Ingestion", role="system")
    persisted: Dict[str, Any] = {}
    try:
        for layer_name, resource in stack.items():
            try:
                saved = await adapter.save(resource, actor)
                persisted[layer_name] = getattr(saved, "id", None)
            except Exception as e:
                persisted[layer_name] = f"error: {e}"
    finally:
        try:
            await adapter.disconnect()
        except Exception:
            pass
    return persisted


@entrypoint(checkpointer=InMemorySaver())
async def instantiate_and_persist_stack(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inputs: { template_name: str, context_text: str, database_url?: str, use_llm?: bool }
    Returns: { persisted: dict, layers: list, stack_preview: dict }
    """
    template_name: str = inputs["template_name"]
    context_text: str = inputs.get("context_text", "")
    database_url: str = inputs.get(
        "database_url", os.getenv("DATABASE_URL", "postgresql://hacs:hacs_dev@localhost:5432/hacs")
    )
    use_llm: bool = bool(inputs.get("use_llm", False))

    # Ask MCP to instantiate for validation and metadata
    os.environ.setdefault("HACS_SESSION_ID", inputs.get("session_id", f"sess-{os.getpid()}"))
    mcp_result = await mcp_instantiate_from_context(template_name, context_text, use_llm)

    # Instantiate locally to get actual resource objects to persist
    # Lookup template by name in registry
    registry = get_global_registry()
    candidates = [r for r in registry._resources.values() if r.metadata.name == template_name]
    if not candidates:
        return {"error": f"Template not found: {template_name}", "mcp_result": mcp_result}
    tpl_res = sorted(candidates, key=lambda r: r.metadata.version, reverse=True)[0]
    # RegisteredResource stores serialized instance data in resource_instance
    instance = getattr(tpl_res, "resource_instance", {}) or {}
    variables_keys = list(instance.get("variables", {}).keys())

    # Fill all variables with the same context by default; the template usually expects one per section
    variables = {k: context_text for k in variables_keys}

    stack = instantiate_registered_stack(template_name, variables)
    persisted = await _persist_stack(database_url, stack)

    return {"persisted": persisted, "layers": mcp_result.get("layers", []), "stack_preview": {k: getattr(v, "resource_type", None) for k, v in stack.items()}}


__all__ = [
    "register_template_from_instruction",
    "instantiate_and_persist_stack",
]


