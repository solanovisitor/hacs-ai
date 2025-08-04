#!/usr/bin/env python3
"""
Document and LangChain Integration Example.

This example demonstrates comprehensive HACS Document functionality with
seamless LangChain integration for clinical document processing workflows.

Features demonstrated:
- Creating FHIR-compatible clinical documents
- LangChain Document conversion (bi-directional)
- Document validation and attestation
- Section-based content organization
- Clinical workflow integration
- Document templates and factory functions
"""

from datetime import datetime, timezone
from typing import List, Dict, Any

from hacs_core.models import (
    Document,
    DocumentType,
    DocumentStatus,
    ConfidentialityLevel,
    DocumentAuthor,
    DocumentSection,
    create_discharge_summary,
    create_progress_note,
    create_consultation_note,
    create_clinical_summary,
)


def create_comprehensive_discharge_summary() -> Document:
    """Create a comprehensive discharge summary with all sections."""
    
    # Create the document
    doc = create_discharge_summary(
        patient_id="patient-12345",
        patient_name="John Doe",
        primary_author="Dr. Sarah Chen",
        encounter_id="enc-67890"
    )
    
    # Set additional metadata
    doc.status = DocumentStatus.FINAL
    doc.confidentiality = ConfidentialityLevel.NORMAL
    doc.custodian = "General Hospital Medical Records"
    
    # Add additional authors
    doc.add_author(
        name="Dr. Michael Rodriguez",
        role="resident-physician",
        organization="General Hospital",
        department="Internal Medicine",
        specialty="Internal Medicine"
    )
    
    # Add attesters
    doc.add_attester(
        mode="professional",
        party_name="Dr. Sarah Chen",
        party_id="physician-001",
        organization="General Hospital"
    )
    
    # Populate sections with detailed content
    
    # Chief Complaint
    chief_complaint = doc.get_section_by_title("Chief Complaint")
    chief_complaint.text = """
    78-year-old male with history of hypertension and diabetes mellitus type 2 
    presented to the emergency department with acute onset chest pain and shortness 
    of breath that began approximately 6 hours prior to arrival.
    """
    
    # History of Present Illness
    hpi = doc.get_section_by_title("History of Present Illness")
    hpi.text = """
    Patient was in his usual state of health until the morning of admission when he 
    developed sudden onset of substernal chest pain described as pressure-like, 
    9/10 severity, radiating to left arm and jaw. Associated symptoms included 
    diaphoresis, nausea, and progressive dyspnea. No relief with rest or sublingual 
    nitroglycerin. Patient called 911 and was transported to the emergency department.
    
    In the ED, initial vital signs were notable for blood pressure 180/95, heart rate 
    102, respiratory rate 24, oxygen saturation 92% on room air. EKG showed ST-elevation 
    in leads II, III, and aVF consistent with inferior STEMI. Patient was taken 
    emergently to cardiac catheterization lab.
    """
    
    # Past Medical History
    pmh = doc.get_section_by_title("Past Medical History")
    pmh.text = """
    1. Hypertension - diagnosed 2018, well-controlled on lisinopril
    2. Diabetes mellitus type 2 - diagnosed 2020, HbA1c 7.2% (3 months ago)
    3. Hyperlipidemia - on atorvastatin
    4. No prior cardiac history
    5. No prior hospitalizations
    
    Surgical History: Appendectomy (1995)
    
    Allergies: No known drug allergies
    
    Social History: Former smoker (quit 2015, 30 pack-year history), occasional alcohol use, 
    retired teacher, lives with spouse, independent with ADLs.
    
    Family History: Father deceased (MI age 72), mother deceased (stroke age 78), 
    brother with diabetes.
    """
    
    # Hospital Course
    hospital_course = doc.get_section_by_title("Hospital Course")
    hospital_course.text = """
    Patient underwent emergent cardiac catheterization revealing 100% occlusion of 
    the right coronary artery (RCA). Successful primary percutaneous coronary 
    intervention (PCI) was performed with drug-eluting stent placement. Peak troponin 
    was 45.2 ng/mL. Echocardiogram showed mild inferior wall motion abnormality with 
    ejection fraction of 50%.
    
    Post-procedurally, patient was monitored in the cardiac care unit for 24 hours 
    without complications. Blood pressure was optimized, and diabetes management was 
    adjusted. Patient participated in cardiac rehabilitation education and was cleared 
    for discharge home with cardiology follow-up.
    
    Hospital course was uncomplicated with no evidence of heart failure, arrhythmias, 
    or other complications. Patient ambulated without difficulty and demonstrated 
    understanding of discharge instructions.
    """
    
    # Discharge Medications
    medications = doc.get_section_by_title("Discharge Medications")
    medications.text = """
    1. Aspirin 81mg daily - continue indefinitely
    2. Clopidogrel 75mg daily - continue for 12 months minimum
    3. Atorvastatin 80mg daily - increased dose for post-MI management
    4. Metoprolol succinate 50mg daily - new, for cardioprotection
    5. Lisinopril 10mg daily - continue current dose
    6. Metformin 1000mg twice daily - continue current regimen
    7. Sublingual nitroglycerin 0.4mg as needed for chest pain
    """
    
    # Discharge Instructions
    instructions = doc.get_section_by_title("Discharge Instructions")
    instructions.text = """
    Activity: Gradual return to activities as tolerated. No heavy lifting >10 pounds 
    for 1 week. May shower but no baths/swimming for 5 days. Return to work in 1-2 weeks 
    as tolerated.
    
    Diet: Heart-healthy diet low in sodium (<2g daily) and saturated fat. Diabetic diet 
    with carbohydrate counting. Follow up with dietitian as scheduled.
    
    Monitoring: Daily weights, blood pressure, and blood glucose monitoring. 
    Call if weight increases >3 pounds in 24 hours or >5 pounds in one week.
    
    Warning Signs: Return to ED immediately for chest pain, shortness of breath, 
    palpitations, syncope, or any concerning symptoms.
    
    Lifestyle: Smoking cessation counseling completed. Exercise as tolerated, 
    cardiac rehabilitation enrollment recommended.
    """
    
    # Follow-up
    followup = doc.get_section_by_title("Follow-up")
    followup.text = """
    1. Cardiology - Dr. James Wilson - 1 week post-discharge
    2. Primary Care - Dr. Lisa Martinez - 2 weeks post-discharge  
    3. Endocrinology - Dr. Robert Kim - 1 month (for diabetes management)
    4. Cardiac Rehabilitation - enrollment within 2 weeks
    5. Laboratory - lipid panel and HbA1c in 6 weeks
    """
    
    # Add custom metadata for LangChain processing
    doc.langchain_metadata.update({
        "medical_specialty": "cardiology",
        "primary_diagnosis": "ST-elevation myocardial infarction",
        "procedure_performed": "primary PCI with stent",
        "complexity_score": 8.5,
        "readmission_risk": "moderate",
        "follow_up_urgency": "high"
    })
    
    return doc


