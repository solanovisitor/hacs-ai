"""
Audit Logger Following SOLID Principles

This module provides audit logging capabilities for the HACS Registry.

SOLID Compliance:
- S: Single Responsibility - Handles audit logging only
- O: Open/Closed - Extensible for new audit types
- L: Liskov Substitution - Implements logging contract
- I: Interface Segregation - Focused audit interface
- D: Dependency Inversion - Depends on abstractions
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ...core.exceptions import InfrastructureException

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Audit logging service for tracking registry operations.
    
    SOLID Compliance:
    - S: Single responsibility - audit logging only
    - O: Open/closed - extensible for new audit events
    """
    
    def __init__(self, log_level: str = "INFO"):
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the audit logger."""
        if not self._initialized:
            self._initialized = True
            self.logger.info("Audit logger initialized")
    
    async def log_event(
        self,
        event_type: str,
        actor_id: Optional[str],
        resource_id: Optional[str],
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log an audit event."""
        try:
            audit_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": event_type,
                "actor_id": actor_id,
                "resource_id": resource_id,
                "details": details or {}
            }
            
            self.logger.info(f"AUDIT: {audit_entry}")
            
        except Exception as e:
            self.logger.error(f"Failed to log audit event: {e}")
            raise InfrastructureException(f"Audit logging failed: {e}")
    
    async def cleanup(self) -> None:
        """Clean up audit logger."""
        self._initialized = False
        self.logger.info("Audit logger cleaned up")