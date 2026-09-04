from __future__ import annotations

import argparse
import json
from pathlib import Path

from aviation_io import evaluate_payload
from executive_report import render_executive_markdown


def main() -> int:
    parser = argparse.ArgumentParser(description="Aviation Recovery deterministic evaluator")
    parser.add_argument("input", type=Path, help="JSON file containing rules and claims")
    parser.add_argument("--output", type=Path, help="Optional path for JSON results")
    parser.add_argument(
        "--report",
        type=Path,
        help="Optional path for an executive Markdown recovery report",
    )
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    evaluated = evaluate_payload(payload)
    rendered = json.dumps(evaluated, indent=2, sort_keys=True)

    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)

    if args.report:
        report = render_executive_markdown(evaluated)
        args.report.write_text(report + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
