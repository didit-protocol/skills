#!/usr/bin/env python3
"""Didit ID Verification - Verify an identity document.

Usage:
    python scripts/verify_id.py <front_image> [back_image] [--vendor-data <id>] [--no-save]

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    python scripts/verify_id.py front.jpg
    python scripts/verify_id.py front.jpg back.jpg --vendor-data user-123
"""
import argparse
import json
import os
import sys

import requests

API_URL = "https://verification.didit.me/v3/id-verification/"


def verify_id(front_image: str, back_image: str = None, vendor_data: str = None, save: bool = True) -> dict:
    api_key = os.environ.get("DIDIT_API_KEY")
    if not api_key:
        print("Error: DIDIT_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(front_image):
        print(f"Error: Front image not found: {front_image}", file=sys.stderr)
        sys.exit(1)

    if back_image and not os.path.isfile(back_image):
        print(f"Error: Back image not found: {back_image}", file=sys.stderr)
        sys.exit(1)

    headers = {"x-api-key": api_key}
    data = {"save_api_request": str(save).lower()}
    if vendor_data:
        data["vendor_data"] = vendor_data

    with open(front_image, "rb") as front_f:
        files = {"front_image": (os.path.basename(front_image), front_f)}
        if back_image:
            with open(back_image, "rb") as back_f:
                files["back_image"] = (os.path.basename(back_image), back_f)
                response = requests.post(API_URL, headers=headers, files=files,
                                         data=data, timeout=60)
        else:
            response = requests.post(API_URL, headers=headers, files=files,
                                     data=data, timeout=60)

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}", file=sys.stderr)
        sys.exit(1)

    return response.json()


def main():
    parser = argparse.ArgumentParser(description="Verify an identity document via Didit API")
    parser.add_argument("front_image", help="Path to front image of ID document")
    parser.add_argument("back_image", nargs="?", help="Path to back image (optional)")
    parser.add_argument("--vendor-data", help="Unique identifier for session tracking")
    parser.add_argument("--no-save", action="store_true", help="Don't save request in Business Console")
    args = parser.parse_args()

    result = verify_id(args.front_image, args.back_image, args.vendor_data, save=not args.no_save)

    print(json.dumps(result, indent=2, ensure_ascii=False))

    status = result.get("id_verification", {}).get("status", "Unknown")
    name = result.get("id_verification", {}).get("full_name", "N/A")
    doc_type = result.get("id_verification", {}).get("document_type", "N/A")
    print(f"\n--- Result: {status} | Name: {name} | Document: {doc_type} ---")


if __name__ == "__main__":
    main()
