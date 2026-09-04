from __future__ import annotations

from collections import Counter
from decimal import Decimal
from typing import Any, Mapping, Sequence

from claim_workflow import ClaimLifecycle, ClaimRecord


def _decimal(value: object) -> Decimal:
    return Decimal(str(value))


def _money(value: Decimal, currency: str) -> str:
    return f"{currency} {value:,.2f}"


def render_executive_markdown(
    evaluated: Mapping[str, Any],
    workflow_records: Sequence[ClaimRecord] = (),
) -> str:
    summary = evaluated.get("summary", {})
    currency = str(summary.get("currency", "UNKNOWN"))

    claim_ready_value = _decimal(summary.get("verified_claim_ready_recovery", "0"))
    review_pipeline = _decimal(summary.get("review_required_pipeline", "0"))
    blocked_potential = _decimal(summary.get("blocked_potential", "0"))

    settled_records = [
        record for record in workflow_records if record.lifecycle == ClaimLifecycle.SETTLED
    ]
    settled_currencies = {record.currency for record in settled_records}
    if settled_currencies and settled_currencies != {currency}:
        raise ValueError("workflow settlement currency differs from evaluation summary currency")
    settled_value = sum(
        (record.verified_settled_amount for record in settled_records), Decimal("0")
    )

    results = list(evaluated.get("results", []))
    blockers: Counter[str] = Counter()
    warnings: Counter[str] = Counter()
    for result in results:
        blockers.update(str(item) for item in result.get("blocking_issues", []))
        warnings.update(str(item) for item in result.get("warnings", []))

    sorted_candidates = sorted(
        results,
        key=lambda item: _decimal(item.get("net_recoverable", "0")),
        reverse=True,
    )

    lines = [
        "# Aviation Recovery — Executive Recovery Report",
        "",
        "## Economic truth",
        "",
        f"- **Verified settled recovery:** {_money(settled_value, currency)}",
        f"- **Claim-ready economic value:** {_money(claim_ready_value, currency)}",
        f"- **Review-required pipeline:** {_money(review_pipeline, currency)}",
        f"- **Blocked potential:** {_money(blocked_potential, currency)}",
        f"- **Candidates evaluated:** {summary.get('candidate_count', len(results))}",
        "",
        "> Settled recovery requires cash, credit, refund or contractually valid offset evidence. Claim-ready and blocked amounts are not reported as recovered cash.",
        "",
        "## Candidate register",
        "",
        "| Claim | Status | Net economic amount | Key issue |",
        "|---|---|---:|---|",
    ]

    for result in sorted_candidates:
        issues = list(result.get("blocking_issues", [])) or list(result.get("warnings", []))
        issue = str(issues[0]) if issues else "—"
        lines.append(
            f"| {result.get('claim_id', 'UNKNOWN')} | {result.get('status', 'unknown')} | "
            f"{_money(_decimal(result.get('net_recoverable', '0')), str(result.get('currency', currency)))} | {issue} |"
        )

    lines.extend(["", "## Portfolio exceptions", ""])
    if not blockers and not warnings:
        lines.append("No blocking issues or warnings are currently recorded.")
    else:
        if blockers:
            lines.append("### Blocking issues")
            lines.append("")
            for issue, count in blockers.most_common():
                lines.append(f"- {issue}: {count}")
            lines.append("")
        if warnings:
            lines.append("### Warnings")
            lines.append("")
            for warning, count in warnings.most_common():
                lines.append(f"- {warning}: {count}")
            lines.append("")

    lines.extend(
        [
            "## Management interpretation",
            "",
            "- Prioritize claim-ready items by deadline and value.",
            "- Resolve evidence gaps on blocked high-value candidates before expanding scope.",
            "- Track submitted/approved claims separately until economic settlement evidence exists.",
            "- Do not combine blocked potential with verified recovery in management reporting.",
            "",
        ]
    )
    return "\n".join(lines)
