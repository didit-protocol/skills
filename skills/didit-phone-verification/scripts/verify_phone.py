#!/usr/bin/env python3
"""Didit Phone Verification - Send and check phone OTP codes.

Usage:
    python scripts/verify_phone.py send <phone> [--channel sms|whatsapp|telegram|voice] [--code-size <4-8>]
    python scripts/verify_phone.py check <phone> <code> [--decline-disposable] [--decline-voip]

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    python scripts/verify_phone.py send +14155552671
    python scripts/verify_phone.py send +14155552671 --channel sms
    python scripts/verify_phone.py check +14155552671 123456
    python scripts/verify_phone.py check +14155552671 123456 --decline-voip
"""
import argparse
import json
import os
import sys

import requests

BASE_URL = "https://verification.didit.me/v3/phone"


def get_headers() -> dict:
    api_key = os.environ.get("DIDIT_API_KEY")
    if not api_key:
        print("Error: DIDIT_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    return {"x-api-key": api_key, "Content-Type": "application/json"}


def send_code(phone: str, channel: str = "whatsapp", code_size: int = 6, vendor_data: str = None) -> dict:
    payload = {
        "phone_number": phone,
        "options": {"preferred_channel": channel, "code_size": code_size},
    }
    if vendor_data:
        payload["vendor_data"] = vendor_data

    response = requests.post(f"{BASE_URL}/send/", headers=get_headers(), json=payload, timeout=30)

    if response.status_code not in (200, 429):
        print(f"Error {response.status_code}: {response.text}", file=sys.stderr)
        sys.exit(1)

    return response.json()


def check_code(phone: str, code: str, decline_disposable: bool = False, decline_voip: bool = False) -> dict:
    payload = {
        "phone_number": phone,
        "code": code,
        "disposable_number_action": "DECLINE" if decline_disposable else "NO_ACTION",
        "voip_number_action": "DECLINE" if decline_voip else "NO_ACTION",
    }

    response = requests.post(f"{BASE_URL}/check/", headers=get_headers(), json=payload, timeout=30)

    if response.status_code not in (200, 404):
        print(f"Error {response.status_code}: {response.text}", file=sys.stderr)
        sys.exit(1)

    return response.json()


def main():
    parser = argparse.ArgumentParser(description="Phone verification via Didit API")
    sub = parser.add_subparsers(dest="command", required=True)

    send_p = sub.add_parser("send", help="Send verification code to phone")
    send_p.add_argument("phone", help="Phone number in E.164 format (e.g. +14155552671)")
    send_p.add_argument("--channel", default="whatsapp", choices=["sms", "whatsapp", "telegram", "voice"], help="Delivery channel (default: whatsapp)")
    send_p.add_argument("--code-size", type=int, default=6, help="Code length 4-8 (default: 6)")
    send_p.add_argument("--vendor-data", help="Unique identifier for session tracking")

    check_p = sub.add_parser("check", help="Check verification code")
    check_p.add_argument("phone", help="Phone number in E.164 format")
    check_p.add_argument("code", help="Verification code received")
    check_p.add_argument("--decline-disposable", action="store_true", help="Decline disposable numbers")
    check_p.add_argument("--decline-voip", action="store_true", help="Decline VoIP numbers")

    args = parser.parse_args()

    if args.command == "send":
        result = send_code(args.phone, args.channel, args.code_size, args.vendor_data)
        print(json.dumps(result, indent=2))
        print(f"\n--- Status: {result.get('status', 'Unknown')} ---")
    elif args.command == "check":
        result = check_code(args.phone, args.code, args.decline_disposable, args.decline_voip)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"\n--- Status: {result.get('status', 'Unknown')} ---")


if __name__ == "__main__":
    main()
