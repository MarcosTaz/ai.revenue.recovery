from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Mapping

from aviation_dossier import build_internal_review_dossier
from aviation_recovery import (
    ClaimInput,
    EntitlementRule,
    EntitlementType,
    EvidenceRef,
    Formula,
    EvaluationResult,
    evaluate_portfolio,
    summarize_recovery,
)


def _date(value: str) -> date:
    return date.fromisoformat(value)


def _decimal(value: Any, default: str = "0") -> Decimal:
    if value is None:
        value = default
    return Decimal(str(value))


def parse_rule(raw: Mapping[str, Any]) -> EntitlementRule:
    return EntitlementRule(
        rule_id=str(raw["rule_id"]),
        entitlement_type=EntitlementType(str(raw["entitlement_type"])),
        formula=Formula(str(raw["formula"])),
        currency=str(raw["currency"]),
        effective_from=_date(str(raw["effective_from"])),
        effective_to=_date(str(raw["effective_to"])) if raw.get("effective_to") else None,
        contribution_rate=_decimal(raw.get("contribution_rate"), "1"),
        fixed_amount=_decimal(raw["fixed_amount"]) if raw.get("fixed_amount") is not None else None,
        deductible=_decimal(raw.get("deductible"), "0"),
        cap=_decimal(raw["cap"]) if raw.get("cap") is not None else None,
        floor=_decimal(raw["floor"]) if raw.get("floor") is not None else None,
        deadline_days_after_event=(
            int(raw["deadline_days_after_event"])
            if raw.get("deadline_days_after_event") is not None
            else None
        ),
        required_evidence_types=tuple(str(v) for v in raw.get("required_evidence_types", [])),
        excluded_cost_categories=tuple(str(v) for v in raw.get("excluded_cost_categories", [])),
        notes=str(raw.get("notes", "")),
    )


def parse_claim(raw: Mapping[str, Any]) -> ClaimInput:
    evidence = tuple(
        EvidenceRef(
            evidence_id=str(item["evidence_id"]),
            evidence_type=str(item["evidence_type"]),
            source_name=str(item["source_name"]),
        )
        for item in raw.get("evidence", [])
    )
    return ClaimInput(
        claim_id=str(raw["claim_id"]),
        rule_id=str(raw["rule_id"]),
        event_date=_date(str(raw["event_date"])),
        evaluation_date=_date(str(raw["evaluation_date"])),
        eligible_cost=_decimal(raw.get("eligible_cost"), "0"),
        available_fund=_decimal(raw.get("available_fund"), "0"),
        prior_paid_or_reimbursed=_decimal(raw.get("prior_paid_or_reimbursed"), "0"),
        claimed_to_date=_decimal(raw.get("claimed_to_date"), "0"),
        cost_categories=tuple(str(v) for v in raw.get("cost_categories", [])),
        evidence=evidence,
        source_refs={str(k): str(v) for k, v in raw.get("source_refs", {}).items()},
        human_waived_evidence_types=tuple(
            str(v) for v in raw.get("human_waived_evidence_types", [])
        ),
    )


def serialize_result(result: EvaluationResult) -> dict[str, Any]:
    return {
        "claim_id": result.claim_id,
        "rule_id": result.rule_id,
        "status": result.status.value,
        "currency": result.currency,
        "gross_entitlement": str(result.gross_entitlement),
        "net_recoverable": str(result.net_recoverable),
        "blocking_issues": list(result.blocking_issues),
        "warnings": list(result.warnings),
        "calculation_trace": list(result.calculation_trace),
        "evidence_ids": list(result.evidence_ids),
    }


def evaluate_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    rules = [parse_rule(item) for item in payload.get("rules", [])]
    claims = [parse_claim(item) for item in payload.get("claims", [])]
    rule_map = {rule.rule_id: rule for rule in rules}

    if len(rule_map) != len(rules):
        raise ValueError("duplicate rule_id in input")

    results = evaluate_portfolio(rule_map, claims)
    result_map = {result.claim_id: result for result in results}

    dossiers: list[dict[str, Any]] = []
    for claim in claims:
        rule = rule_map.get(claim.rule_id)
        result = result_map[claim.claim_id]
        if rule is None:
            dossiers.append(
                {
                    "claim": {"claim_id": claim.claim_id, "rule_id": claim.rule_id},
                    "blocking_issues": ["unknown_rule_id"],
                    "lineage_gaps": [],
                }
            )
            continue
        dossiers.append(build_internal_review_dossier(rule, claim, result))

    summary = summarize_recovery(results)
    summary_json = {
        **summary,
        "net_recoverable": str(summary["net_recoverable"]),
    }

    return {
        "summary": summary_json,
        "results": [serialize_result(result) for result in results],
        "dossiers": dossiers,
    }
