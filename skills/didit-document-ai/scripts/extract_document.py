#!/usr/bin/env python3
"""Didit Document AI - Extract the fields you define from a document.

Usage:
    python scripts/extract_document.py <document> (--fields-file <path> | --fields '<json array>') [options]

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    # Field definitions from a JSON file
    python scripts/extract_document.py statement.pdf --fields-file fields.json

    # Inline fields, with a person name check that sends mismatches to review
    python scripts/extract_document.py payslip.pdf \
        --fields '[{"key":"employee_name","type":"text","required":true,"is_full_name":true},{"key":"net_pay","type":"number","required":true}]' \
        --first-name Jane --last-name Doe --name-mismatch-action REVIEW

    # Company document, not saved in the Business Console
    python scripts/extract_document.py deed.pdf --fields-file company_fields.json \
        --company-name "Acme Energy" --company-country FR --no-save
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import requests

API_URL = "https://verification.didit.me/v3/document-ai/"
ACTIONS = ["DECLINE", "REVIEW", "NO_ACTION"]

# CLI dest -> form field name
ACTION_FIELDS = {
    "unreadable_action": "document_ai_unreadable_document_action",
    "missing_required_action": "document_ai_missing_required_fields_action",
    "tampering_action": "document_ai_document_tampering_action",
    "name_mismatch_action": "document_ai_name_mismatch_action",
    "unsupported_file_action": "document_ai_unsupported_file_action",
}


def fail(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def load_fields(args: argparse.Namespace) -> str:
    if args.fields_file:
        if not os.path.isfile(args.fields_file):
            fail(f"fields file not found: {args.fields_file}")
        with open(args.fields_file, "r", encoding="utf-8") as handle:
            raw = handle.read()
    else:
        raw = args.fields
    try:
        fields = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"fields is not valid JSON: {exc}")
    if not isinstance(fields, list) or not 1 <= len(fields) <= 30:
        fail("fields must be a JSON array with 1 to 30 items.")
    # Send one compact JSON-encoded array string, as the API requires.
    return json.dumps(fields, separators=(",", ":"), ensure_ascii=False)


def build_form(args: argparse.Namespace) -> dict:
    if (args.first_name or args.last_name) and args.company_name:
        fail("send either --first-name/--last-name or --company-name, not both.")
    if args.company_country and not args.company_name:
        fail("--company-country needs --company-name.")

    data = {"fields": load_fields(args)}
    optional = {
        "expected_first_name": args.first_name,
        "expected_last_name": args.last_name,
        "expected_company_name": args.company_name,
        "expected_company_country": args.company_country,
        "vendor_data": args.vendor_data,
    }
    data.update({key: value for key, value in optional.items() if value})
    if args.threshold is not None:
        data["document_ai_name_match_score_threshold"] = str(args.threshold)
    for dest, field_name in ACTION_FIELDS.items():
        value = getattr(args, dest)
        if value:
            data[field_name] = value
    if args.no_save:
        data["save_api_request"] = "false"
    if args.metadata:
        try:
            metadata = json.loads(args.metadata)
        except json.JSONDecodeError as exc:
            fail(f"--metadata is not valid JSON: {exc}")
        if not isinstance(metadata, dict):
            fail("--metadata must be a JSON object.")
        data["metadata"] = json.dumps(metadata)
    return data


def extract(document_path: str, data: dict, timeout: int) -> dict:
    api_key = os.environ.get("DIDIT_API_KEY")
    if not api_key:
        fail("DIDIT_API_KEY environment variable is not set.")
    if not os.path.isfile(document_path):
        fail(f"document not found: {document_path}")

    with open(document_path, "rb") as document:
        files = {"document": (os.path.basename(document_path), document)}
        response = requests.post(
            API_URL, headers={"x-api-key": api_key}, files=files, data=data, timeout=timeout
        )

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}", file=sys.stderr)
        sys.exit(1)
    return response.json()


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract custom fields from a document via Didit Document AI")
    parser.add_argument("document", help="Path to the document (pdf, jpg, jpeg, png, tiff, webp or zip)")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--fields-file", help="Path to a JSON file with the fields array")
    source.add_argument("--fields", help="Fields as one JSON array string")
    parser.add_argument("--first-name", help="Expected first name (person)")
    parser.add_argument("--last-name", help="Expected last name (person)")
    parser.add_argument("--company-name", help="Expected company name")
    parser.add_argument("--company-country", help="2-letter ISO country for company-name matching")
    parser.add_argument("--threshold", type=int, help="Name match threshold 0-100 (default: 80)")
    parser.add_argument("--unreadable-action", choices=ACTIONS, help="Default: REVIEW")
    parser.add_argument("--missing-required-action", choices=ACTIONS, help="Default: REVIEW")
    parser.add_argument("--tampering-action", choices=ACTIONS, help="Default: DECLINE")
    parser.add_argument("--name-mismatch-action", choices=ACTIONS, help="Default: NO_ACTION")
    parser.add_argument("--unsupported-file-action", choices=ACTIONS, help="Default: REVIEW")
    parser.add_argument("--no-save", action="store_true", help="Send save_api_request=false (still billed)")
    parser.add_argument("--vendor-data", help="Your identifier for the user")
    parser.add_argument("--metadata", help="JSON object echoed back, e.g. '{\"flow\":\"onboarding\"}'")
    parser.add_argument("--timeout", type=int, default=90, help="Client timeout in seconds (default: 90)")
    args = parser.parse_args()

    result = extract(args.document, build_form(args), args.timeout)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    doc = result.get("document_ai") or {}
    extracted = doc.get("extracted_data") or {}
    found = sum(1 for value in extracted.values() if value is not None)
    risks = ", ".join(w.get("risk", "?") for w in doc.get("warnings") or []) or "none"
    print(
        f"\n--- Status: {doc.get('status', 'Unknown')} | fields read: {found}/{len(extracted)} | "
        f"name match: {doc.get('name_match_score')} | warnings: {risks} | request_id: {result.get('request_id')} ---"
    )


if __name__ == "__main__":
    main()
