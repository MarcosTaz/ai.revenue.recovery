import json
from pathlib import Path

from recovery_radar.engine import analyze_claim
from recovery_radar.pilot_bundle import load_pilot_bundle
from recovery_radar.t2_io import load_ground_truth, score_from_input


ROOT = Path(__file__).parents[1]


def test_pilot_bundle_template_matches_current_parser(tmp_path):
    template = json.loads((ROOT / "examples" / "pilot-bundle-template.json").read_text(encoding="utf-8"))
    for document in template["evidence"]:
        path = tmp_path / document["file"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"fixture:{document['document_id']}".encode("utf-8"))
    bundle_path = tmp_path / "pilot-bundle.json"
    bundle_path.write_text(json.dumps(template), encoding="utf-8")

    bundle = load_pilot_bundle(bundle_path, workspace_id="TEMPLATE")
    assert bundle.format == "RECOVERY_RADAR_PILOT_BUNDLE_V1"
    assert bundle.supplier_id == "SUPPLIER-ALIAS"
    assert bundle.event.event_id == "EVENT-001"
    assert len(bundle.exposures) == 1
    assert len(bundle.entitlements) == 1
    assert len(bundle.evidence_documents) == 4
    assert all(len(document.content_sha256) == 64 for document in bundle.evidence_documents)


def test_ground_truth_template_matches_current_parser_and_starts_unknown(tmp_path):
    source = ROOT / "examples" / "ground-truth-template.json"
    copy = tmp_path / "ground-truth.json"
    copy.write_bytes(source.read_bytes())
    ground_truth = load_ground_truth(copy)

    bundle_template = json.loads((ROOT / "examples" / "pilot-bundle-template.json").read_text(encoding="utf-8"))
    evidence_root = tmp_path / "analysis"
    for document in bundle_template["evidence"]:
        path = evidence_root / document["file"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"fixture:{document['document_id']}".encode("utf-8"))
    bundle_path = evidence_root / "pilot-bundle.json"
    bundle_path.write_text(json.dumps(bundle_template), encoding="utf-8")
    bundle = load_pilot_bundle(bundle_path, workspace_id="TEMPLATE")

    analysis = analyze_claim(bundle.event, bundle.exposures, bundle.entitlements)
    scorecard = score_from_input(analysis, ground_truth)
    assert ground_truth["complete"] is False
    assert ground_truth["case_origin"] == "UNKNOWN"
    assert scorecard["validation_classification"] == "NON_REAL_CASE_MEASUREMENT_ONLY"
    assert scorecard["terminal_promotion"] == "NOT_INFERRED_FROM_SCORECARD"
    assert scorecard["commercial_truth"]["wtp"] == "UNKNOWN_EXTERNAL"
