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

# Re-export main APIs through the public API facade
from .api import (
    # Core functions
    extract,
    structure,
    extract_sync,
    structure_sync,
    extract_iterative,
    
    # Concise extraction functions
    extract_whole_records_with_spans,
    extract_citations,
    extract_citations_multi,
    extract_document_citations,
    extract_type_citations,
    extract_citations_guided,
    
    # Runner and config
    ExtractionRunner,
    ExtractionConfig,
    ExtractionMetrics,
    
    # Utilities
    group_type_citations,
    FormatType,
)

__all__ = [
    # Core functions
    "extract",
    "structure", 
    "extract_sync",
    "structure_sync",
    "extract_iterative",
    
    # Concise extraction functions
    "extract_whole_records_with_spans",
    "extract_citations",
    "extract_citations_multi",
    "extract_document_citations",
    "extract_type_citations",
    "extract_citations_guided",
    
    # Runner and config
    "ExtractionRunner",
    "ExtractionConfig", 
    "ExtractionMetrics",
    
    # Utilities
    "group_type_citations",
    "FormatType",
]
