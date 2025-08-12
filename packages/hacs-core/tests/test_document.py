"""
Test suite for Document and related components.
"""

import pytest
from datetime import datetime, timezone

from hacs_core.models import (
    Document,
    DocumentStatus,
    DocumentType,
    ConfidentialityLevel,
    DocumentAuthor,
    DocumentAttester,
    DocumentSection,
    DocumentEncounter,
    create_discharge_summary,
    create_progress_note,
    create_consultation_note,
    create_clinical_summary,
)


class TestDocument:
    """Test Document core functionality."""

    def test_basic_document_creation(self):
        """Test basic Document creation and attributes."""
        doc = Document(
            document_type=DocumentType.PROGRESS_NOTE,
            title="Test Progress Note",
            subject_id="patient-001",
            subject_name="John Doe"
        )
        
        assert doc.document_type == DocumentType.PROGRESS_NOTE
        assert doc.title == "Test Progress Note"
        assert doc.subject_id == "patient-001"
        assert doc.subject_name == "John Doe"
        assert doc.resource_type == "Document"
        assert doc.status == DocumentStatus.PRELIMINARY
        assert doc.confidentiality == ConfidentialityLevel.NORMAL
        assert doc.document_identifier is not None  # Auto-generated

    def test_document_identifier_generation(self):
        """Test automatic document identifier generation."""
        doc1 = Document(
            document_type=DocumentType.PROGRESS_NOTE,
            title="Test 1",
            subject_id="patient-001"
        )
        
        doc2 = Document(
            document_type=DocumentType.PROGRESS_NOTE,
            title="Test 2",
            subject_id="patient-001"
        )
        
        assert doc1.document_identifier != doc2.document_identifier
        assert doc1.document_identifier.startswith("doc-")
        assert doc2.document_identifier.startswith("doc-")

    def test_add_section(self):
        """Test adding sections to document."""
        doc = Document(
            document_type=DocumentType.PROGRESS_NOTE,
            title="Test Document",
            subject_id="patient-001"
        )
        
        doc.add_section(
            title="Assessment",
            text="Patient is stable and improving.",
            code="assessment",
            metadata={"priority": "high"}
        )
        
        assert len(doc.sections) == 1
        section = doc.sections[0]
        assert section.title == "Assessment"
        assert section.text == "Patient is stable and improving."
        assert section.code == "assessment"
        assert section.metadata["priority"] == "high"

    def test_add_author(self):
        """Test adding authors to document."""
        doc = Document(
            document_type=DocumentType.PROGRESS_NOTE,
            title="Test Document",
            subject_id="patient-001"
        )
        
        doc.add_author(
            name="Dr. Jane Smith",
            role="attending-physician",
            organization="General Hospital",
            specialty="Internal Medicine"
        )
        
        assert len(doc.authors) == 1
        author = doc.authors[0]
        assert author.name == "Dr. Jane Smith"
        assert author.role == "attending-physician"
        assert author.organization == "General Hospital"
        assert author.specialty == "Internal Medicine"

    def test_add_attester(self):
        """Test adding attesters to document."""
        doc = Document(
            document_type=DocumentType.DISCHARGE_SUMMARY,
            title="Test Document",
            subject_id="patient-001"
        )
        
        doc.add_attester(
            mode="professional",
            party_name="Dr. John Doe",
            party_id="doc-123",
            organization="General Hospital",
            signature="digital-signature-hash"
        )
        
        assert len(doc.attesters) == 1
        attester = doc.attesters[0]
        assert attester.mode == "professional"
        assert attester.party_name == "Dr. John Doe"
        assert attester.party_id == "doc-123"
        assert attester.organization == "General Hospital"
        assert attester.signature == "digital-signature-hash"

    def test_get_full_text(self):
        """Test full text extraction."""
        doc = Document(
            document_type=DocumentType.PROGRESS_NOTE,
            title="Progress Note",
            subject_id="patient-001",
            subject_name="John Doe"
        )
        
        doc.add_author("Dr. Jane Smith")
        doc.add_section("Assessment", "Patient is stable.")
        doc.add_section("Plan", "Continue current treatment.")
        
        full_text = doc.get_full_text()
        
        assert "Document: Progress Note" in full_text
        assert "Subject: John Doe" in full_text
        assert "Authors: Dr. Jane Smith" in full_text
        assert "Assessment" in full_text
        assert "Patient is stable." in full_text
        assert "Plan" in full_text
        assert "Continue current treatment." in full_text

    def test_get_section_by_title(self):
        """Test section retrieval by title."""
        doc = Document(
            document_type=DocumentType.PROGRESS_NOTE,
            title="Test Document",
            subject_id="patient-001"
        )
        
        doc.add_section("Assessment", "Patient assessment")
        doc.add_section("Plan", "Treatment plan")
        
        assessment = doc.get_section_by_title("Assessment")
        plan = doc.get_section_by_title("Plan")
        missing = doc.get_section_by_title("Missing")
        
        assert assessment is not None
        assert assessment.title == "Assessment"
        assert plan is not None
        assert plan.title == "Plan"
        assert missing is None

    def test_get_sections_by_code(self):
        """Test section retrieval by code."""
        doc = Document(
            document_type=DocumentType.PROGRESS_NOTE,
            title="Test Document",
            subject_id="patient-001"
        )
        
        doc.add_section("Assessment 1", "First assessment", code="assessment")
        doc.add_section("Assessment 2", "Second assessment", code="assessment")
        doc.add_section("Plan", "Treatment plan", code="plan")
        
        assessments = doc.get_sections_by_code("assessment")
        plans = doc.get_sections_by_code("plan")
        missing = doc.get_sections_by_code("missing")
        
        assert len(assessments) == 2
        assert len(plans) == 1
        assert len(missing) == 0

    def test_get_word_count(self):
        """Test word count calculation."""
        doc = Document(
            document_type=DocumentType.PROGRESS_NOTE,
            title="Test Document",
            subject_id="patient-001"
        )
        
        doc.add_section("Assessment", "This is a test assessment with ten words total.")
        doc.add_section("Plan", "Short plan.")
        
        word_count = doc.get_word_count()
        assert word_count == 12  # 10 + 2 words

    def test_get_content_hash(self):
        """Test content hash generation."""
        doc1 = Document(
            document_type=DocumentType.PROGRESS_NOTE,
            title="Test Document",
            subject_id="patient-001"
        )
        doc1.add_section("Assessment", "Same content")
        
        doc2 = Document(
            document_type=DocumentType.PROGRESS_NOTE,
            title="Test Document",
            subject_id="patient-001"
        )
        doc2.add_section("Assessment", "Same content")
        
        doc3 = Document(
            document_type=DocumentType.PROGRESS_NOTE,
            title="Test Document",
            subject_id="patient-001"
        )
        doc3.add_section("Assessment", "Different content")
        
        hash1 = doc1.get_content_hash()
        hash2 = doc2.get_content_hash()
        hash3 = doc3.get_content_hash()
        
        assert hash1 == hash2  # Same content, same hash
        assert hash1 != hash3  # Different content, different hash


