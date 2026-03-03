#!/usr/bin/env python3
"""Didit Database Validation - Validate identity against government databases.

Usage:
    python scripts/validate_database.py --id-number 12345678 --country PER
    python scripts/validate_database.py --id-number 12345678901 --country BRA --first-name Carlos

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    python scripts/validate_database.py --id-number 12345678 --country PER --first-name Carlos --last-name Garcia
    python scripts/validate_database.py --id-number GARC850315HDFRRL09 --country MEX
"""
import argparse
import json
import os
import sys

import requests

ENDPOINT = "https://verification.didit.me/v3/database-validation/"


def get_api_key() -> str:
    api_key = os.environ.get("DIDIT_API_KEY")
    if not api_key:
        print("Error: DIDIT_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    return api_key


def validate_database(id_number: str, issuing_state: str = None, first_name: str = None,
                      last_name: str = None, date_of_birth: str = None,
                      vendor_data: str = None) -> dict:
    api_key = get_api_key()
    payload = {"id_number": id_number}
    if issuing_state:
        payload["issuing_state"] = issuing_state
    if first_name:
        payload["first_name"] = first_name
    if last_name:
        payload["last_name"] = last_name
    if date_of_birth:
        payload["date_of_birth"] = date_of_birth
    if vendor_data:
        payload["vendor_data"] = vendor_data
    r = requests.post(ENDPOINT,
                      headers={"x-api-key": api_key, "Content-Type": "application/json"},
                      json=payload, timeout=60)
    if r.status_code not in (200, 201):
        print(f"Error {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)
    return r.json()


def main():
    parser = argparse.ArgumentParser(description="Validate identity against government databases via Didit")
    parser.add_argument("--id-number", required=True, help="ID number (auto-maps to country field)")
    parser.add_argument("--country", help="Issuing country (ISO 3166-1 alpha-3)")
    parser.add_argument("--first-name", help="First name for matching")
    parser.add_argument("--last-name", help="Last name for matching")
    parser.add_argument("--dob", help="Date of birth (YYYY-MM-DD)")
    parser.add_argument("--vendor-data", help="Your identifier for tracking")
    args = parser.parse_args()

    result = validate_database(args.id_number, args.country, args.first_name,
                               args.last_name, args.dob, args.vendor_data)
    print(json.dumps(result, indent=2))

    db_val = result.get("database_validation", {})
    status = db_val.get("status", "Unknown")
    print(f"\n--- Status: {status} ---")
    if db_val.get("matched_fields"):
        print(f"  Matched fields: {', '.join(db_val['matched_fields'])}")


if __name__ == "__main__":
    main()
