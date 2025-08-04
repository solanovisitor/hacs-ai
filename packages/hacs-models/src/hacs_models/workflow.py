"""Workflow models - placeholder for now."""
from typing import Literal
from pydantic import Field
from .base_resource import BaseResource

class WorkflowStep(BaseResource):
    resource_type: Literal["WorkflowStep"] = Field(default="WorkflowStep")

class WorkflowAction(BaseResource):
    resource_type: Literal["WorkflowAction"] = Field(default="WorkflowAction")

class WorkflowDefinition(BaseResource):
    resource_type: Literal["WorkflowDefinition"] = Field(default="WorkflowDefinition")