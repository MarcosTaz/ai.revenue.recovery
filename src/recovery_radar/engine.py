from __future__ import annotations

from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

from .models import EntitlementBasis, ExposureLine, RecoveryEvent

MONEY = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def _is_finite(value: Decimal) -> bool:
    return isinstance(value, Decimal) and value.is_finite()


def _missing_evidence(line: ExposureLine, basis: EntitlementBasis | None) -> list[str]:
    missing: list[str] = []
    if not line.inventory_or_cost_ref:
        missing.append("MISSING_INVENTORY_OR_COST_RECORD")
    if line.ownership == "UNKNOWN":
        missing.append("MISSING_OWNERSHIP_EVIDENCE")
    if _is_finite(line.mitigation_amount) and line.mitigation_amount > 0 and not line.mitigation_evidence_ref:
        missing.append("MISSING_MITIGATION_EVIDENCE")
    if _is_finite(line.already_reimbursed_amount) and line.already_reimbursed_amount > 0 and not line.reimbursement_evidence_ref:
        missing.append("MISSING_REIMBURSEMENT_EVIDENCE")
    if basis is None:
        missing.append("MISSING_CONTRACTUAL_BASIS")
    else:
        if not basis.contractual_basis_ref:
            missing.append("MISSING_CONTRACTUAL_BASIS")
        if not basis.supporting_document_ref:
            missing.append("MISSING_SUPPORTING_DOCUMENT")
    return missing


def _lineage(event: RecoveryEvent, line: ExposureLine, basis: EntitlementBasis | None) -> dict:
    return {
        "event_id": event.event_id,
        "event_source": event.source_ref,
        "event_evidence": event.evidence_ref,
        "exposure_id": line.exposure_id,
        "economic_loss_id": line.economic_loss_id,
        "inventory_or_cost_ref": line.inventory_or_cost_ref or None,
        "entitlement_id": basis.entitlement_id if basis else None,
        "contractual_basis_ref": basis.contractual_basis_ref if basis else None,
        "supporting_document_ref": basis.supporting_document_ref if basis else None,
        "mitigation_evidence_ref": line.mitigation_evidence_ref,
        "reimbursement_evidence_ref": line.reimbursement_evidence_ref,
    }


def _unknown_line(
    event: RecoveryEvent,
    line: ExposureLine,
    basis: EntitlementBasis | None,
    reason: str,
    *,
    missing_evidence: list[str] | None = None,
) -> dict:
    return {
        "category": line.category,
        "currency": line.currency,
        "state": "UNKNOWN",
        "reason": reason,
        "claimable_amount": None,
        "missing_evidence": missing_evidence or [],
        "lineage": _lineage(event, line, basis),
    }


