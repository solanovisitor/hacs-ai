from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class Reference(BaseModel):
    """
    Minimal FHIR-style Reference type used to point from one resource to another.

    Fields:
      - reference: Literal reference string (e.g., "Patient/123", relative/absolute URL, or internal "#id")
      - type: Type the reference refers to (e.g., "Patient")
      - identifier: Logical reference payload when literal reference is not known
      - display: Text alternative for the resource
    """

    model_config = ConfigDict(extra="forbid")

    reference: Optional[str] = Field(default=None, description="Literal reference string (Type/id or URL)")
    type: Optional[str] = Field(default=None, description="Type of the referenced resource, e.g., 'Patient'")
    identifier: Optional[dict[str, Any]] = Field(default=None, description="Logical reference when literal is unknown")
    display: Optional[str] = Field(default=None, description="Text representation for display")


