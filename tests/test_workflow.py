from decimal import Decimal

import pytest

from recovery_radar.workflow import ClaimCase, PaymentRecord, advance_case, record_payment


def _submitted_case() -> ClaimCase:
    case = ClaimCase("CASE-1", "W1", Decimal("800"), "EUR")
    for state in ("ANALYSIS", "REVIEW", "CLAIM_READY", "SUBMITTED"):
        case = advance_case(case, state)
    return case


def test_settled_never_equals_paid_without_payment_evidence():
    case = advance_case(_submitted_case(), "SETTLED", settled_amount=Decimal("600"), settlement_evidence_ref="settlement://1")
    assert case.state == "SETTLED"
    assert case.settled_amount == Decimal("600")
    assert case.paid_amount == Decimal("0")
    with pytest.raises(ValueError, match="INVALID_CLAIM_TRANSITION"):
        advance_case(case, "PAID")


def test_partial_payments_remain_payment_pending_until_full_settlement_paid():
    case = advance_case(_submitted_case(), "SETTLED", settled_amount=Decimal("600"), settlement_evidence_ref="settlement://1")
    case = record_payment(case, PaymentRecord("PAY-1", Decimal("250"), "EUR", "bank://PAY-1"))
    assert case.state == "PAYMENT_PENDING"
    assert case.paid_amount == Decimal("250")
    case = record_payment(case, PaymentRecord("PAY-2", Decimal("350"), "EUR", "bank://PAY-2"))
    assert case.paid_amount == Decimal("600")
    case = advance_case(case, "PAID")
    assert case.state == "PAID"


def test_payment_over_settlement_and_duplicate_payment_fail_closed():
    case = advance_case(_submitted_case(), "SETTLED", settled_amount=Decimal("600"), settlement_evidence_ref="settlement://1")
    case = record_payment(case, PaymentRecord("PAY-1", Decimal("250"), "EUR", "bank://PAY-1"))
    with pytest.raises(ValueError, match="DUPLICATE_PAYMENT_ID"):
        record_payment(case, PaymentRecord("PAY-1", Decimal("100"), "EUR", "bank://PAY-1b"))
    with pytest.raises(ValueError, match="EXCEED_SETTLEMENT"):
        record_payment(case, PaymentRecord("PAY-2", Decimal("351"), "EUR", "bank://PAY-2"))


def test_settlement_requires_documentary_evidence_and_cannot_exceed_claim():
    case = _submitted_case()
    with pytest.raises(ValueError, match="REQUIRES_EVIDENCE"):
        advance_case(case, "SETTLED", settled_amount=Decimal("600"))
    with pytest.raises(ValueError, match="EXCEEDS_CLAIM"):
        advance_case(case, "SETTLED", settled_amount=Decimal("801"), settlement_evidence_ref="settlement://bad")


def test_payment_currency_and_evidence_fail_closed():
    case = advance_case(_submitted_case(), "SETTLED", settled_amount=Decimal("600"), settlement_evidence_ref="settlement://1")
    with pytest.raises(ValueError, match="CURRENCY_MISMATCH"):
        record_payment(case, PaymentRecord("PAY-X", Decimal("100"), "USD", "bank://x"))
    with pytest.raises(ValueError, match="REQUIRES_EVIDENCE"):
        record_payment(case, PaymentRecord("PAY-Y", Decimal("100"), "EUR", ""))
