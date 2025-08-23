from __future__ import annotations

from typing import Optional

from hacs_models.condition import Condition
from hacs_models.types import ConditionClinicalStatus, ConditionVerificationStatus
from hacs_utils.terminology.helpers import lookup_icd10


def add_stage(condition: Condition, summary_text: str) -> Condition:
    condition.add_stage(summary={"text": summary_text})
    return condition


def create_condition(
    text_or_code: str,
    *,
    subject_ref: Optional[str] = None,
    clinical_status: ConditionClinicalStatus = ConditionClinicalStatus.ACTIVE,
    verification_status: ConditionVerificationStatus = ConditionVerificationStatus.CONFIRMED,
) -> Condition:
    """Create a Condition with defaults and attempt ICD-10 coding via UMLS."""
    cond = Condition(clinical_status=clinical_status, verification_status=verification_status)
    if subject_ref:
        cond.subject = subject_ref
    cc = lookup_icd10(text_or_code)
    if cc:
        cond.code = cc.model_dump()
    else:
        cond.code = {"text": text_or_code}
    return cond


