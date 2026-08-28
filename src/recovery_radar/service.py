from __future__ import annotations

from decimal import Decimal

from .auth import Principal
from .storage import Storage
from .workflow import ClaimCase, PaymentRecord, WorkflowState, advance_case, record_payment


class TenantService:
    """Business boundary scoped by an already-authenticated principal."""

    def __init__(self, storage: Storage):
        self.storage = storage

    def create_case(self, principal: Principal, case: ClaimCase) -> None:
        if principal.role not in {"ADMIN", "ANALYST"}:
            raise PermissionError("ROLE_NOT_AUTHORIZED_FOR_CASE_CREATE")
        if case.workspace_id != principal.workspace_id:
            raise PermissionError("CROSS_TENANT_CASE_REJECTED")
        if case.state != "DETECTED" or case.settled_amount != 0 or case.payments:
            raise ValueError("CASE_MUST_START_DETECTED")
        self.storage.put_claim_case(principal.workspace_id, principal.actor_id, case)

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
