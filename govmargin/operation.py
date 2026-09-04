from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Iterable, Mapping, Optional, Sequence, Tuple

from .domain import EconomicFinding, EvidenceRef
from .engine import (
    FindingState,
    IndirectTrueUpInput,
    RateState,
    SupportState,
    compute_indirect_true_up,
)
from .pack import RecoveryPack, build_recovery_pack
from .review import HumanReview
from .rules import RULES


class AuditBundleError(ValueError):
    pass


def _decimal(payload: Mapping[str, object], key: str, optional: bool = False) -> Optional[Decimal]:
    raw = payload.get(key)
    if raw is None and optional:
        return None
    if raw is None:
        raise AuditBundleError(f"missing {key}")
    try:
        return Decimal(str(raw))
    except (InvalidOperation, ValueError) as exc:
        raise AuditBundleError(f"invalid decimal for {key}") from exc


def _enum(enum_type, raw: object, key: str):
    try:
        return enum_type(str(raw))
    except ValueError as exc:
        raise AuditBundleError(f"invalid {key}: {raw}") from exc


def _build_evidence(items: Sequence[Mapping[str, object]]) -> Tuple[EvidenceRef, ...]:
    result = []
    seen = set()
    for item in items:
        evidence_id = str(item.get("evidence_id", "")).strip()
        if not evidence_id or evidence_id in seen:
            raise AuditBundleError("evidence ids must be non-empty and unique")
        seen.add(evidence_id)
        observed_raw = str(item.get("observed_at", ""))
        try:
            observed = datetime.fromisoformat(observed_raw.replace("Z", "+00:00"))
        except ValueError as exc:
            raise AuditBundleError(f"invalid observed_at for {evidence_id}") from exc
        if observed.tzinfo is None:
            raise AuditBundleError(f"observed_at must be timezone-aware for {evidence_id}")
        result.append(
            EvidenceRef(
                evidence_id=evidence_id,
                source_type=str(item.get("source_type", "unknown")),
                source_locator=str(item.get("source_locator", "")),
                sha256=str(item.get("sha256", "")),
                observed_at=observed,
            )
        )
    return tuple(result)


@dataclass(frozen=True)
class AuditOperationResult:
    finding: EconomicFinding
    pack: RecoveryPack
    evidence: Tuple[EvidenceRef, ...]


def run_normalized_indirect_audit(
    bundle: Mapping[str, object],
    reviews: Iterable[HumanReview] = (),
) -> AuditOperationResult:
    organization_id = str(bundle.get("organization_id", "")).strip()
    contract_id = str(bundle.get("contract_id", "")).strip()
    period = str(bundle.get("period", "")).strip()
    finding_id = str(bundle.get("finding_id", "")).strip()
    if not all((organization_id, contract_id, period, finding_id)):
        raise AuditBundleError("organization_id, contract_id, period and finding_id are required")

    evidence_raw = bundle.get("evidence")
    if not isinstance(evidence_raw, list) or not evidence_raw:
        raise AuditBundleError("non-empty evidence list is required")
    evidence = _build_evidence(evidence_raw)
    evidence_ids = tuple(item.evidence_id for item in evidence)

    rule_ids_raw = bundle.get("rule_ids")
    if not isinstance(rule_ids_raw, list) or not rule_ids_raw:
        raise AuditBundleError("non-empty rule_ids list is required")
    rule_ids = tuple(str(item) for item in rule_ids_raw)
    unknown_rules = [rule_id for rule_id in rule_ids if rule_id not in RULES]
    if unknown_rules:
        raise AuditBundleError(f"unknown rule ids: {', '.join(unknown_rules)}")

    true_up = compute_indirect_true_up(
        IndirectTrueUpInput(
            contract_id=contract_id,
            period=period,
            allocation_base=_decimal(bundle, "allocation_base"),
            final_rate=_decimal(bundle, "final_rate"),
            billed_indirect=_decimal(bundle, "billed_indirect"),
            rate_state=_enum(RateState, bundle.get("rate_state"), "rate_state"),
            contract_terms=_enum(SupportState, bundle.get("contract_terms"), "contract_terms"),
            base_allowability=_enum(SupportState, bundle.get("base_allowability"), "base_allowability"),
            base_allocability=_enum(SupportState, bundle.get("base_allocability"), "base_allocability"),
            indirect_ceiling_amount=_decimal(bundle, "indirect_ceiling_amount", optional=True),
            remaining_funding=_decimal(bundle, "remaining_funding", optional=True),
        )
    )

    finding = EconomicFinding(
        finding_id=finding_id,
        contract_id=contract_id,
        state=true_up.state,
        expected_amount=true_up.expected_indirect,
        billed_amount=true_up.billed_indirect,
        paid_amount=None,
        variance=true_up.variance,
        evidence_ids=evidence_ids if true_up.state in {FindingState.RECOVERY_CANDIDATE, FindingState.PAYABLE_CANDIDATE} else (),
        rule_ids=rule_ids if true_up.state in {FindingState.RECOVERY_CANDIDATE, FindingState.PAYABLE_CANDIDATE} else (),
        assumptions=tuple(str(item) for item in bundle.get("assumptions", []) if str(item).strip()),
        human_reviewed=False,
    )

    pack = build_recovery_pack(organization_id, [finding], reviews)
    return AuditOperationResult(finding=finding, pack=pack, evidence=evidence)
