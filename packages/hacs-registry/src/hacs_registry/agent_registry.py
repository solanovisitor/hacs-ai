"""
HACS Agent Registry

This module provides registration and configuration management for healthcare
agents using hacs-core resources. Agents are configured using registered
resources rather than redefining them.

Architecture:
    🤖 Agent configurations reference registered hacs-core resources
    📋 Versioned agent templates and configurations
    🔧 Agent lifecycle management (draft, testing, production)
    🏥 Healthcare-specific agent specializations
"""

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

from pydantic import Field, BaseModel
from hacs_core import BaseResource
from hacs_core import (
    HealthcareDomain, AgentRole,
    AgentInteractionStrategy, AgentMemoryStrategy,
    AgentChainStrategy, AgentRetrievalStrategy,
    VectorStoreType, EmbeddingStrategy
)

from .resource_registry import get_global_registry, RegisteredResource, ResourceStatus

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    """Lifecycle status of an agent configuration."""
    DRAFT = "draft"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class AgentConfigurationType(str, Enum):
    """Types of agent configurations."""
    TEMPLATE = "template"        # Reusable agent template
    INSTANCE = "instance"        # Specific agent instance
    PROTOTYPE = "prototype"      # Experimental agent
    SPECIALIZATION = "specialization"  # Domain-specific variant


@dataclass
class AgentMetadata:
    """Metadata for an agent configuration."""
    name: str
    version: str
    description: str
    domain: HealthcareDomain
    role: AgentRole
    config_type: AgentConfigurationType = AgentConfigurationType.INSTANCE
    status: AgentStatus = AgentStatus.DRAFT
    author: Optional[str] = None
    organization: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    use_cases: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tested_at: Optional[datetime] = None
    deployed_at: Optional[datetime] = None


class AgentConfiguration(BaseResource):
    """
    Agent configuration that references registered hacs-core resources.
    
    This defines how an agent uses registered resources rather than
    redefining those resources.
    """
    
    resource_type: str = Field(default="AgentConfiguration", description="Resource type")
    
    # Agent metadata
    agent_id: str = Field(description="Unique agent identifier")
    metadata: AgentMetadata = Field(description="Agent metadata")
    
    # Agent behavior configuration
    interaction_strategy: AgentInteractionStrategy = Field(
        default=AgentInteractionStrategy.CONVERSATIONAL,
        description="How the agent interacts"
    )
    memory_strategy: AgentMemoryStrategy = Field(
        default=AgentMemoryStrategy.CLINICAL,
        description="Agent memory management"
    )
    chain_strategy: AgentChainStrategy = Field(
        default=AgentChainStrategy.SEQUENTIAL,
        description="Chain execution strategy"
    )
    retrieval_strategy: AgentRetrievalStrategy = Field(
        default=AgentRetrievalStrategy.SEMANTIC,
        description="Information retrieval strategy"
    )
    
    # Technical configuration
    vector_store_type: VectorStoreType = Field(
        default=VectorStoreType.FAISS,
        description="Vector store implementation"
    )
    embedding_strategy: EmbeddingStrategy = Field(
        default=EmbeddingStrategy.CLINICAL,
        description="Embedding strategy"
    )
    
    # Resource references (using registry IDs)
    enabled_resources: List[str] = Field(
        default_factory=list,
        description="List of registered resource IDs this agent can use"
    )
    
    # Agent-specific configurations for resources
    resource_configurations: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Agent-specific configuration for each resource"
    )
    
    # Prompt and model configuration
    prompt_template_id: Optional[str] = Field(
        default=None,
        description="ID of registered prompt template"
    )
    model_configuration: Dict[str, Any] = Field(
        default_factory=dict,
        description="Model parameters and settings"
    )
    
    # Safety and compliance
    safety_constraints: List[str] = Field(
        default_factory=list,
        description="Safety constraints for this agent"
    )
    compliance_requirements: List[str] = Field(
        default_factory=list,
        description="Compliance requirements (HIPAA, etc.)"
    )
    audit_level: str = Field(
        default="standard",
        description="Auditing level (basic, standard, comprehensive)"
    )
    
    # Performance and scaling
    max_concurrent_requests: int = Field(
        default=10,
        description="Maximum concurrent requests"
    )
    timeout_seconds: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    rate_limit_per_minute: Optional[int] = Field(
        default=None,
        description="Rate limit for requests per minute"
    )
    
    # Deployment configuration
    deployment_environment: str = Field(
        default="development",
        description="Target deployment environment"
    )
    resource_requirements: Dict[str, Any] = Field(
        default_factory=dict,
        description="Computational resource requirements"
    )
    
    def get_enabled_resources(self) -> List[RegisteredResource]:
        """Get the actual registered resources this agent can use."""
        registry = get_global_registry()
        resources = []
        
        for resource_id in self.enabled_resources:
            resource = registry.get_resource(resource_id)
            if resource and resource.metadata.status == ResourceStatus.PUBLISHED:
                resources.append(resource)
        
        return resources
    
    def add_resource(self, resource_id: str, configuration: Optional[Dict[str, Any]] = None):
        """Add a resource to this agent's enabled resources."""
        if resource_id not in self.enabled_resources:
            self.enabled_resources.append(resource_id)
        
        if configuration:
            self.resource_configurations[resource_id] = configuration
    
    def remove_resource(self, resource_id: str):
        """Remove a resource from this agent's enabled resources."""
        if resource_id in self.enabled_resources:
            self.enabled_resources.remove(resource_id)
        
        if resource_id in self.resource_configurations:
            del self.resource_configurations[resource_id]
    
    def validate_resources(self) -> List[str]:
        """Validate that all enabled resources are available and published."""
        issues = []
        registry = get_global_registry()
        
        for resource_id in self.enabled_resources:
            resource = registry.get_resource(resource_id)
            if not resource:
                issues.append(f"Resource not found: {resource_id}")
            elif resource.metadata.status != ResourceStatus.PUBLISHED:
                issues.append(f"Resource not published: {resource_id} (status: {resource.metadata.status})")
        
        return issues


