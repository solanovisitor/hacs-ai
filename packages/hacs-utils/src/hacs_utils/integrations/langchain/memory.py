"""
Memory Integration for HACS-LangChain

This module provides comprehensive memory integration using world-class design patterns
to connect HACS memory systems with LangChain memory patterns.

Design patterns implemented:
    🧠 Strategy Pattern - Multiple memory strategies
    🏭 Factory Pattern - Memory creation and management
    🔗 Bridge Pattern - Bridge between HACS and LangChain memory
    📋 Observer Pattern - Memory update notifications
    🎯 Adapter Pattern - Memory format conversion
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field

try:
    from langchain.memory import BaseMemory, ConversationBufferMemory, ConversationSummaryMemory
    from langchain.memory.chat_memory import BaseChatMemory
    from langchain.schema import BaseMessage, HumanMessage, AIMessage
    _has_langchain_memory = True
except ImportError:
    _has_langchain_memory = False
    # Fallback classes
    class BaseMemory:
        def __init__(self):
            self.memory_variables = []
        
        def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
            return {}
        
        def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
            pass
    
    class BaseChatMemory(BaseMemory):
        def __init__(self):
            super().__init__()
            self.chat_memory = []
    
    ConversationBufferMemory = ConversationSummaryMemory = BaseChatMemory
    BaseMessage = HumanMessage = AIMessage = object

try:
    from hacs_core.models import Memory, MemoryType, AgentMessage, MessageRole
    from hacs_core.memory import EpisodicMemory, ProceduralMemory, ExecutiveMemory
    _has_hacs_memory = True
except ImportError:
    _has_hacs_memory = False
    Memory = MemoryType = AgentMessage = MessageRole = object
    EpisodicMemory = ProceduralMemory = ExecutiveMemory = object

from .adapters import hacs_messages_to_langchain, langchain_messages_to_hacs, ConversionContext

logger = logging.getLogger(__name__)

class MemoryStrategy(Enum):
    """Strategy enumeration for different memory approaches."""
    EPISODIC = "episodic"           # Event-based memory storage
    PROCEDURAL = "procedural"       # Process and skill memory
    EXECUTIVE = "executive"         # High-level decision memory
    HYBRID = "hybrid"              # Combined memory approach
    CONVERSATIONAL = "conversational"  # Chat-focused memory
    CLINICAL = "clinical"          # Healthcare-specific memory

@dataclass
class MemoryConfig:
    """Configuration for memory integration."""
    strategy: MemoryStrategy = MemoryStrategy.HYBRID
    max_memories: int = 1000
    retention_days: int = 30
    auto_summarize: bool = True
    include_metadata: bool = True
    clinical_context: bool = True
    conversation_window: int = 50
    summary_threshold: int = 100

class MemoryObserver(ABC):
    """Observer interface for memory updates."""
    
    @abstractmethod
    def on_memory_added(self, memory: Any) -> None:
        """Called when a memory is added."""
        pass
    
    @abstractmethod
    def on_memory_updated(self, memory: Any) -> None:
        """Called when a memory is updated."""
        pass
    
    @abstractmethod
    def on_memory_deleted(self, memory_id: str) -> None:
        """Called when a memory is deleted."""
        pass

class HACSMemoryStrategy(ABC):
    """Abstract strategy for HACS memory integration."""
    
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.observers: List[MemoryObserver] = []
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def add_observer(self, observer: MemoryObserver) -> None:
        """Add a memory observer."""
        self.observers.append(observer)
    
    def remove_observer(self, observer: MemoryObserver) -> None:
        """Remove a memory observer."""
        if observer in self.observers:
            self.observers.remove(observer)
    
    def notify_memory_added(self, memory: Any) -> None:
        """Notify observers of memory addition."""
        for observer in self.observers:
            try:
                observer.on_memory_added(memory)
            except Exception as e:
                self.logger.warning(f"Observer notification failed: {e}")
    
    @abstractmethod
    def store_memory(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """Store a memory and return its ID."""
        pass
    
    @abstractmethod
    def retrieve_memories(self, query: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve memories based on query."""
        pass
    
    @abstractmethod
    def get_conversation_history(self, limit: int = None) -> List[BaseMessage]:
        """Get conversation history as LangChain messages."""
        pass

