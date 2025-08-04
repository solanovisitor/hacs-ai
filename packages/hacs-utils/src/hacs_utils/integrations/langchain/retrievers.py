"""
Healthcare Retrievers for HACS-LangChain Integration

This module provides specialized retrievers for healthcare workflows using
world-class design patterns to create context-aware document retrieval.

Design patterns implemented:
    🎯 Strategy Pattern - Multiple retrieval strategies
    🏭 Factory Pattern - Retriever creation and management
    🔗 Chain of Responsibility - Multi-stage retrieval
    📋 Template Method Pattern - Common retrieval structure
    🔍 Observer Pattern - Retrieval monitoring
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field

try:
    from langchain.schema import BaseRetriever, Document
    from langchain.callbacks.manager import CallbackManagerForRetrieverRun
    _has_langchain_retrievers = True
except ImportError:
    _has_langchain_retrievers = False
    # Fallback classes
    class Document:
        def __init__(self, page_content: str, metadata: Dict = None):
            self.page_content = page_content
            self.metadata = metadata or {}
    
    class BaseRetriever:
        def get_relevant_documents(self, query: str) -> List[Document]:
            return []
    
    class CallbackManagerForRetrieverRun:
        pass

try:
    from hacs_core.models import Patient, Observation, Condition, Encounter
    from hacs_core.base_resource import BaseResource
    _has_hacs = True
except ImportError:
    _has_hacs = False
    Patient = Observation = Condition = Encounter = BaseResource = object

from .vector_stores import HACSVectorStore, VectorStoreConfig, create_clinical_vector_store
from .memory import HACSMemoryStrategy, create_clinical_memory

logger = logging.getLogger(__name__)

class RetrievalStrategy(Enum):
    """Strategy enumeration for different retrieval approaches."""
    SEMANTIC = "semantic"                    # Vector similarity retrieval
    TEMPORAL = "temporal"                   # Time-based retrieval
    PATIENT_SPECIFIC = "patient_specific"   # Patient-focused retrieval
    ENCOUNTER_BASED = "encounter_based"     # Encounter-focused retrieval
    MULTI_MODAL = "multi_modal"            # Combined retrieval approaches
    CLINICAL_CONTEXT = "clinical_context"   # Clinical relevance-based

@dataclass
class RetrievalConfig:
    """Configuration for healthcare retrievers."""
    strategy: RetrievalStrategy = RetrievalStrategy.SEMANTIC
    max_results: int = 10
    similarity_threshold: float = 0.7
    include_metadata: bool = True
    patient_context: bool = True
    temporal_window_days: int = 30
    prioritize_recent: bool = True
    include_related_resources: bool = True
    clinical_relevance_scoring: bool = True

class ClinicalContext:
    """Clinical context for retrieval operations."""
    
    def __init__(self, patient_id: str = None, encounter_id: str = None, 
                 clinical_domain: str = None, specialty: str = None):
        self.patient_id = patient_id
        self.encounter_id = encounter_id
        self.clinical_domain = clinical_domain  # e.g., "cardiology", "oncology"
        self.specialty = specialty
        self.timestamp = datetime.now()
        self.context_metadata = {}
    
    def add_context(self, key: str, value: Any) -> None:
        """Add additional context metadata."""
        self.context_metadata[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'patient_id': self.patient_id,
            'encounter_id': self.encounter_id,
            'clinical_domain': self.clinical_domain,
            'specialty': self.specialty,
            'timestamp': self.timestamp.isoformat(),
            'context_metadata': self.context_metadata
        }

class HACSRetriever(BaseRetriever):
    """Base HACS retriever with clinical context awareness."""
    
    def __init__(self, config: RetrievalConfig, vector_store: HACSVectorStore = None):
        super().__init__()
        self.config = config
        self.vector_store = vector_store or create_clinical_vector_store()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    def get_relevant_documents(self, query: str, 
                             run_manager: CallbackManagerForRetrieverRun = None) -> List[Document]:
        """Get relevant documents based on strategy."""
        try:
            return self._retrieve_documents(query)
        except Exception as e:
            self.logger.error(f"Retrieval failed: {e}")
            return []
    
    @abstractmethod
    def _retrieve_documents(self, query: str) -> List[Document]:
        """Internal document retrieval implementation."""
        pass
    
    def enhance_with_clinical_context(self, documents: List[Document], 
                                    context: ClinicalContext = None) -> List[Document]:
        """Enhance documents with clinical context."""
        if not context:
            return documents
        
        enhanced_docs = []
        for doc in documents:
            # Create enhanced document with clinical context
            enhanced_metadata = doc.metadata.copy()
            enhanced_metadata.update({
                'clinical_context': context.to_dict(),
                'retrieved_at': datetime.now().isoformat(),
                'retrieval_strategy': self.config.strategy.value
            })
            
            enhanced_doc = Document(
                page_content=doc.page_content,
                metadata=enhanced_metadata
            )
            enhanced_docs.append(enhanced_doc)
        
        return enhanced_docs

class SemanticRetriever(HACSRetriever):
    """Semantic similarity-based retriever."""
    
    def _retrieve_documents(self, query: str) -> List[Document]:
        """Retrieve documents using semantic similarity."""
        # Use vector store for semantic search
        results = self.vector_store.search_similar_resources(
            query, 
            k=self.config.max_results
        )
        
        # Convert results to Documents
        documents = []
        for result in results:
            doc = Document(
                page_content=result['content'],
                metadata=result['metadata']
            )
            documents.append(doc)
        
        return documents

class PatientSpecificRetriever(HACSRetriever):
    """Patient-specific document retriever."""
    
    def __init__(self, config: RetrievalConfig, vector_store: HACSVectorStore = None,
                 patient_id: str = None):
        super().__init__(config, vector_store)
        self.patient_id = patient_id
    
    def _retrieve_documents(self, query: str) -> List[Document]:
        """Retrieve patient-specific documents."""
        if not self.patient_id:
            # Fallback to semantic search if no patient context
            return SemanticRetriever(self.config, self.vector_store)._retrieve_documents(query)
        
        # Enhance query with patient context
        patient_query = f"patient_id:{self.patient_id} {query}"
        
        # Get initial results
        results = self.vector_store.search_similar_resources(
            patient_query,
            k=self.config.max_results * 2  # Get more to filter
        )
        
        # Filter for patient-specific results
        patient_results = [
            result for result in results
            if result.get('metadata', {}).get('patient_id') == self.patient_id
        ]
        
        # If not enough patient-specific results, include related ones
        if len(patient_results) < self.config.max_results:
            general_results = [
                result for result in results
                if result not in patient_results
            ]
            patient_results.extend(general_results[:self.config.max_results - len(patient_results)])
        
        # Convert to Documents
        documents = []
        for result in patient_results[:self.config.max_results]:
            doc = Document(
                page_content=result['content'],
                metadata=result['metadata']
            )
            documents.append(doc)
        
        return documents

class TemporalRetriever(HACSRetriever):
    """Time-based document retriever."""
    
    def _retrieve_documents(self, query: str) -> List[Document]:
        """Retrieve documents with temporal relevance."""
        # Get semantic results first
        semantic_results = self.vector_store.search_similar_resources(
            query,
            k=self.config.max_results * 3  # Get more for temporal filtering
        )
        
        # Apply temporal filtering
        cutoff_date = datetime.now() - timedelta(days=self.config.temporal_window_days)
        
        temporal_results = []
        for result in semantic_results:
            metadata = result.get('metadata', {})
            
            # Check for various timestamp fields
            timestamp_fields = ['created_at', 'updated_at', 'indexed_at', 'timestamp']
            result_date = None
            
            for field in timestamp_fields:
                if field in metadata:
                    try:
                        result_date = datetime.fromisoformat(metadata[field].replace('Z', '+00:00'))
                        break
                    except (ValueError, AttributeError):
                        continue
            
            # Include if within temporal window or no date available
            if not result_date or result_date >= cutoff_date:
                temporal_results.append(result)
        
        # Sort by recency if prioritized
        if self.config.prioritize_recent:
            temporal_results.sort(
                key=lambda x: x.get('metadata', {}).get('created_at', ''),
                reverse=True
            )
        
        # Convert to Documents
        documents = []
        for result in temporal_results[:self.config.max_results]:
            doc = Document(
                page_content=result['content'],
                metadata=result['metadata']
            )
            documents.append(doc)
        
        return documents

class MultiModalRetriever(HACSRetriever):
    """Multi-modal retriever combining multiple strategies."""
    
    def __init__(self, config: RetrievalConfig, vector_store: HACSVectorStore = None,
                 strategies: List[RetrievalStrategy] = None):
        super().__init__(config, vector_store)
        self.strategies = strategies or [
            RetrievalStrategy.SEMANTIC,
            RetrievalStrategy.TEMPORAL,
            RetrievalStrategy.PATIENT_SPECIFIC
        ]
        self.retrievers = self._initialize_retrievers()
    
    def _initialize_retrievers(self) -> Dict[RetrievalStrategy, HACSRetriever]:
        """Initialize sub-retrievers for each strategy."""
        retrievers = {}
        
        for strategy in self.strategies:
            if strategy == RetrievalStrategy.SEMANTIC:
                retrievers[strategy] = SemanticRetriever(self.config, self.vector_store)
            elif strategy == RetrievalStrategy.TEMPORAL:
                retrievers[strategy] = TemporalRetriever(self.config, self.vector_store)
            elif strategy == RetrievalStrategy.PATIENT_SPECIFIC:
                retrievers[strategy] = PatientSpecificRetriever(self.config, self.vector_store)
        
        return retrievers
    
    def _retrieve_documents(self, query: str) -> List[Document]:
        """Retrieve documents using multiple strategies."""
        all_documents = []
        document_ids = set()  # Track document IDs to avoid duplicates
        
        # Get results from each strategy
        for strategy, retriever in self.retrievers.items():
            try:
                strategy_docs = retriever._retrieve_documents(query)
                
                # Add unique documents
                for doc in strategy_docs:
                    doc_id = doc.metadata.get('resource_id', hash(doc.page_content))
                    if doc_id not in document_ids:
                        # Add strategy information to metadata
                        doc.metadata['retrieval_strategy'] = strategy.value
                        all_documents.append(doc)
                        document_ids.add(doc_id)
                        
            except Exception as e:
                self.logger.warning(f"Strategy {strategy} failed: {e}")
        
        # Score and rank combined results
        scored_documents = self._score_documents(all_documents, query)
        
        # Return top results
        return scored_documents[:self.config.max_results]
    
    def _score_documents(self, documents: List[Document], query: str) -> List[Document]:
        """Score and rank documents based on multiple factors."""
        # Simple scoring - could be enhanced with proper relevance scoring
        for i, doc in enumerate(documents):
            score = 1.0 / (i + 1)  # Position-based scoring
            
            # Boost recent documents if prioritized
            if self.config.prioritize_recent:
                created_at = doc.metadata.get('created_at')
                if created_at:
                    try:
                        doc_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        days_old = (datetime.now() - doc_date).days
                        recency_boost = max(0, 1 - days_old / 365)  # Boost within a year
                        score *= (1 + recency_boost)
                    except (ValueError, AttributeError):
                        pass
            
            doc.metadata['relevance_score'] = score
        
        # Sort by score
        documents.sort(key=lambda x: x.metadata.get('relevance_score', 0), reverse=True)
        return documents

class RetrieverFactory:
    """Factory for creating healthcare retrievers."""
    
    @staticmethod
    def create_retriever(strategy: RetrievalStrategy, config: RetrievalConfig = None,
                        vector_store: HACSVectorStore = None, **kwargs) -> HACSRetriever:
        """Create a retriever of the specified strategy."""
        config = config or RetrievalConfig(strategy=strategy)
        vector_store = vector_store or create_clinical_vector_store()
        
        if strategy == RetrievalStrategy.SEMANTIC:
            return SemanticRetriever(config, vector_store)
        elif strategy == RetrievalStrategy.PATIENT_SPECIFIC:
            return PatientSpecificRetriever(config, vector_store, 
                                          patient_id=kwargs.get('patient_id'))
        elif strategy == RetrievalStrategy.TEMPORAL:
            return TemporalRetriever(config, vector_store)
        elif strategy == RetrievalStrategy.MULTI_MODAL:
            return MultiModalRetriever(config, vector_store,
                                     strategies=kwargs.get('strategies'))
        else:
            raise ValueError(f"Unsupported retrieval strategy: {strategy}")

# Convenience functions
def create_patient_retriever(patient_id: str, max_results: int = 10) -> PatientSpecificRetriever:
    """Create a patient-specific retriever."""
    config = RetrievalConfig(
        strategy=RetrievalStrategy.PATIENT_SPECIFIC,
        max_results=max_results,
        patient_context=True
    )
    return PatientSpecificRetriever(config, patient_id=patient_id)

def create_temporal_retriever(temporal_window_days: int = 30) -> TemporalRetriever:
    """Create a temporal retriever."""
    config = RetrievalConfig(
        strategy=RetrievalStrategy.TEMPORAL,
        temporal_window_days=temporal_window_days,
        prioritize_recent=True
    )
    return TemporalRetriever(config)

def create_comprehensive_retriever(max_results: int = 10) -> MultiModalRetriever:
    """Create a comprehensive multi-modal retriever."""
    config = RetrievalConfig(
        strategy=RetrievalStrategy.MULTI_MODAL,
        max_results=max_results
    )
    return MultiModalRetriever(config)

__all__ = [
    # Core classes
    'RetrievalStrategy',
    'RetrievalConfig',
    'ClinicalContext',
    'HACSRetriever',
    # Specific retrievers
    'SemanticRetriever',
    'PatientSpecificRetriever',
    'TemporalRetriever',
    'MultiModalRetriever',
    # Factory
    'RetrieverFactory',
    # Convenience functions
    'create_patient_retriever',
    'create_temporal_retriever',
    'create_comprehensive_retriever',
]