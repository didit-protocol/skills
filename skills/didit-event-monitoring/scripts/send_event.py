#!/usr/bin/env python3
"""Didit Event Monitoring - Send one monitoring event, or mint a device monitoring token.

Usage:
    python scripts/send_event.py send --event-id ID --category CATEGORY --action-type ACTION \
        --vendor-data USER [--occurred-at ISO] [--payload JSON] [--ip IP] [--fingerprint FP] ...
    python scripts/send_event.py token --vendor-data USER [--categories auth,session] \
        [--ttl 900] [--max-uses 1000] [--bind-to-origin https://app.example.com]

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    # A failed login (server lane, POST /v3/events/)
    python scripts/send_event.py send --event-id login-0001 --category security \
        --action-type login_failed --vendor-data user_391 --ip 203.0.113.42 \
        --fingerprint didit-fp-v2:a8c1

    # A completed deposit (payment events need payment_reference_id, amount, currency,
    # payment_method and status)
    python scripts/send_event.py send --event-id dep-735-completed --category payment \
        --action-type deposit_completed --vendor-data user_391 --amount 1000.00 --currency EUR \
        --payment-reference-id dep_735 --payload '{"payment_method": "card", "status": "completed"}'

    # Mint a device token (POST /v3/events/sdk-token/); the device then posts to
    # https://verification.didit.me/v1/events/ with the X-Monitoring-Token header
    python scripts/send_event.py token --vendor-data user_391 --categories auth,session,gameplay

Notes:
    - Event monitoring must be on (Business Console: Transactions > Settings > Event
      monitoring), otherwise writes return 403 with "code": "event_monitoring_disabled".
    - event_id is the idempotency key: the same id with the same content returns 200 and
      the stored event; the same id with different content returns 409.
    - occurred_at must be within the last 7 days and at most 5 minutes in the future.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

import requests

BASE_URL = "https://verification.didit.me/v3/events"
CATEGORIES = [
    "auth",
    "session",
    "gameplay",
    "bonus",
    "affiliate",
    "payment",
    "dispute",
    "security",
    "responsible_gambling",
    "custom",
]


def get_headers() -> dict:
    api_key = os.environ.get("DIDIT_API_KEY")
    if not api_key:
        print("Error: DIDIT_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    return {"x-api-key": api_key, "Content-Type": "application/json"}


def parse_json_object(value: str, flag: str) -> dict:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        print(f"Error: {flag} is not valid JSON: {exc}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(parsed, dict):
        print(f"Error: {flag} must be a JSON object.", file=sys.stderr)
        sys.exit(1)
    return parsed


def post(url: str, payload: dict, ok_statuses: tuple) -> dict:
    r = requests.post(url, headers=get_headers(), json=payload, timeout=30)
    if r.status_code not in ok_statuses:
        print(f"Error {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)
    return r.json()


def build_event(args: argparse.Namespace) -> dict:
    event = {
        "event_id": args.event_id,
        "event_category": args.category,
        "action_type": args.action_type,
        "occurred_at": args.occurred_at or datetime.now(timezone.utc).isoformat(),
        "subject": {"vendor_data": args.vendor_data, "entity_type": args.entity_type},
    }
    if args.time_zone:
        event["time_zone"] = args.time_zone
    if args.session_id:
        event["session"] = {"session_id": args.session_id}
    device_context = {}
    if args.fingerprint:
        device_context["fingerprint"] = args.fingerprint
    if args.ip:
        device_context["network_context"] = {"ip_address": args.ip}
    if device_context:
        event["device_context"] = device_context
    transaction_context = {
        key: value
        for key, value in (
            ("amount", args.amount),
            ("currency", args.currency),
            ("payment_reference_id", args.payment_reference_id),
        )
        if value
    }
    if transaction_context:
        event["transaction_context"] = transaction_context
    if args.payload:
        event["payload"] = parse_json_object(args.payload, "--payload")
    if args.custom_values:
        event["custom_values"] = parse_json_object(args.custom_values, "--custom-values")
    return event


def cmd_send(args: argparse.Namespace) -> None:
    body = post(f"{BASE_URL}/", build_event(args), (200, 201))
    print(json.dumps(body, indent=2))
    print(
        f"\n--- event_uuid: {body.get('event_uuid')} | status: {body.get('status')} | score: {body.get('score')}"
        f" | rules matched: {body.get('rules_matched_count')}/{body.get('rules_evaluated_count')}"
        f" | replay: {body.get('idempotent_replay')} | correlation_pending: {body.get('correlation_pending')} ---"
    )


def cmd_token(args: argparse.Namespace) -> None:
    payload = {"vendor_data": args.vendor_data, "entity_type": args.entity_type, "ttl_seconds": args.ttl}
    if args.categories:
        payload["allowed_event_categories"] = [c.strip() for c in args.categories.split(",") if c.strip()]
    if args.max_uses is not None:
        payload["max_uses"] = args.max_uses
    if args.bind_to_origin:
        payload["bind_to_origin"] = args.bind_to_origin
    body = post(f"{BASE_URL}/sdk-token/", payload, (201,))
    print(json.dumps(body, indent=2))
    categories = ", ".join(body.get("allowed_event_categories") or []) or "all"
    print(
        f"\n--- token expires_at: {body.get('expires_at')} | categories: {categories}"
        f" | max_uses: {body.get('max_uses')} | bind_to_origin: {body.get('bind_to_origin')} ---"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Send Didit monitoring events or mint a device token.")
    sub = parser.add_subparsers(dest="command", required=True)

    send = sub.add_parser("send", help="Send one event to POST /v3/events/")
    send.add_argument("--event-id", required=True, help="Your unique event id (max 128 chars, idempotency key)")
    send.add_argument("--category", required=True, choices=CATEGORIES, help="event_category")
    send.add_argument("--action-type", required=True, help="e.g. login, login_failed, bet_placed, chargeback_opened")
    send.add_argument("--vendor-data", required=True, help="Your user id (subject.vendor_data)")
    send.add_argument("--entity-type", default="individual", choices=["individual", "company"])
    send.add_argument("--occurred-at", help="ISO 8601 timestamp (default: now, UTC)")
    send.add_argument("--time-zone", help="e.g. UTC or Europe/Madrid")
    send.add_argument("--session-id", help="session.session_id")
    send.add_argument("--fingerprint", help="device_context.fingerprint")
    send.add_argument("--ip", help="device_context.network_context.ip_address")
    send.add_argument("--amount", help="transaction_context.amount")
    send.add_argument("--currency", help="transaction_context.currency")
    send.add_argument("--payment-reference-id", help="transaction_context.payment_reference_id")
    send.add_argument("--payload", help="payload as a JSON object (max 16 KB)")
    send.add_argument("--custom-values", help="custom_values as a JSON object of scalars (max 100 keys)")
    send.set_defaults(func=cmd_send)

    token = sub.add_parser("token", help="Mint a device token with POST /v3/events/sdk-token/")
    token.add_argument("--vendor-data", required=True, help="Subject every event sent with the token belongs to")
    token.add_argument("--entity-type", default="individual", choices=["individual", "company"])
    token.add_argument("--categories", help="Comma-separated allowed_event_categories (default: all)")
    token.add_argument("--ttl", type=int, default=900, help="ttl_seconds, 60-86400 (default: 900)")
    token.add_argument("--max-uses", type=int, help="max_uses, one use per event (server default: 1000)")
    token.add_argument("--bind-to-origin", help="Exact browser Origin the token is valid from")
    token.set_defaults(func=cmd_token)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
