from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from typing import Iterable

from .evidence import EvidenceDocument, assess_document_scope


_REQUIRED_LINEAGE_REFS = (
    "event_evidence",
    "inventory_or_cost_ref",
    "contractual_basis_ref",
    "supporting_document_ref",
)


def apply_registered_evidence_gate(
    analysis: dict,
    documents: Iterable[EvidenceDocument],
    *,
    workspace_id: str,
    supplier_id: str,
) -> dict:
    """Require registered, correctly scoped evidence before claimability.

    The economic engine may identify an otherwise supportable amount using source
    references. This gate prevents those references from becoming a claim-ready
    amount unless each required source is present in the registered evidence set
    and passes identity/scope checks.
    """
    output = deepcopy(analysis)
    by_source: dict[str, EvidenceDocument] = {}
    duplicate_sources: set[str] = set()
    for document in documents:
        if document.source_ref in by_source:
            duplicate_sources.add(document.source_ref)
        else:
            by_source[document.source_ref] = document

    event = output["event"]
    for line in output["claim_lines"]:
        if line["state"] not in {"CLAIMABLE", "REQUIRES_REVIEW"}:
            line["registered_evidence_gate"] = "NOT_APPLICABLE"
            continue

        required_refs = [line["lineage"].get(name) for name in _REQUIRED_LINEAGE_REFS]
        if Decimal(line.get("mitigation") or "0") > 0:
            required_refs.append(line["lineage"].get("mitigation_evidence_ref"))
        if Decimal(line.get("already_reimbursed") or "0") > 0:
            required_refs.append(line["lineage"].get("reimbursement_evidence_ref"))

        reasons: list[str] = []
        for reference in required_refs:
            if not reference:
                reasons.append("MISSING_REQUIRED_EVIDENCE_REFERENCE")
                continue
            if reference in duplicate_sources:
                reasons.append(f"AMBIGUOUS_REGISTERED_SOURCE:{reference}")
                continue
            document = by_source.get(reference)
            if document is None:
                reasons.append(f"UNREGISTERED_EVIDENCE:{reference}")
                continue
            assessment = assess_document_scope(
                document,
                workspace_id=workspace_id,
                supplier_id=supplier_id,
                customer_id=event["customer_id"],
                program_id=event["program_id"],
            )
            if assessment.state != "ACCEPTED":
                reasons.extend(
                    f"EVIDENCE_SCOPE:{reference}:{reason}"
                    for reason in assessment.reasons
                )

        if reasons:
            line["pre_gate_state"] = line["state"]
            line["pre_gate_amount"] = line.get("claimable_amount")
            line["state"] = "POTENTIAL_ENTITLEMENT"
            line["reason"] = "REGISTERED_EVIDENCE_GATE_FAILED"
            line["claimable_amount"] = None
            line["registered_evidence_gate"] = "FAILED"
            line["registered_evidence_issues"] = sorted(set(reasons))
        else:
            line["registered_evidence_gate"] = "PASSED"
            line["registered_evidence_issues"] = []

    def sum_amount(state: str) -> Decimal:
        return sum(
            (
                Decimal(line["claimable_amount"])
                for line in output["claim_lines"]
                if line["state"] == state and line.get("claimable_amount") is not None
            ),
            Decimal("0"),
        )

    output["claimable_total"] = str(sum_amount("CLAIMABLE").quantize(Decimal("0.01")))
    output["requires_review_amount"] = str(
        sum_amount("REQUIRES_REVIEW").quantize(Decimal("0.01"))
    )
    output["counts"] = {
        state: sum(1 for line in output["claim_lines"] if line["state"] == state)
        for state in sorted({line["state"] for line in output["claim_lines"]})
    }
    output["registered_evidence_gate"] = "APPLIED"
    return output
