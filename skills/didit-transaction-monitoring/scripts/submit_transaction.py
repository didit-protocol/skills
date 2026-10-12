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
        --vendor-data user-42 --subject-name "John Doe" --counterparty-name "Acme Energy"

    # Outbound crypto withdrawal with wallet screening
    python scripts/submit_transaction.py --txn-id wd-0001 --amount 0.25 --currency ETH --chain ETH \
        --vendor-data user-42 --subject-name "Jane Doe" --counterparty-name "Ana Diaz" \
        --wallet 0xBeneficiaryWallet01 --crypto

    # Travel Rule transfer to the user's own self-hosted wallet
    python scripts/submit_transaction.py --txn-id trv-0001 --amount 0.25 --currency ETH --chain ETH \
        --vendor-data user-42 --subject-name "Jane Doe" --counterparty-name "Jane Doe" \
        --wallet 0xJanesColdWallet01 --crypto --category travel_rule --unhosted

Notes:
    transaction_id must be new: reusing one returns 400 (or 409 on a race), never the
    existing transaction. Use the printed uuid for GET /v3/transactions/{uuid}/.
"""
import argparse
import json
import os
import sys

import requests

ENDPOINT = "https://verification.didit.me/v3/transactions/"
TRAVEL_RULE_CATEGORIES = ("travel_rule", "travelRule")


def get_api_key() -> str:
    api_key = os.environ.get("DIDIT_API_KEY")
    if not api_key:
        print("Error: DIDIT_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    return api_key


def build_payload(args: argparse.Namespace) -> dict:
    details = {"direction": args.direction, "amount": args.amount, "currency": args.currency}
    if args.action_type:
        details["action_type"] = args.action_type
    if args.crypto:
        details["currency_kind"] = "crypto"
    if args.chain:
        details["crypto_params"] = {"crypto_chain": args.chain.upper()}

    payload = {
        "transaction_id": args.txn_id,
        "transaction_category": args.category,
        "transaction_details": details,
        "subject": {
            "entity_type": args.entity_type,
            "vendor_data": args.vendor_data,
            "full_name": args.subject_name,
        },
    }
    if args.crypto:
        payload["include_crypto_screening"] = True

    if args.counterparty_name or args.wallet:
        counterparty = {"entity_type": "individual", "full_name": args.counterparty_name or args.subject_name}
        if args.wallet:
            counterparty["payment_method"] = {
                "method_type": "unhosted_wallet" if args.unhosted else "crypto_wallet",
                "account_id": args.wallet,
            }
        payload["counterparty"] = counterparty

    if args.category in TRAVEL_RULE_CATEGORIES and args.wallet:
        # status is required by the API; it is ignored when Travel Rule is enabled
        # (Didit drives the exchange) and stored as-is when Travel Rule is disabled.
        payload["travel_rule_details"] = {
            "status": "AWAITING_COUNTERPARTY",
            "beneficiary_data": {
                "wallet_address": args.wallet,
                "name": args.counterparty_name or args.subject_name,
            },
        }
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Submit a transaction to Didit for monitoring.")
    parser.add_argument("--txn-id", required=True, help="Your unique transaction identifier (max 128 chars)")
    parser.add_argument("--amount", required=True, help="Transaction amount, e.g. 1500.50")
    parser.add_argument("--currency", required=True, help="Currency code, e.g. EUR or ETH")
    parser.add_argument("--direction", default="outbound", choices=["inbound", "outbound"])
    parser.add_argument(
        "--category",
        default="finance",
        help="finance | kyc | travel_rule | user_event | audit_trail_event | gambling_bet | "
        "gambling_limit_change | gambling_bonus_change (default: finance)",
    )
    parser.add_argument("--action-type", help="Sub-type, e.g. deposit, withdrawal, transfer")
    parser.add_argument("--vendor-data", required=True, help="Your internal id for the subject user")
    parser.add_argument("--subject-name", required=True, help="Subject full name")
    parser.add_argument("--entity-type", default="individual", choices=["individual", "company"],
                        help="Subject entity type (default: individual)")
    parser.add_argument("--counterparty-name", help="Counterparty full name")
    parser.add_argument("--wallet", help="Counterparty wallet address (crypto)")
    parser.add_argument("--crypto", action="store_true", help="Mark as crypto and request screening")
    parser.add_argument("--chain", help="Network for screening, e.g. ETH, BTC, TRX, SOL, BASE, OP, ARB")
    parser.add_argument("--unhosted", action="store_true",
                        help="Declare the counterparty wallet self-hosted (Travel Rule)")
    args = parser.parse_args()

    response = requests.post(
        ENDPOINT,
        headers={"x-api-key": get_api_key(), "Content-Type": "application/json"},
        json=build_payload(args),
        timeout=60,
    )
    if not response.ok:
        print(f"Error {response.status_code}: {response.text}", file=sys.stderr)
        sys.exit(1)

    body = response.json()
    print(json.dumps(body, indent=2))

    travel_rule = body.get("travel_rule") or {}
    action = body.get("action_required") or {}
    print(
        f"\n--- uuid: {body.get('uuid')} | status: {body.get('status')} | score: {body.get('score')}"
        f" | travel_rule: {travel_rule.get('status')} | action_required: {action.get('type')} ---"
    )


if __name__ == "__main__":
    main()
