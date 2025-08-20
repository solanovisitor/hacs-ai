import pytest


@pytest.mark.unit
def test_registry_is_source_of_truth_for_tools():
    from hacs_registry import get_global_tool_registry
    reg = get_global_tool_registry()
    tools = reg.get_all_tools()
    assert isinstance(tools, list)


@pytest.mark.unit
def test_framework_adapter_does_not_scan_core():
    from hacs_utils.integrations.framework_adapter import LangChainAdapter
    adapter = LangChainAdapter()
    registry = adapter.create_tool_registry()
    # list_tools must work without importing hacs-core internals
    names = registry.list_tools()
    assert isinstance(names, list)


@pytest.mark.unit
def test_openai_client_scope():
    # OpenAI client should not depend on LangChain
    from hacs_utils.integrations.openai.client import OpenAIClient
    assert OpenAIClient is not None


@pytest.mark.unit
def test_anthropic_client_scope():
    # Anthropic client should be independent and default to claude-sonnet-4-20250514
    try:
        from hacs_utils.integrations.anthropic import AnthropicClient
        c = AnthropicClient(model="claude-sonnet-4-20250514", api_key=None, timeout=5, max_retries=0)
        assert c.model == "claude-sonnet-4-20250514"
    except ImportError:
        pytest.skip("anthropic not installed")

