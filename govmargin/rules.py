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

FAR_52_216_7_FINAL_PAYMENT = RegulatoryRule(
    rule_id="FAR_52_216_7_H_FINAL_PAYMENT",
    source="https://www.acquisition.gov/far/52.216-7",
    section="52.216-7(h)",
    source_version="FAC 2026-01; clause Allowable Cost and Payment (Aug 2018)",
    effective_date=date(2018, 8, 1),
    required_clauses=frozenset({"52.216-7"}),
    test="After approval of a completion invoice or voucher and compliance with contract terms, reconcile the remaining balance of supported allowable costs and unpaid fee, while preserving any refunds, credits, prior overpayments or other offsets owed to the Government.",
    exclusions="Do not treat a draft/unapproved voucher, unsupported cost, unsettled dispute, funding/ceiling issue, release, offset, refund or noncompliance as an automatic collectible balance.",
    required_evidence=frozenset({"contract", "clause_text", "approved_completion_voucher", "allowable_cost_support", "fee_terms", "cumulative_payments", "contract_compliance_state"}),
    review_state=RuleReviewState.VERIFIED_TEXT,
)

FAR_52_232_20_NOTICE = RegulatoryRule(
    rule_id="FAR_52_232_20_B_LIMITATION_OF_COST_NOTICE",
    source="https://www.acquisition.gov/far/52.232-20",
    section="52.232-20(b)",
    source_version="FAC 2026-01; clause Limitation of Cost (Apr 1984)",
    effective_date=date(1984, 4, 1),
    required_clauses=frozenset({"52.232-20"}),
    test="For an evidenced Limitation of Cost clause, test the contract-specific notice window and threshold against incurred plus forecast costs and preserve written-notice evidence.",
    exclusions="The clause permits the notice window and threshold to be varied. Do not infer the contract-specific values from the current FAR text; use the signed contract clause. A notice condition is not a reimbursement entitlement.",
    required_evidence=frozenset({"contract", "clause_text", "estimated_cost", "costs_incurred", "forecast_costs", "notice_terms"}),
    review_state=RuleReviewState.VERIFIED_TEXT,
)

FAR_52_232_20_EXCESS_LIMIT = RegulatoryRule(
    rule_id="FAR_52_232_20_D_LIMITATION_OF_COST_EXCESS",
    source="https://www.acquisition.gov/far/52.232-20",
    section="52.232-20(d)-(g)",
    source_version="FAC 2026-01; clause Limitation of Cost (Apr 1984)",
    effective_date=date(1984, 4, 1),
    required_clauses=frozenset({"52.232-20"}),
    test="Costs above the evidenced estimated-cost limit are not automatically reimbursable; written Contracting Officer action increasing the estimated cost is material and change orders do not alone authorize excess cost unless they increase the estimated cost.",
    exclusions="Do not convert excess incurred cost, a change order, informal communication, or forecast variance into a receivable. Contract-specific exceptions and historic clause versions require review.",
    required_evidence=frozenset({"contract", "clause_text", "estimated_cost", "costs_incurred", "contracting_officer_written_action", "modifications"}),
    review_state=RuleReviewState.VERIFIED_TEXT,
)

FAR_52_232_22_NOTICE = RegulatoryRule(
    rule_id="FAR_52_232_22_C_LIMITATION_OF_FUNDS_NOTICE",
    source="https://www.acquisition.gov/far/52.232-22",
    section="52.232-22(c)-(d)",
    source_version="FAC 2026-01; clause Limitation of Funds (Apr 1984)",
    effective_date=date(1984, 4, 1),
    required_clauses=frozenset({"52.232-22"}),
    test="For an evidenced Limitation of Funds clause, compare incurred plus forecast costs with the contract-specific percentage of funds actually allotted and preserve required written notices.",
    exclusions="The clause permits the notice window and threshold to vary. Do not assume estimated total cost equals funds allotted. A notice condition is not an entitlement to additional funding.",
    required_evidence=frozenset({"contract", "clause_text", "allotted_funds", "costs_incurred", "forecast_costs", "notice_terms"}),
    review_state=RuleReviewState.VERIFIED_TEXT,
)

FAR_52_232_22_EXCESS_LIMIT = RegulatoryRule(
    rule_id="FAR_52_232_22_F_LIMITATION_OF_FUNDS_EXCESS",
    source="https://www.acquisition.gov/far/52.232-22",
    section="52.232-22(f)-(j)",
    source_version="FAC 2026-01; clause Limitation of Funds (Apr 1984)",
    effective_date=date(1984, 4, 1),
    required_clauses=frozenset({"52.232-22"}),
    test="Costs above the amount actually allotted are not automatically reimbursable; written Contracting Officer action increasing the allotment is material and change orders alone do not authorize excess cost unless they increase the allotment.",
    exclusions="Do not infer additional funding from estimated cost, informal communications, performance continuation, or an unsupported modification. Contract-specific exceptions and historic clause versions require review.",
    required_evidence=frozenset({"contract", "clause_text", "allotted_funds", "costs_incurred", "contracting_officer_written_action", "modifications"}),
    review_state=RuleReviewState.VERIFIED_TEXT,
)

RULES = {
    rule.rule_id: rule
    for rule in (
        FAR_52_216_7_UPDATE_BILLINGS,
        FAR_52_216_7_COMPLETION_VOUCHER,
        FAR_52_216_7_BILLING_RATE_ADJUSTMENT,
        FAR_52_216_7_FINAL_PAYMENT,
        FAR_52_232_20_NOTICE,
        FAR_52_232_20_EXCESS_LIMIT,
        FAR_52_232_22_NOTICE,
        FAR_52_232_22_EXCESS_LIMIT,
    )
}
