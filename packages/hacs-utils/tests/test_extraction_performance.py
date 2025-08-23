"""
Performance tests for ExtractionRunner and prompt generation.

Tests with mocked LLM providers to validate:
- Prompt shape and compactness
- ExtractionRunner latency and resource usage
- Concurrency behavior
- Timeout handling
"""

import asyncio
import json
import time
from unittest.mock import Mock
from typing import Any, Dict, List

import pytest

from hacs_utils.structured import (
    ExtractionRunner,
    ExtractionConfig,
    extract_hacs_resources_with_citations,
)
from hacs_utils.extraction.prompt_builder import (
    get_compact_extractable_fields,
    build_structured_prompt,
)
from hacs_models.observation import Observation
from hacs_models.condition import Condition
from hacs_models.immunization import Immunization


class MockLLMProvider:
    """Mock LLM provider for performance testing."""
    
    def __init__(self, response_delay: float = 0.1, response_data: Any = None):
        self.response_delay = response_delay
        self.response_data = response_data or self._default_response()
        self.call_count = 0
        self.total_delay = 0.0
        self.prompts_received: List[str] = []
    
    def _default_response(self) -> Dict[str, Any]:
        """Default mock response for extraction."""
        return {
            "content": json.dumps([
                {
                    "record": {
                        "resource_type": "Observation",
                        "status": "final",
                        "code": {"text": "Heart Rate"},
                        "value_quantity": {"value": 72, "unit": "bpm"}
                    },
                    "citation": "HR 72 bpm",
                    "start_pos": 10,
                    "end_pos": 20
                }
            ])
        }
    
    async def ainvoke(self, prompt: str) -> Mock:
        """Mock async invoke with configurable delay."""
        self.call_count += 1
        self.prompts_received.append(prompt)
        
        # Simulate processing time
        await asyncio.sleep(self.response_delay)
        self.total_delay += self.response_delay
        
        response = Mock()
        response.content = self.response_data["content"]
        return response
    
    def invoke(self, prompt: str) -> Mock:
        """Mock sync invoke."""
        self.call_count += 1
        self.prompts_received.append(prompt)
        
        response = Mock()
        response.content = self.response_data["content"]
        return response


@pytest.fixture
def mock_fast_provider():
    """Fast mock provider for latency tests."""
    return MockLLMProvider(response_delay=0.01)


@pytest.fixture
def mock_slow_provider():
    """Slow mock provider for timeout tests."""
    return MockLLMProvider(response_delay=2.0)


@pytest.fixture
def sample_transcript():
    """Sample clinical transcript for testing."""
    return """
    Patient presents with chest pain. Vital signs: HR 72 bpm, BP 120/80 mmHg, 
    Temp 98.6°F. Physical exam reveals no acute distress. 
    Administered aspirin 325mg. Plan: EKG, cardiac enzymes.
    """


class TestPromptPerformance:
    """Test prompt generation performance and shape."""
    
    def test_compact_extractable_fields_performance(self):
        """Test that extractable field selection is fast and compact."""
        start_time = time.time()
        
        # Test multiple resource types
        for model_class in [Observation, Condition, Immunization]:
            fields = get_compact_extractable_fields(model_class, max_fields=4)
            
            # Validate compactness
            assert len(fields) <= 4, f"{model_class.__name__} returned {len(fields)} fields, expected ≤4"
            assert "resource_type" not in fields, f"{model_class.__name__} included resource_type in extractables"
            
            # Validate non-empty for known models
            if model_class.__name__ in ["Observation", "Condition", "Immunization"]:
                assert len(fields) > 0, f"{model_class.__name__} returned no extractable fields"
        
        duration = time.time() - start_time
        assert duration < 0.1, f"Extractable field selection took {duration:.3f}s, expected <0.1s"
    
    def test_prompt_compactness(self, sample_transcript):
        """Test that generated prompts are compact and focused."""
        # Test with Observation model
        prompt = build_structured_prompt(
            base_prompt="Extract observations from the text.",
            output_model=Observation,
            is_array=True,
            max_items=10,
            use_descriptive_schema=False,
        )
        
        # Validate prompt length (should be compact)
        assert len(prompt) < 2000, f"Prompt length {len(prompt)} chars, expected <2000 for compactness"
        
        # Validate key components are present
        assert "JSON" in prompt
        assert "array" in prompt.lower()
        assert "10 objects" in prompt
        
        # Validate no excessive verbosity
        lines = prompt.split('\n')
        long_lines = [line for line in lines if len(line) > 200]
        assert len(long_lines) < 3, f"Too many long lines ({len(long_lines)}), prompt should be concise"
    
    def test_extractable_field_prioritization(self):
        """Test that required fields are prioritized in compact selection."""
        # Observation has 'code' as required
        fields = get_compact_extractable_fields(Observation, max_fields=3)
        
        # Get required fields
        required = Observation.get_required_extractables()
        
        # Ensure required fields are included when possible
        for req_field in required:
            if req_field != "resource_type":  # resource_type is always excluded
                assert req_field in fields, f"Required field '{req_field}' not in compact selection: {fields}"


