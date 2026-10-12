#!/usr/bin/env python3
"""Didit Case Management - List, inspect, create, resolve and annotate compliance cases.

Usage:
    python scripts/manage_cases.py [--org-id UUID --app-id UUID] <command> ...
    python scripts/manage_cases.py list[--status OPEN,AWAITING_USER] [--priority HIGH] [--source AML_SCREENING]
                                        [--search TEXT] [--tag TAG] [--blueprint UUID] [--assigned-to UUID]
                                        [--unassigned | --assigned] [--overdue] [--ordering due_at]
                                        [--limit 50] [--offset 0]
    python scripts/manage_cases.py get <case_uuid>
    python scripts/manage_cases.py create --title TITLE (--user UUID | --business UUID | --session UUID |
                                          --business-session UUID | --transaction UUID)
                                          [--priority LOW|MEDIUM|HIGH] [--blueprint UUID] [--due-at ISO]
                                          [--tag TAG ...] [--assigned-to UUID]
    python scripts/manage_cases.py resolve <case_uuid> --resolution FALSE_POSITIVE|VALID_THREAT [--note TEXT]
    python scripts/manage_cases.py note <case_uuid> --comment TEXT [--internal] [--tag TAG ...]
    python scripts/manage_cases.py stats [--date-from YYYY-MM-DD --date-to YYYY-MM-DD]

Environment:
    DIDIT_API_KEY - Required. The application's primary API key or a full-access named key.
    DIDIT_ORG_ID  - Organization UUID (or pass --org-id).
    DIDIT_APP_ID  - Application UUID of the key's own application (or pass --app-id).

Examples:
    python scripts/manage_cases.py list --status OPEN,AWAITING_USER --ordering due_at
    python scripts/manage_cases.py --org-id <org_uuid> --app-id <app_uuid> list --overdue
    python scripts/manage_cases.py get 6f1c2a9e-0b7d-4c3e-9a51-2d8e4f7b1c03
    python scripts/manage_cases.py create --title "Manual - Jane Doe" --user 8c0e5a3e-1f7b-4d55-9a0e-6b2f0c7d9e11
    python scripts/manage_cases.py create --title "Flagged payout" --transaction 3b9d2c1a-7e4f-4a6b-8c5d-0e1f2a3b4c5d
    python scripts/manage_cases.py resolve 6f1c2a9e-0b7d-4c3e-9a51-2d8e4f7b1c03 --resolution FALSE_POSITIVE --note "Verified"
    python scripts/manage_cases.py note 6f1c2a9e-0b7d-4c3e-9a51-2d8e4f7b1c03 --comment "Called the customer"
    python scripts/manage_cases.py stats --date-from 2026-09-01 --date-to 2026-09-30
"""
import argparse
import json
import os
import sys

import requests

API_ROOT = "https://verification.didit.me/v3/organization"


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


