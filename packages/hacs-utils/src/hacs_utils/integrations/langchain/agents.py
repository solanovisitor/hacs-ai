"""
Configurable Healthcare Agent Factories for HACS-LangChain Integration

This module provides highly configurable agent factories that allow healthcare developers
to customize every aspect: prompts, parameters, models, resources, tools, and workflows.

Key principles:
    🔧 Everything is configurable
    🏥 Healthcare-domain aware
    🔌 Plugin-based architecture
    📋 Template-driven prompts
    ⚙️ Parameter injection
    🎯 Resource customization

⚠️  ARCHITECTURE NOTE: This module uses proper HACS configuration classes from 
    hacs-registry instead of duplicating configuration logic. Fallback classes
    are minimal and only used when hacs-registry is not available.
"""

import logging
import yaml
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable, Type
from dataclasses import dataclass, field

try:
    from langchain.agents import AgentExecutor, create_openai_functions_agent
    from langchain.agents.agent import BaseMultiActionAgent, BaseSingleActionAgent
    from langchain.schema import BaseLanguageModel
    from langchain.tools import BaseTool
    _has_langchain_agents = True
except ImportError:
    _has_langchain_agents = False
    # Fallback classes
    class BaseLanguageModel:
        def __call__(self, prompt: str) -> str:
            return "Mock LLM response"
    
    class BaseTool:
        def __init__(self, name: str, description: str):
            self.name = name
            self.description = description
    
    class BaseMultiActionAgent:
        pass
    
    class BaseSingleActionAgent:
        pass
    
    class AgentExecutor:
        def __init__(self, agent=None, tools=None, **kwargs):
            self.agent = agent
            self.tools = tools or []
        
        def run(self, input: str) -> str:
            return "Mock agent execution result"
    
    def create_openai_functions_agent(*args, **kwargs):
        return BaseSingleActionAgent()

# Always import from hacs_core since it's a dependency
from hacs_core import (
    HealthcareDomain, AgentRole, AgentInteractionStrategy,
    AgentMemoryStrategy, AgentRetrievalStrategy,
    VectorStoreType, EmbeddingStrategy
)

try:
    from hacs_registry import (
        AgentConfiguration, PromptConfiguration,
        ModelConfiguration, ResourceConfiguration,
        ToolConfiguration, WorkflowConfiguration
    )
    _has_hacs_registry = True
except ImportError:
    _has_hacs_registry = False

from .memory import MemoryConfig, MemoryFactory
from .chains import ChainType, ChainConfig, HealthcareChainFactory
from .retrievers import RetrievalConfig, RetrieverFactory
from .tools import get_hacs_tools

logger = logging.getLogger(__name__)

# Use proper HACS configuration classes from hacs-registry
# These provide full validation, persistence, and versioning capabilities

# Create minimal fallback configuration classes if hacs_registry is not available
# These are intentionally simple and provide basic functionality only
if not _has_hacs_registry:
    from dataclasses import dataclass, field
    
    @dataclass
    class PromptConfiguration:
        """Minimal prompt configuration fallback - use hacs_registry for full features."""
        system_prompt_template: str = ""
        human_prompt_template: str = ""
        custom_variables: Dict[str, Any] = field(default_factory=dict)
    
    @dataclass  
    class ModelConfiguration:
        """Minimal model configuration fallback - use hacs_registry for full features."""
        model_name: str = "gpt-3.5-turbo"
        temperature: float = 0.7
        max_tokens: Optional[int] = None
        api_key: Optional[str] = None
        base_url: Optional[str] = None
    
    @dataclass
    class ResourceConfiguration:
        """Minimal resource configuration fallback - use hacs_registry for full features."""
        enabled_resource_types: List[str] = field(default_factory=list)
    
    @dataclass
    class ToolConfiguration:
        """Minimal tool configuration fallback - use hacs_registry for full features."""
        enabled_tools: List[str] = field(default_factory=list)
        max_execution_time: float = 30.0
    
    @dataclass
    class WorkflowConfiguration:
        """Minimal workflow configuration fallback - use hacs_registry for full features."""
        enabled_steps: List[str] = field(default_factory=list)
    
    @dataclass
    class AgentConfiguration:
        """Minimal agent configuration fallback - use hacs_registry for full features."""
        agent_name: str = "default"
        strategy: AgentInteractionStrategy = AgentInteractionStrategy.CONVERSATIONAL

