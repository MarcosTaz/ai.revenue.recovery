from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit

from aviation_io import evaluate_payload
from claim_package import render_external_claim_markdown
from claim_workflow import ClaimLifecycle
from executive_report import (
    jsonify_management_truth,
    render_executive_markdown,
    summarize_management_truth,
)
from workflow_case import (
    bind_or_validate_cohort_revision,
    build_case_export,
    parse_bundle,
    reconcile_bundle_with_evaluation,
    record_claim_package_artifact,
    serialize_bundle,
    transition_bundle,
    workflow_view,
)


ROOT = Path(__file__).resolve().parent
UI_ROOT = ROOT / "operator_ui"
EXAMPLE_PATH = ROOT / "examples" / "pilot.json"
MAX_REQUEST_BYTES = 2 * 1024 * 1024

STATIC_FILES = {
    "/": (UI_ROOT / "index.html", "text/html; charset=utf-8"),
    "/app.css": (UI_ROOT / "app.css", "text/css; charset=utf-8"),
    "/app.js": (UI_ROOT / "app.js", "text/javascript; charset=utf-8"),
}


def load_synthetic_example() -> dict[str, Any]:
    return json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))


def _normalized_workflow(
    cohort: Mapping[str, Any],
    evaluated: Mapping[str, Any],
    workflow_bundle: Mapping[str, Any] | None,
) -> tuple[list[Any], dict[str, Any]]:
    records, events, artifacts, existing_digest = parse_bundle(workflow_bundle)
    reconcile_bundle_with_evaluation(records, evaluated)
    bound_digest = bind_or_validate_cohort_revision(
        cohort=cohort,
        records=records,
        existing_digest=existing_digest,
    )
    normalized = serialize_bundle(
        records,
        events,
        artifacts,
        bound_cohort_digest=bound_digest,
    )
    return records, normalized


