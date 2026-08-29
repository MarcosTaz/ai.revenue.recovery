from datetime import date
from decimal import Decimal

from recovery_radar.auth import Principal
from recovery_radar.evidence import EvidenceDocument
from recovery_radar.models import EntitlementBasis, ExposureLine, RecoveryEvent
from recovery_radar.service import TenantService
from recovery_radar.storage import Storage


def test_entitlement_upload_is_not_entitlement_verification_and_rejection_revokes_support(tmp_path):
    store = Storage(tmp_path / "entitlement.db")
    try:
        store.create_workspace("A", "Supplier A")
        service = TenantService(store)
        analyst = Principal("A", "analyst", "ANALYST")
        reviewer = Principal("A", "reviewer", "REVIEWER")
        event = RecoveryEvent(
            "EV-1", "OEM-1", "PRG-1", "PART-1", "PROGRAM_CANCELLED",
            date(2026, 7, 1), Decimal("100"), Decimal("0"),
            "event://1", "notice://1"
        )
        line = ExposureLine(
            "EXP-1", "EV-1", "LOSS-1", "RAW_MATERIAL", Decimal("10"),
            Decimal("10"), "EUR", "inventory://1", "SUPPLIER"
        )
        basis = EntitlementBasis(
            "ENT-1", "EV-1", "LOSS-1", "SUPPORTED", "contract://1", "po://1"
        )
        service.store_recovery_event(analyst, event)
        service.store_exposure_line(analyst, line)
        service.store_entitlement_basis(analyst, basis)
        for document in (
            EvidenceDocument.from_bytes(document_id="D-N",workspace_id="A",supplier_id="SUP-1",customer_id="OEM-1",program_id="PRG-1",evidence_type="CUSTOMER_NOTICE",source_ref="notice://1",version_id="v1",document_date=date(2026,7,1),content=b"notice"),
            EvidenceDocument.from_bytes(document_id="D-I",workspace_id="A",supplier_id="SUP-1",customer_id="OEM-1",program_id="PRG-1",evidence_type="INVENTORY_RECORD",source_ref="inventory://1",version_id="v1",document_date=date(2026,7,1),content=b"inventory"),
            EvidenceDocument.from_bytes(document_id="D-C",workspace_id="A",supplier_id="SUP-1",customer_id="OEM-1",program_id="PRG-1",evidence_type="CONTRACT",source_ref="contract://1",version_id="v1",document_date=date(2026,1,1),content=b"contract",signed=True),
            EvidenceDocument.from_bytes(document_id="D-P",workspace_id="A",supplier_id="SUP-1",customer_id="OEM-1",program_id="PRG-1",evidence_type="PURCHASE_ORDER",source_ref="po://1",version_id="v1",document_date=date(2026,1,1),content=b"po"),
        ):
            service.store_evidence_document(analyst, document)
            service.review_evidence_document(reviewer, document.document_id, "VERIFIED")

        before = service.analyze_event(analyst, "EV-1", "SUP-1")
        assert before["claimable_total"] == "0.00"
        assert before["claim_lines"][0]["reason"] == "ENTITLEMENT_UNKNOWN"
        service.review_entitlement_basis(reviewer, "ENT-1", "VERIFIED", "basis checked against contract")
        verified = service.analyze_event(analyst, "EV-1", "SUP-1")
        assert verified["claimable_total"] == "100.00"
        assert verified["claim_lines"][0]["entitlement_review_state"] == "VERIFIED"
        service.review_entitlement_basis(reviewer, "ENT-1", "REJECTED", "later amendment invalidates basis")
        rejected = service.analyze_event(analyst, "EV-1", "SUP-1")
        assert rejected["claimable_total"] == "0.00"
        assert rejected["claim_lines"][0]["state"] == "UNKNOWN"
        assert rejected["claim_lines"][0]["entitlement_review_state"] == "REJECTED"
    finally:
        store.close()
