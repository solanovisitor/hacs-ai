"""
HACS Tools Descriptions

This module contains comprehensive description constants for all HACS healthcare tools.
These descriptions are used by the @tool decorators to provide rich context for
AI agents working with healthcare data and clinical workflows.

Author: HACS Development Team
License: MIT
Version: 0.3.0
"""

# === RESOURCE MANAGEMENT TOOL DESCRIPTIONS ===

CREATE_HACS_RECORD_DESCRIPTION = """
Create new healthcare resource records with full FHIR compliance validation.

This tool creates structured healthcare data records including Patient demographics, 
clinical Observations, medical Conditions, Procedures, and other FHIR-compliant resources. 
Supports auto-ID generation, clinical validation, and audit trail creation.

Key capabilities:
- Creates Patient, Observation, Encounter, Condition, Medication, and other clinical resources
- Automatic FHIR R4/R5 compliance validation
- Actor-based permissions and audit trail logging
- Auto-generates resource IDs if not provided
- Clinical data validation with healthcare-specific error handling

Healthcare use cases: Patient registration, clinical documentation, care plan creation, 
medical record management, clinical data entry, healthcare workflow automation.
"""

GET_HACS_RECORD_DESCRIPTION = """
Retrieve healthcare resource records by ID with comprehensive audit trail support.

This tool fetches healthcare resource data with proper access control validation,
clinical context preservation, and optional audit trail information for regulatory
compliance. Supports all FHIR resource types with healthcare-specific metadata.

Key capabilities:
- Retrieves Patient, Observation, Encounter, and all clinical resource types
- Actor-based access control with healthcare role validation
- Complete audit trail tracking for HIPAA compliance
- Clinical context preservation and metadata retrieval
- Secure healthcare data access with permission validation

Healthcare use cases: Patient chart review, clinical decision support, care coordination,
medical record access, clinical research data retrieval, quality reporting.
"""

UPDATE_HACS_RECORD_DESCRIPTION = """
Update existing healthcare resource records with clinical validation and audit trails.

This tool modifies healthcare resource data while maintaining FHIR compliance,
preserving clinical integrity, and creating comprehensive audit trails for
regulatory requirements and clinical governance.

Key capabilities:
- Updates Patient demographics, clinical observations, and medical conditions
- FHIR compliance validation for all healthcare data modifications
- Clinical data integrity checks and validation rules
- Actor-based permissions with healthcare role verification
- Complete audit trail with before/after change tracking

Healthcare use cases: Patient information updates, clinical data corrections,
care plan modifications, medication adjustments, clinical workflow updates.
"""

DELETE_HACS_RECORD_DESCRIPTION = """
Delete healthcare resource records with compliance-aware soft delete and audit preservation.

This tool removes healthcare resource data while maintaining compliance with healthcare
data retention requirements, preserving audit trails, and supporting both soft and
hard deletion patterns based on clinical and regulatory needs.

Key capabilities:
- Soft delete (recommended) preserves data for compliance and audit requirements
- Hard delete for non-clinical data where appropriate
- Healthcare data retention policy compliance
- Complete audit trail preservation for regulatory requirements
- Actor-based permissions with healthcare role validation

Healthcare use cases: Patient data archival, clinical record cleanup, GDPR compliance,
healthcare data lifecycle management, clinical workflow optimization.
"""

SEARCH_HACS_RECORDS_DESCRIPTION = """
Search healthcare resource records with advanced clinical filtering and FHIR-compliant queries.

This tool performs complex searches across healthcare resource data with support for
clinical search patterns, FHIR-compliant filtering, semantic search capabilities,
and healthcare-specific result ranking.

Key capabilities:
- Advanced search across Patient, Observation, Condition, and all clinical resources
- Clinical search patterns (ICD-10, SNOMED CT, LOINC code searches)
- FHIR-compliant query filters and sorting
- Healthcare-specific result ranking and relevance scoring
- Actor-based access control with clinical context filtering

Healthcare use cases: Patient cohort identification, clinical research queries, care gap analysis,
population health analytics, clinical decision support, quality measure reporting.
"""

# === CLINICAL WORKFLOW TOOL DESCRIPTIONS ===

