"""
ServiceRequest model for HACS.

This module provides a FHIR R4-compliant ServiceRequest resource model,
which is essential for care coordination and clinical workflows.

FHIR R4 Specification:
https://hl7.org/fhir/R4/servicerequest.html
"""

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator

from .base_resource import DomainResource
from .observation import CodeableConcept, Quantity
from .types import (
    ResourceReference,
    ServiceRequestIntent,
    ServiceRequestPriority,
    ServiceRequestStatus,
    TimestampStr,
)


class ServiceRequest(DomainResource):
    """
    ServiceRequest resource for care coordination.

    A record of a request for service such as diagnostic investigations,
    treatments, or operations to be performed.
    """

    resource_type: Literal["ServiceRequest"] = Field(
        default="ServiceRequest",
        description="Resource type identifier"
    )

    # Business identifiers
    identifier: list[str] = Field(
        default_factory=list,
        description="External identifiers for this item"
    )

    # Canonical URL for instantiated protocol
    instantiates_canonical: list[str] = Field(
        default_factory=list,
        description="Instantiates FHIR protocol or definition"
    )

    # URL for instantiated protocol
    instantiates_uri: list[str] = Field(
        default_factory=list,
        description="Instantiates external protocol or definition"
    )

    # Based on reference
    based_on: list[ResourceReference] = Field(
        default_factory=list,
        description="What request fulfills"
    )

    # Replaces reference
    replaces: list[ResourceReference] = Field(
        default_factory=list,
        description="What request replaces"
    )

    # Requisition/grouper id
    requisition: str | None = Field(
        None,
        description="Composite Request ID"
    )

    # Status of the request
    status: ServiceRequestStatus = Field(
        description="Draft | active | on-hold | revoked | completed | entered-in-error | unknown"
    )

    # Intent of the request
    intent: ServiceRequestIntent = Field(
        description="Proposal | plan | directive | order | original-order | reflex-order | filler-order | instance-order | option"
    )

    # Classification of service
    category: list[CodeableConcept] = Field(
        default_factory=list,
        description="Classification of service"
    )

    # Priority of the request
    priority: ServiceRequestPriority | None = Field(
        None,
        description="Routine | urgent | asap | stat"
    )

    # True if service/procedure should not be performed
    do_not_perform: bool | None = Field(
        None,
        description="True if service/procedure should not be performed"
    )

    # What is being requested/ordered
    code: CodeableConcept | None = Field(
        None,
        description="What is being requested/ordered"
    )

    # Order details
    order_detail: list[CodeableConcept] = Field(
        default_factory=list,
        description="Additional order information"
    )

    # Service quantity
    quantity_quantity: Quantity | None = Field(
        None,
        description="Service amount as quantity"
    )

    # Service ratio
    quantity_ratio: str | None = Field(
        None,
        description="Service amount as ratio"
    )

    # Service range
    quantity_range: str | None = Field(
        None,
        description="Service amount as range"
    )

    # Individual or entity the service is ordered for
    subject: ResourceReference = Field(
        description="Individual or entity the service is ordered for"
    )

    # Encounter in which the request was created
    encounter: ResourceReference | None = Field(
        None,
        description="Encounter in which the request was created"
    )

    # When service should occur
    occurrence_datetime: TimestampStr | None = Field(
        None,
        description="When service should occur"
    )

    # When service should occur (period)
    occurrence_period: str | None = Field(
        None,
        description="When service should occur (period)"
    )

    # When service should occur (timing)
    occurrence_timing: str | None = Field(
        None,
        description="When service should occur (timing)"
    )

    # If request is calling patient back for additional procedure
    as_needed_boolean: bool | None = Field(
        None,
        description="Preconditions for service"
    )

    # Preconditions for service
    as_needed_codeable_concept: CodeableConcept | None = Field(
        None,
        description="Preconditions for service"
    )

    # Date request signed
    authored_on: TimestampStr | None = Field(
        None,
        description="Date request signed"
    )

    # Who/what is requesting service
    requester: ResourceReference | None = Field(
        None,
        description="Who/what is requesting service"
    )

    # Performer role
    performer_type: CodeableConcept | None = Field(
        None,
        description="Performer role"
    )

    # Requested performer
    performer: list[ResourceReference] = Field(
        default_factory=list,
        description="Requested performer"
    )

    # Requested location
    location_code: list[CodeableConcept] = Field(
        default_factory=list,
        description="Requested location"
    )

    # Requested location reference
    location_reference: list[ResourceReference] = Field(
        default_factory=list,
        description="Requested location reference"
    )

    # Explanation/Justification for procedure or service
    reason_code: list[CodeableConcept] = Field(
        default_factory=list,
        description="Explanation/Justification for procedure or service"
    )

    # Explanation/Justification for service or service
    reason_reference: list[ResourceReference] = Field(
        default_factory=list,
        description="Explanation/Justification for service or service"
    )

    # Associated insurance coverage
    insurance: list[ResourceReference] = Field(
        default_factory=list,
        description="Associated insurance coverage"
    )

    # Additional clinical information
    supporting_info: list[ResourceReference] = Field(
        default_factory=list,
        description="Additional clinical information"
    )

    # Specimen collection details
    specimen: list[ResourceReference] = Field(
        default_factory=list,
        description="Procedure Samples"
    )

    # Location on Body
    body_site: list[CodeableConcept] = Field(
        default_factory=list,
        description="Location on Body"
    )

    # Comments
    note: list[str] = Field(
        default_factory=list,
        description="Comments"
    )

    # Patient or consumer-oriented instructions
    patient_instruction: str | None = Field(
        None,
        description="Patient or consumer-oriented instructions"
    )

    # What request fulfills
    relevant_history: list[ResourceReference] = Field(
        default_factory=list,
        description="Request provenance"
    )

    @field_validator('subject')
    @classmethod
    def validate_subject_reference(cls, v):
        """Validate subject reference format."""
        if v and not any(v.startswith(prefix) for prefix in [
            'Patient/', 'Group/', 'Location/', 'Device/', 'urn:uuid:'
        ]):
            raise ValueError(
                "Subject reference must start with valid resource type or 'urn:uuid:'"
            )
        return v

    @field_validator('status')
    @classmethod
    def validate_status_required(cls, v):
        """Ensure status is provided."""
        if not v:
            raise ValueError("Status is required for ServiceRequest")
        return v

    @field_validator('intent')
    @classmethod
    def validate_intent_required(cls, v):
        """Ensure intent is provided."""
        if not v:
            raise ValueError("Intent is required for ServiceRequest")
        return v

    @property
    def is_active(self) -> bool:
        """Check if service request is currently active."""
        return self.status == ServiceRequestStatus.ACTIVE

    @property
    def is_draft(self) -> bool:
        """Check if service request is in draft status."""
        return self.status == ServiceRequestStatus.DRAFT

    @property
    def is_completed(self) -> bool:
        """Check if service request is completed."""
        return self.status == ServiceRequestStatus.COMPLETED

    @property
    def is_urgent(self) -> bool:
        """Check if service request has urgent priority."""
        return self.priority in [
            ServiceRequestPriority.URGENT,
            ServiceRequestPriority.ASAP,
            ServiceRequestPriority.STAT
        ]

    def get_display_name(self) -> str:
        """Get a human-readable display name for the service request."""
        if self.code and hasattr(self.code, 'text') and self.code.text:
            return self.code.text
        elif self.code and hasattr(self.code, 'coding') and self.code.coding:
            # Try to get display from first coding
            first_coding = self.code.coding[0] if self.code.coding else None
            if first_coding and hasattr(first_coding, 'display'):
                return first_coding.display
        return f"Service Request {self.id or 'Unknown'}"

    def add_note(self, note: str) -> None:
        """Add a note to this service request."""
        if note and note not in self.note:
            self.note.append(note)

    def add_reason_code(self, reason: CodeableConcept) -> None:
        """Add a reason code to this service request."""
        if reason and reason not in self.reason_code:
            self.reason_code.append(reason)