class TestLangChainIntegration:
    """Test LangChain Document integration."""

    def test_to_langchain_document(self):
        """Test conversion to LangChain Document format."""
        doc = Document(
            document_type=DocumentType.PROGRESS_NOTE,
            title="Progress Note",
            subject_id="patient-001",
            subject_name="John Doe"
        )
        
        doc.add_author("Dr. Jane Smith", role="physician")
        doc.add_section("Assessment", "Patient is stable and improving.")
        doc.add_section("Plan", "Continue current medications.")
        
        langchain_doc = doc.to_langchain_document(custom_field="custom_value")
        
        assert "page_content" in langchain_doc
        assert "metadata" in langchain_doc
        
        content = langchain_doc["page_content"]
        metadata = langchain_doc["metadata"]
        
        assert "Progress Note" in content
        assert "Assessment" in content
        assert "Patient is stable" in content
        
        assert metadata["doc_id"] == doc.id
        assert metadata["document_type"] == DocumentType.PROGRESS_NOTE
        assert metadata["subject_id"] == "patient-001"
        assert metadata["subject_name"] == "John Doe"
        assert metadata["primary_author"] == "Dr. Jane Smith"
        assert metadata["section_count"] == 2
        assert metadata["custom_field"] == "custom_value"
        assert metadata["source"] == "hacs-document"

    def test_from_langchain_document(self):
        """Test creation from LangChain Document format."""
        langchain_doc = {
            "page_content": "Assessment\n----------\nPatient is stable.\n\nPlan\n----\nContinue treatment.",
            "metadata": {
                "title": "Test Progress Note",
                "subject_id": "patient-001",
                "subject_name": "Jane Doe",
                "primary_author": "Dr. Smith",
                "document_type": "progress-note"
            }
        }
        
        doc = Document.from_langchain_document(langchain_doc)
        
        assert doc.title == "Test Progress Note"
        assert doc.subject_id == "patient-001"
        assert doc.subject_name == "Jane Doe"
        assert doc.document_type == DocumentType.PROGRESS_NOTE
        assert len(doc.authors) == 1
        assert doc.authors[0].name == "Dr. Smith"

    def test_to_langchain_documents_split_by_section(self):
        """Test conversion to multiple LangChain Documents split by section."""
        doc = Document(
            document_type=DocumentType.PROGRESS_NOTE,
            title="Progress Note",
            subject_id="patient-001"
        )
        
        doc.add_section("Assessment", "Patient assessment details")
        doc.add_section("Plan", "Treatment plan details")
        
        langchain_docs = doc.to_langchain_documents(split_by_section=True)
        
        assert len(langchain_docs) == 2
        
        # Check first section document
        doc1 = langchain_docs[0]
        assert "Assessment" in doc1["page_content"]
        assert "Patient assessment details" in doc1["page_content"]
        assert doc1["metadata"]["section_index"] == 0
        assert doc1["metadata"]["section_title"] == "Assessment"
        assert doc1["metadata"]["is_section"] is True
        
        # Check second section document
        doc2 = langchain_docs[1]
        assert "Plan" in doc2["page_content"]
        assert "Treatment plan details" in doc2["page_content"]
        assert doc2["metadata"]["section_index"] == 1
        assert doc2["metadata"]["section_title"] == "Plan"


