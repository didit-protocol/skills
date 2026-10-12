#!/usr/bin/env python3
"""Didit ID Verification - Verify an identity document (image or PDF).

Usage:
    python scripts/verify_id.py <front_image> [back_image] [--vendor-data <id>] [--no-save]
                                [--no-document-liveness] [--preferred-characters latin|non_latin]
                                [--front-password <pw>] [--back-password <pw>] [--metadata <json>]
                                [--invalid-mrz-action DECLINE|NO_ACTION] [--inconsistent-data-action ...]
                                [--expiration-date-action ...] [--occlusion-action ...]
                                [--format-mismatch-action ...]

Only the options you pass are sent; everything else uses the server defaults
(document liveness on, MRZ/inconsistent data/occlusion DECLINE, missing expiry and
number format mismatch NO_ACTION, latin characters, request saved).

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    python scripts/verify_id.py front.jpg
    python scripts/verify_id.py front.jpg back.jpg --vendor-data user-123
    python scripts/verify_id.py scan.pdf --front-password secret --no-document-liveness
    python scripts/verify_id.py front.jpg back.jpg --preferred-characters non_latin --no-save
    python scripts/verify_id.py front.jpg --format-mismatch-action DECLINE --metadata '{"flow": "onboarding"}'
"""
import argparse
import json
import mimetypes
import os
import sys

import requests

API_URL = "https://verification.didit.me/v3/id-verification/"
ACTIONS = ("DECLINE", "NO_ACTION")


def _file_part(path: str, handle):
    content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    return (os.path.basename(path), handle, content_type)


def verify_id(front_image: str, back_image: str = None, vendor_data: str = None, save: bool = True,
              options: dict = None) -> dict:
    """Call POST /v3/id-verification/. `options` holds extra form fields (already as strings)."""
    api_key = os.environ.get("DIDIT_API_KEY")
    if not api_key:
        print("Error: DIDIT_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    for label, path in (("Front", front_image), ("Back", back_image)):
        if path and not os.path.isfile(path):
            print(f"Error: {label} image not found: {path}", file=sys.stderr)
            sys.exit(1)

    data = {"save_api_request": str(save).lower()}
    if vendor_data:
        data["vendor_data"] = vendor_data
    data.update(options or {})

    with open(front_image, "rb") as front_f:
        files = {"front_image": _file_part(front_image, front_f)}
        if back_image:
            with open(back_image, "rb") as back_f:
                files["back_image"] = _file_part(back_image, back_f)
                response = requests.post(API_URL, headers={"x-api-key": api_key}, files=files,
                                         data=data, timeout=120)
        else:
            response = requests.post(API_URL, headers={"x-api-key": api_key}, files=files,
                                     data=data, timeout=120)

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}", file=sys.stderr)
        sys.exit(1)

    return response.json()


def main():
    parser = argparse.ArgumentParser(
        description="Verify an identity document via the Didit ID Verification API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Docs: https://docs.didit.me/standalone-apis/id-verification",
    )
    parser.add_argument("front_image", help="Front of the document (jpg, jpeg, png, webp, tiff or pdf, max 10 MB)")
    parser.add_argument("back_image", nargs="?", help="Back of the document (optional)")
    parser.add_argument("--vendor-data", help="Your identifier for the user")
    parser.add_argument("--metadata", help="JSON object stored with the request, e.g. '{\"flow\": \"onboarding\"}'")
    parser.add_argument("--no-save", action="store_true",
                        help="save_api_request=false: store nothing, images returned as base64")
    parser.add_argument("--perform-document-liveness", dest="document_liveness", action="store_true",
                        default=None, help="Screen for screen captures, printed copies, portrait manipulation (default)")
    parser.add_argument("--no-document-liveness", dest="document_liveness", action="store_false",
                        help="perform_document_liveness=false")
    parser.add_argument("--preferred-characters", choices=("latin", "non_latin"),
                        help="Script for names/addresses on documents that print both (default latin)")
    parser.add_argument("--front-password", help="Password of an encrypted front PDF")
    parser.add_argument("--back-password", help="Password of an encrypted back PDF")
    parser.add_argument("--invalid-mrz-action", choices=ACTIONS, help="MRZ_VALIDATION_FAILED (default DECLINE)")
    parser.add_argument("--inconsistent-data-action", choices=ACTIONS,
                        help="DATA_INCONSISTENT, MRZ_AND_DATA_EXTRACTED_FROM_OCR_NOT_SAME (default DECLINE)")
    parser.add_argument("--expiration-date-action", choices=ACTIONS,
                        help="EXPIRATION_DATE_NOT_DETECTED (default NO_ACTION)")
    parser.add_argument("--occlusion-action", choices=ACTIONS,
                        help="CRITICAL_FIELD_OCCLUSION_DETECTED (default DECLINE)")
    parser.add_argument("--format-mismatch-action", choices=ACTIONS,
                        help="DOCUMENT_NUMBER_FORMAT_MISMATCH, PERSONAL_NUMBER_FORMAT_MISMATCH (default NO_ACTION)")
    args = parser.parse_args()

    options = {}
    if args.document_liveness is not None:
        options["perform_document_liveness"] = str(args.document_liveness).lower()
    if args.metadata:
        try:
            if not isinstance(json.loads(args.metadata), dict):
                raise ValueError
        except ValueError:
            print("Error: --metadata must be a JSON object.", file=sys.stderr)
            sys.exit(1)
        options["metadata"] = args.metadata
    for field, value in (
        ("preferred_characters", args.preferred_characters),
        ("front_image_password", args.front_password),
        ("back_image_password", args.back_password),
        ("invalid_mrz_action", args.invalid_mrz_action),
        ("inconsistent_data_action", args.inconsistent_data_action),
        ("expiration_date_not_detected_action", args.expiration_date_action),
        ("critical_field_occlusion_action", args.occlusion_action),
        ("document_or_personal_number_format_mismatch_action", args.format_mismatch_action),
    ):
        if value is not None:
            options[field] = value

    result = verify_id(args.front_image, args.back_image, args.vendor_data, save=not args.no_save,
                       options=options)

    print(json.dumps(result, indent=2, ensure_ascii=False))

    id_v = result.get("id_verification") or {}
    risks = ", ".join(f"{w.get('risk')}({w.get('log_type')})" for w in id_v.get("warnings") or []) or "none"
    print(f"\n--- Result: {id_v.get('status', 'Unknown')} | Name: {id_v.get('full_name')} | "
          f"Document: {id_v.get('document_type')} ({id_v.get('issuing_state')}) | "
          f"request_id: {result.get('request_id')} | Warnings: {risks} ---")


if __name__ == "__main__":
    main()
