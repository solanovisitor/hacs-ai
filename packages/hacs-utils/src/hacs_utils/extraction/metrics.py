"""
Performance tracking and metrics for extraction operations.

This module handles:
- Timing extraction stages
- Counting resources and citations
- Tracking quality metrics (timeouts, failures)
- Resource utilization metrics
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Any, List
from contextlib import contextmanager


@dataclass
class ExtractionStageMetrics:
    """Metrics for a single extraction stage."""
    
    stage_name: str
    duration_sec: float = 0.0
    items_processed: int = 0
    items_extracted: int = 0
    timeout_failures: int = 0
    validation_failures: int = 0
    
    def add_processed(self, count: int = 1) -> None:
        """Add to processed items count."""
        self.items_processed += count
    
    def add_extracted(self, count: int = 1) -> None:
        """Add to extracted items count."""
        self.items_extracted += count
    
    def add_timeout(self, count: int = 1) -> None:
        """Add to timeout failures count."""
        self.timeout_failures += count
    
    def add_validation_failure(self, count: int = 1) -> None:
        """Add to validation failures count."""
        self.validation_failures += count


@dataclass
class ExtractionSessionMetrics:
    """Complete metrics for an extraction session."""
    
    # Overall timing
    total_duration_sec: float = 0.0
    
    # Stage-specific metrics
    stages: Dict[str, ExtractionStageMetrics] = field(default_factory=dict)
    
    # Resource counts
    total_citations_found: int = 0
    total_records_extracted: int = 0
    records_by_type: Dict[str, int] = field(default_factory=dict)
    
    # Quality metrics
    zero_yield_fallbacks_used: int = 0
    total_timeout_failures: int = 0
    total_validation_failures: int = 0
    
    # Concurrency metrics
    concurrent_windows_processed: int = 0
    max_concurrent_windows: int = 0
    
    def get_stage(self, stage_name: str) -> ExtractionStageMetrics:
        """Get or create metrics for a stage."""
        if stage_name not in self.stages:
            self.stages[stage_name] = ExtractionStageMetrics(stage_name=stage_name)
        return self.stages[stage_name]
    
    def add_type_count(self, resource_type: str, count: int) -> None:
        """Add count for a specific resource type."""
        self.records_by_type[resource_type] = self.records_by_type.get(resource_type, 0) + count
        self.total_records_extracted += count
    
    def finalize(self) -> None:
        """Finalize metrics by aggregating stage data."""
        # Aggregate timeout and validation failures from stages
        self.total_timeout_failures = sum(stage.timeout_failures for stage in self.stages.values())
        self.total_validation_failures = sum(stage.validation_failures for stage in self.stages.values())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            "total_duration_sec": self.total_duration_sec,
            "stages": {
                name: {
                    "duration_sec": stage.duration_sec,
                    "items_processed": stage.items_processed,
                    "items_extracted": stage.items_extracted,
                    "timeout_failures": stage.timeout_failures,
                    "validation_failures": stage.validation_failures,
                }
                for name, stage in self.stages.items()
            },
            "total_citations_found": self.total_citations_found,
            "total_records_extracted": self.total_records_extracted,
            "records_by_type": self.records_by_type,
            "zero_yield_fallbacks_used": self.zero_yield_fallbacks_used,
            "total_timeout_failures": self.total_timeout_failures,
            "total_validation_failures": self.total_validation_failures,
            "concurrent_windows_processed": self.concurrent_windows_processed,
            "max_concurrent_windows": self.max_concurrent_windows,
        }


class MetricsTracker:
    """Context manager for tracking extraction metrics."""
    
    def __init__(self, metrics: ExtractionSessionMetrics | None = None):
        self.metrics = metrics or ExtractionSessionMetrics()
        self._start_time: float | None = None
    
    def __enter__(self) -> 'MetricsTracker':
        self._start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._start_time is not None:
            self.metrics.total_duration_sec = time.time() - self._start_time
        self.metrics.finalize()
    
    @contextmanager
    def stage(self, stage_name: str):
        """Context manager for tracking a specific stage."""
        stage_metrics = self.metrics.get_stage(stage_name)
        start_time = time.time()
        try:
            yield stage_metrics
        finally:
            stage_metrics.duration_sec = time.time() - start_time
    
    def add_citations(self, count: int) -> None:
        """Add to total citations found."""
        self.metrics.total_citations_found += count
    
    def add_records(self, resource_type: str, count: int) -> None:
        """Add records for a specific type."""
        self.metrics.add_type_count(resource_type, count)
    
    def add_fallback(self) -> None:
        """Record a zero-yield fallback usage."""
        self.metrics.zero_yield_fallbacks_used += 1
    
    def set_concurrency_stats(self, processed: int, max_concurrent: int) -> None:
        """Set concurrency statistics."""
        self.metrics.concurrent_windows_processed = processed
        self.metrics.max_concurrent_windows = max_concurrent


def calculate_extraction_rate(metrics: ExtractionSessionMetrics) -> Dict[str, float]:
    """Calculate extraction rates from metrics.
    
    Returns:
        Dictionary with rate calculations
    """
    rates = {}
    
    if metrics.total_duration_sec > 0:
        rates["records_per_second"] = metrics.total_records_extracted / metrics.total_duration_sec
        rates["citations_per_second"] = metrics.total_citations_found / metrics.total_duration_sec
    
    if metrics.total_citations_found > 0:
        rates["extraction_efficiency"] = metrics.total_records_extracted / metrics.total_citations_found
    
    total_failures = metrics.total_timeout_failures + metrics.total_validation_failures
    total_attempts = metrics.total_records_extracted + total_failures
    if total_attempts > 0:
        rates["success_rate"] = metrics.total_records_extracted / total_attempts
        rates["failure_rate"] = total_failures / total_attempts
    
    return rates


def format_metrics_summary(metrics: ExtractionSessionMetrics) -> str:
    """Format metrics into a human-readable summary.
    
    Returns:
        Formatted string summary
    """
    rates = calculate_extraction_rate(metrics)
    
    lines = [
        f"=== Extraction Metrics Summary ===",
        f"Total Duration: {metrics.total_duration_sec:.2f}s",
        f"Citations Found: {metrics.total_citations_found}",
        f"Records Extracted: {metrics.total_records_extracted}",
        f"",
        f"Records by Type:",
    ]
    
    for resource_type, count in sorted(metrics.records_by_type.items()):
        lines.append(f"  {resource_type}: {count}")
    
    lines.extend([
        f"",
        f"Quality Metrics:",
        f"  Timeout Failures: {metrics.total_timeout_failures}",
        f"  Validation Failures: {metrics.total_validation_failures}",
        f"  Zero-Yield Fallbacks: {metrics.zero_yield_fallbacks_used}",
        f"",
        f"Performance:",
    ])
    
    if "records_per_second" in rates:
        lines.append(f"  Records/sec: {rates['records_per_second']:.2f}")
    if "extraction_efficiency" in rates:
        lines.append(f"  Extraction Efficiency: {rates['extraction_efficiency']:.2f}")
    if "success_rate" in rates:
        lines.append(f"  Success Rate: {rates['success_rate']:.1%}")
    
    if metrics.stages:
        lines.extend([f"", f"Stage Breakdown:"])
        for stage_name, stage in metrics.stages.items():
            lines.append(f"  {stage_name}: {stage.duration_sec:.2f}s ({stage.items_extracted} extracted)")
    
    return "\n".join(lines)
