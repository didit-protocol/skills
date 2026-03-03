#!/usr/bin/env python3
"""Didit Face Search - Search for matching faces across all verified sessions.

Usage:
    python scripts/search_faces.py <image_path>
    python scripts/search_faces.py photo.jpg --vendor-data user-123

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    python scripts/search_faces.py selfie.jpg
    python scripts/search_faces.py /path/to/photo.png --rotate
"""
import argparse
import json
import os
import sys

import requests

ENDPOINT = "https://verification.didit.me/v3/face-search/"


def get_api_key() -> str:
    api_key = os.environ.get("DIDIT_API_KEY")
    if not api_key:
        print("Error: DIDIT_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    return api_key


def search_faces(image_path: str, rotate: bool = False, vendor_data: str = None) -> dict:
    api_key = get_api_key()
    with open(image_path, "rb") as f:
        files = {"user_image": (os.path.basename(image_path), f, "image/jpeg")}
        data = {}
        if rotate:
            data["rotate_image"] = "true"
        if vendor_data:
            data["vendor_data"] = vendor_data
        r = requests.post(ENDPOINT, headers={"x-api-key": api_key},
                          files=files, data=data, timeout=60)
    if r.status_code not in (200, 201):
        print(f"Error {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)
    return r.json()


def main():
    parser = argparse.ArgumentParser(description="Search for matching faces via Didit")
    parser.add_argument("image", help="Path to face image (JPEG/PNG/WebP/TIFF)")
    parser.add_argument("--rotate", action="store_true", help="Try rotations for non-upright faces")
    parser.add_argument("--vendor-data", help="Your identifier for tracking")
    args = parser.parse_args()

    if not os.path.isfile(args.image):
        print(f"Error: File not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    result = search_faces(args.image, args.rotate, args.vendor_data)
    print(json.dumps(result, indent=2))

    face_search = result.get("face_search", {})
    matches = face_search.get("matches", [])
    print(f"\n--- {len(matches)} match(es) found ---")
    for m in matches:
        print(f"  {m.get('similarity', '?')}% — session {m.get('session_id', '?')} "
              f"({m.get('status', '?')})")


if __name__ == "__main__":
    main()
