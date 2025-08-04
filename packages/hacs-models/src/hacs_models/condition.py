"""Condition model - placeholder for now."""
from typing import Literal
from pydantic import Field
from .base_resource import DomainResource
from .types import ConditionClinicalStatus, ConditionVerificationStatus

class ConditionStage(DomainResource):
    resource_type: Literal["ConditionStage"] = Field(default="ConditionStage")

class ConditionEvidence(DomainResource):
    resource_type: Literal["ConditionEvidence"] = Field(default="ConditionEvidence")

class Condition(DomainResource):
    resource_type: Literal["Condition"] = Field(default="Condition")
    clinical_status: ConditionClinicalStatus | None = Field(default=None)
    verification_status: ConditionVerificationStatus | None = Field(default=None)