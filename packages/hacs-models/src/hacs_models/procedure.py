"""Procedure models - placeholder for now."""
from typing import Literal
from pydantic import Field
from .base_resource import DomainResource
from .types import ProcedureStatus

class ProcedurePerformer(DomainResource):
    resource_type: Literal["ProcedurePerformer"] = Field(default="ProcedurePerformer")

class ProcedureFocalDevice(DomainResource):
    resource_type: Literal["ProcedureFocalDevice"] = Field(default="ProcedureFocalDevice")

class Procedure(DomainResource):
    resource_type: Literal["Procedure"] = Field(default="Procedure")
    status: ProcedureStatus | None = Field(default=None)