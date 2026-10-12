---
name: didit-transaction-monitoring
description: >
  Integrate Didit Transaction Monitoring (KYT), crypto wallet screening, and the FATF / EU TFR
  Travel Rule. Use when the user wants to monitor transactions in real time, score transactions
  against AML/fraud rules, screen crypto wallets or transaction hashes against blockchain
  analytics, comply with the crypto Travel Rule (originator/beneficiary exchange with
  counterparty VASPs), verify self-hosted wallet ownership, mint SDK transaction tokens for
  client-side submission, or step up risky transactions with biometric re-verification using
  Didit. Pay-per-call $0.02 per transaction, no minimums.
version: 1.0.0
metadata:
  openclaw:
    requires:
      env:
        - DIDIT_API_KEY
    primaryEnv: DIDIT_API_KEY
    emoji: "📊"
    homepage: https://docs.didit.me
---

# Didit Transaction Monitoring & Travel Rule API

## Overview

Screens every transaction in real time against a configurable rule engine (velocity, thresholds, behavioral patterns, blocklists), automatically screens crypto wallets and hashes against blockchain analytics, and runs the full FATF / EU TFR Travel Rule exchange with counterparty VASPs.

**Key facts:**
- `POST /v3/transactions/` is synchronous: rules, screening, and Travel Rule routing all run inside the call - the response already carries the verdict.
- Transaction statuses: `APPROVED`, `IN_REVIEW`, `DECLINED`, `AWAITING_USER` (user must act - read `action_required`).
- Pricing: $0.02 per transaction; Travel Rule transfers bill a dedicated $0.02 line instead (outbound only); crypto screening bills separately (from $0.15 managed, $0.02 BYOK), charged once even when Travel Rule attribution needs the same lookup.
- `txn_id` is idempotent per application - resubmitting returns the existing transaction.
- Sandbox applications skip rules, webhooks, and billing.

**API Reference:** https://docs.didit.me/management-api/transactions/create
**Feature guides:** https://docs.didit.me/transaction-monitoring/overview · https://docs.didit.me/transaction-monitoring/travel-rule · https://docs.didit.me/transaction-monitoring/wallet-screening

---

## Authentication

