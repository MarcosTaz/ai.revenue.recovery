from __future__ import annotations

from dataclasses import dataclass
import re


UNSUPPORTED_ASSERTION_PATTERNS = (
    r"\byou (?:have|were|are) (?:been )?overcharg(?:ed|ing)\b",
    r"\byou are owed\b",
    r"\byour lender (?:made|has made) (?:an )?error\b",
    r"\bwe (?:found|identified|confirmed) (?:a |the )?(?:leakage|overcharge|recoverable amount|refund)\b",
    r"\bthere is (?:a |an )?(?:overcharge|lender error|recoverable amount)\b",
    r"\bwe can recover\b",
    r"\bguaranteed recovery\b",
)

DOCUMENT_SOLICITATION_PATTERNS = (
    r"\bupload (?:your |the )?(?:facility|loan|debt|lender|bank|confidential|documents?)\b",
    r"\bsend (?:us |me )?(?:your |the )?(?:facility agreement|loan agreement|lender statement|bank statement|confidential documents?)\b",
    r"\bshare (?:your |the )?(?:facility agreement|loan agreement|lender statement|bank statement|confidential documents?)\b",
)


@dataclass(frozen=True)
class CommercialGateResult:
    checks: dict[str, bool]
    blockers: tuple[str, ...]
    outbound_allowed: bool
    confidential_document_cta_allowed: bool

    def as_dict(self) -> dict:
        return {
            "checks": dict(self.checks),
            "blockers": list(self.blockers),
            "outbound_allowed": self.outbound_allowed,
            "confidential_document_cta_allowed": self.confidential_document_cta_allowed,
        }


def _contains_any(patterns: tuple[str, ...], message: str) -> bool:
    return any(re.search(pattern, message, flags=re.IGNORECASE) for pattern in patterns)


def evaluate_commercial_gate(
    *,
    message: str,
    sender_brand: str,
    sender_professional: bool,
    outbound_authorized: bool,
    recipient_business_route_verified: bool,
    jurisdiction_reviewed: bool,
    public_fit_signal_cited: bool,
    zero_variance_outcome_disclosed: bool,
    claim_evidence_verified: bool = False,
    real_data_deployment_ready: bool = False,
) -> CommercialGateResult:
    """Fail-closed outbound admission for pre-validation DebtRecover GTM.

    The function does not decide whether cold outreach is lawful. `jurisdiction_reviewed`
    represents a separate human/compliance determination for the intended route.
    """
    text = (message or "").strip()
    unsupported_assertion = _contains_any(UNSUPPORTED_ASSERTION_PATTERNS, text)
    solicits_confidential_documents = _contains_any(DOCUMENT_SOLICITATION_PATTERNS, text)

    checks = {
        "message_present": bool(text),
        "dedicated_debtrecover_sender": sender_brand.strip().lower() == "debtrecover" and bool(sender_professional),
        "explicit_outbound_authorization": bool(outbound_authorized),
        "business_recipient_route_verified": bool(recipient_business_route_verified),
        "jurisdiction_reviewed": bool(jurisdiction_reviewed),
        "public_fit_signal_cited": bool(public_fit_signal_cited),
        "zero_variance_outcome_disclosed": bool(zero_variance_outcome_disclosed),
        "no_unsupported_recovery_assertion": (not unsupported_assertion) or bool(claim_evidence_verified),
        "document_cta_safe": (not solicits_confidential_documents) or bool(real_data_deployment_ready),
    }

    blockers = tuple(k for k, v in checks.items() if not v)
    return CommercialGateResult(
        checks=checks,
        blockers=blockers,
        outbound_allowed=not blockers,
        confidential_document_cta_allowed=bool(real_data_deployment_ready),
    )


def require_outbound_ready(**kwargs) -> CommercialGateResult:
    result = evaluate_commercial_gate(**kwargs)
    if not result.outbound_allowed:
        raise RuntimeError("commercial outbound gate failed: " + ",".join(result.blockers))
    return result