@dataclass
class HealthcareAgentConfiguration:
    """Comprehensive agent configuration."""
    
    # Basic identification
    agent_name: str = "HealthcareAgent"
    agent_description: str = "Configurable healthcare AI agent"
    domain: HealthcareDomain = HealthcareDomain.GENERAL
    role: AgentRole = AgentRole.CLINICAL_ASSISTANT
    
    # Component configurations
    prompt_config: PromptConfiguration = field(default_factory=PromptConfiguration)
    model_config: ModelConfiguration = field(default_factory=ModelConfiguration)
    resource_config: ResourceConfiguration = field(default_factory=ResourceConfiguration)
    tool_config: ToolConfiguration = field(default_factory=ToolConfiguration)
    workflow_config: WorkflowConfiguration = field(default_factory=WorkflowConfiguration)
    
    # Memory configuration
    memory_config: MemoryConfig = field(default_factory=MemoryConfig)
    memory_strategy: AgentMemoryStrategy = AgentMemoryStrategy.CLINICAL
    
    # Retrieval configuration
    retrieval_config: RetrievalConfig = field(default_factory=RetrievalConfig)
    retrieval_strategy: AgentRetrievalStrategy = AgentRetrievalStrategy.SEMANTIC
    
    # Chain configuration
    chain_config: ChainConfig = field(default_factory=ChainConfig)
    enabled_chains: List[ChainType] = field(default_factory=list)
    
    # Vector store configuration
    vector_store_type: VectorStoreType = VectorStoreType.FAISS
    embedding_strategy: EmbeddingStrategy = EmbeddingStrategy.CLINICAL
    
    # Plugin configurations
    plugins: Dict[str, Any] = field(default_factory=dict)
    custom_extensions: Dict[str, Callable] = field(default_factory=dict)

class ConfigurableAgentBuilder(ABC):
    """Abstract builder for configurable healthcare agents."""
    
    def __init__(self, config: HealthcareAgentConfiguration):
        self.config = config
        self.llm: Optional[BaseLanguageModel] = None
        self.tools: List[BaseTool] = []
        self.memory = None
        self.retriever = None
        self.chains = []
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def reset(self) -> 'ConfigurableAgentBuilder':
        """Reset builder state."""
        self.llm = None
        self.tools = []
        self.memory = None
        self.retriever = None
        self.chains = []
        return self
    
    def configure_model(self, custom_llm: BaseLanguageModel = None) -> 'ConfigurableAgentBuilder':
        """Configure the language model."""
        if custom_llm:
            self.llm = custom_llm
        else:
            # Create model from configuration
            self.llm = self._create_model_from_config()
        return self
    
    def configure_tools(self) -> 'ConfigurableAgentBuilder':
        """Configure tools based on configuration."""
        # Get HACS tools
        if self.config.tool_config.enabled_tools:
            hacs_tools = []
            try:
                all_tools = get_hacs_tools()
                hacs_tools = [
                    tool for tool in all_tools 
                    if tool.name in self.config.tool_config.enabled_tools
                ]
            except Exception as e:
                self.logger.warning(f"Failed to load HACS tools: {e}")
        
        # Add custom tools
        custom_tools = self.config.tool_config.custom_tools
        
        self.tools = hacs_tools + custom_tools
        return self
    
    def configure_memory(self) -> 'ConfigurableAgentBuilder':
        """Configure memory based on configuration."""
        try:
            self.memory = MemoryFactory.create_langchain_memory(
                self.config.memory_strategy,
                self.config.memory_config
            )
        except Exception as e:
            self.logger.warning(f"Failed to create memory: {e}")
            self.memory = None
        return self
    
    def configure_retriever(self) -> 'ConfigurableAgentBuilder':
        """Configure retriever based on configuration."""
        try:
            self.retriever = RetrieverFactory.create_retriever(
                self.config.retrieval_strategy,
                self.config.retrieval_config
            )
        except Exception as e:
            self.logger.warning(f"Failed to create retriever: {e}")
            self.retriever = None
        return self
    
    def configure_chains(self) -> 'ConfigurableAgentBuilder':
        """Configure chains based on configuration."""
        self.chains = []
        for chain_type in self.config.enabled_chains:
            try:
                chain = HealthcareChainFactory.create_chain(
                    chain_type,
                    self.llm,
                    self.config.chain_config
                )
                self.chains.append(chain)
            except Exception as e:
                self.logger.warning(f"Failed to create chain {chain_type}: {e}")
        return self
    
    @abstractmethod
    def build_agent(self) -> AgentExecutor:
        """Build the final agent."""
        pass
    
    def _create_model_from_config(self) -> BaseLanguageModel:
        """Create language model from configuration."""
        # This would create the actual model based on config
        # For now, return a mock
        return BaseLanguageModel()
    
    def _build_prompts(self) -> Dict[str, str]:
        """Build prompts from configuration."""
        prompts = {}
        
        # Build system prompt
        system_prompt = self.config.prompt_config.system_prompt_template
        
        # Add domain-specific instructions
        domain_instructions = self.config.prompt_config.domain_specific_instructions.get(
            self.config.domain.value, ""
        )
        
        # Add role-specific instructions
        role_instructions = self.config.prompt_config.role_specific_instructions.get(
            self.config.role.value, ""
        )
        
        # Combine prompts
        full_system_prompt = f"{system_prompt}\n{domain_instructions}\n{role_instructions}"
        
        # Add safety and formatting instructions
        if self.config.prompt_config.safety_instructions:
            full_system_prompt += f"\n{self.config.prompt_config.safety_instructions}"
        
        if self.config.prompt_config.output_format_instructions:
            full_system_prompt += f"\n{self.config.prompt_config.output_format_instructions}"
        
        prompts['system'] = full_system_prompt
        prompts['human'] = self.config.prompt_config.human_prompt_template
        
        return prompts

