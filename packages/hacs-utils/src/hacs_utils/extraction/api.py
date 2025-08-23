"""
Public high-level extraction API.

This module re-exports the stable, user-facing functions and classes from
`hacs_utils.structured` so new code can depend on `hacs_utils.extraction`
without breaking existing imports. Over time, implementations can migrate
behind this facade.
"""

from __future__ import annotations

# Re-export from the existing structured module to avoid duplication
from ..structured import (
    # Core
    extract,
    structure,
    extract_sync,
    structure_sync,

    # HACS-specific pipelines
    extract_hacs_resources_with_citations,
    extract_hacs_multi_with_citations,
    extract_hacs_document_with_citations,
    extract_hacs_resource_type_citations,
    extract_hacs_document_with_citation_guidance,
    extract_whole_records_with_spans,

    # Runner and configuration
    ExtractionRunner,
    ExtractionConfig,
    ExtractionMetrics,

    # Utilities
    group_records_by_type,
    group_resource_type_citations,
    FormatType,
)

__all__ = [
    # Core
    "extract",
    "structure",
    "extract_sync",
    "structure_sync",

    # HACS-specific pipelines
    "extract_hacs_resources_with_citations",
    "extract_hacs_multi_with_citations",
    "extract_hacs_document_with_citations",
    "extract_hacs_resource_type_citations",
    "extract_hacs_document_with_citation_guidance",
    "extract_whole_records_with_spans",

    # Runner and configuration
    "ExtractionRunner",
    "ExtractionConfig",
    "ExtractionMetrics",

    # Utilities
    "group_records_by_type",
    "group_resource_type_citations",
    "FormatType",
]


