#!/usr/bin/env python3
"""Didit Age Estimation - Estimate a person's age from a facial image.

Usage:
    python scripts/estimate_age.py <image_path>
    python scripts/estimate_age.py selfie.jpg --threshold 21

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    python scripts/estimate_age.py selfie.jpg
    python scripts/estimate_age.py photo.png --threshold 18 --vendor-data user-123
"""
import argparse
import json
import os
import sys

import requests

ENDPOINT = "https://verification.didit.me/v3/age-estimation/"


def get_api_key() -> str:
    api_key = os.environ.get("DIDIT_API_KEY")
    if not api_key:
        print("Error: DIDIT_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    return api_key


def estimate_age(image_path: str, rotate: bool = False, vendor_data: str = None) -> dict:
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
    parser = argparse.ArgumentParser(description="Estimate age from a facial image via Didit")
    parser.add_argument("image", help="Path to face image (JPEG/PNG/WebP/TIFF)")
    parser.add_argument("--threshold", type=int, default=18,
                        help="Age threshold to check against (default: 18)")
    parser.add_argument("--rotate", action="store_true", help="Try rotations for non-upright faces")
    parser.add_argument("--vendor-data", help="Your identifier for tracking")
    args = parser.parse_args()

    if not os.path.isfile(args.image):
        print(f"Error: File not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    result = estimate_age(args.image, args.rotate, args.vendor_data)
    print(json.dumps(result, indent=2))

    age_est = result.get("age_estimation", {})
    estimated_age = age_est.get("estimated_age")
    status = age_est.get("status", "Unknown")
    print(f"\n--- Estimated age: {estimated_age} | Status: {status} ---")
    if estimated_age is not None:
        age_val = float(estimated_age)
        if age_val >= args.threshold:
            print(f"  PASS: {age_val:.1f} >= {args.threshold}")
        else:
            print(f"  FAIL: {age_val:.1f} < {args.threshold}")


if __name__ == "__main__":
    main()
