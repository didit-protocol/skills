#!/usr/bin/env python3
"""Didit Fraud Networks - List fraud networks, inspect one, or look up an entity's networks.

Usage:
    python scripts/list_networks.py [--org-id UUID --app-id UUID] <command> ...
    python scripts/list_networks.py list [--status active,in_review] [--signal-type device,ip_address]
                                         [--pattern-type exact_same_device] [--risk-band high]
                                         [--min-size 3] [--max-size 50] [--date-from 2026-09-01]
                                         [--date-to 2026-09-30] [--q TEXT] [--ordering=-risk_score]
                                         [--limit 100] [--offset 0]
    python scripts/list_networks.py get <network_uuid>
    python scripts/list_networks.py members <network_uuid>
    python scripts/list_networks.py lookup (--session-id ID | --business-session-id ID | --user-id ID |
                                            --business-id ID | --transaction-id ID [--party-id ID])

Environment:
    DIDIT_API_KEY - Required. The application's primary API key or a full-access named key.
    DIDIT_ORG_ID  - Organization UUID (or pass --org-id).
    DIDIT_APP_ID  - Application UUID of the key's own application (or pass --app-id).

Examples:
    python scripts/list_networks.py list --status active,in_review --risk-band high
    python scripts/list_networks.py list --signal-type device --min-size 3 --ordering=-last_activity_at
    python scripts/list_networks.py get 2b7e1f0c-4d3a-4e5b-9c6d-7e8f9a0b1c2d
    python scripts/list_networks.py members 2b7e1f0c-4d3a-4e5b-9c6d-7e8f9a0b1c2d
    python scripts/list_networks.py lookup --session-id 11111111-2222-4333-8444-555555555555
    python scripts/list_networks.py lookup --user-id 8c0e5a3e-1f7b-4d55-9a0e-6b2f0c7d9e11
    python scripts/list_networks.py lookup --transaction-id 3b9d2c1a-7e4f-4a6b-8c5d-0e1f2a3b4c5d \\
        --party-id b1111111-2222-4333-8444-555555555555
"""
import argparse
import json
import os
import sys
from collections import Counter

import requests

API_ROOT = "https://verification.didit.me/v3/organization"

ORDERINGS = [
    "risk_score", "-risk_score", "last_activity_at", "-last_activity_at",
    "first_activity_at", "-first_activity_at", "network_number", "-network_number",
]


