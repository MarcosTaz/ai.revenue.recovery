from govmargin.evidence_intake import (
    EvidenceIntakeInput,
    IntakeState,
    ScanStatus,
    evaluate_evidence_intake,
)


VALID_HASH = "a" * 64


def test_controlled_file_requires_scan_before_storage_or_parsing():
    decision = evaluate_evidence_intake(EvidenceIntakeInput(
        organization_id="org-a",
        filename="contract.pdf",
        content_type="application/pdf",
        size_bytes=1024,
        sha256=VALID_HASH,
        scan_status=ScanStatus.NOT_RUN,
    ))
    assert decision.state is IntakeState.REQUIRES_SCAN
    assert not decision.eligible_for_storage
    assert not decision.eligible_for_parsing


def test_passed_scan_and_allowlisted_metadata_can_enter_controlled_storage():
    decision = evaluate_evidence_intake(EvidenceIntakeInput(
        organization_id="org-a",
        filename="rates.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        size_bytes=2048,
        sha256=VALID_HASH,
        scan_status=ScanStatus.PASSED,
    ))
    assert decision.state is IntakeState.ACCEPTABLE_FOR_CONTROLLED_STORAGE
    assert decision.eligible_for_storage
    assert decision.eligible_for_parsing


def test_macro_enabled_or_unknown_content_type_is_rejected():
    decision = evaluate_evidence_intake(EvidenceIntakeInput(
        organization_id="org-a",
        filename="rates.xlsm",
        content_type="application/vnd.ms-excel.sheet.macroEnabled.12",
        size_bytes=2048,
        sha256=VALID_HASH,
        scan_status=ScanStatus.PASSED,
    ))
    assert decision.state is IntakeState.REJECTED
    assert not decision.eligible_for_storage


def test_invalid_hash_oversize_and_failed_scan_all_fail_closed():
    bad_hash = evaluate_evidence_intake(EvidenceIntakeInput(
        organization_id="org-a",
        filename="contract.pdf",
        content_type="application/pdf",
        size_bytes=100,
        sha256="bad",
        scan_status=ScanStatus.PASSED,
    ))
    assert bad_hash.state is IntakeState.REJECTED

    oversize = evaluate_evidence_intake(EvidenceIntakeInput(
        organization_id="org-a",
        filename="contract.pdf",
        content_type="application/pdf",
        size_bytes=26 * 1024 * 1024,
        sha256=VALID_HASH,
        scan_status=ScanStatus.PASSED,
    ))
    assert oversize.state is IntakeState.REJECTED

    failed_scan = evaluate_evidence_intake(EvidenceIntakeInput(
        organization_id="org-a",
        filename="contract.pdf",
        content_type="application/pdf",
        size_bytes=100,
        sha256=VALID_HASH,
        scan_status=ScanStatus.FAILED,
    ))
    assert failed_scan.state is IntakeState.REJECTED
