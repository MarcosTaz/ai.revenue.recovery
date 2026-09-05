from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Iterable, Mapping, Sequence


MONEY = Decimal("0.01")
_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")


class EntitlementType(str, Enum):
    MAINTENANCE_RESERVE = "maintenance_reserve_reimbursement"
    LESSOR_CONTRIBUTION = "lessor_contribution"
    COST_SHARING = "cost_sharing"
    SECURITY_DEPOSIT_RELEASE = "security_deposit_release"
    PREPAID_RENT_RELEASE = "prepaid_rent_release"
    END_OF_LEASE_ADJUSTMENT = "end_of_lease_adjustment"


class Formula(str, Enum):
    LOWER_OF_ELIGIBLE_COST_AND_AVAILABLE_FUND = "lower_of_eligible_cost_and_available_fund"
    PERCENT_OF_ELIGIBLE_COST = "percent_of_eligible_cost"
    FIXED_AMOUNT = "fixed_amount"
    ELIGIBLE_COST_MINUS_DEDUCTIBLE = "eligible_cost_minus_deductible"


class Status(str, Enum):
    BLOCKED = "blocked"
    REVIEW_REQUIRED = "review_required"
    CLAIM_READY = "claim_ready"
    ZERO_ENTITLEMENT = "zero_entitlement"


@dataclass(frozen=True)
class EvidenceRef:
    evidence_id: str
    evidence_type: str
    source_name: str


@dataclass(frozen=True)
class EntitlementRule:
    rule_id: str
    entitlement_type: EntitlementType
    formula: Formula
    currency: str
    effective_from: date
    effective_to: date | None = None
    contribution_rate: Decimal = Decimal("1")
    fixed_amount: Decimal | None = None
    deductible: Decimal = Decimal("0")
    cap: Decimal | None = None
    floor: Decimal | None = None
    deadline_days_after_event: int | None = None
    required_evidence_types: tuple[str, ...] = ()
    excluded_cost_categories: tuple[str, ...] = ()
    notes: str = ""

    def applies_on(self, event_date: date) -> bool:
        if event_date < self.effective_from:
            return False
        if self.effective_to is not None and event_date > self.effective_to:
            return False
        return True


@dataclass(frozen=True)
class ClaimInput:
    claim_id: str
    rule_id: str
    event_date: date
    evaluation_date: date
    eligible_cost: Decimal
    available_fund: Decimal = Decimal("0")
    prior_paid_or_reimbursed: Decimal = Decimal("0")
    claimed_to_date: Decimal = Decimal("0")
    cost_categories: tuple[str, ...] = ()
    evidence: tuple[EvidenceRef, ...] = ()
    source_refs: Mapping[str, str] = field(default_factory=dict)
    human_waived_evidence_types: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvaluationResult:
    claim_id: str
    rule_id: str
    status: Status
    currency: str
    gross_entitlement: Decimal
    net_recoverable: Decimal
    blocking_issues: tuple[str, ...]
    warnings: tuple[str, ...]
    calculation_trace: tuple[str, ...]
    evidence_ids: tuple[str, ...]


class RuleConfigurationError(ValueError):
    pass


def _money(value: Decimal) -> Decimal:
    if not value.is_finite():
        raise ValueError("money value must be finite")
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def _non_negative(value: Decimal, name: str) -> None:
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < 0:
        raise ValueError(f"{name} cannot be negative")


def _rule_non_negative(value: Decimal, name: str) -> None:
    if not value.is_finite():
        raise RuleConfigurationError(f"{name} must be finite")
    if value < 0:
        raise RuleConfigurationError(f"{name} cannot be negative")


def validate_rule(rule: EntitlementRule) -> None:
    if not rule.rule_id.strip():
        raise RuleConfigurationError("rule_id is required")
    if not _CURRENCY_RE.fullmatch(rule.currency.strip().upper()):
        raise RuleConfigurationError("currency must be a three-letter code")
    if rule.effective_to is not None and rule.effective_to < rule.effective_from:
        raise RuleConfigurationError("effective_to cannot precede effective_from")

    _rule_non_negative(rule.contribution_rate, "contribution_rate")
    if rule.formula == Formula.FIXED_AMOUNT and rule.fixed_amount is None:
        raise RuleConfigurationError("fixed_amount is required for fixed_amount formula")
    if rule.fixed_amount is not None:
        _rule_non_negative(rule.fixed_amount, "fixed_amount")
    _rule_non_negative(rule.deductible, "deductible")
    if rule.cap is not None:
        _rule_non_negative(rule.cap, "cap")
    if rule.floor is not None:
        _rule_non_negative(rule.floor, "floor")
    if rule.cap is not None and rule.floor is not None and rule.floor > rule.cap:
        raise RuleConfigurationError("floor cannot exceed cap")
    if rule.deadline_days_after_event is not None and rule.deadline_days_after_event < 0:
        raise RuleConfigurationError("deadline_days_after_event cannot be negative")
    if any(not item.strip() for item in rule.required_evidence_types):
        raise RuleConfigurationError("required_evidence_types cannot contain blank values")
    if any(not item.strip() for item in rule.excluded_cost_categories):
        raise RuleConfigurationError("excluded_cost_categories cannot contain blank values")