def _analyze_line(
    event: RecoveryEvent,
    line: ExposureLine,
    basis: EntitlementBasis | None,
    duplicate_reason: str | None,
) -> dict:
    lineage = _lineage(event, line, basis)
    if line.event_id != event.event_id or (basis is not None and basis.event_id != event.event_id):
        return {
            "category": line.category,
            "currency": line.currency,
            "state": "UNKNOWN",
            "reason": "EVENT_REFERENCE_MISMATCH",
            "claimable_amount": None,
            "missing_evidence": ["CORRECT_EVENT_LINKAGE_REQUIRED"],
            "lineage": lineage,
        }
    numeric_inputs = (
        line.quantity,
        line.unit_cost,
        line.mitigation_amount,
        line.already_reimbursed_amount,
    )
    if any(not _is_finite(value) for value in numeric_inputs):
        return _unknown_line(event, line, basis, "NON_FINITE_ECONOMIC_INPUT")
    if not line.currency or not line.currency.strip():
        return _unknown_line(event, line, basis, "CURRENCY_REQUIRED")
    if line.quantity < 0 or line.unit_cost < 0 or line.mitigation_amount < 0 or line.already_reimbursed_amount < 0:
        return _unknown_line(event, line, basis, "INVALID_NEGATIVE_ECONOMIC_INPUT")
    gross = _money(line.gross_exposure)
    if line.mitigation_amount > gross:
        return {
            "category": line.category,
            "currency": line.currency,
            "state": "UNKNOWN",
            "reason": "MITIGATION_EXCEEDS_GROSS_EXPOSURE",
            "gross_exposure": str(gross),
            "claimable_amount": None,
            "missing_evidence": [],
            "lineage": lineage,
        }
    net_after_mitigation = _money(gross - line.mitigation_amount)
    if line.already_reimbursed_amount > net_after_mitigation:
        return {
            "category": line.category,
            "currency": line.currency,
            "state": "UNKNOWN",
            "reason": "REIMBURSEMENT_EXCEEDS_NET_EXPOSURE",
            "gross_exposure": str(gross),
            "net_exposure": str(net_after_mitigation),
            "claimable_amount": None,
            "missing_evidence": [],
            "lineage": lineage,
        }
    net_exposure = _money(net_after_mitigation - line.already_reimbursed_amount)
    missing = _missing_evidence(line, basis)
    base = {
        "category": line.category,
        "currency": line.currency,
        "gross_exposure": str(gross),
        "mitigation": str(_money(line.mitigation_amount)),
        "already_reimbursed": str(_money(line.already_reimbursed_amount)),
        "net_exposure": str(net_exposure),
        "missing_evidence": missing,
        "lineage": lineage,
    }
    if duplicate_reason:
        return {**base, "state": "UNKNOWN", "reason": duplicate_reason, "claimable_amount": None}
    if line.ownership == "CUSTOMER":
        return {**base, "state": "POTENTIAL_EXPOSURE", "reason": "CUSTOMER_OWNED_ASSET_NOT_SUPPLIER_LOSS", "claimable_amount": "0.00"}
    if line.ownership == "UNKNOWN":
        return {**base, "state": "UNKNOWN", "reason": "OWNERSHIP_UNKNOWN", "claimable_amount": None}
    if net_exposure == 0:
        return {**base, "state": "POTENTIAL_EXPOSURE", "reason": "NO_NET_EXPOSURE_AFTER_OFFSETS", "claimable_amount": "0.00"}
    if basis is None:
        return {**base, "state": "POTENTIAL_EXPOSURE", "reason": "EXPOSURE_WITHOUT_ENTITLEMENT_BASIS", "claimable_amount": None}
    if basis.economic_loss_id != line.economic_loss_id:
        return {**base, "state": "UNKNOWN", "reason": "ENTITLEMENT_LOSS_REFERENCE_MISMATCH", "claimable_amount": None}
    if basis.support_state == "NOT_SUPPORTED":
        return {**base, "state": "POTENTIAL_EXPOSURE", "reason": "ENTITLEMENT_NOT_SUPPORTED", "claimable_amount": "0.00"}
    if basis.support_state in {"UNKNOWN", "CONFLICTING"}:
        return {**base, "state": "UNKNOWN", "reason": f"ENTITLEMENT_{basis.support_state}", "claimable_amount": None}
    if missing:
        return {**base, "state": "POTENTIAL_ENTITLEMENT", "reason": "EVIDENCE_GAPS_PREVENT_CLAIMABILITY", "claimable_amount": None}
    if basis.recoverable_cap is not None:
        if not _is_finite(basis.recoverable_cap):
            return {**base, "state": "UNKNOWN", "reason": "NON_FINITE_RECOVERABLE_CAP", "claimable_amount": None}
        if basis.recoverable_cap < 0:
            return {**base, "state": "UNKNOWN", "reason": "INVALID_NEGATIVE_RECOVERABLE_CAP", "claimable_amount": None}
        claimable = min(net_exposure, _money(basis.recoverable_cap))
    elif basis.support_state == "PARTIALLY_SUPPORTED":
        return {**base, "state": "POTENTIAL_ENTITLEMENT", "reason": "PARTIAL_SUPPORT_WITHOUT_DEFENSIBLE_CAP", "claimable_amount": None}
    else:
        claimable = net_exposure
    state = "REQUIRES_REVIEW" if basis.legal_review_required else "CLAIMABLE"
    return {
        **base,
        "state": state,
        "reason": "LEGAL_OR_HIGH_RISK_REVIEW_REQUIRED" if basis.legal_review_required else "DOCUMENTARY_BASIS_AND_EVIDENCE_SUPPORTED",
        "claimable_amount": str(_money(claimable)),
    }


def _economic_fingerprint(line: ExposureLine) -> tuple[str, ...]:
    return (
        line.event_id,
        line.category,
        str(line.quantity),
        str(line.unit_cost),
        line.currency,
        line.inventory_or_cost_ref,
        line.ownership,
        str(line.mitigation_amount),
        line.mitigation_evidence_ref or "",
        str(line.already_reimbursed_amount),
        line.reimbursement_evidence_ref or "",
    )


