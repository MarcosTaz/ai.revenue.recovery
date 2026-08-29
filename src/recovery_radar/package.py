from __future__ import annotations

from decimal import Decimal

from .missing_evidence import build_missing_evidence_actions

MONEY = Decimal("0.01")


def _money(value: Decimal) -> str:
    return str(value.quantize(MONEY))


def build_claim_package(analysis: dict) -> dict:
    lines = analysis["claim_lines"]
    missing = sorted({item for line in lines for item in line.get("missing_evidence", [])})
    gate_applied = analysis.get("registered_evidence_gate") == "APPLIED"
    gate_issues = sorted({item for line in lines for item in line.get("registered_evidence_issues", [])})
    missing_actions = build_missing_evidence_actions(analysis)
    mixed_currency = bool(analysis.get("mixed_currency"))
    if mixed_currency:
        review_status = "MULTI_CURRENCY_SPLIT_REQUIRED"
    elif missing or analysis["requires_review_amount"] != "0.00":
        review_status = "REQUIRES_HUMAN_REVIEW"
    elif not gate_applied:
        review_status = "REGISTERED_EVIDENCE_GATE_REQUIRED"
    elif gate_issues:
        review_status = "REQUIRES_HUMAN_REVIEW"
    else:
        review_status = "ECONOMIC_PACKAGE_READY_FOR_REVIEW"

    exposure_by_category: dict[str, dict[str, dict[str, Decimal]]] = {}
    calculation_trace = []
    evidence = []
    uncertainty = []
    draft_claim_lines = []

    for line in lines:
        category = line.get("category", "UNKNOWN")
        currency = line.get("currency") or "UNKNOWN"
        bucket = exposure_by_category.setdefault(category, {}).setdefault(
            currency,
            {
                "gross_exposure": Decimal("0"),
                "mitigation": Decimal("0"),
                "prior_compensation": Decimal("0"),
                "net_exposure": Decimal("0"),
                "claimable": Decimal("0"),
                "requires_review": Decimal("0"),
            },
        )
        for source_name, target_name in (
            ("gross_exposure", "gross_exposure"),
            ("mitigation", "mitigation"),
            ("already_reimbursed", "prior_compensation"),
            ("net_exposure", "net_exposure"),
        ):
            value = line.get(source_name)
            if value is not None:
                bucket[target_name] += Decimal(value)
        amount = line.get("claimable_amount")
        if amount is not None and line.get("state") == "CLAIMABLE":
            bucket["claimable"] += Decimal(amount)
        if amount is not None and line.get("state") == "REQUIRES_REVIEW":
            bucket["requires_review"] += Decimal(amount)

        lineage = line.get("lineage", {})
        exposure_id = lineage.get("exposure_id")
        calculation_trace.append(
            {
                "exposure_id": exposure_id,
                "category": line.get("category"),
                "currency": line.get("currency"),
                "gross_exposure": line.get("gross_exposure"),
                "mitigation": line.get("mitigation"),
                "prior_compensation": line.get("already_reimbursed"),
                "net_exposure": line.get("net_exposure"),
                "claimable_amount": line.get("claimable_amount"),
                "state": line.get("state"),
                "reason": line.get("reason"),
            }
        )
        evidence.append(
            {
                "exposure_id": exposure_id,
                "lineage": lineage,
                "registered_evidence_gate": line.get("registered_evidence_gate"),
                "registered_evidence_issues": line.get("registered_evidence_issues", []),
                "entitlement_review_state": line.get("entitlement_review_state"),
            }
        )
        if (
            line.get("state") not in {"CLAIMABLE"}
            or line.get("missing_evidence")
            or line.get("registered_evidence_issues")
        ):
            uncertainty.append(
                {
                    "exposure_id": exposure_id,
                    "state": line.get("state"),
                    "reason": line.get("reason"),
                    "missing_evidence": line.get("missing_evidence", []),
                    "registered_evidence_issues": line.get("registered_evidence_issues", []),
                    "entitlement_review_state": line.get("entitlement_review_state"),
                }
            )
        if line.get("state") == "CLAIMABLE" and amount is not None:
            draft_claim_lines.append(
                {
                    "exposure_id": exposure_id,
                    "category": line.get("category"),
                    "currency": line.get("currency"),
                    "amount": amount,
                    "contractual_basis_ref": lineage.get("contractual_basis_ref"),
                    "supporting_document_ref": lineage.get("supporting_document_ref"),
                }
            )

    rendered_categories = {
        category: {
            currency: {name: _money(value) for name, value in totals.items()}
            for currency, totals in currencies.items()
        }
        for category, currencies in exposure_by_category.items()
    }

    totals_by_currency = analysis.get("totals_by_currency", {})
    draft_status = "MULTI_CURRENCY_SPLIT_REQUIRED" if mixed_currency else "DRAFT_NOT_SUBMITTED"

    return {
        "executive_summary": {
            "event_id": analysis["event"]["event_id"],
            "event_type": analysis["event"]["event_type"],
            "net_exposure_total": analysis["net_exposure_total"],
            "claimable_total": analysis["claimable_total"],
            "requires_review_amount": analysis["requires_review_amount"],
            "totals_by_currency": totals_by_currency,
            "mixed_currency": mixed_currency,
            "paid_total": analysis["paid_total"],
            "review_status": review_status,
        },
        "event": analysis["event"],
        "claim_line_items": lines,
        "exposure_by_category": rendered_categories,
        "entitlement_basis": [
            {
                "exposure_id": item.get("exposure_id"),
                "contractual_basis_ref": item["lineage"].get("contractual_basis_ref"),
                "supporting_document_ref": item["lineage"].get("supporting_document_ref"),
                "entitlement_review_state": item.get("entitlement_review_state"),
                "state": next(
                    (
                        line.get("state")
                        for line in lines
                        if line.get("lineage", {}).get("exposure_id") == item.get("exposure_id")
                    ),
                    None,
                ),
            }
            for item in evidence
        ],
        "calculation_trace": calculation_trace,
        "mitigation": [
            {
                "exposure_id": item.get("exposure_id"),
                "mitigation": item.get("mitigation"),
                "prior_compensation": item.get("prior_compensation"),
            }
            for item in calculation_trace
        ],
        "evidence": evidence,
        "missing_evidence": missing,
        "registered_evidence_issues": gate_issues,
        "missing_evidence_actions": missing_actions,
        "uncertainty": uncertainty,
        "recoverability": {
            "claimable_total": analysis["claimable_total"],
            "requires_review_amount": analysis["requires_review_amount"],
            "totals_by_currency": totals_by_currency,
            "mixed_currency": mixed_currency,
            "states": analysis.get("counts", {}),
        },
        "draft_claim_package": {
            "status": draft_status,
            "claimable_total": analysis["claimable_total"],
            "totals_by_currency": totals_by_currency,
            "lines": draft_claim_lines,
        },
        "assumptions": [],
        "open_questions": [],
        "review_status": review_status,
        "legal_boundary": analysis["product_boundary"],
    }