def _base_entitlement(rule: EntitlementRule, claim: ClaimInput) -> tuple[Decimal, list[str]]:
    trace: list[str] = []

    if rule.formula == Formula.LOWER_OF_ELIGIBLE_COST_AND_AVAILABLE_FUND:
        cost_side = claim.eligible_cost * rule.contribution_rate
        base = min(cost_side, claim.available_fund)
        trace.append(
            f"base=min(eligible_cost {claim.eligible_cost} * rate {rule.contribution_rate}, "
            f"available_fund {claim.available_fund})={base}"
        )
    elif rule.formula == Formula.PERCENT_OF_ELIGIBLE_COST:
        base = claim.eligible_cost * rule.contribution_rate
        trace.append(
            f"base=eligible_cost {claim.eligible_cost} * rate {rule.contribution_rate}={base}"
        )
    elif rule.formula == Formula.FIXED_AMOUNT:
        assert rule.fixed_amount is not None
        base = rule.fixed_amount
        trace.append(f"base=fixed_amount {base}")
    elif rule.formula == Formula.ELIGIBLE_COST_MINUS_DEDUCTIBLE:
        base = max(Decimal("0"), claim.eligible_cost - rule.deductible)
        base *= rule.contribution_rate
        trace.append(
            f"base=max(0, eligible_cost {claim.eligible_cost} - deductible {rule.deductible}) "
            f"* rate {rule.contribution_rate}={base}"
        )
    else:  # pragma: no cover - Enum guards this for normal callers
        raise RuleConfigurationError(f"unsupported formula: {rule.formula}")

    if rule.floor is not None:
        before = base
        base = max(base, rule.floor)
        trace.append(f"floor=max({before}, {rule.floor})={base}")

    if rule.cap is not None:
        before = base
        base = min(base, rule.cap)
        trace.append(f"cap=min({before}, {rule.cap})={base}")

    return _money(max(base, Decimal("0"))), trace


def _evidence_integrity_issues(evidence: Sequence[EvidenceRef]) -> tuple[str, ...]:
    issues: list[str] = []
    seen_ids: set[str] = set()
    duplicate_ids: set[str] = set()

    for index, item in enumerate(evidence, start=1):
        evidence_id = item.evidence_id.strip()
        if not evidence_id:
            issues.append(f"evidence_ref_{index}_missing_id")
        elif evidence_id in seen_ids:
            duplicate_ids.add(evidence_id)
        else:
            seen_ids.add(evidence_id)
        if not item.evidence_type.strip():
            issues.append(f"evidence_ref_{index}_missing_type")
        if not item.source_name.strip():
            issues.append(f"evidence_ref_{index}_missing_source_name")

    issues.extend(f"duplicate_evidence_id:{item}" for item in sorted(duplicate_ids))
    return tuple(issues)