# Convenience functions for common service request types

def create_lab_request(
    subject_ref: ResourceReference,
    test_code: CodeableConcept,
    status: ServiceRequestStatus = ServiceRequestStatus.DRAFT,
    intent: ServiceRequestIntent = ServiceRequestIntent.ORDER,
    priority: ServiceRequestPriority = ServiceRequestPriority.ROUTINE,
    **kwargs
) -> ServiceRequest:
    """Create a laboratory test service request."""
    return ServiceRequest(
        subject=subject_ref,
        status=status,
        intent=intent,
        priority=priority,
        code=test_code,
        category=[CodeableConcept(text="Laboratory")],
        **kwargs
    )


def create_imaging_request(
    subject_ref: ResourceReference,
    imaging_code: CodeableConcept,
    status: ServiceRequestStatus = ServiceRequestStatus.DRAFT,
    intent: ServiceRequestIntent = ServiceRequestIntent.ORDER,
    priority: ServiceRequestPriority = ServiceRequestPriority.ROUTINE,
    **kwargs
) -> ServiceRequest:
    """Create an imaging service request."""
    return ServiceRequest(
        subject=subject_ref,
        status=status,
        intent=intent,
        priority=priority,
        code=imaging_code,
        category=[CodeableConcept(text="Imaging")],
        **kwargs
    )


def create_referral_request(
    subject_ref: ResourceReference,
    specialty_code: CodeableConcept,
    status: ServiceRequestStatus = ServiceRequestStatus.ACTIVE,
    intent: ServiceRequestIntent = ServiceRequestIntent.ORDER,
    priority: ServiceRequestPriority = ServiceRequestPriority.ROUTINE,
    **kwargs
) -> ServiceRequest:
    """Create a specialist referral service request."""
    return ServiceRequest(
        subject=subject_ref,
        status=status,
        intent=intent,
        priority=priority,
        code=specialty_code,
        category=[CodeableConcept(text="Referral")],
        **kwargs
    )