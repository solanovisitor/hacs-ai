"""
Compliance Monitor Following SOLID Principles

This module provides compliance monitoring capabilities for the HACS Registry.

SOLID Compliance:
- S: Single Responsibility - Handles compliance monitoring only
- O: Open/Closed - Extensible for new compliance rules
- L: Liskov Substitution - Implements monitoring contract
- I: Interface Segregation - Focused compliance interface
- D: Dependency Inversion - Depends on abstractions
"""

import logging
from typing import Any, Dict, List, Optional

from ...core.exceptions import InfrastructureException

logger = logging.getLogger(__name__)


class ComplianceMonitor:
    """
    Compliance monitoring service for regulatory adherence.
    
    SOLID Compliance:
    - S: Single responsibility - compliance monitoring only
    - O: Open/closed - extensible for new compliance rules
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self._compliance_rules = {}
        self._violations = []
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the compliance monitor."""
        if not self._initialized:
            self._initialized = True
            self.logger.info("Compliance monitor initialized")
    
    async def check_compliance(
        self,
        resource_type: str,
        resource_data: Dict[str, Any]
    ) -> List[str]:
        """Check compliance for a resource."""
        try:
            violations = []
            
            # Placeholder compliance checks
            if resource_type == "clinical":
                if "patient_consent" not in resource_data:
                    violations.append("Missing patient consent documentation")
                
                if "data_retention_policy" not in resource_data:
                    violations.append("Missing data retention policy")
            
            if violations:
                self._violations.extend(violations)
                self.logger.warning(f"Compliance violations found: {violations}")
            
            return violations
            
        except Exception as e:
            self.logger.error(f"Failed to check compliance: {e}")
            raise InfrastructureException(f"Compliance check failed: {e}")
    
    async def add_compliance_rule(
        self,
        rule_name: str,
        rule_config: Dict[str, Any]
    ) -> None:
        """Add a new compliance rule."""
        try:
            self._compliance_rules[rule_name] = rule_config
            self.logger.info(f"Added compliance rule: {rule_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to add compliance rule: {e}")
    
    def get_violations(self) -> List[str]:
        """Get all recorded violations."""
        return self._violations.copy()
    
    async def cleanup(self) -> None:
        """Clean up compliance monitor."""
        self._compliance_rules.clear()
        self._violations.clear()
        self._initialized = False
        self.logger.info("Compliance monitor cleaned up")