#!/usr/bin/env python3
"""Didit Workflows - Create, list, get, update, and delete verification workflows.

Usage:
    python scripts/manage_workflows.py list [--limit N] [--offset N]
    python scripts/manage_workflows.py create [--label NAME] [--ocr] [--liveness] [--face-match] [--aml] [--poa] [--email] [--phone] [--features JSON] [--draft]
    python scripts/manage_workflows.py get <uuid>
    python scripts/manage_workflows.py update <uuid> [--label NAME] [--default] [--features JSON] [--status draft|published]
    python scripts/manage_workflows.py delete <uuid>

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    python scripts/manage_workflows.py list
    python scripts/manage_workflows.py create --label "Standard KYC" --liveness --face-match
    python scripts/manage_workflows.py create --label "KYC + AML" --liveness --face-match --aml
    python scripts/manage_workflows.py create --label "Age check" --features '[{"feature":"AGE_ESTIMATION"}]'
    python scripts/manage_workflows.py update <uuid> --label "Renamed KYC"
    python scripts/manage_workflows.py update <uuid> --features '[{"feature":"OCR"},{"feature":"AML"}]' --status published
    python scripts/manage_workflows.py delete <uuid>

Notes:
    - The v3 workflow API takes an ordered `features` array (uppercase feature values).
      Flat is_*_enabled flags and `workflow_type` are rejected with 400.
    - `uuid` identifies one workflow version; `workflow_id` is the stable id shared by all versions.
    - PATCH with --status published on a published version creates a NEW version (new uuid).
"""
import argparse
import json
import os
import sys

import requests

BASE_URL = "https://verification.didit.me/v3/workflows"


