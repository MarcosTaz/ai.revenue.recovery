import hashlib
import json
from datetime import date
from decimal import Decimal

from recovery_radar.cli import TOKEN_ENV, main
from recovery_radar.gateway import RecoveryRadarGateway
from recovery_radar.models import RecoveryEvent
from recovery_radar.scope_manifest import build_source_scope_manifest_from_records
from recovery_radar.storage import Storage
from recovery_radar.t2_io import FORMAT


def _last_json(capsys):
    output = capsys.readouterr().out.strip().splitlines()
    assert output
    return json.loads(output[-1])


def _setup(tmp_path, capsys, monkeypatch):
    database = tmp_path / "binding.db"
    assert main([
        "bootstrap", "--db", str(database), "--workspace", "A",
        "--name", "Supplier A", "--actor", "owner",
    ]) == 0
    bootstrap = _last_json(capsys)
    token = bootstrap["api_token"]
    monkeypatch.setenv(TOKEN_ENV, token)
    event = RecoveryEvent(
        "EV-BIND", "OEM-A", "PRG-A", "PART-A", "PROGRAM_CANCELLED",
        date(2026, 7, 1), Decimal("100"), Decimal("0"), "event://bind", "",
    )
    storage = Storage(database)
    try:
        gateway = RecoveryRadarGateway(storage)
        gateway.store_recovery_event(token, event)
    finally:
        storage.close()
    scope = build_source_scope_manifest_from_records(
        supplier_id="SUP-A", event=event, exposures=(), entitlements=(), evidence_documents=()
    )
    return database, scope


def _ground_truth(tmp_path, scope_hash):
    path = tmp_path / "ground-truth.json"
    path.write_text(json.dumps({
        "format": FORMAT,
        "case_origin": "SYNTHETIC",
        "ground_truth_complete": True,
        "provenance": {
            "authorization_reference": None,
            "source_scope_sha256": scope_hash,
            "ground_truth_method": "UNKNOWN",
        },
        "lines": [],
        "operational_metrics": {},
    }), encoding="utf-8")
    return path


def test_score_historical_refuses_recorded_scope_that_does_not_match_persisted_truth(tmp_path, capsys, monkeypatch):
    database, _ = _setup(tmp_path, capsys, monkeypatch)
    ground_truth = _ground_truth(tmp_path, "f" * 64)
    output = tmp_path / "scorecard.json"
    status = main([
        "score-historical", "--db", str(database), "--event-id", "EV-BIND",
        "--supplier-id", "SUP-A", "--ground-truth", str(ground_truth),
        "--output", str(output),
    ])
    assert status == 2
    assert _last_json(capsys) == {"ok": False, "error": "SOURCE_SCOPE_SHA256_MISMATCH"}
    assert not output.exists()


def test_score_historical_records_verified_match_to_persisted_scope(tmp_path, capsys, monkeypatch):
    database, scope = _setup(tmp_path, capsys, monkeypatch)
    ground_truth = _ground_truth(tmp_path, scope["source_scope_sha256"])
    output = tmp_path / "scorecard.json"
    status = main([
        "score-historical", "--db", str(database), "--event-id", "EV-BIND",
        "--supplier-id", "SUP-A", "--ground-truth", str(ground_truth),
        "--output", str(output),
    ])
    assert status == 0
    result = _last_json(capsys)
    assert result["ok"] is True
    scorecard = json.loads(output.read_text(encoding="utf-8"))["scorecard"]
    assert scorecard["provenance"]["persisted_source_scope_sha256"] == scope["source_scope_sha256"]
    assert scorecard["provenance"]["persisted_source_scope_status"] == "MATCHED_RECORDED_SCOPE"
    assert scorecard["case_origin_status"] == "RECORDED_NOT_INDEPENDENTLY_VERIFIED"
    assert scorecard["terminal_promotion"] == "NOT_INFERRED_FROM_SCORECARD"
    claimed = scorecard["scorecard_sha256"]
    unsigned = dict(scorecard)
    del unsigned["scorecard_sha256"]
    canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert claimed == hashlib.sha256(canonical).hexdigest()