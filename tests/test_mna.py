from decimal import Decimal

from govmargin.mna import (
    EconomicExposure,
    ExposureCategory,
    ExposureKind,
    build_economic_rights_exposure_schedule,
)

D = Decimal


def test_mna_schedule_keeps_assets_liabilities_and_unknowns_separate():
    rows = [
        EconomicExposure("e1", "C1", ExposureCategory.FINAL_RATE_TRUE_UP, ExposureKind.SUPPORTED_ASSET, D("250000"), ("rate-1",), "Settled final-rate underbilling."),
        EconomicExposure("e2", "C2", ExposureCategory.OVERBILLING, ExposureKind.SUPPORTED_LIABILITY, D("50000"), ("invoice-2",), "Supported overbilling exposure."),
        EconomicExposure("e3", "C3", ExposureCategory.FUNDING_EXPOSURE, ExposureKind.CONTINGENT_REVIEW, D("100000"), ("funding-3",), "Funding limitation requires review."),
        EconomicExposure("e4", "C4", ExposureCategory.UNRESOLVED_RATE, ExposureKind.UNKNOWN, None, (), "Final rate unresolved."),
    ]
    schedule = build_economic_rights_exposure_schedule(rows)
    assert schedule.supported_assets == D("250000.00")
    assert schedule.supported_liabilities == D("50000.00")
    assert schedule.contingent_review_amount == D("100000.00")
    assert schedule.net_supported_position == D("200000.00")
    assert schedule.unknown_count == 1


def test_supported_asset_or_liability_requires_evidence_and_amount():
    for kind in (ExposureKind.SUPPORTED_ASSET, ExposureKind.SUPPORTED_LIABILITY):
        try:
            EconomicExposure("e", "C", ExposureCategory.CLOSEOUT, kind, D("100"), (), "missing evidence")
        except ValueError:
            pass
        else:
            raise AssertionError("supported exposure without evidence must fail closed")


def test_duplicate_exposure_id_is_rejected():
    row = EconomicExposure("dup", "C1", ExposureCategory.CLOSEOUT, ExposureKind.UNKNOWN, None, (), "unknown")
    try:
        build_economic_rights_exposure_schedule([row, row])
    except ValueError as exc:
        assert "duplicate" in str(exc).lower()
    else:
        raise AssertionError("duplicate exposure ids must fail closed")
