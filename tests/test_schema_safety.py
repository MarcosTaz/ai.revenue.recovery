import sqlite3

import pytest

from recovery_radar.gateway import RecoveryRadarGateway
from recovery_radar.schema import APPLICATION_SCHEMA_VERSION, SchemaCompatibilityError
from recovery_radar.storage import Storage


def test_fresh_gateway_records_compatible_schema_version(tmp_path):
    store = Storage(tmp_path / "fresh.db")
    try:
        gateway = RecoveryRadarGateway(store)
        assert gateway.schema == {
            "schema_version": APPLICATION_SCHEMA_VERSION,
            "required_table_count": 10,
            "state": "COMPATIBLE",
        }
        row = store.conn.execute(
            "SELECT schema_version FROM application_schema_metadata WHERE singleton=1"
        ).fetchone()
        assert row["schema_version"] == APPLICATION_SCHEMA_VERSION
    finally:
        store.close()


def test_newer_unknown_database_schema_refuses_gateway_startup(tmp_path):
    path = tmp_path / "future.db"
    store = Storage(path)
    RecoveryRadarGateway(store)
    store.conn.execute(
        "UPDATE application_schema_metadata SET schema_version=999 WHERE singleton=1"
    )
    store.conn.commit()
    store.close()

    reopened = Storage(path)
    try:
        with pytest.raises(
            SchemaCompatibilityError,
            match="DATABASE_SCHEMA_NEWER_THAN_APPLICATION:999>1",
        ):
            RecoveryRadarGateway(reopened)
        row = reopened.conn.execute(
            "SELECT schema_version FROM application_schema_metadata WHERE singleton=1"
        ).fetchone()
        assert row["schema_version"] == 999
    finally:
        reopened.close()


def test_explicit_older_version_requires_migration_instead_of_silent_upgrade(tmp_path):
    path = tmp_path / "older.db"
    store = Storage(path)
    RecoveryRadarGateway(store)
    store.conn.execute(
        "UPDATE application_schema_metadata SET schema_version=0 WHERE singleton=1"
    )
    store.conn.commit()
    store.close()

    reopened = Storage(path)
    try:
        with pytest.raises(
            SchemaCompatibilityError,
            match="EXPLICIT_MIGRATION_REQUIRED:0->1",
        ):
            RecoveryRadarGateway(reopened)
    finally:
        reopened.close()


def test_incompatible_existing_core_table_shape_refuses_gateway_startup(tmp_path):
    path = tmp_path / "incompatible.db"
    raw = sqlite3.connect(path)
    raw.execute("CREATE TABLE workspaces(workspace_id TEXT PRIMARY KEY)")
    raw.commit()
    raw.close()

    store = Storage(path)
    try:
        with pytest.raises(
            SchemaCompatibilityError,
            match="MISSING_COLUMNS:workspaces:name",
        ):
            RecoveryRadarGateway(store)
        assert store.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='application_schema_metadata'"
        ).fetchone() is None
    finally:
        store.close()
