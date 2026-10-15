#!/usr/bin/env python3
"""Didit Sessions - Create verification sessions, retrieve decisions, and list sessions.

Usage:
    python scripts/create_session.py create --workflow-id UUID [--vendor-data ID] [--callback URL]
                                            [--language CODE] [--metadata JSON]
    python scripts/create_session.py get <session_id>
    python scripts/create_session.py list [--status STATUS] [--vendor-data ID] [--workflow-id UUID]
                                          [--limit N] [--offset N]

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    python scripts/create_session.py create --workflow-id d8d2fa2d-... --vendor-data user-123
    python scripts/create_session.py create --workflow-id d8d2fa2d-... --vendor-data user-123 \\
        --callback https://yourdomain.com/verified --metadata '{"plan": "pro"}'
    python scripts/create_session.py get 11111111-2222-3333-4444-555555555555
    python scripts/create_session.py list --status Approved --vendor-data user-123 --limit 20

Notes:
    - An unfinished session with the same vendor_data and workflow is returned instead of a new one.
    - `metadata` is sent as a JSON value (an object is recommended), not as a string.
"""
import argparse
import json
import os
import sys

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


def _check(r, ok_statuses):
    if r.status_code not in ok_statuses:
        print(f"Error {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)


def create_session(workflow_id: str, vendor_data: str = None, callback: str = None,
                   language: str = None, metadata=None) -> dict:
    payload = {"workflow_id": workflow_id}
    if vendor_data:
        payload["vendor_data"] = vendor_data
    if callback:
        payload["callback"] = callback
    if language:
        payload["language"] = language
    if metadata is not None:
        payload["metadata"] = metadata
    r = requests.post(f"{BASE_URL}/session/", headers=get_headers(content_type=True),
                      json=payload, timeout=30)
    _check(r, (200, 201))
    return r.json()


def get_decision(session_id: str) -> dict:
    r = requests.get(f"{BASE_URL}/session/{session_id}/decision/",
                     headers=get_headers(), timeout=30)
    _check(r, (200,))
    return r.json()


def list_sessions(status: str = None, vendor_data: str = None, workflow_id: str = None,
                  limit: int = 50, offset: int = 0) -> dict:
    params = {"limit": limit, "offset": offset}
    if status:
        params["status"] = status
    if vendor_data:
        params["vendor_data"] = vendor_data
    if workflow_id:
        params["workflow_id"] = workflow_id
    r = requests.get(f"{BASE_URL}/sessions/", headers=get_headers(),
                     params=params, timeout=30)
    _check(r, (200,))
    return r.json()


def main():
    parser = argparse.ArgumentParser(description="Manage Didit verification sessions")
    sub = parser.add_subparsers(dest="command", required=True)

    create_p = sub.add_parser("create", help="Create a new verification session")
    create_p.add_argument("--workflow-id", required=True, help="Workflow version UUID")
    create_p.add_argument("--vendor-data", help="Your user identifier")
    create_p.add_argument("--callback", help="Redirect URL after verification")
    create_p.add_argument("--language", help="UI language code, e.g. en, es, pt-BR")
    create_p.add_argument("--metadata", help="Custom metadata as JSON, e.g. '{\"plan\": \"pro\"}'")

    get_p = sub.add_parser("get", help="Get a session decision")
    get_p.add_argument("session_id", help="Session UUID")

    list_p = sub.add_parser("list", help="List sessions (newest first)")
    list_p.add_argument("--status", help="Filter by status, e.g. Approved, Declined, 'In Review'")
    list_p.add_argument("--vendor-data", help="Filter by vendor_data (exact match)")
    list_p.add_argument("--workflow-id", help="Filter by workflow UUID")
    list_p.add_argument("--limit", type=int, default=50, help="Page size (default 50)")
    list_p.add_argument("--offset", type=int, default=0, help="Rows to skip (default 0)")

    args = parser.parse_args()

    if args.command == "create":
        metadata = None
        if args.metadata:
            try:
                metadata = json.loads(args.metadata)
            except json.JSONDecodeError as e:
                print(f"Invalid --metadata JSON: {e}", file=sys.stderr)
                sys.exit(1)
        result = create_session(args.workflow_id, args.vendor_data, args.callback,
                                args.language, metadata)
        print(json.dumps(result, indent=2))
        print(f"\n--- Session {result.get('session_id')} (#{result.get('session_number')}) "
              f"status {result.get('status')}: send the user to {result.get('url')} ---")

    elif args.command == "get":
        result = get_decision(args.session_id)
        print(json.dumps(result, indent=2))
        print(f"\n--- Session {result.get('session_id')} status: {result.get('status')} ---")

    elif args.command == "list":
        result = list_sessions(args.status, args.vendor_data, args.workflow_id, args.limit, args.offset)
        print(json.dumps(result, indent=2))
        print(f"\n--- {len(result.get('results', []))} session(s) on this page, count {result.get('count')} ---")


if __name__ == "__main__":
    main()
