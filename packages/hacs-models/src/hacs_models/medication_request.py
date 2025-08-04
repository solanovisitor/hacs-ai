"""Medication request models - placeholder for now."""
from typing import Literal
from pydantic import Field
from .base_resource import DomainResource
from .types import MedicationRequestStatus

class Dosage(DomainResource):
    resource_type: Literal["Dosage"] = Field(default="Dosage")

class DosageInstruction(DomainResource):
    resource_type: Literal["DosageInstruction"] = Field(default="DosageInstruction")

class MedicationRequest(DomainResource):
    resource_type: Literal["MedicationRequest"] = Field(default="MedicationRequest")
    status: MedicationRequestStatus | None = Field(default=None)