#!/usr/bin/env python3
"""Didit KYC — Create a KYC workflow, session, and retrieve decisions.

Usage:
    python scripts/run_kyc.py setup [--label NAME] [--liveness] [--face-match] [--aml] [--nfc]
    python scripts/run_kyc.py session --workflow-id UUID [--vendor-data ID] [--callback URL]
    python scripts/run_kyc.py decision <session_id> [--poll] [--interval SECONDS]
    python scripts/run_kyc.py full [--vendor-data ID] [--callback URL] [--label NAME]

Commands:
    setup     Create a KYC workflow (one-time — reuse the workflow_id)
    session   Create a verification session for a user
    decision  Get the verification decision for a session
    full      Full flow: create workflow + session in one command

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    python scripts/run_kyc.py setup --label "Onboarding KYC" --liveness --face-match
    python scripts/run_kyc.py session --workflow-id d8d2fa2d-... --vendor-data user-123
    python scripts/run_kyc.py decision 11111111-2222-... --poll --interval 15
    python scripts/run_kyc.py full --vendor-data user-abc --callback https://myapp.com/done
"""
import argparse
import json
import os
import sys
import time

import requests

BASE_URL = "https://verification.didit.me/v3"


def get_headers(content_type=False) -> dict:
    api_key = os.environ.get("DIDIT_API_KEY")
    if not api_key:
        print("Error: DIDIT_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    h = {"x-api-key": api_key}
    if content_type:
        h["Content-Type"] = "application/json"
    return h


def setup_kyc_workflow(label="KYC Onboarding", liveness=True, face_match=True,
                       aml=False, nfc=False) -> dict:
    """Create a KYC workflow with recommended defaults."""
    payload = {
        "workflow_label": label,
        "workflow_type": "kyc",
        "is_liveness_enabled": liveness,
        "is_face_match_enabled": face_match,
        "face_match_score_decline_threshold": 50,
        "max_retry_attempts": 3,
    }
    if aml:
        payload["is_aml_enabled"] = True
        payload["aml_decline_threshold"] = 80
    if nfc:
        payload["is_nfc_enabled"] = True

    r = requests.post(f"{BASE_URL}/workflows/", headers=get_headers(content_type=True),
                      json=payload, timeout=30)
    if r.status_code not in (200, 201):
        print(f"Error {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)
    return r.json()


def create_kyc_session(workflow_id: str, vendor_data: str = None,
                       callback: str = None, language: str = None) -> dict:
    """Create a verification session for a user."""
    payload = {"workflow_id": workflow_id}
    if vendor_data:
        payload["vendor_data"] = vendor_data
    if callback:
        payload["callback"] = callback
    if language:
        payload["language"] = language

    r = requests.post(f"{BASE_URL}/session/", headers=get_headers(content_type=True),
                      json=payload, timeout=30)
    if r.status_code not in (200, 201):
        print(f"Error {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)
    return r.json()


def get_decision(session_id: str) -> dict:
    """Retrieve the verification decision for a session."""
    r = requests.get(f"{BASE_URL}/session/{session_id}/decision/",
                     headers=get_headers(), timeout=30)
    if r.status_code != 200:
        print(f"Error {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)
    return r.json()


def poll_decision(session_id: str, interval: int = 10, max_wait: int = 600) -> dict:
    """Poll until a terminal status is reached or timeout."""
    terminal = {"Approved", "Declined", "In Review", "Expired"}
    elapsed = 0
    while elapsed < max_wait:
        result = get_decision(session_id)
        status = result.get("status", "")
        print(f"  [{elapsed}s] Status: {status}")
        if status in terminal:
            return result
        time.sleep(interval)
        elapsed += interval
    print(f"Timeout after {max_wait}s. Last status: {status}", file=sys.stderr)
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Didit KYC — End-to-end identity verification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Full docs: https://docs.didit.me/sessions-api/management-api",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # setup
    setup_p = sub.add_parser("setup", help="Create a KYC workflow")
    setup_p.add_argument("--label", default="KYC Onboarding", help="Workflow display name")
    setup_p.add_argument("--liveness", action="store_true", default=True,
                         help="Enable liveness detection (default: on)")
    setup_p.add_argument("--no-liveness", action="store_false", dest="liveness",
                         help="Disable liveness detection")
    setup_p.add_argument("--face-match", action="store_true", default=True,
                         help="Enable face match (default: on)")
    setup_p.add_argument("--no-face-match", action="store_false", dest="face_match",
                         help="Disable face match")
    setup_p.add_argument("--aml", action="store_true", help="Enable AML screening")
    setup_p.add_argument("--nfc", action="store_true", help="Enable NFC chip reading")

    # session
    sess_p = sub.add_parser("session", help="Create a verification session")
    sess_p.add_argument("--workflow-id", required=True, help="Workflow UUID from setup")
    sess_p.add_argument("--vendor-data", help="Your user ID to link the session")
    sess_p.add_argument("--callback", help="Redirect URL after verification")
    sess_p.add_argument("--language", help="UI language code (e.g. en, es, de)")

    # decision
    dec_p = sub.add_parser("decision", help="Get verification decision")
    dec_p.add_argument("session_id", help="Session UUID")
    dec_p.add_argument("--poll", action="store_true", help="Poll until terminal status")
    dec_p.add_argument("--interval", type=int, default=10, help="Poll interval in seconds (default: 10)")
    dec_p.add_argument("--max-wait", type=int, default=600, help="Max poll time in seconds (default: 600)")

    # full
    full_p = sub.add_parser("full", help="Full flow: create workflow + session")
    full_p.add_argument("--vendor-data", help="Your user ID to link the session")
    full_p.add_argument("--callback", help="Redirect URL after verification")
    full_p.add_argument("--label", default="KYC Onboarding", help="Workflow display name")
    full_p.add_argument("--aml", action="store_true", help="Enable AML screening")
    full_p.add_argument("--nfc", action="store_true", help="Enable NFC chip reading")

    args = parser.parse_args()

    if args.command == "setup":
        result = setup_kyc_workflow(args.label, args.liveness, args.face_match,
                                    args.aml, args.nfc)
        print(json.dumps(result, indent=2))
        print(f"\n--- KYC Workflow Created ---")
        print(f"Workflow ID: {result.get('uuid')}")
        print(f"Type: {result.get('workflow_type')}")
        print(f"Price per session: ${result.get('total_price', '?')}")
        print(f"\nSave this workflow_id — use it when creating sessions.")

    elif args.command == "session":
        result = create_kyc_session(args.workflow_id, args.vendor_data,
                                    args.callback, args.language)
        print(json.dumps(result, indent=2))
        print(f"\n--- Session Created ---")
        print(f"Session ID: {result.get('session_id')}")
        print(f"Verification URL: {result.get('url')}")
        print(f"\nSend the URL to your user to start verification.")

    elif args.command == "decision":
        if args.poll:
            print(f"Polling session {args.session_id} every {args.interval}s...")
            result = poll_decision(args.session_id, args.interval, args.max_wait)
        else:
            result = get_decision(args.session_id)
        print(json.dumps(result, indent=2))
        status = result.get("status", "Unknown")
        print(f"\n--- Decision: {status} ---")
        if status == "Approved":
            ids = result.get("id_verifications", [])
            if ids:
                id_data = ids[0]
                print(f"Name: {id_data.get('first_name', '')} {id_data.get('last_name', '')}")
                print(f"DOB: {id_data.get('date_of_birth', '')}")
                print(f"Document: {id_data.get('document_type', '')} ({id_data.get('issuing_country', '')})")

    elif args.command == "full":
        print("Step 1: Creating KYC workflow...")
        workflow = setup_kyc_workflow(args.label, aml=args.aml, nfc=args.nfc)
        workflow_id = workflow.get("uuid")
        print(f"  Workflow ID: {workflow_id}")
        print(f"  Price per session: ${workflow.get('total_price', '?')}")

        print("\nStep 2: Creating verification session...")
        session = create_kyc_session(workflow_id, args.vendor_data, args.callback)
        print(f"  Session ID: {session.get('session_id')}")
        print(f"  Verification URL: {session.get('url')}")
        print(f"\n--- KYC Ready ---")
        print(f"Send this URL to your user: {session.get('url')}")
        print(f"Then run: python scripts/run_kyc.py decision {session.get('session_id')} --poll")


if __name__ == "__main__":
    main()
