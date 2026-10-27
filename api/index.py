"""Private synthetic-only preview of the existing AERVIND recovery engine.
Not customer-ready. Vercel deployment authentication must stay enabled.
"""
import os
import sys
from pathlib import Path
from flask import Flask, jsonify, request, send_file
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from operator_app import (
    load_synthetic_example,build_case_response,build_evaluation_response,
    build_case_export_response,build_workflow_transition_response,
    build_claim_package_response)
app=Flask(__name__)
app.config["MAX_CONTENT_LENGTH"]=2*1024*1024
EXAMPLE=load_synthetic_example()
STATIC={"/":"index.html","/app.css":"app.css","/app.js":"app.js"}
@app.before_request
def guard():
    if os.environ.get("AERVIND_NO_SEND_HOLD")!="ACTIVE" or os.environ.get("AERVIND_ENV")!="preview":
        return jsonify(error="preview_disabled"),503
    if request.method not in ("GET","POST"):
        return jsonify(error="method_denied"),405
    if request.method=="POST":
        origin=request.headers.get("Origin")
        if origin and origin!=request.host_url.rstrip("/"):
            return jsonify(error="origin_denied"),403
        if request.mimetype!="application/json":
            return jsonify(error="json_required"),415
@app.after_request
def response_headers(response):
    response.headers["Cache-Control"]="no-store"
    response.headers["X-Content-Type-Options"]="nosniff"
    response.headers["X-Frame-Options"]="DENY"
    response.headers["X-Robots-Tag"]="noindex, nofollow"
    response.headers["Referrer-Policy"]="no-referrer"
    response.headers["Content-Security-Policy"]="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    response.headers["X-AERVIND-Preview"]="synthetic-only"
    return response
@app.get("/api/health")
def health():
    return jsonify(status="ok",mode="private_synthetic_preview",external_send="HOLD",customer_data_allowed=False)
@app.get("/api/example")
def example():
    return jsonify(synthetic=True,label="SYNTHETIC ONLY — NOT CUSTOMER DATA",payload=EXAMPLE)
@app.get("/")
@app.get("/<path:path>")
def preview_asset(path=""):
    asset=STATIC.get("/"+path)
    if not asset:
        return jsonify(error="not_found"),404
    path=ROOT/"operator_ui"/asset
    if not path.is_file():
        return jsonify(error="static_asset_missing"),503
    mime={"index.html":"text/html","app.css":"text/css","app.js":"application/javascript"}[asset]
    return send_file(path,mimetype=mime)
@app.post("/api/evaluate")
@app.post("/api/evaluate-case")
@app.post("/api/workflow-transition")
@app.post("/api/claim-package")
@app.post("/api/case-export")
def run_evaluation():
    body=request.get_json(silent=True)
    if not isinstance(body,dict):
        return jsonify(error="invalid_json"),400
    op=request.path
    cohort=body if op=="/api/evaluate" else body.get("payload")
    if not isinstance(cohort,dict) or cohort!=EXAMPLE:
        return jsonify(error="synthetic_cohort_required",customer_data_allowed=False),403
    workflow=body.get("workflow")
    if workflow is not None and not isinstance(workflow,dict):
        return jsonify(error="invalid_workflow"),422
    try:
        if op=="/api/evaluate":
            result=build_evaluation_response(cohort)
        elif op=="/api/evaluate-case":
            result=build_case_response(cohort,workflow)
        elif op=="/api/case-export":
            result=build_case_export_response(cohort,workflow)
        elif op=="/api/claim-package":
            result=build_claim_package_response(cohort,workflow_bundle=workflow,
                claim_id=str(body.get("claim_id","")),
                human_release_confirmed=body.get("human_release_confirmed") is True,
                generated_at=str(body.get("generated_at","")),
                generated_by=str(body.get("generated_by","")))
        else:
            result=build_workflow_transition_response(
                cohort=cohort,workflow_bundle=workflow,
                claim_id=str(body.get("claim_id","")),
                target=str(body.get("target","")),
                occurred_at=str(body.get("occurred_at","")),
                actor=str(body.get("actor","")),
                reason=str(body.get("reason","")),
                external_reference=str(body["external_reference"]) if body.get("external_reference") is not None else None,
                settlement=body.get("settlement"))
    except (ValueError,KeyError,TypeError) as exc:
        return jsonify(error="workflow_rejected",detail=str(exc)[:250]),422
    return jsonify(result)
