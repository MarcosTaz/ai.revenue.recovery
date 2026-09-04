from __future__ import annotations

from typing import Any, Mapping

from markdown_safety import markdown_plain_text


def _md(value: Any, default: str = "UNKNOWN") -> str:
    return markdown_plain_text(value, default)


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
        f"- **Claim ID:** {_md(claim.get('claim_id'))}",
        f"- **Entitlement type:** {_md(claim.get('entitlement_type'))}",
        f"- **Event date:** {_md(claim.get('event_date'))}",
        f"- **Currency:** {_md(claim.get('currency'))}",
        f"- **Gross contractual entitlement:** {_md(claim.get('gross_entitlement'), '0')}",
        f"- **Net amount requested:** {_md(claim.get('net_recoverable'), '0')}",
        "",
        "## Contractual basis",
        "",
        f"- **Rule ID:** {_md(claim.get('rule_id'))}",
        f"- **Formula:** {_md(rule.get('formula'))}",
        f"- **Effective from:** {_md(rule.get('effective_from'))}",
        f"- **Effective to:** {_md(rule.get('effective_to'), 'open-ended / not specified')}",
        f"- **Contribution rate:** {_md(rule.get('contribution_rate'), '1')}",
        f"- **Cap:** {_md(rule.get('cap'), 'none recorded')}",
        f"- **Floor:** {_md(rule.get('floor'), 'none recorded')}",
        f"- **Deductible:** {_md(rule.get('deductible'), '0')}",
        f"- **Contract source:** {_md(source_refs.get('rule_source'))}",
        "",
        "## Calculation schedule",
        "",
        f"- Eligible cost: {_md(financial.get('eligible_cost'), '0')}",
        f"- Available reserve/contribution fund: {_md(financial.get('available_fund'), '0')}",
        f"- Prior paid/reimbursed: {_md(financial.get('prior_paid_or_reimbursed'), '0')}",
        f"- Claimed to date: {_md(financial.get('claimed_to_date'), '0')}",
        f"- **Net amount requested: {_md(claim.get('net_recoverable'), '0')} {_md(claim.get('currency'), '')}**",
        "",
        "### Reproducible calculation trace",
        "",
    ]

    for step in dossier.get("calculation_trace", []):
        lines.append(f"- {_md(step, '—')}")

    lines.extend(["", "## Supporting evidence", ""])
    for item in evidence:
        lines.append(
            f"- {_md(item.get('evidence_id'))} — "
            f"{_md(item.get('evidence_type'), 'unknown')}: {_md(item.get('source_name'), 'unknown')}"
        )

    lines.extend(["", "## Material source references", ""])
    for key, value in sorted(source_refs.items(), key=lambda item: str(item[0])):
        lines.append(f"- {_md(key)}: {_md(value)}")

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
