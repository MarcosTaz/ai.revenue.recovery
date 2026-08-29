from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date
from typing import Literal

EvidenceType = Literal[
    "CUSTOMER_NOTICE",
    "CONTRACT",
    "PURCHASE_ORDER",
    "RELEASE",
    "FORECAST",
    "INVENTORY_RECORD",
    "COST_RECORD",
    "TOOLING_APPROVAL",
    "MITIGATION_RECORD",
    "REIMBURSEMENT_RECORD",
    "SETTLEMENT",
    "PAYMENT",
    "OTHER",
]


@dataclass(frozen=True, slots=True)
class EvidenceDocument:
    document_id: str
    workspace_id: str
    supplier_id: str
    customer_id: str
    program_id: str
    evidence_type: EvidenceType
    source_ref: str
    version_id: str
    document_date: date | None
    content_sha256: str
    signed: bool | None = None

    @classmethod
    def from_bytes(
        cls,
        *,
        document_id: str,
        workspace_id: str,
        supplier_id: str,
        customer_id: str,
        program_id: str,
        evidence_type: EvidenceType,
        source_ref: str,
        version_id: str,
        document_date: date | None,
        content: bytes,
        signed: bool | None = None,
    ) -> "EvidenceDocument":
        return cls(
            document_id=document_id,
            workspace_id=workspace_id,
            supplier_id=supplier_id,
            customer_id=customer_id,
            program_id=program_id,
            evidence_type=evidence_type,
            source_ref=source_ref,
            version_id=version_id,
            document_date=document_date,
            content_sha256=hashlib.sha256(content).hexdigest(),
            signed=signed,
        )


@dataclass(frozen=True, slots=True)
class EvidenceAssessment:
    state: Literal["ACCEPTED", "REVIEW_REQUIRED"]
    reasons: tuple[str, ...]


def assess_document_scope(
    document: EvidenceDocument,
    *,
    workspace_id: str,
    supplier_id: str,
    customer_id: str,
    program_id: str,
) -> EvidenceAssessment:
    """Check identity scope only; document text never changes system behavior."""
    reasons: list[str] = []
    if document.workspace_id != workspace_id:
        reasons.append("CROSS_TENANT_DOCUMENT")
    if document.supplier_id != supplier_id:
        reasons.append("WRONG_SUPPLIER")
    if document.customer_id != customer_id:
        reasons.append("WRONG_CUSTOMER")
    if document.program_id != program_id:
        reasons.append("WRONG_PROGRAM")
    if not document.source_ref:
        reasons.append("MISSING_SOURCE_REF")
    if not document.version_id:
        reasons.append("MISSING_VERSION_ID")
    if document.evidence_type in {"CONTRACT", "TOOLING_APPROVAL", "SETTLEMENT"} and document.signed is not True:
        reasons.append("SIGNATURE_NOT_CONFIRMED")
    return EvidenceAssessment(
        state="REVIEW_REQUIRED" if reasons else "ACCEPTED",
        reasons=tuple(reasons),
    )


class EvidenceRegistry:
    """In-memory deterministic registry used before persistence.

    Exact duplicate bytes are represented once per workspace. Reusing a document
    ID for different bytes fails closed instead of silently replacing evidence.
    """

    def __init__(self) -> None:
        self._by_id: dict[tuple[str, str], EvidenceDocument] = {}
        self._by_hash: dict[tuple[str, str], str] = {}

    def register(self, document: EvidenceDocument) -> EvidenceDocument:
        key = (document.workspace_id, document.document_id)
        existing = self._by_id.get(key)
        if existing is not None:
            if existing == document:
                return existing
            raise ValueError("DOCUMENT_ID_VERSION_CONFLICT")
        hash_key = (document.workspace_id, document.content_sha256)
        duplicate_id = self._by_hash.get(hash_key)
        if duplicate_id is not None:
            raise ValueError(f"DUPLICATE_DOCUMENT_CONTENT:{duplicate_id}")
        self._by_id[key] = document
        self._by_hash[hash_key] = document.document_id
        return document

    def get(self, workspace_id: str, document_id: str) -> EvidenceDocument | None:
        return self._by_id.get((workspace_id, document_id))


def treat_extracted_text_as_untrusted(text: str) -> dict[str, str | bool]:
    """Mark extraction as evidence content, never as executable instructions."""
    return {
        "text": text,
        "trust": "UNTRUSTED_DOCUMENT_CONTENT",
        "can_override_system_rules": False,
    }