class TestDocumentSection:
    """Test DocumentSection functionality."""

    def test_section_creation(self):
        """Test DocumentSection creation."""
        section = DocumentSection(
            title="Assessment",
            text="Patient assessment details",
            code="assessment",
            metadata={"priority": "high"}
        )
        
        assert section.title == "Assessment"
        assert section.text == "Patient assessment details"
        assert section.code == "assessment"
        assert section.metadata["priority"] == "high"

    def test_nested_sections(self):
        """Test nested sections functionality."""
        parent_section = DocumentSection(
            title="Physical Exam",
            text="Overall physical examination findings"
        )
        
        subsection1 = DocumentSection(
            title="Cardiovascular",
            text="Heart rate regular, no murmurs"
        )
        
        subsection2 = DocumentSection(
            title="Respiratory",
            text="Lungs clear bilaterally"
        )
        
        parent_section.sections = [subsection1, subsection2]
        
        full_text = parent_section.get_full_text()
        assert "Overall physical examination findings" in full_text
        assert "Cardiovascular" in full_text
        assert "Heart rate regular" in full_text
        assert "Respiratory" in full_text
        assert "Lungs clear bilaterally" in full_text

    def test_section_word_count(self):
        """Test section word count calculation."""
        section = DocumentSection(
            title="Assessment",
            text="This is a test assessment with exactly ten words."
        )
        
        subsection = DocumentSection(
            title="Subsection",
            text="Additional five words here."
        )
        
        section.sections = [subsection]
        
        assert section.get_word_count() == 15  # 10 + 5 words


class TestDocumentValidation:
    """Test document validation rules."""

    def test_final_document_requires_sections(self):
        """Test that final documents must have sections."""
        with pytest.raises(ValueError, match="Final documents must contain at least one section"):
            Document(
                document_type=DocumentType.PROGRESS_NOTE,
                title="Test Document",
                subject_id="patient-001",
                status=DocumentStatus.FINAL
            )

    def test_document_validation(self):
        """Test clinical content validation."""
        doc = Document(
            document_type=DocumentType.DISCHARGE_SUMMARY,
            title="Discharge Summary",
            subject_id="patient-001",
            status=DocumentStatus.FINAL
        )
        
        # Add required sections
        doc.add_section("Chief Complaint", "Chest pain")
        doc.add_section("History", "Patient history")
        doc.add_section("Assessment", "Clinical assessment")
        doc.add_section("Plan", "Treatment plan")
        
        # Add author and attester
        doc.add_author("Dr. Smith")
        doc.add_attester("professional", "Dr. Jones")
        
        validation = doc.validate_clinical_content()
        
        assert validation["valid"] is True
        assert validation["has_authors"] is True
        assert validation["has_attesters"] is True
        assert validation["section_count"] == 4
        assert len(validation["issues"]) == 0