class ClinicalAssistantAgentBuilder(ConfigurableAgentBuilder):
    """Builder for clinical assistant agents."""
    
    def build_agent(self) -> AgentExecutor:
        """Build clinical assistant agent."""
        if not _has_langchain_agents:
            return AgentExecutor()
        
        try:
            # Build prompts
            prompts = self._build_prompts()
            
            # Create agent
            agent = create_openai_functions_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=prompts.get('system', 'You are a clinical assistant AI.')
            )
            
            # Create executor
            executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                memory=self.memory,
                verbose=True,
                max_iterations=self.config.workflow_config.step_configurations.get('max_iterations', 10)
            )
            
            return executor
            
        except Exception as e:
            self.logger.error(f"Failed to build clinical assistant agent: {e}")
            return AgentExecutor()

class DiagnosticAssistantAgentBuilder(ConfigurableAgentBuilder):
    """Builder for diagnostic assistant agents."""
    
    def build_agent(self) -> AgentExecutor:
        """Build diagnostic assistant agent."""
        if not _has_langchain_agents:
            return AgentExecutor()
        
        # Similar implementation with diagnostic-specific configuration
        return AgentExecutor()

class HealthcareAgentFactory:
    """Factory for creating configurable healthcare agents."""
    
    _builders = {
        AgentRole.CLINICAL_ASSISTANT: ClinicalAssistantAgentBuilder,
        AgentRole.DIAGNOSTIC_ASSISTANT: DiagnosticAssistantAgentBuilder,
        # Add more builders as needed
    }
    
    @classmethod
    def create_agent(cls, config: HealthcareAgentConfiguration, 
                    custom_llm: BaseLanguageModel = None) -> AgentExecutor:
        """Create a healthcare agent with full configuration."""
        builder_class = cls._builders.get(config.role)
        if not builder_class:
            # Default to clinical assistant
            builder_class = ClinicalAssistantAgentBuilder
        
        builder = builder_class(config)
        
        return (builder
                .reset()
                .configure_model(custom_llm)
                .configure_tools()
                .configure_memory()
                .configure_retriever()
                .configure_chains()
                .build_agent())
    
    @classmethod
    def register_builder(cls, role: AgentRole, builder_class: Type[ConfigurableAgentBuilder]):
        """Register a custom agent builder."""
        cls._builders[role] = builder_class