def get_api_key() -> str:
    api_key = os.environ.get("DIDIT_API_KEY")
    if not api_key:
        print("Error: DIDIT_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    return api_key


def base_url(org_id: str, app_id: str) -> str:
    if not org_id or not app_id:
        print("Error: pass --org-id and --app-id, or set DIDIT_ORG_ID and DIDIT_APP_ID.", file=sys.stderr)
        sys.exit(1)
    return f"{API_ROOT}/{org_id}/application/{app_id}"


def get(url: str, params: dict = None) -> dict:
    r = requests.get(url, headers={"x-api-key": get_api_key()}, params=params, timeout=60)
    if r.status_code != 200:
        print(f"Error {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)
    return r.json()


def list_networks(base: str, args) -> dict:
    params = {"limit": args.limit, "offset": args.offset}
    optional = {
        "status": args.status,
        "signal_type": args.signal_type,
        "pattern_type": args.pattern_type,
        "risk_band": args.risk_band,
        "min_size": args.min_size,
        "max_size": args.max_size,
        "date_from": args.date_from,
        "date_to": args.date_to,
        "q": args.q,
        "ordering": args.ordering,
    }
    params.update({key: value for key, value in optional.items() if value is not None})
    return get(f"{base}/networks/", params)


def lookup_path(args) -> str:
    if args.party_id and not args.transaction_id:
        print("Error: --party-id needs --transaction-id.", file=sys.stderr)
        sys.exit(1)
    if args.session_id:
        return f"sessions/{args.session_id}/networks/"
    if args.business_session_id:
        return f"business-sessions/{args.business_session_id}/networks/"
    if args.user_id:
        return f"users/{args.user_id}/networks/"
    if args.business_id:
        return f"businesses/{args.business_id}/networks/"
    if args.party_id:
        return f"transactions/{args.transaction_id}/parties/{args.party_id}/networks/"
    return f"transactions/{args.transaction_id}/networks/"


def describe(network: dict) -> str:
    risk = network.get("risk") or {}
    return (f"{network.get('network_id')} [{network.get('status')}] risk {risk.get('score')} "
            f"({risk.get('band')}) signals: {', '.join(network.get('signal_types') or []) or '-'} "
            f"({network.get('uuid')})")


def summarize(command: str, data: dict) -> str:
    if command == "list":
        rows = data.get("results", [])
        lines = [f"--- {len(rows)} network(s) on this page | next offset: {data.get('next')} ---"]
        lines += [f"  {describe(network)}" for network in rows[:20]]
        return "\n".join(lines)
    if command == "get":
        return f"--- {describe(data)} | notes: {data.get('notes_count')} ---"
    if command == "members":
        rows = data.get("results", [])
        by_status = Counter(member.get("node_status") for member in rows)
        breakdown = ", ".join(f"{status}: {count}" for status, count in sorted(by_status.items())) or "-"
        return f"--- {len(rows)} member(s) | {breakdown} ---"
    rows = data.get("results", [])
    if not rows:
        return "--- Not in any network visible to this application ---"
    lines = [f"--- In {len(rows)} network(s) ---"]
    for membership in rows:
        lines.append(f"  {describe(membership.get('network') or {})} via "
                     f"{', '.join(membership.get('signal_types') or [])}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Inspect Didit fraud networks")
    parser.add_argument("--org-id", default=os.environ.get("DIDIT_ORG_ID"),
                        help="Organization UUID (default: $DIDIT_ORG_ID)")
    parser.add_argument("--app-id", default=os.environ.get("DIDIT_APP_ID"),
                        help="Application UUID of the key's application (default: $DIDIT_APP_ID)")
    sub = parser.add_subparsers(dest="command", required=True)

    list_p = sub.add_parser("list", help="List and filter networks")
    list_p.add_argument("--status", help="Comma-separated: active,in_review,resolved,dismissed "
                                         "(default: all but dismissed)")
    list_p.add_argument("--signal-type", help="Comma-separated: ip_address,device,face,document_number,"
                                              "phone,email,address")
    list_p.add_argument("--pattern-type", help="Comma-separated pattern types, e.g. exact_same_device,same_email")
    list_p.add_argument("--risk-band", help="Comma-separated: low,medium,high")
    list_p.add_argument("--min-size", type=int, help="Minimum member count")
    list_p.add_argument("--max-size", type=int, help="Maximum member count")
    list_p.add_argument("--date-from", help="ISO 8601 date or datetime (last activity on or after)")
    list_p.add_argument("--date-to", help="ISO 8601 date or datetime (first activity on or before)")
    list_p.add_argument("--q", help="Network name, member name, network id (N-0001) or pattern type")
    list_p.add_argument("--ordering", choices=ORDERINGS,
                        help="Write descending values with =, e.g. --ordering=-risk_score "
                             "(default: -risk_score, then -last_activity_at)")
    list_p.add_argument("--limit", type=int, default=100, help="Page size 1-500 (default: 100)")
    list_p.add_argument("--offset", type=int, default=0, help="Offset (default: 0)")

    get_p = sub.add_parser("get", help="Get one network")
    get_p.add_argument("network_uuid", help="Network UUID")

    members_p = sub.add_parser("members", help="List a network's members")
    members_p.add_argument("network_uuid", help="Network UUID")

    lookup_p = sub.add_parser("lookup", help="Networks a session, user, business, transaction or party belongs to")
    target = lookup_p.add_mutually_exclusive_group(required=True)
    target.add_argument("--session-id", help="Session ID (session_id)")
    target.add_argument("--business-session-id", help="Business session ID (session_id)")
    target.add_argument("--user-id", help="User didit_internal_id")
    target.add_argument("--business-id", help="Business didit_internal_id")
    target.add_argument("--transaction-id", help="Transaction uuid")
    lookup_p.add_argument("--party-id", help="With --transaction-id: a parties[].uuid of that transaction")

    args = parser.parse_args()
    base = base_url(args.org_id, args.app_id)

    if args.command == "list":
        result = list_networks(base, args)
    elif args.command == "get":
        result = get(f"{base}/networks/{args.network_uuid}/")
    elif args.command == "members":
        result = get(f"{base}/networks/{args.network_uuid}/members/")
    else:
        result = get(f"{base}/{lookup_path(args)}")

    print(json.dumps(result, indent=2))
    print(f"\n{summarize(args.command, result)}")


if __name__ == "__main__":
    main()
