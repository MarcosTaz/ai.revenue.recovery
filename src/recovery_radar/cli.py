from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
from typing import Any, Sequence

from .gateway import RecoveryRadarGateway
from .pilot_bundle import ingest_pilot_bundle, load_pilot_bundle
from .storage import Storage
from .t2_io import export_scorecard_atomic, load_ground_truth, score_from_input

TOKEN_ENV = "RECOVERY_RADAR_TOKEN"


def _token() -> str:
    token = os.environ.get(TOKEN_ENV, "")
    if not token:
        raise PermissionError(f"{TOKEN_ENV}_REQUIRED")
    return token


def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(_jsonable(payload), sort_keys=True, ensure_ascii=False))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="recovery-radar",
        description="Assisted-pilot operator interface for Recovery Radar",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    bootstrap = sub.add_parser("bootstrap", help="create workspace and first admin key")
    bootstrap.add_argument("--db", required=True)
    bootstrap.add_argument("--workspace", required=True)
    bootstrap.add_argument("--name", required=True)
    bootstrap.add_argument("--actor", required=True)

    issue = sub.add_parser("issue-key", help="issue a tenant-scoped API key")
    issue.add_argument("--db", required=True)
    issue.add_argument("--actor", required=True)
    issue.add_argument("--role", required=True, choices=["ADMIN", "ANALYST", "REVIEWER"])

    ingest = sub.add_parser("import-bundle", help="import normalized source truth")
    ingest.add_argument("--db", required=True)
    ingest.add_argument("--bundle", required=True)

    review_evidence = sub.add_parser("review-evidence", help="review one evidence document")
    review_evidence.add_argument("--db", required=True)
    review_evidence.add_argument("--document-id", required=True)
    review_evidence.add_argument("--state", required=True, choices=["VERIFIED", "REJECTED"])
    review_evidence.add_argument("--note", default="")

    review_entitlement = sub.add_parser("review-entitlement", help="review one entitlement interpretation")
    review_entitlement.add_argument("--db", required=True)
    review_entitlement.add_argument("--entitlement-id", required=True)
    review_entitlement.add_argument("--state", required=True, choices=["VERIFIED", "REJECTED"])
    review_entitlement.add_argument("--note", default="")

    package = sub.add_parser("package", help="build current evidence-gated claim package")
    package.add_argument("--db", required=True)
    package.add_argument("--event-id", required=True)
    package.add_argument("--supplier-id", required=True)

    export = sub.add_parser("export", help="atomically export current claim package")
    export.add_argument("--db", required=True)
    export.add_argument("--event-id", required=True)
    export.add_argument("--supplier-id", required=True)
    export.add_argument("--output", required=True)

    create_case = sub.add_parser("create-case", help="derive a workflow case from current claimable truth")
    create_case.add_argument("--db", required=True)
    create_case.add_argument("--event-id", required=True)
    create_case.add_argument("--supplier-id", required=True)
    create_case.add_argument("--exposure-id", action="append", dest="exposure_ids")

    score = sub.add_parser(
        "score-historical",
        help="score current gated analysis against explicit historical ground truth",
    )
    score.add_argument("--db", required=True)
    score.add_argument("--event-id", required=True)
    score.add_argument("--supplier-id", required=True)
    score.add_argument("--ground-truth", required=True)
    score.add_argument("--output", required=True)

    return parser


def _open(db: str) -> tuple[Storage, RecoveryRadarGateway]:
    storage = Storage(Path(db))
    try:
        return storage, RecoveryRadarGateway(storage)
    except Exception:
        storage.close()
        raise


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    args = _parser().parse_args(argv)

    if args.command == "bootstrap":
        storage = Storage(Path(args.db))
        try:
            storage.create_workspace(args.workspace, args.name)
            gateway = RecoveryRadarGateway(storage)
            token = gateway.bootstrap_workspace_admin(args.workspace, args.actor)
            return {
                "command": "bootstrap",
                "workspace_id": args.workspace,
                "actor_id": args.actor,
                "role": "ADMIN",
                "api_token": token,
                "token_notice": "SECRET_RETURNED_ONCE_STORE_SECURELY",
                "schema": gateway.schema,
            }
        finally:
            storage.close()

    storage, gateway = _open(args.db)
    try:
        token = _token()
        if args.command == "issue-key":
            issued = gateway.issue_key(token, args.actor, args.role)
            principal = gateway.auth.authenticate(issued)
            return {
                "command": "issue-key",
                "workspace_id": principal.workspace_id,
                "actor_id": principal.actor_id,
                "role": principal.role,
                "api_token": issued,
                "token_notice": "SECRET_RETURNED_ONCE_STORE_SECURELY",
            }

        principal = gateway.auth.authenticate(token)
        if args.command == "import-bundle":
            bundle = load_pilot_bundle(args.bundle, workspace_id=principal.workspace_id)
            result = ingest_pilot_bundle(gateway, token, bundle)
            return {"command": "import-bundle", **result}

        if args.command == "review-evidence":
            gateway.review_evidence_document(
                token, args.document_id, args.state, args.note
            )
            return {
                "command": "review-evidence",
                "document_id": args.document_id,
                "state": args.state,
            }

        if args.command == "review-entitlement":
            gateway.review_entitlement_basis(
                token, args.entitlement_id, args.state, args.note
            )
            return {
                "command": "review-entitlement",
                "entitlement_id": args.entitlement_id,
                "state": args.state,
            }

        if args.command == "package":
            package = gateway.build_claim_package(token, args.event_id, args.supplier_id)
            return {"command": "package", "package": package}

        if args.command == "export":
            manifest = gateway.export_claim_package(
                token, args.event_id, args.supplier_id, args.output
            )
            return {"command": "export", "manifest": manifest}

        if args.command == "create-case":
            case = gateway.create_case(
                token,
                args.event_id,
                args.supplier_id,
                selected_exposure_ids=args.exposure_ids,
            )
            return {"command": "create-case", "case": asdict(case)}

        if args.command == "score-historical":
            analysis = gateway.analyze_event(token, args.event_id, args.supplier_id)
            ground_truth = load_ground_truth(args.ground_truth)
            scorecard = score_from_input(analysis, ground_truth)
            manifest = export_scorecard_atomic(scorecard, args.output)
            return {
                "command": "score-historical",
                "manifest": manifest,
                "validation_classification": scorecard["validation_classification"],
                "terminal_promotion": scorecard["terminal_promotion"],
            }

        raise RuntimeError("UNREACHABLE_COMMAND")
    finally:
        storage.close()


def main(argv: Sequence[str] | None = None) -> int:
    try:
        _emit({"ok": True, **run(argv)})
        return 0
    except (ValueError, KeyError, PermissionError, RuntimeError) as exc:
        _emit({"ok": False, "error": str(exc)})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
