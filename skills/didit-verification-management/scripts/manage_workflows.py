#!/usr/bin/env python3
"""Didit Workflows - Create, list, update, and delete verification workflows.

Usage:
    python scripts/manage_workflows.py list
    python scripts/manage_workflows.py create [--label NAME] [--ocr] [--liveness] [--face-match] [--aml] [--poa] [--email] [--phone]
    python scripts/manage_workflows.py get <uuid>
    python scripts/manage_workflows.py update <uuid> [--label NAME] [--default] [--features '<json array>']
    python scripts/manage_workflows.py delete <uuid>

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    python scripts/manage_workflows.py list
    python scripts/manage_workflows.py create --label "Standard KYC" --liveness --face-match
    python scripts/manage_workflows.py create --label "KYC + AML" --liveness --face-match --aml
    python scripts/manage_workflows.py update abc-123 --label "Renamed KYC"
    python scripts/manage_workflows.py update abc-123 --features '[{"feature":"OCR"},{"feature":"AML"}]'
    python scripts/manage_workflows.py delete abc-123

Note: the v3 workflow API takes an ordered `features` array (uppercase feature
values), NOT flat is_*_enabled flags or a workflow_type — those are rejected with 400.
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


def list_workflows() -> list:
    r = requests.get(f"{BASE_URL}/", headers=get_headers(), timeout=30)
    if r.status_code != 200:
        print(f"Error {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)
    return r.json()


def build_features(ocr=False, liveness=False, face_match=False, aml=False,
                   poa=False, email=False, phone=False) -> list:
    """Build the ordered features array. Dependency features (OCR) come first."""
    features = []
    # OCR must run first for any feature that consumes document/identity data
    # (face match against the ID portrait, AML screening of the extracted name).
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
    # Sensible default: full KYC if no feature flags were given.
    if not features:
        features = [{"feature": "OCR"},
                    {"feature": "LIVENESS", "config": {"face_liveness_method": "PASSIVE"}},
                    {"feature": "FACE_MATCH"}]
    return features


def create_workflow(label=None, features=None) -> dict:
    if not features:
        raise ValueError("create_workflow requires a non-empty features list")
    payload = {"features": features}
    if label:
        payload["workflow_label"] = label
    r = requests.post(f"{BASE_URL}/", headers=get_headers(content_type=True), json=payload, timeout=30)
    if r.status_code not in (200, 201):
        print(f"Error {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)
    return r.json()


def get_workflow(uuid: str) -> dict:
    r = requests.get(f"{BASE_URL}/{uuid}/", headers=get_headers(), timeout=30)
    if r.status_code != 200:
        print(f"Error {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)
    return r.json()


def update_workflow(uuid: str, changes: dict) -> dict:
    r = requests.patch(f"{BASE_URL}/{uuid}/", headers=get_headers(content_type=True), json=changes, timeout=30)
    if r.status_code != 200:
        print(f"Error {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)
    return r.json()


def delete_workflow(uuid: str) -> bool:
    r = requests.delete(f"{BASE_URL}/{uuid}/", headers=get_headers(), timeout=30)
    if r.status_code not in (200, 204):
        print(f"Error {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)
    return True


def main():
    parser = argparse.ArgumentParser(description="Manage Didit verification workflows")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List all workflows")

    create_p = sub.add_parser("create", help="Create a new workflow")
    create_p.add_argument("--label", help="Workflow display name")
    create_p.add_argument("--ocr", action="store_true", help="Add ID document (OCR) step")
    create_p.add_argument("--liveness", action="store_true", help="Add liveness detection step")
    create_p.add_argument("--face-match", action="store_true", help="Add face match step (implies OCR)")
    create_p.add_argument("--aml", action="store_true", help="Add AML screening step")
    create_p.add_argument("--poa", action="store_true", help="Add proof-of-address step")
    create_p.add_argument("--email", action="store_true", help="Add email verification step")
    create_p.add_argument("--phone", action="store_true", help="Add phone verification step")
    create_p.add_argument("--features", help="Full features array as a JSON string (overrides the flags above; "
                                             "use for NFC, DATABASE_VALIDATION, QUESTIONNAIRE, AGE_ESTIMATION, "
                                             "IP_ANALYSIS, KYB_REGISTRY/DOCUMENTS/KEY_PEOPLE, or per-feature config)")

    get_p = sub.add_parser("get", help="Get workflow details")
    get_p.add_argument("uuid", help="Workflow UUID")

    update_p = sub.add_parser("update", help="Update a workflow")
    update_p.add_argument("uuid", help="Workflow UUID")
    update_p.add_argument("--label", help="Update workflow label")
    update_p.add_argument("--default", action="store_true", help="Set as the default workflow")
    update_p.add_argument("--features", help="Replacement features array as a JSON string")

    del_p = sub.add_parser("delete", help="Delete a workflow")
    del_p.add_argument("uuid", help="Workflow UUID")

    args = parser.parse_args()

    if args.command == "list":
        workflows = list_workflows()
        print(json.dumps(workflows, indent=2))
        print(f"\n--- {len(workflows)} workflow(s) ---")
        for wf in workflows:
            default = " (default)" if wf.get("is_default") else ""
            print(f"  {wf['uuid']} — {wf.get('workflow_label', 'Untitled')} [{wf.get('workflow_type')}]{default}")

    elif args.command == "create":
        if args.features:
            try:
                features = json.loads(args.features)
            except json.JSONDecodeError as e:
                print(f"Invalid --features JSON: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            features = build_features(args.ocr, args.liveness, args.face_match, args.aml,
                                      args.poa, args.email, args.phone)
        result = create_workflow(args.label, features)
        print(json.dumps(result, indent=2))
        print(f"\n--- Created workflow: {result.get('uuid')} ---")

    elif args.command == "get":
        result = get_workflow(args.uuid)
        print(json.dumps(result, indent=2))

    elif args.command == "update":
        changes = {}
        if args.label:
            changes["workflow_label"] = args.label
        if args.default:
            changes["is_default"] = True
        if args.features:
            try:
                changes["features"] = json.loads(args.features)
            except json.JSONDecodeError as e:
                print(f"Invalid --features JSON: {e}", file=sys.stderr)
                sys.exit(1)
        if not changes:
            print("No changes specified. Use --label, --default, or --features.", file=sys.stderr)
            sys.exit(1)
        result = update_workflow(args.uuid, changes)
        print(json.dumps(result, indent=2))
        print(f"\n--- Updated workflow: {args.uuid} ---")

    elif args.command == "delete":
        delete_workflow(args.uuid)
        print(f"--- Deleted workflow: {args.uuid} ---")


if __name__ == "__main__":
    main()
