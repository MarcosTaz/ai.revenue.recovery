from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

EXPORT_FORMAT = "RECOVERY_RADAR_CLAIM_PACKAGE_V1"


def canonical_claim_package_bytes(package: dict[str, Any]) -> bytes:
    """Serialize a claim package deterministically without adding new truth."""
    envelope = {
        "format": EXPORT_FORMAT,
        "package": package,
    }
    return (
        json.dumps(
            envelope,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")


def claim_package_export_manifest(package: dict[str, Any]) -> dict[str, Any]:
    content = canonical_claim_package_bytes(package)
    return {
        "format": EXPORT_FORMAT,
        "sha256": hashlib.sha256(content).hexdigest(),
        "byte_length": len(content),
    }


def export_claim_package_atomic(
    package: dict[str, Any], destination: str | Path
) -> dict[str, Any]:
    """Atomically persist a reproducible package and verify its final bytes."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    content = canonical_claim_package_bytes(package)
    expected_hash = hashlib.sha256(content).hexdigest()

    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=str(destination.parent)
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        persisted = destination.read_bytes()
        actual_hash = hashlib.sha256(persisted).hexdigest()
        if actual_hash != expected_hash or persisted != content:
            destination.unlink(missing_ok=True)
            raise RuntimeError("CLAIM_PACKAGE_EXPORT_VERIFICATION_FAILED")
        return {
            "format": EXPORT_FORMAT,
            "sha256": actual_hash,
            "byte_length": len(persisted),
            "path": str(destination),
        }
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def verify_claim_package_export(path: str | Path, expected_sha256: str) -> dict[str, Any]:
    path = Path(path)
    content = path.read_bytes()
    actual_hash = hashlib.sha256(content).hexdigest()
    if actual_hash != expected_sha256:
        raise RuntimeError("CLAIM_PACKAGE_EXPORT_HASH_MISMATCH")
    envelope = json.loads(content.decode("utf-8"))
    if envelope.get("format") != EXPORT_FORMAT or not isinstance(envelope.get("package"), dict):
        raise RuntimeError("CLAIM_PACKAGE_EXPORT_FORMAT_INVALID")
    return {
        "format": EXPORT_FORMAT,
        "sha256": actual_hash,
        "byte_length": len(content),
        "package": envelope["package"],
    }