EXECUTE_CLINICAL_WORKFLOW_DESCRIPTION = """
Execute structured clinical workflows using FHIR PlanDefinition specifications.

This tool runs healthcare protocols and clinical workflows with proper tracking of
execution steps, clinical outcomes, decision points, and compliance requirements.
Supports complex care pathways, clinical guidelines, and treatment protocols.

Key capabilities:
- Executes FHIR PlanDefinition-based clinical workflows and care pathways
- Tracks clinical decision points and treatment outcomes
- Monitors compliance with clinical guidelines and quality measures
- Generates clinical recommendations and next steps
- Patient-specific workflow execution with context preservation

Healthcare use cases: Care pathway automation, clinical protocol execution, treatment
plan implementation, care coordination workflows, clinical decision support automation.
"""

GET_CLINICAL_GUIDANCE_DESCRIPTION = """
Generate AI-powered clinical decision support and evidence-based guidance.

This tool provides evidence-based clinical recommendations using healthcare knowledge
bases, clinical guidelines, patient-specific context, and medical literature to
support informed clinical decision making.

Key capabilities:
- Evidence-based clinical recommendations with confidence scoring
- Patient-specific clinical context analysis and personalized guidance
- Integration with clinical knowledge bases and medical literature
- Contraindication detection and alternative treatment suggestions
- Clinical urgency assessment and follow-up recommendations

Healthcare use cases: Clinical decision support, treatment recommendations, medication
guidance, diagnostic assistance, care planning support, clinical consultation aid.
"""

QUERY_WITH_DATAREQUIREMENT_DESCRIPTION = """
Execute structured healthcare data queries using FHIR DataRequirement specifications.

This tool performs complex clinical data queries with FHIR-compliant filtering,
aggregation capabilities, and clinical insight generation for decision support,
quality reporting, and population health analytics.

Key capabilities:
- FHIR DataRequirement-based structured healthcare queries
- Clinical data aggregation and population health analytics
- Quality measure calculation and clinical indicator reporting
- Patient cohort analysis and care gap identification
- Clinical insights generation from healthcare data patterns

Healthcare use cases: Quality reporting, population health analysis, clinical research
queries, care gap analysis, performance measurement, clinical quality improvement.
"""

VALIDATE_CLINICAL_PROTOCOL_DESCRIPTION = """
Validate clinical protocols and care pathways for compliance and clinical best practices.

This tool performs comprehensive validation of clinical protocols against healthcare
standards, regulatory requirements, evidence-based guidelines, and best practice
recommendations to ensure clinical safety and effectiveness.

Key capabilities:
- Clinical protocol structure and completeness validation
- Healthcare compliance checking against regulatory standards
- Evidence-based guideline validation and recommendation checking
- Clinical decision point validation and care pathway verification
- Quality assurance for clinical workflow design

Healthcare use cases: Clinical protocol development, care pathway validation, quality
assurance for clinical guidelines, regulatory compliance checking, clinical governance.
"""

# === MEMORY OPERATIONS TOOL DESCRIPTIONS ===

CREATE_HACS_MEMORY_DESCRIPTION = """
Store structured memories for healthcare AI agents with clinical context preservation.

This tool creates episodic, procedural, and executive memories that preserve clinical
context, enable sophisticated retrieval for healthcare decision support, and support
AI agent learning from clinical experiences and knowledge.

Key capabilities:
- Multi-type memory storage (episodic clinical experiences, procedural protocols, executive decisions)
- Clinical context preservation with patient-specific and specialty-specific categorization
- Confidence scoring and clinical accuracy tracking
- Integration with clinical knowledge bases and medical literature
- HIPAA-compliant memory storage with audit trails

Healthcare use cases: Clinical experience capture, medical knowledge retention, treatment
protocol learning, diagnostic pattern recognition, clinical decision support enhancement.
"""

SEARCH_HACS_MEMORIES_DESCRIPTION = """
Search healthcare AI agent memories using semantic similarity and clinical context.

This tool performs semantic search across stored clinical memories to find relevant
medical knowledge, treatment procedures, and clinical experiences for informed
decision support and evidence-based care recommendations.

Key capabilities:
- Semantic search across clinical memories with medical terminology understanding
- Clinical context filtering (specialty, patient type, condition, treatment)
- Confidence-based memory retrieval with clinical relevance scoring
- Multi-type memory search (episodic, procedural, executive)
- Healthcare-specific search patterns and medical concept matching

Healthcare use cases: Clinical decision support, treatment protocol retrieval, diagnostic
assistance, medical knowledge lookup, clinical experience sharing, evidence-based recommendations.
"""

