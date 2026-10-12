#!/usr/bin/env python3
"""Didit Transaction Monitoring - Submit a transaction for real-time rule evaluation.

Usage:
    python scripts/submit_transaction.py --txn-id tx-0001 --amount 1500.50 --currency EUR \
        --vendor-data user-42 --subject-name "John Doe"

Environment:
    DIDIT_API_KEY - Required. Your Didit API key.

Examples:
    # Plain finance transaction
    python scripts/submit_transaction.py --txn-id tx-0001 --amount 1500.50 --currency EUR \
        --vendor-data user-42 --subject-name "John Doe" --counterparty-name "Acme Corp"

    # Crypto withdrawal with wallet screening
    python scripts/submit_transaction.py --txn-id wd-0001 --amount 0.25 --currency ETH \
        --vendor-data user-42 --subject-name "Jane Doe" --counterparty-name "Ana Diaz" \
        --wallet 0xBeneficiaryWallet01 --crypto

    # Travel Rule transfer to a self-hosted wallet
    python scripts/submit_transaction.py --txn-id trv-0001 --amount 0.25 --currency ETH \
        --vendor-data user-42 --subject-name "Jane Doe" --counterparty-name "Jane Doe" \
        --wallet 0xJanesColdWallet01 --crypto --category travel_rule --unhosted
"""
import argparse
import json
import os
import sys

import requests

ENDPOINT = "https://verification.didit.me/v3/transactions/"


def get_api_key() -> str:
    api_key = os.environ.get("DIDIT_API_KEY")
    if not api_key:
        print("Error: DIDIT_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    return api_key


def main() -> None:
    parser = argparse.ArgumentParser(description="Submit a transaction to Didit for monitoring.")
    parser.add_argument("--txn-id", required=True, help="Your unique transaction identifier")
    parser.add_argument("--amount", required=True, help="Transaction amount, e.g. 1500.50")
    parser.add_argument("--currency", required=True, help="Currency code, e.g. EUR or ETH")
    parser.add_argument("--direction", default="outbound", choices=["inbound", "outbound"])
    parser.add_argument("--category", default="finance", help="finance | travel_rule | user_event | ...")
    parser.add_argument("--vendor-data", required=True, help="Your internal id for the subject user")
    parser.add_argument("--subject-name", required=True, help="Subject full name")
    parser.add_argument("--counterparty-name", help="Counterparty full name")
    parser.add_argument("--wallet", help="Counterparty wallet address (crypto)")
    parser.add_argument("--crypto", action="store_true", help="Mark as crypto and request screening")
    parser.add_argument("--unhosted", action="store_true", help="Declare the counterparty wallet self-hosted (Travel Rule)")
    args = parser.parse_args()

    details = {"direction": args.direction, "amount": args.amount, "currency": args.currency}
    if args.crypto:
        details["currency_kind"] = "crypto"

    payload = {
        "transaction_id": args.txn_id,
        "transaction_category": args.category,
        "transaction_details": details,
        "subject": {
            "entity_type": "person",
            "vendor_data": args.vendor_data,
            "full_name": args.subject_name,
        },
    }
    if args.crypto:
        payload["include_crypto_screening"] = True

    if args.counterparty_name or args.wallet:
        counterparty = {"entity_type": "person", "full_name": args.counterparty_name or args.subject_name}
        if args.wallet:
            counterparty["payment_method"] = {
                "method_type": "unhosted_wallet" if args.unhosted else "crypto_wallet",
                "account_id": args.wallet,
            }
        payload["counterparty"] = counterparty

    if args.category in ("travel_rule", "travelRule") and args.wallet:
        payload["travel_rule_details"] = {
            "beneficiary_data": {
                "wallet_address": args.wallet,
                "name": args.counterparty_name or args.subject_name,
            }
        }

    response = requests.post(
        ENDPOINT,
        headers={"x-api-key": get_api_key(), "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    body = response.json() if response.content else {}
    print(json.dumps(body, indent=2))

    if not response.ok:
        sys.exit(1)

    summary = {
        "uuid": body.get("uuid"),
        "status": body.get("status"),
        "score": body.get("score"),
        "travel_rule_status": (body.get("travel_rule") or {}).get("status"),
        "action_required": (body.get("action_required") or {}).get("type"),
    }
    print("\nSummary:", json.dumps(summary, indent=2), file=sys.stderr)


if __name__ == "__main__":
    main()
