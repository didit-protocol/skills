#!/usr/bin/env python3
"""Didit Age Estimation - Estimate a person's age from a facial image (with passive liveness).

Usage:
    python scripts/estimate_age.py <image_path> [--threshold <0-100>] [--liveness-threshold <0-100>]
        [--rotate] [--vendor-data <id>] [--metadata '<json object>'] [--no-save]

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    python scripts/estimate_age.py selfie.jpg
    python scripts/estimate_age.py photo.png --threshold 21 --vendor-data user-123
    python scripts/estimate_age.py photo.png --liveness-threshold 50 --rotate --no-save
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


def estimate_age(image_path: str, age_threshold: int = None, liveness_threshold: float = None,
                 rotate: bool = False, vendor_data: str = None, metadata: str = None, save: bool = True) -> dict:
    api_key = get_api_key()
    data = {"save_api_request": "true" if save else "false"}
    if age_threshold is not None:
        data["age_estimation_decline_threshold"] = str(age_threshold)
    if liveness_threshold is not None:
        data["face_liveness_score_decline_threshold"] = str(liveness_threshold)
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
    parser = argparse.ArgumentParser(description="Estimate age from a facial image via Didit")
    parser.add_argument("image", help="Path to the face image (tiff/jpg/jpeg/png/webp, max 5 MB)")
    parser.add_argument("--threshold", type=int,
                        help="age_estimation_decline_threshold 0-100 (server default 18; 0 disables the age check). "
                             "Estimated ages strictly below it decline")
    parser.add_argument("--liveness-threshold", type=float,
                        help="face_liveness_score_decline_threshold 0-100 (server default 30); "
                             "liveness scores at or below it decline")
    parser.add_argument("--rotate", action="store_true", help="Try 90-degree rotations for non-upright faces")
    parser.add_argument("--vendor-data", help="Your user identifier, stored and echoed back")
    parser.add_argument("--metadata", help="JSON object stored with the session and echoed back")
    parser.add_argument("--no-save", action="store_true",
                        help="Send save_api_request=false: nothing stored, face not added to the index")
    args = parser.parse_args()

    if not os.path.isfile(args.image):
        print(f"Error: File not found: {args.image}", file=sys.stderr)
        sys.exit(1)
    if args.threshold is not None and not 0 <= args.threshold <= 100:
        print("Error: --threshold must be between 0 and 100", file=sys.stderr)
        sys.exit(1)
    if args.metadata:
        try:
            if not isinstance(json.loads(args.metadata), dict):
                raise ValueError
        except ValueError:
            print("Error: --metadata must be a JSON object, e.g. '{\"flow\": \"age-gate\"}'", file=sys.stderr)
            sys.exit(1)

    result = estimate_age(args.image, args.threshold, args.liveness_threshold, args.rotate, args.vendor_data,
                          args.metadata, save=not args.no_save)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    age_est = result.get("age_estimation") or {}
    risks = ", ".join(w.get("risk", "?") for w in age_est.get("warnings") or []) or "none"
    print(f"\n--- Status: {age_est.get('status', 'Unknown')} | Estimated age: {age_est.get('age_estimation')} | "
          f"Liveness score: {age_est.get('score')} | Warnings: {risks} ---")


if __name__ == "__main__":
    main()
