from __future__ import annotations

from typing import Dict, Optional

from hacs_models.observation import CodeableConcept, Coding


# Minimal registry of common clinical document section codes.
# When exact LOINC/SNOMED codes are uncertain, we provide text-only concepts.
_SECTION_CODE_MAP: Dict[str, CodeableConcept] = {
    # Confident mappings
    "vital signs": CodeableConcept(
        text="Vital Signs",
        coding=[Coding(system="http://loinc.org", code="8716-3", display="Vital signs")],
    ),
    # Text-only placeholders (safe defaults)
    "chief complaint": CodeableConcept(text="Chief Complaint"),
    "history of present illness": CodeableConcept(text="History of Present Illness"),
    "hpi": CodeableConcept(text="History of Present Illness"),
    "medications": CodeableConcept(text="Medications"),
    "medications in use": CodeableConcept(text="Medications in Use"),
    "prescribed today": CodeableConcept(text="Medications Prescribed Today"),
    "past history": CodeableConcept(text="Past Medical History"),
    "vaccination": CodeableConcept(text="Immunizations"),
    "immunization": CodeableConcept(text="Immunizations"),
    "family history": CodeableConcept(text="Family History"),
    "social": CodeableConcept(text="Social History"),
    "social history": CodeableConcept(text="Social History"),
    "physical exam": CodeableConcept(text="Physical Examination"),
    "anthropometrics": CodeableConcept(text="Anthropometrics"),
    "test results": CodeableConcept(text="Test Results"),
    "diagnostic results": CodeableConcept(text="Diagnostic Results"),
    "diagnoses": CodeableConcept(text="Diagnoses"),
    "care plan": CodeableConcept(text="Plan of Care"),
    "plan": CodeableConcept(text="Plan of Care"),
    "orders": CodeableConcept(text="Orders and Referrals"),
    "referrals": CodeableConcept(text="Orders and Referrals"),
    # Portuguese canonical keys
    "queixa principal": CodeableConcept(
        text="Queixa Principal",
        coding=[Coding(system="http://loinc.org", code="10154-3", display="Chief complaint Narrative")],
    ),
    "história da doença atual": CodeableConcept(
        text="História da Doença Atual",
        coding=[Coding(system="http://loinc.org", code="10164-2", display="History of present illness Narrative")],
    ),
    "hda": CodeableConcept(
        text="História da Doença Atual",
        coding=[Coding(system="http://loinc.org", code="10164-2", display="History of present illness Narrative")],
    ),
    "história familiar": CodeableConcept(text="História Familiar"),
    "história social e hábitos de vida": CodeableConcept(text="História Social e Hábitos de Vida"),
    "exame físico": CodeableConcept(text="Exame físico"),
    "dados antropométricos": CodeableConcept(text="Dados Antropométricos"),
    "sinais vitais": CodeableConcept(
        text="Sinais Vitais",
        coding=[Coding(system="http://loinc.org", code="8716-3", display="Vital signs")],
    ),
    "resultado de exames": CodeableConcept(text="Resultado de Exames"),
    "hipóteses diagnósticas": CodeableConcept(text="Hipóteses Diagnósticas"),
    "medicações em uso": CodeableConcept(text="Medicações em uso"),
    "medicações prescritas": CodeableConcept(text="Medicações Prescritas"),
    "orientações": CodeableConcept(text="Orientações"),
    "exames complementares": CodeableConcept(text="Exames Complementares"),
    "atestado": CodeableConcept(text="Atestado"),
    "encaminhamento": CodeableConcept(text="Encaminhamento"),
}


def _normalize_key(name: str) -> str:
    return (name or "").strip().lower()


def resolve_section_code(title_or_key: str) -> Optional[CodeableConcept]:
    """Resolve a section `CodeableConcept` by section title or canonical key.

    Returns None if no mapping is available.
    """
    key = _normalize_key(title_or_key)
    return _SECTION_CODE_MAP.get(key)


def register_section_code(key: str, concept: CodeableConcept) -> None:
    """Register or override a section code mapping at runtime."""
    _SECTION_CODE_MAP[_normalize_key(key)] = concept


