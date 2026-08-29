from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class Applicability(str, Enum):
    SUPPORTED_WEDGE = "SUPPORTED_WEDGE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    UNSUPPORTED = "UNSUPPORTED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ContractTypeDecision:
    normalized_type: str
    applicability: Applicability
    enabled_for_recovery_engine: bool
    reason: str


_ALIASES = {
    "CPFF": "CPFF",
    "COST PLUS FIXED FEE": "CPFF",
    "COST-PLUS-FIXED-FEE": "CPFF",
    "COST REIMBURSEMENT": "COST_REIMBURSEMENT",
    "COST-REIMBURSEMENT": "COST_REIMBURSEMENT",
    "T&M": "T&M",
    "TIME AND MATERIALS": "T&M",
    "TIME-AND-MATERIALS": "T&M",
    "LH": "LABOR_HOUR",
    "LABOR HOUR": "LABOR_HOUR",
    "LABOUR HOUR": "LABOR_HOUR",
    "LABOR-HOUR": "LABOR_HOUR",
    "FFP": "FFP",
    "FIRM FIXED PRICE": "FFP",
    "FIRM-FIXED-PRICE": "FFP",
}


def _normalize(value: str | None) -> str:
    raw = " ".join(str(value or "").strip().upper().split())
    return _ALIASES.get(raw, raw)


def classify_contract_type(
    contract_type: str | None,
    *,
    clause_ids: Iterable[str] = (),
    settled_final_rates_evidenced: bool = False,
) -> ContractTypeDecision:
    """Classify applicability without inferring legal/accounting entitlement.

    The current executable wedge is deliberately narrow: cost-reimbursement/CPFF
    work with evidence-backed settled final indirect rates. T&M/LH and FFP remain
    disabled until their distinct billing/rate/ceiling rules are implemented and
    reviewed. Missing/ambiguous contract type always fails closed.
    """
    normalized = _normalize(contract_type)
    clauses = {str(value).strip().upper() for value in clause_ids if str(value).strip()}

    if not normalized:
        return ContractTypeDecision(
            normalized_type="UNKNOWN",
            applicability=Applicability.UNKNOWN,
            enabled_for_recovery_engine=False,
            reason="Contract type is missing; applicability cannot be inferred.",
        )

    if normalized in {"CPFF", "COST_REIMBURSEMENT"}:
        if "52.216-7" not in clauses:
            return ContractTypeDecision(
                normalized_type=normalized,
                applicability=Applicability.REVIEW_REQUIRED,
                enabled_for_recovery_engine=False,
                reason="Current settled-rate wedge requires evidence of FAR 52.216-7 applicability.",
            )
        if not settled_final_rates_evidenced:
            return ContractTypeDecision(
                normalized_type=normalized,
                applicability=Applicability.REVIEW_REQUIRED,
                enabled_for_recovery_engine=False,
                reason="Settled final indirect rates are not evidenced.",
            )
        return ContractTypeDecision(
            normalized_type=normalized,
            applicability=Applicability.SUPPORTED_WEDGE,
            enabled_for_recovery_engine=True,
            reason="Current cost-reimbursement settled-rate wedge prerequisites are evidenced.",
        )

    if normalized in {"T&M", "LABOR_HOUR"}:
        return ContractTypeDecision(
            normalized_type=normalized,
            applicability=Applicability.UNSUPPORTED,
            enabled_for_recovery_engine=False,
            reason="T&M/LH billing and rate-rule coverage is not yet enabled; use qualified review.",
        )

    if normalized == "FFP":
        return ContractTypeDecision(
            normalized_type=normalized,
            applicability=Applicability.UNSUPPORTED,
            enabled_for_recovery_engine=False,
            reason="Firm-fixed-price economics are outside the current settled-rate recovery wedge.",
        )

    return ContractTypeDecision(
        normalized_type=normalized,
        applicability=Applicability.UNKNOWN,
        enabled_for_recovery_engine=False,
        reason="Contract type is not recognized by the current executable applicability registry.",
    )
