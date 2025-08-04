"""
LangChain Integration for HACS

Provides LangChain utilities for healthcare document processing and workflows.
"""

try:
    from langchain.schema import Document
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    _has_langchain = True
except ImportError:
    _has_langchain = False
    # Placeholder classes
    class Document:
        def __init__(self, page_content: str, metadata: dict = None):
            self.page_content = page_content
            self.metadata = metadata or {}

    class RecursiveCharacterTextSplitter:
        def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap

        def split_documents(self, documents):
            return documents


class LangChainDocumentAdapter:
    """LangChain document adapter for healthcare documents."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Initialize document adapter."""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

    def process_text(self, text: str, metadata: dict = None) -> list:
        """Process text into documents."""
        doc = Document(page_content=text, metadata=metadata or {})
        return self.text_splitter.split_documents([doc])


# Keep the processor for backward compatibility
LangChainDocumentProcessor = LangChainDocumentAdapter


def create_langchain_adapter(chunk_size: int = 1000, chunk_overlap: int = 200) -> LangChainDocumentAdapter:
    """Create a LangChain document adapter."""
    return LangChainDocumentAdapter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)


# Keep the processor creator for backward compatibility
def create_document_processor(chunk_size: int = 1000, chunk_overlap: int = 200) -> LangChainDocumentAdapter:
    """Create a LangChain document processor."""
    return create_langchain_adapter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)


from .tools import (
    get_hacs_tools,
    get_hacs_tool,
    get_hacs_tools_by_category,
    HACSToolRegistry,
    validate_tool_inputs,
)

# Import new comprehensive modules
from .adapters import (
    TypeAdapter,
    ConversionStrategy,
    ConversionContext,
    BidirectionalConverter,
    HACSToLangChainDocumentAdapter,
    HACSToLangChainMessageAdapter,
    AdapterFactory,
    hacs_to_documents,
    documents_to_hacs,
    hacs_messages_to_langchain,
    langchain_messages_to_hacs,
)

from .memory import (
    MemoryStrategy,
    MemoryConfig,
    HACSMemoryStrategy,
    EpisodicMemoryStrategy,
    ClinicalMemoryStrategy,
    HACSLangChainMemory,
    MemoryFactory,
    create_clinical_memory,
    create_episodic_memory,
)

from .chains import (
    ChainType,
    ChainStrategy,
    ChainConfig,
    HealthcareChainFactory,
    create_clinical_assessment_chain,
    create_diagnostic_chain,
    create_treatment_planning_chain,
    create_comprehensive_clinical_chain,
)

from .vector_stores import (
    VectorStoreType,
    EmbeddingStrategy,
    VectorStoreConfig,
    HACSEmbeddings,
    HACSVectorStore,
    VectorStoreFactory,
    create_clinical_vector_store,
    create_general_vector_store,
)

from .retrievers import (
    RetrievalStrategy,
    RetrievalConfig,
    ClinicalContext,
    HACSRetriever,
    RetrieverFactory,
    create_patient_retriever,
    create_temporal_retriever,
    create_comprehensive_retriever,
)

__all__ = [
    # Document Processing
    "LangChainDocumentAdapter",
    "LangChainDocumentProcessor", 
    "create_langchain_adapter",
    "create_document_processor",
    "Document",
    "RecursiveCharacterTextSplitter",
    
    # HACS Tools Integration
    "get_hacs_tools",
    "get_hacs_tool",
    "get_hacs_tools_by_category", 
    "HACSToolRegistry",
    "validate_tool_inputs",
    
    # Type Adapters
    "TypeAdapter",
    "ConversionStrategy",
    "ConversionContext",
    "BidirectionalConverter",
    "HACSToLangChainDocumentAdapter",
    "HACSToLangChainMessageAdapter",
    "AdapterFactory",
    "hacs_to_documents",
    "documents_to_hacs",
    "hacs_messages_to_langchain",
    "langchain_messages_to_hacs",
    
    # Memory Integration
    "MemoryStrategy",
    "MemoryConfig",
    "HACSMemoryStrategy",
    "EpisodicMemoryStrategy",
    "ClinicalMemoryStrategy",
    "HACSLangChainMemory",
    "MemoryFactory",
    "create_clinical_memory",
    "create_episodic_memory",
    
    # Chain Builders
    "ChainType",
    "ChainStrategy",
    "ChainConfig",
    "HealthcareChainFactory",
    "create_clinical_assessment_chain",
    "create_diagnostic_chain",
    "create_treatment_planning_chain",
    "create_comprehensive_clinical_chain",
    
    # Vector Stores
    "VectorStoreType",
    "EmbeddingStrategy",
    "VectorStoreConfig",
    "HACSEmbeddings",
    "HACSVectorStore",
    "VectorStoreFactory",
    "create_clinical_vector_store",
    "create_general_vector_store",
    
    # Retrievers
    "RetrievalStrategy",
    "RetrievalConfig",
    "ClinicalContext",
    "HACSRetriever",
    "RetrieverFactory",
    "create_patient_retriever",
    "create_temporal_retriever",
    "create_comprehensive_retriever",
]