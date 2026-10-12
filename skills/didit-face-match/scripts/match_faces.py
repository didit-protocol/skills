#!/usr/bin/env python3
"""Didit Face Match - Compare two facial images.

Usage:
    python scripts/match_faces.py <user_image> <ref_image> [--threshold <0-100>] [--rotate] [--vendor-data <id>]

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    python scripts/match_faces.py selfie.jpg id_photo.jpg
    python scripts/match_faces.py selfie.jpg id_photo.jpg --threshold 50 --rotate
"""
import argparse
import json
import os
import sys

import requests

API_URL = "https://verification.didit.me/v3/face-match/"


def match_faces(user_image: str, ref_image: str, threshold: int = 30, rotate: bool = False, vendor_data: str = None) -> dict:
    api_key = os.environ.get("DIDIT_API_KEY")
    if not api_key:
        print("Error: DIDIT_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    for path, label in [(user_image, "User image"), (ref_image, "Reference image")]:
        if not os.path.isfile(path):
            print(f"Error: {label} not found: {path}", file=sys.stderr)
            sys.exit(1)

    headers = {"x-api-key": api_key}
    data = {
        "face_match_score_decline_threshold": str(threshold),
        "rotate_image": str(rotate).lower(),
    }
    if vendor_data:
        data["vendor_data"] = vendor_data

    with open(user_image, "rb") as uf, open(ref_image, "rb") as rf:
        files = {
            "user_image": (os.path.basename(user_image), uf),
            "ref_image": (os.path.basename(ref_image), rf),
        }
        response = requests.post(API_URL, headers=headers, files=files,
                                 data=data, timeout=60)

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}", file=sys.stderr)
        sys.exit(1)

    return response.json()


def main():
    parser = argparse.ArgumentParser(description="Compare two facial images via Didit API")
    parser.add_argument("user_image", help="Path to user's face image")
    parser.add_argument("ref_image", help="Path to reference image")
    parser.add_argument("--threshold", type=int, default=30, help="Decline threshold 0-100 (default: 30)")
    parser.add_argument("--rotate", action="store_true", help="Try rotating images to find upright face")
    parser.add_argument("--vendor-data", help="Unique identifier for session tracking")
    args = parser.parse_args()

    result = match_faces(args.user_image, args.ref_image, args.threshold, args.rotate, args.vendor_data)

    print(json.dumps(result, indent=2, ensure_ascii=False))

    fm = result.get("face_match", {})
    print(f"\n--- Result: {fm.get('status', 'Unknown')} | Score: {fm.get('score', 'N/A')}/100 ---")


if __name__ == "__main__":
    main()
