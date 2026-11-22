#!/usr/bin/env python3
"""Didit AML Screening - Screen individuals or companies against global watchlists.

Usage:
    python scripts/screen_aml.py --name "Jane Doe"
    python scripts/screen_aml.py --name "Jane Doe" --dob 1985-03-15 --nationality US [--doc-number <n>]
        [--entity-type person|company] [--match-threshold 0-100] [--approve-threshold 0-100]
        [--review-threshold 0-100] [--weights NAME DOB COUNTRY] [--adverse-media] [--ongoing-monitoring]
        [--no-save] [--vendor-data <id>] [--metadata <json>] [--idempotency-key <key>]

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    python scripts/screen_aml.py --name "Jane Doe"
    python scripts/screen_aml.py --name "Acme Energy Ltd" --entity-type company
    python scripts/screen_aml.py --name "Maria Ejemplo" --dob 1990-01-01 --nationality ES --doc-number X1234567
    python scripts/screen_aml.py --name "Jane Doe" --adverse-media --ongoing-monitoring --idempotency-key user-1234-aml
"""
import argparse
import json
import os
import sys

import requests

ENDPOINT = "https://verification.didit.me/v3/aml/"


def get_api_key() -> str:
    api_key = os.environ.get("DIDIT_API_KEY")
    if not api_key:
        print("Error: DIDIT_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    return api_key


def screen_aml(full_name: str, date_of_birth: str = None, nationality: str = None,
               document_number: str = None, entity_type: str = "person",
               match_threshold: int = None, approve_threshold: float = None, review_threshold: float = None,
               weights: tuple = None, include_adverse_media: bool = False,
               include_ongoing_monitoring: bool = False, save_api_request: bool = True,
               vendor_data: str = None, metadata: dict = None, idempotency_key: str = None) -> dict:
    """POST /v3/aml/. `nationality` must be ISO 3166-1 alpha-2 (e.g. "US")."""
    payload = {"full_name": full_name, "entity_type": entity_type}
    if date_of_birth:
        payload["date_of_birth"] = date_of_birth
    if nationality:
        payload["nationality"] = nationality
    if document_number:
        payload["document_number"] = document_number
    if match_threshold is not None:
        payload["aml_match_score_threshold"] = match_threshold
    if approve_threshold is not None:
        payload["aml_score_approve_threshold"] = approve_threshold
    if review_threshold is not None:
        payload["aml_score_review_threshold"] = review_threshold
    if weights is not None:
        payload["aml_name_weight"], payload["aml_dob_weight"], payload["aml_country_weight"] = weights
    if include_adverse_media:
        payload["include_adverse_media"] = True
    if include_ongoing_monitoring:
        payload["include_ongoing_monitoring"] = True
    if not save_api_request:
        payload["save_api_request"] = False
    if vendor_data:
        payload["vendor_data"] = vendor_data
    if metadata is not None:
        payload["metadata"] = metadata

    headers = {"x-api-key": get_api_key(), "Content-Type": "application/json"}
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key

    # Adverse media can add about 30 seconds; keep the timeout well above 60 seconds.
    r = requests.post(ENDPOINT, headers=headers, json=payload, timeout=120)
    if not 200 <= r.status_code < 300:
        print(f"Error {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)
    return r.json()


def _parse_metadata(raw: str):
    if raw is None:
        return None
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        print(f"Error: --metadata is not valid JSON ({error}).", file=sys.stderr)
        sys.exit(1)
    if not isinstance(value, dict):
        print("Error: --metadata must be a JSON object.", file=sys.stderr)
        sys.exit(1)
    return value


def main():
    parser = argparse.ArgumentParser(description="Screen against AML watchlists via Didit")
    parser.add_argument("--name", required=True, help="Full name of the person or company (min 2 characters)")
    parser.add_argument("--dob", help="Date of birth or incorporation date (YYYY-MM-DD)")
    parser.add_argument("--nationality", help="ISO 3166-1 alpha-2 country code, e.g. US (alpha-3 is rejected)")
    parser.add_argument("--doc-number", help="Document number (golden key: an exact match sets match_score to 100)")
    parser.add_argument("--entity-type", default="person", choices=["person", "company"],
                        help="Entity type (default: person)")
    parser.add_argument("--match-threshold", "--threshold", dest="match_threshold", type=int,
                        help="aml_match_score_threshold 0-100 (default 93): hits below it are False Positive")
    parser.add_argument("--approve-threshold", type=float,
                        help="aml_score_approve_threshold 0-100 (default 80): score at or below it is Approved")
    parser.add_argument("--review-threshold", type=float,
                        help="aml_score_review_threshold 0-100 (default 100): score above it is Declined")
    parser.add_argument("--weights", type=int, nargs=3, metavar=("NAME", "DOB", "COUNTRY"),
                        help="Match-score weights, must sum to 100 (default: 60 25 15)")
    parser.add_argument("--adverse-media", action="store_true", help="Include adverse media (slower, about 30 s)")
    parser.add_argument("--ongoing-monitoring", action="store_true",
                        help="Enable ongoing monitoring (billed per profile per year; needs the request saved)")
    parser.add_argument("--no-save", action="store_true",
                        help="save_api_request=false: stateless check, nothing stored (not allowed with monitoring)")
    parser.add_argument("--vendor-data", help="Your identifier for the screened user")
    parser.add_argument("--metadata", help="JSON object stored with the request")
    parser.add_argument("--idempotency-key", help="Idempotency-Key header (max 255 characters) for safe retries")
    args = parser.parse_args()

    if args.nationality and len(args.nationality) != 2:
        parser.error("--nationality must be an ISO 3166-1 alpha-2 code, e.g. US or ES")
    if args.weights and sum(args.weights) != 100:
        parser.error("--weights must sum to 100")
    if args.ongoing_monitoring and args.no_save:
        parser.error("--ongoing-monitoring requires the request to be saved (drop --no-save)")

    result = screen_aml(args.name, args.dob, args.nationality.upper() if args.nationality else None,
                        args.doc_number, args.entity_type, args.match_threshold, args.approve_threshold,
                        args.review_threshold, tuple(args.weights) if args.weights else None,
                        args.adverse_media, args.ongoing_monitoring, not args.no_save,
                        args.vendor_data, _parse_metadata(args.metadata), args.idempotency_key)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    aml = result.get("aml") or {}
    print(f"\n--- Status: {aml.get('status')} | score: {aml.get('score')} | total hits: {aml.get('total_hits')} "
          f"| request_id: {result.get('request_id')} ---")
    for hit in (aml.get("hits") or [])[:5]:
        datasets = ", ".join(hit.get("datasets") or [])
        print(f"  match {hit.get('match_score')} | risk {hit.get('risk_score')} | {hit.get('review_status')} "
              f"| {hit.get('caption')} [{datasets}] (id {hit.get('id')})")


if __name__ == "__main__":
    main()
