"""
Document Models - FHIR-Compatible Clinical Documents with LangChain Integration.

This module provides comprehensive document modeling based on FHIR Document specification,
optimized for clinical workflows and seamless integration with LangChain Document types.

Features:
- FHIR-compatible document structure and composition
- LangChain Document conversion and integration
- Clinical narrative extraction and presentation
- Document attestation and digital signatures
- Section-based organization with rich metadata
- Support for various document types (clinical, discharge, referral, etc.)
"""

import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, validator

from ..base_resource import BaseResource


class DocumentStatus(str, Enum):
    """Status of a clinical document."""
    PRELIMINARY = "preliminary"  # Document is in preliminary form
    FINAL = "final"  # Document is complete and verified by authorized person
    AMENDED = "amended"  # Document has been modified subsequent to being Final
    CORRECTED = "corrected"  # Document has been corrected
    CANCELLED = "cancelled"  # Document is no longer valid
    ENTERED_IN_ERROR = "entered-in-error"  # Document was created in error


class DocumentType(str, Enum):
    """Types of clinical documents based on common healthcare use cases."""
    DISCHARGE_SUMMARY = "discharge-summary"
    PROGRESS_NOTE = "progress-note" 
    CONSULTATION_NOTE = "consultation-note"
    HISTORY_PHYSICAL = "history-physical"
    OPERATIVE_NOTE = "operative-note"
    REFERRAL_LETTER = "referral-letter"
    CARE_PLAN = "care-plan"
    ASSESSMENT_REPORT = "assessment-report"
    MEDICATION_LIST = "medication-list"
    PROBLEM_LIST = "problem-list"
    IMMUNIZATION_RECORD = "immunization-record"
    LAB_REPORT = "lab-report"
    IMAGING_REPORT = "imaging-report"
    PATHOLOGY_REPORT = "pathology-report"
    CLINICAL_SUMMARY = "clinical-summary"


class ConfidentialityLevel(str, Enum):
    """Document confidentiality levels."""
    NORMAL = "N"  # Normal access restriction
    RESTRICTED = "R"  # Restricted access
    VERY_RESTRICTED = "V"  # Very restricted access
    UNRESTRICTED = "U"  # Unrestricted access


class DocumentAuthor(BaseModel):
    """Author information for a document."""
    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True
    )
    
    id: Optional[str] = Field(None, description="Author identifier")
    name: str = Field(..., description="Author's full name")
    role: Optional[str] = Field(None, description="Author's role (e.g., physician, nurse)")
    organization: Optional[str] = Field(None, description="Author's organization")
    department: Optional[str] = Field(None, description="Author's department")
    contact: Optional[str] = Field(None, description="Contact information")
    license_number: Optional[str] = Field(None, description="Professional license number")
    specialty: Optional[str] = Field(None, description="Medical specialty")


class DocumentAttester(BaseModel):
    """Attester information for document verification."""
    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True
    )
    
    mode: str = Field(..., description="Attestation mode: legal, professional, personal, official")
    party_id: Optional[str] = Field(None, description="Attester identifier")
    party_name: str = Field(..., description="Attester's name")
    time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Attestation timestamp")
    signature: Optional[str] = Field(None, description="Digital signature or reference")
    organization: Optional[str] = Field(None, description="Attester's organization")


class DocumentSection(BaseModel):
    """A section within a clinical document with narrative and structured data."""
    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        extra="allow"
    )
    
    # Section identification
    id: Optional[str] = Field(None, description="Section identifier")
    title: str = Field(..., description="Human-readable section title")
    code: Optional[str] = Field(None, description="Section code (LOINC, SNOMED, etc.)")
    
    # Section content
    text: str = Field(..., description="Human-readable narrative content")
    mode: str = Field("snapshot", description="Section mode: snapshot, changes")
    order_by: Optional[str] = Field(None, description="How entries are ordered")
    
    # Section metadata
    author: Optional[DocumentAuthor] = Field(None, description="Section author")
    focus: Optional[str] = Field(None, description="Subject of this section")
    
    # Structured entries
    entries: List[str] = Field(default_factory=list, description="References to structured resources")
    
    # Subsections
    sections: List["DocumentSection"] = Field(default_factory=list, description="Nested subsections")
    
    # Custom metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional section metadata")

    def get_full_text(self) -> str:
        """Get complete text content including subsections."""
        full_text = self.text
        
        for section in self.sections:
            full_text += f"\n\n{section.title}\n{section.get_full_text()}"
        
        return full_text
    
    def get_word_count(self) -> int:
        """Get word count for this section including subsections."""
        return len(self.get_full_text().split())


