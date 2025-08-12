"""
Type Adapters for HACS-LangChain Integration

This module provides comprehensive type adapters using the Adapter design pattern
to enable seamless bidirectional conversion between HACS and LangChain types.

World-class design patterns implemented:
    🎯 Adapter Pattern - Type conversion between systems
    🏭 Factory Pattern - Dynamic adapter creation  
    🔗 Strategy Pattern - Multiple conversion strategies
    📋 Validator Pattern - Type safety and validation
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union, TypeVar, Generic
from dataclasses import dataclass

try:
    from pydantic import BaseModel, Field, ValidationError, create_model
    _has_pydantic = True
except ImportError:
    _has_pydantic = False
    BaseModel = object
    Field = lambda *args, **kwargs: None
    ValidationError = Exception
    create_model = lambda *args, **kwargs: None

try:
    from langchain.schema import Document, BaseMessage, HumanMessage, AIMessage, SystemMessage
    from langchain_core.documents import Document as CoreDocument
    _has_langchain = True
except ImportError:
    _has_langchain = False
    # Fallback classes
    class Document:
        def __init__(self, page_content: str, metadata: Dict = None):
            self.page_content = page_content
            self.metadata = metadata or {}
    
    class BaseMessage:
        def __init__(self, content: str):
            self.content = content
    
    HumanMessage = AIMessage = SystemMessage = BaseMessage
    CoreDocument = Document

try:
    from hacs_core.base_resource import BaseResource
    from hacs_core.models import (
        Patient, Observation, Encounter, Condition, Memory, Document as HACSDocument,
        AgentMessage, MessageRole, MessageType
    )
    _has_hacs = True
except ImportError:
    _has_hacs = False
    BaseResource = object
    Patient = Observation = Encounter = Condition = Memory = HACSDocument = object
    AgentMessage = MessageRole = MessageType = object

logger = logging.getLogger(__name__)

# Generic type variables for adapter pattern
T = TypeVar('T')
U = TypeVar('U')

class ConversionStrategy(Enum):
    """Strategy enumeration for different conversion approaches."""
    STRICT = "strict"          # Exact type matching required
    FLEXIBLE = "flexible"      # Allow type coercion
    FUZZY = "fuzzy"           # Best-effort conversion
    METADATA_RICH = "metadata_rich"  # Preserve all metadata

@dataclass
class ConversionContext:
    """Context for type conversion operations."""
    strategy: ConversionStrategy = ConversionStrategy.FLEXIBLE
    preserve_metadata: bool = True
    validate_output: bool = True
    conversion_timestamp: Optional[datetime] = None
    source_system: str = "unknown"
    target_system: str = "unknown"

class ConversionError(Exception):
    """Exception raised when type conversion fails."""
    
    def __init__(self, message: str, source_type: Type, target_type: Type, context: ConversionContext = None):
        self.source_type = source_type
        self.target_type = target_type
        self.context = context
        super().__init__(f"Conversion error from {source_type} to {target_type}: {message}")

class TypeAdapter(ABC, Generic[T, U]):
    """Abstract base adapter for type conversions."""
    
    def __init__(self, context: ConversionContext = None):
        self.context = context or ConversionContext()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def can_convert(self, source: Any) -> bool:
        """Check if the adapter can convert the given source type."""
        pass
    
    @abstractmethod
    def convert(self, source: T) -> U:
        """Convert source type to target type."""
        pass
    
    @abstractmethod
    def reverse_convert(self, target: U) -> T:
        """Convert target type back to source type."""
        pass
    
    def validate_conversion(self, source: T, result: U) -> bool:
        """Validate that conversion was successful."""
        return result is not None

class HACSToLangChainDocumentAdapter(TypeAdapter[BaseResource, Document]):
    """Adapter to convert HACS resources to LangChain documents."""
    
    def can_convert(self, source: Any) -> bool:
        """Check if source is a HACS resource."""
        if not _has_hacs:
            return False
        return isinstance(source, BaseResource)
    
    def convert(self, source: BaseResource) -> Document:
        """Convert HACS resource to LangChain document."""
        if not self.can_convert(source):
            raise ConversionError("Source is not a HACS BaseResource", type(source), Document, self.context)
        
        try:
            # Use structured serialization instead of field-by-field extraction
            if hasattr(source, 'model_dump'):
                source_data = source.model_dump()
            elif hasattr(source, 'dict'):
                source_data = source.dict()
            else:
                source_data = {"content": str(source)}
            
            # Create structured content using JSON representation
            page_content = str(source_data)
            
            # Create comprehensive metadata
            metadata = {
                "source": "hacs",
                "resource_type": getattr(source, 'resource_type', 'unknown'),
                "resource_id": getattr(source, 'id', 'unknown'),
                "conversion_strategy": self.context.strategy.value,
                "converted_at": datetime.now().isoformat()
            }
            
            # Preserve all metadata if requested
            if self.context.preserve_metadata:
                metadata.update(source_data)
            
            return Document(page_content=page_content, metadata=metadata)
            
        except Exception as e:
            raise ConversionError(f"Failed to convert HACS resource: {e}", type(source), Document, self.context)
    
    def reverse_convert(self, target: Document) -> BaseResource:
        """Convert LangChain document back to HACS resource."""
        if not _has_hacs:
            raise ConversionError("HACS not available", Document, BaseResource, self.context)
        
        metadata = target.metadata
        resource_type = metadata.get('resource_type', 'BaseResource')
        
        # Try to reconstruct the original resource
        try:
            # Basic resource data
            resource_data = {
                'id': metadata.get('resource_id', 'converted-resource'),
                'resource_type': resource_type,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            # Add back original fields if available
            if self.context.preserve_metadata:
                for key, value in metadata.items():
                    if key not in ['source', 'conversion_strategy', 'converted_at']:
                        resource_data[key] = value
            
            # Create appropriate resource type
            if resource_type == 'Patient' and _has_hacs:
                return Patient(**resource_data)
            elif resource_type == 'Observation' and _has_hacs:
                return Observation(**resource_data)
            else:
                # Fallback to BaseResource
                return BaseResource(**resource_data)
                
        except Exception as e:
            raise ConversionError(f"Failed to reconstruct HACS resource: {e}", Document, BaseResource, self.context)

class HACSToLangChainMessageAdapter(TypeAdapter[AgentMessage, BaseMessage]):
    """Adapter to convert HACS AgentMessage to LangChain messages."""
    
    def can_convert(self, source: Any) -> bool:
        """Check if source is a HACS AgentMessage."""
        if not _has_hacs:
            return False
        return isinstance(source, AgentMessage)
    
    def convert(self, source: AgentMessage) -> BaseMessage:
        """Convert HACS AgentMessage to LangChain message."""
        if not self.can_convert(source):
            raise ConversionError("Source is not a HACS AgentMessage", type(source), BaseMessage, self.context)
        
        try:
            # Map HACS message roles to LangChain message types
            role_mapping = {
                MessageRole.USER: HumanMessage,
                MessageRole.ASSISTANT: AIMessage,
                MessageRole.SYSTEM: SystemMessage,
            }
            
            message_class = role_mapping.get(source.role, HumanMessage)
            content = source.content or ""
            
            # Create the appropriate message type
            if _has_langchain:
                return message_class(content=content)
            else:
                return BaseMessage(content=content)
                
        except Exception as e:
            raise ConversionError(f"Failed to convert HACS message: {e}", type(source), BaseMessage, self.context)
    
    def reverse_convert(self, target: BaseMessage) -> AgentMessage:
        """Convert LangChain message back to HACS AgentMessage."""
        if not _has_hacs:
            raise ConversionError("HACS not available", BaseMessage, AgentMessage, self.context)
        
        try:
            # Map LangChain message types to HACS roles
            if isinstance(target, HumanMessage):
                role = MessageRole.USER
            elif isinstance(target, AIMessage):
                role = MessageRole.ASSISTANT
            elif isinstance(target, SystemMessage):
                role = MessageRole.SYSTEM
            else:
                role = MessageRole.USER  # Default
            
            return AgentMessage(
                role=role,
                content=target.content,
                message_type=MessageType.CLINICAL,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            raise ConversionError(f"Failed to reconstruct HACS message: {e}", BaseMessage, AgentMessage, self.context)

class AdapterFactory:
    """Factory for creating type adapters."""
    
    _adapters = {
        (BaseResource, Document): HACSToLangChainDocumentAdapter,
        (AgentMessage, BaseMessage): HACSToLangChainMessageAdapter,
    }
    
    @classmethod
    def create_adapter(cls, source_type: Type[T], target_type: Type[U], 
                      context: ConversionContext = None) -> TypeAdapter[T, U]:
        """Create an appropriate adapter for the given type pair."""
        adapter_class = cls._adapters.get((source_type, target_type))
        
        if not adapter_class:
            # Try to find a compatible adapter
            for (src, tgt), adapter_cls in cls._adapters.items():
                if issubclass(source_type, src) and issubclass(target_type, tgt):
                    adapter_class = adapter_cls
                    break
        
        if not adapter_class:
            raise ValueError(f"No adapter available for {source_type} -> {target_type}")
        
        return adapter_class(context or ConversionContext())
    
    @classmethod
    def register_adapter(cls, source_type: Type[T], target_type: Type[U], 
                        adapter_class: Type[TypeAdapter[T, U]]):
        """Register a new adapter for a type pair."""
        cls._adapters[(source_type, target_type)] = adapter_class

class BidirectionalConverter:
    """High-level converter that handles bidirectional type conversion."""
    
    def __init__(self, context: ConversionContext = None):
        self.context = context or ConversionContext()
        self.logger = logging.getLogger(f"{__name__.BidirectionalConverter}")
    
    def convert(self, source: Any, target_type: Type[U]) -> U:
        """Convert source to target type using appropriate adapter."""
        source_type = type(source)
        
        try:
            adapter = AdapterFactory.create_adapter(source_type, target_type, self.context)
            result = adapter.convert(source)
            
            if self.context.validate_output and not adapter.validate_conversion(source, result):
                raise ConversionError("Conversion validation failed", source_type, target_type, self.context)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Conversion failed: {e}")
            raise
    
    def convert_batch(self, sources: List[Any], target_type: Type[U]) -> List[U]:
        """Convert a batch of sources to target type."""
        results = []
        for source in sources:
            try:
                result = self.convert(source, target_type)
                results.append(result)
            except ConversionError as e:
                self.logger.warning(f"Failed to convert item: {e}")
                if self.context.strategy == ConversionStrategy.STRICT:
                    raise
                # Skip failed conversions in flexible mode
        return results

# Convenience functions for common conversions
def hacs_to_documents(resources: List[BaseResource], 
                     context: ConversionContext = None) -> List[Document]:
    """Convert HACS resources to LangChain documents."""
    converter = BidirectionalConverter(context)
    return converter.convert_batch(resources, Document)

def documents_to_hacs(documents: List[Document], 
                     context: ConversionContext = None) -> List[BaseResource]:
    """Convert LangChain documents to HACS resources."""
    converter = BidirectionalConverter(context)
    return converter.convert_batch(documents, BaseResource)

def hacs_messages_to_langchain(messages: List[AgentMessage], 
                              context: ConversionContext = None) -> List[BaseMessage]:
    """Convert HACS messages to LangChain messages."""
    converter = BidirectionalConverter(context)
    return converter.convert_batch(messages, BaseMessage)

def langchain_messages_to_hacs(messages: List[BaseMessage], 
                              context: ConversionContext = None) -> List[AgentMessage]:
    """Convert LangChain messages to HACS messages."""
    converter = BidirectionalConverter(context)
    return converter.convert_batch(messages, AgentMessage)

__all__ = [
    # Core classes
    'TypeAdapter',
    'ConversionStrategy', 
    'ConversionContext',
    'ConversionError',
    'BidirectionalConverter',
    # Specific adapters
    'HACSToLangChainDocumentAdapter',
    'HACSToLangChainMessageAdapter',
    # Factory
    'AdapterFactory',
    # Convenience functions
    'hacs_to_documents',
    'documents_to_hacs', 
    'hacs_messages_to_langchain',
    'langchain_messages_to_hacs',
]