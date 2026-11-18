#!/usr/bin/env python3
"""Didit Passive Liveness - Verify a user is physically present from one selfie.

Usage:
    python scripts/check_liveness.py <user_image> [--threshold <0-100>] [--rotate]
        [--vendor-data <id>] [--metadata '<json object>'] [--no-save]

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    python scripts/check_liveness.py selfie.jpg
    python scripts/check_liveness.py selfie.jpg --threshold 50 --vendor-data user-123
    python scripts/check_liveness.py selfie.jpg --rotate --no-save --metadata '{"flow": "withdrawal"}'
"""
import argparse
import json
import os
import sys

import requests

API_URL = "https://verification.didit.me/v3/passive-liveness/"


def check_liveness(user_image: str, threshold: float = None, rotate: bool = False, vendor_data: str = None,
                   metadata: str = None, save: bool = True) -> dict:
    api_key = os.environ.get("DIDIT_API_KEY")
    if not api_key:
        print("Error: DIDIT_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(user_image):
        print(f"Error: Image not found: {user_image}", file=sys.stderr)
        sys.exit(1)

    data = {"save_api_request": "true" if save else "false"}
    if threshold is not None:
        data["face_liveness_score_decline_threshold"] = str(threshold)
    if rotate:
        data["rotate_image"] = "true"
    if vendor_data:
        data["vendor_data"] = vendor_data
    if metadata:
        data["metadata"] = metadata

    with open(user_image, "rb") as f:
        files = {"user_image": (os.path.basename(user_image), f)}
        response = requests.post(API_URL, headers={"x-api-key": api_key}, files=files, data=data, timeout=60)

    if not response.ok:
        print(f"Error {response.status_code}: {response.text}", file=sys.stderr)
        sys.exit(1)

    return response.json()


def main():
    parser = argparse.ArgumentParser(description="Check passive liveness via the Didit API")
    parser.add_argument("user_image", help="Path to the user's face image (tiff/jpg/jpeg/png/webp, max 5 MB)")
    parser.add_argument("--threshold", type=float,
                        help="face_liveness_score_decline_threshold 0-100 (server default 30); "
                             "scores at or below it decline")
    parser.add_argument("--rotate", action="store_true", help="Try 90-degree rotations to find an upright face")
    parser.add_argument("--vendor-data", help="Your user identifier (also skips this user's earlier faces "
                                              "in the duplicate check)")
    parser.add_argument("--metadata", help="JSON object stored with the session and echoed back")
    parser.add_argument("--no-save", action="store_true",
                        help="Send save_api_request=false: nothing stored, face not enrolled")
    args = parser.parse_args()

    if args.metadata:
        try:
            if not isinstance(json.loads(args.metadata), dict):
                raise ValueError
        except ValueError:
            print("Error: --metadata must be a JSON object, e.g. '{\"flow\": \"withdrawal\"}'", file=sys.stderr)
            sys.exit(1)

    result = check_liveness(args.user_image, args.threshold, args.rotate, args.vendor_data, args.metadata,
                            save=not args.no_save)

    print(json.dumps(result, indent=2, ensure_ascii=False))

    lv = result.get("liveness") or {}
    risks = ", ".join(w.get("risk", "?") for w in lv.get("warnings") or []) or "none"
    print(f"\n--- Result: {lv.get('status', 'Unknown')} | Score: {lv.get('score')} | "
          f"Quality: {lv.get('face_quality')} | Luminance: {lv.get('face_luminance')} | Warnings: {risks} ---")


if __name__ == "__main__":
    main()
