from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Iterable, Tuple

from .engine import money


class ExposureKind(str, Enum):
    SUPPORTED_ASSET = "SUPPORTED_ASSET"
    SUPPORTED_LIABILITY = "SUPPORTED_LIABILITY"
    CONTINGENT_REVIEW = "CONTINGENT_REVIEW"
    UNKNOWN = "UNKNOWN"


class ExposureCategory(str, Enum):
    UNBILLED_REVENUE = "UNBILLED_REVENUE"
    FINAL_RATE_TRUE_UP = "FINAL_RATE_TRUE_UP"
    FINAL_VOUCHER_BALANCE = "FINAL_VOUCHER_BALANCE"
    PAYMENT_SHORTFALL = "PAYMENT_SHORTFALL"
    OVERBILLING = "OVERBILLING"
    REFUND_CREDIT = "REFUND_CREDIT"
    FUNDING_EXPOSURE = "FUNDING_EXPOSURE"
    CEILING_EXPOSURE = "CEILING_EXPOSURE"
    QUESTIONED_COST = "QUESTIONED_COST"
    UNRESOLVED_RATE = "UNRESOLVED_RATE"
    CLOSEOUT = "CLOSEOUT"


@dataclass(frozen=True)
class EconomicExposure:
    exposure_id: str
    contract_id: str
    category: ExposureCategory
    kind: ExposureKind
    amount: Decimal | None
    evidence_ids: Tuple[str, ...]
    explanation: str

    def __post_init__(self):
        if not self.exposure_id.strip() or not self.contract_id.strip():
            raise ValueError("exposure_id and contract_id are required")
        if self.amount is not None and (not self.amount.is_finite() or self.amount < 0):
            raise ValueError("exposure amount must be finite and nonnegative")
        if self.kind in {ExposureKind.SUPPORTED_ASSET, ExposureKind.SUPPORTED_LIABILITY}:
            if self.amount is None or not self.evidence_ids:
                raise ValueError("supported assets/liabilities require amount and evidence")


@dataclass(frozen=True)
class EconomicRightsExposureSchedule:
    supported_assets: Decimal
    supported_liabilities: Decimal
    contingent_review_amount: Decimal
    net_supported_position: Decimal
    unknown_count: int
    rows: Tuple[EconomicExposure, ...]


def build_economic_rights_exposure_schedule(
    exposures: Iterable[EconomicExposure],
) -> EconomicRightsExposureSchedule:
    rows = tuple(exposures)
    seen = set()
    for row in rows:
        if row.exposure_id in seen:
            raise ValueError(f"duplicate exposure_id {row.exposure_id}")
        seen.add(row.exposure_id)

    assets = sum(
        (row.amount or Decimal("0"))
        for row in rows
        if row.kind is ExposureKind.SUPPORTED_ASSET
    )
    liabilities = sum(
        (row.amount or Decimal("0"))
        for row in rows
        if row.kind is ExposureKind.SUPPORTED_LIABILITY
    )
    contingent = sum(
        (row.amount or Decimal("0"))
        for row in rows
        if row.kind is ExposureKind.CONTINGENT_REVIEW
    )
    unknown_count = sum(row.kind is ExposureKind.UNKNOWN for row in rows)

    return EconomicRightsExposureSchedule(
        supported_assets=money(assets),
        supported_liabilities=money(liabilities),
        contingent_review_amount=money(contingent),
        net_supported_position=money(assets - liabilities),
        unknown_count=unknown_count,
        rows=rows,
    )