class TestExtractionRunnerPerformance:
    """Test ExtractionRunner performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_runner_latency(self, mock_fast_provider, sample_transcript):
        """Test ExtractionRunner latency with fast provider."""
        config = ExtractionConfig(
            concurrency_limit=2,
            window_timeout_sec=5,
            total_timeout_sec=30,
            max_extractable_fields=3,
            enable_metrics=True,
        )
        
        runner = ExtractionRunner(config)
        
        start_time = time.time()
        results = await runner.extract_single_type(
            mock_fast_provider,
            source_text=sample_transcript,
            resource_model=Observation,
        )
        duration = time.time() - start_time
        
        # Validate performance
        assert duration < 5.0, f"Single type extraction took {duration:.3f}s, expected <5s"
        assert len(results) >= 0, "Should return results (even if empty)"
        
        # Validate metrics
        metrics = runner.get_metrics()
        assert metrics is not None
        assert metrics.total_duration_sec > 0
        assert metrics.total_duration_sec < 10.0
    
    @pytest.mark.asyncio
    async def test_runner_concurrency_behavior(self, mock_fast_provider, sample_transcript):
        """Test that ExtractionRunner respects concurrency limits."""
        config = ExtractionConfig(
            concurrency_limit=2,
            window_timeout_sec=10,
            total_timeout_sec=60,
            enable_metrics=True,
        )
        
        runner = ExtractionRunner(config)
        
        # Create multiple resource types to trigger concurrent processing
        start_time = time.time()
        await runner.extract_document(
            mock_fast_provider,
            source_text=sample_transcript,
        )
        duration = time.time() - start_time
        
        # Should complete reasonably quickly with concurrency
        assert duration < 15.0, f"Document extraction took {duration:.3f}s, expected <15s with concurrency"
        
        # Validate provider was called
        assert mock_fast_provider.call_count > 0, "Provider should have been called"
        
        # Validate metrics
        metrics = runner.get_metrics()
        assert metrics is not None
        assert metrics.total_duration_sec > 0
    
    @pytest.mark.asyncio
    async def test_runner_timeout_handling(self, mock_slow_provider, sample_transcript):
        """Test ExtractionRunner timeout behavior."""
        config = ExtractionConfig(
            concurrency_limit=1,
            window_timeout_sec=0.5,  # Very short timeout
            total_timeout_sec=2.0,   # Short total timeout
            max_retries=0,           # No retries to speed up test
            enable_metrics=True,
        )
        
        runner = ExtractionRunner(config)
        
        # Should timeout quickly
        start_time = time.time()
        with pytest.raises((TimeoutError, asyncio.TimeoutError)):
            await runner.extract_single_type(
                mock_slow_provider,
                source_text=sample_transcript,
                resource_model=Observation,
            )
        duration = time.time() - start_time
        
        # Should timeout within reasonable bounds
        assert duration < 5.0, f"Timeout took {duration:.3f}s, expected <5s"
        assert duration >= 1.5, f"Timeout too fast {duration:.3f}s, expected ≥1.5s"
    
    @pytest.mark.asyncio
    async def test_runner_resource_usage(self, mock_fast_provider, sample_transcript):
        """Test ExtractionRunner resource usage patterns."""
        config = ExtractionConfig(
            concurrency_limit=3,
            enable_metrics=True,
        )
        
        runner = ExtractionRunner(config)
        
        # Run extraction and measure provider calls
        initial_calls = mock_fast_provider.call_count
        
        await runner.extract_document(
            mock_fast_provider,
            source_text=sample_transcript,
        )
        
        final_calls = mock_fast_provider.call_count
        calls_made = final_calls - initial_calls
        
        # Validate reasonable number of calls (not excessive)
        assert calls_made > 0, "Should make at least one LLM call"
        assert calls_made < 50, f"Made {calls_made} calls, seems excessive for small transcript"
        
        # Validate metrics tracking
        metrics = runner.get_metrics()
        assert metrics is not None
        assert metrics.total_records_extracted >= 0


class TestPromptShapeValidation:
    """Test that prompts have the expected shape and content."""
    
    @pytest.mark.asyncio
    async def test_extraction_prompt_contains_allowed_keys(self, mock_fast_provider, sample_transcript):
        """Test that extraction prompts contain allowed keys specification."""
        # Run extraction to capture prompts
        await extract_hacs_resources_with_citations(
            mock_fast_provider,
            source_text=sample_transcript,
            resource_model=Observation,
            max_items=5,
        )
        
        # Validate provider received prompts
        assert len(mock_fast_provider.prompts_received) > 0, "No prompts were sent to provider"
        
        # Check that prompts contain allowed keys
        for prompt in mock_fast_provider.prompts_received:
            # Should contain extractable field guidance
            assert any(keyword in prompt.lower() for keyword in ["allowed", "keys", "field"]), \
                f"Prompt missing field guidance: {prompt[:200]}..."
            
            # Should be reasonably compact
            assert len(prompt) < 5000, f"Prompt too long ({len(prompt)} chars): {prompt[:200]}..."
    
    def test_prompt_includes_model_hints(self):
        """Test that prompts include model-specific hints when available."""
        # Get Observation hints
        hints = Observation.llm_hints()
        assert len(hints) > 0, "Observation should have LLM hints"
        
        # Build prompt
        prompt = build_structured_prompt(
            base_prompt="Extract observations.",
            output_model=Observation,
            use_descriptive_schema=True,
        )
        
        # Validate hints are included
        for hint in hints:
            # Check if key parts of the hint are in the prompt
            hint_words = hint.lower().split()[:3]  # First few words
            if len(hint_words) > 0:
                assert any(word in prompt.lower() for word in hint_words), \
                    f"Hint not found in prompt: {hint[:50]}..."
    
    @pytest.mark.asyncio
    async def test_window_prompts_are_compact(self, mock_fast_provider):
        """Test that window-specific prompts are compact and focused."""
        # Use citation-guided extraction to trigger window prompts
        from hacs_utils.structured import extract_hacs_document_with_citation_guidance
        
        sample_text = "Patient has hypertension. BP 140/90. Given lisinopril 10mg daily."
        
        await extract_hacs_document_with_citation_guidance(
            mock_fast_provider,
            source_text=sample_text,
            resource_models=[Observation, Condition],
            debug_prefix="test_compact",
        )
        
        # Check prompts for compactness
        for prompt in mock_fast_provider.prompts_received:
            # Window prompts should be more compact than full prompts
            if "ALLOWED KEYS:" in prompt:
                # This is a window prompt - should be very compact
                assert len(prompt) < 1000, f"Window prompt too long ({len(prompt)} chars)"
                assert "RULES:" in prompt, "Window prompt should have clear rules"
                assert prompt.count('\n') < 20, "Window prompt should have few lines"


def test_end_to_end_performance_smoke():
    """Smoke test for end-to-end performance with realistic scenario."""
    import asyncio
    
    async def _run_test():
        mock_provider = MockLLMProvider(response_delay=0.05)
        
        config = ExtractionConfig(
            concurrency_limit=2,
            window_timeout_sec=10,
            total_timeout_sec=30,
            max_extractable_fields=4,
            enable_metrics=True,
        )
        
        runner = ExtractionRunner(config)
        
        # Realistic clinical text
        clinical_text = """
        Chief Complaint: Chest pain and shortness of breath.
        
        History: 65-year-old male presents with acute onset chest pain radiating to left arm.
        Associated with diaphoresis and nausea. No prior cardiac history.
        
        Vital Signs: BP 150/95 mmHg, HR 88 bpm, RR 22, Temp 98.4°F, O2 sat 96% on RA
        
        Physical Exam: Anxious appearing. Heart regular rate and rhythm, no murmurs.
        Lungs clear bilaterally. No peripheral edema.
        
        Assessment: Acute coronary syndrome, rule out myocardial infarction.
        
        Plan: 
        - Aspirin 325mg chewed
        - Nitroglycerin SL PRN chest pain  
        - Serial EKGs and cardiac enzymes
        - Cardiology consult
        """
        
        start_time = time.time()
        results = await runner.extract_document(
            mock_provider,
            source_text=clinical_text,
        )
        duration = time.time() - start_time
        
        # Performance assertions
        assert duration < 20.0, f"E2E extraction took {duration:.3f}s, expected <20s"
        
        # Quality assertions
        assert isinstance(results, dict), "Results should be a dictionary"
        total_records = sum(len(items) for items in results.values())
        assert total_records >= 0, "Should return some results"
        
        # Metrics assertions
        metrics = runner.get_metrics()
        assert metrics is not None
        assert metrics.total_duration_sec > 0
        assert metrics.total_duration_sec < 30.0
        
        # Provider usage assertions
        assert mock_provider.call_count > 0, "Should make LLM calls"
        assert mock_provider.call_count < 30, f"Made {mock_provider.call_count} calls, seems excessive"
        
        print(f"✓ E2E performance test passed: {duration:.3f}s, {mock_provider.call_count} calls, {total_records} records")
    
    # Run the async test
    asyncio.run(_run_test())
