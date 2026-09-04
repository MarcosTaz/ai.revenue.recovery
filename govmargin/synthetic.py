from __future__ import annotations

from datetime import date
from decimal import Decimal

from .allocations import IndirectLayer, compute_multi_pool
from .closeout import FinalVoucherInput, ReleaseState, reconcile_final_voucher
from .contracts import ContractEconomicState, Modification, TaskOrder, constrain_order_candidate, state_at
from .costs import (
    AllowabilityState,
    ContractBillability,
    DirectCostInput,
    PaymentInput,
    compute_direct_cost_variance,
    compute_payment_shortfall,
)
from .engine import FindingState, IndirectTrueUpInput, RateState, SupportState, compute_indirect_true_up
from .fees import FeeInput, FeeMethod, compute_fee_variance
from .lineage import SourceTransaction, trace_migrated_transaction
from .rules import ContractContext, FAR_52_216_7_COMPLETION_VOUCHER

D = Decimal
S = SupportState.SUPPORTED


def _true_up(**overrides):
    data = dict(
        contract_id="SYN-C",
        period="FY2025",
        allocation_base=D("1000"),
        final_rate=D("0.20"),
        billed_indirect=D("200"),
        rate_state=RateState.SETTLED_FINAL,
        contract_terms=S,
        base_allowability=S,
        base_allocability=S,
        indirect_ceiling_amount=None,
        remaining_funding=D("500"),
    )
    data.update(overrides)
    return compute_indirect_true_up(IndirectTrueUpInput(**data))


def _direct(**overrides):
    data = dict(
        contract_id="SYN-C",
        transaction_id="TX-1",
        amount=D("100"),
        billed_amount=D("0"),
        allowability=AllowabilityState.SUPPORTED_ALLOWABLE,
        allocability=S,
        contract_billability=ContractBillability.BILLABLE,
        duplicate=False,
        remaining_cost_ceiling=None,
        remaining_funding=D("500"),
    )
    data.update(overrides)
    return compute_direct_cost_variance(DirectCostInput(**data))


