import json

from recovery_radar.cli import TOKEN_ENV, main


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
