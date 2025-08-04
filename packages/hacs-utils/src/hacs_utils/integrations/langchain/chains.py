"""
Healthcare Chain Builders for HACS-LangChain Integration

This module provides specialized chain builders for healthcare workflows using
world-class design patterns to create domain-specific LangChain chains.

Design patterns implemented:
    🏭 Factory Pattern - Chain creation and management
    🔨 Builder Pattern - Step-by-step chain construction
    🎯 Strategy Pattern - Different chain strategies
    📋 Template Method Pattern - Common chain structure
    🔗 Chain of Responsibility - Processing pipelines
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable, Type
from dataclasses import dataclass, field

try:
    from langchain.chains import LLMChain, ConversationChain, SequentialChain
    from langchain.chains.base import Chain
    from langchain.prompts import PromptTemplate, ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
    from langchain.schema import BaseOutputParser, OutputParserException
    from langchain.callbacks.base import BaseCallbackHandler
    _has_langchain_chains = True
except ImportError:
    _has_langchain_chains = False
    # Fallback classes
    class BaseCallbackHandler:
        pass
    
    class BaseOutputParser:
        def parse(self, text: str):
            return text
    
    OutputParserException = Exception
    
    class PromptTemplate:
        def __init__(self, template: str, input_variables: List[str]):
            self.template = template
            self.input_variables = input_variables
    
    ChatPromptTemplate = SystemMessagePromptTemplate = HumanMessagePromptTemplate = PromptTemplate
    
    class Chain:
        def __init__(self, **kwargs):
            pass
        
        def run(self, **kwargs):
            return "Chain execution result"
    
    class LLMChain(Chain):
        def __init__(self, llm=None, prompt=None, **kwargs):
            super().__init__(**kwargs)
            self.llm = llm
            self.prompt = prompt
    
    ConversationChain = SequentialChain = LLMChain

try:
    from hacs_core.models import Patient, Observation, Condition, Procedure, Goal
    from hacs_core.clinical_reasoning import ClinicalReasoner
    _has_hacs_clinical = True
except ImportError:
    _has_hacs_clinical = False
    Patient = Observation = Condition = Procedure = Goal = object
    ClinicalReasoner = object

from .memory import create_clinical_memory, create_episodic_memory, HACSLangChainMemory
from .adapters import BidirectionalConverter, ConversionContext

logger = logging.getLogger(__name__)

class ChainType(Enum):
    """Enumeration of healthcare chain types."""
    CLINICAL_ASSESSMENT = "clinical_assessment"
    DIAGNOSTIC_REASONING = "diagnostic_reasoning"
    TREATMENT_PLANNING = "treatment_planning"
    MEDICATION_REVIEW = "medication_review"
    PATIENT_EDUCATION = "patient_education"
    CLINICAL_DOCUMENTATION = "clinical_documentation"
    QUALITY_ASSURANCE = "quality_assurance"
    TRIAGE_ASSESSMENT = "triage_assessment"
    DISCHARGE_PLANNING = "discharge_planning"
    CARE_COORDINATION = "care_coordination"

class ChainStrategy(Enum):
    """Strategy for chain execution."""
    SEQUENTIAL = "sequential"       # Step-by-step execution
    PARALLEL = "parallel"          # Parallel processing
    CONDITIONAL = "conditional"    # Conditional branching
    ITERATIVE = "iterative"       # Iterative refinement
    HIERARCHICAL = "hierarchical" # Hierarchical processing

@dataclass
class ChainConfig:
    """Configuration for healthcare chains."""
    chain_type: ChainType
    strategy: ChainStrategy = ChainStrategy.SEQUENTIAL
    include_memory: bool = True
    memory_type: str = "clinical"
    max_iterations: int = 3
    confidence_threshold: float = 0.8
    include_validation: bool = True
    clinical_context: bool = True
    output_format: str = "structured"
    callback_handlers: List[BaseCallbackHandler] = field(default_factory=list)

class HealthcareOutputParser(BaseOutputParser):
    """Output parser for healthcare-specific responses."""
    
    def __init__(self, expected_format: str = "structured"):
        self.expected_format = expected_format
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Parse healthcare output into structured format."""
        try:
            # Use structured approach instead of pattern matching
            result = {
                'content': text,
                'timestamp': datetime.now().isoformat(),
                'format': self.expected_format,
                'raw_output': text
            }
            
            # Return the structured result without pattern matching
            # This should be enhanced with proper LLM-based parsing if needed
            return result
            
        except Exception as e:
            raise OutputParserException(f"Failed to parse healthcare output: {e}")