class ConfigurationTemplates:
    """Predefined configuration templates for common use cases."""
    
    @staticmethod
    def cardiology_clinical_assistant() -> HealthcareAgentConfiguration:
        """Configuration for cardiology clinical assistant."""
        config = HealthcareAgentConfiguration(
            agent_name="CardiologyAssistant",
            domain=HealthcareDomain.CARDIOLOGY,
            role=AgentRole.CLINICAL_ASSISTANT
        )
        
        # Cardiology-specific prompts
        config.prompt_config.domain_specific_instructions[HealthcareDomain.CARDIOLOGY.value] = """
        You are specialized in cardiology and cardiovascular medicine. Focus on:
        - Cardiac risk assessment
        - ECG interpretation
        - Heart failure management
        - Coronary artery disease
        - Arrhythmia analysis
        """
        
        # Cardiology-specific tools
        config.tool_config.enabled_tools = [
            "create_hacs_record",
            "search_hacs_records", 
            "cardiac_risk_assessment",
            "ecg_analysis"
        ]
        
        # Cardiology-specific resources
        config.resource_config.enabled_resource_types = [
            "Patient",
            "Observation",
            "Condition",
            "Procedure",
            "RiskAssessment"
        ]
        
        return config
    
    @staticmethod
    def emergency_triage_agent() -> HealthcareAgentConfiguration:
        """Configuration for emergency triage agent."""
        config = HealthcareAgentConfiguration(
            agent_name="TriageAssistant",
            domain=HealthcareDomain.EMERGENCY,
            role=AgentRole.TRIAGE_SPECIALIST
        )
        
        # Emergency-specific prompts
        config.prompt_config.domain_specific_instructions[HealthcareDomain.EMERGENCY.value] = """
        You are an emergency triage specialist. Prioritize by:
        - Life-threatening conditions first
        - Rapid assessment protocols
        - ESI (Emergency Severity Index) guidelines
        - Time-critical interventions
        """
        
        # Fast response configuration
        config.model_config.temperature = 0.3  # More deterministic
        config.tool_config.max_execution_time = 10.0  # Faster execution
        
        return config
    
    @staticmethod
    def research_assistant() -> HealthcareAgentConfiguration:
        """Configuration for clinical research assistant."""
        config = HealthcareAgentConfiguration(
            agent_name="ResearchAssistant",
            domain=HealthcareDomain.GENERAL,
            role=AgentRole.CLINICAL_RESEARCHER
        )
        
        # Research-specific configuration
        config.retrieval_strategy = AgentRetrievalStrategy.MULTI_MODAL
        config.memory_strategy = AgentMemoryStrategy.EPISODIC
        config.embedding_strategy = EmbeddingStrategy.DOMAIN_SPECIFIC
        
        return config

# Convenience functions for quick agent creation
def create_cardiology_assistant(custom_llm: BaseLanguageModel = None) -> AgentExecutor:
    """Create a cardiology clinical assistant."""
    config = ConfigurationTemplates.cardiology_clinical_assistant()
    return HealthcareAgentFactory.create_agent(config, custom_llm)

def create_emergency_triage_agent(custom_llm: BaseLanguageModel = None) -> AgentExecutor:
    """Create an emergency triage agent."""
    config = ConfigurationTemplates.emergency_triage_agent()
    return HealthcareAgentFactory.create_agent(config, custom_llm)

def create_research_assistant(custom_llm: BaseLanguageModel = None) -> AgentExecutor:
    """Create a clinical research assistant."""
    config = ConfigurationTemplates.research_assistant()
    return HealthcareAgentFactory.create_agent(config, custom_llm)

def create_custom_agent(
    domain: HealthcareDomain,
    role: AgentRole,
    custom_prompts: Dict[str, str] = None,
    custom_tools: List[str] = None,
    custom_resources: List[str] = None,
    model_config: Dict[str, Any] = None,
    custom_llm: BaseLanguageModel = None
) -> AgentExecutor:
    """Create a fully customized healthcare agent."""
    
    config = HealthcareAgentConfiguration(
        domain=domain,
        role=role
    )
    
    # Apply customizations
    if custom_prompts:
        config.prompt_config.domain_specific_instructions.update(custom_prompts)
    
    if custom_tools:
        config.tool_config.enabled_tools = custom_tools
    
    if custom_resources:
        config.resource_config.enabled_resource_types = custom_resources
    
    if model_config:
        config.model_config.model_parameters.update(model_config)
    
    return HealthcareAgentFactory.create_agent(config, custom_llm)

