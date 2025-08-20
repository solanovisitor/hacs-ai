import os
import pytest

pytestmark = pytest.mark.llm


def test_structured_extraction_via_langchain_minimal():
    """End-to-end minimal structured extraction using LangChain ChatOpenAI.

    Skips if OPENAI_API_KEY is not present. Keeps a strict timeout to bound CI cost.
    """
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set; skipping LLM structured extraction test")

    try:
        from langchain_openai import ChatOpenAI
        from hacs_utils.structured import extract
        from hacs_models import Patient
    except Exception as e:
        pytest.skip(f"Dependencies not available: {e}")

    # Tiny subset schema
    PatientInfo = Patient.pick("full_name", "birth_date")

    llm = ChatOpenAI(
        model=os.getenv("HACS_LLM_MODEL", "gpt-5-mini-2025-08-07"),
        timeout=20,
        max_retries=1,
    )
    note = "John Smith (1980-05-15), male."

    instance = extract(
        llm_provider=llm,
        prompt=f"Extract a patient name and birth date from the note.\n\n{note}",
        output_model=PatientInfo,
        use_descriptive_schema=True,
        strict=False,
    )

    # Basic validations to avoid flakiness but ensure structure
    assert instance is not None
    assert hasattr(instance, "full_name")
    assert isinstance(instance.full_name, str)
    assert len(instance.full_name) > 0
    # birth_date may be a date object or string depending on model config;
    # ensure it can be stringified
    assert getattr(instance, "birth_date", None) is not None
