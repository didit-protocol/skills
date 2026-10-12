#!/usr/bin/env python3
"""Didit Database Validation - Validate identity against government databases.

Pick the number field that matches the issuing country (see the country table in
SKILL.md): most countries use --personal-number (e.g. PE DNI, MX CURP, CL RUT,
CO/CR/DO/EC Cedula, ES DNI/NIE, UY CI), Brazil uses --tax-number (CPF), and
AR/BO/GT/HN/PA/PY/SV/VE use --document-number. The field name is load-bearing:
the API does not auto-route by issuing_state, so sending the value under the
wrong field returns a no-match.

Usage:
    python scripts/validate_database.py --issuing-state PE --personal-number 12345678
    python scripts/validate_database.py --issuing-state BR --tax-number 12345678901 --first-name Carlos

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    python scripts/validate_database.py --issuing-state PE --personal-number 12345678 --first-name Carlos --last-name Garcia
    python scripts/validate_database.py --issuing-state MX --personal-number GARC850315HDFRRL09
    python scripts/validate_database.py --issuing-state BR --tax-number 12345678901
    python scripts/validate_database.py --issuing-state AR --document-number 12345678
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


def validate_database(issuing_state: str, document_number: str = None, personal_number: str = None,
                      tax_number: str = None, first_name: str = None, last_name: str = None,
                      date_of_birth: str = None, vendor_data: str = None) -> dict:
    api_key = get_api_key()
    payload = {"issuing_state": issuing_state}
    if document_number:
        payload["document_number"] = document_number
    if personal_number:
        payload["personal_number"] = personal_number
    if tax_number:
        payload["tax_number"] = tax_number
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
    parser.add_argument("--issuing-state", required=True, help="Issuing country (ISO 3166-1 alpha-2) — selects data sources")
    parser.add_argument("--document-number", help="Country-specific document number (AR/BO/GT/HN/PA/PY/SV/VE)")
    parser.add_argument("--personal-number", help="Country-specific personal number (PE/MX/CL/CO/CR/DO/EC/ES/UY)")
    parser.add_argument("--tax-number", help="Country-specific tax number (BR CPF)")
    parser.add_argument("--first-name", help="First name for matching")
    parser.add_argument("--last-name", help="Last name for matching")
    parser.add_argument("--dob", help="Date of birth (YYYY-MM-DD)")
    parser.add_argument("--vendor-data", help="Your identifier for tracking")
    args = parser.parse_args()

    if not (args.document_number or args.personal_number or args.tax_number):
        parser.error("provide one of --document-number / --personal-number / --tax-number "
                     "(see the country table in SKILL.md for which one your issuing_state needs)")

    result = validate_database(args.issuing_state, args.document_number, args.personal_number,
                               args.tax_number, args.first_name, args.last_name,
                               args.dob, args.vendor_data)
    print(json.dumps(result, indent=2))

    db_val = result.get("database_validation", {})
    status = db_val.get("status", "Unknown")
    print(f"\n--- Status: {status} ---")
    if db_val.get("matched_fields"):
        print(f"  Matched fields: {', '.join(db_val['matched_fields'])}")


if __name__ == "__main__":
    main()
