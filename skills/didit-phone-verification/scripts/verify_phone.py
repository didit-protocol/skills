#!/usr/bin/env python3
"""Didit Phone Verification - Send and check phone OTP codes, or score phone risk without a code.

Usage:
    python scripts/verify_phone.py send <phone> [--channel whatsapp|sms|telegram|voice|rcs|viber|zalo]
                                                [--code-size <4-8>] [--locale <bcp47>] [--sms-sender-name <name>]
                                                [--white-label] [--ip <ip>] [--vendor-data <id>] [--metadata <json>]
    python scripts/verify_phone.py check <phone> <code> [--decline-disposable] [--decline-voip]
                                                       [--decline-duplicated] [--social] [--decline-no-social]
    python scripts/verify_phone.py risk <phone> [--country-code <cc>] [--social] [--ip <ip>]
                                               [--vendor-data <id>] [--metadata <json>]

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    python scripts/verify_phone.py send +14155552671
    python scripts/verify_phone.py send +14155552671 --channel sms --sms-sender-name "Example Bank"
    python scripts/verify_phone.py check +14155552671 123456
    python scripts/verify_phone.py check +14155552671 123456 --decline-voip --decline-disposable
    python scripts/verify_phone.py risk +14155552671 --country-code US
"""
import argparse
import json
import os
import sys

import requests

BASE_URL = "https://verification.didit.me/v3/phone"
CHANNELS = ["whatsapp", "sms", "telegram", "voice", "rcs", "viber", "zalo"]