def get_headers(content_type=False) -> dict:
    api_key = os.environ.get("DIDIT_API_KEY")
    if not api_key:
        print("Error: DIDIT_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    h = {"x-api-key": api_key}
    if content_type:
        h["Content-Type"] = "application/json"
    return h


def _check(r, ok_statuses):
    if r.status_code not in ok_statuses:
        print(f"Error {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)


def list_workflows(limit: int = 50, offset: int = 0) -> dict:
    """Returns the pagination envelope {count, next, previous, results}."""
    r = requests.get(f"{BASE_URL}/", headers=get_headers(),
                     params={"limit": limit, "offset": offset}, timeout=30)
    _check(r, (200,))
    return r.json()


def build_features(ocr=False, liveness=False, face_match=False, aml=False,
                   poa=False, email=False, phone=False) -> list:
    """Build the ordered features array. AML cannot be the first feature, so OCR goes first."""
    features = []
    if ocr or face_match or aml:
        features.append({"feature": "OCR"})
    if liveness:
        features.append({"feature": "LIVENESS", "config": {"face_liveness_method": "PASSIVE"}})
    if face_match:
        features.append({"feature": "FACE_MATCH"})
    if aml:
        features.append({"feature": "AML"})
    if poa:
        features.append({"feature": "PROOF_OF_ADDRESS"})
    if email:
        features.append({"feature": "EMAIL_VERIFICATION"})
    if phone:
        features.append({"feature": "PHONE_VERIFICATION"})
    if not features:
        features = [{"feature": "OCR"},
                    {"feature": "LIVENESS", "config": {"face_liveness_method": "PASSIVE"}},
                    {"feature": "FACE_MATCH"}]
    return features


def create_workflow(label=None, features=None, draft=False) -> dict:
    if not features:
        raise ValueError("create_workflow requires a non-empty features list")
    payload = {"features": features}
    if label:
        payload["workflow_label"] = label
    if draft:
        payload["status"] = "draft"
    r = requests.post(f"{BASE_URL}/", headers=get_headers(content_type=True), json=payload, timeout=30)
    _check(r, (200, 201))
    return r.json()


def get_workflow(uuid: str) -> dict:
    r = requests.get(f"{BASE_URL}/{uuid}/", headers=get_headers(), timeout=30)
    _check(r, (200,))
    return r.json()


def update_workflow(uuid: str, changes: dict) -> dict:
    r = requests.patch(f"{BASE_URL}/{uuid}/", headers=get_headers(content_type=True), json=changes, timeout=30)
    _check(r, (200,))
    return r.json()


def delete_workflow(uuid: str) -> bool:
    r = requests.delete(f"{BASE_URL}/{uuid}/", headers=get_headers(), timeout=30)
    _check(r, (200, 204))
    return True


def _parse_features(raw: str) -> list:
    try:
        features = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Invalid --features JSON: {e}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(features, list) or not features:
        print("--features must be a non-empty JSON array", file=sys.stderr)
        sys.exit(1)
    return features


def main():
    parser = argparse.ArgumentParser(description="Manage Didit verification workflows")
    sub = parser.add_subparsers(dest="command", required=True)

    list_p = sub.add_parser("list", help="List workflow versions (paginated)")
    list_p.add_argument("--limit", type=int, default=50, help="Page size (default 50)")
    list_p.add_argument("--offset", type=int, default=0, help="Rows to skip (default 0)")

    create_p = sub.add_parser("create", help="Create a new workflow")
    create_p.add_argument("--label", help="Workflow display name (max 50 chars)")
    create_p.add_argument("--ocr", action="store_true", help="Add ID document (OCR) step")
    create_p.add_argument("--liveness", action="store_true", help="Add liveness detection step")
    create_p.add_argument("--face-match", action="store_true", help="Add face match step (adds OCR first)")
    create_p.add_argument("--aml", action="store_true", help="Add AML screening step (adds OCR first)")
    create_p.add_argument("--poa", action="store_true", help="Add proof-of-address step")
    create_p.add_argument("--email", action="store_true", help="Add email verification step")
    create_p.add_argument("--phone", action="store_true", help="Add phone verification step")
    create_p.add_argument("--features", help="Full features array as a JSON string (overrides the flags above; "
                                             "use for NFC, DATABASE_VALIDATION, QUESTIONNAIRE, AGE_ESTIMATION, "
                                             "IP_ANALYSIS, DOCUMENT_AI, KYB_* or per-feature config)")
    create_p.add_argument("--draft", action="store_true", help="Save as a draft instead of publishing")

    get_p = sub.add_parser("get", help="Get one workflow version")
    get_p.add_argument("uuid", help="Workflow version UUID")

    update_p = sub.add_parser("update", help="Update a workflow version")
    update_p.add_argument("uuid", help="Workflow version UUID")
    update_p.add_argument("--label", help="New workflow label")
    update_p.add_argument("--default", action="store_true", help="Set as the default workflow")
    update_p.add_argument("--features", help="Replacement features array as a JSON string")
    update_p.add_argument("--status", choices=["draft", "published"],
                          help="'published' on a published version creates a new version")

    del_p = sub.add_parser("delete", help="Delete one workflow version")
    del_p.add_argument("uuid", help="Workflow version UUID")

    args = parser.parse_args()

    if args.command == "list":
        page = list_workflows(args.limit, args.offset)
        print(json.dumps(page, indent=2))
        results = page.get("results", [])
        print(f"\n--- {len(results)} of {page.get('count', len(results))} workflow version(s) ---")
        for wf in results:
            default = " (default)" if wf.get("is_default") else ""
            wf_type = wf.get("workflow_type") or "custom"
            print(f"  {wf.get('uuid')} v{wf.get('version')} {wf.get('status')} - "
                  f"{wf.get('workflow_label', 'Untitled')} [{wf_type}] {wf.get('features', '')}{default}")

    elif args.command == "create":
        if args.features:
            features = _parse_features(args.features)
        else:
            features = build_features(args.ocr, args.liveness, args.face_match, args.aml,
                                      args.poa, args.email, args.phone)
        result = create_workflow(args.label, features, args.draft)
        print(json.dumps(result, indent=2))
        print(f"\n--- Created workflow version {result.get('uuid')} (status {result.get('status')}) ---")

    elif args.command == "get":
        result = get_workflow(args.uuid)
        print(json.dumps(result, indent=2))
        print(f"\n--- {result.get('workflow_label')} v{result.get('version')} ({result.get('status')}) ---")

    elif args.command == "update":
        changes = {}
        if args.label:
            changes["workflow_label"] = args.label
        if args.default:
            changes["is_default"] = True
        if args.features:
            changes["features"] = _parse_features(args.features)
        if args.status:
            changes["status"] = args.status
        if not changes:
            print("No changes specified. Use --label, --default, --features or --status.", file=sys.stderr)
            sys.exit(1)
        result = update_workflow(args.uuid, changes)
        print(json.dumps(result, indent=2))
        print(f"\n--- Updated: now version {result.get('uuid')} v{result.get('version')} ({result.get('status')}) ---")

    elif args.command == "delete":
        delete_workflow(args.uuid)
        print(f"--- Deleted workflow version: {args.uuid} ---")


if __name__ == "__main__":
    main()
