from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

EventType = Literal[
    "PROGRAM_CANCELLED",
    "VOLUME_REDUCTION",
    "SOURCING_TERMINATED",
    "ENGINEERING_CHANGE",
    "CUSTOMER_STOP_ORDER",
    "PHASE_OUT_ACCELERATED",
]
ExposureCategory = Literal[
    "RAW_MATERIAL",
    "E_AND_O",
    "WIP",
    "FINISHED_GOODS",
    "TOOLING",
    "NRE",
    "SUPPLIER_COMMITMENTS",
    "DEDICATED_CAPACITY",
    "OTHER",
]
Ownership = Literal["SUPPLIER", "CUSTOMER", "UNKNOWN"]
SupportState = Literal[
    "SUPPORTED",
    "PARTIALLY_SUPPORTED",
    "CONFLICTING",
    "NOT_SUPPORTED",
    "UNKNOWN",
]


@dataclass(frozen=True, slots=True)
class RecoveryEvent:
    event_id: str
    customer_id: str
    program_id: str
    part_id: str
    event_type: EventType
    event_date: date
    expected_volume: Decimal
    revised_volume: Decimal
    source_ref: str
    evidence_ref: str

    @property
    def impacted_volume(self) -> Decimal:
        impact = self.expected_volume - self.revised_volume
        return impact if impact > 0 else Decimal("0")


@dataclass(frozen=True, slots=True)
class ExposureLine:
    exposure_id: str
    event_id: str
    economic_loss_id: str
    category: ExposureCategory
    quantity: Decimal
    unit_cost: Decimal
    currency: str
    inventory_or_cost_ref: str
    ownership: Ownership
    mitigation_amount: Decimal = Decimal("0")
    mitigation_evidence_ref: str | None = None
    already_reimbursed_amount: Decimal = Decimal("0")
    reimbursement_evidence_ref: str | None = None

    @property
    def gross_exposure(self) -> Decimal:
        return self.quantity * self.unit_cost


@dataclass(frozen=True, slots=True)
class EntitlementBasis:
    entitlement_id: str
    event_id: str
    economic_loss_id: str
    support_state: SupportState
    contractual_basis_ref: str | None
    supporting_document_ref: str | None
    recoverable_cap: Decimal | None = None
    legal_review_required: bool = False
