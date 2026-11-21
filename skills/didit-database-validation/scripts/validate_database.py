#!/usr/bin/env python3
"""Didit Database Validation - Validate identity data against government databases.

--issuing-state is ISO 3166-1 alpha-3 (PER, BRA, ARG, ...); alpha-2 returns 400.
Send the number field the country needs (see the country table in SKILL.md):
  --document-number  ARG, BOL, GTM, HND, PRY, SLV, VEN
  --personal-number  CHL, COL, CRI, DOM, ECU, MEX, PAN, PER, URY
  --tax-number       BRA (CPF)
or use --identification-number, which the API maps to the right field for those
17 countries. A missing or wrongly named field returns 400 "Missing required fields"
(never billed). Without --services exactly one default service runs; ESP, KEN, ZMB
and most non-Latin-American countries have no default, so pass --services.
--selfie switches the request to multipart/form-data (biometric services such as
arg_renaper and pan_cedula_sib).

Usage:
    python scripts/validate_database.py --issuing-state PER --personal-number 12345678
    python scripts/validate_database.py --issuing-state BRA --tax-number 12345678900 --dob 1980-01-01 --services bra_cpf

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    python scripts/validate_database.py --issuing-state PER --personal-number 12345678 --first-name Carlos --last-name Garcia
    python scripts/validate_database.py --issuing-state MEX --identification-number GARC850315HDFRRL09
    python scripts/validate_database.py --issuing-state COL --personal-number 1234567890 --date-of-issue 2015-06-20
    python scripts/validate_database.py --issuing-state ARG --document-number 12345678 --gender F --selfie selfie.jpg
    python scripts/validate_database.py --issuing-state ARG --services arg_renaper_data --document-number 12345678 --gender M
    python scripts/validate_database.py --issuing-state ESP --services esp_dni --consent --first-name John --last-name Doe \\
        --dob 1990-01-01 --address '{"street_1": "Calle Mayor 10", "city": "Madrid", "postal_code": "28013", "country": "ES"}'
"""
import argparse
import json
import mimetypes
import os
import re
import sys

import requests

ENDPOINT = "https://verification.didit.me/v3/database-validation/"
ACTIONS = ("DECLINE", "NO_ACTION")


