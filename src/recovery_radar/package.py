from __future__ import annotations


def build_claim_package(analysis: dict) -> dict:
    lines = analysis["claim_lines"]
    missing = sorted({item for line in lines for item in line.get("missing_evidence", [])})
    return {
        "executive_summary":{"event_id":analysis["event"]["event_id"],"event_type":analysis["event"]["event_type"],"net_exposure_total":analysis["net_exposure_total"],"claimable_total":analysis["claimable_total"],"requires_review_amount":analysis["requires_review_amount"],"paid_total":analysis["paid_total"]},
        "event":analysis["event"],
        "claim_lines":lines,
        "missing_evidence":missing,
        "assumptions":[],
        "open_questions":[],
        "review_status":"REQUIRES_HUMAN_REVIEW" if analysis["requires_review_amount"] != "0.00" or missing else "ECONOMIC_PACKAGE_READY_FOR_REVIEW",
        "legal_boundary":analysis["product_boundary"],
    }
