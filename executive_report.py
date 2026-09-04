from __future__ import annotations

from collections import Counter
from decimal import Decimal
from typing import Any, Mapping, Sequence

from claim_workflow import ClaimLifecycle, ClaimRecord


def _decimal(value: object) -> Decimal:
    return Decimal(str(value))


def _money(value: Decimal, currency: str) -> str:
    return f"{currency} {value:,.2f}"


def _workflow_index(
    results: Sequence[Mapping[str, Any]],
    workflow_records: Sequence[ClaimRecord],
    currency: str,
) -> dict[str, ClaimRecord]:
    result_by_id = {str(item.get("claim_id", "")): item for item in results}
    indexed: dict[str, ClaimRecord] = {}

    for record in workflow_records:
        if record.claim_id in indexed:
            raise ValueError(f"duplicate workflow record for claim {record.claim_id}")
        result = result_by_id.get(record.claim_id)
        if result is None:
            raise ValueError(f"workflow record references unknown claim {record.claim_id}")
        if record.currency != currency:
            raise ValueError("workflow settlement currency differs from evaluation summary currency")
        if record.asserted_recovery_amount < 0 or record.verified_settled_amount < 0:
            raise ValueError("workflow amounts cannot be negative")

        evaluated_amount = _decimal(result.get("net_recoverable", "0"))
        if record.asserted_recovery_amount != evaluated_amount:
            raise ValueError(
                f"workflow asserted amount differs from current evaluation for {record.claim_id}"
            )
        indexed[record.claim_id] = record

    return indexed


def render_executive_markdown(
    evaluated: Mapping[str, Any],
    workflow_records: Sequence[ClaimRecord] = (),
) -> str:
    summary = evaluated.get("summary", {})
    currency = str(summary.get("currency", "UNKNOWN"))
    results = list(evaluated.get("results", []))
    workflows = _workflow_index(results, workflow_records, currency)

    review_pipeline = _decimal(summary.get("review_required_pipeline", "0"))
    blocked_potential = _decimal(summary.get("blocked_potential", "0"))

    claim_ready_unsubmitted = Decimal("0")
    external_unsettled = Decimal("0")
    workflow_review_or_rejected = Decimal("0")
    settled_value = Decimal("0")

    external_unsettled_states = {
        ClaimLifecycle.SUBMITTED,
        ClaimLifecycle.ACKNOWLEDGED,
        ClaimLifecycle.DISPUTED,
        ClaimLifecycle.APPROVED,
    }
    workflow_review_states = {
        ClaimLifecycle.DETECTED,
        ClaimLifecycle.REVIEWING,
        ClaimLifecycle.REJECTED,
    }

    for result in results:
        if str(result.get("status", "")) != "claim_ready":
            continue

        claim_id = str(result.get("claim_id", ""))
        amount = _decimal(result.get("net_recoverable", "0"))
        workflow = workflows.get(claim_id)

        if workflow is None or workflow.lifecycle == ClaimLifecycle.CLAIM_READY:
            claim_ready_unsubmitted += amount
        elif workflow.lifecycle in external_unsettled_states:
            external_unsettled += workflow.asserted_recovery_amount
        elif workflow.lifecycle in workflow_review_states:
            workflow_review_or_rejected += workflow.asserted_recovery_amount
        elif workflow.lifecycle == ClaimLifecycle.SETTLED:
            settled_value += workflow.verified_settled_amount

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
        f"- **Claim-ready, not yet submitted:** {_money(claim_ready_unsubmitted, currency)}",
        f"- **Submitted / in counterparty process, unsettled:** {_money(external_unsettled, currency)}",
        f"- **Workflow review / rejected:** {_money(workflow_review_or_rejected, currency)}",
        f"- **Review-required pipeline:** {_money(review_pipeline, currency)}",
        f"- **Blocked potential:** {_money(blocked_potential, currency)}",
        f"- **Candidates evaluated:** {summary.get('candidate_count', len(results))}",
        "",
        "> A candidate appears in only one workflow-economic bucket. Settled recovery requires cash, credit, refund or contractually valid offset evidence. Submitted or approved value remains unsettled until that evidence exists.",
        "",
        "## Candidate register",
        "",
        "| Claim | Economic status | Workflow state | Net economic amount | Key issue |",
        "|---|---|---|---:|---|",
    ]

    for result in sorted_candidates:
        issues = list(result.get("blocking_issues", [])) or list(result.get("warnings", []))
        issue = str(issues[0]) if issues else "—"
        claim_id = str(result.get("claim_id", "UNKNOWN"))
        workflow = workflows.get(claim_id)
        workflow_state = workflow.lifecycle.value if workflow is not None else "—"
        lines.append(
            f"| {claim_id} | {result.get('status', 'unknown')} | {workflow_state} | "
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
            "- Prioritize claim-ready, not-yet-submitted items by deadline and value.",
            "- Track submitted, acknowledged, disputed and approved claims separately until economic settlement evidence exists.",
            "- Resolve evidence gaps on blocked high-value candidates before expanding scope.",
            "- Re-open rejected/disputed items into review rather than silently retaining them as claim-ready.",
            "- Never combine blocked potential or unsettled counterparty value with verified recovery.",
            "",
        ]
    )
    return "\n".join(lines)
