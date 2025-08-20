"""
Medication model for HACS.

This module provides a comprehensive, FHIR-compliant Medication resource model
for pharmaceutical product representation and medication information management.

FHIR R4 Specification:
https://hl7.org/fhir/R4/medication.html
"""

from typing import Any, Literal

from pydantic import Field, field_validator

from .base_resource import DomainResource
from .observation import CodeableConcept
from .types import MedicationStatus, ResourceReference


class MedicationIngredient(DomainResource):
    """
    Active or inactive ingredient in a medication.

    Describes the active or inactive ingredients that make up a medication,
    including strength and concentration information.
    """

    resource_type: Literal["MedicationIngredient"] = Field(default="MedicationIngredient")

    # Coded representation of the ingredient
    item_codeable_concept: CodeableConcept | None = Field(
        default=None, description="The actual ingredient (substance or other medication)"
    )

    # Reference to the ingredient
    item_reference: ResourceReference | None = Field(
        default=None, description="Reference to a Substance or Medication resource"
    )

    # Active ingredient indicator
    is_active: bool | None = Field(default=None, description="Active ingredient indicator")

    # Quantity of ingredient present
    strength: dict[str, Any] | None = Field(
        default=None,
        description="Quantity of ingredient present",
        examples=[
            {
                "numerator": {"value": 500, "unit": "mg", "system": "http://unitsofmeasure.org"},
                "denominator": {
                    "value": 1,
                    "unit": "tablet",
                    "system": "http://unitsofmeasure.org",
                },
            }
        ],
    )


class MedicationBatch(DomainResource):
    """
    Batch information for manufactured medication.

    Information about a group of medication produced or packaged from one
    production run.
    """

    resource_type: Literal["MedicationBatch"] = Field(default="MedicationBatch")

    # Identifier assigned to batch
    lot_number: str | None = Field(
        default=None,
        description="Identifier assigned to batch",
        examples=["LOT123456", "BATCH789"],
        max_length=50,
    )

    # When batch will expire
    expiration_date: str | None = Field(
        default=None,
        description="When batch will expire (YYYY-MM-DD)",
        examples=["2025-12-31", "2024-06-15"],
    )