class TestFactoryFunctions:
    """Test factory functions for creating documents."""

    def test_create_discharge_summary(self):
        """Test discharge summary factory function."""
        doc = create_discharge_summary(
            patient_id="patient-001",
            patient_name="John Doe",
            primary_author="Dr. Smith",
            encounter_id="enc-001"
        )
        
        assert doc.document_type == DocumentType.DISCHARGE_SUMMARY
        assert doc.subject_id == "patient-001"
        assert doc.subject_name == "John Doe"
        assert len(doc.authors) == 1
        assert doc.authors[0].name == "Dr. Smith"
        assert doc.encounter is not None
        assert doc.encounter.id == "enc-001"
        assert len(doc.sections) == 7  # Standard discharge sections

    def test_create_progress_note(self):
        """Test progress note factory function."""
        doc = create_progress_note(
            patient_id="patient-001",
            patient_name="John Doe",
            author="Dr. Smith",
            note_type="daily"
        )
        
        assert doc.document_type == DocumentType.PROGRESS_NOTE
        assert doc.subject_id == "patient-001"
        assert doc.subject_name == "John Doe"
        assert "daily" in doc.title
        assert len(doc.authors) == 1
        assert doc.authors[0].name == "Dr. Smith"
        assert len(doc.sections) == 4  # SOAP sections

    def test_create_consultation_note(self):
        """Test consultation note factory function."""
        doc = create_consultation_note(
            patient_id="patient-001",
            patient_name="John Doe",
            consultant="Dr. Specialist",
            specialty="Cardiology",
            referring_physician="Dr. Primary"
        )
        
        assert doc.document_type == DocumentType.CONSULTATION_NOTE
        assert doc.subject_id == "patient-001"
        assert doc.subject_name == "John Doe"
        assert "Cardiology" in doc.title
        assert len(doc.authors) == 1
        assert doc.authors[0].name == "Dr. Specialist"
        assert doc.authors[0].specialty == "Cardiology"
        assert doc.langchain_metadata["referring_physician"] == "Dr. Primary"
        assert len(doc.sections) == 6  # Standard consultation sections

    def test_create_clinical_summary(self):
        """Test clinical summary factory function."""
        doc = create_clinical_summary(
            patient_id="patient-001",
            patient_name="John Doe",
            author="Dr. Smith",
            summary_type="comprehensive"
        )
        
        assert doc.document_type == DocumentType.CLINICAL_SUMMARY
        assert doc.subject_id == "patient-001"
        assert doc.subject_name == "John Doe"
        assert "comprehensive" in doc.title
        assert len(doc.authors) == 1
        assert doc.authors[0].name == "Dr. Smith"
        assert len(doc.sections) == 6  # Standard summary sections


class TestDocumentTypes:
    """Test different document type behaviors."""

    def test_document_type_enum(self):
        """Test document type enumeration."""
        doc = Document(
            document_type=DocumentType.DISCHARGE_SUMMARY,
            title="Test",
            subject_id="patient-001"
        )
        
        assert doc.document_type == DocumentType.DISCHARGE_SUMMARY
        assert doc.document_type.value == "discharge-summary"

    def test_document_status_enum(self):
        """Test document status enumeration."""
        doc = Document(
            document_type=DocumentType.PROGRESS_NOTE,
            title="Test",
            subject_id="patient-001",
            status=DocumentStatus.FINAL
        )
        
        assert doc.status == DocumentStatus.FINAL
        assert doc.status.value == "final"

    def test_confidentiality_enum(self):
        """Test confidentiality level enumeration."""
        doc = Document(
            document_type=DocumentType.PROGRESS_NOTE,
            title="Test",
            subject_id="patient-001",
            confidentiality=ConfidentialityLevel.RESTRICTED
        )
        
        assert doc.confidentiality == ConfidentialityLevel.RESTRICTED
        assert doc.confidentiality.value == "R"


class TestDocumentEncounter:
    """Test DocumentEncounter functionality."""

    def test_encounter_creation(self):
        """Test DocumentEncounter creation."""
        encounter = DocumentEncounter(
            id="enc-001",
            type="inpatient",
            period_start=datetime.now(timezone.utc),
            location="General Hospital",
            class_code="inpatient"
        )
        
        assert encounter.id == "enc-001"
        assert encounter.type == "inpatient"
        assert encounter.location == "General Hospital"
        assert encounter.class_code == "inpatient"

    def test_document_with_encounter(self):
        """Test document with encounter context."""
        encounter = DocumentEncounter(
            id="enc-001",
            type="emergency",
            class_code="emergency"
        )
        
        doc = Document(
            document_type=DocumentType.PROGRESS_NOTE,
            title="Emergency Note",
            subject_id="patient-001",
            encounter=encounter
        )
        
        langchain_doc = doc.to_langchain_document()
        metadata = langchain_doc["metadata"]
        
        assert metadata["encounter_id"] == "enc-001"
        assert metadata["encounter_type"] == "emergency"
        assert metadata["encounter_class"] == "emergency"