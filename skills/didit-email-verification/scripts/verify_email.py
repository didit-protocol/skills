#!/usr/bin/env python3
"""Didit Email Verification - Send and check email OTP codes, or score email risk without a code.

Usage:
    python scripts/verify_email.py send <email> [--code-size <4-8>] [--alphanumeric] [--locale <code>]
                                                [--white-label] [--ip <ip>] [--vendor-data <id>] [--metadata <json>]
    python scripts/verify_email.py check <email> <code> [--decline-breached] [--decline-disposable]
                                                       [--decline-duplicated] [--social] [--decline-no-social]
    python scripts/verify_email.py risk <email> [--country-code <cc>] [--social] [--ip <ip>]
                                               [--vendor-data <id>] [--metadata <json>]

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    python scripts/verify_email.py send user@example.com
    python scripts/verify_email.py send user@example.com --locale es --alphanumeric --code-size 8
    python scripts/verify_email.py check user@example.com 123456
    python scripts/verify_email.py check user@example.com 123456 --decline-breached --decline-disposable
    python scripts/verify_email.py risk user@example.com --country-code US --vendor-data lead-123
"""
import argparse
import json
import os
import sys

import requests

BASE_URL = "https://verification.didit.me/v3/email"


def get_headers() -> dict:
    api_key = os.environ.get("DIDIT_API_KEY")
    if not api_key:
        print("Error: DIDIT_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    return {"x-api-key": api_key, "Content-Type": "application/json"}


def _post(path: str, payload: dict) -> dict:
    response = requests.post(f"{BASE_URL}/{path}/", headers=get_headers(), json=payload, timeout=60)
    if not 200 <= response.status_code < 300:
        print(f"Error {response.status_code}: {response.text}", file=sys.stderr)
        sys.exit(1)
    return response.json()


def _action(decline: bool) -> str:
    return "DECLINE" if decline else "NO_ACTION"


def send_code(email: str, code_size: int = 6, alphanumeric: bool = False, locale: str = None,
              white_label: bool = False, signals: dict = None, vendor_data: str = None,
              metadata: dict = None) -> dict:
    """POST /v3/email/send/. Returns {request_id, status, reason, vendor_data, metadata}."""
    options = {"code_size": code_size, "alphanumeric_code": alphanumeric}
    if locale:
        options["locale"] = locale
    if white_label:
        options["use_white_label_customization"] = True
    payload = {"email": email, "options": options}
    if signals:
        payload["signals"] = signals
    if vendor_data:
        payload["vendor_data"] = vendor_data
    if metadata is not None:
        payload["metadata"] = metadata
    return _post("send", payload)


def check_code(email: str, code: str, decline_breached: bool = False, decline_disposable: bool = False,
               decline_duplicated: bool = False, enable_social: bool = False,
               decline_no_social: bool = False) -> dict:
    """POST /v3/email/check/. Wrong or expired codes still return HTTP 200: read `status`."""
    payload = {
        "email": email,
        "code": code,
        "duplicated_email_action": _action(decline_duplicated),
        "breached_email_action": _action(decline_breached),
        "disposable_email_action": _action(decline_disposable),
    }
    if enable_social:
        payload["enable_social"] = True
        payload["email_no_social_presence_action"] = _action(decline_no_social)
    return _post("check", payload)


def score_email_risk(email: str, country_code: str = None, enable_social: bool = False,
                     signals: dict = None, vendor_data: str = None, metadata: dict = None) -> dict:
    """POST /v3/email/risk/. Scores the address without sending a code."""
    payload = {"email": email}
    if country_code:
        payload["country_code"] = country_code
    if enable_social:
        payload["enable_social"] = True
    if signals:
        payload["signals"] = signals
    if vendor_data:
        payload["vendor_data"] = vendor_data
    if metadata is not None:
        payload["metadata"] = metadata
    return _post("risk", payload)


def _parse_metadata(raw: str):
    if raw is None:
        return None
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        print(f"Error: --metadata is not valid JSON ({error}).", file=sys.stderr)
        sys.exit(1)
    if not isinstance(value, dict):
        print("Error: --metadata must be a JSON object.", file=sys.stderr)
        sys.exit(1)
    return value


def _signals(args) -> dict:
    signals = {}
    if getattr(args, "ip", None):
        signals["ip"] = args.ip
    if getattr(args, "device_id", None):
        signals["device_id"] = args.device_id
    if getattr(args, "user_agent", None):
        signals["user_agent"] = args.user_agent
    return signals


def _add_signal_args(parser):
    parser.add_argument("--ip", help="End user's IP address (signals.ip)")
    parser.add_argument("--device-id", help="End user's device id (signals.device_id)")
    parser.add_argument("--user-agent", help="End user's user agent (signals.user_agent)")


def main():
    parser = argparse.ArgumentParser(description="Email verification and email risk via the Didit API")
    sub = parser.add_subparsers(dest="command", required=True)

    send_p = sub.add_parser("send", help="Send a verification code to an email address")
    send_p.add_argument("email", help="Email address to verify")
    send_p.add_argument("--code-size", type=int, default=6, choices=range(4, 9), metavar="4-8",
                        help="Code length 4-8 (default: 6)")
    send_p.add_argument("--alphanumeric", action="store_true", help="Uppercase letters and digits instead of digits")
    send_p.add_argument("--locale", help="Template language, e.g. en, es, pt-BR, zh-CN (default: en)")
    send_p.add_argument("--white-label", action="store_true",
                        help="Use your application's white-label branding (options.use_white_label_customization)")
    send_p.add_argument("--vendor-data", help="Your identifier for the user")
    send_p.add_argument("--metadata", help="JSON object stored with the session")
    _add_signal_args(send_p)

    check_p = sub.add_parser("check", help="Check the code the user received")
    check_p.add_argument("email", help="Same email address used for send")
    check_p.add_argument("code", help="Verification code received")
    check_p.add_argument("--decline-breached", action="store_true", help="Decline breached emails")
    check_p.add_argument("--decline-disposable", action="store_true", help="Decline disposable emails")
    check_p.add_argument("--decline-duplicated", action="store_true",
                         help="Decline emails already approved for a different user")
    check_p.add_argument("--social", action="store_true", help="Add the social footprint lookup (billed add-on)")
    check_p.add_argument("--decline-no-social", action="store_true",
                         help="With --social: decline when the address is registered on no platform")

    risk_p = sub.add_parser("risk", help="Score email risk without sending a code")
    risk_p.add_argument("email", help="Email address to score")
    risk_p.add_argument("--country-code", help="ISO 3166-1 alpha-2 or alpha-3 country hint")
    risk_p.add_argument("--social", action="store_true", help="Add the social footprint lookup (billed add-on)")
    risk_p.add_argument("--vendor-data", help="Your identifier for the request")
    risk_p.add_argument("--metadata", help="JSON object stored with the session")
    _add_signal_args(risk_p)

    args = parser.parse_args()

    if args.command == "send":
        result = send_code(args.email, args.code_size, args.alphanumeric, args.locale, args.white_label,
                           _signals(args), args.vendor_data, _parse_metadata(args.metadata))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"\n--- Status: {result.get('status')} | request_id: {result.get('request_id')} "
              f"| reason: {result.get('reason')} ---")
    elif args.command == "check":
        result = check_code(args.email, args.code, args.decline_breached, args.decline_disposable,
                            args.decline_duplicated, args.social, args.decline_no_social)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"\n--- Status: {result.get('status')} | {result.get('message')} ---")
    elif args.command == "risk":
        result = score_email_risk(args.email, args.country_code, args.social, _signals(args),
                                  args.vendor_data, _parse_metadata(args.metadata))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        email = result.get("email") or {}
        print(f"\n--- Status: {result.get('status')} | breached: {email.get('is_breached')} "
              f"| disposable: {email.get('is_disposable')} | undeliverable: {email.get('is_undeliverable')} ---")


if __name__ == "__main__":
    main()
