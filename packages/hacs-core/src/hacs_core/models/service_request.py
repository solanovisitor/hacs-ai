"""
HACS ServiceRequest Model - FHIR R4 Compliant

This module implements the FHIR R4 ServiceRequest resource with full compliance
to the healthcare interoperability standard. The ServiceRequest resource represents
a record of a request for service such as diagnostic investigations, treatments,
or operations to be performed.

FHIR R4 ServiceRequest Resource:
https://hl7.org/fhir/R4/servicerequest.html

Key Features:
- Full FHIR R4 compliance with all 40+ fields
- Comprehensive validation rules and constraints (2 FHIR rules)
- Support for ordering procedures, diagnostics, and services
- Complex order details and parameters support
- LLM-friendly fields for AI applications
- Clinical workflow integration support
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from ..base_resource import BaseResource


class RequestStatus(str, Enum):
    """FHIR R4 Request Status codes."""
    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on-hold"
    REVOKED = "revoked"
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"


class RequestIntent(str, Enum):
    """FHIR R4 Request Intent codes."""
    PROPOSAL = "proposal"
    PLAN = "plan"
    DIRECTIVE = "directive"
    ORDER = "order"
    ORIGINAL_ORDER = "original-order"
    REFLEX_ORDER = "reflex-order"
    FILLER_ORDER = "filler-order"
    INSTANCE_ORDER = "instance-order"
    OPTION = "option"


class RequestPriority(str, Enum):
    """FHIR R4 Request Priority codes."""
    ROUTINE = "routine"
    URGENT = "urgent"
    ASAP = "asap"
    STAT = "stat"


class ServiceCategory(str, Enum):
    """Service request category codes."""
    LABORATORY = "laboratory"
    IMAGING = "imaging"
    PATHOLOGY = "pathology"
    RADIOLOGY = "radiology"
    CARDIOLOGY = "cardiology"
    DERMATOLOGY = "dermatology"
    ENDOCRINOLOGY = "endocrinology"
    GASTROENTEROLOGY = "gastroenterology"
    NEUROLOGY = "neurology"
    ONCOLOGY = "oncology"
    OPHTHALMOLOGY = "ophthalmology"
    ORTHOPEDICS = "orthopedics"
    PSYCHIATRY = "psychiatry"
    PULMONOLOGY = "pulmonology"
    SURGERY = "surgery"
    THERAPY = "therapy"
    CONSULTATION = "consultation"
    REFERRAL = "referral"
    SCREENING = "screening"
    PROCEDURE = "procedure"


class PerformerRole(str, Enum):
    """Performer role types."""
    PHYSICIAN = "physician"
    NURSE = "nurse"
    TECHNICIAN = "technician"
    THERAPIST = "therapist"
    SPECIALIST = "specialist"
    CONSULTANT = "consultant"
    RADIOLOGIST = "radiologist"
    PATHOLOGIST = "pathologist"
    SURGEON = "surgeon"
    ANESTHESIOLOGIST = "anesthesiologist"
    PHARMACIST = "pharmacist"
    SOCIAL_WORKER = "social-worker"
    COUNSELOR = "counselor"


class ServiceRequestOrderDetail(BaseModel):
    """Additional order information for service request."""
    parameter_focus: Optional[dict[str, Any]] = Field(
        None, description="The context of the order details by reference"
    )
    parameter: list["ServiceRequestParameter"] = Field(
        ..., description="The parameter details for the service being requested"
    )

    # LLM-friendly fields
    detail_description: Optional[str] = Field(
        None, description="Human-readable description of order details"
    )
    special_instructions: Optional[str] = Field(
        None, description="Special instructions for this order"
    )


class ServiceRequestParameter(BaseModel):
    """Parameter details for the service being requested."""
    code: dict[str, Any] = Field(
        ..., description="The detail of the order being requested"
    )

    # Value choice type - only one should be present
    value_quantity: Optional[dict[str, Any]] = Field(
        None, description="Quantity value for the parameter"
    )
    value_ratio: Optional[dict[str, Any]] = Field(
        None, description="Ratio value for the parameter"
    )
    value_range: Optional[dict[str, Any]] = Field(
        None, description="Range value for the parameter"
    )
    value_boolean: Optional[bool] = Field(
        None, description="Boolean value for the parameter"
    )
    value_codeable_concept: Optional[dict[str, Any]] = Field(
        None, description="Coded value for the parameter"
    )
    value_string: Optional[str] = Field(
        None, description="String value for the parameter"
    )
    value_period: Optional[dict[str, Any]] = Field(
        None, description="Period value for the parameter"
    )

    # LLM-friendly fields
    parameter_name: Optional[str] = Field(
        None, description="Human-readable parameter name"
    )
    parameter_value_display: Optional[str] = Field(
        None, description="Human-readable parameter value"
    )


class ServiceRequestPatientInstruction(BaseModel):
    """Patient or consumer-oriented instructions."""
    instruction_markdown: Optional[str] = Field(
        None, description="Instructions in markdown format"
    )
    instruction_reference: Optional[dict[str, Any]] = Field(
        None, description="Reference to instruction document"
    )

    # LLM-friendly fields
    instruction_summary: Optional[str] = Field(
        None, description="Summary of patient instructions"
    )
    is_critical: Optional[bool] = Field(
        None, description="Whether these instructions are critical"
    )


class ServiceRequest(BaseResource):
    """
    FHIR R4 ServiceRequest Resource

    A record of a request for service such as diagnostic investigations,
    treatments, or operations to be performed.
    """

    resource_type: Literal["ServiceRequest"] = Field(
        default="ServiceRequest", description="Resource type identifier"
    )

    # FHIR R4 Core Fields
    identifier: Optional[list[dict[str, Any]]] = Field(
        None, description="Identifiers assigned to this order"
    )
    instantiates_canonical: Optional[list[str]] = Field(
        None, description="Instantiates FHIR protocol or definition"
    )
    instantiates_uri: Optional[list[str]] = Field(
        None, description="Instantiates external protocol or definition"
    )
    based_on: Optional[list[dict[str, Any]]] = Field(
        None, description="What request fulfills"
    )
    replaces: Optional[list[dict[str, Any]]] = Field(
        None, description="What request replaces"
    )
    requisition: Optional[dict[str, Any]] = Field(
        None, description="Composite Request ID"
    )
    status: RequestStatus = Field(
        ..., description="Current status of the service request"
    )
    intent: RequestIntent = Field(
        ..., description="Intent of the service request"
    )
    category: Optional[list[dict[str, Any]]] = Field(
        None, description="Classification of service"
    )
    priority: Optional[RequestPriority] = Field(
        None, description="Priority of the request"
    )
    do_not_perform: Optional[bool] = Field(
        None, description="True if service/procedure should not be performed"
    )
    code: Optional[dict[str, Any]] = Field(
        None, description="What is being requested/ordered"
    )
    order_detail: Optional[list[ServiceRequestOrderDetail]] = Field(
        None, description="Additional order information"
    )

    # Quantity choice type
    quantity_quantity: Optional[dict[str, Any]] = Field(
        None, description="Service amount as quantity"
    )
    quantity_ratio: Optional[dict[str, Any]] = Field(
        None, description="Service amount as ratio"
    )
    quantity_range: Optional[dict[str, Any]] = Field(
        None, description="Service amount as range"
    )

    subject: dict[str, Any] = Field(
        ..., description="Individual or Entity the service is ordered for"
    )
    focus: Optional[list[dict[str, Any]]] = Field(
        None, description="What the service request is about"
    )
    encounter: Optional[dict[str, Any]] = Field(
        None, description="Encounter in which the request was created"
    )

    # Occurrence choice type
    occurrence_date_time: Optional[datetime] = Field(
        None, description="When service should occur (specific date/time)"
    )
    occurrence_period: Optional[dict[str, Any]] = Field(
        None, description="When service should occur (period)"
    )
    occurrence_timing: Optional[dict[str, Any]] = Field(
        None, description="When service should occur (timing)"
    )

    # As needed choice type
    as_needed_boolean: Optional[bool] = Field(
        None, description="Service is as needed (boolean)"
    )
    as_needed_codeable_concept: Optional[dict[str, Any]] = Field(
        None, description="Preconditions for service (coded)"
    )

    authored_on: Optional[datetime] = Field(
        None, description="Date request signed"
    )
    requester: Optional[dict[str, Any]] = Field(
        None, description="Who/what is requesting service"
    )
    performer_type: Optional[dict[str, Any]] = Field(
        None, description="Performer role"
    )
    performer: Optional[list[dict[str, Any]]] = Field(
        None, description="Requested performer"
    )
    location: Optional[list[dict[str, Any]]] = Field(
        None, description="Requested location"
    )
    reason: Optional[list[dict[str, Any]]] = Field(
        None, description="Explanation/Justification for procedure or service"
    )
    insurance: Optional[list[dict[str, Any]]] = Field(
        None, description="Associated insurance coverage"
    )
    supporting_info: Optional[list[dict[str, Any]]] = Field(
        None, description="Additional clinical information"
    )
    specimen: Optional[list[dict[str, Any]]] = Field(
        None, description="Procedure Samples"
    )
    body_site: Optional[list[dict[str, Any]]] = Field(
        None, description="Coded location on Body"
    )
    body_structure: Optional[dict[str, Any]] = Field(
        None, description="BodyStructure-based location on the body"
    )
    note: Optional[list[dict[str, Any]]] = Field(
        None, description="Comments"
    )
    patient_instruction: Optional[list[ServiceRequestPatientInstruction]] = Field(
        None, description="Patient or consumer-oriented instructions"
    )
    relevant_history: Optional[list[dict[str, Any]]] = Field(
        None, description="Request provenance"
    )

    # LLM-friendly fields
    service_name: Optional[str] = Field(
        None, description="Human-readable service name"
    )
    service_description: Optional[str] = Field(
        None, description="Description of the requested service"
    )
    urgency_level: Optional[str] = Field(
        None, description="Urgency description"
    )
    expected_duration: Optional[str] = Field(
        None, description="Expected duration of the service"
    )
    preparation_required: Optional[bool] = Field(
        None, description="Whether patient preparation is required"
    )
    preparation_instructions: Optional[str] = Field(
        None, description="Patient preparation instructions"
    )
    clinical_indication: Optional[str] = Field(
        None, description="Clinical reason for the request"
    )
    ordering_provider_name: Optional[str] = Field(
        None, description="Name of the ordering provider"
    )
    performing_department: Optional[str] = Field(
        None, description="Department that will perform the service"
    )
    estimated_cost: Optional[str] = Field(
        None, description="Estimated cost of the service"
    )
    requires_authorization: Optional[bool] = Field(
        None, description="Whether prior authorization is required"
    )
    contraindications: Optional[list[str]] = Field(
        None, description="Known contraindications for this service"
    )
    expected_outcomes: Optional[list[str]] = Field(
        None, description="Expected outcomes from the service"
    )

    def __init__(self, **data):
        if "id" not in data:
            data["id"] = str(uuid.uuid4())
        if "authored_on" not in data:
            data["authored_on"] = datetime.now(timezone.utc)
        super().__init__(**data)

    @field_validator("authored_on", "occurrence_date_time")
    @classmethod
    def validate_datetime_timezone(cls, v):
        """Ensure datetime fields are timezone-aware."""
        if v and isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @model_validator(mode="after")
    def validate_service_request_constraints(self) -> "ServiceRequest":
        """Validate FHIR R4 service request constraints."""

        # Rule bdystr-1: bodyStructure SHALL only be present if bodySite is not present
        if self.body_site and self.body_structure:
            raise ValueError("bodyStructure SHALL only be present if bodySite is not present")

        # Rule prr-1: orderDetail SHALL only be present if code is present
        if self.order_detail and not self.code:
            raise ValueError("orderDetail SHALL only be present if code is present")

        return self

    # Helper properties
    @property
    def display_name(self) -> str:
        """Human-readable display name for the service request."""
        if self.service_name:
            return self.service_name

        if isinstance(self.code, dict) and self.code.get("text"):
            return self.code["text"]
        elif isinstance(self.code, dict) and self.code.get("coding"):
            coding = self.code["coding"][0] if self.code["coding"] else {}
            return coding.get("display", coding.get("code", "Unknown Service"))

        return "Service Request"

    @property
    def status_display(self) -> str:
        """Human-readable status display."""
        status_map = {
            RequestStatus.DRAFT: "Draft",
            RequestStatus.ACTIVE: "Active",
            RequestStatus.ON_HOLD: "On Hold",
            RequestStatus.REVOKED: "Revoked",
            RequestStatus.COMPLETED: "Completed",
            RequestStatus.ENTERED_IN_ERROR: "Entered in Error",
            RequestStatus.UNKNOWN: "Unknown Status"
        }
        return status_map.get(self.status, str(self.status))

    @property
    def intent_display(self) -> str:
        """Human-readable intent display."""
        intent_map = {
            RequestIntent.PROPOSAL: "Proposal",
            RequestIntent.PLAN: "Plan",
            RequestIntent.DIRECTIVE: "Directive",
            RequestIntent.ORDER: "Order",
            RequestIntent.ORIGINAL_ORDER: "Original Order",
            RequestIntent.REFLEX_ORDER: "Reflex Order",
            RequestIntent.FILLER_ORDER: "Filler Order",
            RequestIntent.INSTANCE_ORDER: "Instance Order",
            RequestIntent.OPTION: "Option"
        }
        return intent_map.get(self.intent, str(self.intent))

    @property
    def priority_display(self) -> str:
        """Human-readable priority display."""
        if not self.priority:
            return "Routine"

        priority_map = {
            RequestPriority.ROUTINE: "Routine",
            RequestPriority.URGENT: "Urgent",
            RequestPriority.ASAP: "ASAP",
            RequestPriority.STAT: "STAT"
        }
        return priority_map.get(self.priority, str(self.priority))

    @property
    def urgency_description(self) -> str:
        """Get urgency description based on priority."""
        if self.urgency_level:
            return self.urgency_level

        if not self.priority:
            return "Standard scheduling - no special urgency"

        urgency_descriptions = {
            RequestPriority.ROUTINE: "Standard scheduling - no special urgency",
            RequestPriority.URGENT: "Should be performed within 24-48 hours",
            RequestPriority.ASAP: "Should be performed as soon as possible",
            RequestPriority.STAT: "Immediate - perform within 1 hour"
        }
        return urgency_descriptions.get(self.priority, "Standard scheduling")

    # Helper methods
    def is_active(self) -> bool:
        """Check if the service request is currently active."""
        return self.status == RequestStatus.ACTIVE

    def is_completed(self) -> bool:
        """Check if the service request is completed."""
        return self.status == RequestStatus.COMPLETED

    def is_urgent(self) -> bool:
        """Check if the service request is urgent."""
        return self.priority in [RequestPriority.URGENT, RequestPriority.ASAP, RequestPriority.STAT]

    def is_stat(self) -> bool:
        """Check if the service request is STAT priority."""
        return self.priority == RequestPriority.STAT

    def requires_preparation(self) -> bool:
        """Check if patient preparation is required."""
        if self.preparation_required is not None:
            return self.preparation_required

        # Check if there are patient instructions
        return bool(self.patient_instruction and len(self.patient_instruction) > 0)

    def get_service_category(self) -> Optional[str]:
        """Get the primary service category."""
        if not self.category or len(self.category) == 0:
            return None

        primary_category = self.category[0]
        if isinstance(primary_category, dict):
            if primary_category.get("text"):
                return primary_category["text"]
            elif primary_category.get("coding"):
                coding = primary_category["coding"][0] if primary_category["coding"] else {}
                return coding.get("display", coding.get("code"))

        return None

    def get_ordering_provider(self) -> Optional[str]:
        """Get the ordering provider name."""
        if self.ordering_provider_name:
            return self.ordering_provider_name

        if isinstance(self.requester, dict):
            if self.requester.get("display"):
                return self.requester["display"]
            elif self.requester.get("reference"):
                return self.requester["reference"]

        return None

    def get_target_performer(self) -> Optional[str]:
        """Get the target performer name."""
        if not self.performer or len(self.performer) == 0:
            return None

        primary_performer = self.performer[0]
        if isinstance(primary_performer, dict):
            if primary_performer.get("display"):
                return primary_performer["display"]
            elif primary_performer.get("reference"):
                return primary_performer["reference"]

        return None

    def get_clinical_reasons(self) -> list[str]:
        """Get list of clinical reasons for the request."""
        reasons = []

        if self.clinical_indication:
            reasons.append(self.clinical_indication)

        if self.reason:
            for reason in self.reason:
                if isinstance(reason, dict):
                    if reason.get("text"):
                        reasons.append(reason["text"])
                    elif reason.get("coding"):
                        coding = reason["coding"][0] if reason["coding"] else {}
                        if coding.get("display"):
                            reasons.append(coding["display"])

        return reasons

    def get_body_sites(self) -> list[str]:
        """Get list of body sites for the procedure."""
        sites = []

        if self.body_site:
            for site in self.body_site:
                if isinstance(site, dict):
                    if site.get("text"):
                        sites.append(site["text"])
                    elif site.get("coding"):
                        coding = site["coding"][0] if site["coding"] else {}
                        if coding.get("display"):
                            sites.append(coding["display"])

        return sites

    def get_patient_instructions(self) -> list[str]:
        """Get list of patient instructions."""
        instructions = []

        if self.preparation_instructions:
            instructions.append(self.preparation_instructions)

        if self.patient_instruction:
            for instruction in self.patient_instruction:
                if instruction.instruction_summary:
                    instructions.append(instruction.instruction_summary)
                elif instruction.instruction_markdown:
                    instructions.append(instruction.instruction_markdown)

        return instructions

    def get_order_parameters(self) -> list[dict[str, Any]]:
        """Get structured order parameters."""
        parameters = []

        if self.order_detail:
            for detail in self.order_detail:
                for param in detail.parameter:
                    param_info = {
                        "name": param.parameter_name or "Unknown Parameter",
                        "value": param.parameter_value_display or "Not specified",
                        "code": param.code
                    }
                    parameters.append(param_info)

        return parameters

    def has_contraindications(self) -> bool:
        """Check if there are known contraindications."""
        return bool(self.contraindications and len(self.contraindications) > 0)

    def requires_authorization_check(self) -> bool:
        """Check if prior authorization is required."""
        return bool(self.requires_authorization)

    def get_occurrence_timing(self) -> Optional[str]:
        """Get human-readable occurrence timing."""
        if self.occurrence_date_time:
            return self.occurrence_date_time.strftime("%Y-%m-%d %H:%M")
        elif self.occurrence_period and isinstance(self.occurrence_period, dict):
            start = self.occurrence_period.get("start", "")
            end = self.occurrence_period.get("end", "")
            if start and end:
                return f"Between {start} and {end}"
            elif start:
                return f"Starting {start}"
            elif end:
                return f"Before {end}"
        elif self.occurrence_timing and isinstance(self.occurrence_timing, dict):
            # This would need more complex parsing of FHIR Timing
            return "Complex timing specified"

        return None

    def to_order_summary(self) -> dict[str, Any]:
        """Convert to order summary format."""
        return {
            "id": self.id,
            "service": self.display_name,
            "status": self.status_display,
            "intent": self.intent_display,
            "priority": self.priority_display,
            "urgency": self.urgency_description,
            "category": self.get_service_category(),
            "ordering_provider": self.get_ordering_provider(),
            "target_performer": self.get_target_performer(),
            "clinical_reasons": self.get_clinical_reasons(),
            "body_sites": self.get_body_sites(),
            "timing": self.get_occurrence_timing(),
            "patient_instructions": self.get_patient_instructions(),
            "requires_preparation": self.requires_preparation(),
            "requires_authorization": self.requires_authorization_check(),
            "contraindications": self.contraindications or [],
            "authored_on": self.authored_on.isoformat() if self.authored_on else None,
        }

    def to_clinical_summary(self) -> dict[str, Any]:
        """Convert to clinical summary format."""
        return {
            "service_request_id": self.id,
            "service": {
                "name": self.display_name,
                "description": self.service_description,
                "category": self.get_service_category(),
                "code": self.code,
            },
            "workflow": {
                "status": self.status_display,
                "intent": self.intent_display,
                "priority": self.priority_display,
                "is_urgent": self.is_urgent(),
                "is_active": self.is_active(),
                "authored_on": self.authored_on.isoformat() if self.authored_on else None,
            },
            "clinical_context": {
                "reasons": self.get_clinical_reasons(),
                "body_sites": self.get_body_sites(),
                "contraindications": self.contraindications or [],
                "supporting_info": self.supporting_info,
            },
            "providers": {
                "ordering_provider": self.get_ordering_provider(),
                "target_performer": self.get_target_performer(),
                "performing_department": self.performing_department,
            },
            "logistics": {
                "timing": self.get_occurrence_timing(),
                "expected_duration": self.expected_duration,
                "requires_preparation": self.requires_preparation(),
                "preparation_instructions": self.get_patient_instructions(),
                "requires_authorization": self.requires_authorization_check(),
                "estimated_cost": self.estimated_cost,
            },
            "parameters": self.get_order_parameters(),
        }

    def to_patient_summary(self) -> dict[str, Any]:
        """Convert to patient-friendly summary."""
        return {
            "service_name": self.display_name,
            "description": self.service_description or "Medical service requested by your provider",
            "why_needed": self.get_clinical_reasons(),
            "when_scheduled": self.get_occurrence_timing(),
            "urgency": self.urgency_description,
            "preparation_needed": self.requires_preparation(),
            "instructions": self.get_patient_instructions(),
            "where_performed": self.get_body_sites(),
            "ordering_doctor": self.get_ordering_provider(),
            "performing_department": self.performing_department,
            "estimated_duration": self.expected_duration,
            "estimated_cost": self.estimated_cost,
            "requires_authorization": self.requires_authorization_check(),
            "contraindications": self.contraindications or [],
            "expected_outcomes": self.expected_outcomes or [],
            "status": self.status_display,
        }


# Type aliases for different service request contexts
DiagnosticOrder = ServiceRequest
ProcedureRequest = ServiceRequest
ReferralRequest = ServiceRequest
TherapyOrder = ServiceRequest
ConsultationRequest = ServiceRequest