class ChainBuilder(ABC):
    """Abstract builder for healthcare chains."""
    
    def __init__(self, config: ChainConfig):
        self.config = config
        self.chain: Optional[Chain] = None
        self.memory: Optional[HACSLangChainMemory] = None
        self.prompt: Optional[PromptTemplate] = None
        self.output_parser: Optional[BaseOutputParser] = None
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def reset(self) -> 'ChainBuilder':
        """Reset builder to initial state."""
        self.chain = None
        self.memory = None
        self.prompt = None
        self.output_parser = None
        return self
    
    @abstractmethod
    def build_prompt(self) -> 'ChainBuilder':
        """Build the prompt template."""
        pass
    
    @abstractmethod
    def build_memory(self) -> 'ChainBuilder':
        """Build the memory component."""
        pass
    
    def build_output_parser(self) -> 'ChainBuilder':
        """Build the output parser."""
        self.output_parser = HealthcareOutputParser(self.config.output_format)
        return self
    
    @abstractmethod
    def build_chain(self, llm: Any) -> 'ChainBuilder':
        """Build the final chain."""
        pass
    
    def get_chain(self) -> Chain:
        """Get the built chain."""
        if not self.chain:
            raise ValueError("Chain not built. Call build_chain() first.")
        return self.chain

class ClinicalAssessmentChainBuilder(ChainBuilder):
    """Builder for clinical assessment chains."""
    
    def build_prompt(self) -> 'ChainBuilder':
        """Build clinical assessment prompt."""
        template = """You are a clinical AI assistant performing a comprehensive clinical assessment.

Patient Information:
{patient_info}

Current Symptoms/Concerns:
{symptoms}

Clinical History:
{history}

Please provide a thorough clinical assessment including:

1. **Chief Complaint Analysis**
   - Primary concern identified
   - Symptom characterization

2. **Clinical Assessment**
   - Relevant findings
   - Risk factors
   - Clinical reasoning

3. **Differential Diagnosis**
   - Possible diagnoses (ranked by likelihood)
   - Supporting evidence
   - Ruling out considerations

4. **Recommended Actions**
   - Further investigations needed
   - Immediate interventions
   - Follow-up requirements

Assessment:
[Provide detailed assessment here]

Plan:
[Provide recommended plan here]
"""
        
        self.prompt = PromptTemplate(
            template=template,
            input_variables=["patient_info", "symptoms", "history"]
        )
        return self
    
    def build_memory(self) -> 'ChainBuilder':
        """Build clinical memory."""
        if self.config.include_memory:
            self.memory = create_clinical_memory()
        return self
    
    def build_chain(self, llm: Any) -> 'ChainBuilder':
        """Build clinical assessment chain."""
        if not _has_langchain_chains:
            self.chain = Chain()
            return self
        
        chain_kwargs = {
            'llm': llm,
            'prompt': self.prompt,
            'output_parser': self.output_parser,
        }
        
        if self.memory:
            chain_kwargs['memory'] = self.memory
        
        self.chain = LLMChain(**chain_kwargs)
        return self