def get_api_key() -> str:
    api_key = os.environ.get("DIDIT_API_KEY")
    if not api_key:
        print("Error: DIDIT_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    return api_key


def parse_address(value: str):
    """Accept a JSON object ({"street_1": ..., "postal_code": ...}) or one complete address line."""
    text = value.strip()
    if text.startswith("{"):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            raise argparse.ArgumentTypeError("--address JSON is not valid")
        if not isinstance(parsed, dict):
            raise argparse.ArgumentTypeError("--address JSON must be an object")
        return parsed
    return text


def validate_database(payload: dict, selfie_path: str = None) -> dict:
    api_key = get_api_key()
    headers = {"x-api-key": api_key}
    if selfie_path:
        # multipart/form-data: lists go as repeated fields, objects as JSON strings
        data = []
        for key, value in payload.items():
            if isinstance(value, list):
                data.extend((key, item) for item in value)
            elif isinstance(value, dict):
                data.append((key, json.dumps(value)))
            elif isinstance(value, bool):
                data.append((key, "true" if value else "false"))
            else:
                data.append((key, str(value)))
        mime = mimetypes.guess_type(selfie_path)[0] or "image/jpeg"
        with open(selfie_path, "rb") as f:
            files = {"selfie": (os.path.basename(selfie_path), f, mime)}
            r = requests.post(ENDPOINT, headers=headers, data=data, files=files, timeout=90)
    else:
        r = requests.post(ENDPOINT, headers=headers, json=payload, timeout=90)
    if r.status_code != 200:
        print(f"Error {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)
    return r.json()


def main():
    parser = argparse.ArgumentParser(
        description="Validate identity data against government databases via Didit (POST /v3/database-validation/)")
    parser.add_argument("--issuing-state", required=True,
                        help="Registry country, ISO 3166-1 alpha-3 (e.g. PER, BRA, ARG, ESP)")
    parser.add_argument("--services",
                        help="Comma-separated service_ids, e.g. bra_cpf or esp_dni (default: the country's one default service)")
    parser.add_argument("--identification-number",
                        help="Universal number, mapped to the country's field (ARG..VEN, see SKILL.md)")
    parser.add_argument("--document-number", help="Number field for ARG, BOL, GTM, HND, PRY, SLV, VEN")
    parser.add_argument("--personal-number", help="Number field for CHL, COL, CRI, DOM, ECU, MEX, PAN, PER, URY")
    parser.add_argument("--tax-number", help="Number field for BRA (CPF, 11 digits)")
    parser.add_argument("--national-id", help="National ID for KEN, ZMB, ZAF and other services (optional for esp_dni)")
    parser.add_argument("--first-name", help="First name")
    parser.add_argument("--last-name", help="Last name")
    parser.add_argument("--dob", help="Date of birth, YYYY-MM-DD (date_of_birth)")
    parser.add_argument("--date-of-issue", help="Document issue date, YYYY-MM-DD (required by col_cedula)")
    parser.add_argument("--expiration-date", help="Document expiry date, YYYY-MM-DD")
    parser.add_argument("--gender", choices=("M", "F", "X"), help="Gender (required by arg_renaper, arg_renaper_data)")
    parser.add_argument("--nationality", help="Nationality, ISO alpha-3 (required by col_migracion)")
    parser.add_argument("--address", type=parse_address,
                        help='Address as JSON {"street_1","street_2","city","region","postal_code","country"} or one line')
    parser.add_argument("--selfie", help="Selfie image (jpg/jpeg/png/webp, max 2 MB); sends multipart/form-data")
    parser.add_argument("--consent", action="store_true",
                        help="Send consent=true (required by services with requires_consent, e.g. esp_dni)")
    parser.add_argument("--partial-match-action", choices=ACTIONS, help="Default NO_ACTION (partial match stays Approved)")
    parser.add_argument("--no-match-action", choices=ACTIONS, help="Default DECLINE")
    parser.add_argument("--vendor-data", help="Your identifier for tracking (vendor_data)")
    parser.add_argument("--no-save", action="store_true",
                        help="Send save_api_request=false (nothing stored; validations becomes a merged map)")
    args = parser.parse_args()

    issuing_state = args.issuing_state.strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", issuing_state):
        parser.error("--issuing-state must be an ISO 3166-1 alpha-3 code, e.g. PER, BRA, ARG")
    if args.selfie:
        if not os.path.isfile(args.selfie):
            parser.error(f"selfie not found: {args.selfie}")
        if os.path.splitext(args.selfie)[1].lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            parser.error("--selfie must be .jpg, .jpeg, .png or .webp")
        if os.path.getsize(args.selfie) > 2 * 1024 * 1024:
            parser.error("--selfie is larger than 2 MB")

    payload = {"issuing_state": issuing_state}
    if args.services:
        payload["services"] = [s.strip() for s in args.services.split(",") if s.strip()]
    optional = {
        "identification_number": args.identification_number,
        "document_number": args.document_number,
        "personal_number": args.personal_number,
        "tax_number": args.tax_number,
        "national_id": args.national_id,
        "first_name": args.first_name,
        "last_name": args.last_name,
        "date_of_birth": args.dob,
        "date_of_issue": args.date_of_issue,
        "expiration_date": args.expiration_date,
        "gender": args.gender,
        "nationality": args.nationality,
        "address": args.address,
        "partial_match_action": args.partial_match_action,
        "no_match_action": args.no_match_action,
        "vendor_data": args.vendor_data,
    }
    payload.update({key: value for key, value in optional.items() if value})
    if args.consent:
        payload["consent"] = True
    if args.no_save:
        payload["save_api_request"] = False

    result = validate_database(payload, args.selfie)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    db_val = result.get("database_validation") or {}
    print(f"\n--- Status: {db_val.get('status', 'Unknown')} | match_type: {db_val.get('match_type')} "
          f"| validation_type: {db_val.get('validation_type')} ---")
    validations = db_val.get("validations")
    if isinstance(validations, list):
        for item in validations:
            fields = ", ".join(f"{k}={v}" for k, v in (item.get("validation") or {}).items())
            print(f"  {item.get('service_id')}: {item.get('outcome_code')} {fields}")
    elif isinstance(validations, dict) and validations:
        print("  " + ", ".join(f"{k}={v}" for k, v in validations.items()))
    for warning in db_val.get("warnings") or []:
        print(f"  Warning: {warning.get('risk')} ({warning.get('log_type')})")
    for error in db_val.get("errors") or []:
        print(f"  Error: {error.get('service_id')} {error.get('code')} retryable={error.get('retryable')}")
    if "match_score" in db_val:
        print(f"  services_used: {db_val.get('services_used')} | match_score: {db_val.get('match_score')}")


if __name__ == "__main__":
    main()