CONSOLIDATE_MEMORIES_DESCRIPTION = """
Consolidate related healthcare memories to enhance clinical knowledge and reduce redundancy.

This tool combines similar clinical memories to create more comprehensive medical
knowledge representations while preserving important clinical nuances, treatment
variations, and patient-specific considerations.

Key capabilities:
- Semantic clustering of related clinical memories and medical knowledge
- Clinical knowledge consolidation with medical accuracy preservation
- Treatment protocol merging with variation and exception handling
- Clinical experience synthesis with outcome correlation
- Medical knowledge graph enhancement and relationship mapping

Healthcare use cases: Clinical knowledge base optimization, medical protocol enhancement,
treatment guideline consolidation, clinical experience synthesis, medical education content creation.
"""

RETRIEVE_CONTEXT_DESCRIPTION = """
Retrieve contextual clinical memories for comprehensive healthcare decision support.

This tool gathers relevant clinical memories, treatment protocols, and patient context
to provide comprehensive background information for informed clinical decision making
and evidence-based care planning.

Key capabilities:
- Patient-specific clinical context retrieval with comprehensive medical history
- Contextual clinical memory gathering for decision support
- Treatment protocol and guideline context assembly
- Clinical experience and outcome context for similar cases
- Temporal clinical context with historical pattern analysis

Healthcare use cases: Clinical decision support, patient case review, treatment planning,
care coordination, clinical consultation preparation, medical education case studies.
"""

ANALYZE_MEMORY_PATTERNS_DESCRIPTION = """
Analyze patterns in healthcare AI agent memory usage and clinical knowledge gaps.

This tool provides insights into clinical memory utilization, identifies medical
knowledge gaps, analyzes learning patterns, and generates recommendations to
optimize healthcare AI agent performance and clinical decision support capabilities.

Key capabilities:
- Clinical memory usage pattern analysis and optimization recommendations
- Medical knowledge gap identification and learning opportunity assessment
- Clinical decision pattern analysis and improvement suggestions
- Healthcare specialty knowledge distribution analysis
- AI agent performance optimization for clinical applications

Healthcare use cases: Clinical AI optimization, medical knowledge assessment, healthcare
training needs analysis, clinical decision support improvement, medical education enhancement.
"""

# === VECTOR SEARCH TOOL DESCRIPTIONS ===

STORE_EMBEDDING_DESCRIPTION = """
Store healthcare content as vector embeddings optimized for clinical semantic search.

This tool converts clinical text, medical literature, treatment protocols, and
healthcare documentation into vector embeddings optimized for medical terminology,
clinical concepts, and healthcare-specific semantic relationships.

Key capabilities:
- Healthcare-optimized embedding generation for clinical text and medical content
- Medical terminology and clinical concept vector representation
- HIPAA-compliant vector storage with clinical metadata preservation
- Clinical context categorization and specialty-specific indexing
- Integration with medical knowledge bases and clinical literature

Healthcare use cases: Clinical literature indexing, medical knowledge base creation,
treatment protocol embedding, clinical documentation search, medical education content organization.
"""

VECTOR_SIMILARITY_SEARCH_DESCRIPTION = """
Perform semantic similarity search on healthcare vector embeddings for clinical information retrieval.

This tool searches clinical vector embeddings using semantic similarity to find
medically relevant content based on clinical meaning, medical concepts, and
healthcare context rather than exact text matching.

Key capabilities:
- Clinical semantic search with medical terminology understanding
- Healthcare concept matching and clinical relationship identification
- Medical literature and clinical guideline semantic retrieval
- Clinical context filtering by specialty, condition, or treatment type
- Relevance scoring based on clinical significance and medical accuracy

Healthcare use cases: Medical literature search, clinical guideline retrieval, treatment
protocol discovery, diagnostic assistance, clinical research support, medical education content finding.
"""

VECTOR_HYBRID_SEARCH_DESCRIPTION = """
Perform hybrid search combining keyword and semantic vector search for comprehensive clinical retrieval.

This tool combines traditional medical keyword search with semantic vector search
to provide comprehensive clinical information retrieval, covering both exact
medical terminology matches and conceptual healthcare relationships.

Key capabilities:
- Hybrid clinical search combining exact medical term matching with semantic understanding
- Weighted combination of keyword and semantic relevance for optimal clinical results
- Medical terminology and clinical concept integrated search
- Clinical context filtering and healthcare specialty-specific results
- Comprehensive medical literature and clinical guideline coverage

Healthcare use cases: Comprehensive medical research, clinical guideline discovery, treatment
protocol identification, diagnostic support, medical education content retrieval, clinical decision support.
"""