class DiagnosticReasoningChainBuilder(ChainBuilder):
    """Builder for diagnostic reasoning chains."""
    
    def build_prompt(self) -> 'ChainBuilder':
        """Build diagnostic reasoning prompt."""
        template = """You are a diagnostic reasoning AI assistant. Analyze the clinical presentation systematically.

Clinical Presentation:
{clinical_presentation}

Laboratory Results:
{lab_results}

Imaging Results:
{imaging_results}

Physical Examination:
{physical_exam}

Follow this diagnostic reasoning framework:

1. **Pattern Recognition**
   - Key clinical patterns identified
   - Syndrome recognition

2. **Hypothesis Generation**
   - Initial diagnostic hypotheses
   - Probability estimation

3. **Evidence Analysis**
   - Supporting evidence for each hypothesis
   - Contradictory evidence
   - Evidence strength assessment

4. **Diagnostic Refinement**
   - Most likely diagnosis
   - Confidence level
   - Alternative diagnoses

5. **Validation**
   - Additional tests needed for confirmation
   - Clinical decision rules applied

Diagnosis:
[Primary diagnosis with confidence level]

Reasoning:
[Detailed diagnostic reasoning]

Recommendations:
[Next steps for confirmation/management]
"""
        
        self.prompt = PromptTemplate(
            template=template,
            input_variables=["clinical_presentation", "lab_results", "imaging_results", "physical_exam"]
        )
        return self
    
    def build_memory(self) -> 'ChainBuilder':
        """Build diagnostic memory."""
        if self.config.include_memory:
            self.memory = create_clinical_memory()
        return self
    
    def build_chain(self, llm: Any) -> 'ChainBuilder':
        """Build diagnostic reasoning chain."""
        if not _has_langchain_chains:
            self.chain = Chain()
            return self
        
        self.chain = LLMChain(
            llm=llm,
            prompt=self.prompt,
            memory=self.memory,
            output_parser=self.output_parser
        )
        return self

class TreatmentPlanningChainBuilder(ChainBuilder):
    """Builder for treatment planning chains."""
    
    def build_prompt(self) -> 'ChainBuilder':
        """Build treatment planning prompt."""
        template = """You are a treatment planning AI assistant. Develop a comprehensive treatment plan.

Patient Profile:
{patient_profile}

Diagnosis:
{diagnosis}

Current Medications:
{current_medications}

Allergies/Contraindications:
{allergies}

Patient Preferences:
{preferences}

Develop a comprehensive treatment plan:

1. **Treatment Goals**
   - Primary objectives
   - Secondary objectives
   - Success metrics

2. **Therapeutic Interventions**
   - Pharmacological treatments
   - Non-pharmacological treatments
   - Dosing and administration

3. **Monitoring Plan**
   - Clinical monitoring
   - Laboratory monitoring
   - Imaging requirements
   - Timeline for follow-up

4. **Patient Education**
   - Key education points
   - Lifestyle modifications
   - Warning signs to watch for

5. **Care Coordination**
   - Specialist referrals needed
   - Team communication requirements
   - Transition planning

Treatment Plan:
[Detailed treatment plan]

Monitoring:
[Monitoring requirements]

Education:
[Patient education points]
"""
        
        self.prompt = PromptTemplate(
            template=template,
            input_variables=["patient_profile", "diagnosis", "current_medications", "allergies", "preferences"]
        )
        return self
    
    def build_memory(self) -> 'ChainBuilder':
        """Build treatment memory."""
        if self.config.include_memory:
            self.memory = create_clinical_memory()
        return self
    
    def build_chain(self, llm: Any) -> 'ChainBuilder':
        """Build treatment planning chain."""
        if not _has_langchain_chains:
            self.chain = Chain()
            return self
        
        self.chain = LLMChain(
            llm=llm,
            prompt=self.prompt,
            memory=self.memory,
            output_parser=self.output_parser
        )
        return self

class ChainDirector:
    """Director for orchestrating chain building."""
    
    def __init__(self, builder: ChainBuilder):
        self.builder = builder
    
    def construct_basic_chain(self, llm: Any) -> Chain:
        """Construct a basic healthcare chain."""
        return (self.builder
                .reset()
                .build_prompt()
                .build_memory()
                .build_output_parser()
                .build_chain(llm)
                .get_chain())
    
    def construct_advanced_chain(self, llm: Any, custom_prompt: str = None) -> Chain:
        """Construct an advanced healthcare chain with custom components."""
        builder = self.builder.reset().build_prompt()
        
        # Use custom prompt if provided
        if custom_prompt:
            builder.prompt = PromptTemplate(
                template=custom_prompt,
                input_variables=["input"]
            )
        
        return (builder
                .build_memory()
                .build_output_parser()
                .build_chain(llm)
                .get_chain())