def _currency_totals(results: list[dict]) -> tuple[dict[str, dict[str, str]], bool]:
    currencies = sorted({line.get("currency") for line in results if line.get("currency")})
    totals: dict[str, dict[str, str]] = {}
    for currency in currencies:
        in_currency = [line for line in results if line.get("currency") == currency]
        net = sum(
            (Decimal(line["net_exposure"]) for line in in_currency if line.get("net_exposure") is not None),
            Decimal("0"),
        )
        claimable = sum(
            (
                Decimal(line["claimable_amount"])
                for line in in_currency
                if line.get("state") == "CLAIMABLE" and line.get("claimable_amount") is not None
            ),
            Decimal("0"),
        )
        review = sum(
            (
                Decimal(line["claimable_amount"])
                for line in in_currency
                if line.get("state") == "REQUIRES_REVIEW" and line.get("claimable_amount") is not None
            ),
            Decimal("0"),
        )
        totals[currency] = {
            "net_exposure_total": str(_money(net)),
            "claimable_total": str(_money(claimable)),
            "requires_review_amount": str(_money(review)),
        }
    return totals, len(currencies) > 1


def analyze_claim(event: RecoveryEvent, exposures: Iterable[ExposureLine], entitlements: Iterable[EntitlementBasis]) -> dict:
    exposures = tuple(exposures)
    entitlements = tuple(entitlements)
    invalid_event = any(
        not _is_finite(value) or value < 0
        for value in (event.expected_volume, event.revised_volume)
    )

    entitlement_by_loss: dict[str, list[EntitlementBasis]] = {}
    for basis in entitlements:
        entitlement_by_loss.setdefault(basis.economic_loss_id, []).append(basis)

    loss_counts = Counter(line.economic_loss_id for line in exposures)
    fingerprint_counts = Counter(_economic_fingerprint(line) for line in exposures)

    results: list[dict] = []
    for line in exposures:
        bases = entitlement_by_loss.get(line.economic_loss_id, [])
        basis = bases[0] if len(bases) == 1 else None
        if invalid_event:
            result = _unknown_line(event, line, basis, "INVALID_EVENT_ECONOMIC_INPUT")
        elif len(bases) > 1:
            result = {
                "category": line.category,
                "currency": line.currency,
                "state": "UNKNOWN",
                "reason": "CONFLICTING_ENTITLEMENT_RECORDS",
                "claimable_amount": None,
                "missing_evidence": [],
                "lineage": {
                    "event_id": event.event_id,
                    "exposure_id": line.exposure_id,
                    "economic_loss_id": line.economic_loss_id,
                    "entitlement_ids": sorted(b.entitlement_id for b in bases),
                },
            }
        else:
            duplicate_reason = None
            if loss_counts[line.economic_loss_id] > 1:
                duplicate_reason = "DUPLICATE_ECONOMIC_LOSS_ID_REQUIRES_REVIEW"
            elif fingerprint_counts[_economic_fingerprint(line)] > 1:
                duplicate_reason = "DUPLICATE_ECONOMIC_REPRESENTATION_REQUIRES_REVIEW"
            result = _analyze_line(event, line, basis, duplicate_reason)
        results.append(result)

    totals_by_currency, mixed_currency = _currency_totals(results)
    if mixed_currency:
        net_exposure_total = None
        claimable_total = None
        requires_review_amount = None
    elif totals_by_currency:
        only = next(iter(totals_by_currency.values()))
        net_exposure_total = only["net_exposure_total"]
        claimable_total = only["claimable_total"]
        requires_review_amount = only["requires_review_amount"]
    else:
        net_exposure_total = "0.00"
        claimable_total = "0.00"
        requires_review_amount = "0.00"

    return {
        "event": {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "customer_id": event.customer_id,
            "program_id": event.program_id,
            "part_id": event.part_id,
            "event_date": event.event_date.isoformat(),
            "expected_volume": str(event.expected_volume),
            "revised_volume": str(event.revised_volume),
            "impacted_volume": None if invalid_event else str(event.impacted_volume),
            "source_ref": event.source_ref,
            "evidence_ref": event.evidence_ref,
        },
        "claim_lines": results,
        "net_exposure_total": net_exposure_total,
        "claimable_total": claimable_total,
        "requires_review_amount": requires_review_amount,
        "totals_by_currency": totals_by_currency,
        "mixed_currency": mixed_currency,
        "paid_total": "0.00",
        "counts": {
            state: sum(1 for line in results if line["state"] == state)
            for state in sorted({line["state"] for line in results})
        },
        "product_boundary": "ECONOMIC_AND_EVIDENCE_ASSISTANCE_NOT_LEGAL_DETERMINATION",
    }