GET_VECTOR_COLLECTION_STATS_DESCRIPTION = """
Get comprehensive statistics and analytics for healthcare vector collections.

This tool provides detailed analytics about clinical vector collections including
medical specialty distribution, embedding quality metrics, clinical content
coverage, and healthcare-specific usage patterns for optimization.

Key capabilities:
- Clinical vector collection analytics with medical specialty breakdown
- Healthcare content distribution analysis and clinical coverage assessment
- Medical terminology embedding quality metrics and clinical accuracy scoring
- Clinical usage pattern analysis and optimization recommendations
- Healthcare compliance and data quality assessment for clinical collections

Healthcare use cases: Clinical knowledge base optimization, medical content analysis,
healthcare AI performance monitoring, clinical data quality assessment, medical education analytics.
"""

OPTIMIZE_VECTOR_COLLECTION_DESCRIPTION = """
Optimize healthcare vector collections for improved clinical search performance and medical accuracy.

This tool performs optimization operations on clinical vector collections to improve
medical search quality, reduce storage requirements, enhance clinical relevance,
and optimize for healthcare-specific search patterns and medical workflows.

Key capabilities:
- Clinical vector collection optimization for medical search performance
- Healthcare-specific indexing and medical terminology clustering
- Clinical relevance scoring enhancement and medical accuracy optimization
- Medical knowledge graph optimization and clinical relationship enhancement
- Healthcare compliance optimization and clinical data governance

Healthcare use cases: Clinical search optimization, medical knowledge base enhancement,
healthcare AI performance improvement, clinical data management, medical education platform optimization.
"""

# === SCHEMA DISCOVERY TOOL DESCRIPTIONS ===

DISCOVER_HACS_RESOURCES_DESCRIPTION = """
Discover all available HACS healthcare resources with comprehensive medical metadata and clinical context.

This tool helps healthcare AI agents understand available clinical resources,
their medical purposes, FHIR compliance status, clinical applications, and
healthcare-specific capabilities for informed resource selection and usage.

Key capabilities:
- Complete healthcare resource catalog with medical specialty categorization
- FHIR compliance assessment and clinical standard validation
- Medical use case identification and clinical application mapping
- Healthcare resource capability analysis and clinical workflow integration
- Clinical metadata extraction and medical context documentation

Healthcare use cases: Healthcare system integration, clinical workflow design, medical
application development, FHIR implementation planning, clinical data modeling, healthcare AI architecture.
"""

GET_HACS_RESOURCE_SCHEMA_DESCRIPTION = """
Get comprehensive schema information for healthcare resources with clinical context and FHIR compliance details.

This tool provides detailed JSON schema definitions for healthcare resources
including medical field types, clinical validation rules, FHIR compliance
information, and healthcare-specific usage patterns.

Key capabilities:
- Detailed healthcare resource schema with medical field documentation
- FHIR compliance information and clinical standard alignment
- Medical validation rules and healthcare data quality requirements
- Clinical context documentation and medical use case examples
- Healthcare integration guidance and clinical implementation support

Healthcare use cases: Healthcare application development, clinical data integration, FHIR
implementation, medical system design, clinical workflow integration, healthcare API development.
"""

ANALYZE_RESOURCE_FIELDS_DESCRIPTION = """
Perform detailed analysis of healthcare resource fields for clinical usage optimization.

This tool analyzes individual fields within healthcare resources, providing insights
about clinical significance, FHIR requirements, medical validation needs, and
optimization recommendations for healthcare AI agent interactions.

Key capabilities:
- Clinical field significance analysis and medical relevance scoring
- FHIR compliance requirements and healthcare standard validation
- Medical terminology analysis and clinical concept mapping
- Healthcare AI optimization recommendations for clinical field usage
- Clinical workflow integration guidance and medical use case recommendations

Healthcare use cases: Clinical data modeling, healthcare AI optimization, medical application
design, FHIR implementation planning, clinical workflow optimization, healthcare system integration.
"""

COMPARE_RESOURCE_SCHEMAS_DESCRIPTION = """
Compare schemas between healthcare resource types for clinical integration and medical workflow analysis.

This tool performs detailed comparison between healthcare resource schemas to
identify clinical relationships, medical data integration opportunities, and
healthcare workflow optimization possibilities.

Key capabilities:
- Clinical resource schema comparison with medical relationship identification
- Healthcare data integration analysis and clinical workflow mapping
- Medical field compatibility assessment and clinical data harmonization
- FHIR resource relationship analysis and healthcare standard alignment
- Clinical workflow integration recommendations and medical use case optimization

Healthcare use cases: Healthcare system integration, clinical workflow design, medical data
harmonization, FHIR implementation planning, clinical decision support optimization, healthcare AI architecture.
"""