# Simplified Configuration Classes
@dataclass
class AgentConfig:
    """Simplified agent configuration for easy setup."""
    
    name: str = "HealthcareAgent"
    domain: str = "general"
    role: str = "clinical_assistant"
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    tools: List[str] = field(default_factory=list)
    # Enhanced configuration options
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    enable_memory: bool = True
    enable_tools: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_config()
    
    def _validate_config(self):
        """Validate the configuration values."""
        # Validate temperature
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError(f"Temperature must be between 0.0 and 2.0, got {self.temperature}")
        
        # Validate domain
        valid_domains = [domain.value.lower() for domain in HealthcareDomain]
        if self.domain.lower() not in valid_domains:
            logger.warning(f"Domain '{self.domain}' not in standard domains: {valid_domains}")
        
        # Validate role
        valid_roles = [role.value.lower() for role in AgentRole]
        if self.role.lower() not in valid_roles:
            logger.warning(f"Role '{self.role}' not in standard roles: {valid_roles}")
    
    @classmethod
    def from_yaml(cls, file_path: Union[str, Path]) -> 'AgentConfig':
        """
        Load configuration from YAML file.
        
        Args:
            file_path: Path to YAML configuration file
            
        Returns:
            AgentConfig instance
            
        Raises:
            FileNotFoundError: If the YAML file doesn't exist
            yaml.YAMLError: If the YAML is malformed
            ValueError: If the configuration is invalid
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in {file_path}: {e}")
        
        if not isinstance(data, dict):
            raise ValueError(f"YAML file must contain a dictionary, got {type(data)}")
        
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentConfig':
        """
        Create configuration from dictionary.
        
        Args:
            data: Configuration dictionary
            
        Returns:
            AgentConfig instance
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Filter out any extra keys that aren't valid fields
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        # Log any ignored fields
        ignored_fields = set(data.keys()) - valid_fields
        if ignored_fields:
            logger.warning(f"Ignoring unknown configuration fields: {ignored_fields}")
        
        return cls(**filtered_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'name': self.name,
            'domain': self.domain,
            'role': self.role,
            'model': self.model,
            'temperature': self.temperature,
            'tools': self.tools
        }
    
    def to_healthcare_config(self) -> 'HealthcareAgentConfiguration':
        """Convert to full HealthcareAgentConfiguration."""
        # Map simple values to enum types
        domain_map = {
            'general': HealthcareDomain.GENERAL,
            'cardiology': HealthcareDomain.CARDIOLOGY,
            'oncology': HealthcareDomain.ONCOLOGY,
            'neurology': HealthcareDomain.NEUROLOGY,
            'psychiatry': HealthcareDomain.PSYCHIATRY,
            'emergency': HealthcareDomain.EMERGENCY,
            'icu': HealthcareDomain.ICU,
            'surgery': HealthcareDomain.SURGERY,
            'pediatrics': HealthcareDomain.PEDIATRICS,
            'geriatrics': HealthcareDomain.GERIATRICS,
            'radiology': HealthcareDomain.RADIOLOGY,
            'pathology': HealthcareDomain.PATHOLOGY,
            'pharmacy': HealthcareDomain.PHARMACY,
            'nursing': HealthcareDomain.NURSING,
            'administration': HealthcareDomain.ADMINISTRATION,
            'research': HealthcareDomain.RESEARCH,
            'education': HealthcareDomain.EDUCATION
        }
        
        role_map = {
            'clinical_assistant': AgentRole.CLINICAL_ASSISTANT,
            'diagnostic_assistant': AgentRole.DIAGNOSTIC_ASSISTANT,
            'treatment_planner': AgentRole.TREATMENT_PLANNER,
            'clinical_researcher': AgentRole.CLINICAL_RESEARCHER,
            'patient_educator': AgentRole.PATIENT_EDUCATOR,
            'quality_assessor': AgentRole.QUALITY_ASSESSOR,
            'triage_specialist': AgentRole.TRIAGE_SPECIALIST,
            'medication_reviewer': AgentRole.MEDICATION_REVIEWER,
            'documentation_specialist': AgentRole.DOCUMENTATION_SPECIALIST,
            'care_coordinator': AgentRole.CARE_COORDINATOR,
            'clinical_decision_support': AgentRole.CLINICAL_DECISION_SUPPORT,
            'protocol_advisor': AgentRole.PROTOCOL_ADVISOR
        }
        
        # Create model configuration using proper HACS types
        model_config_data = {
            'model_name': self.model,
            'temperature': self.temperature
        }
        
        # Add optional model parameters
        if self.max_tokens:
            model_config_data['max_tokens'] = self.max_tokens
        
        if self.api_key:
            model_config_data['api_key'] = self.api_key
            
        if self.base_url:
            model_config_data['base_url'] = self.base_url
        
        model_config = ModelConfiguration(**model_config_data)
        
        # Create prompt configuration with system prompt
        prompt_config_data = {}
        if self.system_prompt:
            prompt_config_data['system_prompt_template'] = self.system_prompt
        
        prompt_config = PromptConfiguration(**prompt_config_data)
        
        # Create tool configuration
        tool_config = ToolConfiguration(
            enabled_tools=self.tools if self.enable_tools else []
        )
        
        # Create memory configuration
        memory_config = MemoryConfig(
            strategy=AgentMemoryStrategy.CLINICAL if self.enable_memory else AgentMemoryStrategy.NONE
        )
        
        return HealthcareAgentConfiguration(
            agent_name=self.name,
            domain=domain_map.get(self.domain.lower(), HealthcareDomain.GENERAL),
            role=role_map.get(self.role.lower(), AgentRole.CLINICAL_ASSISTANT),
            model_config=model_config,
            prompt_config=prompt_config,
            tool_config=tool_config,
            memory_config=memory_config,
            retrieval_config=RetrievalConfig(strategy=AgentRetrievalStrategy.SEMANTIC),
            chain_config=ChainConfig(chain_type=ChainType.CLINICAL_ASSESSMENT)
        )

