from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from typing import Callable, Iterable, TypeVar

from .audit import tenant_audit_trail
from .auth import Principal
from .case_factory import case_from_gated_analysis
from .claimability import apply_registered_evidence_gate
from .engine import analyze_claim
from .evidence import EvidenceDocument
from .models import EntitlementBasis, ExposureLine, RecoveryEvent
from .package import build_claim_package
from .storage import Storage
from .verification import EvidenceReviewStore, EntitlementReviewStore, ReviewState
from .workflow import ClaimCase, PaymentRecord, WorkflowState, advance_case, record_payment

T = TypeVar("T")


class TenantService:
    """Tenant-scoped business boundary with independent evidence/entitlement review."""

    _REVIEWER_ALLOWED_TRANSITIONS = {
        "ANALYSIS",
        "EVIDENCE_COLLECTION",
        "REVIEW",
        "CLAIM_READY",
        "REJECTED",
    }

    def __init__(self, storage: Storage):
        self.storage = storage
        self.evidence_reviews = EvidenceReviewStore(storage)
        self.entitlement_reviews = EntitlementReviewStore(storage)

    def _mutate(self, operation: Callable[..., T], *args, **kwargs) -> T:
        """Fail closed at the application boundary on interrupted SQLite writes."""
        try:
            return operation(*args, **kwargs)
        except Exception:
            self.storage.conn.rollback()
            raise

    @staticmethod
    def _require_source_write(principal: Principal) -> None:
        if principal.role not in {"ADMIN", "ANALYST"}:
            raise PermissionError("ROLE_NOT_AUTHORIZED_FOR_SOURCE_WRITE")

    @staticmethod
    def _require_reviewer(principal: Principal) -> None:
        if principal.role != "REVIEWER":
            raise PermissionError("REVIEWER_REQUIRED_FOR_INDEPENDENT_VERIFICATION")

    def _require_independent_actor_review(
        self,
        principal: Principal,
        *,
        entity_type: str,
        entity_id: str,
    ) -> None:
        row = self.storage.conn.execute(
            """
            SELECT actor_id
            FROM audit_events
            WHERE workspace_id=? AND entity_type=? AND entity_id=? AND action='CREATE'
            ORDER BY event_id ASC
            LIMIT 1
            """,
            (principal.workspace_id, entity_type, entity_id),
        ).fetchone()
        if row is None:
            raise PermissionError("SOURCE_CREATOR_PROVENANCE_REQUIRED_FOR_REVIEW")
        if row["actor_id"] == principal.actor_id:
            raise PermissionError("SELF_REVIEW_NOT_ALLOWED")

    def store_recovery_event(self, principal: Principal, event: RecoveryEvent) -> None:
        self._require_source_write(principal)
        self._mutate(
            self.storage.put_recovery_event,
            principal.workspace_id,
            principal.actor_id,
            event,
        )

    def get_recovery_event(self, principal: Principal, event_id: str) -> RecoveryEvent | None:
        return self.storage.get_recovery_event(principal.workspace_id, event_id)

    def store_exposure_line(self, principal: Principal, line: ExposureLine) -> None:
        self._require_source_write(principal)
        self._mutate(
            self.storage.put_exposure_line,
            principal.workspace_id,
            principal.actor_id,
            line,
        )

    def get_exposure_line(self, principal: Principal, exposure_id: str) -> ExposureLine | None:
        return self.storage.get_exposure_line(principal.workspace_id, exposure_id)

    def store_entitlement_basis(self, principal: Principal, basis: EntitlementBasis) -> None:
        self._require_source_write(principal)
        self._mutate(
            self.storage.put_entitlement_basis,
            principal.workspace_id,
            principal.actor_id,
            basis,
        )

    def get_entitlement_basis(self, principal: Principal, entitlement_id: str) -> EntitlementBasis | None:
        return self.storage.get_entitlement_basis(principal.workspace_id, entitlement_id)

    def review_entitlement_basis(
        self,
        principal: Principal,
        entitlement_id: str,
        state: ReviewState,
        note: str = "",
    ) -> None:
        self._require_reviewer(principal)
        self._require_independent_actor_review(
            principal,
            entity_type="ENTITLEMENT_BASIS",
            entity_id=entitlement_id,
        )
        self._mutate(
            self.entitlement_reviews.review,
            principal.workspace_id,
            principal.actor_id,
            entitlement_id,
            state,
            note,
        )

    def store_evidence_document(
        self, principal: Principal, document: EvidenceDocument
    ) -> None:
        self._require_source_write(principal)
        if document.workspace_id != principal.workspace_id:
            raise PermissionError("CROSS_TENANT_DOCUMENT_REJECTED")
        self._mutate(
            self.storage.put_evidence_document,
            principal.workspace_id,
            principal.actor_id,
            document,
        )

    def get_evidence_document(
        self, principal: Principal, document_id: str
    ) -> EvidenceDocument | None:
        return self.storage.get_evidence_document(principal.workspace_id, document_id)

    def review_evidence_document(
        self,
        principal: Principal,
        document_id: str,
        state: ReviewState,
        note: str = "",
    ) -> None:
        self._require_reviewer(principal)
        self._require_independent_actor_review(
            principal,
            entity_type="EVIDENCE_DOCUMENT",
            entity_id=document_id,
        )
        self._mutate(
            self.evidence_reviews.review,
            principal.workspace_id,
            principal.actor_id,
            document_id,
            state,
            note,
        )

    def analyze_event(self, principal: Principal, event_id: str, supplier_id: str) -> dict:
        """Recompute from persisted truth plus independent reviewer attestations."""
        event = self.storage.get_recovery_event(principal.workspace_id, event_id)
        if event is None:
            raise KeyError("RECOVERY_EVENT_NOT_FOUND")
        exposures = self.storage.list_exposure_lines(principal.workspace_id, event_id)
        stored_entitlements = self.storage.list_entitlement_bases(principal.workspace_id, event_id)
        verified_entitlement_ids = self.entitlement_reviews.verified_entitlement_ids(
            principal.workspace_id
        )
        entitlement_review_states = {
            basis.entitlement_id: self.entitlement_reviews.current_state(
                principal.workspace_id, basis.entitlement_id
            )
            for basis in stored_entitlements
        }
        entitlements = [
            basis
            if basis.entitlement_id in verified_entitlement_ids
            else replace(basis, support_state="UNKNOWN", legal_review_required=True)
            for basis in stored_entitlements
        ]
        documents = self.storage.list_evidence_documents(principal.workspace_id)
        verified_document_ids = self.evidence_reviews.verified_document_ids(
            principal.workspace_id
        )
        raw = analyze_claim(event, exposures, entitlements)
        gated = apply_registered_evidence_gate(
            raw,
            documents,
            workspace_id=principal.workspace_id,
            supplier_id=supplier_id,
            verified_document_ids=verified_document_ids,
            require_verification=True,
        )
        for line in gated["claim_lines"]:
            entitlement_id = line.get("lineage", {}).get("entitlement_id")
            line["entitlement_review_state"] = (
                entitlement_review_states.get(entitlement_id)
                if entitlement_id
                else None
            )
        gated["independent_entitlement_verification_required"] = True
        return gated

    def build_claim_package(self, principal: Principal, event_id: str, supplier_id: str) -> dict:
        package = build_claim_package(self.analyze_event(principal, event_id, supplier_id))
        trail = tenant_audit_trail(self.storage, principal.workspace_id)
        package["audit_trail"] = trail
        package["audit_event_count"] = len(trail)
        package["workspace_id"] = principal.workspace_id
        return package

    def create_case(
        self,
        principal: Principal,
        event_id: str,
        supplier_id: str,
        *,
        selected_exposure_ids: Iterable[str] | None = None,
    ) -> ClaimCase:
        if principal.role not in {"ADMIN", "ANALYST"}:
            raise PermissionError("ROLE_NOT_AUTHORIZED_FOR_CASE_CREATE")
        gated = self.analyze_event(principal, event_id, supplier_id)
        case = case_from_gated_analysis(
            principal.workspace_id,
            gated,
            selected_exposure_ids=selected_exposure_ids,
        )
        self._mutate(
            self.storage.put_claim_case,
            principal.workspace_id,
            principal.actor_id,
            case,
        )
        return case

    def get_case(self, principal: Principal, case_id: str) -> ClaimCase | None:
        return self.storage.get_claim_case(principal.workspace_id, case_id)

    def advance_case(
        self,
        principal: Principal,
        case_id: str,
        new_state: WorkflowState,
        *,
        settled_amount: Decimal | None = None,
        settlement_evidence_ref: str | None = None,
    ) -> ClaimCase:
        if (
            principal.role == "REVIEWER"
            and new_state not in self._REVIEWER_ALLOWED_TRANSITIONS
        ):
            raise PermissionError("ROLE_NOT_AUTHORIZED_FOR_COMMERCIAL_DISPOSITION")
        current = self.storage.get_claim_case(principal.workspace_id, case_id)
        if current is None:
            raise KeyError("CLAIM_CASE_NOT_FOUND")
        updated = advance_case(
            current,
            new_state,
            settled_amount=settled_amount,
            settlement_evidence_ref=settlement_evidence_ref,
        )
        self._mutate(
            self.storage.put_claim_case,
            principal.workspace_id,
            principal.actor_id,
            updated,
        )
        return updated

    def record_payment(
        self,
        principal: Principal,
        case_id: str,
        payment: PaymentRecord,
    ) -> ClaimCase:
        if principal.role not in {"ADMIN", "ANALYST"}:
            raise PermissionError("ROLE_NOT_AUTHORIZED_FOR_PAYMENT")
        current = self.storage.get_claim_case(principal.workspace_id, case_id)
        if current is None:
            raise KeyError("CLAIM_CASE_NOT_FOUND")
        updated = record_payment(current, payment)
        self._mutate(
            self.storage.put_claim_case,
            principal.workspace_id,
            principal.actor_id,
            updated,
        )
        return updated
