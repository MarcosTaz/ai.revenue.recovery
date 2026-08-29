from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .export import EXPORT_FORMAT
from .scope_manifest import FORMAT as SOURCE_SCOPE_FORMAT
from .t2_io import SCORECARD_FORMAT


def _read_verified_bytes(path: str | Path, expected_sha256: str) -> bytes:
    source = Path(path)
    if not source.is_file():
        raise RuntimeError("ARTIFACT_FILE_NOT_FOUND")
    if len(expected_sha256) != 64 or any(ch not in "0123456789abcdef" for ch in expected_sha256):
        raise RuntimeError("EXPECTED_ARTIFACT_SHA256_INVALID")
    content = source.read_bytes()
    actual = hashlib.sha256(content).hexdigest()
    if actual != expected_sha256:
        raise RuntimeError("ARTIFACT_SHA256_MISMATCH")
    return content


def _json_object(content: bytes) -> dict[str, Any]:
    try:
        value = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("ARTIFACT_INVALID_JSON_UTF8") from exc
    if not isinstance(value, dict):
        raise RuntimeError("ARTIFACT_ROOT_MUST_BE_OBJECT")
    return value


def verify_claim_package_artifact(path: str | Path, expected_sha256: str) -> dict[str, Any]:
    content = _read_verified_bytes(path, expected_sha256)
    envelope = _json_object(content)
    if envelope.get("format") != EXPORT_FORMAT or not isinstance(envelope.get("package"), dict):
        raise RuntimeError("CLAIM_PACKAGE_EXPORT_FORMAT_INVALID")
    return {
        "kind": "CLAIM_PACKAGE",
        "format": EXPORT_FORMAT,
        "artifact_sha256": expected_sha256,
        "byte_length": len(content),
        "status": "VERIFIED",
    }


def verify_scorecard_artifact(path: str | Path, expected_sha256: str) -> dict[str, Any]:
    content = _read_verified_bytes(path, expected_sha256)
    envelope = _json_object(content)
    scorecard = envelope.get("scorecard")
    if envelope.get("format") != SCORECARD_FORMAT or not isinstance(scorecard, dict):
        raise RuntimeError("T2_SCORECARD_EXPORT_FORMAT_INVALID")
    internal = scorecard.get("scorecard_sha256")
    if not isinstance(internal, str):
        raise RuntimeError("T2_SCORECARD_INTERNAL_SHA256_MISSING")
    unsigned = dict(scorecard)
    del unsigned["scorecard_sha256"]
    canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    actual_internal = hashlib.sha256(canonical).hexdigest()
    if actual_internal != internal:
        raise RuntimeError("T2_SCORECARD_INTERNAL_SHA256_MISMATCH")
    return {
        "kind": "T2_SCORECARD",
        "format": SCORECARD_FORMAT,
        "artifact_sha256": expected_sha256,
        "scorecard_sha256": internal,
        "byte_length": len(content),
        "status": "VERIFIED",
    }


def verify_source_scope_artifact(
    path: str | Path,
    expected_sha256: str,
    *,
    expected_source_scope_sha256: str | None = None,
) -> dict[str, Any]:
    content = _read_verified_bytes(path, expected_sha256)
    manifest = _json_object(content)
    if manifest.get("format") != SOURCE_SCOPE_FORMAT:
        raise RuntimeError("SOURCE_SCOPE_EXPORT_FORMAT_INVALID")
    internal = manifest.get("source_scope_sha256")
    if not isinstance(internal, str):
        raise RuntimeError("SOURCE_SCOPE_INTERNAL_SHA256_MISSING")
    unsigned = dict(manifest)
    del unsigned["source_scope_sha256"]
    canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    actual_internal = hashlib.sha256(canonical).hexdigest()
    if actual_internal != internal:
        raise RuntimeError("SOURCE_SCOPE_INTERNAL_SHA256_MISMATCH")
    if expected_source_scope_sha256 is not None:
        if len(expected_source_scope_sha256) != 64 or any(
            ch not in "0123456789abcdef" for ch in expected_source_scope_sha256
        ):
            raise RuntimeError("EXPECTED_SOURCE_SCOPE_SHA256_INVALID")
        if internal != expected_source_scope_sha256:
            raise RuntimeError("SOURCE_SCOPE_SHA256_MISMATCH")
    return {
        "kind": "SOURCE_SCOPE",
        "format": SOURCE_SCOPE_FORMAT,
        "artifact_sha256": expected_sha256,
        "source_scope_sha256": internal,
        "byte_length": len(content),
        "status": "VERIFIED",
    }