from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from .auth import Principal
from .case_factory import case_from_gated_analysis
from .claimability import apply_registered_evidence_gate
from .engine import analyze_claim
from .evidence import EvidenceDocument
from .models import EntitlementBasis, ExposureLine, RecoveryEvent
from .package import build_claim_package
from .storage import Storage
from .workflow import ClaimCase, PaymentRecord, WorkflowState, advance_case, record_payment


class TenantService:
    """Tenant-scoped business boundary.

    Claim amounts are never accepted from callers. Claim analysis is recomputed
    from persisted source records and registered evidence inside the tenant.
    """

    _REVIEWER_ALLOWED_TRANSITIONS = {
        "ANALYSIS",
        "EVIDENCE_COLLECTION",
        "REVIEW",
        "CLAIM_READY",
        "REJECTED",
    }

    def __init__(self, storage: Storage):
        self.storage = storage

    @staticmethod
    def _require_source_write(principal: Principal) -> None:
        if principal.role not in {"ADMIN", "ANALYST"}:
            raise PermissionError("ROLE_NOT_AUTHORIZED_FOR_SOURCE_WRITE")

    def store_recovery_event(self, principal: Principal, event: RecoveryEvent) -> None:
        self._require_source_write(principal)
        self.storage.put_recovery_event(principal.workspace_id, principal.actor_id, event)

    def get_recovery_event(self, principal: Principal, event_id: str) -> RecoveryEvent | None:
        return self.storage.get_recovery_event(principal.workspace_id, event_id)

    def store_exposure_line(self, principal: Principal, line: ExposureLine) -> None:
        self._require_source_write(principal)
        self.storage.put_exposure_line(principal.workspace_id, principal.actor_id, line)

    def get_exposure_line(self, principal: Principal, exposure_id: str) -> ExposureLine | None:
        return self.storage.get_exposure_line(principal.workspace_id, exposure_id)

    def store_entitlement_basis(self, principal: Principal, basis: EntitlementBasis) -> None:
        self._require_source_write(principal)
        self.storage.put_entitlement_basis(principal.workspace_id, principal.actor_id, basis)

    def get_entitlement_basis(self, principal: Principal, entitlement_id: str) -> EntitlementBasis | None:
        return self.storage.get_entitlement_basis(principal.workspace_id, entitlement_id)

    def analyze_event(self, principal: Principal, event_id: str, supplier_id: str) -> dict:
        """Recompute a registry-gated analysis from persisted tenant source truth."""
        event = self.storage.get_recovery_event(principal.workspace_id, event_id)
        if event is None:
            raise KeyError("RECOVERY_EVENT_NOT_FOUND")
        exposures = self.storage.list_exposure_lines(principal.workspace_id, event_id)
        entitlements = self.storage.list_entitlement_bases(principal.workspace_id, event_id)
        documents = self.storage.list_evidence_documents(principal.workspace_id)
        raw = analyze_claim(event, exposures, entitlements)
        return apply_registered_evidence_gate(
            raw,
            documents,
            workspace_id=principal.workspace_id,
            supplier_id=supplier_id,
        )

    def build_claim_package(self, principal: Principal, event_id: str, supplier_id: str) -> dict:
        package = build_claim_package(self.analyze_event(principal, event_id, supplier_id))
        package["audit_event_count"] = self.storage.audit_count(principal.workspace_id)
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
        """Derive and persist a claim from tenant-owned persisted source truth.

        The caller can choose which already-claimable exposure lines to include,
        but cannot provide case ID, amount, currency, analysis fingerprint, or a
        precomputed analysis object.
        """
        if principal.role not in {"ADMIN", "ANALYST"}:
            raise PermissionError("ROLE_NOT_AUTHORIZED_FOR_CASE_CREATE")
        gated = self.analyze_event(principal, event_id, supplier_id)
        case = case_from_gated_analysis(
            principal.workspace_id,
            gated,
            selected_exposure_ids=selected_exposure_ids,
        )
        self.storage.put_claim_case(principal.workspace_id, principal.actor_id, case)
        return case

    def get_case(self, principal: Principal, case_id: str) -> ClaimCase | None:
        return self.storage.get_claim_case(principal.workspace_id, case_id)

    def store_evidence_document(
        self, principal: Principal, document: EvidenceDocument
    ) -> None:
        if document.workspace_id != principal.workspace_id:
            raise PermissionError("CROSS_TENANT_DOCUMENT_REJECTED")
        self.storage.put_evidence_document(
            principal.workspace_id, principal.actor_id, document
        )

    def get_evidence_document(
        self, principal: Principal, document_id: str
    ) -> EvidenceDocument | None:
        return self.storage.get_evidence_document(principal.workspace_id, document_id)

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
        self.storage.put_claim_case(principal.workspace_id, principal.actor_id, updated)
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
        self.storage.put_claim_case(principal.workspace_id, principal.actor_id, updated)
        return updated