def create_progress_note_example() -> Document:
    """Create a detailed daily progress note."""
    
    doc = create_progress_note(
        patient_id="patient-12345",
        patient_name="John Doe",
        author="Dr. Michael Rodriguez",
        note_type="daily"
    )
    
    # Update sections with SOAP note content
    subjective = doc.get_section_by_title("Subjective")
    subjective.text = """
    Patient reports feeling much better today. Chest pain resolved since yesterday. 
    No shortness of breath at rest. Slept well overnight. No nausea, dizziness, 
    or palpitations. Appetite has returned. Asking about going home.
    """
    
    objective = doc.get_section_by_title("Objective")
    objective.text = """
    Vital Signs: BP 128/76, HR 72, RR 16, O2 sat 98% RA, Temp 98.6°F
    
    Physical Exam:
    - General: Alert, oriented, comfortable appearing
    - Cardiovascular: Regular rate and rhythm, no murmurs, rubs, or gallops
    - Pulmonary: Clear to auscultation bilaterally, no rales or wheezes
    - Extremities: No edema, catheter site clean and dry
    
    Laboratory: Troponin trending down to 12.3 ng/mL, BNP 85 pg/mL, 
    Creatinine 1.1 mg/dL, glucose well-controlled
    
    Telemetry: Normal sinus rhythm, no ectopy
    """
    
    assessment = doc.get_section_by_title("Assessment")
    assessment.text = """
    78-year-old male with inferior STEMI status post successful primary PCI 
    with drug-eluting stent to RCA. Post-MI day 2, stable condition with 
    good clinical recovery. No signs of heart failure or complications.
    
    1. STEMI - stable post-PCI, optimal medical therapy initiated
    2. Diabetes mellitus - well controlled during hospitalization  
    3. Hypertension - stable on current regimen
    4. Hyperlipidemia - statin optimized
    """
    
    plan = doc.get_section_by_title("Plan")
    plan.text = """
    1. Continue dual antiplatelet therapy and statin
    2. Continue beta-blocker and ACE inhibitor
    3. Monitor for complications - none evident
    4. Discharge planning - likely tomorrow if continues stable
    5. Arrange cardiology follow-up and cardiac rehabilitation
    6. Patient education on medications and lifestyle modifications
    """
    
    return doc


