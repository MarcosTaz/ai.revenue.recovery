from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal
from typing import Any

from aviation_recovery import ClaimInput, EntitlementRule, EvaluationResult, Formula, Status


class DossierIntegrityError(ValueError):
    pass


def required_source_fields(rule: EntitlementRule, claim: ClaimInput) -> tuple[str, ...]:
    fields: list[str] = ["rule_source", "event_date"]

    if rule.formula in {
        Formula.LOWER_OF_ELIGIBLE_COST_AND_AVAILABLE_FUND,
        Formula.PERCENT_OF_ELIGIBLE_COST,
        Formula.ELIGIBLE_COST_MINUS_DEDUCTIBLE,
    }:
        fields.append("eligible_cost")

    if rule.formula == Formula.LOWER_OF_ELIGIBLE_COST_AND_AVAILABLE_FUND:
        fields.append("available_fund")

    if claim.prior_paid_or_reimbursed > 0:
        fields.append("prior_paid_or_reimbursed")

    if claim.claimed_to_date > 0:
        fields.append("claimed_to_date")

    return tuple(fields)


def lineage_gaps(rule: EntitlementRule, claim: ClaimInput) -> tuple[str, ...]:
    gaps: list[str] = []
    for field_name in required_source_fields(rule, claim):
        value = claim.source_refs.get(field_name, "")
        if not str(value).strip():
            gaps.append(f"missing_source_ref:{field_name}")
    return tuple(gaps)


def build_internal_review_dossier(
    rule: EntitlementRule,
    claim: ClaimInput,
    result: EvaluationResult,
) -> dict[str, Any]:
    if claim.claim_id != result.claim_id:
        raise DossierIntegrityError("claim/result id mismatch")
    if claim.rule_id != result.rule_id or rule.rule_id != result.rule_id:
        raise DossierIntegrityError("rule/result id mismatch")

    gaps = lineage_gaps(rule, claim)

    return {
        "claim": {
            "claim_id": claim.claim_id,
            "rule_id": rule.rule_id,
            "entitlement_type": rule.entitlement_type.value,
            "event_date": claim.event_date.isoformat(),
            "evaluation_date": claim.evaluation_date.isoformat(),
            "status": result.status.value,
            "currency": result.currency,
            "gross_entitlement": str(result.gross_entitlement),
            "net_recoverable": str(result.net_recoverable),
        },
        "rule": {
            "formula": rule.formula.value,
            "effective_from": rule.effective_from.isoformat(),
            "effective_to": rule.effective_to.isoformat() if rule.effective_to else None,
            "contribution_rate": str(rule.contribution_rate),
            "fixed_amount": str(rule.fixed_amount) if rule.fixed_amount is not None else None,
            "deductible": str(rule.deductible),
            "cap": str(rule.cap) if rule.cap is not None else None,
            "floor": str(rule.floor) if rule.floor is not None else None,
            "deadline_days_after_event": rule.deadline_days_after_event,
            "required_evidence_types": list(rule.required_evidence_types),
            "excluded_cost_categories": list(rule.excluded_cost_categories),
            "notes": rule.notes,
        },
        "financial_inputs": {
            "eligible_cost": str(claim.eligible_cost),
            "available_fund": str(claim.available_fund),
            "prior_paid_or_reimbursed": str(claim.prior_paid_or_reimbursed),
            "claimed_to_date": str(claim.claimed_to_date),
        },
        "calculation_trace": list(result.calculation_trace),
        "blocking_issues": list(result.blocking_issues),
        "warnings": list(result.warnings),
        "source_refs": dict(claim.source_refs),
        "lineage_gaps": list(gaps),
        "evidence": [
            {
                "evidence_id": item.evidence_id,
                "evidence_type": item.evidence_type,
                "source_name": item.source_name,
            }
            for item in claim.evidence
        ],
    }


def build_external_claim_dossier(
    rule: EntitlementRule,
    claim: ClaimInput,
    result: EvaluationResult,
) -> dict[str, Any]:
    dossier = build_internal_review_dossier(rule, claim, result)

    if result.status != Status.CLAIM_READY:
        raise DossierIntegrityError(
            f"external dossier requires claim_ready result, got {result.status.value}"
        )

    if dossier["lineage_gaps"]:
        raise DossierIntegrityError(
            "external dossier blocked by lineage gaps: " + ", ".join(dossier["lineage_gaps"])
        )

    if result.blocking_issues:
        raise DossierIntegrityError("external dossier cannot contain blocking issues")

    dossier["externalization_gate"] = "passed"
    return dossier
