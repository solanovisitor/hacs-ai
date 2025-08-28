"""
CarePlan model for HACS (minimal).

HACS-native, FHIR-inspired CarePlan to represent planned care activities,
goals, and management for a patient. Lightweight with safe defaults.
"""

from typing import Any, Literal

from pydantic import Field

from .base_resource import DomainResource
from .observation import CodeableConcept
from .types import (
    CarePlanIntent,
    CarePlanStatus,
    ResourceReference,
    TimestampStr,
)


class CarePlan(DomainResource):
    resource_type: Literal["CarePlan"] = Field(default="CarePlan")

    # Lifecycle
    status: CarePlanStatus = Field(
        default=CarePlanStatus.ACTIVE,
        description="CarePlan lifecycle status (RequestStatus)",
    )
    intent: CarePlanIntent = Field(
        default=CarePlanIntent.PLAN, description="proposal | plan | order | option | directive"
    )

    # Human readable
    title: str | None = Field(default=None, description="Human-readable title")
    description_text: str | None = Field(default=None, description="Free-text description")
    category: list[CodeableConcept] = Field(
        default_factory=list, description="Type/category of plan"
    )

    # Subject and context
    subject_ref: ResourceReference | None = Field(
        default=None, description="Who the care plan is for (Patient/Group)"
    )
    encounter_ref: ResourceReference | None = Field(
        default=None, description="Encounter during which this CarePlan was created"
    )
    custodian_ref: ResourceReference | None = Field(
        default=None, description="Designated responsible party"
    )
    contributor_refs: list[ResourceReference] = Field(
        default_factory=list, description="Contributors who provided content of the plan"
    )
    care_team_refs: list[ResourceReference] = Field(
        default_factory=list, description="Who is involved in plan?"
    )

    # Relationships
    based_on: list[ResourceReference] = Field(
        default_factory=list,
        description="Fulfills plan, proposal or order",
    )
    replaces: list[ResourceReference] = Field(
        default_factory=list, description="CarePlan replaced by this CarePlan"
    )
    part_of: list[ResourceReference] = Field(
        default_factory=list, description="Part of referenced CarePlan"
    )
    supporting_info_refs: list[ResourceReference] = Field(
        default_factory=list, description="Information considered as part of plan"
    )
    addresses_refs: list[ResourceReference] = Field(
        default_factory=list, description="Health issues this plan addresses (refs)"
    )
    addresses_code: list[CodeableConcept] = Field(
        default_factory=list, description="Health issues this plan addresses (codes)"
    )

    goal_refs: list[ResourceReference] = Field(
        default_factory=list, description="References to Goal resources"
    )

    # Timing
    created: TimestampStr | None = Field(default=None, description="When the plan was created")
    period_start: TimestampStr | None = Field(default=None, description="Start of plan period")
    period_end: TimestampStr | None = Field(default=None, description="End of plan period")

    # Activities
    planned_activity_refs: list[ResourceReference] = Field(
        default_factory=list, description="Activities intended to be part of the care plan"
    )
    performed_activity_refs: list[ResourceReference] = Field(
        default_factory=list, description="Activities that are completed or in progress"
    )
    activity_text: list[str] = Field(
        default_factory=list, description="Planned activities (free text)"
    )
    activity_progress: list[str] = Field(
        default_factory=list, description="Comments about activity status/progress"
    )

    # --- Helpers ---
    def is_active(self) -> bool:
        return self.status == CarePlanStatus.ACTIVE

    def is_completed(self) -> bool:
        return self.status == CarePlanStatus.COMPLETED

    def has_activities(self) -> bool:
        return bool(
            self.planned_activity_refs or self.performed_activity_refs or self.activity_text
        )

    def add_category(self, text: str, code: str | None = None, system: str | None = None) -> None:
        cc = CodeableConcept(text=text)
        if code and system:
            cc.coding = [{"system": system, "code": code, "display": text}]
        self.category.append(cc)

    def add_goal_ref(self, ref: ResourceReference) -> None:
        if ref and ref not in self.goal_refs:
            self.goal_refs.append(ref)

    def add_planned_activity(self, ref: ResourceReference) -> None:
        if ref and ref not in self.planned_activity_refs:
            self.planned_activity_refs.append(ref)

    def add_performed_activity(self, ref: ResourceReference) -> None:
        if ref and ref not in self.performed_activity_refs:
            self.performed_activity_refs.append(ref)

    def add_supporting_info(self, ref: ResourceReference) -> None:
        if ref and ref not in self.supporting_info_refs:
            self.supporting_info_refs.append(ref)

    def add_address_ref(self, ref: ResourceReference) -> None:
        if ref and ref not in self.addresses_refs:
            self.addresses_refs.append(ref)

    def add_address_code(self, text: str, code: str | None = None, system: str | None = None) -> None:
        cc = CodeableConcept(text=text)
        if code and system:
            cc.coding = [{"system": system, "code": code, "display": text}]
        self.addresses_code.append(cc)

    def add_activity_note(self, note: str) -> None:
        if note.strip():
            self.activity_progress.append(note.strip())
            self.update_timestamp()

    def add_note(self, note: str) -> None:  # override DomainResource notes helper semantics
        if note.strip():
            self.note.append(note.strip())
            self.update_timestamp()

    # --- LLM-friendly extractable facade overrides ---
    @classmethod
    def get_extractable_fields(cls) -> list[str]:  # type: ignore[override]
        """Return fields that should be extracted by LLMs (3-4 key fields only)."""
        return [
            "status",
            "title",
            "description_text",
            "category",
        ]

    @classmethod
    def get_canonical_defaults(cls) -> dict[str, Any]:
        """Default values for system/required fields during extraction."""
        return {
            "status": "active",
            "intent": "plan",
            "subject_ref": "Patient/UNKNOWN",
        }

    @classmethod
    def coerce_extractable(cls, payload: dict[str, Any], relax: bool = True) -> dict[str, Any]:
        """Coerce extractable payload to proper CarePlan field types."""
        coerced = payload.copy()
        
        # Handle status string validation
        if "status" in coerced and isinstance(coerced["status"], str):
            status_str = coerced["status"].lower()
            valid_statuses = ["draft", "active", "on-hold", "revoked", "completed", "entered-in-error", "unknown"]
            if status_str not in valid_statuses:
                # Map common variations
                if status_str in ["ativo", "active"]:
                    coerced["status"] = "active"
                elif status_str in ["completo", "finalizado", "completed"]:
                    coerced["status"] = "completed"
                elif status_str in ["rascunho", "draft"]:
                    coerced["status"] = "draft"
                else:
                    coerced["status"] = "active"  # Default fallback
        
        # Handle category - ensure proper CodeableConcept structure
        if "category" in coerced:
            category_data = coerced["category"]
            if isinstance(category_data, str):
                # Convert string to CodeableConcept
                coerced["category"] = [{"text": category_data}]
            elif isinstance(category_data, list):
                processed_categories = []
                for cat_item in category_data:
                    if isinstance(cat_item, str):
                        processed_categories.append({"text": cat_item})
                    elif isinstance(cat_item, dict):
                        processed_categories.append(cat_item)
                coerced["category"] = processed_categories
        
        # Remove system fields that shouldn't be LLM-generated
        system_fields = ["id", "created_at", "updated_at", "version", "meta_tag"]
        for field in system_fields:
            coerced.pop(field, None)
        
        return coerced

    @classmethod
    def llm_hints(cls) -> list[str]:  # type: ignore[override]
        """Provide LLM-specific extraction hints."""
        return [
            "Extract a concise title for the plan when present",
            "Prefer short free-text description over verbose narratives",
            "Include high-level category labels if available",
            "Use 'active' status unless explicitly specified otherwise",
        ]

    @classmethod
    def get_facades(cls) -> dict[str, "FacadeSpec"]:
        """Return available extraction facades for CarePlan."""
        from .base_resource import FacadeSpec
        
        return {
            "basic": FacadeSpec(
                fields=["status", "title", "description_text"],
                required_fields=["status"],
                field_examples={
                    "status": "active",
                    "title": "Diabetes Management Plan",
                    "description_text": "Comprehensive care plan for type 2 diabetes management"
                },
                field_types={
                    "status": "CarePlanStatus",
                    "title": "str | None",
                    "description_text": "str | None"
                },
                description="Essential care plan information and description",
                llm_guidance="Use this facade for extracting basic care plan details from clinical notes. Focus on plan title, status, and general description.",
                conversational_prompts=[
                    "What care plan was established?",
                    "What is the treatment plan?",
                    "What are the care management goals?"
                ]
            ),
            
            "complete": FacadeSpec(
                fields=["status", "title", "description_text", "category"],
                required_fields=["status"],
                field_examples={
                    "status": "active",
                    "title": "Comprehensive Cardiac Rehabilitation Plan",
                    "description_text": "Post-surgical cardiac rehabilitation including exercise, diet, and medication management",
                    "category": [{"text": "cardiac rehabilitation"}, {"text": "post-operative care"}]
                },
                field_types={
                    "status": "CarePlanStatus",
                    "title": "str | None",
                    "description_text": "str | None",
                    "category": "list[CodeableConcept]"
                },
                description="Comprehensive care plan information with categorization",
                llm_guidance="Use for extracting detailed care plan information when comprehensive planning documentation is available, including care categories and classifications.",
                conversational_prompts=[
                    "Can you provide the complete care plan details?",
                    "What are all aspects of the treatment plan?",
                    "Document the full care management approach"
                ]
            )
        }