class Medication(DomainResource):
    """
    Medication resource for pharmaceutical product representation.

    A medication is a pharmaceutical product which may be consumable, injectable
    or other types of product. Used to represent branded products, generic products,
    investigational products, and clinical drugs.

    This resource covers all medications except blood products, which use BiologicallyDerivedProduct.
    """

    resource_type: Literal["Medication"] = Field(default="Medication")

    # Business identifiers
    identifier: list[str] = Field(
        default_factory=list,
        description="Business identifier for this medication",
        examples=[["urn:oid:1.2.3.4.5.6.7.8.9|12345", "NDC:0123-4567-89"]],
    )

    # Codes that identify this medication
    code: CodeableConcept | None = Field(
        default=None,
        description="Codes that identify this medication",
        examples=[
            {
                "coding": [
                    {
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "code": "313782",
                        "display": "Acetaminophen 325 MG Oral Tablet",
                    }
                ],
                "text": "Acetaminophen 325mg tablets",
            }
        ],
    )

    # Status of this medication
    status: MedicationStatus | None = Field(
        default=None, description="Status of this medication (active, inactive, entered-in-error)"
    )

    # Manufacturer of the item
    manufacturer: ResourceReference | None = Field(
        default=None,
        description="Manufacturer of the item",
        examples=["Organization/manufacturer-acme-pharma"],
    )

    # powder | tablets | capsule +
    form: CodeableConcept | None = Field(
        default=None,
        description="Form of the medication (tablet, capsule, liquid, etc.)",
        examples=[
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "421026006",
                        "display": "Oral tablet",
                    }
                ],
                "text": "Tablet",
            }
        ],
    )

    # Amount of drug in package
    amount: dict[str, Any] | None = Field(
        default=None,
        description="Amount of drug in package",
        examples=[
            {
                "numerator": {"value": 100, "unit": "tablets"},
                "denominator": {"value": 1, "unit": "bottle"},
            }
        ],
    )

    # Active or inactive ingredient
    ingredient: list[MedicationIngredient] = Field(
        default_factory=list, description="Active or inactive ingredient"
    )

    # Details about packaged medications
    batch: MedicationBatch | None = Field(
        default=None, description="Details about packaged medications"
    )

    # Additional medication classification
    category: list[CodeableConcept] = Field(
        default_factory=list,
        description="Category or classification of the medication",
        examples=[
            [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/medication-category",
                            "code": "prescription",
                            "display": "Prescription",
                        }
                    ],
                    "text": "Prescription Medication",
                }
            ]
        ],
    )

    # Controlled substance schedule
    schedule: CodeableConcept | None = Field(
        default=None,
        description="Controlled substance schedule",
        examples=[
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-substanceAdminSubstitution",
                        "code": "C-II",
                        "display": "Schedule II",
                    }
                ],
                "text": "Schedule II Controlled Substance",
            }
        ],
    )

    # Strength or concentration
    strength_description: str | None = Field(
        default=None,
        description="Human-readable description of strength/concentration",
        examples=["500mg", "5mg/mL", "10% cream"],
        max_length=100,
    )

    # Special handling requirements
    special_handling: list[CodeableConcept] = Field(
        default_factory=list,
        description="Special handling requirements (refrigeration, light-sensitive, etc.)",
    )

    # NDC (National Drug Code) for US medications
    ndc: str | None = Field(
        default=None,
        description="National Drug Code (US)",
        examples=["0123-4567-89", "12345-678-90"],
        max_length=20,
    )

    # Generic name
    generic_name: str | None = Field(
        default=None,
        description="Generic or non-proprietary name",
        examples=["acetaminophen", "ibuprofen", "lisinopril"],
        max_length=200,
    )

    # Brand or trade name
    brand_name: str | None = Field(
        default=None,
        description="Brand or trade name",
        examples=["Tylenol", "Advil", "Prinivil"],
        max_length=200,
    )

    @field_validator("ndc")
    @classmethod
    def validate_ndc_format(cls, v: str | None) -> str | None:
        """Validate NDC format."""
        if v is None:
            return None

        # Remove any spaces or dashes for validation
        clean_ndc = v.replace("-", "").replace(" ", "")

        # NDC should be 10 or 11 digits
        if not clean_ndc.isdigit() or len(clean_ndc) not in [10, 11]:
            raise ValueError("NDC must be 10 or 11 digits, optionally formatted with dashes")

        return v

    @property
    def is_active(self) -> bool:
        """Check if medication is active."""
        return self.status == MedicationStatus.ACTIVE if self.status else True

    @property
    def is_generic(self) -> bool:
        """Check if this appears to be a generic medication."""
        return bool(self.generic_name and not self.brand_name)

    @property
    def is_branded(self) -> bool:
        """Check if this is a branded medication."""
        return bool(self.brand_name)

    @property
    def is_controlled_substance(self) -> bool:
        """Check if this is a controlled substance."""
        if not self.schedule:
            return False

        if hasattr(self.schedule, "coding") and self.schedule.coding:
            for coding in self.schedule.coding:
                if hasattr(coding, "code") and coding.code:
                    # Look for DEA schedule codes
                    if coding.code.startswith(("C-", "CI", "CII", "CIII", "CIV", "CV")):
                        return True

        return False

    def get_display_name(self) -> str:
        """Get a human-readable display name for the medication."""
        # Prefer brand name if available
        if self.brand_name:
            if self.strength_description:
                return f"{self.brand_name} {self.strength_description}"
            return self.brand_name

        # Fall back to generic name
        if self.generic_name:
            if self.strength_description:
                return f"{self.generic_name} {self.strength_description}"
            return self.generic_name

        # Use coded text if available
        if self.code and hasattr(self.code, "text") and self.code.text:
            return self.code.text

        # Use coded display if available
        if self.code and hasattr(self.code, "coding") and self.code.coding:
            first_coding = self.code.coding[0]
            if hasattr(first_coding, "display") and first_coding.display:
                return first_coding.display

        return f"Medication {self.id or 'Unknown'}"

    def add_ingredient(
        self,
        ingredient_name: str,
        strength_value: float | None = None,
        strength_unit: str | None = None,
        is_active: bool = True,
        **kwargs,
    ) -> MedicationIngredient:
        """Add an ingredient to this medication."""
        ingredient = MedicationIngredient(
            item_codeable_concept=CodeableConcept(text=ingredient_name),
            is_active=is_active,
            **kwargs,
        )

        if strength_value is not None and strength_unit:
            ingredient.strength = {
                "numerator": {
                    "value": strength_value,
                    "unit": strength_unit,
                    "system": "http://unitsofmeasure.org",
                },
                "denominator": {"value": 1, "unit": "dose"},
            }

        self.ingredient.append(ingredient)
        return ingredient

    def add_category(
        self,
        category_code: str,
        category_display: str,
        system: str = "http://terminology.hl7.org/CodeSystem/medication-category",
    ) -> CodeableConcept:
        """Add a category to the medication."""
        category = CodeableConcept(
            text=category_display,
            coding=[{"system": system, "code": category_code, "display": category_display}],
        )
        self.category.append(category)
        return category

    def set_batch_info(
        self, lot_number: str | None = None, expiration_date: str | None = None
    ) -> MedicationBatch:
        """Set batch information for the medication."""
        self.batch = MedicationBatch(lot_number=lot_number, expiration_date=expiration_date)
        return self.batch


# Convenience functions for common medication types


def create_generic_medication(
    generic_name: str, strength: str | None = None, form: str = "tablet", **kwargs
) -> Medication:
    """Create a generic medication."""
    medication = Medication(
        generic_name=generic_name,
        strength_description=strength,
        status=MedicationStatus.ACTIVE,
        **kwargs,
    )

    medication.add_category("generic", "Generic Medication")

    if form:
        medication.form = CodeableConcept(text=form.title())

    return medication


def create_branded_medication(
    brand_name: str,
    generic_name: str | None = None,
    strength: str | None = None,
    form: str = "tablet",
    manufacturer_ref: ResourceReference | None = None,
    **kwargs,
) -> Medication:
    """Create a branded medication."""
    medication = Medication(
        brand_name=brand_name,
        generic_name=generic_name,
        strength_description=strength,
        manufacturer=manufacturer_ref,
        status=MedicationStatus.ACTIVE,
        **kwargs,
    )

    medication.add_category("branded", "Branded Medication")

    if form:
        medication.form = CodeableConcept(text=form.title())

    return medication


def create_controlled_substance(
    name: str, schedule: str, strength: str | None = None, form: str = "tablet", **kwargs
) -> Medication:
    """Create a controlled substance medication."""
    medication = Medication(
        generic_name=name,
        strength_description=strength,
        status=MedicationStatus.ACTIVE,
        schedule=CodeableConcept(
            text=f"Schedule {schedule}",
            coding=[
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-substanceAdminSubstitution",
                    "code": f"C-{schedule}",
                    "display": f"Schedule {schedule}",
                }
            ],
        ),
        **kwargs,
    )

    medication.add_category("controlled", "Controlled Substance")

    if form:
        medication.form = CodeableConcept(text=form.title())

    return medication