class AgentTemplate(BaseResource):
    """
    Reusable agent template for creating agent configurations.
    
    Templates define common patterns that can be instantiated
    with specific parameters.
    """
    
    resource_type: str = Field(default="AgentTemplate", description="Resource type")
    
    # Template metadata
    template_id: str = Field(description="Unique template identifier")
    name: str = Field(description="Template name")
    version: str = Field(description="Template version")
    description: str = Field(description="Template description")
    
    # Template configuration
    domain: HealthcareDomain = Field(description="Target healthcare domain")
    role: AgentRole = Field(description="Agent role")
    
    # Default configuration values
    default_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Default configuration values"
    )
    
    # Required and optional parameters for instantiation
    required_parameters: List[str] = Field(
        default_factory=list,
        description="Parameters that must be provided"
    )
    optional_parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional parameters with defaults"
    )
    
    # Recommended resources for this template
    recommended_resources: List[str] = Field(
        default_factory=list,
        description="Registry IDs of recommended resources"
    )
    
    def instantiate(self, **parameters) -> AgentConfiguration:
        """Create an agent configuration from this template."""
        # Validate required parameters
        missing = [param for param in self.required_parameters if param not in parameters]
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")
        
        # Merge parameters with defaults
        config_data = self.default_config.copy()
        config_data.update(parameters)
        config_data.update(self.optional_parameters)
        config_data.update(parameters)  # Parameters override defaults
        
        # Create agent metadata
        agent_id = f"{self.template_id}-{parameters.get('instance_name', 'instance')}"
        metadata = AgentMetadata(
            name=parameters.get('name', f"{self.name} Instance"),
            version="1.0.0",
            description=parameters.get('description', f"Instance of {self.name} template"),
            domain=self.domain,
            role=self.role,
            config_type=AgentConfigurationType.INSTANCE
        )
        
        # Create agent configuration
        agent_config = AgentConfiguration(
            agent_id=agent_id,
            metadata=metadata,
            enabled_resources=self.recommended_resources.copy(),
            **config_data
        )
        
        return agent_config