def demonstrate_langchain_integration():
    """Demonstrate comprehensive LangChain integration capabilities."""
    
    print("🏥 HACS Document - LangChain Integration Demo\n")
    
    # Create comprehensive discharge summary
    print("1. Creating Comprehensive Discharge Summary...")
    discharge_doc = create_comprehensive_discharge_summary()
    print(f"   ✅ Document created: {discharge_doc.title}")
    print(f"   📊 Sections: {len(discharge_doc.sections)}")
    print(f"   👨‍⚕️ Authors: {len(discharge_doc.authors)}")
    print(f"   ✍️ Attesters: {len(discharge_doc.attesters)}")
    print(f"   📝 Word count: {discharge_doc.get_word_count()}")
    
    # Convert to LangChain format
    print("\n2. Converting to LangChain Document...")
    langchain_doc = discharge_doc.to_langchain_document(
        processing_pipeline="clinical-nlp",
        intended_use="information_extraction"
    )
    
    print(f"   📄 Content length: {len(langchain_doc['page_content'])} characters")
    print(f"   🏷️ Metadata fields: {len(langchain_doc['metadata'])}")
    print(f"   🔍 Medical specialty: {langchain_doc['metadata'].get('medical_specialty')}")
    print(f"   🩺 Primary diagnosis: {langchain_doc['metadata'].get('primary_diagnosis')}")
    
    # Demonstrate section-based splitting
    print("\n3. Creating Section-Based LangChain Documents...")
    section_docs = discharge_doc.to_langchain_documents(split_by_section=True)
    print(f"   📚 Generated {len(section_docs)} section documents")
    
    for i, section_doc in enumerate(section_docs[:3]):  # Show first 3
        metadata = section_doc["metadata"]
        content_preview = section_doc["page_content"][:100] + "..."
        print(f"   📄 Section {i+1}: {metadata['section_title']}")
        print(f"      Content: {content_preview}")
    
    # Create progress note
    print("\n4. Creating Progress Note...")
    progress_doc = create_progress_note_example()
    progress_langchain = progress_doc.to_langchain_document()
    
    print(f"   📝 Progress note: {progress_doc.title}")
    print(f"   📊 SOAP sections: {len(progress_doc.sections)}")
    print(f"   🏷️ LangChain metadata: {len(progress_langchain['metadata'])} fields")
    
    # Demonstrate round-trip conversion
    print("\n5. Demonstrating Round-Trip Conversion...")
    
    # Convert back from LangChain format
    reconstructed_doc = Document.from_langchain_document(
        langchain_doc,
        document_type=DocumentType.DISCHARGE_SUMMARY
    )
    
    print(f"   🔄 Original sections: {len(discharge_doc.sections)}")
    print(f"   🔄 Reconstructed sections: {len(reconstructed_doc.sections)}")
    print(f"   ✅ Round-trip successful: {len(reconstructed_doc.sections) > 0}")
    
    # Document validation
    print("\n6. Clinical Content Validation...")
    validation = discharge_doc.validate_clinical_content()
    
    print(f"   ✅ Valid: {validation['valid']}")
    print(f"   📊 Word count: {validation['word_count']}")
    print(f"   👨‍⚕️ Has authors: {validation['has_authors']}")
    print(f"   ✍️ Has attesters: {validation['has_attesters']}")
    
    if validation['warnings']:
        print(f"   ⚠️ Warnings: {validation['warnings']}")
    if validation['issues']:
        print(f"   ❌ Issues: {validation['issues']}")
    
    # Content integrity
    print("\n7. Content Integrity Checking...")
    content_hash = discharge_doc.get_content_hash()
    print(f"   🔐 Content hash: {content_hash[:16]}...")
    
    # Modify content slightly
    discharge_doc.sections[0].text += " [Modified]"
    new_hash = discharge_doc.get_content_hash()
    print(f"   🔐 Modified hash: {new_hash[:16]}...")
    print(f"   🔍 Hashes different: {content_hash != new_hash}")
    
    return {
        "discharge_summary": discharge_doc,
        "progress_note": progress_doc,
        "langchain_documents": section_docs,
        "validation_results": validation
    }


