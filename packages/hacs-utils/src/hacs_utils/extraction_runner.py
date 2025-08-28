"""
ExtractionRunner: High-level orchestrator for HACS resource extraction.

Provides a single entrypoint that manages:
- Concurrency control and per-call timeouts
- Retry logic with exponential backoff
- Zero-yield fallback mechanisms
- Standard injection, coercion, validation, and deduplication
- Performance metrics and debugging
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import Any, Type, Sequence, Literal, Dict, List
from dataclasses import dataclass, field
from pydantic import BaseModel

from .extraction.api import (
    extract_citations_guided,
    extract_citations_multi,
    extract_citations,
)
from .extraction.dedupe import dedupe_by_semantic_key


@dataclass
class ExtractionMetrics:
    """Performance and quality metrics for extraction runs."""
    
    # Timing
    total_duration_sec: float = 0.0
    stage1_duration_sec: float = 0.0
    stage2_duration_sec: float = 0.0
    
    # Counts
    total_citations_found: int = 0
    total_records_extracted: int = 0
    records_by_type: Dict[str, int] = field(default_factory=dict)
    
    # Quality
    zero_yield_fallbacks_used: int = 0
    timeout_failures: int = 0
    validation_failures: int = 0
    
    # Resource utilization
    concurrent_windows_processed: int = 0
    max_concurrent_windows: int = 0
    
    def add_type_count(self, resource_type: str, count: int) -> None:
        """Add count for a specific resource type."""
        self.records_by_type[resource_type] = self.records_by_type.get(resource_type, 0) + count
        self.total_records_extracted += count


@dataclass
class ExtractionConfig:
    """Configuration for ExtractionRunner."""
    
    # Concurrency and timeouts
    concurrency_limit: int = 3
    window_timeout_sec: int = 30
    total_timeout_sec: int = 300  # 5 minutes max
    
    # Retry and fallback
    max_retries: int = 2
    retry_backoff_sec: float = 1.0
    enable_zero_yield_fallback: bool = True
    
    # Field extraction limits
    max_extractable_fields: int = 4
    max_items_per_type: int = 50
    
    # Citation guidance
    expand_citation_window: int = 200
    citation_chunking_policy: Any = None
    
    # Injection and validation
    injection_mode: Literal["guide", "frozen"] = "guide"
    use_descriptive_schema: bool = True
    
    # Debug and metrics
    debug_dir: str | None = None
    enable_metrics: bool = True


class ExtractionRunner:
    """High-level orchestrator for HACS resource extraction."""
    
    def __init__(self, config: ExtractionConfig | None = None):
        self.config = config or ExtractionConfig()
        self.metrics = ExtractionMetrics() if self.config.enable_metrics else None
    
    async def extract_document(
        self,
        llm_provider: Any,
        *,
        source_text: str,
        resource_models: Sequence[Type[BaseModel]] | None = None,
        injected_fields_by_type: Dict[str, Dict[str, Any]] | None = None,
        debug_prefix: str | None = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Extract a complete document using citation-guided approach.
        
        Returns:
            Mapping: ResourceTypeName -> list[{record, citation, char_interval}]
        """
        start_time = time.time()
        
        try:
            # Apply total timeout
            result = await asyncio.wait_for(
                self._extract_document_impl(
                    llm_provider,
                    source_text=source_text,
                    resource_models=resource_models,
                    injected_fields_by_type=injected_fields_by_type,
                    debug_prefix=debug_prefix,
                ),
                timeout=self.config.total_timeout_sec
            )
            
            if self.metrics:
                self.metrics.total_duration_sec = time.time() - start_time
                # Calculate totals
                for resource_type, items in result.items():
                    self.metrics.add_type_count(resource_type, len(items))
            
            return result
            
        except asyncio.TimeoutError:
            if self.metrics:
                self.metrics.timeout_failures += 1
                self.metrics.total_duration_sec = time.time() - start_time
            raise TimeoutError(f"Extraction exceeded {self.config.total_timeout_sec}s timeout")
    
    async def extract_single_type(
        self,
        llm_provider: Any,
        *,
        source_text: str,
        resource_model: Type[BaseModel],
        injected_fields: Dict[str, Any] | None = None,
        debug_prefix: str | None = None,
    ) -> List[Dict[str, Any]]:
        """Extract a single resource type with standard processing.
        
        Returns:
            List of {record, citation, char_interval}
        """
        start_time = time.time()
        
        try:
            result = await asyncio.wait_for(
                self._extract_single_type_impl(
                    llm_provider,
                    source_text=source_text,
                    resource_model=resource_model,
                    injected_fields=injected_fields,
                    debug_prefix=debug_prefix,
                ),
                timeout=self.config.total_timeout_sec
            )
            
            if self.metrics:
                self.metrics.total_duration_sec = time.time() - start_time
                resource_type = getattr(resource_model, "__name__", "Resource")
                self.metrics.add_type_count(resource_type, len(result))
            
            return result
            
        except asyncio.TimeoutError:
            if self.metrics:
                self.metrics.timeout_failures += 1
                self.metrics.total_duration_sec = time.time() - start_time
            raise TimeoutError(f"Extraction exceeded {self.config.total_timeout_sec}s timeout")
    
    async def extract_multi_type(
        self,
        llm_provider: Any,
        *,
        source_text: str,
        resource_models: Sequence[Type[BaseModel]],
        injected_fields_by_type: Dict[str, Dict[str, Any]] | None = None,
        debug_prefix: str | None = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Extract multiple resource types without citation guidance.
        
        Returns:
            Mapping: ResourceTypeName -> list[{record, citation, char_interval}]
        """
        start_time = time.time()
        
        try:
            result = await asyncio.wait_for(
                self._extract_multi_type_impl(
                    llm_provider,
                    source_text=source_text,
                    resource_models=resource_models,
                    injected_fields_by_type=injected_fields_by_type,
                    debug_prefix=debug_prefix,
                ),
                timeout=self.config.total_timeout_sec
            )
            
            if self.metrics:
                self.metrics.total_duration_sec = time.time() - start_time
                for resource_type, items in result.items():
                    self.metrics.add_type_count(resource_type, len(items))
            
            return result
            
        except asyncio.TimeoutError:
            if self.metrics:
                self.metrics.timeout_failures += 1
                self.metrics.total_duration_sec = time.time() - start_time
            raise TimeoutError(f"Extraction exceeded {self.config.total_timeout_sec}s timeout")
    
    def get_metrics(self) -> ExtractionMetrics | None:
        """Get performance metrics from the last extraction run."""
        return self.metrics
    
    def reset_metrics(self) -> None:
        """Reset metrics for a new extraction run."""
        if self.config.enable_metrics:
            self.metrics = ExtractionMetrics()
    
    # Implementation methods
    
    async def _extract_document_impl(
        self,
        llm_provider: Any,
        *,
        source_text: str,
        resource_models: Sequence[Type[BaseModel]] | None = None,
        injected_fields_by_type: Dict[str, Dict[str, Any]] | None = None,
        debug_prefix: str | None = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Implementation for document extraction with retry logic."""
        
        for attempt in range(self.config.max_retries + 1):
            try:
                ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                prefix = debug_prefix or f"runner_document_{ts}"
                if attempt > 0:
                    prefix += f"_retry_{attempt}"
                
                result = await extract_citations_guided(
                    llm_provider,
                    source_text=source_text,
                    resource_models=resource_models,
                    injected_fields_by_type=injected_fields_by_type,
                    max_items_per_type=self.config.max_items_per_type,
                    citation_chunking_policy=self.config.citation_chunking_policy,
                    expand_citation_window=self.config.expand_citation_window,
                    debug_dir=self.config.debug_dir,
                    debug_prefix=prefix,
                    injection_mode=self.config.injection_mode,
                    window_timeout_sec=self.config.window_timeout_sec,
                    concurrency_limit=self.config.concurrency_limit,
                )
                
                # Apply post-processing and validation
                return self._post_process_results(result)
                
            except Exception:
                if attempt == self.config.max_retries:
                    raise
                
                # Exponential backoff
                await asyncio.sleep(self.config.retry_backoff_sec * (2 ** attempt))
                continue
        
        return {}  # Should not reach here
    
    async def _extract_single_type_impl(
        self,
        llm_provider: Any,
        *,
        source_text: str,
        resource_model: Type[BaseModel],
        injected_fields: Dict[str, Any] | None = None,
        debug_prefix: str | None = None,
    ) -> List[Dict[str, Any]]:
        """Implementation for single type extraction with retry logic."""
        
        for attempt in range(self.config.max_retries + 1):
            try:
                ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                resource_name = getattr(resource_model, "__name__", "Resource")
                prefix = debug_prefix or f"runner_single_{resource_name}_{ts}"
                if attempt > 0:
                    prefix += f"_retry_{attempt}"
                
                result = await extract_citations(
                    llm_provider,
                    source_text=source_text,
                    resource_model=resource_model,
                    injected_fields=injected_fields,
                    max_items=self.config.max_items_per_type,
                    use_descriptive_schema=self.config.use_descriptive_schema,
                    debug_dir=self.config.debug_dir,
                    debug_prefix=prefix,
                    injection_mode=self.config.injection_mode,
                )
                
                # Apply validation and deduplication
                return self._validate_and_dedupe_single(result, resource_model)
                
            except Exception:
                if attempt == self.config.max_retries:
                    raise
                
                await asyncio.sleep(self.config.retry_backoff_sec * (2 ** attempt))
                continue
        
        return []  # Should not reach here
    
    async def _extract_multi_type_impl(
        self,
        llm_provider: Any,
        *,
        source_text: str,
        resource_models: Sequence[Type[BaseModel]],
        injected_fields_by_type: Dict[str, Dict[str, Any]] | None = None,
        debug_prefix: str | None = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Implementation for multi-type extraction with retry logic."""
        
        for attempt in range(self.config.max_retries + 1):
            try:
                ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                prefix = debug_prefix or f"runner_multi_{ts}"
                if attempt > 0:
                    prefix += f"_retry_{attempt}"
                
                result = await extract_citations_multi(
                    llm_provider,
                    source_text=source_text,
                    resource_models=resource_models,
                    injected_fields_by_type=injected_fields_by_type,
                    max_items_per_type=self.config.max_items_per_type,
                    use_descriptive_schema=self.config.use_descriptive_schema,
                    debug_dir=self.config.debug_dir,
                    debug_prefix=prefix,
                )
                
                # Apply post-processing and validation
                return self._post_process_results(result)
                
            except Exception:
                if attempt == self.config.max_retries:
                    raise
                
                await asyncio.sleep(self.config.retry_backoff_sec * (2 ** attempt))
                continue
        
        return {}  # Should not reach here
    
    def _post_process_results(
        self, 
        results: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Apply validation, deduplication, and quality checks to results."""
        
        processed: Dict[str, List[Dict[str, Any]]] = {}
        
        for resource_type, items in results.items():
            # Validate records
            validated_items: List[Dict[str, Any]] = []
            for item in items:
                try:
                    record = item.get("record")
                    if record and hasattr(record, "model_validate"):
                        # Re-validate the record to ensure it's still valid
                        record.model_validate(record.model_dump())
                    validated_items.append(item)
                except Exception:
                    if self.metrics:
                        self.metrics.validation_failures += 1
                    continue
            
            # Apply semantic deduplication using dedicated module
            deduped_items = dedupe_by_semantic_key(resource_type, validated_items)
            processed[resource_type] = deduped_items
        
        return processed
    
    def _validate_and_dedupe_single(
        self, 
        items: List[Dict[str, Any]], 
        resource_model: Type[BaseModel]
    ) -> List[Dict[str, Any]]:
        """Validate and dedupe items for a single resource type."""
        
        resource_type = getattr(resource_model, "__name__", "Resource")
        
        # Validate records
        validated_items: List[Dict[str, Any]] = []
        for item in items:
            try:
                record = item.get("record")
                if record and hasattr(record, "model_validate"):
                    record.model_validate(record.model_dump())
                validated_items.append(item)
            except Exception:
                if self.metrics:
                    self.metrics.validation_failures += 1
                continue
        
        # Apply deduplication using dedicated module
        return dedupe_by_semantic_key(resource_type, validated_items)
    
# Removed: _dedupe_by_semantic_key() - now using extraction.dedupe.dedupe_by_semantic_key()
