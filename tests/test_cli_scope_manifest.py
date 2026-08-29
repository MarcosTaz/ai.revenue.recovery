import json

from recovery_radar.cli import TOKEN_ENV, main
from recovery_radar.pilot_bundle import BUNDLE_FORMAT
from recovery_radar.scope_manifest import FORMAT


def _last_json(capsys):
    output = capsys.readouterr().out.strip().splitlines()
    assert output
    return json.loads(output[-1])


def test_cli_exports_source_scope_from_concrete_evidence_bytes(tmp_path, capsys, monkeypatch):
    database = tmp_path / "scope.db"
    assert main([
        "bootstrap", "--db", str(database), "--workspace", "A",
        "--name", "Supplier A", "--actor", "owner",
    ]) == 0
    bootstrap = _last_json(capsys)
    monkeypatch.setenv(TOKEN_ENV, bootstrap["api_token"])

    evidence = tmp_path / "contract.txt"
    evidence.write_text("historical contract bytes", encoding="utf-8")
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps({
        "format": BUNDLE_FORMAT,
        "supplier_id": "SUP-A",
        "event": {
            "event_id": "EV-1", "customer_id": "OEM-A", "program_id": "PRG-A",
            "part_id": "PART-A", "event_type": "PROGRAM_CANCELLED",
            "event_date": "2026-07-01", "expected_volume": "100",
            "revised_volume": "0", "source_ref": "event://1", "evidence_ref": "contract://1"
        },
        "exposures": [],
        "entitlements": [],
        "evidence": [{
            "document_id": "DOC-1", "supplier_id": "SUP-A", "customer_id": "OEM-A",
            "program_id": "PRG-A", "evidence_type": "CONTRACT", "source_ref": "contract://1",
            "version_id": "v1", "document_date": "2026-01-01", "file": "contract.txt", "signed": True
        }]
    }), encoding="utf-8")

    output = tmp_path / "source-scope.json"
    status = main([
        "scope-manifest", "--db", str(database), "--bundle", str(bundle_path),
        "--output", str(output),
    ])
    assert status == 0
    result = _last_json(capsys)
    assert result["ok"] is True
    assert result["manifest"]["format"] == FORMAT
    assert len(result["manifest"]["source_scope_sha256"]) == 64
    assert result["authorization_status"] == "NOT_INFERRED_FROM_SOURCE_SCOPE"
    persisted = json.loads(output.read_text(encoding="utf-8"))
    assert persisted["raw_evidence_bytes_embedded"] is False
    assert "historical contract bytes" not in output.read_text(encoding="utf-8")
