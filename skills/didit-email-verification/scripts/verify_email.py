#!/usr/bin/env python3
"""Didit Email Verification - Send and check email OTP codes.

Usage:
    python scripts/verify_email.py send <email> [--code-size <4-8>] [--alphanumeric]
    python scripts/verify_email.py check <email> <code> [--decline-breached] [--decline-disposable]

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    python scripts/verify_email.py send user@example.com
    python scripts/verify_email.py check user@example.com 123456
    python scripts/verify_email.py check user@example.com 123456 --decline-breached --decline-disposable
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


def send_code(email: str, code_size: int = 6, alphanumeric: bool = False, vendor_data: str = None) -> dict:
    payload = {
        "email": email,
        "options": {"code_size": code_size, "alphanumeric_code": alphanumeric},
    }
    if vendor_data:
        payload["vendor_data"] = vendor_data

    response = requests.post(f"{BASE_URL}/send/", headers=get_headers(), json=payload, timeout=30)

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}", file=sys.stderr)
        sys.exit(1)

    return response.json()


def check_code(email: str, code: str, decline_breached: bool = False, decline_disposable: bool = False) -> dict:
    payload = {
        "email": email,
        "code": code,
        "breached_email_action": "DECLINE" if decline_breached else "NO_ACTION",
        "disposable_email_action": "DECLINE" if decline_disposable else "NO_ACTION",
    }

    response = requests.post(f"{BASE_URL}/check/", headers=get_headers(), json=payload, timeout=30)

    if response.status_code not in (200, 404):
        print(f"Error {response.status_code}: {response.text}", file=sys.stderr)
        sys.exit(1)

    return response.json()


def main():
    parser = argparse.ArgumentParser(description="Email verification via Didit API")
    sub = parser.add_subparsers(dest="command", required=True)

    send_p = sub.add_parser("send", help="Send verification code to email")
    send_p.add_argument("email", help="Email address to verify")
    send_p.add_argument("--code-size", type=int, default=6, help="Code length 4-8 (default: 6)")
    send_p.add_argument("--alphanumeric", action="store_true", help="Use alphanumeric code")
    send_p.add_argument("--vendor-data", help="Unique identifier for session tracking")

    check_p = sub.add_parser("check", help="Check verification code")
    check_p.add_argument("email", help="Email address to verify")
    check_p.add_argument("code", help="Verification code received")
    check_p.add_argument("--decline-breached", action="store_true", help="Decline breached emails")
    check_p.add_argument("--decline-disposable", action="store_true", help="Decline disposable emails")

    args = parser.parse_args()

    if args.command == "send":
        result = send_code(args.email, args.code_size, args.alphanumeric, args.vendor_data)
        print(json.dumps(result, indent=2))
        print(f"\n--- Status: {result.get('status', 'Unknown')} ---")
    elif args.command == "check":
        result = check_code(args.email, args.code, args.decline_breached, args.decline_disposable)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"\n--- Status: {result.get('status', 'Unknown')} ---")


if __name__ == "__main__":
    main()
