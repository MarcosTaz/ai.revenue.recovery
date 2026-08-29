from govmargin.redaction import REDACTED, redact_for_log


def test_sensitive_financial_and_personal_fields_are_redacted_recursively():
    payload = {
        "organization_id": "org-a",
        "contract_id": "c-1",
        "bank_account_number": "123456789",
        "nested": {
            "tax_id": "12-3456789",
            "employee_name": "Jane Doe",
            "safe_state": "REQUIRES_REVIEW",
        },
        "documents": [
            {"attachment_bytes": "raw", "sha256": "a" * 64},
        ],
    }
    safe = redact_for_log(payload)
    assert safe["organization_id"] == "org-a"
    assert safe["contract_id"] == "c-1"
    assert safe["bank_account_number"] == REDACTED
    assert safe["nested"]["tax_id"] == REDACTED
    assert safe["nested"]["employee_name"] == REDACTED
    assert safe["nested"]["safe_state"] == "REQUIRES_REVIEW"
    assert safe["documents"][0]["attachment_bytes"] == REDACTED
    assert safe["documents"][0]["sha256"] == "a" * 64


def test_credentials_and_tokens_never_survive_log_copy():
    safe = redact_for_log({
        "api_token": "secret-token",
        "db_password": "hunter2",
        "credential_blob": {"value": "x"},
    })
    assert safe == {
        "api_token": REDACTED,
        "db_password": REDACTED,
        "credential_blob": REDACTED,
    }