def evaluate_claim(rule: EntitlementRule, claim: ClaimInput) -> EvaluationResult:
    validate_rule(rule)

    for name, value in (
        ("eligible_cost", claim.eligible_cost),
        ("available_fund", claim.available_fund),
        ("prior_paid_or_reimbursed", claim.prior_paid_or_reimbursed),
        ("claimed_to_date", claim.claimed_to_date),
    ):
        _non_negative(value, name)

    blocking: list[str] = []
    warnings: list[str] = []
    trace: list[str] = []

    if not claim.claim_id.strip():
        blocking.append("claim_id_required")
    if not claim.rule_id.strip():
        blocking.append("claim_rule_id_required")
    if claim.rule_id != rule.rule_id:
        blocking.append("claim_rule_mismatch")
    if claim.evaluation_date < claim.event_date:
        blocking.append("evaluation_date_precedes_event_date")

    if not rule.applies_on(claim.event_date):
        blocking.append("rule_not_effective_on_event_date")

    evidence_integrity = _evidence_integrity_issues(claim.evidence)
    blocking.extend(evidence_integrity)

    if any(not item.strip() for item in claim.human_waived_evidence_types):
        blocking.append("human_waived_evidence_types_contains_blank")

    present_types = {
        item.evidence_type
        for item in claim.evidence
        if item.evidence_id.strip() and item.evidence_type.strip() and item.source_name.strip()
    }
    waived_types = set(claim.human_waived_evidence_types)
    for required in rule.required_evidence_types:
        if required not in present_types and required not in waived_types:
            blocking.append(f"missing_evidence:{required}")
        elif required in waived_types and required not in present_types:
            warnings.append(f"evidence_waived_by_human:{required}")

    excluded_hits = sorted(set(rule.excluded_cost_categories).intersection(claim.cost_categories))
    if excluded_hits:
        blocking.extend(f"excluded_cost_category_present:{item}" for item in excluded_hits)

    if rule.deadline_days_after_event is not None:
        elapsed = (claim.evaluation_date - claim.event_date).days
        remaining = rule.deadline_days_after_event - elapsed
        trace.append(
            f"deadline={rule.deadline_days_after_event}d; elapsed={elapsed}d; remaining={remaining}d"
        )
        if remaining < 0:
            blocking.append("contractual_deadline_expired")
        elif remaining <= 30:
            warnings.append(f"deadline_approaching:{remaining}_days")

    gross, gross_trace = _base_entitlement(rule, claim)
    trace.extend(gross_trace)

    offsets = claim.prior_paid_or_reimbursed + claim.claimed_to_date
    net = _money(max(Decimal("0"), gross - offsets))
    trace.append(
        f"net=max(0, gross {gross} - prior_paid_or_reimbursed {claim.prior_paid_or_reimbursed} "
        f"- claimed_to_date {claim.claimed_to_date})={net}"
    )

    if blocking:
        status = Status.BLOCKED
    elif net == 0:
        status = Status.ZERO_ENTITLEMENT
    elif warnings:
        status = Status.REVIEW_REQUIRED
    else:
        status = Status.CLAIM_READY

    return EvaluationResult(
        claim_id=claim.claim_id,
        rule_id=rule.rule_id,
        status=status,
        currency=rule.currency,
        gross_entitlement=gross,
        net_recoverable=net,
        blocking_issues=tuple(blocking),
        warnings=tuple(warnings),
        calculation_trace=tuple(trace),
        evidence_ids=tuple(item.evidence_id for item in claim.evidence),
    )


def evaluate_portfolio(
    rules: Mapping[str, EntitlementRule], claims: Iterable[ClaimInput]
) -> tuple[EvaluationResult, ...]:
    results: list[EvaluationResult] = []
    for claim in claims:
        rule = rules.get(claim.rule_id)
        if rule is None:
            results.append(
                EvaluationResult(
                    claim_id=claim.claim_id,
                    rule_id=claim.rule_id,
                    status=Status.BLOCKED,
                    currency="UNKNOWN",
                    gross_entitlement=Decimal("0.00"),
                    net_recoverable=Decimal("0.00"),
                    blocking_issues=("unknown_rule_id",),
                    warnings=(),
                    calculation_trace=(),
                    evidence_ids=tuple(item.evidence_id for item in claim.evidence),
                )
            )
            continue
        results.append(evaluate_claim(rule, claim))
    return tuple(results)


def summarize_recovery(results: Sequence[EvaluationResult]) -> dict[str, object]:
    """Return a conservative status-aware portfolio summary.

    `net_recoverable` is retained for backwards compatibility, but now means only
    claim-ready economic value. Blocked and review-required amounts are exposed
    separately and must not be reported as recovered/ready value.
    """
    currencies = {result.currency for result in results if result.currency != "UNKNOWN"}
    if len(currencies) > 1:
        raise ValueError("portfolio summary requires a single currency or prior FX normalization")

    claim_ready = [result for result in results if result.status == Status.CLAIM_READY]
    review_required = [result for result in results if result.status == Status.REVIEW_REQUIRED]
    blocked = [result for result in results if result.status == Status.BLOCKED]

    claim_ready_value = sum((result.net_recoverable for result in claim_ready), Decimal("0"))
    review_value = sum((result.net_recoverable for result in review_required), Decimal("0"))
    blocked_value = sum((result.net_recoverable for result in blocked), Decimal("0"))

    return {
        "currency": next(iter(currencies), "UNKNOWN"),
        "candidate_count": len(results),
        "claim_ready_count": len(claim_ready),
        "review_required_count": len(review_required),
        "blocked_count": len(blocked),
        "zero_entitlement_count": sum(result.status == Status.ZERO_ENTITLEMENT for result in results),
        "net_recoverable": _money(claim_ready_value),
        "review_required_pipeline": _money(review_value),
        "blocked_potential": _money(blocked_value),
        "total_identified_before_status_filter": _money(
            claim_ready_value + review_value + blocked_value
        ),
    }
