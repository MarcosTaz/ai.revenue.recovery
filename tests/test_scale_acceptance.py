from datetime import date
from decimal import Decimal

from recovery_radar.engine import analyze_claim
from recovery_radar.models import EntitlementBasis, ExposureLine, RecoveryEvent


def test_two_thousand_claim_lines_remain_exact_and_deterministic():
    event = RecoveryEvent(
        "EV-SCALE",
        "OEM-SCALE",
        "PRG-SCALE",
        "PART-SCALE",
        "VOLUME_REDUCTION",
        date(2026, 7, 1),
        Decimal("100000"),
        Decimal("50000"),
        "event://scale",
        "notice://scale",
    )
    exposures = []
    entitlements = []
    for index in range(2000):
        loss_id = f"LOSS-{index:04d}"
        exposure_id = f"EXP-{index:04d}"
        exposures.append(
            ExposureLine(
                exposure_id,
                event.event_id,
                loss_id,
                "RAW_MATERIAL",
                Decimal("10"),
                Decimal("12.34"),
                "EUR",
                f"inventory://scale/{index}",
                "SUPPLIER",
            )
        )
        entitlements.append(
            EntitlementBasis(
                f"ENT-{index:04d}",
                event.event_id,
                loss_id,
                "SUPPORTED",
                f"contract://scale/{index}",
                f"po://scale/{index}",
            )
        )

    first = analyze_claim(event, exposures, entitlements)
    second = analyze_claim(event, reversed(exposures), reversed(entitlements))

    expected = "246800.00"
    assert first["net_exposure_total"] == expected
    assert first["claimable_total"] == expected
    assert first["requires_review_amount"] == "0.00"
    assert first["counts"] == {"CLAIMABLE": 2000}
    assert first["totals_by_currency"]["EUR"]["claimable_total"] == expected
    assert second["net_exposure_total"] == expected
    assert second["claimable_total"] == expected
    assert second["counts"] == first["counts"]
