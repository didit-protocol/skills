#!/usr/bin/env python3
"""Didit Proof of Address - Verify address documents (utility bills, bank statements, etc.).

Sends the document to POST /v3/poa/ (multipart/form-data), prints the JSON response,
then a short summary: status, formatted address, issuer, issue date and warning risks.
Extraction takes 5-15 s (up to ~30 s for multi-page PDFs), so the client timeout is 60 s.

Usage:
    python scripts/verify_address.py <document_path> [options]

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    python scripts/verify_address.py bill.pdf
    python scripts/verify_address.py bank_statement.jpg --vendor-data user-456
    python scripts/verify_address.py bill.pdf --first-name Jane --last-name Doe --country ESP
    python scripts/verify_address.py bill.pdf --expected-address "Calle Mayor 10, 28013 Madrid" --languages en,es
    python scripts/verify_address.py bill.pdf --document-age utility_bill:6,bank_statement:6,government_issued_document:12,other_poa_document:12
    python scripts/verify_address.py locked.pdf --password "pdf-password" --no-save
"""
import argparse
import json
import mimetypes
import os
import sys

import requests

ENDPOINT = "https://verification.didit.me/v3/poa/"
ALLOWED_EXTENSIONS = {".tiff", ".jpg", ".jpeg", ".png", ".pdf", ".webp"}
MAX_UPLOAD_BYTES = 15 * 1024 * 1024
ACTIONS = ("DECLINE", "NO_ACTION")


def get_api_key() -> str:
    api_key = os.environ.get("DIDIT_API_KEY")
    if not api_key:
        print("Error: DIDIT_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    return api_key


def guess_mime(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    if mime:
        return mime
    if path.lower().endswith(".webp"):
        return "image/webp"
    return "application/octet-stream"


def verify_address(document_path: str, fields: dict) -> dict:
    api_key = get_api_key()
    data = {key: value for key, value in fields.items() if value is not None}
    with open(document_path, "rb") as f:
        files = {"document": (os.path.basename(document_path), f, guess_mime(document_path))}
        r = requests.post(ENDPOINT, headers={"x-api-key": api_key}, files=files, data=data, timeout=60)
    if r.status_code != 200:
        print(f"Error {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)
    return r.json()


def main():
    parser = argparse.ArgumentParser(description="Verify a proof of address document via Didit (POST /v3/poa/)")
    parser.add_argument("document", help="Path to the document (JPG/JPEG/PNG/TIFF/PDF/WEBP, max 15 MB)")
    parser.add_argument("--password", help="Password of an encrypted PDF (document_password)")
    parser.add_argument("--first-name", help="Expected first name (expected_first_name); use with --last-name")
    parser.add_argument("--last-name", help="Expected last name (expected_last_name); use with --first-name")
    parser.add_argument("--expected-address", help="Expected address to geocode and compare (expected_address)")
    parser.add_argument("--country", help="Expected country, ISO alpha-2 or alpha-3, e.g. ESP (expected_country)")
    parser.add_argument("--languages", help="Accepted ISO 639-1 languages, comma-separated, e.g. en,es (poa_languages_allowed)")
    parser.add_argument("--document-age",
                        help="Max age in months per type, e.g. utility_bill:3,bank_statement:3,"
                             "government_issued_document:12,other_poa_document:12 (poa_document_age_months; "
                             "-1 = no age check; omitted types count as not accepted)")
    parser.add_argument("--mismatch-action", choices=ACTIONS,
                        help="Action for name/address/country mismatches (poa_address_mismatch_action, default DECLINE)")
    parser.add_argument("--issues-action", choices=ACTIONS,
                        help="Action for DOCUMENT_METADATA_MISMATCH (poa_document_issues_action, default DECLINE)")
    parser.add_argument("--authenticity-action", choices=ACTIONS,
                        help="Action for SUSPECTED_DOCUMENT_MANIPULATION (poa_document_authenticity_action, default DECLINE)")
    parser.add_argument("--language-action", choices=ACTIONS,
                        help="Action for UNSUPPORTED_DOCUMENT_LANGUAGE (poa_unsupported_language_action, default DECLINE)")
    parser.add_argument("--issuer-action", choices=ACTIONS,
                        help="Action for ISSUER_NOT_IDENTIFIED (poa_issuer_not_identified_action, default DECLINE)")
    parser.add_argument("--vendor-data", help="Your identifier for tracking (vendor_data)")
    parser.add_argument("--metadata", help='JSON object stored with the session, e.g. \'{"flow":"onboarding"}\'')
    parser.add_argument("--no-save", action="store_true",
                        help="Send save_api_request=false (nothing stored, request_id cannot be looked up)")
    args = parser.parse_args()

    if not os.path.isfile(args.document):
        print(f"Error: File not found: {args.document}", file=sys.stderr)
        sys.exit(1)
    if os.path.splitext(args.document)[1].lower() not in ALLOWED_EXTENSIONS:
        parser.error("document must be .jpg, .jpeg, .png, .tiff, .pdf or .webp")
    if os.path.getsize(args.document) > MAX_UPLOAD_BYTES:
        parser.error("document is larger than 15 MB")
    if bool(args.first_name) != bool(args.last_name):
        print("Note: the name check runs only when both --first-name and --last-name are sent.", file=sys.stderr)
    if args.metadata:
        try:
            if not isinstance(json.loads(args.metadata), dict):
                raise ValueError
        except ValueError:
            parser.error("--metadata must be a JSON object")

    fields = {
        "document_password": args.password,
        "expected_first_name": args.first_name,
        "expected_last_name": args.last_name,
        "expected_address": args.expected_address,
        "expected_country": args.country,
        "poa_languages_allowed": args.languages,
        "poa_document_age_months": args.document_age,
        "poa_address_mismatch_action": args.mismatch_action,
        "poa_document_issues_action": args.issues_action,
        "poa_document_authenticity_action": args.authenticity_action,
        "poa_unsupported_language_action": args.language_action,
        "poa_issuer_not_identified_action": args.issuer_action,
        "vendor_data": args.vendor_data,
        "metadata": args.metadata,
        "save_api_request": "false" if args.no_save else None,
    }

    result = verify_address(args.document, fields)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    poa = result.get("poa") or {}
    parsed = poa.get("poa_parsed_address") or {}
    address = poa.get("poa_formatted_address") or ", ".join(
        str(parsed[k]) for k in ("street_1", "street_2", "city", "region", "postal_code", "country") if parsed.get(k)
    )
    risks = [f"{w.get('risk')} ({w.get('log_type')})" for w in poa.get("warnings") or []]
    print(f"\n--- Status: {poa.get('status', 'Unknown')} ---")
    print(f"  Document: {poa.get('document_type')} / {poa.get('document_subtype')}, "
          f"issuer: {poa.get('issuer')}, issued: {poa.get('issue_date')}")
    print(f"  Address: {address or '-'}")
    print(f"  Warnings: {', '.join(risks) if risks else 'none'}")


if __name__ == "__main__":
    main()
