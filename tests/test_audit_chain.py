from dataclasses import replace
from datetime import datetime, timezone

from govmargin.audit import append_event, verify_chain
from govmargin.domain import AuditEvent


def _event(event_id: str, action: str = "CALCULATE") -> AuditEvent:
    return AuditEvent(
        event_id=event_id,
        occurred_at=datetime(2026, 8, 29, 19, 30, tzinfo=timezone.utc),
        actor="analyst-1",
        action=action,
        subject_id="finding-1",
        evidence_ids=("evidence-1",),
    )


def test_append_only_chain_verifies_and_links_events():
    chain = append_event((), _event("evt-1"))
    chain = append_event(chain, _event("evt-2", "REVIEW"))
    assert len(chain) == 2
    assert chain[1].previous_hash == chain[0].event_hash
    assert verify_chain(chain)


def test_event_tampering_breaks_verification():
    chain = append_event((), _event("evt-1"))
    tampered = replace(chain[0], event=replace(chain[0].event, action="APPROVE"))
    assert not verify_chain((tampered,))


def test_chain_reordering_or_link_tampering_breaks_verification():
    chain = append_event((), _event("evt-1"))
    chain = append_event(chain, _event("evt-2", "REVIEW"))
    assert not verify_chain(tuple(reversed(chain)))
    broken = replace(chain[1], previous_hash="f" * 64)
    assert not verify_chain((chain[0], broken))


def test_duplicate_event_id_is_rejected():
    chain = append_event((), _event("evt-1"))
    try:
        append_event(chain, _event("evt-1", "REVIEW"))
    except ValueError as exc:
        assert "duplicate" in str(exc).lower()
    else:
        raise AssertionError("duplicate audit event id must fail closed")
