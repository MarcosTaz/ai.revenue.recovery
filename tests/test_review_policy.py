from datetime import datetime, timezone
from decimal import Decimal

from govmargin.domain import EconomicFinding
from govmargin.engine import FindingState
from govmargin.pack import PackStatus, build_recovery_pack
from govmargin.review import HumanReview, ReviewDecision

D = Decimal
NOW = datetime(2026, 8, 29, 20, 0, tzinfo=timezone.utc)


def _finding():
    return EconomicFinding(
        "f-high",
        "C1",
        FindingState.RECOVERY_CANDIDATE,
        D("1000000"),
        D("800000"),
        D("800000"),
        D("200000"),
        ("e1",),
        ("r1",),
    )


def _review(reviewer, decision=ReviewDecision.APPROVED):
    return HumanReview(
        "f-high",
        reviewer,
        "GovCon finance reviewer",
        decision,
        "Independent evidence and calculation review completed.",
        NOW,
    )


def test_dual_review_policy_requires_two_independent_approvals():
    one = build_recovery_pack("org-a", [_finding()], [_review("r1")], required_approvals=2)
    assert one.status is PackStatus.DRAFT
    assert one.approved_recovery_candidates == []

    two = build_recovery_pack(
        "org-a",
        [_finding()],
        [_review("r1"), _review("r2")],
        required_approvals=2,
    )
    assert two.status is PackStatus.READY_FOR_CLIENT_FINANCE_REVIEW
    assert len(two.approved_recovery_candidates) == 1


def test_any_blocking_review_prevents_promotion_even_with_approvals():
    pack = build_recovery_pack(
        "org-a",
        [_finding()],
        [_review("r1"), _review("r2"), _review("r3", ReviewDecision.NEEDS_MORE_EVIDENCE)],
        required_approvals=2,
    )
    assert pack.status is PackStatus.DRAFT
    assert pack.approved_recovery_candidates == []
    assert len(pack.unresolved) == 1


def test_same_reviewer_cannot_satisfy_multiple_approval_slots():
    try:
        build_recovery_pack(
            "org-a",
            [_finding()],
            [_review("same"), _review("same")],
            required_approvals=2,
        )
    except ValueError as exc:
        assert "duplicate reviewer" in str(exc).lower()
    else:
        raise AssertionError("duplicate reviewer must fail closed")


def test_review_cannot_reference_unknown_finding():
    review = HumanReview(
        "missing",
        "r1",
        "GovCon finance reviewer",
        ReviewDecision.APPROVED,
        "Reviewed.",
        NOW,
    )
    try:
        build_recovery_pack("org-a", [_finding()], [review])
    except ValueError as exc:
        assert "unknown finding" in str(exc).lower()
    else:
        raise AssertionError("orphan review must fail closed")
