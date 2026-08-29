from __future__ import annotations

import csv
import hashlib
import io
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import List, Mapping, Tuple


class ImportValidationError(ValueError):
    pass


class CrossTenantError(ImportValidationError):
    pass


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_nonnegative_decimal(raw: str, field: str) -> Decimal:
    try:
        value = Decimal(raw)
    except (InvalidOperation, TypeError) as exc:
        raise ImportValidationError(f"{field} is not a decimal") from exc
    if not value.is_finite() or value < 0:
        raise ImportValidationError(f"{field} must be finite and non-negative")
    return value


@dataclass(frozen=True)
class ImportedTransaction:
    organization_id: str
    contract_id: str
    period: str
    transaction_id: str
    category: str
    amount: Decimal
    evidence_sha256: str


@dataclass(frozen=True)
class ImportedInvoice:
    organization_id: str
    contract_id: str
    invoice_id: str
    amount: Decimal
    paid_amount: Decimal
    evidence_sha256: str


def _validate_hash(value: str, field: str) -> str:
    if len(value) != 64:
        raise ImportValidationError(f"{field} must be a SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ImportValidationError(f"{field} must be hexadecimal") from exc
    return value.lower()


def _read_rows(csv_text: str, required: Tuple[str, ...]) -> List[Mapping[str, str]]:
    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames is None:
        raise ImportValidationError("CSV is missing a header")
    missing = [field for field in required if field not in reader.fieldnames]
    if missing:
        raise ImportValidationError(f"CSV missing required columns: {', '.join(missing)}")
    return list(reader)


def import_transactions(csv_text: str, organization_id: str) -> List[ImportedTransaction]:
    required = ("organization_id", "contract_id", "period", "transaction_id", "category", "amount", "evidence_sha256")
    rows = _read_rows(csv_text, required)
    result: List[ImportedTransaction] = []
    seen: set[Tuple[str, str]] = set()
    for index, row in enumerate(rows, start=2):
        if row["organization_id"] != organization_id:
            raise CrossTenantError(f"row {index} belongs to another organization")
        key = (row["contract_id"], row["transaction_id"])
        if key in seen:
            raise ImportValidationError(f"duplicate transaction at row {index}: {key}")
        seen.add(key)
        result.append(
            ImportedTransaction(
                organization_id=organization_id,
                contract_id=row["contract_id"],
                period=row["period"],
                transaction_id=row["transaction_id"],
                category=row["category"],
                amount=parse_nonnegative_decimal(row["amount"], f"row {index} amount"),
                evidence_sha256=_validate_hash(row["evidence_sha256"], f"row {index} evidence_sha256"),
            )
        )
    return result


def import_invoices(csv_text: str, organization_id: str) -> List[ImportedInvoice]:
    required = ("organization_id", "contract_id", "invoice_id", "amount", "paid_amount", "evidence_sha256")
    rows = _read_rows(csv_text, required)
    result: List[ImportedInvoice] = []
    seen: set[Tuple[str, str]] = set()
    for index, row in enumerate(rows, start=2):
        if row["organization_id"] != organization_id:
            raise CrossTenantError(f"row {index} belongs to another organization")
        key = (row["contract_id"], row["invoice_id"])
        if key in seen:
            raise ImportValidationError(f"duplicate invoice at row {index}: {key}")
        seen.add(key)
        result.append(
            ImportedInvoice(
                organization_id=organization_id,
                contract_id=row["contract_id"],
                invoice_id=row["invoice_id"],
                amount=parse_nonnegative_decimal(row["amount"], f"row {index} amount"),
                paid_amount=parse_nonnegative_decimal(row["paid_amount"], f"row {index} paid_amount"),
                evidence_sha256=_validate_hash(row["evidence_sha256"], f"row {index} evidence_sha256"),
            )
        )
    return result
