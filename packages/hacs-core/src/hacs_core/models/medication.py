"""
Medication model based on FHIR US Core Medication Profile.

This model represents medications with comprehensive drug information,
optimized for structured outputs and LLM interactions.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from ..base_resource import BaseResource
from pydantic import Field


class MedicationStatus(str, Enum):
    """Status of the medication."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ENTERED_IN_ERROR = "entered-in-error"


class MedicationForm(str, Enum):
    """Form of the medication."""

    TABLET = "tablet"
    CAPSULE = "capsule"
    LIQUID = "liquid"
    INJECTION = "injection"
    CREAM = "cream"
    OINTMENT = "ointment"
    PATCH = "patch"
    INHALER = "inhaler"
    DROPS = "drops"
    SPRAY = "spray"
    POWDER = "powder"
    GEL = "gel"
    SUPPOSITORY = "suppository"


class Medication(BaseResource):
    """
    Represents a medication.

    Based on FHIR US Core Medication Profile with HACS enhancements.
    Optimized for structured outputs and LLM interactions.
    """

    resource_type: Literal["Medication"] = Field(
        default="Medication", description="Resource type identifier"
    )

    # Identifiers
    identifier: list[dict[str, Any]] = Field(
        default_factory=list, description="Business identifier for this medication"
    )

    # Code - required in US Core
    code: dict[str, Any] = Field(description="Codes that identify this medication")

    # LLM-FRIENDLY: Simple medication name
    medication_name: str | None = Field(
        default=None,
        description="Common name of the medication",
        examples=["Lisinopril", "Metformin", "Amoxicillin", "Aspirin", "Ibuprofen"],
    )

    brand_name: str | None = Field(
        default=None,
        description="Brand or trade name",
        examples=["Tylenol", "Advil", "Lipitor", "Zestril", "Glucophage"],
    )

    generic_name: str | None = Field(
        default=None,
        description="Generic or chemical name",
        examples=[
            "Acetaminophen",
            "Ibuprofen",
            "Atorvastatin",
            "Lisinopril",
            "Metformin",
        ],
    )

    status: MedicationStatus | None = Field(
        default=None,
        description="A code to indicate if the medication is in active use",
    )

    manufacturer: str | None = Field(
        default=None,
        description="Manufacturer of the medication",
        examples=["Pfizer", "Johnson & Johnson", "Merck", "Generic manufacturer"],
    )

    # Form
    form: dict[str, Any] | None = Field(
        default=None, description="powder | tablets | capsule +"
    )

    # LLM-FRIENDLY: Simple form
    dosage_form: MedicationForm | None = Field(
        default=None, description="Physical form of the medication"
    )

    # Amount
    amount: dict[str, Any] | None = Field(
        default=None, description="Amount of drug in package"
    )

    # LLM-FRIENDLY: Simple amount description
    package_size: str | None = Field(
        default=None,
        description="Size of the package",
        examples=["30 tablets", "100ml bottle", "1 inhaler", "90 day supply"],
    )

    # Ingredients
    ingredient: list[dict[str, Any]] = Field(
        default_factory=list, description="Active or inactive ingredient"
    )

    # LLM-FRIENDLY: Simple ingredients
    active_ingredients: list[str] = Field(
        default_factory=list,
        description="List of active ingredients",
        examples=[
            ["Lisinopril 10mg"],
            ["Acetaminophen 500mg", "Caffeine 65mg"],
            ["Amoxicillin 250mg"],
        ],
    )

    inactive_ingredients: list[str] = Field(
        default_factory=list, description="List of inactive ingredients or excipients"
    )

    # Batch information
    batch: dict[str, Any] | None = Field(
        default=None, description="Details about packaged medications"
    )

    lot_number: str | None = Field(default=None, description="Lot or batch number")

    expiration_date: datetime | None = Field(
        default=None, description="When this specific batch expires"
    )

    # HACS-specific enhancements
    drug_class: str | None = Field(
        default=None,
        description="Therapeutic class of the medication",
        examples=[
            "ACE Inhibitor",
            "Beta Blocker",
            "Antibiotic",
            "Analgesic",
            "Antidiabetic",
        ],
    )

    controlled_substance: bool | None = Field(
        default=None, description="Whether this is a controlled substance"
    )

    controlled_substance_schedule: str | None = Field(
        default=None,
        description="Controlled substance schedule (I-V)",
        examples=["Schedule II", "Schedule III", "Schedule IV", "Schedule V"],
    )

    requires_prescription: bool | None = Field(
        default=True, description="Whether this medication requires a prescription"
    )

    over_the_counter: bool | None = Field(
        default=None, description="Whether this is available over-the-counter"
    )

    # Clinical information
    indications: list[str] = Field(
        default_factory=list,
        description="What conditions this medication treats",
        examples=[
            ["Hypertension", "Heart failure"],
            ["Pain", "Fever", "Inflammation"],
            ["Type 2 diabetes"],
        ],
    )

    contraindications: list[str] = Field(
        default_factory=list, description="When this medication should not be used"
    )

    side_effects: list[str] = Field(
        default_factory=list, description="Common side effects"
    )

    warnings: list[str] = Field(
        default_factory=list, description="Important warnings about this medication"
    )

    # Storage and handling
    storage_requirements: str | None = Field(
        default=None,
        description="How to store this medication",
        examples=[
            "Store at room temperature",
            "Refrigerate",
            "Keep dry",
            "Protect from light",
        ],
    )

    # Pricing (if relevant)
    typical_cost: str | None = Field(
        default=None, description="Typical cost or price range"
    )

    # Alternative medications
    alternatives: list[str] = Field(
        default_factory=list, description="Alternative medications with similar effects"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "id": "medication-lisinopril-001",
                    "resource_type": "Medication",
                    "status": "active",
                    "medication_name": "Lisinopril",
                    "generic_name": "Lisinopril",
                    "brand_name": "Zestril",
                    "dosage_form": "tablet",
                    "active_ingredients": ["Lisinopril 10mg"],
                    "drug_class": "ACE Inhibitor",
                    "requires_prescription": True,
                    "over_the_counter": False,
                    "indications": [
                        "Hypertension",
                        "Heart failure",
                        "Post-myocardial infarction",
                    ],
                    "side_effects": ["Dry cough", "Dizziness", "Hyperkalemia"],
                    "contraindications": ["Pregnancy", "Angioedema history"],
                    "storage_requirements": "Store at room temperature",
                    "code": {
                        "coding": [
                            {
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "29046",
                                "display": "Lisinopril",
                            }
                        ],
                        "text": "Lisinopril",
                    },
                },
                {
                    "id": "medication-ibuprofen-002",
                    "resource_type": "Medication",
                    "status": "active",
                    "medication_name": "Ibuprofen",
                    "generic_name": "Ibuprofen",
                    "brand_name": "Advil",
                    "dosage_form": "tablet",
                    "active_ingredients": ["Ibuprofen 200mg"],
                    "drug_class": "NSAID",
                    "requires_prescription": False,
                    "over_the_counter": True,
                    "indications": ["Pain", "Fever", "Inflammation"],
                    "side_effects": ["Stomach upset", "Dizziness", "Heartburn"],
                    "contraindications": [
                        "Severe kidney disease",
                        "Severe heart failure",
                    ],
                    "warnings": ["May increase risk of heart attack or stroke"],
                    "storage_requirements": "Store at room temperature in dry place",
                    "alternatives": ["Acetaminophen", "Naproxen", "Aspirin"],
                    "code": {
                        "coding": [
                            {
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "5640",
                                "display": "Ibuprofen",
                            }
                        ],
                        "text": "Ibuprofen",
                    },
                },
            ]
        }
