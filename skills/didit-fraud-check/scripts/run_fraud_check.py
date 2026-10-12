#!/usr/bin/env python3
"""Didit Fraud Check - Plan, run and read Fraud Checks.

Usage:
    python scripts/run_fraud_check.py plan [identifier flags] [options]
    python scripts/run_fraud_check.py run  [identifier flags] [options]
    python scripts/run_fraud_check.py get  <check_id>

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    # Quote email + phone risk before running anything (no charge)
    python scripts/run_fraud_check.py plan --email user@example.com --phone +14155552671 \
        --include email_risk,phone_risk --profile-version 2026-09-14.1

    # Run with an idempotency key; IP risk needs a public IP address
    python scripts/run_fraud_check.py run --email user@example.com --ip "$USER_PUBLIC_IP" \
        --include email_risk,ip_risk,networks_same_org --client-reference signup-001

    # Selfie to Brazilian CPF (profile 2026-09-14.2, consent required)
    python scripts/run_fraud_check.py run --tax-number 12345678909 --country BR \
        --selfie selfie.jpg --consent --include biometric_identity --profile-version 2026-09-14.2

    # Read a stored check
    python scripts/run_fraud_check.py get 6f1c2d3e-4a5b-4c6d-8e9f-0a1b2c3d4e5f
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys

import requests

BASE_URL = "https://verification.didit.me/v3/fraud/checks/"
PLAN_URL = BASE_URL + "plan/"

MODULES = [
    "normalization",
    "email_risk",
    "email_social",
    "phone_social",
    "phone_risk",
    "ip_risk",
    "database_validation",
    "networks_same_org",
    "networks_cross_org",
    "biometric_identity",
]

# (CLI flag dest, identifier type, needs issuing country)
IDENTIFIER_FLAGS = [
    ("email", "email", False),
    ("phone", "phone", False),
    ("national_id", "national_id", True),
    ("tax_number", "tax_number", True),
    ("passport_number", "passport_number", True),
    ("driving_licence_number", "driving_licence_number", True),
    ("residence_permit_number", "residence_permit_number", True),
    ("voter_id", "voter_id", True),
    ("external_id", "external_id", False),
]

ATTRIBUTE_FLAGS = [
    "first_name",
    "last_name",
    "full_name",
    "date_of_birth",
    "nationality",
    "gender",
    "address",
    "city",
    "state",
    "postal_code",
]


def get_api_key() -> str:
    api_key = os.environ.get("DIDIT_API_KEY")
    if not api_key:
        print("Error: DIDIT_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    return api_key


def parse_modules(value: str | None) -> list[str] | None:
    if value is None:
        return None
    modules = [item.strip() for item in value.split(",") if item.strip()]
    unknown = [module for module in modules if module not in MODULES]
    if unknown:
        print(f"Error: unknown module(s): {', '.join(unknown)}. Valid: {', '.join(MODULES)}", file=sys.stderr)
        sys.exit(1)
    return modules


def read_selfie(path: str) -> str:
    if not os.path.isfile(path):
        print(f"Error: selfie file not found: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path, "rb") as handle:
        return base64.b64encode(handle.read()).decode("ascii")


def build_body(args: argparse.Namespace) -> dict:
    identifiers = []
    for dest, identifier_type, needs_country in IDENTIFIER_FLAGS:
        for value in getattr(args, dest) or []:
            entry = {"type": identifier_type, "value": value}
            if needs_country:
                if not args.country:
                    print(f"Error: --country is required with --{dest.replace('_', '-')}.", file=sys.stderr)
                    sys.exit(1)
                entry["country"] = args.country
                if args.issuer:
                    entry["issuer"] = args.issuer
            identifiers.append(entry)

    subject: dict = {}
    if identifiers:
        subject["identifiers"] = identifiers
    attributes = {name: getattr(args, name) for name in ATTRIBUTE_FLAGS if getattr(args, name)}
    if attributes:
        subject["attributes"] = attributes
    if args.selfie:
        subject["selfie"] = read_selfie(args.selfie)

    body: dict = {}
    if subject:
        body["subject"] = subject

    context = {}
    if args.ip:
        context["ip_address"] = args.ip
    if args.user_agent:
        context["user_agent"] = args.user_agent
    if args.context_country:
        context["country"] = args.context_country
    if args.purpose:
        context["purpose"] = args.purpose
    if args.consent:
        context["consent_obtained"] = True
    if context:
        body["context"] = context

    checks = {}
    include = parse_modules(args.include)
    exclude = parse_modules(args.exclude)
    if include is not None:
        checks["include"] = include
    if exclude is not None:
        checks["exclude"] = exclude
    if checks:
        body["checks"] = checks

    if args.profile:
        body["profile"] = args.profile
    if args.profile_version:
        body["profile_version"] = args.profile_version
    if args.client_reference:
        body["client_reference"] = args.client_reference
    if args.vendor_data:
        body["vendor_data"] = args.vendor_data
    if args.metadata:
        try:
            body["metadata"] = json.loads(args.metadata)
        except json.JSONDecodeError as exc:
            print(f"Error: --metadata is not valid JSON: {exc}", file=sys.stderr)
            sys.exit(1)
    return body


def request(method: str, url: str, body: dict | None = None) -> dict:
    headers = {"x-api-key": get_api_key()}
    if body is not None:
        headers["Content-Type"] = "application/json"
    response = requests.request(method, url, headers=headers, json=body, timeout=90)
    if not 200 <= response.status_code < 300:
        retry_after = response.headers.get("Retry-After")
        suffix = f" (Retry-After: {retry_after}s)" if retry_after else ""
        print(f"Error {response.status_code}{suffix}: {response.text}", file=sys.stderr)
        sys.exit(1)
    return response.json()


def summarize_plan(result: dict) -> str:
    will_run = [m["module"] for m in result.get("modules", []) if m.get("will_run")]
    return (
        f"--- Plan {result.get('profile_id')}@{result.get('profile_version')} | "
        f"will run: {', '.join(will_run) or 'none'} | "
        f"estimated: {result.get('estimated_price')} {result.get('currency') or ''} | "
        f"can_afford: {result.get('can_afford')} | sandbox: {result.get('is_sandbox')} ---"
    )


def summarize_check(result: dict) -> str:
    bands = ", ".join(f"{r.get('dimension')}={r.get('band')}" for r in result.get("risk", []))
    return (
        f"--- Check {result.get('check_id')} | {result.get('recommendation')} / {result.get('next_action')} | "
        f"risk: {bands or 'n/a'} | reasons: {', '.join(result.get('decision_reasons') or []) or 'none'} ---"
    )


def add_body_arguments(parser: argparse.ArgumentParser) -> None:
    ids = parser.add_argument_group("identifiers (repeatable)")
    for dest, _, needs_country in IDENTIFIER_FLAGS:
        flag = "--" + dest.replace("_", "-")
        hint = " (needs --country)" if needs_country else ""
        ids.add_argument(flag, dest=dest, action="append", help=f"{dest} identifier value{hint}")
    ids.add_argument("--country", help="ISO alpha-2 or alpha-3 issuing country for government identifiers")
    ids.add_argument("--issuer", help="Issuing authority or sub-national issuer, when the country is not unique")

    attrs = parser.add_argument_group("claimed attributes")
    for name in ATTRIBUTE_FLAGS:
        help_text = "YYYY-MM-DD" if name == "date_of_birth" else None
        flag = "--dob" if name == "date_of_birth" else "--" + name.replace("_", "-")
        attrs.add_argument(flag, dest=name, help=help_text)
    attrs.add_argument("--selfie", help="Path to a JPEG, PNG or WebP selfie (<= 6 MB) for biometric_identity")

    ctx = parser.add_argument_group("context")
    ctx.add_argument("--ip", help="The attempt's public IP address")
    ctx.add_argument("--user-agent", help="The attempt's user agent")
    ctx.add_argument("--context-country", help="Country the subject claims to be in")
    ctx.add_argument("--purpose", help="Purpose of the check")
    ctx.add_argument("--consent", action="store_true", help="Set context.consent_obtained=true")

    opts = parser.add_argument_group("options")
    opts.add_argument("--include", help="Comma-separated modules to run")
    opts.add_argument("--exclude", help="Comma-separated modules to skip")
    opts.add_argument("--profile", help="Profile id (default: standard)")
    opts.add_argument("--profile-version", help="Pin a profile version, e.g. 2026-09-14.1")
    opts.add_argument("--client-reference", help="Your reference; also the idempotency key")
    opts.add_argument("--vendor-data", help="Your identifier for the user")
    opts.add_argument("--metadata", help="JSON value echoed back")


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan, run and read Didit Fraud Checks.")
    sub = parser.add_subparsers(dest="command", required=True)

    plan_parser = sub.add_parser("plan", help="Estimate a check without running it (no charge)")
    add_body_arguments(plan_parser)
    run_parser = sub.add_parser("run", help="Run a Fraud Check")
    add_body_arguments(run_parser)
    get_parser = sub.add_parser("get", help="Read a stored check")
    get_parser.add_argument("check_id", help="check_id returned by run")

    args = parser.parse_args()

    if args.command == "get":
        result = request("GET", f"{BASE_URL}{args.check_id}/")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("\n" + summarize_check(result))
        return

    body = build_body(args)
    if args.command == "run" and not body.get("subject", {}).get("identifiers"):
        print("Error: run needs at least one identifier (e.g. --email, --phone, --tax-number).", file=sys.stderr)
        sys.exit(1)
    if args.command == "plan":
        result = request("POST", PLAN_URL, body)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("\n" + summarize_plan(result))
    else:
        result = request("POST", BASE_URL, body)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("\n" + summarize_check(result))


if __name__ == "__main__":
    main()
