import pytest

from hacs_models import Procedure
from hacs_utils.extraction.validation import apply_injection_and_validation
from hacs_tools.common import runnable_context, HACSCommonInput
from hacs_models import MessageDefinition


def test_procedure_normalize_and_validate_dict_first():
    raw = {
        "resource_type": "Procedure",
        "code": "endoscopia digestiva alta",
        "status": "completed",
        "id": "llm-supplied-should-be-dropped",
        "created_at": "2024-01-01T00:00:00Z",
    }
    validated = apply_injection_and_validation(raw, Procedure, injected_fields=None, injection_mode="guide")
    assert isinstance(validated, Procedure)
    # Coercion: string code -> CodeableConcept with text
    assert hasattr(validated.code, "text") and validated.code.text == "endoscopia digestiva alta"
    # System fields should be regenerated/managed by model
    assert validated.id is not None and validated.id != "llm-supplied-should-be-dropped"
    assert validated.resource_type == "Procedure"


def test_runnable_context_uses_state_messages():
    # Minimal stand-in objects for config/state
    class DummyState:
        def __init__(self, messages):
            self.messages = messages

    msgs = [{"role": "user", "content": "Hi"}]
    ctx = runnable_context(config=None, state=DummyState(msgs))
    assert isinstance(ctx.messages, list) and isinstance(ctx.messages[0], MessageDefinition)
    assert ctx.messages[0].text() == "Hi"


def test_runnable_context_override_model_and_params():
    class DummyConfig:
        class Models:
            default_model = "gpt-4.1"
            provider = "openai"
            default_params = {"temperature": 0.3}
        models = Models()

    ctx = runnable_context(config=DummyConfig(), state=None, model_override="claude-3.5", params={"max_tokens": 256})
    assert ctx.model == "claude-3.5"
    assert ctx.provider in ("openai", None)
    assert ctx.params.get("temperature") == 0.3
    assert ctx.params.get("max_tokens") == 256
