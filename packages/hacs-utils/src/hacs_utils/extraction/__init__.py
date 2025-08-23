"""
Extraction submodule for organized structured output components.

This module splits the large structured.py into focused components:
- prompt_builder: Prompt construction and schema handling
- pipeline: Core LLM invocation and structured output pipeline
- parsing: Response parsing and validation
- windowing: Citation windowing and span extraction
- validation: Record validation and coercion
- dedupe: Deduplication logic
- metrics: Performance tracking
"""

# Re-export main APIs for backward compatibility
from ..structured import (
    # Core functions
    extract,
    structure,
    extract_sync,
    structure_sync,
    
    # HACS extraction functions
    extract_hacs_resources_with_citations,
    extract_hacs_multi_with_citations,
    extract_hacs_document_with_citations,
    extract_hacs_resource_type_citations,
    extract_hacs_document_with_citation_guidance,
    extract_whole_records_with_spans,
    
    # Runner and config
    ExtractionRunner,
    ExtractionConfig,
    ExtractionMetrics,
    
    # Utilities
    group_records_by_type,
    group_resource_type_citations,
    FormatType,
)

__all__ = [
    # Core functions
    "extract",
    "structure", 
    "extract_sync",
    "structure_sync",
    
    # HACS extraction functions
    "extract_hacs_resources_with_citations",
    "extract_hacs_multi_with_citations", 
    "extract_hacs_document_with_citations",
    "extract_hacs_resource_type_citations",
    "extract_hacs_document_with_citation_guidance",
    "extract_whole_records_with_spans",
    
    # Runner and config
    "ExtractionRunner",
    "ExtractionConfig", 
    "ExtractionMetrics",
    
    # Utilities
    "group_records_by_type",
    "group_resource_type_citations",
    "FormatType",
]