class AgentFactory:
    """Simplified agent factory to hide complexity from users."""
    
    @staticmethod
    def create(config: Union[AgentConfig, Dict[str, Any], str, Path], **kwargs) -> Any:
        """
        Create an agent from configuration.
        
        Args:
            config: Can be:
                - AgentConfig instance
                - Dictionary with config data
                - Path to YAML config file
                - YAML string content
            **kwargs: Additional options:
                - force_mock: Force using mock agent
                - verbose: Enable verbose logging
                - validate_tools: Validate that tools are available
        
        Returns:
            Configured agent instance
            
        Raises:
            ValueError: If configuration is invalid
            FileNotFoundError: If YAML file is not found
        """
        verbose = kwargs.get('verbose', False)
        force_mock = kwargs.get('force_mock', False)
        validate_tools = kwargs.get('validate_tools', True)
        
        if verbose:
            logger.setLevel(logging.DEBUG)
            
        logger.debug(f"Creating agent from config type: {type(config)}")
        
        # Handle different input types
        try:
            if isinstance(config, (str, Path)):
                if isinstance(config, str) and ('\n' in config or '{' in config):
                    # YAML string content or JSON
                    try:
                        data = yaml.safe_load(config)
                    except yaml.YAMLError:
                        # Try as JSON
                        import json
                        data = json.loads(config)
                    agent_config = AgentConfig.from_dict(data)
                else:
                    # File path
                    agent_config = AgentConfig.from_yaml(config)
            elif isinstance(config, dict):
                agent_config = AgentConfig.from_dict(config)
            elif isinstance(config, AgentConfig):
                agent_config = config
            else:
                raise ValueError(f"Unsupported config type: {type(config)}")
        except Exception as e:
            logger.error(f"Failed to parse configuration: {e}")
            raise ValueError(f"Invalid configuration: {e}")
        
        logger.debug(f"Created agent config: {agent_config.name} ({agent_config.domain}/{agent_config.role})")
        
        # Validate tools if requested
        if validate_tools and agent_config.tools:
            AgentFactory._validate_tools(agent_config.tools)
        
        # Convert to full configuration
        full_config = agent_config.to_healthcare_config()
        
        # Return mock agent if forced or if LangChain is not available
        if force_mock or not _has_langchain_agents:
            logger.info(f"Using mock agent for {agent_config.name}")
            return MockAgent(config=full_config)
        
        # Create agent using existing builder
        try:
            builder = AgentFactory._get_builder(full_config.role)
            logger.debug(f"Using builder: {type(builder).__name__}")
            agent = builder.build_agent(full_config)
            logger.info(f"Successfully created agent: {agent_config.name}")
            return agent
        except Exception as e:
            logger.warning(f"Failed to build full agent, using mock: {e}")
            return MockAgent(config=full_config)
    
    @staticmethod
    def _get_builder(role: AgentRole):
        """Get the appropriate builder for a given role."""
        builder_map = {
            AgentRole.CLINICAL_ASSISTANT: ClinicalAssistantAgentBuilder,
            AgentRole.DIAGNOSTIC_ASSISTANT: DiagnosticAssistantAgentBuilder,
            AgentRole.TREATMENT_PLANNER: ClinicalAssistantAgentBuilder,  # Use as default
            AgentRole.CLINICAL_RESEARCHER: ClinicalAssistantAgentBuilder,
            # Add more mappings as needed
        }
        
        builder_class = builder_map.get(role, ClinicalAssistantAgentBuilder)
        return builder_class()
    
    @staticmethod
    def _validate_tools(tools: List[str]) -> None:
        """Validate that the requested tools are available."""
        try:
            from .tools import get_hacs_tools
            available_tools = get_hacs_tools()
            available_tool_names = {tool.name for tool in available_tools}
            
            missing_tools = set(tools) - available_tool_names
            if missing_tools:
                logger.warning(f"Some requested tools are not available: {missing_tools}")
                logger.debug(f"Available tools: {available_tool_names}")
        except ImportError:
            logger.debug("Could not validate tools - tools module not available")
    
    @staticmethod
    def create_preset(preset_name: str, **overrides) -> Any:
        """
        Create an agent from a preset configuration.
        
        Args:
            preset_name: Name of the preset ('cardiology', 'emergency', 'research', etc.)
            **overrides: Override any configuration values
            
        Returns:
            Configured agent instance
        """
        presets = {
            'cardiology': {
                'name': 'CardiologyAssistant',
                'domain': 'cardiology',
                'role': 'clinical_assistant',
                'model': 'gpt-4',
                'temperature': 0.3,
                'tools': ['patient_search', 'medication_lookup', 'clinical_guidelines'],
                'system_prompt': 'You are a specialized cardiology assistant. Focus on heart conditions, treatments, and patient care.'
            },
            'emergency': {
                'name': 'EmergencyTriageAgent',
                'domain': 'emergency',
                'role': 'triage_specialist',
                'model': 'gpt-4',
                'temperature': 0.1,
                'tools': ['patient_search', 'clinical_protocols', 'medication_lookup'],
                'system_prompt': 'You are an emergency triage specialist. Prioritize patient safety and rapid assessment.'
            },
            'research': {
                'name': 'ClinicalResearcher',
                'domain': 'research',
                'role': 'clinical_researcher',
                'model': 'gpt-4',
                'temperature': 0.5,
                'tools': ['literature_search', 'data_analysis', 'protocol_review'],
                'system_prompt': 'You are a clinical research assistant. Focus on evidence-based analysis and research protocols.'
            }
        }
        
        if preset_name not in presets:
            available = list(presets.keys())
            raise ValueError(f"Unknown preset '{preset_name}'. Available presets: {available}")
        
        config_data = presets[preset_name].copy()
        config_data.update(overrides)
        
        return AgentFactory.create(config_data)

class MockAgent:
    """Mock agent for when full LangChain is not available."""
    
    def __init__(self, config: HealthcareAgentConfiguration):
        self.config = config
        self.name = config.agent_name
    
    def run(self, input_text: str) -> str:
        return f"Mock response from {self.name} for: {input_text}"
    
    def __call__(self, input_text: str) -> str:
        return self.run(input_text)

__all__ = [
    # Core classes
    'HealthcareDomain',
    'AgentRole',
    'HealthcareAgentConfiguration',
    'PromptConfiguration',
    'ModelConfiguration',
    'ResourceConfiguration',
    'ToolConfiguration',
    'WorkflowConfiguration',
    # Simplified configuration classes
    'AgentConfig',
    'AgentFactory',
    'MockAgent',
    # Builders
    'ConfigurableAgentBuilder',
    'ClinicalAssistantAgentBuilder',
    'DiagnosticAssistantAgentBuilder',
    # Factory
    'HealthcareAgentFactory',
    # Templates
    'ConfigurationTemplates',
    # Convenience functions
    'create_cardiology_assistant',
    'create_emergency_triage_agent',
    'create_research_assistant',
    'create_custom_agent',
]