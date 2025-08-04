"""
HACS Registry - Resource, prompt, and workflow definitions.

This package provides the domain models for defining and managing versioned
healthcare AI resources including resource schemas, prompt templates, and workflow definitions.
"""

from .definitions import (
    ResourceDefinition,
    ModelDefinition,
    PromptDefinition,
    AgentWorkflowDefinition,
    ToolDefinition,
    DefinitionStatus
)
from .exceptions import RegistryError
from .tool_registry import HACSToolRegistry, get_global_registry, discover_hacs_tools
from .integration import (
    HACSToolIntegrationManager,
    get_integration_manager,
    FrameworkType,
    ExecutionStrategyType,
    ExecutionContext,
    ToolExecutionResult,
    get_langchain_tools,
    get_mcp_tools,
    execute_hacs_tool
)

# Import configuration and validation types (base types come from hacs-core)
from .agent_config import (
    # Configuration resources
    PromptConfiguration,
    ModelConfiguration,
    ResourceConfiguration,
    ToolConfiguration,
    WorkflowConfiguration,
    AgentConfiguration,
    
    # Templates and rules
    ValidationRule,
    ConfigurationTemplate,
)

from .validation import (
    # Validation framework
    ValidationResult,
    ValidationReport,
    ValidationEngine,
    
    # Validators
    BaseValidator,
    TypeSafetyValidator,
    ConfigurationValidator,
    HealthcareComplianceValidator,
    CustomRuleValidator,
    
    # Convenience functions
    validate_agent_config,
    validate_all_configs,
    create_custom_validator,
)

__version__ = "0.1.0"

__all__ = [
    # Resource and workflow definitions
    "ResourceDefinition",
    "ModelDefinition",  # Backwards compatibility
    "PromptDefinition",
    "AgentWorkflowDefinition",
    "ToolDefinition",

    # Tool registry
    "HACSToolRegistry",
    "get_global_registry",
    "discover_hacs_tools",
    
    # Integration framework
    "HACSToolIntegrationManager",
    "get_integration_manager",
    "FrameworkType",
    "ExecutionStrategyType", 
    "ExecutionContext",
    "ToolExecutionResult",
    "get_langchain_tools",
    "get_mcp_tools",
    "execute_hacs_tool",
    
    # Enums and status
    "DefinitionStatus",
    
    # Exceptions
    "RegistryError",
    
    # Configuration resources (base types are in hacs-core)
    "PromptConfiguration",
    "ModelConfiguration",
    "ResourceConfiguration",
    "ToolConfiguration",
    "WorkflowConfiguration",
    "AgentConfiguration",
    
    # Templates and rules
    "ValidationRule",
    "ConfigurationTemplate",
    
    # Validation framework (base types are in hacs-core)
    "ValidationResult",
    "ValidationReport",
    "ValidationEngine",
    
    # Validators
    "BaseValidator",
    "TypeSafetyValidator",
    "ConfigurationValidator",
    "HealthcareComplianceValidator",
    "CustomRuleValidator",
    
    # Convenience functions
    "validate_agent_config",
    "validate_all_configs",
    "create_custom_validator",
]
