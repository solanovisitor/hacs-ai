## Use and register Tools

Minimal, real examples for discovering, registering, and executing HACS tools through the unified registry. Shows the distinction between base tools (direct registry) and framework adapters. No mocks.

### Base HACS tools (direct registry)

```python
from dotenv import load_dotenv
load_dotenv()

from hacs_registry import get_global_tool_registry
from hacs_registry.tool_registry import register_tool

# Discover and register
reg = get_global_tool_registry()
print("discovered:", len(reg.get_all_tools()))

@register_tool(name="compute_bmi", domain="modeling", tags=["domain:modeling"]) 
def compute_bmi(height_cm: float, weight_kg: float) -> dict:
    return {"bmi": round(weight_kg / ((height_cm / 100.0) ** 2), 1)}

# Execute tools directly
bmi_result = reg.get_tool_function("compute_bmi")(175, 70)
pin_result = reg.get_tool_function("pin_resource")("Patient", {"full_name": "Alice Nguyen", "gender": "female", "age": 34})

print("bmi:", bmi_result)
print("pin_success:", pin_result.success)
```

Example output:
```
discovered: 75
bmi: {'bmi': 22.9}
pin_success: True
```

### Tool search and metadata

```python
# Search and inspect tools
modeling_tools = reg.search_tools(domain="modeling")
pin_tool = reg.get_tool("pin_resource")

print("modeling:", [t.name for t in modeling_tools[:5]])
print("pin_metadata:", pin_tool.domain, pin_tool.requires_actor)
```

Example output:
```
modeling: ['pin_resource', 'compose_bundle', 'validate_resource', 'diff_resources', 'validate_bundle']
pin_metadata: modeling False
```

### LangChain adapter (framework wrapping)

```python
from hacs_utils.integrations.framework_adapter import LangChainAdapter

# Adapt tools for LangChain
adapter = LangChainAdapter()
lc_registry = adapter.create_tool_registry()
lc_tools = lc_registry.list_tools() if hasattr(lc_registry, "list_tools") else []

print("langchain_tools:", len(lc_tools))
```

Example output:
```
langchain_tools: 75
```

### Create resources end-to-end

```python
# Custom BMI + Patient creation
bmi = reg.get_tool_function("compute_bmi")(180, 75)
patient = reg.get_tool_function("pin_resource")("Patient", {"full_name": "Test Patient", "age": 30})

print("bmi:", bmi)
print("patient_id:", patient.data["resource"]["id"])
```

Example output:
```
bmi: {'bmi': 23.1}
patient_id: patient-7372c609
```
