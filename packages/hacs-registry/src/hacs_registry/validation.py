"""
HACS Validation Framework

Comprehensive validation framework for type safety, configuration validation,
and healthcare-specific compliance checking. All validation rules are
configurable and versionable through the registry.

Features:
    ✅ Type safety validation
    🏥 Healthcare compliance checking
    📋 Configuration validation
    🔧 Custom validation rules
    📊 Validation reporting
    🎯 Domain-specific validators
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field

from pydantic import ValidationError
from hacs_core import (
    BaseResource,
    # Import validation types from hacs-core
    ValidationSeverity,
    ValidationCategory,
    # Import domain types from hacs-core
    HealthcareDomain,
    AgentRole,
)

from .agent_registry import (
    AgentConfiguration
)

logger = logging.getLogger(__name__)


# Simplified validation rule class for the new architecture
@dataclass
class ValidationRule:
    """Simplified validation rule."""
    name: str
    description: str
    severity: str = "error"
    active: bool = True

@dataclass
class ValidationResult:
    """Result of a validation check."""
    
    # Basic result info
    is_valid: bool
    severity: ValidationSeverity
    category: ValidationCategory
    rule_name: str
    
    # Detailed information
    message: str
    details: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    
    # Context
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    field_path: Optional[str] = None
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    validator_name: str = ""

@dataclass
class ValidationReport:
    """Comprehensive validation report."""
    
    # Summary
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    
    # Results by severity
    info_count: int = 0
    warning_count: int = 0
    error_count: int = 0
    critical_count: int = 0
    
    # Detailed results
    results: List[ValidationResult] = field(default_factory=list)
    
    # Overall status
    is_valid: bool = True
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    validation_duration: float = 0.0

class BaseValidator(ABC):
    """Abstract base class for all validators."""
    
    def __init__(self, name: str, category: ValidationCategory = ValidationCategory.TYPE_SAFETY):
        self.name = name
        self.category = category
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def validate(self, target: Any, context: Dict[str, Any] = None) -> List[ValidationResult]:
        """Perform validation and return results."""
        pass
    
    def create_result(self, is_valid: bool, severity: ValidationSeverity, 
                     message: str, **kwargs) -> ValidationResult:
        """Helper to create validation results."""
        return ValidationResult(
            is_valid=is_valid,
            severity=severity,
            category=self.category,
            rule_name=self.name,
            message=message,
            validator_name=self.__class__.__name__,
            **kwargs
        )

class TypeSafetyValidator(BaseValidator):
    """Validator for type safety and Pydantic model validation."""
    
    def __init__(self):
        super().__init__("type_safety", ValidationCategory.TYPE_SAFETY)
    
    def validate(self, target: Any, context: Dict[str, Any] = None) -> List[ValidationResult]:
        """Validate type safety."""
        results = []
        
        try:
            # Check if target is a BaseResource
            if isinstance(target, BaseResource):
                # Validate the Pydantic model
                try:
                    # Trigger validation by creating a copy
                    target.model_validate(target.model_dump())
                    results.append(self.create_result(
                        True, ValidationSeverity.INFO,
                        f"Resource {target.resource_type} passed type validation",
                        resource_type=target.resource_type,
                        resource_id=getattr(target, 'id', None)
                    ))
                except ValidationError as e:
                    for error in e.errors():
                        results.append(self.create_result(
                            False, ValidationSeverity.ERROR,
                            f"Type validation failed: {error['msg']}",
                            details={'error': error},
                            field_path='.'.join(str(loc) for loc in error['loc']),
                            resource_type=target.resource_type,
                            resource_id=getattr(target, 'id', None)
                        ))
            else:
                # Generic type checking
                results.append(self.create_result(
                    True, ValidationSeverity.INFO,
                    f"Object of type {type(target).__name__} processed"
                ))
                
        except Exception as e:
            results.append(self.create_result(
                False, ValidationSeverity.CRITICAL,
                f"Type safety validation failed with exception: {str(e)}",
                details={'exception': str(e)}
            ))
        
        return results

class ConfigurationValidator(BaseValidator):
    """Validator for integration configurations."""
    
    def __init__(self):
        super().__init__("configuration_validation", ValidationCategory.CONFIGURATION)
    
    def validate(self, target: Any, context: Dict[str, Any] = None) -> List[ValidationResult]:
        """Validate configuration completeness and consistency."""
        results = []
        
        if isinstance(target, AgentConfiguration):
            results.extend(self._validate_agent_config(target))
        # Note: In the new architecture, only AgentConfiguration is validated here
        # Other configurations are managed through the resource registry
        else:
            results.append(self.create_result(
                True, ValidationSeverity.INFO,
                f"No specific validation rules for {type(target).__name__}"
            ))
        
        return results
    
    def _validate_agent_config(self, config: AgentConfiguration) -> List[ValidationResult]:
        """Validate agent configuration."""
        results = []
        
        # Check required fields
        if not config.agent_name:
            results.append(self.create_result(
                False, ValidationSeverity.ERROR,
                "Agent name is required",
                resource_type="AgentConfiguration",
                field_path="agent_name"
            ))
        
        if not config.agent_version:
            results.append(self.create_result(
                False, ValidationSeverity.ERROR,
                "Agent version is required",
                resource_type="AgentConfiguration",
                field_path="agent_version"
            ))
        
        # Validate domain and role compatibility
        if config.domain == HealthcareDomain.EMERGENCY and config.role == AgentRole.CLINICAL_RESEARCHER:
            results.append(self.create_result(
                False, ValidationSeverity.WARNING,
                "Clinical researcher role may not be optimal for emergency domain",
                resource_type="AgentConfiguration",
                suggestions=["Consider using TRIAGE_SPECIALIST or CLINICAL_ASSISTANT role"]
            ))
        
        return results
    
    # Note: In the new architecture, validation focuses on AgentConfiguration
    # Resource-specific validation is handled by the resource registry

class HealthcareComplianceValidator(BaseValidator):
    """Validator for healthcare-specific compliance rules."""
    
    def __init__(self):
        super().__init__("healthcare_compliance", ValidationCategory.HEALTHCARE_COMPLIANCE)
    
    def validate(self, target: Any, context: Dict[str, Any] = None) -> List[ValidationResult]:
        """Validate healthcare compliance."""
        results = []
        
        # HIPAA compliance checks
        results.extend(self._check_hipaa_compliance(target, context))
        
        # Clinical safety checks
        results.extend(self._check_clinical_safety(target, context))
        
        # Data quality checks
        results.extend(self._check_data_quality(target, context))
        
        return results
    
    def _check_hipaa_compliance(self, target: Any, context: Dict[str, Any] = None) -> List[ValidationResult]:
        """Check HIPAA compliance requirements."""
        results = []
        
        if isinstance(target, AgentConfiguration):
            # Check for audit logging
            if not target.enable_monitoring:
                results.append(self.create_result(
                    False, ValidationSeverity.ERROR,
                    "HIPAA compliance requires audit logging - enable monitoring",
                    resource_type="AgentConfiguration",
                    field_path="enable_monitoring",
                    suggestions=["Enable monitoring for HIPAA compliance"]
                ))
        
        return results
    
    def _check_clinical_safety(self, target: Any, context: Dict[str, Any] = None) -> List[ValidationResult]:
        """Check clinical safety requirements."""
        results = []
        
        if isinstance(target, PromptConfiguration):
            # Check for disclaimer
            if "disclaimer" not in target.safety_instructions.lower():
                results.append(self.create_result(
                    False, ValidationSeverity.WARNING,
                    "Clinical safety: Consider adding medical disclaimer to prompts",
                    resource_type="PromptConfiguration",
                    suggestions=["Add medical disclaimer to safety instructions"]
                ))
        
        return results
    
    def _check_data_quality(self, target: Any, context: Dict[str, Any] = None) -> List[ValidationResult]:
        """Check data quality requirements."""
        results = []
        
        # Generic data quality checks
        if hasattr(target, 'model_dump'):
            data = target.model_dump()
            
            # Check for empty critical fields
            critical_fields = ['id', 'resource_type', 'created_at']
            for field in critical_fields:
                if field in data and not data[field]:
                    results.append(self.create_result(
                        False, ValidationSeverity.WARNING,
                        f"Critical field '{field}' is empty",
                        field_path=field,
                        suggestions=[f"Ensure {field} is properly populated"]
                    ))
        
        return results

class CustomRuleValidator(BaseValidator):
    """Validator that executes custom validation rules from the registry."""
    
    def __init__(self):
        super().__init__("custom_rules", ValidationCategory.BUSINESS_RULES)
        self.custom_functions: Dict[str, Callable] = {}
    
    def register_validation_function(self, name: str, func: Callable):
        """Register a custom validation function."""
        self.custom_functions[name] = func
    
    def validate(self, target: Any, context: Dict[str, Any] = None) -> List[ValidationResult]:
        """Execute custom validation rules."""
        results = []
        
        # Get custom rules from context
        custom_rules = context.get('custom_rules', []) if context else []
        
        for rule in custom_rules:
            if isinstance(rule, ValidationRule):
                results.extend(self._execute_custom_rule(rule, target, context))
        
        return results
    
    def _execute_custom_rule(self, rule: ValidationRule, target: Any, 
                           context: Dict[str, Any] = None) -> List[ValidationResult]:
        """Execute a specific custom validation rule."""
        results = []
        
        try:
            # Check if rule applies to target
            target_type = getattr(target, 'resource_type', type(target).__name__)
            if target_type not in rule.target_resource_types:
                return results
            
            # Get validation function
            func = self.custom_functions.get(rule.validation_function)
            if not func:
                results.append(self.create_result(
                    False, ValidationSeverity.ERROR,
                    f"Custom validation function '{rule.validation_function}' not found",
                    details={'rule_name': rule.rule_name}
                ))
                return results
            
            # Execute validation function
            is_valid = func(target, rule.validation_parameters, context)
            
            severity = ValidationSeverity.ERROR if rule.severity == "error" else ValidationSeverity.WARNING
            
            if is_valid:
                results.append(self.create_result(
                    True, ValidationSeverity.INFO,
                    f"Custom rule '{rule.rule_name}' passed"
                ))
            else:
                results.append(self.create_result(
                    False, severity,
                    rule.error_message_template,
                    details={'rule_name': rule.rule_name}
                ))
                
        except Exception as e:
            results.append(self.create_result(
                False, ValidationSeverity.CRITICAL,
                f"Custom rule '{rule.rule_name}' failed with exception: {str(e)}",
                details={'exception': str(e), 'rule_name': rule.rule_name}
            ))
        
        return results

class ValidationEngine:
    """Main validation engine that orchestrates all validators."""
    
    def __init__(self):
        self.validators: List[BaseValidator] = [
            TypeSafetyValidator(),
            ConfigurationValidator(),
            HealthcareComplianceValidator(),
            CustomRuleValidator(),
        ]
        self.logger = logging.getLogger(f"{__name__}.ValidationEngine")
    
    def add_validator(self, validator: BaseValidator):
        """Add a custom validator to the engine."""
        self.validators.append(validator)
    
    def validate(self, target: Any, context: Dict[str, Any] = None, 
                categories: List[ValidationCategory] = None) -> ValidationReport:
        """Perform comprehensive validation."""
        start_time = datetime.now()
        
        report = ValidationReport()
        
        # Filter validators by category if specified
        active_validators = self.validators
        if categories:
            active_validators = [v for v in self.validators if v.category in categories]
        
        # Run all validators
        for validator in active_validators:
            try:
                results = validator.validate(target, context)
                report.results.extend(results)
                
                for result in results:
                    report.total_checks += 1
                    
                    if result.is_valid:
                        report.passed_checks += 1
                    else:
                        report.failed_checks += 1
                        report.is_valid = False
                    
                    # Count by severity
                    if result.severity == ValidationSeverity.INFO:
                        report.info_count += 1
                    elif result.severity == ValidationSeverity.WARNING:
                        report.warning_count += 1
                    elif result.severity == ValidationSeverity.ERROR:
                        report.error_count += 1
                    elif result.severity == ValidationSeverity.CRITICAL:
                        report.critical_count += 1
                        
            except Exception as e:
                self.logger.error(f"Validator {validator.name} failed: {e}")
                report.results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.CRITICAL,
                    category=validator.category,
                    rule_name=validator.name,
                    message=f"Validator failed with exception: {str(e)}",
                    validator_name=validator.__class__.__name__
                ))
                report.failed_checks += 1
                report.critical_count += 1
                report.is_valid = False
        
        # Calculate duration
        end_time = datetime.now()
        report.validation_duration = (end_time - start_time).total_seconds()
        
        return report
    
    def validate_configuration_set(self, configurations: Dict[str, Any]) -> ValidationReport:
        """Validate a complete set of configurations."""
        combined_report = ValidationReport()
        
        for config_name, config in configurations.items():
            individual_report = self.validate(config)
            
            # Merge reports
            combined_report.total_checks += individual_report.total_checks
            combined_report.passed_checks += individual_report.passed_checks
            combined_report.failed_checks += individual_report.failed_checks
            combined_report.info_count += individual_report.info_count
            combined_report.warning_count += individual_report.warning_count
            combined_report.error_count += individual_report.error_count
            combined_report.critical_count += individual_report.critical_count
            
            # Add context to results
            for result in individual_report.results:
                result.details = result.details or {}
                result.details['configuration_name'] = config_name
                combined_report.results.append(result)
            
            if not individual_report.is_valid:
                combined_report.is_valid = False
        
        return combined_report

# Convenience functions
def validate_agent_config(config: AgentConfiguration) -> ValidationReport:
    """Validate an agent configuration."""
    engine = ValidationEngine()
    return engine.validate(config)

def validate_all_configs(**configs) -> ValidationReport:
    """Validate multiple configurations together."""
    engine = ValidationEngine()
    return engine.validate_configuration_set(configs)

def create_custom_validator(name: str, category: ValidationCategory, 
                          validation_func: Callable) -> BaseValidator:
    """Create a custom validator from a function."""
    
    class CustomValidator(BaseValidator):
        def __init__(self):
            super().__init__(name, category)
            self.validation_func = validation_func
        
        def validate(self, target: Any, context: Dict[str, Any] = None) -> List[ValidationResult]:
            try:
                is_valid, message = self.validation_func(target, context)
                severity = ValidationSeverity.INFO if is_valid else ValidationSeverity.ERROR
                return [self.create_result(is_valid, severity, message)]
            except Exception as e:
                return [self.create_result(
                    False, ValidationSeverity.CRITICAL,
                    f"Custom validator failed: {str(e)}"
                )]
    
    return CustomValidator()

__all__ = [
    # Core validation classes
    'ValidationSeverity',
    'ValidationCategory',
    'ValidationResult',
    'ValidationReport',
    'ValidationEngine',
    
    # Validators
    'BaseValidator',
    'TypeSafetyValidator',
    'ConfigurationValidator',
    'HealthcareComplianceValidator',
    'CustomRuleValidator',
    
    # Convenience functions
    'validate_agent_config',
    'validate_all_configs',
    'create_custom_validator',
]