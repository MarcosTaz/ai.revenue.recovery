from __future__ import annotations

from typing import Any, Mapping


def render_external_claim_markdown(dossier: Mapping[str, Any]) -> str:
    if dossier.get("externalization_gate") != "passed":
        raise ValueError("claim package requires a passed externalization gate")

    claim = dossier.get("claim", {})
    rule = dossier.get("rule", {})
    financial = dossier.get("financial_inputs", {})
    evidence = dossier.get("evidence", [])
    source_refs = dossier.get("source_refs", {})

    blockers = dossier.get("blocking_issues", [])
    lineage_gaps = dossier.get("lineage_gaps", [])
    if blockers or lineage_gaps:
        raise ValueError("claim package cannot contain blockers or lineage gaps")

    lines = [
        "# Aviation Lease Entitlement Claim Package",
        "",
        "## Claim summary",
        "",
        f"- **Claim ID:** {claim.get('claim_id', 'UNKNOWN')}",
        f"- **Entitlement type:** {claim.get('entitlement_type', 'UNKNOWN')}",
        f"- **Event date:** {claim.get('event_date', 'UNKNOWN')}",
        f"- **Currency:** {claim.get('currency', 'UNKNOWN')}",
        f"- **Gross contractual entitlement:** {claim.get('gross_entitlement', '0')}",
        f"- **Net amount requested:** {claim.get('net_recoverable', '0')}",
        "",
        "## Contractual basis",
        "",
        f"- **Rule ID:** {claim.get('rule_id', 'UNKNOWN')}",
        f"- **Formula:** {rule.get('formula', 'UNKNOWN')}",
        f"- **Effective from:** {rule.get('effective_from', 'UNKNOWN')}",
        f"- **Effective to:** {rule.get('effective_to') or 'open-ended / not specified'}",
        f"- **Contribution rate:** {rule.get('contribution_rate', '1')}",
        f"- **Cap:** {rule.get('cap') or 'none recorded'}",
        f"- **Floor:** {rule.get('floor') or 'none recorded'}",
        f"- **Deductible:** {rule.get('deductible', '0')}",
        f"- **Contract source:** {source_refs.get('rule_source', 'UNKNOWN')}",
        "",
        "## Calculation schedule",
        "",
        f"- Eligible cost: {financial.get('eligible_cost', '0')}",
        f"- Available reserve/contribution fund: {financial.get('available_fund', '0')}",
        f"- Prior paid/reimbursed: {financial.get('prior_paid_or_reimbursed', '0')}",
        f"- Claimed to date: {financial.get('claimed_to_date', '0')}",
        f"- **Net amount requested: {claim.get('net_recoverable', '0')} {claim.get('currency', '')}**",
        "",
        "### Reproducible calculation trace",
        "",
    ]

    for step in dossier.get("calculation_trace", []):
        lines.append(f"- {step}")

    lines.extend(["", "## Supporting evidence", ""])
    for item in evidence:
        lines.append(
            f"- {item.get('evidence_id', 'UNKNOWN')} — "
            f"{item.get('evidence_type', 'unknown')}: {item.get('source_name', 'unknown')}"
        )

    lines.extend(["", "## Material source references", ""])
    for key, value in sorted(source_refs.items()):
        lines.append(f"- {key}: {value}")

    lines.extend(
        [
            "",
            "## Submission note",
            "",
            "This package presents the contractual and evidential basis for the amount requested. "
            "It is generated only after the internal economic-evaluation and evidence-lineage gates have passed. "
            "Any counterparty adjustment, rejection or settlement must be recorded separately in the claim audit trail.",
            "",
        ]
    )
    return "\n".join(lines)