def call(method: str, url: str, params: dict = None, payload: dict = None, ok=(200,)) -> dict:
    headers = {"x-api-key": get_api_key()}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    r = requests.request(method, url, headers=headers, params=params, json=payload, timeout=60)
    if r.status_code not in ok:
        print(f"Error {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)
    return r.json()


def list_cases(base: str, args) -> dict:
    params = {"limit": args.limit, "offset": args.offset}
    optional = {
        "status__in": args.status,
        "priority": args.priority,
        "source__in": args.source,
        "search": args.search,
        "tag": args.tag,
        "blueprint": args.blueprint,
        "assigned_to": args.assigned_to,
        "ordering": args.ordering,
    }
    params.update({key: value for key, value in optional.items() if value})
    if args.unassigned:
        params["unassigned"] = "true"
    elif args.assigned:
        params["unassigned"] = "false"
    if args.overdue:
        params["overdue"] = "true"
    return call("GET", f"{base}/cases/", params=params)


def create_case(base: str, args) -> dict:
    payload = {"title": args.title}
    if args.user:
        payload["subject"] = {"type": "user", "uuid": args.user}
    elif args.business:
        payload["subject"] = {"type": "business", "uuid": args.business}
    links = []
    for entity_type, entity_uuid in (("session", args.session),
                                     ("business_session", args.business_session),
                                     ("transaction", args.transaction)):
        if entity_uuid:
            links.append({"entity_type": entity_type, "entity_uuid": entity_uuid})
    if links:
        payload["links"] = links
    if "subject" not in payload and not links:
        print("Error: give a subject (--user/--business) or a link (--session/--business-session/--transaction).",
              file=sys.stderr)
        sys.exit(1)
    if args.priority:
        payload["priority"] = args.priority
    if args.blueprint:
        payload["blueprint"] = args.blueprint
    if args.due_at:
        payload["due_at"] = args.due_at
    if args.tag:
        payload["tags"] = args.tag
    if args.assigned_to:
        payload["assigned_to"] = args.assigned_to
    return call("POST", f"{base}/cases/", payload=payload, ok=(201,))


def resolve_case(base: str, args) -> dict:
    payload = {"resolution": args.resolution}
    if args.note:
        payload["note"] = args.note
    return call("POST", f"{base}/cases/{args.case_uuid}/resolve/", payload=payload)


def add_note(base: str, args) -> dict:
    payload = {"comment": args.comment, "is_internal": args.internal}
    if args.tag:
        payload["tags"] = args.tag
    return call("POST", f"{base}/cases/{args.case_uuid}/notes/", payload=payload, ok=(200, 201))


def case_statistics(base: str, args) -> dict:
    params = {}
    if args.date_from and args.date_to:
        params = {"date_from": args.date_from, "date_to": args.date_to}
    elif args.date_from or args.date_to:
        print("Error: pass both --date-from and --date-to (or neither for the last 30 days).", file=sys.stderr)
        sys.exit(1)
    return call("GET", f"{base}/cases/statistics/", params=params)


def summarize(command: str, data: dict) -> str:
    if command == "list":
        rows = data.get("results", [])
        lines = [f"--- {len(rows)} case(s) on this page | more: {'yes' if data.get('next') else 'no'} ---"]
        for case in rows[:20]:
            lines.append(f"  {case.get('case_number')} [{case.get('status')}/{case.get('priority')}] "
                         f"{case.get('title')} ({case.get('uuid')})")
        return "\n".join(lines)
    if command in ("get", "create", "resolve"):
        staged = " | 4-eyes approval pending" if data.get("pending_resolution") else ""
        return (f"--- {data.get('case_number')} | status: {data.get('status')} | "
                f"resolution: {data.get('resolution')} | uuid: {data.get('uuid')}{staged} ---")
    if command == "note":
        return f"--- Note {data.get('uuid')} added at {data.get('created_at')} ---"
    if command == "stats":
        totals = data.get("totals", {})
        queue = data.get("queue", {})
        return (f"--- created: {totals.get('created')} | resolved: {totals.get('resolved')} | "
                f"open now: {queue.get('open')} | overdue now: {queue.get('overdue')} ---")
    return ""


def main():
    parser = argparse.ArgumentParser(description="Manage Didit compliance cases")
    parser.add_argument("--org-id", default=os.environ.get("DIDIT_ORG_ID"),
                        help="Organization UUID (default: $DIDIT_ORG_ID)")
    parser.add_argument("--app-id", default=os.environ.get("DIDIT_APP_ID"),
                        help="Application UUID of the key's application (default: $DIDIT_APP_ID)")
    sub = parser.add_subparsers(dest="command", required=True)

    list_p = sub.add_parser("list", help="List and filter cases")
    list_p.add_argument("--status", help="Comma-separated: OPEN,AWAITING_USER,RESOLVED")
    list_p.add_argument("--priority", help="Comma-separated: LOW,MEDIUM,HIGH")
    list_p.add_argument("--source", help="Comma-separated: MANUAL,AML_SCREENING,TRANSACTION_RULE,WORKFLOW_BUILDER")
    list_p.add_argument("--search", help="Title, case number, tag, subject name/ID, linked session or transaction ID")
    list_p.add_argument("--tag", help="Exact tag")
    list_p.add_argument("--blueprint", help="Blueprint UUID")
    list_p.add_argument("--assigned-to", help="Assignee user UUID")
    assignment = list_p.add_mutually_exclusive_group()
    assignment.add_argument("--unassigned", action="store_true", help="Only unassigned cases")
    assignment.add_argument("--assigned", action="store_true", help="Only assigned cases")
    list_p.add_argument("--overdue", action="store_true", help="Only overdue open/awaiting-user cases")
    list_p.add_argument("--ordering", choices=["created_at", "-created_at", "due_at", "-due_at"],
                        help="Write descending values with =, e.g. --ordering=-due_at (default: -created_at)")
    list_p.add_argument("--limit", type=int, default=50, help="Page size (default: 50)")
    list_p.add_argument("--offset", type=int, default=0, help="Offset (default: 0)")

    get_p = sub.add_parser("get", help="Get a case with notes, events, links and checklist")
    get_p.add_argument("case_uuid", help="Case UUID")

    create_p = sub.add_parser("create", help="Create a manual case")
    create_p.add_argument("--title", required=True, help="Case title (max 255 chars)")
    subject = create_p.add_mutually_exclusive_group()
    subject.add_argument("--user", help="User didit_internal_id (subject type user)")
    subject.add_argument("--business", help="Business didit_internal_id (subject type business)")
    create_p.add_argument("--session", help="Session ID to link")
    create_p.add_argument("--business-session", help="Business session ID to link")
    create_p.add_argument("--transaction", help="Transaction uuid to link")
    create_p.add_argument("--priority", choices=["LOW", "MEDIUM", "HIGH"])
    create_p.add_argument("--blueprint", help="Blueprint UUID")
    create_p.add_argument("--due-at", help="ISO 8601 deadline, e.g. 2026-11-01T00:00:00Z")
    create_p.add_argument("--tag", action="append", help="Tag (repeatable)")
    create_p.add_argument("--assigned-to", help="Member user UUID (see GET .../cases/reviewers/)")

    resolve_p = sub.add_parser("resolve", help="Resolve a case (stages it on 4-eyes blueprints)")
    resolve_p.add_argument("case_uuid", help="Case UUID")
    resolve_p.add_argument("--resolution", required=True, choices=["FALSE_POSITIVE", "VALID_THREAT"])
    resolve_p.add_argument("--note", help="Resolution note (required when the blueprint demands one)")

    note_p = sub.add_parser("note", help="Add a plain-text note to a case")
    note_p.add_argument("case_uuid", help="Case UUID")
    note_p.add_argument("--comment", required=True, help="Note text (max 10000 chars)")
    note_p.add_argument("--internal", action="store_true", help="Mark the note as internal")
    note_p.add_argument("--tag", action="append", help="Note tag (repeatable)")

    stats_p = sub.add_parser("stats", help="Case analytics (default: last 30 days)")
    stats_p.add_argument("--date-from", help="YYYY-MM-DD")
    stats_p.add_argument("--date-to", help="YYYY-MM-DD")

    args = parser.parse_args()
    base = base_url(args.org_id, args.app_id)

    if args.command == "list":
        result = list_cases(base, args)
    elif args.command == "get":
        result = call("GET", f"{base}/cases/{args.case_uuid}/")
    elif args.command == "create":
        result = create_case(base, args)
    elif args.command == "resolve":
        result = resolve_case(base, args)
    elif args.command == "note":
        result = add_note(base, args)
    else:
        result = case_statistics(base, args)

    print(json.dumps(result, indent=2))
    print(f"\n{summarize(args.command, result)}")


if __name__ == "__main__":
    main()