All requests require the `x-api-key` header. Get your key from [Didit Business Console](https://business.didit.me) → API & Webhooks, or via programmatic registration (see below).

## Getting Started (No Account Yet?)

1. **Register:** `POST https://apx.didit.me/auth/v2/programmatic/register/` with `{"email": "you@gmail.com", "password": "MyStr0ng!Pass"}`
2. **Check email** for a 6-character OTP code
3. **Verify:** `POST https://apx.didit.me/auth/v2/programmatic/verify-email/` with `{"email": "you@gmail.com", "code": "A3K9F2"}` → response includes `api_key`

See the **didit-verification-management** skill for full platform management (workflows, sessions, users, billing).

---

## Create Transaction

`POST https://verification.didit.me/v3/transactions/`

Required: `transaction_id` (your unique id), `transaction_category`, `transaction_details` (`direction`, `amount`, `currency`), `subject` (`entity_type`, `vendor_data`, `full_name`).

Categories: `finance`, `kyc`, `travel_rule` (alias `travelRule`), `user_event`, `audit_trail_event`, `gambling_bet`, `gambling_limit_change`, `gambling_bonus_change`.

```bash
curl -X POST https://verification.didit.me/v3/transactions/ \
  -H "x-api-key: $DIDIT_API_KEY" -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "tx-0001",
    "transaction_category": "finance",
    "transaction_details": {"direction": "outbound", "amount": "1500.50", "currency": "EUR", "action_type": "withdrawal"},
    "subject": {"entity_type": "person", "vendor_data": "user-42", "full_name": "John Doe"},
    "counterparty": {"entity_type": "company", "full_name": "Acme Corp"},
    "custom_properties": {"order_id": "ORD-7891"}
  }'
```

Response essentials: `uuid` (Didit id, use in `GET /v3/transactions/{uuid}/`), `status`, `score` (0-100+), `severity`, `decision_reason_code`/`decision_reason_label`, `rule_runs[]`, `provider_results[]`, `travel_rule` (when applicable), `action_required`, `cost_breakdown`.

- `subject.vendor_data` links to the user's KYC profile - the same id you used for verification sessions. This powers velocity rules, entity aggregation, and stored-face reuse for step-up verification.
- camelCase aliases accepted: `txnId`, `type`, `info`, `applicant`, `props`, `travelRule`, `includeCryptoScreening`.
- Attach `subject.payment_method` / `counterparty.payment_method` (`method_type`, `account_id`, `issuing_country`); a counterparty `method_type: "unhosted_wallet"` declares a self-hosted wallet for Travel Rule.

## `action_required` (AWAITING_USER)

When a transaction needs the end user to act, the response (and every read + webhook) carries one of:

- `{"type": "verification_session", "url", "session_id", "session_token", "status"}` - a rule demanded step-up verification (e.g. biometric re-check against the face captured at KYC onboarding). Send the user to `url` or feed `session_token` to a Didit SDK.
- `{"type": "wallet_ownership", "url", "widget_session_id", "expires_at"}` - a Travel Rule transfer needs proof of wallet control. Open `url` in a real browser (never a mobile webview).

`action_required` returns to `null` once resolved; the transaction re-evaluates automatically and fires `transaction.status.updated`.

## Crypto screening

Runs automatically when `transaction_details.currency_kind: "crypto"` and monitoring is enabled (override per call with top-level `include_crypto_screening: true|false`).
Direction picks the screened wallet: inbound pre-transfer screens `counterparty.payment_method.account_id` (sender); outbound screens the destination in `counterparty.payment_method.account_id`. Include the on-chain hash in `transaction_details.payment_reference_id` for post-transfer screening.

**On-demand (no transaction):** `POST /v3/wallet-screening/` with `{"wallet_address": "0x...", "blockchain": "ETH"}` (chains: BTC, ETH, LTC, XRP, BCH, DOGE, TRX, SOL, MATIC, BNB, USDT, USDC). Returns `risk_score` (0-100), `severity`, `sanctions_hit`, `source_of_funds[]`, `destination_of_funds[]`, `counterparty_connections[]`. `409` = no provider configured.

## Travel Rule (FATF / EU TFR)

Enable once: `PUT /v3/travel-rule/settings/` with `{"is_enabled": true, "legal_name": "Your CASP SL", "jurisdiction": "EU"}` (partial update; `GET` the same path to read, including `networks` modes and your `travel_address`).

Send a transfer: create a transaction with `transaction_category: "travelRule"` and `travel_rule_details.beneficiary_data` (`wallet_address`, `name`, plus optional counterparty identifiers: `travel_address`, `counterparty_vasp_lei`, `counterparty_vasp_name`, `counterparty_vasp_email`, network ids). Didit routes over seven rails in priority order (INTERNAL → TRP → GTR → TRUST → VERIFYVASP → SYGNA → EMAIL), falling back to blockchain-analytics attribution of the destination wallet.

Transfer status lives at `travel_rule.status` (13 states). The ones that matter operationally:

| Status | Meaning / action |
|--------|------------------|
| `AWAITING_COUNTERPARTY` | Waiting on the counterparty VASP - do not settle yet. |
| `UNCONFIRMED_OWNERSHIP` | End user must prove wallet control (widget in `action_required`). |
| `COMPLETED` | Data matched - **safe to broadcast on-chain now**. |
| `FINISHED` | You reported the on-chain hash; exchange closed. |
| `COUNTERPARTY_VASP_NOT_FOUND` / `NOT_REACHABLE` / `NOT_ENOUGH_COUNTERPARTY_DATA` | Improve counterparty data, then resend. |
| `NOT_APPLICABLE` | Below your `threshold_amount` or Travel Rule disabled. |

**Never broadcast before `COMPLETED`.** Close out with `PATCH /v3/transactions/{uuid}/travel-rule/`:
- `{"payment_txn_id": "0xhash"}` → `FINISHED` (outbound + COMPLETED only)
- `{"action": "resend"}` → re-run routing (from the three unroutable states)
- `{"action": "cancel"}` → cancel any non-terminal transfer

Other Travel Rule endpoints (all `x-api-key`):
- `GET /v3/travel-rule/vasps/?search=<name>` - VASP directory with due-diligence scores + reachable rails.
- `GET|POST /v3/travel-rule/wallet-addresses/`, `PATCH|DELETE .../{entry_uuid}/` - the address book inbound INTERNAL-rail transfers resolve against (`self_declared: true` pre-verifies).
- `POST /v3/transactions/{uuid}/travel-rule/ownership/` with `{"confirmed": true|false}` - confirm/deny ownership (e.g. after screenshot review).
- `POST /v3/travel-rule/widget-session/` - mint a hosted wallet-ownership proof link (message signing, Satoshi test, screenshot, self-declaration); poll `GET /v3/travel-rule/widget/{token}/` for `completed_at`.
- `POST /v3/travel-rule/inbound/` - register an already-settled deposit (sunrise flow), dedupes on `txid` + `wallet_address`.

Full guide: https://docs.didit.me/transaction-monitoring/travel-rule

## SDK transaction tokens (client-side submission)

Mint on your backend: `POST /v3/transactions/sdk-token/` with `{"vendor_data": "user-42", "ttl_seconds": 900, "max_uses": 3}` → `{"sdk_token", "expires_at"}`.
The device then calls `POST /v1/transactions/` (and `GET /v1/transactions/{uuid}/`) with the `X-Transaction-Token` header - subject identity is enforced from the token, device intelligence is attached automatically, and the Didit SDKs wrap this as `submitTransaction`. Never ship an API key in an app.
Guide: https://docs.didit.me/transaction-monitoring/sdk-transaction-submission

## Webhooks

Subscribe via `POST /v3/webhook/destinations/` to:
- `transaction.created` - every submitted transaction (payload: `transaction_id`, `txn_id`, `status`, `score`, `severity`, `amount`, `currency`, `direction`, `action_required`).
- `transaction.status.updated` - every status change; fetch the full record for the reason.
- `travel_rule.status.updated` - every exchange transition (`travel_rule_status`, `rail`, `direction`).

Flat envelope with `webhook_type`, `event_id` (dedupe key), `timestamp`, `application_id`, `environment`; HMAC headers `X-Signature-V2` (recommended), `X-Signature`, `X-Signature-Simple`, `X-Timestamp`.

## Common Workflows

### Crypto withdrawal with Travel Rule (end to end)

1. `PUT /v3/travel-rule/settings/` once: `is_enabled: true` + `legal_name`.
2. `POST /v3/transactions/` with `transaction_category: "travelRule"`, crypto `transaction_details`, the user as `subject`, destination wallet as counterparty `payment_method` (`unhosted_wallet` if the user's own wallet), and `travel_rule_details.beneficiary_data`.
3. If `action_required.type == "wallet_ownership"`, send the user to its `url`.
4. Wait for `travel_rule.status == "COMPLETED"` (webhook or `GET /v3/transactions/{uuid}/`).
5. Broadcast on-chain, then `PATCH .../travel-rule/` with `payment_txn_id` → `FINISHED`.

### Step-up biometrics for high-value transactions

1. In the console (Transactions → Rules), create a rule: `amount gte 5000` → change status `AWAITING_USER` + select a Biometric Authentication workflow.
2. Submit transactions as usual; when the rule fires, `action_required.type == "verification_session"`.
3. Send the user to the session `url` - Didit face-matches a live selfie against the face verified at their KYC onboarding (same `vendor_data`), defeating stolen-credential ATO.
4. The transaction auto-resolves to `APPROVED`/`DECLINED`; `transaction.status.updated` fires.
