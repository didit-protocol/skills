#!/usr/bin/env python3
"""Didit Face Search - Search a face (1:N) against every face enrolled in your application.

Usage:
    python scripts/search_faces.py <image_path> [--search-type most_similar|blocklisted_or_approved]
        [--rotate] [--vendor-data <id>] [--metadata '<json object>'] [--no-save]

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    python scripts/search_faces.py selfie.jpg
    python scripts/search_faces.py photo.png --search-type blocklisted_or_approved
    python scripts/search_faces.py photo.png --rotate --vendor-data user-123 --no-save
"""
import argparse
import json
import os
import sys

import requests

ENDPOINT = "https://verification.didit.me/v3/face-search/"
SEARCH_TYPES = ("most_similar", "blocklisted_or_approved")


def get_api_key() -> str:
    api_key = os.environ.get("DIDIT_API_KEY")
    if not api_key:
        print("Error: DIDIT_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    return api_key


def search_faces(image_path: str, search_type: str = None, rotate: bool = False, vendor_data: str = None,
                 metadata: str = None, save: bool = True) -> dict:
    api_key = get_api_key()
    data = {"save_api_request": "true" if save else "false"}
    if search_type:
        data["search_type"] = search_type
    if rotate:
        data["rotate_image"] = "true"
    if vendor_data:
        data["vendor_data"] = vendor_data
    if metadata:
        data["metadata"] = metadata
    with open(image_path, "rb") as f:
        files = {"user_image": (os.path.basename(image_path), f)}
        r = requests.post(ENDPOINT, headers={"x-api-key": api_key}, files=files, data=data, timeout=60)
    if not r.ok:
        print(f"Error {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)
    return r.json()


def main():
    parser = argparse.ArgumentParser(description="Search for matching faces via Didit Face Search")
    parser.add_argument("image", help="Path to the face image (tiff/jpg/jpeg/png/webp, max 5 MB)")
    parser.add_argument("--search-type", choices=SEARCH_TYPES,
                        help="most_similar (server default) or blocklisted_or_approved")
    parser.add_argument("--rotate", action="store_true", help="Try 90-degree rotations for non-upright faces")
    parser.add_argument("--vendor-data", help="Your user identifier, stored and echoed back (does not filter results)")
    parser.add_argument("--metadata", help="JSON object stored with the session and echoed back")
    parser.add_argument("--no-save", action="store_true",
                        help="Send save_api_request=false: nothing stored, face not enrolled")
    args = parser.parse_args()

    if not os.path.isfile(args.image):
        print(f"Error: File not found: {args.image}", file=sys.stderr)
        sys.exit(1)
    if args.metadata:
        try:
            if not isinstance(json.loads(args.metadata), dict):
                raise ValueError
        except ValueError:
            print("Error: --metadata must be a JSON object, e.g. '{\"flow\": \"dedup_check\"}'", file=sys.stderr)
            sys.exit(1)

    result = search_faces(args.image, args.search_type, args.rotate, args.vendor_data, args.metadata,
                          save=not args.no_save)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    face_search = result.get("face_search") or {}
    matches = face_search.get("matches") or []
    risks = ", ".join(w.get("risk", "?") for w in face_search.get("warnings") or []) or "none"
    print(f"\n--- Status: {face_search.get('status', 'Unknown')} | "
          f"{face_search.get('total_matches', len(matches))} match(es) | Warnings: {risks} ---")
    for m in matches:
        ref = m.get("session_id") or m.get("vendor_user_id") or m.get("biometric_template_id") or "-"
        flags = " BLOCKLISTED" if m.get("is_blocklisted") else ""
        flags += " ALLOWLISTED" if m.get("is_allowlisted") else ""
        print(f"  {m.get('similarity_percentage', '?')}% | {m.get('source', '?')} {ref} | "
              f"status {m.get('status')} | vendor_data {m.get('vendor_data')}{flags}")


if __name__ == "__main__":
    main()
