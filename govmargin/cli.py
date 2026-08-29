from __future__ import annotations

import argparse
import json
from pathlib import Path

from .operation import run_normalized_indirect_audit


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a normalized GovMargin indirect-rate audit bundle")
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    payload = json.loads(args.bundle.read_text(encoding="utf-8"))
    result = run_normalized_indirect_audit(payload)
    output = {
        "finding": {
            "finding_id": result.finding.finding_id,
            "contract_id": result.finding.contract_id,
            "state": result.finding.state.value,
            "expected_amount": None if result.finding.expected_amount is None else str(result.finding.expected_amount),
            "billed_amount": None if result.finding.billed_amount is None else str(result.finding.billed_amount),
            "variance": None if result.finding.variance is None else str(result.finding.variance),
            "evidence_ids": list(result.finding.evidence_ids),
            "rule_ids": list(result.finding.rule_ids),
        },
        "pack_status": result.pack.status.value,
    }
    text = json.dumps(output, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
