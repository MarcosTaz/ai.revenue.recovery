from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ScanStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    NOT_RUN = "NOT_RUN"


class IntakeState(str, Enum):
    ACCEPTABLE_FOR_CONTROLLED_STORAGE = "ACCEPTABLE_FOR_CONTROLLED_STORAGE"
    REJECTED = "REJECTED"
    REQUIRES_SCAN = "REQUIRES_SCAN"
    UNKNOWN = "UNKNOWN"


ALLOWED_CONTENT_TYPES = frozenset({
    "application/pdf",
    "text/csv",
    "text/plain",
    "application/json",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
})

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024


@dataclass(frozen=True)
class EvidenceIntakeInput:
    organization_id: str
    filename: str
    content_type: str
    size_bytes: int
    sha256: str
    scan_status: ScanStatus


@dataclass(frozen=True)
class EvidenceIntakeDecision:
    state: IntakeState
    eligible_for_storage: bool
    eligible_for_parsing: bool
    explanation: str


def evaluate_evidence_intake(item: EvidenceIntakeInput) -> EvidenceIntakeDecision:
    if not item.organization_id.strip() or not item.filename.strip():
        return EvidenceIntakeDecision(IntakeState.REJECTED, False, False, "Tenant identity and filename are required.")
    if item.content_type not in ALLOWED_CONTENT_TYPES:
        return EvidenceIntakeDecision(IntakeState.REJECTED, False, False, "Content type is not in the controlled allowlist.")
    if item.size_bytes <= 0 or item.size_bytes > MAX_FILE_SIZE_BYTES:
        return EvidenceIntakeDecision(IntakeState.REJECTED, False, False, "File size is outside the controlled intake range.")
    try:
        if len(item.sha256) != 64:
            raise ValueError
        int(item.sha256, 16)
    except ValueError:
        return EvidenceIntakeDecision(IntakeState.REJECTED, False, False, "A valid SHA-256 digest is required before storage.")
    if item.scan_status is ScanStatus.FAILED:
        return EvidenceIntakeDecision(IntakeState.REJECTED, False, False, "Security scan failed.")
    if item.scan_status is ScanStatus.NOT_RUN:
        return EvidenceIntakeDecision(IntakeState.REQUIRES_SCAN, False, False, "Security scan must pass before controlled storage or parsing.")
    return EvidenceIntakeDecision(
        IntakeState.ACCEPTABLE_FOR_CONTROLLED_STORAGE,
        True,
        True,
        "Metadata, size, hash and external scan gate passed. Parser output must still remain separate from the immutable original.",
    )
