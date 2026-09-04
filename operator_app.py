from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit

from aviation_io import evaluate_payload
from executive_report import render_executive_markdown


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


def build_evaluation_response(payload: Mapping[str, Any]) -> dict[str, Any]:
    evaluated = evaluate_payload(payload)
    return {
        "evaluation": evaluated,
        "executive_report_markdown": render_executive_markdown(evaluated),
        "truth_note": (
            "Claim-ready, review-required and blocked amounts are not recovered cash. "
            "Verified settlement requires separate economic settlement evidence."
        ),
    }


class OperatorHandler(BaseHTTPRequestHandler):
    server_version = "AERVINDOperator/1.0"

    def log_message(self, format: str, *args: object) -> None:
        # Deliberately avoid logging request bodies or customer evidence.
        super().log_message(format, *args)

    def _send_headers(self, status: int, content_type: str, content_length: int) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(content_length))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self'; script-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'",
        )
        self.end_headers()

    def _send_bytes(self, status: int, body: bytes, content_type: str) -> None:
        self._send_headers(status, content_type, len(body))
        self.wfile.write(body)

    def _send_json(self, status: int, payload: Mapping[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_bytes(status, body, "application/json; charset=utf-8")

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
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "ui_asset_missing"})
            return
        self._send_bytes(HTTPStatus.OK, body, content_type)

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        path = urlsplit(self.path).path
        if path != "/api/evaluate":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return

        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            self._send_json(
                HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                {"error": "content_type_must_be_application_json"},
            )
            return

        raw_length = self.headers.get("Content-Length")
        try:
            length = int(raw_length or "0")
        except ValueError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_content_length"})
            return

        if length <= 0:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "empty_request"})
            return
        if length > MAX_REQUEST_BYTES:
            self._send_json(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                {"error": "request_too_large", "max_bytes": MAX_REQUEST_BYTES},
            )
            return

        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("top-level JSON must be an object")
            result = build_evaluation_response(payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "invalid_json", "detail": str(exc)},
            )
            return
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
    print("Assisted-pilot mode. Customer payloads are processed in memory and are not persisted by this server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AERVIND assisted operator console")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
