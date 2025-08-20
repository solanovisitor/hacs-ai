import os
import pytest

pytestmark = pytest.mark.llm


def test_anthropic_connectivity_optional():
    """Optional Anthropic connectivity test for provider diversity.
    
    Skips if ANTHROPIC_API_KEY not set. Provides alternative to OpenAI/LangChain.
    Nightly only; not required for PR CI.
    """
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set; skipping optional Anthropic test")

    try:
        from hacs_utils.integrations.anthropic import AnthropicClient
    except Exception as e:
        pytest.skip(f"Anthropic integration not available: {e}")

    client = AnthropicClient(model="claude-sonnet-4-20250514", timeout=15, max_retries=1)
    
    # Minimal text generation test
    text = client.invoke("Say 'hello' in one word")
    assert isinstance(text, str)
    assert len(text) > 0


def test_anthropic_structured_output_optional():
    """Test Anthropic structured output using tool-based JSON mode."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set; skipping Anthropic structured output test")

    try:
        from hacs_utils.integrations.anthropic import AnthropicClient
        from hacs_models import Patient
    except Exception as e:
        pytest.skip(f"Dependencies not available: {e}")

    client = AnthropicClient(model="claude-sonnet-4-20250514", timeout=20, max_retries=1)
    
    # Use Patient subset for structured extraction
    PatientInfo = Patient.pick("full_name", "birth_date")
    note = "Alice Smith was born on 1990-05-15."

    instance = client.structured_output(
        prompt=f"Extract patient demographics from: {note}",
        response_model=PatientInfo,
    )

    # Validate structured output
    assert instance is not None
    assert hasattr(instance, "full_name")
    assert isinstance(instance.full_name, str)
    assert len(instance.full_name) > 0
    assert getattr(instance, "birth_date", None) is not None


def test_anthropic_tool_use_optional():
    """Test Anthropic tool use capability with HACS-style tools."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set; skipping Anthropic tool use test")

    try:
        from hacs_utils.integrations.anthropic import AnthropicClient
    except Exception as e:
        pytest.skip(f"Dependencies not available: {e}")

    client = AnthropicClient(model="claude-sonnet-4-20250514", timeout=20, max_retries=1)
    
    # Define a simple healthcare tool
    tools = [{
        "name": "calculate_bmi",
        "description": "Calculate BMI from height and weight",
        "input_schema": {
            "type": "object",
            "properties": {
                "height_cm": {"type": "number", "description": "Height in centimeters"},
                "weight_kg": {"type": "number", "description": "Weight in kilograms"}
            },
            "required": ["height_cm", "weight_kg"]
        }
    }]

    response = client.tool_use(
        messages=[{"role": "user", "content": "Calculate BMI for someone who is 175cm tall and weighs 70kg"}],
        tools=tools,
    )

    # Verify tool use was triggered
    tool_calls = client.extract_tool_calls(response)
    assert len(tool_calls) > 0
    
    call = tool_calls[0]
    assert call["name"] == "calculate_bmi"
    assert "height_cm" in call["input"]
    assert "weight_kg" in call["input"]
    assert isinstance(call["input"]["height_cm"], (int, float))
    assert isinstance(call["input"]["weight_kg"], (int, float))
