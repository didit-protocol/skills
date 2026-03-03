#!/usr/bin/env python3
"""Didit Proof of Address - Verify address documents (utility bills, bank statements, etc.).

Usage:
    python scripts/verify_address.py <document_path>
    python scripts/verify_address.py utility_bill.pdf --vendor-data user-123

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    python scripts/verify_address.py bill.pdf
    python scripts/verify_address.py bank_statement.jpg --vendor-data user-456
"""
import argparse
import json
import os
import sys

import requests

ENDPOINT = "https://verification.didit.me/v3/poa/"


def get_api_key() -> str:
    api_key = os.environ.get("DIDIT_API_KEY")
    if not api_key:
        print("Error: DIDIT_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    return api_key


def verify_address(document_path: str, vendor_data: str = None) -> dict:
    api_key = get_api_key()
    mime = "application/pdf" if document_path.lower().endswith(".pdf") else "image/jpeg"
    with open(document_path, "rb") as f:
        files = {"document": (os.path.basename(document_path), f, mime)}
        data = {}
        if vendor_data:
            data["vendor_data"] = vendor_data
        r = requests.post(ENDPOINT, headers={"x-api-key": api_key},
                          files=files, data=data, timeout=60)
    if r.status_code not in (200, 201):
        print(f"Error {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)
    return r.json()


def main():
    parser = argparse.ArgumentParser(description="Verify proof of address via Didit")
    parser.add_argument("document", help="Path to document (JPG/PNG/TIFF/PDF, max 15MB)")
    parser.add_argument("--vendor-data", help="Your identifier for tracking")
    args = parser.parse_args()

    if not os.path.isfile(args.document):
        print(f"Error: File not found: {args.document}", file=sys.stderr)
        sys.exit(1)

    result = verify_address(args.document, args.vendor_data)
    print(json.dumps(result, indent=2))

    poa = result.get("poa", {})
    status = poa.get("status", "Unknown")
    address = poa.get("address", {})
    print(f"\n--- Status: {status} ---")
    if address:
        parts = [address.get("street", ""), address.get("city", ""),
                 address.get("state", ""), address.get("country", "")]
        print(f"  Address: {', '.join(p for p in parts if p)}")


if __name__ == "__main__":
    main()
