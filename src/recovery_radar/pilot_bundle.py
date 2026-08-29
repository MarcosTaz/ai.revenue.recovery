from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from .bundle_ingest import ingest_bundle_atomic
from .evidence import EvidenceDocument
from .models import EntitlementBasis, ExposureLine, RecoveryEvent

BUNDLE_FORMAT = "RECOVERY_RADAR_PILOT_BUNDLE_V1"
MAX_BUNDLE_BYTES = 5 * 1024 * 1024
MAX_EVIDENCE_FILE_BYTES = 10 * 1024 * 1024
MAX_TOTAL_EVIDENCE_BYTES = 50 * 1024 * 1024
MAX_RECORDS_PER_SECTION = 10_000
_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")

_EVENT_TYPES = {
    "PROGRAM_CANCELLED",
    "VOLUME_REDUCTION",
    "SOURCING_TERMINATED",
    "ENGINEERING_CHANGE",
    "CUSTOMER_STOP_ORDER",
    "PHASE_OUT_ACCELERATED",
}
_EXPOSURE_CATEGORIES = {
    "RAW_MATERIAL",
    "E_AND_O",
    "WIP",
    "FINISHED_GOODS",
    "TOOLING",
    "NRE",
    "SUPPLIER_COMMITMENTS",
    "DEDICATED_CAPACITY",
    "OTHER",
}
_OWNERSHIP = {"SUPPLIER", "CUSTOMER", "UNKNOWN"}
_SUPPORT_STATES = {
    "SUPPORTED",
    "PARTIALLY_SUPPORTED",
    "CONFLICTING",
    "NOT_SUPPORTED",
    "UNKNOWN",
}
_EVIDENCE_TYPES = {
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
}


class PilotBundleError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class PilotBundle:
    format: str
    supplier_id: str
    event: RecoveryEvent
    exposures: tuple[ExposureLine, ...]
    entitlements: tuple[EntitlementBasis, ...]
    evidence_documents: tuple[EvidenceDocument, ...]


def _require_mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PilotBundleError(f"{name}_MUST_BE_OBJECT")
    return value


