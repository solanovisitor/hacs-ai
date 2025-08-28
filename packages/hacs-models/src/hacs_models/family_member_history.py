"""
FamilyMemberHistory model for HACS (lightweight).

Captures significant conditions in family members relevant to patient care.
"""

from typing import Any, Literal

from pydantic import Field

from .base_resource import DomainResource


class FamilyMemberHistory(DomainResource):
    resource_type: Literal["FamilyMemberHistory"] = Field(default="FamilyMemberHistory")

    status: str = Field(
        default="completed", description="partial | completed | entered-in-error | health-unknown"
    )
    patient_ref: str | None = Field(default=None, description="Patient reference")
    relationship_text: str | None = Field(
        default=None, description="Relationship (e.g., mother, father, aunt)"
    )
    name: str | None = Field(default=None, description="Family member name (optional)")
    sex: str | None = Field(default=None, description="male | female | other | unknown")
    condition_text: str | None = Field(default=None, description="Condition summary (free text)")
    outcome_text: str | None = Field(default=None, description="Outcome summary (free text)")
    contributed_to_death: bool | None = Field(
        default=None, description="Whether the condition contributed to death"
    )

    # --- LLM-friendly extractable facade overrides ---
    @classmethod
    def get_extractable_fields(cls) -> list[str]:  # type: ignore[override]
        """Return fields that should be extracted by LLMs (3-4 key fields only)."""
        return [
            "relationship_text",
            "condition_text",
            "outcome_text",
        ]

    @classmethod
    def get_extraction_examples(cls) -> dict[str, Any]:
        """Return extraction examples showing different extractable field scenarios."""
        # Mother with cancer history
        mother_example = {
            "relationship_text": "mãe",
            "condition_text": "câncer de mama",
            "outcome_text": "faleceu aos 65 anos",
        }

        # Father with diabetes
        father_example = {
            "relationship_text": "pai",
            "condition_text": "diabetes tipo 2",
        }

        # Sibling with living condition
        sibling_example = {
            "relationship_text": "irmão",
            "condition_text": "hipertensão",
            "outcome_text": "controlada com medicação",
        }

        return {
            "object": mother_example,
            "array": [mother_example, father_example, sibling_example],
            "scenarios": {
                "deceased": mother_example,
                "living": father_example,
                "controlled": sibling_example,
            }
        }

    @classmethod
    def llm_hints(cls) -> list[str]:  # type: ignore[override]
        """Return LLM-specific extraction hints for FamilyMemberHistory."""
        return [
            "Extract family history when relatives' conditions are mentioned",
            "Use relationship_text for family relationship (e.g., 'mother', 'father')",
            "Use condition_text for the medical condition or problem",
        ]