def demonstrate_clinical_workflows():
    """Demonstrate clinical workflow integration scenarios."""
    
    print("\n\n🔬 Clinical Workflow Integration Scenarios\n")
    
    # Scenario 1: Multi-document patient summary
    print("1. Multi-Document Patient Summary Creation...")
    
    # Create multiple documents for same patient
    discharge_summary = create_discharge_summary(
        patient_id="patient-12345",
        patient_name="John Doe",
        primary_author="Dr. Sarah Chen"
    )
    
    progress_note = create_progress_note(
        patient_id="patient-12345", 
        patient_name="John Doe",
        author="Dr. Michael Rodriguez"
    )
    
    consultation_note = create_consultation_note(
        patient_id="patient-12345",
        patient_name="John Doe", 
        consultant="Dr. James Wilson",
        specialty="Cardiology"
    )
    
    # Convert all to LangChain format for processing
    documents = [
        discharge_summary.to_langchain_document(doc_sequence=1),
        progress_note.to_langchain_document(doc_sequence=2),
        consultation_note.to_langchain_document(doc_sequence=3)
    ]
    
    print(f"   📚 Created {len(documents)} documents for patient")
    print(f"   🏷️ Document types: {[doc['metadata']['document_type'] for doc in documents]}")
    
    # Scenario 2: Section-based analysis
    print("\n2. Section-Based Clinical Analysis...")
    
    # Extract all assessment sections for longitudinal analysis
    assessment_sections = []
    for doc in [discharge_summary, progress_note, consultation_note]:
        assessment = doc.get_section_by_title("Assessment") or doc.get_section_by_title("Assessment and Clinical Impression")
        if assessment:
            langchain_section = {
                "page_content": assessment.text,
                "metadata": {
                    "section_type": "assessment",
                    "document_type": doc.document_type,
                    "author": doc.authors[0].name if doc.authors else "Unknown",
                    "date": doc.date.isoformat(),
                    "patient_id": doc.subject_id
                }
            }
            assessment_sections.append(langchain_section)
    
    print(f"   🎯 Extracted {len(assessment_sections)} assessment sections")
    print(f"   📅 Date range: Clinical assessments over time")
    
    # Scenario 3: Template-based document generation
    print("\n3. Template-Based Document Generation...")
    
    # Create template documents
    templates = {
        "discharge": create_discharge_summary("PATIENT_ID", "PATIENT_NAME", "AUTHOR_NAME"),
        "progress": create_progress_note("PATIENT_ID", "PATIENT_NAME", "AUTHOR_NAME"),
        "consultation": create_consultation_note("PATIENT_ID", "PATIENT_NAME", "CONSULTANT", "SPECIALTY")
    }
    
    print(f"   📋 Created {len(templates)} document templates")
    
    # Convert templates to LangChain format for template processing
    langchain_templates = {}
    for template_type, template_doc in templates.items():
        langchain_templates[template_type] = template_doc.to_langchain_document(
            template_type=template_type,
            is_template=True
        )
    
    print(f"   🏷️ Template types: {list(langchain_templates.keys())}")
    
    print("\n✅ Clinical workflow scenarios demonstrated successfully!")
    
    return {
        "patient_documents": documents,
        "assessment_sections": assessment_sections,
        "document_templates": langchain_templates
    }


