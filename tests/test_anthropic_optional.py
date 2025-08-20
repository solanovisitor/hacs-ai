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
        from anthropic import Anthropic
    except Exception as e:
        pytest.skip(f"Anthropic SDK not available: {e}")

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    # Minimal text generation test
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=20,
        messages=[{"role": "user", "content": "Say 'hello' in one word"}]
    )
    
    text = response.content[0].text if response.content else ""
    assert isinstance(text, str)
    assert len(text) > 0


def test_anthropic_json_mode_optional():
    """Optional Anthropic JSON mode test for structured outputs.
    
    Tests if Anthropic can produce structured JSON for simple schemas.
    """
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set; skipping optional Anthropic JSON test")

    try:
        from anthropic import Anthropic
        import json
    except Exception as e:
        pytest.skip(f"Dependencies not available: {e}")

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    prompt = '''Extract name and age from: "Alice Smith is 30 years old"
    
Return only valid JSON in this format:
{"name": "string", "age": number}'''

    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=50,
        messages=[{"role": "user", "content": prompt}]
    )
    
    text = response.content[0].text if response.content else ""
    
    # Try parsing as JSON
    try:
        data = json.loads(text)
        assert "name" in data
        assert "age" in data
        assert isinstance(data["name"], str)
        assert isinstance(data["age"], (int, float))
    except json.JSONDecodeError:
        pytest.fail(f"Anthropic did not return valid JSON: {text}")
