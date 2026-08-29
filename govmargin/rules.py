from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import FrozenSet, Optional


class RuleReviewState(str, Enum):
    VERIFIED_TEXT = "VERIFIED_TEXT"
    REQUIRES_QUALIFIED_REVIEW = "REQUIRES_QUALIFIED_REVIEW"


@dataclass(frozen=True)
class ContractContext:
    clauses: FrozenSet[str]
    contract_date: date
    agency: Optional[str] = None


@dataclass(frozen=True)
class RegulatoryRule:
    rule_id: str
    source: str
    section: str
    source_version: str
    effective_date: date
    required_clauses: FrozenSet[str]
    test: str
    exclusions: str
    required_evidence: FrozenSet[str]
    review_state: RuleReviewState

    def applies_to(self, context: ContractContext) -> bool:
        if context.contract_date < self.effective_date:
            return False
        return self.required_clauses.issubset(context.clauses)


FAR_52_216_7_UPDATE_BILLINGS = RegulatoryRule(
    rule_id="FAR_52_216_7_D2V_UPDATE_BILLINGS",
    source="https://www.acquisition.gov/far/52.216-7",
    section="52.216-7(d)(2)(v)",
    source_version="FAC 2026-01; clause Allowable Cost and Payment (Aug 2018)",
    effective_date=date(2018, 8, 1),
    required_clauses=frozenset({"52.216-7"}),
    test="After final indirect cost rate settlement, cumulative billings must be updated to reflect settled rates within the clause deadline.",
    exclusions="Does not override contract ceilings, funding limits, specific cost disallowances, releases, or other contract-specific limitations.",
    required_evidence=frozenset({"contract", "clause_text", "rate_agreement", "cumulative_billings"}),
    review_state=RuleReviewState.VERIFIED_TEXT,
)

FAR_52_216_7_COMPLETION_VOUCHER = RegulatoryRule(
    rule_id="FAR_52_216_7_D5_COMPLETION_VOUCHER",
    source="https://www.acquisition.gov/far/52.216-7",
    section="52.216-7(d)(5)",
    source_version="FAC 2026-01; clause Allowable Cost and Payment (Aug 2018)",
    effective_date=date(2018, 8, 1),
    required_clauses=frozenset({"52.216-7"}),
    test="After all final annual indirect rates for a physically complete contract are settled, submit a completion invoice or voucher reflecting settled amounts and rates.",
    exclusions="Written extensions and contract-specific terms may alter timing; qualified review is required for deadline disputes.",
    required_evidence=frozenset({"contract", "clause_text", "rate_agreement", "physical_completion_date"}),
    review_state=RuleReviewState.VERIFIED_TEXT,
)

FAR_52_216_7_BILLING_RATE_ADJUSTMENT = RegulatoryRule(
    rule_id="FAR_52_216_7_E_BILLING_RATE_ADJUSTMENT",
    source="https://www.acquisition.gov/far/52.216-7",
    section="52.216-7(e)",
    source_version="FAC 2026-01; clause Allowable Cost and Payment (Aug 2018)",
    effective_date=date(2018, 8, 1),
    required_clauses=frozenset({"52.216-7"}),
    test="Interim billing rates are subject to adjustment when final rates are established and may be revised to prevent substantial overpayment or underpayment.",
    exclusions="A rate difference alone is not a receivable; ceilings, funding, cost allowability, allocability, prior billings and contract terms remain controlling.",
    required_evidence=frozenset({"contract", "clause_text", "billing_rates", "final_rate_agreement", "cumulative_billings"}),
    review_state=RuleReviewState.VERIFIED_TEXT,
)

RULES = {
    rule.rule_id: rule
    for rule in (
        FAR_52_216_7_UPDATE_BILLINGS,
        FAR_52_216_7_COMPLETION_VOUCHER,
        FAR_52_216_7_BILLING_RATE_ADJUSTMENT,
    )
}
