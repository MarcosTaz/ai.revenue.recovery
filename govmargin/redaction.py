from __future__ import annotations

from typing import Any, Mapping, Sequence


REDACTED = "[REDACTED]"

SENSITIVE_KEY_FRAGMENTS = (
    "bank",
    "account_number",
    "routing",
    "tax_id",
    "tin",
    "ssn",
    "employee_name",
    "employee_email",
    "employee_phone",
    "raw_gl",
    "gl_line",
    "attachment",
    "document_content",
    "contract_text",
    "invoice_line_detail",
    "credential",
    "password",
    "secret",
    "token",
)


def _sensitive_key(key: str) -> bool:
    normalized = key.strip().lower()
    return any(fragment in normalized for fragment in SENSITIVE_KEY_FRAGMENTS)


def redact_for_log(value: Any) -> Any:
    """Return a log-safe structural copy without raw sensitive payload values."""
    if isinstance(value, Mapping):
        return {
            str(key): REDACTED if _sensitive_key(str(key)) else redact_for_log(item)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return tuple(redact_for_log(item) for item in value)
    if isinstance(value, list):
        return [redact_for_log(item) for item in value]
    if isinstance(value, set):
        return sorted(redact_for_log(item) for item in value)
    return value