class HACSAgentRegistry:
    """
    Registry for managing agent configurations and templates.
    
    Provides lifecycle management for healthcare agents without
    redefining any hacs-core resources.
    """
    
    def __init__(self):
        self._configurations: Dict[str, AgentConfiguration] = {}
        self._templates: Dict[str, AgentTemplate] = {}
        self._by_domain: Dict[HealthcareDomain, List[str]] = {
            domain: [] for domain in HealthcareDomain
        }
        self._by_role: Dict[AgentRole, List[str]] = {
            role: [] for role in AgentRole
        }
    
    def register_agent(self, config: AgentConfiguration, actor_id: Optional[str] = None) -> str:
        """Register an agent configuration."""
        # IAM check for agent registration
        if actor_id:
            try:
                from .iam_registry import get_global_iam_registry, AccessLevel
                iam = get_global_iam_registry()
                if not iam.check_access(actor_id, f"agent_registry:{config.metadata.domain.value}", AccessLevel.WRITE):
                    raise PermissionError(f"Actor {actor_id} not authorized to register agents in {config.metadata.domain.value}")
            except ImportError:
                # IAM not available, proceed without check
                pass
        agent_id = config.agent_id
        self._configurations[agent_id] = config
        
        # Index by domain and role
        domain = config.metadata.domain
        role = config.metadata.role
        
        if agent_id not in self._by_domain[domain]:
            self._by_domain[domain].append(agent_id)
        if agent_id not in self._by_role[role]:
            self._by_role[role].append(agent_id)
        
        logger.info(f"Registered agent: {agent_id}")
        return agent_id
    
    def register_template(self, template: AgentTemplate) -> str:
        """Register an agent template."""
        template_id = template.template_id
        self._templates[template_id] = template
        
        logger.info(f"Registered agent template: {template_id}")
        return template_id
    
    def get_agent(self, agent_id: str) -> Optional[AgentConfiguration]:
        """Get an agent configuration by ID."""
        return self._configurations.get(agent_id)
    
    def get_template(self, template_id: str) -> Optional[AgentTemplate]:
        """Get an agent template by ID."""
        return self._templates.get(template_id)
    
    def list_agents(
        self,
        domain: Optional[HealthcareDomain] = None,
        role: Optional[AgentRole] = None,
        status: Optional[AgentStatus] = None
    ) -> List[AgentConfiguration]:
        """List agent configurations with optional filtering."""
        agents = []
        
        if domain:
            agent_ids = self._by_domain.get(domain, [])
        elif role:
            agent_ids = self._by_role.get(role, [])
        else:
            agent_ids = list(self._configurations.keys())
        
        for agent_id in agent_ids:
            agent = self._configurations[agent_id]
            if status is None or agent.metadata.status == status:
                agents.append(agent)
        
        return agents
    
    def list_templates(self, domain: Optional[HealthcareDomain] = None) -> List[AgentTemplate]:
        """List agent templates with optional domain filtering."""
        templates = []
        
        for template in self._templates.values():
            if domain is None or template.domain == domain:
                templates.append(template)
        
        return templates
    
    def create_from_template(self, template_id: str, **parameters) -> AgentConfiguration:
        """Create an agent configuration from a template."""
        template = self._templates.get(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        agent_config = template.instantiate(**parameters)
        self.register_agent(agent_config)
        return agent_config


# Global agent registry instance
_global_agent_registry: Optional[HACSAgentRegistry] = None


def get_global_agent_registry() -> HACSAgentRegistry:
    """Get the global agent registry instance."""
    global _global_agent_registry
    if _global_agent_registry is None:
        _global_agent_registry = HACSAgentRegistry()
    return _global_agent_registry


__all__ = [
    'AgentStatus',
    'AgentConfigurationType', 
    'AgentMetadata',
    'AgentConfiguration',
    'AgentTemplate',
    'HACSAgentRegistry',
    'get_global_agent_registry',
]