# === DEVELOPMENT TOOL DESCRIPTIONS ===

CREATE_RESOURCE_STACK_DESCRIPTION = """
Create sophisticated healthcare resource stacks by layering multiple clinical resources for comprehensive medical workflows.

This advanced tool enables building complex clinical data structures by stacking
healthcare resources, creating comprehensive patient views, integrated care plans,
and sophisticated medical workflow templates for healthcare AI applications.

Key capabilities:
- Multi-resource healthcare stacking with clinical relationship preservation
- Comprehensive patient view creation with integrated medical data
- Clinical workflow template generation with care pathway integration
- Medical data composition with FHIR compliance and healthcare standard alignment
- Healthcare resource dependency management with clinical context preservation

Healthcare use cases: Comprehensive patient dashboards, integrated care plans, clinical
workflow templates, medical record composition, healthcare data integration, clinical decision support enhancement.
"""

CREATE_CLINICAL_TEMPLATE_DESCRIPTION = """
Generate pre-configured clinical templates for common healthcare scenarios and medical workflows.

This tool creates ready-to-use healthcare resource compositions for typical clinical
workflows, medical procedures, and healthcare scenarios, eliminating manual field
selection and ensuring clinical best practices and medical standard compliance.

Key capabilities:
- Clinical template generation for common medical scenarios (assessment, intake, discharge, consultation)
- Medical specialty-specific templates (cardiology, emergency, mental health, pediatric)
- SOAP note templates with structured clinical documentation
- Healthcare workflow templates with clinical decision support integration
- FHIR-compliant template generation with medical standard validation

Healthcare use cases: Clinical documentation templates, medical workflow automation, healthcare
form generation, clinical assessment tools, medical procedure templates, care plan creation.
"""

OPTIMIZE_RESOURCE_FOR_LLM_DESCRIPTION = """
Optimize healthcare resources for AI/LLM interactions through intelligent clinical field selection.

This tool automatically selects the most AI-friendly and clinically relevant fields
from healthcare resources based on medical optimization goals, clinical use cases,
and healthcare AI agent requirements for enhanced performance.

Key capabilities:
- AI-optimized healthcare field selection with clinical relevance prioritization
- Medical terminology optimization for LLM understanding and clinical accuracy
- Healthcare use case-specific optimization (clinical classification, medical extraction, diagnostic validation)
- Clinical context preservation with medical accuracy and FHIR compliance
- Healthcare AI agent interaction optimization with medical workflow enhancement

Healthcare use cases: Healthcare AI optimization, clinical decision support enhancement, medical
chatbot development, clinical documentation automation, healthcare workflow optimization, medical education AI.
"""

# === FHIR INTEGRATION TOOL DESCRIPTIONS ===

CONVERT_TO_FHIR_DESCRIPTION = """
Convert healthcare resource data to FHIR-compliant format with comprehensive validation.

This tool converts HACS resource data or other healthcare formats (HL7v2, CCD, custom)
to FHIR-compliant JSON representation with proper resource structure, terminology
mapping, and compliance validation for healthcare interoperability.

Key capabilities:
- Multi-format healthcare data conversion to FHIR R4/R5 standards
- Medical terminology mapping and clinical concept transformation
- FHIR compliance validation and healthcare standard alignment
- Metadata generation and clinical provenance tracking
- Healthcare interoperability optimization and data harmonization

Healthcare use cases: EHR integration, healthcare data migration, FHIR implementation,
clinical data exchange, medical record conversion, healthcare system interoperability.
"""

VALIDATE_FHIR_COMPLIANCE_DESCRIPTION = """
Validate FHIR resource compliance against healthcare standards and regulatory requirements.

This tool performs comprehensive FHIR compliance validation including structure
validation, terminology checking, cardinality rules, and healthcare-specific
business rules validation for regulatory compliance and data quality assurance.

Key capabilities:
- Complete FHIR structure and schema validation against R4/R5 specifications
- Medical terminology and code system validation with healthcare standards
- Clinical business rules validation and healthcare compliance checking
- Healthcare data quality assessment and error reporting
- Regulatory compliance validation for healthcare standards and requirements

Healthcare use cases: FHIR implementation validation, healthcare compliance auditing,
clinical data quality assurance, regulatory submission preparation, healthcare system certification.
"""

