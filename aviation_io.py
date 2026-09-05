from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from aviation_dossier import build_internal_review_dossier
from aviation_recovery import (
    ClaimInput,
    EntitlementRule,
    EntitlementType,
    EvidenceRef,
    Formula,
    EvaluationResult,
    Status,
    evaluate_portfolio,
    validate_rule,
)
from recovery_truth import summarize_recovery_truth


def _date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid ISO date: {value!r}") from exc


def _decimal(value: Any, default: str = "0") -> Decimal:
    if value is None:
        value = default
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid decimal value: {value!r}") from exc
    if not parsed.is_finite():
        raise ValueError("decimal values must be finite")
    return parsed


def _require_list(raw: Mapping[str, Any], key: str) -> list[Any]:
    value = raw.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a JSON array")
    return value


def _require_mapping(raw: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = raw.get(key, {})
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be a JSON object")
    return value


def _string_list(raw: Mapping[str, Any], key: str) -> tuple[str, ...]:
    return tuple(str(value).strip() for value in _require_list(raw, key))


def parse_rule(raw: Mapping[str, Any]) -> EntitlementRule:
    if not isinstance(raw, Mapping):
        raise ValueError("each rule must be a JSON object")
    return EntitlementRule(
        rule_id=str(raw["rule_id"]).strip(),
        entitlement_type=EntitlementType(str(raw["entitlement_type"]).strip()),
        formula=Formula(str(raw["formula"]).strip()),
        currency=str(raw["currency"]).strip().upper(),
        effective_from=_date(str(raw["effective_from"]).strip()),
        effective_to=_date(str(raw["effective_to"]).strip()) if raw.get("effective_to") else None,
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
        required_evidence_types=_string_list(raw, "required_evidence_types"),
        excluded_cost_categories=_string_list(raw, "excluded_cost_categories"),
        notes=str(raw.get("notes", "")),
    )


def parse_claim(raw: Mapping[str, Any]) -> ClaimInput:
    if not isinstance(raw, Mapping):
        raise ValueError("each claim must be a JSON object")

    evidence_items = _require_list(raw, "evidence")
    evidence: list[EvidenceRef] = []
    for item in evidence_items:
        if not isinstance(item, Mapping):
            raise ValueError("each evidence reference must be a JSON object")
        evidence.append(
            EvidenceRef(
                evidence_id=str(item["evidence_id"]).strip(),
                evidence_type=str(item["evidence_type"]).strip(),
                source_name=str(item["source_name"]).strip(),
            )
        )

    source_refs = _require_mapping(raw, "source_refs")
    return ClaimInput(
        claim_id=str(raw["claim_id"]).strip(),
        rule_id=str(raw["rule_id"]).strip(),
        event_date=_date(str(raw["event_date"]).strip()),
        evaluation_date=_date(str(raw["evaluation_date"]).strip()),
        eligible_cost=_decimal(raw.get("eligible_cost"), "0"),
        available_fund=_decimal(raw.get("available_fund"), "0"),
        prior_paid_or_reimbursed=_decimal(raw.get("prior_paid_or_reimbursed"), "0"),
        claimed_to_date=_decimal(raw.get("claimed_to_date"), "0"),
        cost_categories=_string_list(raw, "cost_categories"),
        evidence=tuple(evidence),
        source_refs={str(k).strip(): str(v).strip() for k, v in source_refs.items()},
        human_waived_evidence_types=_string_list(raw, "human_waived_evidence_types"),
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


def _jsonify_summary(summary: Mapping[str, object]) -> dict[str, object]:
    rendered: dict[str, object] = {}
    for key, value in summary.items():
        rendered[key] = str(value) if isinstance(value, Decimal) else value
    return rendered


def _apply_lineage_gate(
    result: EvaluationResult,
    dossier: Mapping[str, Any],
) -> EvaluationResult:
    """Prevent untraceable candidates from inflating claim-ready/review value.

    Source lineage is an externalization prerequisite. The deterministic economic
    engine intentionally does not know dossier/source-reference semantics, so the
    IO boundary applies the gate before portfolio recovery truth is summarized.
    """
    gaps = tuple(str(item) for item in dossier.get("lineage_gaps", []))
    if not gaps:
        return result
    if result.status not in {Status.CLAIM_READY, Status.REVIEW_REQUIRED}:
        return result

    blocking = tuple(dict.fromkeys((*result.blocking_issues, *gaps)))
    return replace(result, status=Status.BLOCKED, blocking_issues=blocking)


def evaluate_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise ValueError("recovery payload must be a JSON object")

    rules_raw = payload.get("rules", [])
    claims_raw = payload.get("claims", [])
    if not isinstance(rules_raw, list):
        raise ValueError("rules must be a JSON array")
    if not isinstance(claims_raw, list):
        raise ValueError("claims must be a JSON array")

    rules = [parse_rule(item) for item in rules_raw]
    claims = [parse_claim(item) for item in claims_raw]

    for rule in rules:
        validate_rule(rule)

    rule_map = {rule.rule_id: rule for rule in rules}
    if len(rule_map) != len(rules):
        raise ValueError("duplicate rule_id in input")

    claim_ids = [claim.claim_id for claim in claims]
    if any(not claim_id for claim_id in claim_ids):
        raise ValueError("claim_id is required")
    if any(not claim.rule_id for claim in claims):
        raise ValueError("claim rule_id is required")
    if len(set(claim_ids)) != len(claim_ids):
        raise ValueError("duplicate claim_id in input")

    preliminary_results = evaluate_portfolio(rule_map, claims)
    preliminary_map = {result.claim_id: result for result in preliminary_results}

    dossiers: list[dict[str, Any]] = []
    final_results: list[EvaluationResult] = []

    for claim in claims:
        rule = rule_map.get(claim.rule_id)
        result = preliminary_map[claim.claim_id]

        if rule is None:
            final_results.append(result)
            dossiers.append(
                {
                    "claim": {"claim_id": claim.claim_id, "rule_id": claim.rule_id},
                    "blocking_issues": ["unknown_rule_id"],
                    "lineage_gaps": [],
                }
            )
            continue

        dossier = build_internal_review_dossier(rule, claim, result)
        gated_result = _apply_lineage_gate(result, dossier)
        if gated_result is not result:
            dossier = build_internal_review_dossier(rule, claim, gated_result)

        final_results.append(gated_result)
        dossiers.append(dossier)

    summary = summarize_recovery_truth(final_results)

    return {
        "summary": _jsonify_summary(summary),
        "results": [serialize_result(result) for result in final_results],
        "dossiers": dossiers,
    }
