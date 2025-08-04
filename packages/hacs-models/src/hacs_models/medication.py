"""Medication models - placeholder for now."""
from typing import Literal
from pydantic import Field
from .base_resource import DomainResource

class MedicationIngredient(DomainResource):
    resource_type: Literal["MedicationIngredient"] = Field(default="MedicationIngredient")

class Medication(DomainResource):
    resource_type: Literal["Medication"] = Field(default="Medication")