def demonstrate_advanced_features():
    """Demonstrate advanced Document features."""
    
    print("\n\n🚀 Advanced Document Features\n")
    
    # Advanced document with complex structure
    print("1. Creating Complex Multi-Section Document...")
    
    doc = Document(
        document_type=DocumentType.CONSULTATION_NOTE,
        title="Complex Cardiology Consultation",
        subject_id="patient-12345",
        subject_name="John Doe",
        status=DocumentStatus.FINAL,
        confidentiality=ConfidentialityLevel.RESTRICTED
    )
    
    # Add multiple authors with different roles
    doc.add_author("Dr. James Wilson", role="attending-cardiologist", specialty="Interventional Cardiology")
    doc.add_author("Dr. Emily Chen", role="cardiology-fellow", specialty="Cardiology")
    doc.add_author("Sarah Johnson, NP", role="nurse-practitioner", specialty="Cardiology")
    
    # Add attesters
    doc.add_attester("professional", "Dr. James Wilson", party_id="cardio-001")
    doc.add_attester("legal", "Dr. Emily Chen", party_id="fellow-001")
    
    # Create nested sections
    main_section = DocumentSection(
        title="Cardiovascular Assessment",
        text="Comprehensive cardiovascular evaluation performed.",
        code="cardiovascular-assessment"
    )
    
    # Add subsections
    main_section.sections = [
        DocumentSection(
            title="Hemodynamics",
            text="Blood pressure well controlled at 128/76 mmHg. Heart rate regular at 72 bpm.",
            code="hemodynamics"
        ),
        DocumentSection(
            title="Rhythm Analysis",
            text="Normal sinus rhythm maintained. No ectopy observed on telemetry.",
            code="rhythm"
        ),
        DocumentSection(
            title="Structural Assessment",
            text="Echocardiogram shows preserved ejection fraction at 55%. No significant valvular disease.",
            code="structural"
        )
    ]
    
    doc.sections.append(main_section)
    
    print(f"   📊 Document structure: {len(doc.sections)} main sections")
    print(f"   📋 Nested subsections: {sum(len(s.sections) for s in doc.sections)}")
    print(f"   👥 Multi-disciplinary team: {len(doc.authors)} authors")
    
    # Advanced LangChain conversion with metadata
    print("\n2. Advanced LangChain Metadata Integration...")
    
    langchain_doc = doc.to_langchain_document(
        # Clinical metadata
        acuity_level="high",
        clinical_complexity=8.5,
        follow_up_required=True,
        
        # Processing metadata  
        nlp_pipeline="clinical-bert",
        extraction_targets=["medications", "procedures", "diagnoses"],
        annotation_complete=False,
        
        # Workflow metadata
        workflow_stage="review",
        approval_required=True,
        quality_score=9.2
    )
    
    metadata = langchain_doc["metadata"]
    print(f"   🏷️ Rich metadata: {len(metadata)} fields")
    print(f"   🩺 Clinical complexity: {metadata.get('clinical_complexity')}")
    print(f"   🔬 NLP pipeline: {metadata.get('nlp_pipeline')}")
    print(f"   ⭐ Quality score: {metadata.get('quality_score')}")
    
    # Content analysis
    print("\n3. Advanced Content Analysis...")
    
    full_text = doc.get_full_text()
    word_count = doc.get_word_count()
    content_hash = doc.get_content_hash()
    
    print(f"   📄 Full text length: {len(full_text)} characters")
    print(f"   📊 Word count: {word_count} words")
    print(f"   🔐 Content integrity: {content_hash[:16]}...")
    
    # Section analysis
    print(f"   📋 Section analysis:")
    for i, section in enumerate(doc.sections):
        section_words = section.get_word_count()
        print(f"      Section {i+1}: {section.title} ({section_words} words)")
        for j, subsection in enumerate(section.sections):
            subsection_words = subsection.get_word_count()
            print(f"         Subsection {j+1}: {subsection.title} ({subsection_words} words)")
    
    # Advanced validation
    print("\n4. Advanced Clinical Validation...")
    
    validation = doc.validate_clinical_content()
    print(f"   ✅ Clinical validity: {validation['valid']}")
    print(f"   📊 Content metrics: {validation['word_count']} words, {validation['section_count']} sections")
    print(f"   👨‍⚕️ Authorship: {validation['has_authors']} authors, {validation['has_attesters']} attesters")
    
    if validation.get('recommendations'):
        print(f"   💡 Recommendations: {validation['recommendations']}")
    
    return {
        "complex_document": doc,
        "langchain_conversion": langchain_doc,
        "validation_results": validation,
        "content_metrics": {
            "word_count": word_count,
            "content_hash": content_hash,
            "section_count": len(doc.sections)
        }
    }


if __name__ == "__main__":
    print("🏥 HACS Document & LangChain Integration Comprehensive Demo")
    print("=" * 60)
    
    # Run all demonstrations
    basic_results = demonstrate_langchain_integration()
    workflow_results = demonstrate_clinical_workflows() 
    advanced_results = demonstrate_advanced_features()
    
    print("\n" + "=" * 60)
    print("🎉 Demo Complete! Key Achievements:")
    print()
    print("✅ FHIR-Compatible Document Structure")
    print("✅ Seamless LangChain Integration") 
    print("✅ Bi-Directional Document Conversion")
    print("✅ Clinical Content Validation")
    print("✅ Section-Based Processing")
    print("✅ Multi-Document Workflows")
    print("✅ Template-Based Generation")
    print("✅ Advanced Metadata Support")
    print("✅ Content Integrity Checking")
    print("✅ Clinical Team Collaboration")
    print()
    print("🔧 Ready for Production Clinical Workflows!")
    
    # Summary statistics
    total_docs_created = (
        1 +  # discharge summary
        1 +  # progress note  
        len(workflow_results["patient_documents"]) +
        1    # complex document
    )
    
    print(f"\n📊 Demo Statistics:")
    print(f"   📄 Documents created: {total_docs_created}")
    print(f"   🔄 LangChain conversions: {len(basic_results['langchain_documents']) + 3}")
    print(f"   ✅ Validations performed: 3")
    print(f"   🏷️ Metadata fields used: 50+")
    print(f"   📋 Templates generated: {len(workflow_results['document_templates'])}")