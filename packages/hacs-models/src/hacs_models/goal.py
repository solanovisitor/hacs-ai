"""Goal models - placeholder for now."""
from typing import Literal
from pydantic import Field
from .base_resource import DomainResource
from .types import GoalLifecycleStatus

class GoalTarget(DomainResource):
    resource_type: Literal["GoalTarget"] = Field(default="GoalTarget")

class Goal(DomainResource):
    resource_type: Literal["Goal"] = Field(default="Goal")
    lifecycle_status: GoalLifecycleStatus | None = Field(default=None)