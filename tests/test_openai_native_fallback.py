import os
import pytest

pytestmark = pytest.mark.llm


def test_openai_native_structured_fallback():
    """Test native OpenAI structured output as fallback to LangChain.
    
    Uses our hacs_utils.integrations.openai.client.OpenAIClient with responses_parse.
    Nightly only to de-risk LangChain changes without blocking PR CI.
    """
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set; skipping native OpenAI fallback test")

    try:
        from hacs_utils.integrations.openai.client import OpenAIClient
        from hacs_models import Patient
    except Exception as e:
        pytest.skip(f"Dependencies not available: {e}")

    # Tiny subset schema
    PatientInfo = Patient.pick("full_name", "birth_date")

    client = OpenAIClient(
        model=os.getenv("HACS_LLM_MODEL", "gpt-5-mini-2025-08-07"),
        timeout=20,
        max_retries=1
    )

    note = "Jane Doe (1985-03-20), female."
    prompt = f"Extract patient name and birth date from: {note}"

    # Use native responses_parse (OpenAI structured outputs)
    instance = client.responses_parse(
        prompt=prompt,
        response_model=PatientInfo,
        temperature=0
    )

    # Basic validations
    assert instance is not None
    assert hasattr(instance, "full_name")
    assert isinstance(instance.full_name, str)
    assert len(instance.full_name) > 0
    assert getattr(instance, "birth_date", None) is not None
