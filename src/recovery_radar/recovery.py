from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any


class BackupVerificationError(RuntimeError):
    pass


def _json_value(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"bytes_hex": value.hex()}
    return value


def database_truth_digest(conn: sqlite3.Connection) -> str:
    """Digest all application tables, including auth/review/audit state."""
    previous_factory = conn.row_factory
    conn.row_factory = sqlite3.Row
    try:
        table_rows = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        snapshot: dict[str, list[dict[str, Any]]] = {}
        for table_row in table_rows:
            table = table_row["name"]
            safe_table = table.replace('"', '""')
            rows = conn.execute(f'SELECT * FROM "{safe_table}"').fetchall()
            encoded = [
                {key: _json_value(row[key]) for key in row.keys()}
                for row in rows
            ]
            snapshot[table] = sorted(
                encoded,
                key=lambda item: json.dumps(
                    item, sort_keys=True, separators=(",", ":")
                ),
            )
        raw = json.dumps(
            snapshot, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()
    finally:
        conn.row_factory = previous_factory


def verify_database_connection(conn: sqlite3.Connection) -> dict[str, str | int]:
    quick_check = conn.execute("PRAGMA quick_check").fetchone()[0]
    if quick_check != "ok":
        raise BackupVerificationError(f"SQLITE_QUICK_CHECK_FAILED:{quick_check}")
    foreign_key_rows = conn.execute("PRAGMA foreign_key_check").fetchall()
    if foreign_key_rows:
        raise BackupVerificationError(
            f"SQLITE_FOREIGN_KEY_CHECK_FAILED:{len(foreign_key_rows)}"
        )
    return {
        "quick_check": "ok",
        "foreign_key_violations": 0,
        "truth_digest": database_truth_digest(conn),
    }


def verify_database_path(path: str | Path) -> dict[str, str | int]:
    try:
        conn = sqlite3.connect(str(path))
        try:
            return verify_database_connection(conn)
        finally:
            conn.close()
    except (sqlite3.DatabaseError, sqlite3.OperationalError) as exc:
        raise BackupVerificationError("SQLITE_BACKUP_UNREADABLE") from exc


def backup_verified(storage, destination: str | Path) -> dict[str, str | int]:
    """Create a backup and prove it is structurally and semantically identical."""
    destination = Path(destination)
    source_report = verify_database_connection(storage.conn)
    storage.backup_to(destination)
    try:
        target_report = verify_database_path(destination)
        if target_report["truth_digest"] != source_report["truth_digest"]:
            raise BackupVerificationError("BACKUP_TRUTH_DIGEST_MISMATCH")
        return target_report
    except Exception:
        destination.unlink(missing_ok=True)
        raise
