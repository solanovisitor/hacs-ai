"""
HACS Registry - Resource Registration and Versioning System

This package provides registration, versioning, and lifecycle management 
for hacs-core healthcare resources. It acts as a wrapper/facade around
hacs-core resources rather than redefining them.

Core Architecture:
    🏗️ hacs-core: Defines healthcare resources (Patient, Observation, etc.)
    📋 hacs-registry: Registers, versions, and manages those resources
    🤖 Agent management: Configures agents using registered resources
    🔧 Tool integration: Manages tool access to registered resources
    
Key Principles:
    • Pure wrapper pattern - no resource redefinition
    • Registry as source of truth for resource metadata
    • Versioned configurations and templates
    • Healthcare-specific specializations
"""

# Core registry functionality
from .resource_registry import (
    ResourceStatus,
    ResourceCategory,
    ResourceMetadata,
    RegisteredResource,
    HACSResourceRegistry,
    get_global_registry,
    register_hacs_resource,
)

# Agent configuration and management
from .agent_registry import (
    AgentStatus,
    AgentConfigurationType,
    AgentMetadata,
    AgentConfiguration,
    AgentTemplate,
    HACSAgentRegistry,
    get_global_agent_registry,
)

# IAM and access control
from .iam_registry import (
    AccessLevel,
    PermissionScope,
    ComplianceRule,
    AuditEventType,
    ActorIdentity,
    Permission,
    AuditEntry,
    PermissionMatrix,
    HACSIAMRegistry,
    get_global_iam_registry,
    iam_context,
    require_permission,
)

# Tool registry (existing)
from .tool_registry import (
    HACSToolRegistry,
    get_global_registry as get_global_tool_registry,
    discover_hacs_tools
)

# Plugin discovery system
from .plugin_discovery import (
    PluginRegistry,
    ToolPlugin,
    PluginMetadata,
    register_tool,
    discover_hacs_plugins,
    plugin_registry
)

# Versioning system
from .versioning import (
    VersionStatus,
    VersionInfo,
    SemanticVersion,
    ToolVersionManager,
    version_manager,
    check_tool_version,
    register_tool_version,
    get_tool_version_info
)

# Integration framework (existing)
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

# Validation framework (updated to work with registered resources)
from .validation import (
    ValidationResult,
    ValidationReport,
    ValidationEngine,
    BaseValidator,
    TypeSafetyValidator,
    ConfigurationValidator,
    HealthcareComplianceValidator,
    CustomRuleValidator,
    validate_agent_config,
    validate_all_configs,
    create_custom_validator,
)

# Exceptions
from .exceptions import RegistryError

__version__ = "0.2.0"  # Updated for new architecture

__all__ = [
    # Resource registry - Core functionality
    "ResourceStatus",
    "ResourceCategory", 
    "ResourceMetadata",
    "RegisteredResource",
    "HACSResourceRegistry",
    "get_global_registry",
    "register_hacs_resource",
    
    # Agent registry - Agent management
    "AgentStatus",
    "AgentConfigurationType",
    "AgentMetadata", 
    "AgentConfiguration",
    "AgentTemplate",
    "HACSAgentRegistry",
    "get_global_agent_registry",
    
    # IAM registry - Access control
    "AccessLevel",
    "PermissionScope",
    "ComplianceRule",
    "AuditEventType",
    "ActorIdentity",
    "Permission",
    "AuditEntry",
    "PermissionMatrix",
    "HACSIAMRegistry",
    "get_global_iam_registry",
    "iam_context",
    "require_permission",
    
    # Tool registry - Tool management
    "HACSToolRegistry",
    "get_global_tool_registry",
    "discover_hacs_tools",
    
    # Plugin discovery system
    "PluginRegistry",
    "ToolPlugin", 
    "PluginMetadata",
    "register_tool",
    "discover_hacs_plugins",
    "plugin_registry",
    
    # Versioning system
    "VersionStatus",
    "VersionInfo",
    "SemanticVersion", 
    "ToolVersionManager",
    "version_manager",
    "check_tool_version",
    "register_tool_version",
    "get_tool_version_info",
    
    # Integration framework - Tool execution
    "HACSToolIntegrationManager",
    "get_integration_manager",
    "FrameworkType",
    "ExecutionStrategyType", 
    "ExecutionContext",
    "ToolExecutionResult",
    "get_langchain_tools",
    "get_mcp_tools",
    "execute_hacs_tool",
    
    # Validation framework - Resource validation
    "ValidationResult",
    "ValidationReport",
    "ValidationEngine",
    "BaseValidator",
    "TypeSafetyValidator",
    "ConfigurationValidator",
    "HealthcareComplianceValidator",
    "CustomRuleValidator",
    "validate_agent_config",
    "validate_all_configs",
    "create_custom_validator",
    
    # Exceptions
    "RegistryError",
]

# Registry convenience functions
def register_patient_template(name: str, version: str = "1.0.0", **kwargs) -> RegisteredResource:
    """Convenience function to register a Patient resource template."""
    from hacs_core.models import Patient
    return register_hacs_resource(
        Patient, name, version, 
        f"Patient template: {name}",
        ResourceCategory.CLINICAL,
        **kwargs
    )

def register_workflow_template(name: str, version: str = "1.0.0", **kwargs) -> RegisteredResource:
    """Convenience function to register a WorkflowDefinition template."""
    from hacs_core.models.workflow import WorkflowDefinition
    return register_hacs_resource(
        WorkflowDefinition, name, version,
        f"Workflow template: {name}", 
        ResourceCategory.WORKFLOW,
        **kwargs
    )

def create_cardiology_agent(name: str, **config) -> AgentConfiguration:
    """Convenience function to create a cardiology agent."""
    from hacs_core import HealthcareDomain, AgentRole
    
    agent_registry = get_global_agent_registry()
    
    metadata = AgentMetadata(
        name=name,
        version="1.0.0",
        description=f"Cardiology agent: {name}",
        domain=HealthcareDomain.CARDIOLOGY,
        role=AgentRole.CLINICAL_ASSISTANT
    )
    
    agent_config = AgentConfiguration(
        agent_id=f"cardiology-{name.lower().replace(' ', '-')}",
        metadata=metadata,
        **config
    )
    
    agent_registry.register_agent(agent_config)
    return agent_config

def create_emergency_agent(name: str, **config) -> AgentConfiguration:
    """Convenience function to create an emergency medicine agent."""
    from hacs_core import HealthcareDomain, AgentRole
    
    agent_registry = get_global_agent_registry()
    
    metadata = AgentMetadata(
        name=name,
        version="1.0.0", 
        description=f"Emergency medicine agent: {name}",
        domain=HealthcareDomain.EMERGENCY,
        role=AgentRole.TRIAGE_SPECIALIST
    )
    
    agent_config = AgentConfiguration(
        agent_id=f"emergency-{name.lower().replace(' ', '-')}",
        metadata=metadata,
        **config
    )
    
    agent_registry.register_agent(agent_config)
    return agent_config

# Add convenience functions to __all__
__all__.extend([
    "register_patient_template",
    "register_workflow_template", 
    "create_cardiology_agent",
    "create_emergency_agent",
])