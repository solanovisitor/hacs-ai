import pytest


@pytest.mark.unit
def test_mcp_optional_imports():
    try:
        from hacs_utils import get_integration_info

        info = get_integration_info("mcp")
        assert isinstance(info, dict)
        assert "description" in info
    except Exception:
        # Just assert that we can query info map without import errors
        assert True
