#!/usr/bin/env python3
"""Didit Passive Liveness - Verify a user is physically present.

Usage:
    python scripts/check_liveness.py <user_image> [--threshold <0-100>] [--rotate] [--vendor-data <id>]

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    python scripts/check_liveness.py selfie.jpg
    python scripts/check_liveness.py selfie.jpg --threshold 80
"""
import argparse
import json
import os
import sys

import requests

API_URL = "https://verification.didit.me/v3/passive-liveness/"


def check_liveness(user_image: str, threshold: int = None, rotate: bool = False, vendor_data: str = None) -> dict:
    api_key = os.environ.get("DIDIT_API_KEY")
    if not api_key:
        print("Error: DIDIT_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(user_image):
        print(f"Error: Image not found: {user_image}", file=sys.stderr)
        sys.exit(1)

    headers = {"x-api-key": api_key}
    data = {}
    if threshold is not None:
        data["face_liveness_score_decline_threshold"] = str(threshold)
    if rotate:
        data["rotate_image"] = "true"
    if vendor_data:
        data["vendor_data"] = vendor_data

    with open(user_image, "rb") as f:
        files = {"user_image": (os.path.basename(user_image), f)}
        response = requests.post(API_URL, headers=headers, files=files,
                                 data=data, timeout=60)

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}", file=sys.stderr)
        sys.exit(1)

    return response.json()


def main():
    parser = argparse.ArgumentParser(description="Check passive liveness via Didit API")
    parser.add_argument("user_image", help="Path to user's face image")
    parser.add_argument("--threshold", type=int, help="Decline threshold 0-100")
    parser.add_argument("--rotate", action="store_true", help="Try rotating image to find upright face")
    parser.add_argument("--vendor-data", help="Unique identifier for session tracking")
    args = parser.parse_args()

    result = check_liveness(args.user_image, args.threshold, args.rotate, args.vendor_data)

    print(json.dumps(result, indent=2, ensure_ascii=False))

    lv = result.get("liveness", {})
    print(f"\n--- Result: {lv.get('status', 'Unknown')} | Score: {lv.get('score', 'N/A')}/100 | Quality: {lv.get('face_quality', 'N/A')} ---")


if __name__ == "__main__":
    main()