def run_synthetic_case(letter: str) -> FindingState:
    letter = letter.upper()
    if letter == "A":
        return _true_up().state
    if letter == "B":
        return _true_up(billed_indirect=D("150")).state
    if letter == "C":
        return _true_up(billed_indirect=D("250")).state
    if letter == "D":
        return _direct(allowability=AllowabilityState.SUPPORTED_UNALLOWABLE, billed_amount=D("100")).state
    if letter == "E":
        return _direct(amount=D("100"), billed_amount=D("0")).state
    if letter == "F":
        return compute_multi_pool([
            IndirectLayer("g&a", D("100"), D("0.1"), RateState.SETTLED_FINAL, True, False),
        ])["state"]
    if letter == "G":
        return compute_multi_pool([
            IndirectLayer("g&a", D("100"), D("0.1"), RateState.SETTLED_FINAL, False, True),
        ])["state"]
    if letter == "H":
        return _true_up(billed_indirect=D("180"), indirect_ceiling_amount=D("180")).state
    if letter == "I":
        return _true_up(billed_indirect=D("100"), remaining_funding=D("10")).state
    if letter == "J":
        return _direct(amount=D("100"), billed_amount=D("0")).state
    if letter == "K":
        return _direct(contract_billability=ContractBillability.NOT_BILLABLE).state
    if letter == "L":
        return compute_fee_variance(FeeInput(
            "SYN-C", FeeMethod.FIXED_AMOUNT, True, D("80"), fixed_fee_amount=D("100")
        ))["state"]
    if letter == "M":
        base = ContractEconomicState(date(2025, 1, 1), D("100"))
        mod = Modification("M1", date(2025, 6, 1), resulting_funding=D("200"), evidence_supported=True)
        state = state_at(base, [mod], date(2025, 7, 1))
        return FindingState.NO_VARIANCE if state.funding == D("200.00") else FindingState.UNKNOWN
    if letter == "N":
        base = ContractEconomicState(date(2025, 1, 1), D("500"), D("100"))
        mod = Modification("M2", date(2025, 6, 1), resulting_cost_ceiling=D("150"), evidence_supported=True)
        state = state_at(base, [mod], date(2025, 7, 1))
        return FindingState.NO_VARIANCE if state.cost_ceiling == D("150.00") else FindingState.UNKNOWN
    if letter == "O":
        return _true_up(billed_indirect=D("200")).state
    if letter == "P":
        return compute_payment_shortfall(PaymentInput("INV", D("100"), D("80"), True, True))["state"]
    if letter == "Q":
        return reconcile_final_voucher(FinalVoucherInput(
            "SYN-C", D("1000"), D("800"), True, True, ReleaseState.NOT_SIGNED, date(2026, 1, 1), True
        ))["state"]
    if letter == "R":
        return reconcile_final_voucher(FinalVoucherInput(
            "SYN-C", D("1000"), D("800"), True, True, ReleaseState.SIGNED_GENERAL, date(2026, 1, 1), True
        ))["state"]
    if letter == "S":
        old = SourceTransaction("old", "1", D("100"), "SYN-C", "FY2025")
        new = SourceTransaction("new", "99", D("100"), "SYN-C", "FY2025")
        return trace_migrated_transaction(old, new, [])["state"]
    if letter == "T":
        order = TaskOrder("TO-1", D("500"), D("150"), True, ("e1",))
        return constrain_order_candidate(order, D("150"), D("100"))["state"]
    if letter == "U":
        return compute_multi_pool([
            IndirectLayer("fringe", D("100"), D("0.2"), RateState.SETTLED_FINAL, True, True),
            IndirectLayer("overhead", D("120"), D("0.3"), RateState.SETTLED_FINAL, True, True, ("fringe",)),
        ])["state"]
    if letter == "V":
        applies = FAR_52_216_7_COMPLETION_VOUCHER.applies_to(
            ContractContext(frozenset({"52.216-7"}), date(2010, 1, 1))
        )
        return FindingState.UNKNOWN if not applies else FindingState.RECOVERY_CANDIDATE
    if letter == "W":
        return _direct(allowability=AllowabilityState.SUPPORTED_UNALLOWABLE).state
    if letter == "X":
        return _true_up(contract_terms=SupportState.UNKNOWN).state
    if letter == "Y":
        return _direct(duplicate=True).state
    if letter == "Z":
        return _true_up(billed_indirect=D("0"), rate_state=RateState.PROVISIONAL).state
    raise KeyError(letter)


EXPECTED = {
    "A": FindingState.NO_VARIANCE,
    "B": FindingState.RECOVERY_CANDIDATE,
    "C": FindingState.PAYABLE_CANDIDATE,
    "D": FindingState.PAYABLE_CANDIDATE,
    "E": FindingState.RECOVERY_CANDIDATE,
    "F": FindingState.REQUIRES_REVIEW,
    "G": FindingState.REQUIRES_REVIEW,
    "H": FindingState.NO_VARIANCE,
    "I": FindingState.REQUIRES_REVIEW,
    "J": FindingState.RECOVERY_CANDIDATE,
    "K": FindingState.NO_VARIANCE,
    "L": FindingState.RECOVERY_CANDIDATE,
    "M": FindingState.NO_VARIANCE,
    "N": FindingState.NO_VARIANCE,
    "O": FindingState.NO_VARIANCE,
    "P": FindingState.RECOVERY_CANDIDATE,
    "Q": FindingState.RECOVERY_CANDIDATE,
    "R": FindingState.REQUIRES_REVIEW,
    "S": FindingState.UNKNOWN,
    "T": FindingState.RECOVERY_CANDIDATE,
    "U": FindingState.NO_VARIANCE,
    "V": FindingState.UNKNOWN,
    "W": FindingState.NO_VARIANCE,
    "X": FindingState.UNKNOWN,
    "Y": FindingState.NO_VARIANCE,
    "Z": FindingState.REQUIRES_REVIEW,
}