def _require_text(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PilotBundleError(f"{key.upper()}_REQUIRED")
    return value.strip()


def _string_allow_empty(data: dict[str, Any], key: str) -> str:
    value = data.get(key, "")
    if not isinstance(value, str):
        raise PilotBundleError(f"{key.upper()}_MUST_BE_STRING")
    return value.strip()


def _optional_text(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise PilotBundleError(f"{key.upper()}_INVALID")
    return value.strip()


def _strict_bool(data: dict[str, Any], key: str, *, default: bool = False) -> bool:
    value = data.get(key, default)
    if not isinstance(value, bool):
        raise PilotBundleError(f"{key.upper()}_MUST_BE_BOOLEAN")
    return value


def _decimal(data: dict[str, Any], key: str, *, default: str | None = None) -> Decimal:
    value = data.get(key, default)
    if value is None:
        raise PilotBundleError(f"{key.upper()}_REQUIRED")
    if isinstance(value, bool):
        raise PilotBundleError(f"{key.upper()}_INVALID_DECIMAL")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise PilotBundleError(f"{key.upper()}_INVALID_DECIMAL") from None
    if not parsed.is_finite():
        raise PilotBundleError(f"{key.upper()}_NON_FINITE")
    return parsed


def _date(value: Any, key: str, *, optional: bool = False) -> date | None:
    if value is None and optional:
        return None
    if not isinstance(value, str):
        raise PilotBundleError(f"{key.upper()}_INVALID_DATE")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise PilotBundleError(f"{key.upper()}_INVALID_DATE") from None


def _enum(value: str, allowed: set[str], key: str) -> str:
    if value not in allowed:
        raise PilotBundleError(f"{key.upper()}_UNSUPPORTED:{value}")
    return value


def _currency(value: str) -> str:
    if _CURRENCY_RE.fullmatch(value) is None:
        raise PilotBundleError(f"CURRENCY_INVALID_FORMAT:{value}")
    return value


def _bounded_list(data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key, [])
    if not isinstance(value, list):
        raise PilotBundleError(f"{key.upper()}_MUST_BE_ARRAY")
    if len(value) > MAX_RECORDS_PER_SECTION:
        raise PilotBundleError(f"{key.upper()}_TOO_MANY_RECORDS")
    return value


def _safe_evidence_path(root: Path, relative: str) -> Path:
    requested = Path(relative)
    if requested.is_absolute():
        raise PilotBundleError("EVIDENCE_FILE_PATH_ESCAPE")
    unresolved = root / requested
    if unresolved.is_symlink():
        raise PilotBundleError("EVIDENCE_FILE_SYMLINK_REJECTED")
    candidate = unresolved.resolve()
    root_resolved = root.resolve()
    if not candidate.is_relative_to(root_resolved):
        raise PilotBundleError("EVIDENCE_FILE_PATH_ESCAPE")
    if not candidate.is_file():
        raise PilotBundleError("EVIDENCE_FILE_NOT_FOUND")
    size = candidate.stat().st_size
    if size > MAX_EVIDENCE_FILE_BYTES:
        raise PilotBundleError("EVIDENCE_FILE_TOO_LARGE")
    return candidate


def load_pilot_bundle(path: str | Path, *, workspace_id: str) -> PilotBundle:
    """Load normalized pilot inputs while hashing concrete local evidence files.

    Documentary references may be empty when the source is genuinely missing;
    that gap is preserved for the evidence engine instead of being hidden by the
    importer. Concrete evidence records, when supplied, are always hashed from
    their file bytes rather than accepting caller-supplied hashes.
    """
    bundle_path = Path(path)
    if not bundle_path.is_file():
        raise PilotBundleError("BUNDLE_NOT_FOUND")
    if bundle_path.stat().st_size > MAX_BUNDLE_BYTES:
        raise PilotBundleError("BUNDLE_TOO_LARGE")
    try:
        payload = json.loads(bundle_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PilotBundleError("BUNDLE_INVALID_JSON_UTF8") from exc
    data = _require_mapping(payload, "BUNDLE")
    if data.get("format") != BUNDLE_FORMAT:
        raise PilotBundleError("BUNDLE_FORMAT_UNSUPPORTED")
    if not workspace_id.strip():
        raise PilotBundleError("WORKSPACE_ID_REQUIRED")
    supplier_id = _require_text(data, "supplier_id")

    event_data = _require_mapping(data.get("event"), "EVENT")
    event_type = _enum(_require_text(event_data, "event_type"), _EVENT_TYPES, "event_type")
    event = RecoveryEvent(
        event_id=_require_text(event_data, "event_id"),
        customer_id=_require_text(event_data, "customer_id"),
        program_id=_require_text(event_data, "program_id"),
        part_id=_require_text(event_data, "part_id"),
        event_type=event_type,
        event_date=_date(event_data.get("event_date"), "event_date"),
        expected_volume=_decimal(event_data, "expected_volume"),
        revised_volume=_decimal(event_data, "revised_volume"),
        source_ref=_require_text(event_data, "source_ref"),
        evidence_ref=_string_allow_empty(event_data, "evidence_ref"),
    )

    exposures: list[ExposureLine] = []
    exposure_ids: set[str] = set()
    for raw in _bounded_list(data, "exposures"):
        item = _require_mapping(raw, "EXPOSURE")
        exposure_id = _require_text(item, "exposure_id")
        if exposure_id in exposure_ids:
            raise PilotBundleError(f"DUPLICATE_EXPOSURE_ID:{exposure_id}")
        exposure_ids.add(exposure_id)
        category = _enum(_require_text(item, "category"), _EXPOSURE_CATEGORIES, "category")
        ownership = _enum(_require_text(item, "ownership"), _OWNERSHIP, "ownership")
        currency = _currency(_require_text(item, "currency"))
        exposures.append(
            ExposureLine(
                exposure_id=exposure_id,
                event_id=_require_text(item, "event_id"),
                economic_loss_id=_require_text(item, "economic_loss_id"),
                category=category,
                quantity=_decimal(item, "quantity"),
                unit_cost=_decimal(item, "unit_cost"),
                currency=currency,
                inventory_or_cost_ref=_string_allow_empty(item, "inventory_or_cost_ref"),
                ownership=ownership,
                mitigation_amount=_decimal(item, "mitigation_amount", default="0"),
                mitigation_evidence_ref=_optional_text(item, "mitigation_evidence_ref"),
                already_reimbursed_amount=_decimal(item, "already_reimbursed_amount", default="0"),
                reimbursement_evidence_ref=_optional_text(item, "reimbursement_evidence_ref"),
            )
        )

    entitlements: list[EntitlementBasis] = []
    entitlement_ids: set[str] = set()
    for raw in _bounded_list(data, "entitlements"):
        item = _require_mapping(raw, "ENTITLEMENT")
        entitlement_id = _require_text(item, "entitlement_id")
        if entitlement_id in entitlement_ids:
            raise PilotBundleError(f"DUPLICATE_ENTITLEMENT_ID:{entitlement_id}")
        entitlement_ids.add(entitlement_id)
        support_state = _enum(
            _require_text(item, "support_state"), _SUPPORT_STATES, "support_state"
        )
        cap_value = item.get("recoverable_cap")
        entitlements.append(
            EntitlementBasis(
                entitlement_id=entitlement_id,
                event_id=_require_text(item, "event_id"),
                economic_loss_id=_require_text(item, "economic_loss_id"),
                support_state=support_state,
                contractual_basis_ref=_optional_text(item, "contractual_basis_ref"),
                supporting_document_ref=_optional_text(item, "supporting_document_ref"),
                recoverable_cap=(None if cap_value is None else _decimal(item, "recoverable_cap")),
                legal_review_required=_strict_bool(item, "legal_review_required"),
            )
        )

    evidence_documents: list[EvidenceDocument] = []
    document_ids: set[str] = set()
    total_evidence_bytes = 0
    root = bundle_path.parent
    for raw in _bounded_list(data, "evidence"):
        item = _require_mapping(raw, "EVIDENCE")
        document_id = _require_text(item, "document_id")
        if document_id in document_ids:
            raise PilotBundleError(f"DUPLICATE_DOCUMENT_ID:{document_id}")
        document_ids.add(document_id)
        evidence_type = _enum(
            _require_text(item, "evidence_type"), _EVIDENCE_TYPES, "evidence_type"
        )
        evidence_file = _safe_evidence_path(root, _require_text(item, "file"))
        total_evidence_bytes += evidence_file.stat().st_size
        if total_evidence_bytes > MAX_TOTAL_EVIDENCE_BYTES:
            raise PilotBundleError("TOTAL_EVIDENCE_TOO_LARGE")
        signed = item.get("signed")
        if signed is not None and not isinstance(signed, bool):
            raise PilotBundleError("SIGNED_MUST_BE_BOOLEAN_OR_NULL")
        evidence_documents.append(
            EvidenceDocument.from_bytes(
                document_id=document_id,
                workspace_id=workspace_id,
                supplier_id=_require_text(item, "supplier_id"),
                customer_id=_require_text(item, "customer_id"),
                program_id=_require_text(item, "program_id"),
                evidence_type=evidence_type,
                source_ref=_require_text(item, "source_ref"),
                version_id=_require_text(item, "version_id"),
                document_date=_date(item.get("document_date"), "document_date", optional=True),
                content=evidence_file.read_bytes(),
                signed=signed,
            )
        )

    return PilotBundle(
        format=BUNDLE_FORMAT,
        supplier_id=supplier_id,
        event=event,
        exposures=tuple(exposures),
        entitlements=tuple(entitlements),
        evidence_documents=tuple(evidence_documents),
    )


def ingest_pilot_bundle(gateway, token: str, bundle: PilotBundle) -> dict[str, Any]:
    """Atomically persist normalized source truth; verification remains separate."""
    return ingest_bundle_atomic(gateway, token, bundle)
