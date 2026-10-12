#!/usr/bin/env python3
"""Didit AML Screening - Screen individuals or companies against global watchlists.

Usage:
    python scripts/screen_aml.py --name "John Smith"
    python scripts/screen_aml.py --name "John Smith" --dob 1985-03-15 --nationality US

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    python scripts/screen_aml.py --name "John Smith"
    python scripts/screen_aml.py --name "Acme Corp" --entity-type company
    python scripts/screen_aml.py --name "Maria Garcia" --dob 1990-01-01 --nationality ESP --doc-number X1234567
"""
import argparse
import json
import os
import sys

import requests

ENDPOINT = "https://verification.didit.me/v3/aml/"


def get_api_key() -> str:
    api_key = os.environ.get("DIDIT_API_KEY")
    if not api_key:
        print("Error: DIDIT_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    return api_key


def screen_aml(full_name: str, date_of_birth: str = None, nationality: str = None,
               document_number: str = None, entity_type: str = "person",
               threshold: int = None, vendor_data: str = None) -> dict:
    api_key = get_api_key()
    payload = {"full_name": full_name, "entity_type": entity_type}
    if date_of_birth:
        payload["date_of_birth"] = date_of_birth
    if nationality:
        payload["nationality"] = nationality
    if document_number:
        payload["document_number"] = document_number
    if threshold is not None:
        payload["aml_match_score_threshold"] = threshold
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
    parser = argparse.ArgumentParser(description="Screen against AML watchlists via Didit")
    parser.add_argument("--name", required=True, help="Full name of person or entity")
    parser.add_argument("--dob", help="Date of birth (YYYY-MM-DD)")
    parser.add_argument("--nationality", help="Country code (alpha-2 or alpha-3)")
    parser.add_argument("--doc-number", help="Document number")
    parser.add_argument("--entity-type", default="person", choices=["person", "company"],
                        help="Entity type (default: person)")
    parser.add_argument("--threshold", type=int, help="Match score threshold (0-100)")
    parser.add_argument("--vendor-data", help="Your identifier for tracking")
    args = parser.parse_args()

    result = screen_aml(args.name, args.dob, args.nationality, args.doc_number,
                        args.entity_type, args.threshold, args.vendor_data)
    print(json.dumps(result, indent=2))

    aml = result.get("aml", {})
    status = aml.get("status", "Unknown")
    total_hits = aml.get("total_hits", 0)
    print(f"\n--- Status: {status} | Total hits: {total_hits} ---")
    for hit in aml.get("hits", [])[:5]:
        print(f"  {hit.get('match_score', '?')}% — {hit.get('name', '?')} "
              f"[{', '.join(hit.get('categories', []))}]")


if __name__ == "__main__":
    main()
