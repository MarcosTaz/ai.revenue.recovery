from datetime import datetime, timezone

from govmargin.audit import verify_chain
from govmargin.audit_trace import build_operation_audit_trace
from govmargin.operation import run_normalized_indirect_audit


def _bundle():
    return {
        "organization_id": "synthetic-org",
        "contract_id": "SYN-CPFF-001",
        "period": "FY2025",
        "finding_id": "SYN-F-001",
        "allocation_base": "1000000",
        "final_rate": "0.25",
        "billed_indirect": "200000",
        "rate_state": "SETTLED_FINAL",
        "contract_terms": "SUPPORTED",
        "base_allowability": "SUPPORTED",
        "base_allocability": "SUPPORTED",
        "indirect_ceiling_amount": None,
        "remaining_funding": "100000",
        "rule_ids": ["FAR_52_216_7_D2V_UPDATE_BILLINGS"],
        "evidence": [{
            "evidence_id": "rate-agreement",
            "source_type": "rate_agreement",
            "source_locator": "synthetic://rate-agreement",
            "sha256": "06275d9f93b99e28b013420a6ad3de9bdefd0381734c4386f57a2a30045e79ba",
            "observed_at": "2026-08-29T02:30:00+00:00",
        }],
        "assumptions": [],
    }


def test_operation_trace_covers_run_and_output_with_evidence_lineage():
    result = run_normalized_indirect_audit(_bundle())
    chain = build_operation_audit_trace(
        result=result,
        organization_id="synthetic-org",
        actor_user_id="analyst-1",
        occurred_at=datetime(2026, 8, 29, 20, 0, tzinfo=timezone.utc),
        audit_run_id="run-001",
    )
    assert len(chain) == 2
    assert chain[0].event.evidence_ids == ("rate-agreement",)
    assert chain[-1].event.subject_id == "synthetic-org"
    assert verify_chain(chain)


def test_operation_trace_requires_explicit_identity_and_timezone():
    result = run_normalized_indirect_audit(_bundle())
    try:
        build_operation_audit_trace(
            result=result,
            organization_id="",
            actor_user_id="analyst-1",
            occurred_at=datetime(2026, 8, 29, 20, 0, tzinfo=timezone.utc),
            audit_run_id="run-001",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("missing organization must fail closed")

    try:
        build_operation_audit_trace(
            result=result,
            organization_id="synthetic-org",
            actor_user_id="analyst-1",
            occurred_at=datetime(2026, 8, 29, 20, 0),
            audit_run_id="run-001",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("naive timestamp must fail closed")