def get_headers() -> dict:
    api_key = os.environ.get("DIDIT_API_KEY")
    if not api_key:
        print("Error: DIDIT_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    return {"x-api-key": api_key, "Content-Type": "application/json"}


def _post(path: str, payload: dict) -> dict:
    response = requests.post(f"{BASE_URL}/{path}/", headers=get_headers(), json=payload, timeout=60)
    if not 200 <= response.status_code < 300:
        # 429 (rate limit or 4 sends per number per hour) and 502 (provider unavailable) land here too.
        print(f"Error {response.status_code}: {response.text}", file=sys.stderr)
        sys.exit(1)
    return response.json()


def _action(decline: bool) -> str:
    return "DECLINE" if decline else "NO_ACTION"


def send_code(phone: str, channel: str = None, code_size: int = 6, locale: str = None,
              sms_sender_name: str = None, white_label: bool = False, signals: dict = None,
              vendor_data: str = None, metadata: dict = None) -> dict:
    """POST /v3/phone/send/. Returns {request_id, status, reason, vendor_data, metadata}.

    `channel` maps to options.preferred_channel; the server default is whatsapp.
    """
    options = {"code_size": code_size}
    if channel:
        options["preferred_channel"] = channel
    if locale:
        options["locale"] = locale
    if sms_sender_name:
        options["sms_sender_name"] = sms_sender_name
    if white_label:
        options["use_white_label_customization"] = True
    payload = {"phone_number": phone, "options": options}
    if signals:
        payload["signals"] = signals
    if vendor_data:
        payload["vendor_data"] = vendor_data
    if metadata is not None:
        payload["metadata"] = metadata
    return _post("send", payload)


def check_code(phone: str, code: str, decline_disposable: bool = False, decline_voip: bool = False,
               decline_duplicated: bool = False, enable_social: bool = False,
               decline_no_social: bool = False) -> dict:
    """POST /v3/phone/check/. Wrong or expired codes still return HTTP 200: read `status`."""
    payload = {
        "phone_number": phone,
        "code": code,
        "duplicated_phone_number_action": _action(decline_duplicated),
        "disposable_number_action": _action(decline_disposable),
        "voip_number_action": _action(decline_voip),
    }
    if enable_social:
        payload["enable_social"] = True
        payload["phone_no_social_presence_action"] = _action(decline_no_social)
    return _post("check", payload)


def score_phone_risk(phone: str, country_code: str = None, enable_social: bool = False,
                     signals: dict = None, vendor_data: str = None, metadata: dict = None) -> dict:
    """POST /v3/phone/risk/. Scores the number without sending a code."""
    payload = {"phone_number": phone}
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
    if getattr(args, "device_platform", None):
        signals["device_platform"] = args.device_platform
    if getattr(args, "user_agent", None):
        signals["user_agent"] = args.user_agent
    return signals


def _add_signal_args(parser):
    parser.add_argument("--ip", help="End user's IP address (signals.ip)")
    parser.add_argument("--device-id", help="End user's device id (signals.device_id)")
    parser.add_argument("--device-platform", choices=["android", "ios", "ipados", "tvos", "web"],
                        help="End user's device platform (signals.device_platform)")
    parser.add_argument("--user-agent", help="End user's user agent (signals.user_agent)")


def main():
    parser = argparse.ArgumentParser(description="Phone verification and phone risk via the Didit API")
    sub = parser.add_subparsers(dest="command", required=True)

    send_p = sub.add_parser("send", help="Send a verification code to a phone number")
    send_p.add_argument("phone", help="Phone number in E.164 format (e.g. +14155552671)")
    send_p.add_argument("--channel", choices=CHANNELS,
                        help="Preferred channel, sent as options.preferred_channel (server default: whatsapp; "
                             "falls back to SMS when unavailable)")
    send_p.add_argument("--code-size", type=int, default=6, choices=range(4, 9), metavar="4-8",
                        help="Code length 4-8 (default: 6)")
    send_p.add_argument("--locale", help="BCP-47 message language, e.g. en-US, fr, es")
    send_p.add_argument("--sms-sender-name", help="Name this code's SMS carries (1-30 characters)")
    send_p.add_argument("--white-label", action="store_true",
                        help="Without an SMS sender name, sign the SMS with your white-label public name")
    send_p.add_argument("--vendor-data", help="Your identifier for the user")
    send_p.add_argument("--metadata", help="JSON object stored with the session")
    _add_signal_args(send_p)

    check_p = sub.add_parser("check", help="Check the code the user received")
    check_p.add_argument("phone", help="Same phone number used for send (E.164)")
    check_p.add_argument("code", help="Verification code received (4-8 digits)")
    check_p.add_argument("--decline-disposable", action="store_true", help="Decline disposable numbers")
    check_p.add_argument("--decline-voip", action="store_true", help="Decline VoIP/virtual numbers")
    check_p.add_argument("--decline-duplicated", action="store_true",
                         help="Decline numbers already used by a different user")
    check_p.add_argument("--social", action="store_true", help="Add the social footprint lookup (billed add-on)")
    check_p.add_argument("--decline-no-social", action="store_true",
                         help="With --social: decline when the number is registered on no platform")

    risk_p = sub.add_parser("risk", help="Score phone risk without sending a code")
    risk_p.add_argument("phone", help="Phone number to score (E.164)")
    risk_p.add_argument("--country-code", help="ISO 3166-1 alpha-2 or alpha-3 country hint")
    risk_p.add_argument("--social", action="store_true", help="Add the social footprint lookup (billed add-on)")
    risk_p.add_argument("--vendor-data", help="Your identifier for the request")
    risk_p.add_argument("--metadata", help="JSON object stored with the session")
    _add_signal_args(risk_p)

    args = parser.parse_args()

    if args.command == "send":
        result = send_code(args.phone, args.channel, args.code_size, args.locale, args.sms_sender_name,
                           args.white_label, _signals(args), args.vendor_data, _parse_metadata(args.metadata))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"\n--- Status: {result.get('status')} | request_id: {result.get('request_id')} "
              f"| reason: {result.get('reason')} ---")
    elif args.command == "check":
        result = check_code(args.phone, args.code, args.decline_disposable, args.decline_voip,
                            args.decline_duplicated, args.social, args.decline_no_social)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"\n--- Status: {result.get('status')} | {result.get('message')} ---")
    elif args.command == "risk":
        result = score_phone_risk(args.phone, args.country_code, args.social, _signals(args),
                                  args.vendor_data, _parse_metadata(args.metadata))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        phone = result.get("phone") or {}
        carrier = phone.get("carrier") or {}
        print(f"\n--- Status: {result.get('status')} | line type: {carrier.get('type')} "
              f"| virtual: {phone.get('is_virtual')} | disposable: {phone.get('is_disposable')} ---")


if __name__ == "__main__":
    main()