def build_case_response(
    cohort: Mapping[str, Any],
    workflow_bundle: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    evaluated = evaluate_payload(cohort)
    records, normalized_workflow = _normalized_workflow(
        cohort, evaluated, workflow_bundle
    )
    management = summarize_management_truth(evaluated, records)
    return {
        "evaluation": evaluated,
        "workflow": normalized_workflow,
        "workflow_view": workflow_view(normalized_workflow),
        "management_truth": jsonify_management_truth(management),
        "executive_report_markdown": render_executive_markdown(evaluated, records),
        "truth_note": (
            "Every candidate belongs to one economic/workflow bucket. Claim-ready, "
            "submitted, acknowledged, disputed or approved value is not recovered cash. "
            "Verified recovery requires evidence-backed settlement."
        ),
    }


def build_evaluation_response(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Backward-compatible cohort-only evaluation used by the CLI-style API test."""
    return build_case_response(payload, None)


def build_workflow_transition_response(
    *,
    cohort: Mapping[str, Any],
    workflow_bundle: Mapping[str, Any] | None,
    claim_id: str,
    target: str,
    occurred_at: str,
    actor: str,
    reason: str,
    external_reference: str | None = None,
    settlement: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    evaluated = evaluate_payload(cohort)
    updated_workflow = transition_bundle(
        cohort=cohort,
        evaluated=evaluated,
        bundle=workflow_bundle,
        claim_id=claim_id,
        target=target,
        occurred_at=occurred_at,
        actor=actor,
        reason=reason,
        external_reference=external_reference,
        settlement=settlement,
    )
    return build_case_response(cohort, updated_workflow)


def build_claim_package_response(
    payload: Mapping[str, Any],
    *,
    workflow_bundle: Mapping[str, Any] | None,
    claim_id: str,
    human_release_confirmed: bool,
    generated_at: str,
    generated_by: str,
) -> dict[str, Any]:
    """Render and audit, but never submit, an external-ready claim package."""
    if not human_release_confirmed:
        raise ValueError("human release confirmation is required")

    normalized_claim_id = str(claim_id).strip()
    if not normalized_claim_id:
        raise ValueError("claim_id is required")

    evaluated = evaluate_payload(payload)
    records, normalized_workflow = _normalized_workflow(
        payload, evaluated, workflow_bundle
    )
    record = next(
        (item for item in records if item.claim_id == normalized_claim_id), None
    )
    if record is None or record.lifecycle != ClaimLifecycle.CLAIM_READY:
        raise ValueError(
            "claim package requires the auditable workflow lifecycle to be claim_ready"
        )

    dossier = next(
        (
            item
            for item in evaluated.get("dossiers", [])
            if item.get("claim", {}).get("claim_id") == normalized_claim_id
        ),
        None,
    )
    if dossier is None:
        raise ValueError("claim_id not found in evaluated cohort")

    claim = dossier.get("claim", {})
    status = str(claim.get("status", "unknown"))
    if status != "claim_ready":
        raise ValueError(f"claim package requires claim_ready candidate, got {status}")

    blockers = list(dossier.get("blocking_issues", []))
    lineage_gaps = list(dossier.get("lineage_gaps", []))
    if blockers or lineage_gaps:
        raise ValueError(
            "claim package blocked by unresolved evidence or source lineage"
        )

    external_dossier = dict(dossier)
    external_dossier["externalization_gate"] = "passed"
    markdown = render_external_claim_markdown(external_dossier)
    audited_workflow = record_claim_package_artifact(
        cohort=payload,
        evaluated=evaluated,
        bundle=normalized_workflow,
        claim_id=normalized_claim_id,
        generated_at=generated_at,
        generated_by=generated_by,
        content=markdown,
    )
    case_response = build_case_response(payload, audited_workflow)

    return {
        **case_response,
        "claim_id": normalized_claim_id,
        "claim_package_markdown": markdown,
        "external_dossier": external_dossier,
        "human_release_confirmed": True,
        "submission_status": "not_submitted",
        "submission_note": (
            "Package generation does not send or submit anything to a lessor, airline, "
            "counterparty or external system."
        ),
    }


def build_case_export_response(
    cohort: Mapping[str, Any],
    workflow_bundle: Mapping[str, Any] | None,
) -> dict[str, Any]:
    response = build_case_response(cohort, workflow_bundle)
    exported = build_case_export(
        cohort=cohort,
        evaluated=response["evaluation"],
        workflow_bundle=response["workflow"],
    )
    return {
        "case": exported,
        "workflow_view": response["workflow_view"],
        "management_truth": response["management_truth"],
    }


class OperatorHandler(BaseHTTPRequestHandler):
    server_version = "AERVINDOperator/1.2"

    def log_message(self, format: str, *args: object) -> None:
        # Request bodies/customer evidence are never logged by this application.
        super().log_message(format, *args)

    def _send_headers(
        self, status: int, content_type: str, content_length: int
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(content_length))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Permitted-Cross-Domain-Policies", "none")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
        )
        self.send_header("Cache-Control", "no-store")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self'; script-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
            "base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
        )
        self.end_headers()

    def _send_bytes(self, status: int, body: bytes, content_type: str) -> None:
        self._send_headers(status, content_type, len(body))
        self.wfile.write(body)

    def _send_json(self, status: int, payload: Mapping[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_bytes(status, body, "application/json; charset=utf-8")

    def _read_json_body(self) -> dict[str, Any] | None:
        content_type = (
            self.headers.get("Content-Type", "")
            .split(";", 1)[0]
            .strip()
            .lower()
        )
        if content_type != "application/json":
            self._send_json(
                HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                {"error": "content_type_must_be_application_json"},
            )
            return None

        raw_length = self.headers.get("Content-Length")
        try:
            length = int(raw_length or "0")
        except ValueError:
            self._send_json(
                HTTPStatus.BAD_REQUEST, {"error": "invalid_content_length"}
            )
            return None

        if length <= 0:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "empty_request"})
            return None
        if length > MAX_REQUEST_BYTES:
            self._send_json(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                {"error": "request_too_large", "max_bytes": MAX_REQUEST_BYTES},
            )
            return None

        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "invalid_json", "detail": str(exc)},
            )
            return None

        if not isinstance(payload, dict):
            self._send_json(
                HTTPStatus.UNPROCESSABLE_ENTITY,
                {
                    "error": "invalid_recovery_payload",
                    "detail": "top-level JSON must be an object",
                },
            )
            return None
        return payload

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        path = urlsplit(self.path).path

        if path == "/api/health":
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "service": "AERVIND Operator Console",
                    "mode": "assisted_pilot",
                    "persistence": "none",
                    "case_state": "portable_export_only",
                },
            )
            return

        if path == "/api/example":
            self._send_json(
                HTTPStatus.OK,
                {
                    "synthetic": True,
                    "label": "Synthetic pilot example — not customer data",
                    "payload": load_synthetic_example(),
                },
            )
            return

        static = STATIC_FILES.get(path)
        if static is None:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return

        file_path, content_type = static
        try:
            body = file_path.read_bytes()
        except FileNotFoundError:
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "ui_asset_missing"}
            )
            return
        self._send_bytes(HTTPStatus.OK, body, content_type)

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        path = urlsplit(self.path).path
        supported = {
            "/api/evaluate",
            "/api/evaluate-case",
            "/api/workflow-transition",
            "/api/claim-package",
            "/api/case-export",
        }
        if path not in supported:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return

        request_payload = self._read_json_body()
        if request_payload is None:
            return

        try:
            if path == "/api/evaluate":
                result = build_evaluation_response(request_payload)
            else:
                cohort = request_payload.get("payload")
                if not isinstance(cohort, dict):
                    raise ValueError(
                        "payload must contain the Recovery Scan cohort object"
                    )
                workflow = request_payload.get("workflow")
                if workflow is not None and not isinstance(workflow, dict):
                    raise ValueError("workflow must be an object when supplied")

                if path == "/api/evaluate-case":
                    result = build_case_response(cohort, workflow)
                elif path == "/api/workflow-transition":
                    settlement = request_payload.get("settlement")
                    if settlement is not None and not isinstance(settlement, dict):
                        raise ValueError("settlement must be an object when supplied")
                    result = build_workflow_transition_response(
                        cohort=cohort,
                        workflow_bundle=workflow,
                        claim_id=str(request_payload.get("claim_id", "")),
                        target=str(request_payload.get("target", "")),
                        occurred_at=str(request_payload.get("occurred_at", "")),
                        actor=str(request_payload.get("actor", "")),
                        reason=str(request_payload.get("reason", "")),
                        external_reference=(
                            str(request_payload["external_reference"])
                            if request_payload.get("external_reference") is not None
                            else None
                        ),
                        settlement=settlement,
                    )
                elif path == "/api/claim-package":
                    result = build_claim_package_response(
                        cohort,
                        workflow_bundle=workflow,
                        claim_id=str(request_payload.get("claim_id", "")),
                        human_release_confirmed=(
                            request_payload.get("human_release_confirmed") is True
                        ),
                        generated_at=str(request_payload.get("generated_at", "")),
                        generated_by=str(request_payload.get("generated_by", "")),
                    )
                else:
                    result = build_case_export_response(cohort, workflow)
        except (KeyError, TypeError, ValueError) as exc:
            self._send_json(
                HTTPStatus.UNPROCESSABLE_ENTITY,
                {"error": "invalid_recovery_payload", "detail": str(exc)},
            )
            return

        self._send_json(HTTPStatus.OK, result)


def run(host: str = "127.0.0.1", port: int = 8080) -> None:
    server = ThreadingHTTPServer((host, port), OperatorHandler)
    print(f"AERVIND Operator Console: http://{host}:{port}")
    print(
        "Assisted-pilot mode. Customer payloads are processed in memory. "
        "Durable state exists only in operator-exported case files."
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the AERVIND assisted operator console"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
