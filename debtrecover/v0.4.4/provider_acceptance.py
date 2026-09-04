from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import re


REQUIRED_PROVIDER_PROBES = (
    "OIDC_TOKEN_JWKS_VERIFY",
    "DATA_API_RLS_POLICY_SIMULATION",
    "DATABASE_WRITE_READ",
    "OBJECT_STORAGE_PUT_GET_DELETE",
    "KMS_ENCRYPT_DECRYPT",
    "SECRET_MANAGER_RESOLVE",
    "MALWARE_SCANNER_CLEAN_BLOCK",
    "MONITORING_ALERT_DELIVERY",
    "BACKUP_RESTORE",
    "AUDIT_ANCHOR_WRITE_VERIFY",
)

_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ProviderProbe:
    probe_type: str
    provider: str
    result: str
    synthetic: bool
    payload_hash: str
    observed_at: datetime
    evidence_id: str

    @classmethod
    def from_dict(cls, value: dict) -> "ProviderProbe":
        observed = value.get("observed_at")
        if isinstance(observed, str):
            observed = datetime.fromisoformat(observed.replace("Z", "+00:00"))
        if not isinstance(observed, datetime):
            raise ValueError("observed_at required")
        if observed.tzinfo is None:
            observed = observed.replace(tzinfo=timezone.utc)
        return cls(
            probe_type=str(value.get("probe_type", "")).strip().upper(),
            provider=str(value.get("provider", "")).strip(),
            result=str(value.get("result", "")).strip().upper(),
            synthetic=bool(value.get("synthetic", False)),
            payload_hash=str(value.get("payload_hash", "")).strip().lower(),
            observed_at=observed.astimezone(timezone.utc),
            evidence_id=str(value.get("evidence_id", "")).strip(),
        )

    def valid(self, *, now: datetime, max_age: timedelta) -> bool:
        now = now.astimezone(timezone.utc)
        return all((
            self.probe_type in REQUIRED_PROVIDER_PROBES,
            bool(self.provider),
            self.result == "PASS",
            self.synthetic is True,
            bool(_HASH_RE.fullmatch(self.payload_hash)),
            bool(self.evidence_id),
            self.observed_at <= now + timedelta(minutes=5),
            now - self.observed_at <= max_age,
        ))


@dataclass(frozen=True)
class ProviderAcceptance:
    accepted_probe_types: tuple[str, ...]
    missing_probe_types: tuple[str, ...]
    invalid_probe_types: tuple[str, ...]
    external_provider_acceptance: bool

    def as_dict(self) -> dict:
        return {
            "accepted_probe_types": list(self.accepted_probe_types),
            "missing_probe_types": list(self.missing_probe_types),
            "invalid_probe_types": list(self.invalid_probe_types),
            "external_provider_acceptance": self.external_provider_acceptance,
        }


def evaluate_provider_acceptance(
    probes: list[ProviderProbe | dict],
    *,
    now: datetime | None = None,
    max_age_hours: int = 24,
) -> ProviderAcceptance:
    now = now or datetime.now(timezone.utc)
    max_age = timedelta(hours=max_age_hours)
    parsed = [p if isinstance(p, ProviderProbe) else ProviderProbe.from_dict(p) for p in probes]

    by_type: dict[str, list[ProviderProbe]] = {}
    for p in parsed:
        by_type.setdefault(p.probe_type, []).append(p)

    accepted = []
    invalid = []
    missing = []
    for required in REQUIRED_PROVIDER_PROBES:
        candidates = by_type.get(required, [])
        if not candidates:
            missing.append(required)
            continue

        latest_time = max(p.observed_at for p in candidates)
        latest = [p for p in candidates if p.observed_at == latest_time]
        latest_fingerprints = {
            (p.provider, p.result, p.synthetic, p.payload_hash, p.evidence_id) for p in latest
        }
        if len(latest_fingerprints) != 1:
            invalid.append(required)
            continue

        freshest = latest[0]
        if freshest.valid(now=now, max_age=max_age):
            accepted.append(required)
        else:
            invalid.append(required)

    return ProviderAcceptance(
        accepted_probe_types=tuple(accepted),
        missing_probe_types=tuple(missing),
        invalid_probe_types=tuple(invalid),
        external_provider_acceptance=not missing and not invalid,
    )


def require_provider_acceptance(probes: list[ProviderProbe | dict], **kwargs) -> ProviderAcceptance:
    result = evaluate_provider_acceptance(probes, **kwargs)
    if not result.external_provider_acceptance:
        blockers = list(result.missing_probe_types) + list(result.invalid_probe_types)
        raise RuntimeError("external provider acceptance failed: " + ",".join(blockers))
    return result
