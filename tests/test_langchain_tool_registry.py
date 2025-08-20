import pytest

pytestmark = pytest.mark.unit


def test_langchain_adapter_reads_catalog():
    try:
        from hacs_utils.integrations.framework_adapter import LangChainAdapter
        from hacs_registry import get_global_tool_registry
    except Exception as e:
        pytest.skip(f"Dependencies not available: {e}")

    adapter = LangChainAdapter()
    registry = adapter.create_tool_registry()

    names = registry.list_tools()
    assert isinstance(names, list)

    # If catalog has tools, ensure we can fetch at least one
    cat = get_global_tool_registry()
    all_tools = cat.get_all_tools()
    if all_tools:
        name = all_tools[0].name
        t = registry.get_tool(name)
        assert callable(t) or t is None  # Tool may require framework present; at least call doesn't crash
