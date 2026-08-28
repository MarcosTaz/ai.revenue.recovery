from __future__ import annotations

from datetime import date
from decimal import Decimal

from .models import EntitlementBasis, ExposureLine, RecoveryEvent


def alpha_components_fixture():
    event = RecoveryEvent("EV-ALPHA-1","OEM-A","PRG-A","PART-A","PROGRAM_CANCELLED",date(2026,5,1),Decimal("1000"),Decimal("0"),"notice://alpha/cancel","document://alpha/customer-notice")
    exposures = [ExposureLine("EXP-A1",event.event_id,"LOSS-A1","RAW_MATERIAL",Decimal("100"),Decimal("10"),"EUR","inventory://alpha/A1","SUPPLIER",Decimal("200"),"mitigation://alpha/resale")]
    entitlements = [EntitlementBasis("ENT-A1",event.event_id,"LOSS-A1","SUPPORTED","contract://alpha/termination-clause","po://alpha/PO-1")]
    truth = {"net_exposure_total":"800.00","claimable_total":"800.00","paid_total":"0.00"}
    return event, exposures, entitlements, truth


def zero_recovery_fixture():
    event = RecoveryEvent("EV-ZERO-1","OEM-Z","PRG-Z","PART-Z","PROGRAM_CANCELLED",date(2026,5,2),Decimal("1000"),Decimal("0"),"notice://zero/cancel","document://zero/customer-notice")
    exposures = [ExposureLine("EXP-Z1",event.event_id,"LOSS-Z1","FINISHED_GOODS",Decimal("100"),Decimal("10"),"EUR","inventory://zero/FG","SUPPLIER")]
    entitlements = [EntitlementBasis("ENT-Z1",event.event_id,"LOSS-Z1","NOT_SUPPORTED","contract://zero/no-cancellation-recovery","terms://zero/terms")]
    truth = {"net_exposure_total":"1000.00","claimable_total":"0.00","paid_total":"0.00"}
    return event, exposures, entitlements, truth


def partial_recovery_fixture():
    event = RecoveryEvent("EV-PART-1","OEM-P","PRG-P","PART-P","VOLUME_REDUCTION",date(2026,6,1),Decimal("10000"),Decimal("5000"),"release://partial/reduction","document://partial/release")
    exposures = [ExposureLine("EXP-P1",event.event_id,"LOSS-P1","TOOLING",Decimal("1"),Decimal("1000000"),"EUR","asset://partial/tool-1","SUPPLIER")]
    entitlements = [EntitlementBasis("ENT-P1",event.event_id,"LOSS-P1","PARTIALLY_SUPPORTED","agreement://partial/tooling","approval://partial/cap",recoverable_cap=Decimal("420000"),legal_review_required=True)]
    truth = {"net_exposure_total":"1000000.00","claimable_total":"0.00","requires_review_amount":"420000.00","paid_total":"0.00"}
    return event, exposures, entitlements, truth