# Forward reference resolution
DocumentSection.model_rebuild()


class DocumentEncounter(BaseModel):
    """Encounter context for the document."""
    model_config = ConfigDict(validate_assignment=True)
    
    id: Optional[str] = Field(None, description="Encounter identifier")
    type: Optional[str] = Field(None, description="Encounter type")
    period_start: Optional[datetime] = Field(None, description="Encounter start time")
    period_end: Optional[datetime] = Field(None, description="Encounter end time")
    location: Optional[str] = Field(None, description="Encounter location")
    class_code: Optional[str] = Field(None, description="Encounter class (inpatient, outpatient, etc.)")


class Document(BaseResource):
    """
    A FHIR-compatible clinical document with LangChain integration capabilities.
    
    Represents a composition of healthcare information that provides a coherent set
    of information including clinical observations and services. Documents have
    fixed presentation and are authored/attested by humans, organizations, or devices.
    
    Features:
    - FHIR Document Bundle compatibility
    - LangChain Document conversion
    - Clinical narrative management
    - Section-based organization
    - Attestation and signature support
    - Rich metadata for healthcare workflows
    """
    
    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        extra="allow",
        json_schema_extra={
            "examples": [
                {
                    "id": "doc-001",
                    "resource_type": "Document",
                    "document_type": "discharge-summary",
                    "title": "Discharge Summary - John Doe",
                    "status": "final",
                    "subject_id": "patient-001",
                    "encounter": {"id": "enc-001", "type": "inpatient"},
                    "date": "2024-01-15T10:30:00Z",
                    "sections": [
                        {
                            "title": "Chief Complaint",
                            "text": "Patient presented with chest pain and shortness of breath."
                        }
                    ]
                }
            ]
        }
    )
    
    # Override resource_type
    resource_type: str = Field(default="Document", frozen=True)
    
    # Document Identification
    document_identifier: Optional[str] = Field(None, description="Globally unique document identifier")
    version: str = Field("1.0", description="Document version")
    
    # Document Classification
    document_type: DocumentType = Field(..., description="Type of clinical document")
    title: str = Field(..., description="Human-readable document title")
    status: DocumentStatus = Field(DocumentStatus.PRELIMINARY, description="Document status")
    confidentiality: ConfidentialityLevel = Field(ConfidentialityLevel.NORMAL, description="Confidentiality level")
    
    # Clinical Context
    subject_id: str = Field(..., description="Patient/subject this document is about")
    subject_name: Optional[str] = Field(None, description="Patient/subject name for display")
    encounter: Optional[DocumentEncounter] = Field(None, description="Healthcare encounter context")
    
    # Authorship and Attestation
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Document composition date")
    authors: List[DocumentAuthor] = Field(default_factory=list, description="Document authors")
    attesters: List[DocumentAttester] = Field(default_factory=list, description="Document attesters")
    custodian: Optional[str] = Field(None, description="Organization responsible for ongoing maintenance")
    
    # Document Content
    sections: List[DocumentSection] = Field(default_factory=list, description="Document sections")
    
    # Document Metadata
    language: str = Field("en", description="Document language (ISO 639-1)")
    relates_to: List[str] = Field(default_factory=list, description="Related document identifiers")
    event_codes: List[str] = Field(default_factory=list, description="Event codes this document describes")
    
    # Technical Metadata
    stylesheet_url: Optional[str] = Field(None, description="CSS stylesheet for presentation")
    signature: Optional[str] = Field(None, description="Digital signature")
    
    # LangChain Integration
    langchain_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional LangChain metadata")
    
    @validator('document_identifier', pre=True, always=True)
    def generate_document_identifier(cls, v):
        """Generate document identifier if not provided."""
        if not v:
            # Generate based on timestamp and random component
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            import uuid
            return f"doc-{timestamp}-{str(uuid.uuid4())[:8]}"
        return v
    
    @validator('sections')
    def validate_sections_not_empty(cls, v, values):
        """Ensure final documents have content."""
        status = values.get('status')
        if status == DocumentStatus.FINAL and not v:
            raise ValueError("Final documents must contain at least one section")
        return v
    
    def add_section(
        self,
        title: str,
        text: str,
        code: Optional[str] = None,
        author: Optional[DocumentAuthor] = None,
        entries: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "Document":
        """
        Add a section to the document.
        
        Args:
            title: Section title
            text: Narrative content
            code: Optional section code
            author: Optional section author
            entries: Optional resource references
            metadata: Optional additional metadata
            
        Returns:
            Self for method chaining
        """
        section = DocumentSection(
            title=title,
            text=text,
            code=code,
            author=author,
            entries=entries or [],
            metadata=metadata or {}
        )
        self.sections.append(section)
        return self
    
    def add_author(
        self,
        name: str,
        role: Optional[str] = None,
        organization: Optional[str] = None,
        contact: Optional[str] = None,
        **kwargs
    ) -> "Document":
        """
        Add an author to the document.
        
        Args:
            name: Author's name
            role: Author's role
            organization: Author's organization
            contact: Contact information
            **kwargs: Additional author fields
            
        Returns:
            Self for method chaining
        """
        author = DocumentAuthor(
            name=name,
            role=role,
            organization=organization,
            contact=contact,
            **kwargs
        )
        self.authors.append(author)
        return self
    
    def add_attester(
        self,
        mode: str,
        party_name: str,
        party_id: Optional[str] = None,
        organization: Optional[str] = None,
        signature: Optional[str] = None
    ) -> "Document":
        """
        Add an attester to the document.
        
        Args:
            mode: Attestation mode
            party_name: Attester's name
            party_id: Attester's ID
            organization: Attester's organization
            signature: Digital signature
            
        Returns:
            Self for method chaining
        """
        attester = DocumentAttester(
            mode=mode,
            party_name=party_name,
            party_id=party_id,
            organization=organization,
            signature=signature
        )
        self.attesters.append(attester)
        return self
    
    def get_full_text(self) -> str:
        """
        Extract complete document text for LangChain processing.
        
        Returns:
            Complete document text with all sections
        """
        parts = [f"Document: {self.title}"]
        
        if self.subject_name:
            parts.append(f"Subject: {self.subject_name}")
        
        parts.append(f"Date: {self.date.strftime('%Y-%m-%d %H:%M:%S')}")
        parts.append(f"Type: {self.document_type}")
        parts.append(f"Status: {self.status}")
        
        if self.authors:
            authors_str = ", ".join([author.name for author in self.authors])
            parts.append(f"Authors: {authors_str}")
        
        parts.append("")  # Empty line before sections
        
        for section in self.sections:
            parts.append(f"\n{section.title}")
            parts.append("-" * len(section.title))
            parts.append(section.get_full_text())
        
        return "\n".join(parts)
    
    def get_section_by_title(self, title: str) -> Optional[DocumentSection]:
        """Get a section by its title."""
        for section in self.sections:
            if section.title.lower() == title.lower():
                return section
        return None
    
    def get_sections_by_code(self, code: str) -> List[DocumentSection]:
        """Get sections by their code."""
        return [section for section in self.sections if section.code == code]
    
    def get_word_count(self) -> int:
        """Get total word count for the document."""
        return sum(section.get_word_count() for section in self.sections)
    
    def get_content_hash(self) -> str:
        """Generate content hash for document integrity checking."""
        content = self.get_full_text()
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def to_langchain_document(self, **extra_metadata) -> Dict[str, Any]:
        """
        Convert to LangChain Document format.
        
        Args:
            **extra_metadata: Additional metadata to include
            
        Returns:
            Dictionary in LangChain Document format with page_content and metadata
        """
        metadata = {
            # Document identifiers
            "doc_id": self.id,
            "document_identifier": self.document_identifier,
            "document_type": self.document_type,
            "version": self.version,
            
            # Clinical context
            "subject_id": self.subject_id,
            "subject_name": self.subject_name,
            "status": self.status,
            "confidentiality": self.confidentiality,
            
            # Temporal information
            "date": self.date.isoformat(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            
            # Authorship
            "authors": [author.name for author in self.authors],
            "primary_author": self.authors[0].name if self.authors else None,
            
            # Content metadata
            "title": self.title,
            "language": self.language,
            "section_count": len(self.sections),
            "word_count": self.get_word_count(),
            "content_hash": self.get_content_hash(),
            
            # Technical metadata
            "source": "hacs-document",
            "resource_type": self.resource_type,
        }
        
        # Add encounter information if available
        if self.encounter:
            metadata.update({
                "encounter_id": self.encounter.id,
                "encounter_type": self.encounter.type,
                "encounter_class": self.encounter.class_code,
            })
        
        # Add custom LangChain metadata
        metadata.update(self.langchain_metadata)
        metadata.update(extra_metadata)
        
        return {
            "page_content": self.get_full_text(),
            "metadata": metadata
        }
    
    @classmethod
    def from_langchain_document(
        cls,
        langchain_doc: Dict[str, Any],
        document_type: Optional[DocumentType] = None,
        **kwargs
    ) -> "Document":
        """
        Create Document from LangChain Document format.
        
        Args:
            langchain_doc: LangChain document with page_content and metadata
            document_type: Override document type
            **kwargs: Additional document fields
            
        Returns:
            Document instance
        """
        page_content = langchain_doc.get("page_content", "")
        metadata = langchain_doc.get("metadata", {})
        
        # Extract document sections from text
        sections = cls._parse_sections_from_text(page_content)
        
        # Create document
        doc = cls(
            title=metadata.get("title", "Imported Document"),
            document_type=document_type or metadata.get("document_type", DocumentType.CLINICAL_SUMMARY),
            subject_id=metadata.get("subject_id", "unknown"),
            subject_name=metadata.get("subject_name"),
            status=metadata.get("status", DocumentStatus.PRELIMINARY),
            sections=sections,
            langchain_metadata=metadata,
            **kwargs
        )
        
        # Add author if available
        if metadata.get("primary_author"):
            doc.add_author(metadata["primary_author"])
        
        return doc
    
    @staticmethod
    def _parse_sections_from_text(text: str) -> List[DocumentSection]:
        """Parse sections from text content."""
        sections = []
        
        # Simple section parsing based on common patterns
        section_pattern = r'^([A-Z][A-Za-z\s]+):?\n[-=]*\n?(.*?)(?=\n\n[A-Z][A-Za-z\s]+:?\n[-=]*|\Z)'
        matches = re.findall(section_pattern, text, re.MULTILINE | re.DOTALL)
        
        for title, content in matches:
            title = title.strip().rstrip(':')
            content = content.strip()
            if content:
                sections.append(DocumentSection(
                    title=title,
                    text=content
                ))
        
        # If no sections found, create a single section
        if not sections and text.strip():
            sections.append(DocumentSection(
                title="Content",
                text=text.strip()
            ))
        
        return sections
    
    def to_langchain_documents(self, split_by_section: bool = False) -> List[Dict[str, Any]]:
        """
        Convert to multiple LangChain Documents.
        
        Args:
            split_by_section: If True, create one document per section
            
        Returns:
            List of LangChain Document dictionaries
        """
        if not split_by_section:
            return [self.to_langchain_document()]
        
        documents = []
        base_metadata = self.to_langchain_document()["metadata"]
        
        for i, section in enumerate(self.sections):
            section_metadata = base_metadata.copy()
            section_metadata.update({
                "section_index": i,
                "section_title": section.title,
                "section_code": section.code,
                "section_word_count": section.get_word_count(),
                "is_section": True
            })
            
            documents.append({
                "page_content": f"{section.title}\n{'-' * len(section.title)}\n{section.get_full_text()}",
                "metadata": section_metadata
            })
        
        return documents
    
    def validate_clinical_content(self) -> Dict[str, Any]:
        """
        Validate clinical document content and structure.
        
        Returns:
            Validation results with issues and recommendations
        """
        issues = []
        warnings = []
        recommendations = []
        
        # Check required clinical sections for different document types
        required_sections = {
            DocumentType.DISCHARGE_SUMMARY: ["Chief Complaint", "History", "Assessment", "Plan"],
            DocumentType.PROGRESS_NOTE: ["Assessment", "Plan"],
            DocumentType.CONSULTATION_NOTE: ["Reason for Consultation", "Assessment", "Recommendations"],
            DocumentType.HISTORY_PHYSICAL: ["Chief Complaint", "History", "Physical Exam", "Assessment"]
        }
        
        if self.document_type in required_sections:
            required = required_sections[self.document_type]
            existing = [section.title for section in self.sections]
            missing = [req for req in required if not any(req.lower() in existing_title.lower() for existing_title in existing)]
            
            if missing:
                warnings.append(f"Missing recommended sections for {self.document_type}: {missing}")
        
        # Check authorship
        if not self.authors:
            issues.append("Document must have at least one author")
        
        # Check attestation for final documents
        if self.status == DocumentStatus.FINAL and not self.attesters:
            warnings.append("Final documents should have attesters")
        
        # Check content completeness
        if not self.sections:
            issues.append("Document must contain at least one section")
        
        total_words = self.get_word_count()
        if total_words < 10:
            warnings.append("Document content appears very brief")
        
        # Check for empty sections
        empty_sections = [section.title for section in self.sections if not section.text.strip()]
        if empty_sections:
            warnings.append(f"Empty sections found: {empty_sections}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "recommendations": recommendations,
            "word_count": total_words,
            "section_count": len(self.sections),
            "has_authors": len(self.authors) > 0,
            "has_attesters": len(self.attesters) > 0
        }


# Factory functions for common document types

def create_discharge_summary(
    patient_id: str,
    patient_name: str,
    primary_author: str,
    encounter_id: Optional[str] = None,
    **kwargs
) -> Document:
    """
    Create a discharge summary document template.
    
    Args:
        patient_id: Patient identifier
        patient_name: Patient name
        primary_author: Primary author name
        encounter_id: Associated encounter ID
        **kwargs: Additional document fields
        
    Returns:
        Discharge summary document template
    """
    doc = Document(
        document_type=DocumentType.DISCHARGE_SUMMARY,
        title=f"Discharge Summary - {patient_name}",
        subject_id=patient_id,
        subject_name=patient_name,
        **kwargs
    )
    
    if encounter_id:
        doc.encounter = DocumentEncounter(id=encounter_id, type="inpatient")
    
    doc.add_author(primary_author, role="attending-physician")
    
    # Add standard discharge summary sections
    doc.add_section("Chief Complaint", "")
    doc.add_section("History of Present Illness", "")
    doc.add_section("Past Medical History", "")
    doc.add_section("Hospital Course", "")
    doc.add_section("Discharge Medications", "")
    doc.add_section("Discharge Instructions", "")
    doc.add_section("Follow-up", "")
    
    return doc


def create_progress_note(
    patient_id: str,
    patient_name: str,
    author: str,
    note_type: str = "daily",
    **kwargs
) -> Document:
    """
    Create a progress note document.
    
    Args:
        patient_id: Patient identifier
        patient_name: Patient name
        author: Note author
        note_type: Type of progress note
        **kwargs: Additional document fields
        
    Returns:
        Progress note document
    """
    doc = Document(
        document_type=DocumentType.PROGRESS_NOTE,
        title=f"Progress Note - {patient_name} ({note_type})",
        subject_id=patient_id,
        subject_name=patient_name,
        **kwargs
    )
    
    doc.add_author(author)
    
    # Add standard progress note sections
    doc.add_section("Subjective", "")
    doc.add_section("Objective", "")
    doc.add_section("Assessment", "")
    doc.add_section("Plan", "")
    
    return doc


def create_consultation_note(
    patient_id: str,
    patient_name: str,
    consultant: str,
    specialty: str,
    referring_physician: Optional[str] = None,
    **kwargs
) -> Document:
    """
    Create a consultation note document.
    
    Args:
        patient_id: Patient identifier
        patient_name: Patient name
        consultant: Consulting physician
        specialty: Medical specialty
        referring_physician: Referring physician
        **kwargs: Additional document fields
        
    Returns:
        Consultation note document
    """
    doc = Document(
        document_type=DocumentType.CONSULTATION_NOTE,
        title=f"{specialty} Consultation - {patient_name}",
        subject_id=patient_id,
        subject_name=patient_name,
        **kwargs
    )
    
    doc.add_author(consultant, role="consultant", specialty=specialty)
    
    # Add consultation sections
    doc.add_section("Reason for Consultation", "")
    doc.add_section("History of Present Illness", "")
    doc.add_section("Review of Systems", "")
    doc.add_section("Physical Examination", "")
    doc.add_section("Assessment and Clinical Impression", "")
    doc.add_section("Recommendations", "")
    
    if referring_physician:
        doc.langchain_metadata["referring_physician"] = referring_physician
    
    return doc


def create_clinical_summary(
    patient_id: str,
    patient_name: str,
    author: str,
    summary_type: str = "comprehensive",
    **kwargs
) -> Document:
    """
    Create a clinical summary document.
    
    Args:
        patient_id: Patient identifier
        patient_name: Patient name
        author: Summary author
        summary_type: Type of summary
        **kwargs: Additional document fields
        
    Returns:
        Clinical summary document
    """
    doc = Document(
        document_type=DocumentType.CLINICAL_SUMMARY,
        title=f"Clinical Summary - {patient_name} ({summary_type})",
        subject_id=patient_id,
        subject_name=patient_name,
        **kwargs
    )
    
    doc.add_author(author)
    
    # Add summary sections
    doc.add_section("Patient Demographics", "")
    doc.add_section("Active Problems", "")
    doc.add_section("Current Medications", "")
    doc.add_section("Allergies", "")
    doc.add_section("Recent Visits", "")
    doc.add_section("Care Team", "")
    
    return doc