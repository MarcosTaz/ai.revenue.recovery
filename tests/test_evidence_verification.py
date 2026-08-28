from datetime import date

from recovery_radar.auth import Principal
from recovery_radar.evidence import EvidenceDocument
from recovery_radar.service import TenantService
from recovery_radar.storage import Storage


def _doc(workspace="A"):
    return EvidenceDocument.from_bytes(
        document_id="DOC-1",
        workspace_id=workspace,
        supplier_id="SUP-1",
        customer_id="OEM-1",
        program_id="PRG-1",
        evidence_type="CONTRACT",
        source_ref="contract://1",
        version_id="v1",
        document_date=date(2026, 1, 1),
        content=b"synthetic contract v1",
        signed=True,
    )


def test_upload_is_not_verification_and_latest_reviewer_state_controls(tmp_path):
    store = Storage(tmp_path / "verify.db")
    try:
        store.create_workspace("A", "Supplier A")
        service = TenantService(store)
        analyst = Principal("A", "analyst", "ANALYST")
        reviewer = Principal("A", "reviewer", "REVIEWER")
        service.store_evidence_document(analyst, _doc())
        assert service.evidence_reviews.current_state("A", "DOC-1") is None
        assert service.evidence_reviews.verified_document_ids("A") == set()
        service.review_evidence_document(reviewer, "DOC-1", "VERIFIED", "source checked")
        assert service.evidence_reviews.current_state("A", "DOC-1") == "VERIFIED"
        assert service.evidence_reviews.verified_document_ids("A") == {"DOC-1"}
        service.review_evidence_document(reviewer, "DOC-1", "REJECTED", "later conflict found")
        assert service.evidence_reviews.current_state("A", "DOC-1") == "REJECTED"
        assert service.evidence_reviews.verified_document_ids("A") == set()
        history = service.evidence_reviews.history("A", "DOC-1")
        assert [item["state"] for item in history] == ["VERIFIED", "REJECTED"]
    finally:
        store.close()


def test_verification_state_is_tenant_scoped_for_same_document_id(tmp_path):
    store = Storage(tmp_path / "verify.db")
    try:
        store.create_workspace("A", "Supplier A")
        store.create_workspace("B", "Supplier B")
        service = TenantService(store)
        service.store_evidence_document(Principal("A", "analyst-a", "ANALYST"), _doc("A"))
        service.store_evidence_document(Principal("B", "analyst-b", "ANALYST"), _doc("B"))
        service.review_evidence_document(Principal("A", "reviewer-a", "REVIEWER"), "DOC-1", "VERIFIED")
        assert service.evidence_reviews.current_state("A", "DOC-1") == "VERIFIED"
        assert service.evidence_reviews.current_state("B", "DOC-1") is None
    finally:
        store.close()
