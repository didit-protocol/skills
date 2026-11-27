#!/usr/bin/env python3
"""Didit Face Match - Compare two facial images (1:1).

Usage:
    python scripts/match_faces.py <user_image> <ref_image> [--threshold <0-100>] [--rotate]
        [--vendor-data <id>] [--metadata '<json object>'] [--no-save]

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    python scripts/match_faces.py selfie.jpg id_photo.jpg
    python scripts/match_faces.py selfie.jpg id_photo.jpg --threshold 50 --rotate --vendor-data user-123
    python scripts/match_faces.py selfie.jpg id_photo.jpg --no-save --metadata '{"flow": "login"}'
"""
import argparse
import json
import os
import sys

import requests

API_URL = "https://verification.didit.me/v3/face-match/"


def match_faces(user_image: str, ref_image: str, threshold: float = None, rotate: bool = False,
                vendor_data: str = None, metadata: str = None, save: bool = True) -> dict:
    api_key = os.environ.get("DIDIT_API_KEY")
    if not api_key:
        print("Error: DIDIT_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    for path, label in [(user_image, "User image"), (ref_image, "Reference image")]:
        if not os.path.isfile(path):
            print(f"Error: {label} not found: {path}", file=sys.stderr)
            sys.exit(1)

    data = {
        "rotate_image": "true" if rotate else "false",
        "save_api_request": "true" if save else "false",
    }
    if threshold is not None:
        data["face_match_score_decline_threshold"] = str(threshold)
    if vendor_data:
        data["vendor_data"] = vendor_data
    if metadata:
        data["metadata"] = metadata

    with open(user_image, "rb") as uf, open(ref_image, "rb") as rf:
        files = {
            "user_image": (os.path.basename(user_image), uf),
            "ref_image": (os.path.basename(ref_image), rf),
        }
        response = requests.post(API_URL, headers={"x-api-key": api_key}, files=files, data=data, timeout=60)

    if not response.ok:
        print(f"Error {response.status_code}: {response.text}", file=sys.stderr)
        sys.exit(1)

    return response.json()


def main():
    parser = argparse.ArgumentParser(description="Compare two facial images via the Didit API")
    parser.add_argument("user_image", help="Path to the user's face image (tiff/jpg/jpeg/png/webp, max 5 MB)")
    parser.add_argument("ref_image", help="Path to the reference face image")
    parser.add_argument("--threshold", type=float,
                        help="face_match_score_decline_threshold 0-100 (server default 30); "
                             "scores at or below it decline")
    parser.add_argument("--rotate", action="store_true", help="Try 90-degree rotations to find upright faces")
    parser.add_argument("--vendor-data", help="Your user identifier, stored and echoed back")
    parser.add_argument("--metadata", help="JSON object stored with the session and echoed back")
    parser.add_argument("--no-save", action="store_true", help="Send save_api_request=false: nothing is stored")
    args = parser.parse_args()

    if args.metadata:
        try:
            if not isinstance(json.loads(args.metadata), dict):
                raise ValueError
        except ValueError:
            print("Error: --metadata must be a JSON object, e.g. '{\"flow\": \"login\"}'", file=sys.stderr)
            sys.exit(1)

    result = match_faces(args.user_image, args.ref_image, args.threshold, args.rotate, args.vendor_data,
                         args.metadata, save=not args.no_save)

    print(json.dumps(result, indent=2, ensure_ascii=False))

    fm = result.get("face_match") or {}
    risks = ", ".join(w.get("risk", "?") for w in fm.get("warnings") or []) or "none"
    print(f"\n--- Result: {fm.get('status', 'Unknown')} | Score: {fm.get('score')} | Warnings: {risks} ---")


if __name__ == "__main__":
    main()
