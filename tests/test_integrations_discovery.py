import pytest
from dotenv import load_dotenv


@pytest.mark.unit
def test_list_available_integrations_and_info():
    load_dotenv()
    from hacs_utils import list_available_integrations, get_integration_info

    names = list_available_integrations()
    assert isinstance(names, list)

    info = get_integration_info()
    # Ensure known keys exist
    for key in [
        "openai",
        "anthropic",
        "pinecone",
        "qdrant",
        "langgraph",
        "mcp",
    ]:
        assert key in info
        assert "description" in info[key]
        assert "available" in info[key]

    # Availability flags should be consistent
    for name in names:
        assert info.get(name, {}).get("available", False) is True