class EpisodicMemoryStrategy(HACSMemoryStrategy):
    """Episodic memory strategy for event-based storage."""
    
    def __init__(self, config: MemoryConfig):
        super().__init__(config)
        self.memories: List[Dict[str, Any]] = []
        self.conversation_history: List[Dict[str, Any]] = []
    
    def store_memory(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """Store an episodic memory."""
        memory_id = f"episodic-{datetime.now().isoformat()}-{len(self.memories)}"
        
        memory = {
            'id': memory_id,
            'type': 'episodic',
            'content': content,
            'timestamp': datetime.now(),
            'metadata': metadata or {},
            'importance': metadata.get('importance', 0.5) if metadata else 0.5,
            'clinical_context': metadata.get('clinical_context') if metadata else None
        }
        
        self.memories.append(memory)
        self.notify_memory_added(memory)
        
        # Auto-cleanup old memories
        if len(self.memories) > self.config.max_memories:
            self._cleanup_old_memories()
        
        return memory_id
    
    def retrieve_memories(self, query: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve episodic memories."""
        # Simple retrieval - in practice would use semantic search
        if query:
            # Filter memories containing query terms
            filtered = [m for m in self.memories if query.lower() in m['content'].lower()]
        else:
            filtered = self.memories
        
        # Sort by importance and recency
        filtered.sort(key=lambda x: (x['importance'], x['timestamp']), reverse=True)
        return filtered[:limit]
    
    def get_conversation_history(self, limit: int = None) -> List[BaseMessage]:
        """Get conversation history as LangChain messages."""
        limit = limit or self.config.conversation_window
        recent_conversations = self.conversation_history[-limit:]
        
        messages = []
        for conv in recent_conversations:
            if conv['role'] == 'user':
                messages.append(HumanMessage(content=conv['content']))
            elif conv['role'] == 'assistant':
                messages.append(AIMessage(content=conv['content']))
        
        return messages
    
    def add_conversation_turn(self, human_input: str, ai_response: str, metadata: Dict[str, Any] = None):
        """Add a conversation turn to history."""
        timestamp = datetime.now()
        
        # Add human message
        self.conversation_history.append({
            'role': 'user',
            'content': human_input,
            'timestamp': timestamp,
            'metadata': metadata or {}
        })
        
        # Add AI response
        self.conversation_history.append({
            'role': 'assistant', 
            'content': ai_response,
            'timestamp': timestamp,
            'metadata': metadata or {}
        })
        
        # Store as episodic memory if important
        if metadata and metadata.get('store_as_memory', True):
            memory_content = f"Conversation - User: {human_input}\nAssistant: {ai_response}"
            self.store_memory(memory_content, {
                'type': 'conversation',
                'importance': metadata.get('importance', 0.3),
                **metadata
            })
    
    def _cleanup_old_memories(self) -> None:
        """Clean up old memories based on retention policy."""
        cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
        
        # Keep important memories longer
        self.memories = [
            m for m in self.memories 
            if m['timestamp'] > cutoff_date or m['importance'] > 0.8
        ]

class ClinicalMemoryStrategy(HACSMemoryStrategy):
    """Clinical memory strategy for healthcare-specific memory."""
    
    def __init__(self, config: MemoryConfig):
        super().__init__(config)
        self.clinical_memories: Dict[str, List[Dict[str, Any]]] = {
            'patient_encounters': [],
            'clinical_decisions': [],
            'diagnostic_reasoning': [],
            'treatment_plans': [],
            'medication_history': [],
            'adverse_events': []
        }
    
    def store_memory(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """Store clinical memory with explicit categorization."""
        memory_id = f"clinical-{datetime.now().isoformat()}-{hash(content) % 10000}"
        
        # Use explicit category from metadata or default to patient_encounters
        category = metadata.get('category', 'patient_encounters') if metadata else 'patient_encounters'
        
        # Ensure category exists in our structure
        if category not in self.clinical_memories:
            category = 'patient_encounters'
        
        memory = {
            'id': memory_id,
            'type': 'clinical',
            'category': category,
            'content': content,
            'timestamp': datetime.now(),
            'metadata': metadata or {},
            'patient_id': metadata.get('patient_id') if metadata else None,
            'encounter_id': metadata.get('encounter_id') if metadata else None,
            'importance': metadata.get('importance', 0.7) if metadata else 0.7,
            'clinical_context': metadata.get('clinical_context', {}) if metadata else {}
        }
        
        self.clinical_memories[category].append(memory)
        self.notify_memory_added(memory)
        
        return memory_id
    
    def retrieve_memories(self, query: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve clinical memories with structured search."""
        all_memories = []
        for category, memories in self.clinical_memories.items():
            all_memories.extend(memories)
        
        if query:
            # Use structured search instead of keyword matching
            # This could be enhanced with semantic search or vector similarity
            filtered = [
                memory for memory in all_memories 
                if query in memory['content'] or 
                   query in str(memory.get('metadata', {})) or
                   query == memory['category']
            ]
        else:
            filtered = all_memories
        
        # Sort by clinical importance and recency
        filtered.sort(key=lambda x: (x['importance'], x['timestamp']), reverse=True)
        return filtered[:limit]
    
    def get_conversation_history(self, limit: int = None) -> List[BaseMessage]:
        """Get clinical conversation history."""
        # For clinical context, focus on recent clinical decisions and patient interactions
        clinical_conversations = []
        
        for category in ['patient_encounters', 'clinical_decisions', 'diagnostic_reasoning']:
            for memory in self.clinical_memories[category]:
                if 'conversation' in memory.get('metadata', {}):
                    clinical_conversations.append(memory)
        
        # Sort by timestamp and convert to messages
        clinical_conversations.sort(key=lambda x: x['timestamp'], reverse=True)
        limit = limit or self.config.conversation_window
        
        messages = []
        for memory in clinical_conversations[:limit]:
            # Create contextual message
            content = f"[{memory['category'].title()}] {memory['content']}"
            messages.append(AIMessage(content=content))
        
        return messages
    


class HACSLangChainMemory(BaseChatMemory):
    """LangChain memory implementation using HACS memory backend."""
    
    def __init__(self, strategy: HACSMemoryStrategy, memory_key: str = "history", 
                 return_messages: bool = True):
        super().__init__()
        self.strategy = strategy
        self.memory_key = memory_key
        self.return_messages = return_messages
        self.memory_variables = [memory_key]
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load memory variables for LangChain."""
        if self.return_messages:
            history = self.strategy.get_conversation_history()
        else:
            # Convert to string format
            messages = self.strategy.get_conversation_history()
            history = "\n".join([f"{m.__class__.__name__}: {m.content}" for m in messages])
        
        return {self.memory_key: history}
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Save context to HACS memory."""
        # Extract human input and AI output
        human_input = inputs.get('input', str(inputs))
        ai_output = outputs.get('output', str(outputs))
        
        # Add to strategy if it supports conversation tracking
        if hasattr(self.strategy, 'add_conversation_turn'):
            self.strategy.add_conversation_turn(human_input, ai_output, {
                'timestamp': datetime.now(),
                'importance': 0.5,
                'clinical_context': inputs.get('clinical_context')
            })
        else:
            # Store as regular memory
            self.strategy.store_memory(
                f"Input: {human_input}\nOutput: {ai_output}",
                {'type': 'conversation', 'importance': 0.5}
            )

class MemoryFactory:
    """Factory for creating memory strategies and integrations."""
    
    @staticmethod
    def create_strategy(strategy_type: MemoryStrategy, config: MemoryConfig = None) -> HACSMemoryStrategy:
        """Create a memory strategy of the specified type."""
        config = config or MemoryConfig()
        
        strategy_map = {
            MemoryStrategy.EPISODIC: EpisodicMemoryStrategy,
            MemoryStrategy.CLINICAL: ClinicalMemoryStrategy,
            # Add more strategies as needed
        }
        
        strategy_class = strategy_map.get(strategy_type)
        if not strategy_class:
            raise ValueError(f"Unknown memory strategy: {strategy_type}")
        
        return strategy_class(config)
    
    @staticmethod
    def create_langchain_memory(strategy_type: MemoryStrategy, 
                               config: MemoryConfig = None,
                               memory_key: str = "history") -> HACSLangChainMemory:
        """Create a LangChain-compatible memory using HACS backend."""
        strategy = MemoryFactory.create_strategy(strategy_type, config)
        return HACSLangChainMemory(strategy, memory_key)
    
    @staticmethod
    def create_hybrid_memory(config: MemoryConfig = None) -> HACSMemoryStrategy:
        """Create a hybrid memory strategy combining multiple approaches."""
        config = config or MemoryConfig(strategy=MemoryStrategy.HYBRID)
        
        # Create composite strategy (simplified for now)
        if config.clinical_context:
            return ClinicalMemoryStrategy(config)
        else:
            return EpisodicMemoryStrategy(config)

# Convenience functions
def create_clinical_memory(max_memories: int = 1000, retention_days: int = 30) -> HACSLangChainMemory:
    """Create a clinical memory for healthcare applications."""
    config = MemoryConfig(
        strategy=MemoryStrategy.CLINICAL,
        max_memories=max_memories,
        retention_days=retention_days,
        clinical_context=True
    )
    return MemoryFactory.create_langchain_memory(MemoryStrategy.CLINICAL, config)

def create_episodic_memory(conversation_window: int = 50) -> HACSLangChainMemory:
    """Create an episodic memory for general conversations."""
    config = MemoryConfig(
        strategy=MemoryStrategy.EPISODIC,
        conversation_window=conversation_window
    )
    return MemoryFactory.create_langchain_memory(MemoryStrategy.EPISODIC, config)

__all__ = [
    # Core classes
    'MemoryStrategy',
    'MemoryConfig', 
    'MemoryObserver',
    'HACSMemoryStrategy',
    # Specific strategies
    'EpisodicMemoryStrategy',
    'ClinicalMemoryStrategy',
    # LangChain integration
    'HACSLangChainMemory',
    # Factory
    'MemoryFactory',
    # Convenience functions
    'create_clinical_memory',
    'create_episodic_memory',
]