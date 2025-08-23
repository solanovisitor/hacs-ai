import os
import pytest

pytestmark = pytest.mark.llm


def test_openai_connectivity_minimal():
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set; skipping LLM smoke test")

    try:
        from langchain_openai import ChatOpenAI
    except Exception as e:
        pytest.skip(f"langchain_openai not available: {e}")

    # Minimal request with strict timeout
    llm = ChatOpenAI(
        model=os.getenv("HACS_LLM_MODEL", "gpt-5-mini-2025-08-07"),
        timeout=10,
        max_retries=1,
    )
    # Dry prompt that should return quickly
    resp = llm.invoke([{"role": "user", "content": "Say 'ok'"}])
    text = getattr(resp, "content", "")
    assert isinstance(text, str)
    assert len(text) > 0
