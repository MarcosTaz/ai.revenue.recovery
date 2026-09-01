from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import unicodedata


ALLOWED_CONTENT_TYPES = frozenset({
    "application/pdf",
    "text/csv",
    "text/plain",
    "application/json",
})
MAX_EVIDENCE_BYTES = 25 * 1024 * 1024


@dataclass(frozen=True)
class EvidenceManifest:
    organization_id: str
    evidence_id: str
    filename: str
    content_type: str
    byte_size: int
    sha256: str
    captured_at: str


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    return value.strip()


def build_evidence_manifest(
    *,
    organization_id: str,
    evidence_id: str,
    filename: str,
    content_type: str,
    content: bytes,
    captured_at: str,
) -> EvidenceManifest:
    """Validate raw evidence metadata before any parser or model sees content.

    This boundary intentionally does not parse or execute document content. It
    establishes tenant identity, bounded size, approved content type, immutable
    content hash and an offset-aware capture time. Malware scanning, file-signature
    verification and durable encrypted object storage remain production deployment
    responsibilities and must not be inferred from this manifest.
    """
    organization_id = _required_text(organization_id, "organization_id")
    evidence_id = _required_text(evidence_id, "evidence_id")
    filename = unicodedata.normalize("NFC", _required_text(filename, "filename"))
    content_type = _required_text(content_type, "content_type")
    captured_at = _required_text(captured_at, "captured_at")

    if filename in {".", ".."}:
        raise ValueError("filename is required")
    if "/" in filename or "\\" in filename or "\x00" in filename:
        raise ValueError("filename must not contain path separators or NUL")
    if any(unicodedata.category(char).startswith("C") for char in filename):
        raise ValueError("filename must not contain control or format characters")

    normalized_type = content_type.split(";", 1)[0].strip().lower()
    if normalized_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError("unsupported content type")
    if not isinstance(content, bytes):
        raise TypeError("content must be bytes")
    if not content:
        raise ValueError("evidence content must not be empty")
    if len(content) > MAX_EVIDENCE_BYTES:
        raise ValueError("evidence content exceeds size limit")
    try:
        captured = datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("captured_at must be ISO-8601") from exc
    if captured.tzinfo is None or captured.utcoffset() is None:
        raise ValueError("captured_at must be timezone-aware")

    digest = hashlib.sha256(content).hexdigest()
    return EvidenceManifest(
        organization_id=organization_id,
        evidence_id=evidence_id,
        filename=filename,
        content_type=normalized_type,
        byte_size=len(content),
        sha256=digest,
        captured_at=captured.isoformat(),
    )
