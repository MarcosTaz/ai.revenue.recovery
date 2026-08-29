import json
from datetime import date
from decimal import Decimal

from recovery_radar.cli import TOKEN_ENV, main
from recovery_radar.gateway import RecoveryRadarGateway
from recovery_radar.models import RecoveryEvent
from recovery_radar.storage import Storage
from recovery_radar.t2_io import FORMAT, SCORECARD_FORMAT


def _last_json(capsys):
    output = capsys.readouterr().out.strip().splitlines()
    assert output
    return json.loads(output[-1])


def test_cli_bootstrap_and_admin_issued_keys_are_tenant_scoped(tmp_path, capsys, monkeypatch):
    database = tmp_path / "cli.db"
    status = main(
        [
            "bootstrap",
            "--db",
            str(database),
            "--workspace",
            "A",
            "--name",
            "Supplier A",
            "--actor",
            "owner",
        ]
    )
    assert status == 0
    bootstrap = _last_json(capsys)
    assert bootstrap["ok"] is True
    assert bootstrap["workspace_id"] == "A"
    assert bootstrap["role"] == "ADMIN"
    assert bootstrap["api_token"].startswith("rrk_")
    assert bootstrap["token_notice"] == "SECRET_RETURNED_ONCE_STORE_SECURELY"
    assert bootstrap["schema"]["state"] == "COMPATIBLE"

    monkeypatch.setenv(TOKEN_ENV, bootstrap["api_token"])
    status = main(
        [
            "issue-key",
            "--db",
            str(database),
            "--actor",
            "analyst",
            "--role",
            "ANALYST",
        ]
    )
    assert status == 0
    issued = _last_json(capsys)
    assert issued["ok"] is True
    assert issued["workspace_id"] == "A"
    assert issued["actor_id"] == "analyst"
    assert issued["role"] == "ANALYST"
    assert issued["api_token"].startswith("rrk_")


def test_cli_refuses_authenticated_commands_without_token_env(tmp_path, capsys, monkeypatch):
    database = tmp_path / "cli.db"
    assert main(
        [
            "bootstrap",
            "--db",
            str(database),
            "--workspace",
            "A",
            "--name",
            "Supplier A",
            "--actor",
            "owner",
        ]
    ) == 0
    _last_json(capsys)
    monkeypatch.delenv(TOKEN_ENV, raising=False)

    status = main(
        [
            "package",
            "--db",
            str(database),
            "--event-id",
            "EV-X",
            "--supplier-id",
            "SUP-A",
        ]
    )
    assert status == 2
    result = _last_json(capsys)
    assert result == {"ok": False, "error": f"{TOKEN_ENV}_REQUIRED"}


def test_cli_scores_historical_ground_truth_to_verified_file(tmp_path, capsys, monkeypatch):
    database = tmp_path / "score.db"
    assert main(
        [
            "bootstrap",
            "--db",
            str(database),
            "--workspace",
            "A",
            "--name",
            "Supplier A",
            "--actor",
            "owner",
        ]
    ) == 0
    bootstrap = _last_json(capsys)
    token = bootstrap["api_token"]

    storage = Storage(database)
    try:
        gateway = RecoveryRadarGateway(storage)
        gateway.store_recovery_event(
            token,
            RecoveryEvent(
                "EV-T2",
                "OEM-A",
                "PRG-A",
                "PART-A",
                "PROGRAM_CANCELLED",
                date(2026, 7, 1),
                Decimal("100"),
                Decimal("0"),
                "event://t2",
                "",
            ),
        )
    finally:
        storage.close()

    ground_truth = tmp_path / "ground-truth.json"
    ground_truth.write_text(
        json.dumps(
            {
                "format": FORMAT,
                "case_origin": "SYNTHETIC",
                "ground_truth_complete": True,
                "lines": [],
                "operational_metrics": {},
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "scorecard.json"
    monkeypatch.setenv(TOKEN_ENV, token)
    status = main(
        [
            "score-historical",
            "--db",
            str(database),
            "--event-id",
            "EV-T2",
            "--supplier-id",
            "SUP-A",
            "--ground-truth",
            str(ground_truth),
            "--output",
            str(output),
        ]
    )
    assert status == 0
    result = _last_json(capsys)
    assert result["ok"] is True
    assert result["validation_classification"] == "NON_REAL_CASE_MEASUREMENT_ONLY"
    assert result["terminal_promotion"] == "NOT_INFERRED_FROM_SCORECARD"
    assert result["manifest"]["format"] == SCORECARD_FORMAT
    envelope = json.loads(output.read_text(encoding="utf-8"))
    assert envelope["format"] == SCORECARD_FORMAT
    assert envelope["scorecard"]["commercial_truth"]["wtp"] == "UNKNOWN_EXTERNAL"
