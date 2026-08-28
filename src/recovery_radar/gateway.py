from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from .auth import AuthService, Role
from .evidence import EvidenceDocument
from .models import EntitlementBasis, ExposureLine, RecoveryEvent
from .service import TenantService
from .verification import ReviewState
from .workflow import ClaimCase, PaymentRecord, WorkflowState


class RecoveryRadarGateway:
    """Token-authenticated application boundary for an assisted pilot."""

    def __init__(self, storage):
        self.auth = AuthService(storage)
        self.tenant = TenantService(storage)

    def bootstrap_workspace_admin(self, workspace_id: str, actor_id: str) -> str:
        return self.auth.bootstrap_workspace_admin(workspace_id, actor_id)

    def issue_key(self, admin_token: str, actor_id: str, role: Role) -> str:
        return self.auth.issue_key(admin_token, actor_id, role)

    def revoke_key(self, admin_token: str, key_id: str) -> None:
        self.auth.revoke_key(admin_token, key_id)

    def store_recovery_event(self, token: str, event: RecoveryEvent) -> None:
        self.tenant.store_recovery_event(self.auth.authenticate(token), event)

    def store_exposure_line(self, token: str, line: ExposureLine) -> None:
        self.tenant.store_exposure_line(self.auth.authenticate(token), line)

    def store_entitlement_basis(self, token: str, basis: EntitlementBasis) -> None:
        self.tenant.store_entitlement_basis(self.auth.authenticate(token), basis)

    def review_entitlement_basis(
        self,
        token: str,
        entitlement_id: str,
        state: ReviewState,
        note: str = "",
    ) -> None:
        self.tenant.review_entitlement_basis(
            self.auth.authenticate(token), entitlement_id, state, note
        )

    def store_evidence_document(self, token: str, document: EvidenceDocument) -> None:
        self.tenant.store_evidence_document(self.auth.authenticate(token), document)

    def review_evidence_document(
        self,
        token: str,
        document_id: str,
        state: ReviewState,
        note: str = "",
    ) -> None:
        self.tenant.review_evidence_document(
            self.auth.authenticate(token), document_id, state, note
        )

    def analyze_event(self, token: str, event_id: str, supplier_id: str) -> dict:
        return self.tenant.analyze_event(
            self.auth.authenticate(token), event_id, supplier_id
        )

    def build_claim_package(self, token: str, event_id: str, supplier_id: str) -> dict:
        return self.tenant.build_claim_package(
            self.auth.authenticate(token), event_id, supplier_id
        )

    def create_case(
        self,
        token: str,
        event_id: str,
        supplier_id: str,
        *,
        selected_exposure_ids: Iterable[str] | None = None,
    ) -> ClaimCase:
        return self.tenant.create_case(
            self.auth.authenticate(token),
            event_id,
            supplier_id,
            selected_exposure_ids=selected_exposure_ids,
        )

    def get_case(self, token: str, case_id: str) -> ClaimCase | None:
        return self.tenant.get_case(self.auth.authenticate(token), case_id)

    def advance_case(
        self,
        token: str,
        case_id: str,
        new_state: WorkflowState,
        *,
        settled_amount: Decimal | None = None,
        settlement_evidence_ref: str | None = None,
    ) -> ClaimCase:
        return self.tenant.advance_case(
            self.auth.authenticate(token),
            case_id,
            new_state,
            settled_amount=settled_amount,
            settlement_evidence_ref=settlement_evidence_ref,
        )

    def record_payment(
        self, token: str, case_id: str, payment: PaymentRecord
    ) -> ClaimCase:
        return self.tenant.record_payment(
            self.auth.authenticate(token), case_id, payment
        )
