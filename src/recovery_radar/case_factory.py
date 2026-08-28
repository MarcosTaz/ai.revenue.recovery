from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Iterable

from .workflow import ClaimCase


def analysis_fingerprint(analysis: dict) -> str:
    """Fingerprint the complete gated analysis used to create a claim case."""
    raw = json.dumps(analysis, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def case_from_gated_analysis(
    workspace_id: str,
    analysis: dict,
    *,
    selected_exposure_ids: Iterable[str] | None = None,
) -> ClaimCase:
    """Create a claim case only from claimable, registry-gated analysis lines.

    Legal-review lines are never auto-selected. Multi-currency selections must be
    split into separate cases. The resulting amount and provenance are derived,
    not caller supplied.
    """
    if analysis.get("registered_evidence_gate") != "APPLIED":
        raise ValueError("CLAIM_CASE_REQUIRES_REGISTERED_EVIDENCE_GATE")
    event = analysis.get("event") or {}
    event_id = event.get("event_id")
    if not event_id:
        raise ValueError("CLAIM_CASE_REQUIRES_EVENT_ID")

    claimable_lines = [
        line
        for line in analysis.get("claim_lines", [])
        if line.get("state") == "CLAIMABLE"
        and line.get("registered_evidence_gate") == "PASSED"
        and line.get("claimable_amount") is not None
        and Decimal(line["claimable_amount"]) > 0
    ]
    by_exposure = {
        line.get("lineage", {}).get("exposure_id"): line
        for line in claimable_lines
        if line.get("lineage", {}).get("exposure_id")
    }

    if selected_exposure_ids is None:
        selected = tuple(sorted(by_exposure))
    else:
        selected = tuple(sorted(set(selected_exposure_ids)))
        if not selected:
            raise ValueError("CLAIM_CASE_REQUIRES_SELECTED_CLAIMABLE_LINE")
        missing = sorted(set(selected) - set(by_exposure))
        if missing:
            raise ValueError("SELECTED_LINE_NOT_CLAIMABLE:" + ",".join(missing))

    if not selected:
        raise ValueError("NO_CLAIMABLE_REGISTERED_EVIDENCE_LINES")

    lines = [by_exposure[exposure_id] for exposure_id in selected]
    currencies = {line.get("currency") for line in lines}
    if None in currencies or "" in currencies:
        raise ValueError("CLAIM_LINE_CURRENCY_REQUIRED")
    if len(currencies) != 1:
        raise ValueError("MULTI_CURRENCY_CLAIM_CASE_REQUIRES_SPLIT")
    currency = next(iter(currencies))
    amount = sum((Decimal(line["claimable_amount"]) for line in lines), Decimal("0"))
    if amount <= 0:
        raise ValueError("CLAIM_CASE_REQUIRES_POSITIVE_AMOUNT")

    fingerprint = analysis_fingerprint(analysis)
    identity = "|".join(
        [workspace_id, event_id, fingerprint, currency, str(amount), *selected]
    )
    case_id = "CASE-" + hashlib.sha256(identity.encode()).hexdigest()[:24]
    return ClaimCase(
        case_id=case_id,
        workspace_id=workspace_id,
        claim_amount=amount,
        currency=currency,
        event_id=event_id,
        analysis_fingerprint=fingerprint,
        selected_exposure_ids=selected,
    )
