"""
Metrics Collector Following SOLID Principles

This module provides metrics collection capabilities for the HACS Registry.

SOLID Compliance:
- S: Single Responsibility - Handles metrics collection only
- O: Open/Closed - Extensible for new metric types
- L: Liskov Substitution - Implements metrics contract
- I: Interface Segregation - Focused metrics interface
- D: Dependency Inversion - Depends on abstractions
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from collections import defaultdict

from ...core.exceptions import InfrastructureException

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Metrics collection service for registry performance tracking.
    
    SOLID Compliance:
    - S: Single responsibility - metrics collection only
    - O: Open/closed - extensible for new metrics
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self._metrics = defaultdict(list)
        self._counters = defaultdict(int)
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the metrics collector."""
        if not self._initialized:
            self._initialized = True
            self.logger.info("Metrics collector initialized")
    
    async def record_metric(
        self,
        metric_name: str,
        value: Any,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a metric value."""
        try:
            metric_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "name": metric_name,
                "value": value,
                "tags": tags or {}
            }
            
            self._metrics[metric_name].append(metric_entry)
            self.logger.debug(f"METRIC: {metric_name} = {value}")
            
        except Exception as e:
            self.logger.error(f"Failed to record metric: {e}")
            raise InfrastructureException(f"Metrics recording failed: {e}")
    
    async def increment_counter(self, counter_name: str, amount: int = 1) -> None:
        """Increment a counter metric."""
        try:
            self._counters[counter_name] += amount
            await self.record_metric(f"counter.{counter_name}", self._counters[counter_name])
            
        except Exception as e:
            self.logger.error(f"Failed to increment counter: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        return {
            "metrics": dict(self._metrics),
            "counters": dict(self._counters)
        }
    
    async def cleanup(self) -> None:
        """Clean up metrics collector."""
        self._metrics.clear()
        self._counters.clear()
        self._initialized = False
        self.logger.info("Metrics collector cleaned up")