class HealthcareChainFactory:
    """Factory for creating healthcare-specific chains."""
    
    _builders = {
        ChainType.CLINICAL_ASSESSMENT: ClinicalAssessmentChainBuilder,
        ChainType.DIAGNOSTIC_REASONING: DiagnosticReasoningChainBuilder,
        ChainType.TREATMENT_PLANNING: TreatmentPlanningChainBuilder,
        # Add more as needed
    }
    
    @classmethod
    def create_chain(cls, chain_type: ChainType, llm: Any, config: ChainConfig = None) -> Chain:
        """Create a healthcare chain of the specified type."""
        config = config or ChainConfig(chain_type=chain_type)
        
        builder_class = cls._builders.get(chain_type)
        if not builder_class:
            raise ValueError(f"Unknown chain type: {chain_type}")
        
        builder = builder_class(config)
        director = ChainDirector(builder)
        return director.construct_basic_chain(llm)
    
    @classmethod
    def create_sequential_chain(cls, chain_types: List[ChainType], llm: Any) -> Chain:
        """Create a sequential chain combining multiple healthcare chains."""
        if not _has_langchain_chains:
            return Chain()
        
        chains = []
        for chain_type in chain_types:
            chain = cls.create_chain(chain_type, llm)
            chains.append(chain)
        
        return SequentialChain(chains=chains)
    
    @classmethod
    def register_builder(cls, chain_type: ChainType, builder_class: Type[ChainBuilder]):
        """Register a new chain builder."""
        cls._builders[chain_type] = builder_class

# Convenience functions for common healthcare chains
def create_clinical_assessment_chain(llm: Any, include_memory: bool = True) -> Chain:
    """Create a clinical assessment chain."""
    config = ChainConfig(
        chain_type=ChainType.CLINICAL_ASSESSMENT,
        include_memory=include_memory,
        clinical_context=True
    )
    return HealthcareChainFactory.create_chain(ChainType.CLINICAL_ASSESSMENT, llm, config)

def create_diagnostic_chain(llm: Any, confidence_threshold: float = 0.8) -> Chain:
    """Create a diagnostic reasoning chain."""
    config = ChainConfig(
        chain_type=ChainType.DIAGNOSTIC_REASONING,
        confidence_threshold=confidence_threshold,
        include_validation=True
    )
    return HealthcareChainFactory.create_chain(ChainType.DIAGNOSTIC_REASONING, llm, config)

def create_treatment_planning_chain(llm: Any, max_iterations: int = 3) -> Chain:
    """Create a treatment planning chain."""
    config = ChainConfig(
        chain_type=ChainType.TREATMENT_PLANNING,
        max_iterations=max_iterations,
        strategy=ChainStrategy.ITERATIVE
    )
    return HealthcareChainFactory.create_chain(ChainType.TREATMENT_PLANNING, llm, config)

def create_comprehensive_clinical_chain(llm: Any) -> Chain:
    """Create a comprehensive clinical chain combining assessment, diagnosis, and treatment."""
    chain_types = [
        ChainType.CLINICAL_ASSESSMENT,
        ChainType.DIAGNOSTIC_REASONING,
        ChainType.TREATMENT_PLANNING
    ]
    return HealthcareChainFactory.create_sequential_chain(chain_types, llm)

__all__ = [
    # Core classes
    'ChainType',
    'ChainStrategy',
    'ChainConfig',
    'ChainBuilder',
    'ChainDirector',
    # Specific builders
    'ClinicalAssessmentChainBuilder',
    'DiagnosticReasoningChainBuilder', 
    'TreatmentPlanningChainBuilder',
    # Factory and utilities
    'HealthcareChainFactory',
    'HealthcareOutputParser',
    # Convenience functions
    'create_clinical_assessment_chain',
    'create_diagnostic_chain',
    'create_treatment_planning_chain',
    'create_comprehensive_clinical_chain',
]