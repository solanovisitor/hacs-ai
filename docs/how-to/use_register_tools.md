# Use and register Tools

Use tools via registry, MCP, or LangChain. Register new tools with the unified registry decorator.

```python
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env", override=True)

from hacs_registry import get_global_tool_registry
from hacs_registry.tool_registry import register_tool

# Discover available tools
reg = get_global_tool_registry()
print("tools:", [t.name for t in reg.get_all_tools()[:10]])

# Register a custom tool (domain: modeling)
@register_tool(name="compute_bmi", domain="modeling", tags=["domain:modeling"])
def compute_bmi(height_cm: float, weight_kg: float) -> dict:
    return {"bmi": round(weight_kg / ((height_cm / 100.0) ** 2), 1)}

print("has bmi:", reg.get_tool("compute_bmi") is not None)
```

```
tools: ['pin_resource', 'compose_bundle', 'validate_resource', 'diff_resources', 'validate_bundle', 'list_models', 'describe_model', 'describe_models', 'list_model_fields', 'list_fields']
has bmi: True
```

### LangChain binding (with injected params)

```python
from hacs_utils.integrations.common.tool_loader import get_all_hacs_tools_sync, set_injected_params
from hacs_tools import load_tool, load_domain_tools

set_injected_params({"actor_name": "llm-agent-docs"})
pin_tool = load_tool("pin_resource")
modeling_tools = load_domain_tools("domain:modeling")
print('pin_tool loaded:', bool(pin_tool))
print('modeling_tools count:', len(modeling_tools))
```

```
pin_tool loaded: True
modeling_tools count: 18
```