PROCESS_FHIR_BUNDLE_DESCRIPTION = """
Process FHIR Bundle operations for bulk healthcare data transactions and operations.

This tool handles comprehensive FHIR Bundle processing including transaction bundles,
batch operations, search result bundles, and bulk data operations with validation,
error handling, and healthcare-specific transaction management.

Key capabilities:
- FHIR Bundle transaction and batch operation processing
- Bulk healthcare data import/export and clinical record management
- Healthcare transaction validation and clinical data integrity checking
- FHIR operation outcome generation and error handling
- Clinical workflow bundle processing and care coordination support

Healthcare use cases: Bulk clinical data import, healthcare system integration, 
FHIR transaction processing, clinical care coordination, medical record bulk operations.
"""

LOOKUP_FHIR_TERMINOLOGY_DESCRIPTION = """
Lookup and validate FHIR terminology codes and healthcare code systems.

This tool provides comprehensive terminology lookup capabilities for FHIR code systems
including SNOMED CT, LOINC, ICD-10, CPT, and other healthcare terminologies with
validation, hierarchy exploration, and multi-language support.

Key capabilities:
- Comprehensive medical terminology lookup across major healthcare code systems
- Clinical concept hierarchy exploration and relationship mapping
- Multi-language terminology support and clinical translation services
- Medical code validation and healthcare terminology compliance checking
- Clinical concept synonyms and alternative term identification

Healthcare use cases: Clinical coding support, medical terminology validation, 
healthcare documentation assistance, clinical decision support, medical education tools.
"""

# === HEALTHCARE ANALYTICS TOOL DESCRIPTIONS ===

CALCULATE_QUALITY_MEASURES_DESCRIPTION = """
Calculate clinical quality measures for comprehensive healthcare performance monitoring.

This tool computes clinical quality measures such as HEDIS, CMS, MIPS, and custom
quality indicators for patient populations with benchmarking, trending, and
improvement opportunity identification for quality improvement programs.

Key capabilities:
- Clinical quality measure calculation across HEDIS, CMS, MIPS, and custom measures
- Healthcare performance benchmarking and comparative analytics
- Quality improvement opportunity identification and intervention recommendations
- Population health quality assessment and care gap analysis
- Healthcare outcomes measurement and performance trending

Healthcare use cases: Quality reporting and compliance, healthcare performance improvement,
clinical outcomes measurement, regulatory quality reporting, population health management.
"""

ANALYZE_POPULATION_HEALTH_DESCRIPTION = """
Analyze population health patterns, trends, and outcomes for comprehensive healthcare management.

This tool performs comprehensive population health analysis including demographic
patterns, clinical outcomes, social determinants of health, and health equity
assessment for population health management and community health improvement.

Key capabilities:
- Comprehensive population health analytics and demographic analysis
- Social determinants of health assessment and community health factors
- Health equity gap identification and disparity analysis
- Clinical outcomes analysis and population health trending
- Community health insights and public health intervention recommendations

Healthcare use cases: Population health management, community health assessment,
health equity initiatives, public health planning, healthcare resource allocation.
"""

GENERATE_CLINICAL_DASHBOARD_DESCRIPTION = """
Generate interactive clinical dashboards for comprehensive healthcare performance monitoring.

This tool creates customized clinical dashboards with key performance indicators,
quality metrics, patient outcomes, and real-time alerts for healthcare
professionals and administrators with specialty-specific and role-based customization.

Key capabilities:
- Customized clinical dashboard generation with role-based and specialty-specific views
- Real-time healthcare performance monitoring and clinical alerts
- Key performance indicator tracking and quality metrics visualization
- Clinical workflow optimization and healthcare operational insights
- Interactive healthcare analytics and decision support visualization

Healthcare use cases: Clinical performance monitoring, healthcare administration dashboards,
quality improvement tracking, clinical workflow optimization, healthcare executive reporting.
"""

PERFORM_RISK_STRATIFICATION_DESCRIPTION = """
Perform patient risk stratification and predictive analytics for proactive healthcare management.

This tool analyzes comprehensive patient data to identify high-risk individuals,
predict clinical outcomes, and recommend targeted interventions for care management
and population health improvement with machine learning and clinical intelligence.

Key capabilities:
- Advanced patient risk stratification using predictive analytics and clinical intelligence
- High-risk patient identification and clinical outcome prediction
- Targeted intervention recommendations and care management optimization
- Clinical decision support for proactive care and preventive medicine
- Population health risk analysis and healthcare resource optimization

Healthcare use cases: Care management programs, preventive care initiatives, 
clinical decision support, population health improvement, healthcare cost management.
""" 