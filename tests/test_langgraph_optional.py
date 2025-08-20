import pytest


@pytest.mark.unit
def test_langgraph_optional_imports():
    try:
        from hacs_utils import LangGraphWorkflow, create_langgraph_workflow

        assert LangGraphWorkflow is not None
        assert callable(create_langgraph_workflow)
    except ImportError:
        pytest.skip("langgraph not installed")
