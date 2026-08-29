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


def redteam_industrial_fixture():
    event = RecoveryEvent(
        "EV-RT-1","OEM-RT","PRG-RT","PART-RT","PROGRAM_CANCELLED",date(2026,7,1),
        Decimal("1000"),Decimal("0"),"notice://rt/cancel","document://rt/customer-notice"
    )
    exposures = [
        ExposureLine("RT-1",event.event_id,"LOSS-1","RAW_MATERIAL",Decimal("10"),Decimal("10"),"EUR","inventory://rt/1","SUPPLIER"),
        ExposureLine("RT-2",event.event_id,"LOSS-2","TOOLING",Decimal("1"),Decimal("500"),"EUR","asset://rt/2","CUSTOMER"),
        ExposureLine("RT-3",event.event_id,"LOSS-3","NRE",Decimal("1"),Decimal("300"),"EUR","cost://rt/3","SUPPLIER"),
        ExposureLine("RT-4",event.event_id,"LOSS-4","FINISHED_GOODS",Decimal("10"),Decimal("20"),"EUR","inventory://rt/4","SUPPLIER",Decimal("50"),None),
        ExposureLine("RT-5",event.event_id,"LOSS-DUP","RAW_MATERIAL",Decimal("10"),Decimal("5"),"EUR","inventory://rt/5","SUPPLIER"),
        ExposureLine("RT-6",event.event_id,"LOSS-DUP","WIP",Decimal("5"),Decimal("10"),"EUR","inventory://rt/6","SUPPLIER"),
        ExposureLine("RT-7",event.event_id,"LOSS-7","WIP",Decimal("-1"),Decimal("10"),"EUR","inventory://rt/7","SUPPLIER"),
        ExposureLine("RT-8",event.event_id,"LOSS-8","TOOLING",Decimal("1"),Decimal("1000"),"EUR","asset://rt/8","SUPPLIER"),
        ExposureLine("RT-9",event.event_id,"LOSS-9","RAW_MATERIAL",Decimal("100"),Decimal("2"),"EUR","inventory://rt/9","SUPPLIER",Decimal("20"),"mitigation://rt/9",Decimal("30"),"credit://rt/9"),
    ]
    entitlements = [
        EntitlementBasis("RT-E1",event.event_id,"LOSS-1","SUPPORTED","contract://rt/1","po://rt/1"),
        EntitlementBasis("RT-E2",event.event_id,"LOSS-2","SUPPORTED","contract://rt/2","po://rt/2"),
        EntitlementBasis("RT-E4",event.event_id,"LOSS-4","SUPPORTED","contract://rt/4","po://rt/4"),
        EntitlementBasis("RT-E5",event.event_id,"LOSS-DUP","SUPPORTED","contract://rt/dup","po://rt/dup"),
        EntitlementBasis("RT-E7",event.event_id,"LOSS-7","SUPPORTED","contract://rt/7","po://rt/7"),
        EntitlementBasis("RT-E8",event.event_id,"LOSS-8","PARTIALLY_SUPPORTED","contract://rt/8","approval://rt/8",recoverable_cap=Decimal("420"),legal_review_required=True),
        EntitlementBasis("RT-E9",event.event_id,"LOSS-9","SUPPORTED","contract://rt/9","po://rt/9"),
    ]
    truth = {
        "RT-1":{"expected_state":"CLAIMABLE","claimable_amount":"100.00"},
        "RT-2":{"expected_state":"POTENTIAL_EXPOSURE","claimable_amount":"0.00"},
        "RT-3":{"expected_state":"POTENTIAL_EXPOSURE","claimable_amount":"0.00"},
        "RT-4":{"expected_state":"POTENTIAL_ENTITLEMENT","claimable_amount":"0.00"},
        "RT-5":{"expected_state":"UNKNOWN","claimable_amount":"0.00"},
        "RT-6":{"expected_state":"UNKNOWN","claimable_amount":"0.00"},
        "RT-7":{"expected_state":"UNKNOWN","claimable_amount":"0.00"},
        "RT-8":{"expected_state":"REQUIRES_REVIEW","claimable_amount":"420.00"},
        "RT-9":{"expected_state":"CLAIMABLE","claimable_amount":"150.00"},
    }
    return event, exposures, entitlements, truth
