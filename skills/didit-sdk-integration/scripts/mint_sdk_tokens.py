#!/usr/bin/env python3
"""Didit SDK Integration - Create the client-side credentials a Didit SDK needs.

Run this on your backend. It uses the API key to create a verification session
(for startVerification), mint a transaction SDK token (for submitTransaction)
and/or mint a monitoring token (for device events), then prints only the
client-safe values. The API key is never printed.

Usage:
    python scripts/mint_sdk_tokens.py --vendor-data <user_id> [--workflow-id <uuid>] \
        [--transaction-token] [--monitoring-token]

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    # Session for the Web SDK (url) or a native SDK (session_token)
    python scripts/mint_sdk_tokens.py --vendor-data user-42 \
        --workflow-id 11111111-2222-3333-4444-555555555555

    # Session with a callback that both devices may follow
    python scripts/mint_sdk_tokens.py --vendor-data user-42 \
        --workflow-id 11111111-2222-3333-4444-555555555555 \
        --callback https://yourapp.example.com/verification-done --callback-method both

    # Transaction token for submitTransaction: 15 minutes, 3 submissions
    python scripts/mint_sdk_tokens.py --vendor-data user-42 --transaction-token \
        --ttl-seconds 900 --max-uses 3

    # Monitoring token for device events, limited to auth and session events
    python scripts/mint_sdk_tokens.py --vendor-data user-42 --monitoring-token \
        --event-categories auth,session --bind-to-origin https://app.example.com
"""
import argparse
import json
import os
import sys

import requests

BASE_URL = "https://verification.didit.me"
EVENT_CATEGORIES = (
    "auth", "session", "gameplay", "bonus", "affiliate",
    "payment", "dispute", "security", "responsible_gambling", "custom",
)


def get_api_key() -> str:
    api_key = os.environ.get("DIDIT_API_KEY")
    if not api_key:
        print("Error: DIDIT_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    return api_key


def post(path: str, payload: dict, api_key: str) -> dict:
    response = requests.post(
        f"{BASE_URL}{path}",
        headers={"x-api-key": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    if not response.ok:
        print(f"Error: POST {path} returned {response.status_code}", file=sys.stderr)
        print(response.text, file=sys.stderr)
        sys.exit(1)
    return response.json() if response.content else {}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a Didit session and/or mint transaction and monitoring SDK tokens (backend only)."
    )
    parser.add_argument("--vendor-data", required=True, help="Your internal id for the end user")
    parser.add_argument("--workflow-id", help="Create a verification session for this workflow")
    parser.add_argument("--callback", help="Session callback URL (Didit appends verificationSessionId and status)")
    parser.add_argument("--callback-method", choices=["initiator", "completer", "both"],
                        help="Which device follows the callback (default: initiator)")
    parser.add_argument("--language", help="Session UI language, ISO 639-1 (e.g. es)")
    parser.add_argument("--transaction-token", action="store_true",
                        help="Mint a transaction SDK token (POST /v3/transactions/sdk-token/)")
    parser.add_argument("--monitoring-token", action="store_true",
                        help="Mint a monitoring token for device events (POST /v3/events/sdk-token/)")
    parser.add_argument("--ttl-seconds", type=int, default=900,
                        help="Token lifetime in seconds, 60 to 86400 (default: 900)")
    parser.add_argument("--max-uses", type=int,
                        help="Token use limit, >= 1 (default: unlimited for transaction tokens, 1000 for monitoring tokens)")
    parser.add_argument("--event-categories",
                        help="Comma-separated categories the monitoring token may write: " + ", ".join(EVENT_CATEGORIES))
    parser.add_argument("--bind-to-origin", help="Browser Origin the monitoring token is bound to")
    args = parser.parse_args()

    if not (args.workflow_id or args.transaction_token or args.monitoring_token):
        parser.error("choose at least one of --workflow-id, --transaction-token, --monitoring-token")
    if not 60 <= args.ttl_seconds <= 86400:
        parser.error("--ttl-seconds must be between 60 and 86400")
    if args.max_uses is not None and args.max_uses < 1:
        parser.error("--max-uses must be 1 or more")
    categories = None
    if args.event_categories:
        categories = [c.strip() for c in args.event_categories.split(",") if c.strip()]
        unknown = [c for c in categories if c not in EVENT_CATEGORIES]
        if unknown:
            parser.error(f"unknown event categories: {', '.join(unknown)}")

    api_key = get_api_key()
    output = {}
    summary = []

    if args.workflow_id:
        payload = {"workflow_id": args.workflow_id, "vendor_data": args.vendor_data}
        if args.callback:
            payload["callback"] = args.callback
        if args.callback_method:
            payload["callback_method"] = args.callback_method
        if args.language:
            payload["language"] = args.language
        body = post("/v3/session/", payload, api_key)
        output["session"] = {key: body.get(key) for key in ("session_id", "session_token", "url", "status")}
        summary.append(f"session {body.get('session_id')} ({body.get('status')})")
        if body.get("url") is None or body.get("session_token") is None:
            print("Note: url and session_token are null: this API key needs Sessions write.", file=sys.stderr)

    if args.transaction_token:
        payload = {"vendor_data": args.vendor_data, "ttl_seconds": args.ttl_seconds}
        if args.max_uses is not None:
            payload["max_uses"] = args.max_uses
        body = post("/v3/transactions/sdk-token/", payload, api_key)
        output["transaction_token"] = {key: body.get(key) for key in ("sdk_token", "expires_at")}
        summary.append(f"transaction token until {body.get('expires_at')}")

    if args.monitoring_token:
        payload = {"vendor_data": args.vendor_data, "ttl_seconds": args.ttl_seconds}
        if args.max_uses is not None:
            payload["max_uses"] = args.max_uses
        if categories:
            payload["allowed_event_categories"] = categories
        if args.bind_to_origin:
            payload["bind_to_origin"] = args.bind_to_origin
        body = post("/v3/events/sdk-token/", payload, api_key)
        output["monitoring_token"] = {
            key: body.get(key)
            for key in ("monitoring_token", "expires_at", "allowed_event_categories", "max_uses", "bind_to_origin")
        }
        summary.append(f"monitoring token until {body.get('expires_at')}")

    print(json.dumps(output, indent=2))
    print("\nSummary: " + "; ".join(summary), file=sys.stderr)


if __name__ == "__main__":
    main()
