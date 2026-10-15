---
name: didit-transaction-monitoring
description: >
  Integrate Didit Transaction Monitoring (KYT), crypto wallet screening, and the FATF / EU TFR
  Travel Rule. Use when the user wants to monitor transactions in real time, score transactions
  against AML/fraud rules, create, backtest or install monitoring rules by API, list or read
  monitored transactions, screen crypto wallets or transaction hashes against blockchain
  analytics, render a wallet-screening PDF, comply with the crypto Travel Rule
  (originator/beneficiary exchange with counterparty VASPs), verify self-hosted wallet
  ownership, register after-deposit (sunrise) transfers, mint SDK transaction tokens for
  client-side submission, or step up risky transactions with biometric re-verification using
  Didit. $0.02 per transaction.
version: 1.1.0
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

Scores every transaction in real time against a rule engine (conditions, velocity windows, blocklists), screens crypto wallets and transaction hashes against blockchain analytics, and runs the FATF / EU TFR Travel Rule exchange with counterparty VASPs.

**Key facts:**
- `POST /v3/transactions/` is synchronous: screening, Travel Rule routing and rules all run inside the call, so the `201` response already carries the verdict. A transaction is created `APPROVED`; rules may move it to `IN_REVIEW`, `DECLINED` or `AWAITING_USER`.
- `transaction_id` is unique per application. Reusing it is rejected (`400` with `{"transaction_id": "A transaction with this transaction_id already exists."}`, or `409` when two requests race); the existing transaction is never returned. After a timeout, treat that `400` as "already created" and find the record in `GET /v3/transactions/` instead of resubmitting.
- `GET /v3/transactions/{uuid}/` takes Didit's `uuid` from the create response, not your `transaction_id`.
- Sandbox applications store transactions but skip rules, crypto screening, webhooks and billing (they stay `APPROVED`).
- Non-monetary activity (logins, gameplay, bonuses, chargebacks) goes to the events API: see the **didit-event-monitoring** skill.

**Pricing:** $0.02 per transaction (Transaction Screening); a Travel Rule transfer is billed $0.02 per outbound transfer on its own line instead of the screening fee, never both; Wallet Verification & Screening (transaction-coupled or on-demand) from $0.15 with Didit-managed analytics, $0.02 with your own provider key, charged once even when Travel Rule attribution needs the same lookup. Sandbox is never billed. These are the list prices until 1 November 2026, when Didit pricing changes and the 500 free checks a month become $10 of free credit a month. Check [didit.me/pricing](https://didit.me/pricing) for current prices.

**API Reference:** https://docs.didit.me/management-api/transactions/create
**Feature guides:** https://docs.didit.me/transaction-monitoring/overview | https://docs.didit.me/transaction-monitoring/rules-api | https://docs.didit.me/transaction-monitoring/travel-rule | https://docs.didit.me/transaction-monitoring/wallet-screening

---

## Authentication

Every request needs the `x-api-key` header. Use your application's API key from the [Didit Business Console](https://business.didit.me) under **Developers > API keys**, or create an account and key programmatically (see Getting Started). Named keys with custom access need **Transactions** access (read for GET, write for POST, PUT, PATCH and DELETE); a key limited to some workflows or to approved sessions cannot have Transactions access.

Two exceptions: `GET /v3/travel-rule/widget/{token}/` takes no key (the token is the credential), and the device endpoints `/v1/transactions/` authenticate with `X-Transaction-Token` (see SDK transaction tokens).

## Getting Started (No Account Yet?)

If you don't have a Didit API key, create one in 2 API calls:

1. **Register:** `POST https://apx.didit.me/auth/v2/programmatic/register/` with `{"email": "you@yourdomain.com", "password": "MyStr0ng!Pass"}`
2. **Check email** for a 6-character verification code
3. **Verify:** `POST https://apx.didit.me/auth/v2/programmatic/verify-email/` with `{"email": "you@yourdomain.com", "code": "A3K9F2"}`. The key is in the response at `application.api_key`.

**To add credits:** `GET /v3/billing/balance/` to check, `POST /v3/billing/top-up/` with `{"amount_in_dollars": 50}` for a Stripe checkout link.

See the **didit-verification-management** skill for full platform management (workflows, sessions, users, billing).

---

## Endpoints

Base URL: `https://verification.didit.me`

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/v3/transactions/` | Submit a transaction (synchronous verdict) |
| `GET` | `/v3/transactions/` | List transactions, newest first (`limit`, default 50, and `offset`) |
| `GET` | `/v3/transactions/{uuid}/` | Full transaction detail |
| `POST` | `/v3/transactions/sdk-token/` | Mint a device token for `/v1/transactions/` |
| `GET`, `POST` | `/v3/transactions/rules/` | List / create rules |
| `GET`, `PATCH`, `DELETE` | `/v3/transactions/rules/{rule_uuid}/` | Read / update / delete a rule |
| `POST` | `/v3/transactions/rules/backtest/` | Evaluate a hypothetical rule against history |
| `GET` | `/v3/transactions/rules/library/` | Preset library with `is_installed` |
| `POST`, `DELETE` | `/v3/transactions/rules/install/` | Install / uninstall presets |
| `POST` | `/v3/wallet-screening/` | Screen one wallet, no transaction |
| `POST` | `/v3/wallet-screening/pdf/` | Render a screening result as PDF |
| `GET`, `PUT` | `/v3/travel-rule/settings/` | Travel Rule settings (PUT is partial) |
| `PATCH` | `/v3/transactions/{uuid}/travel-rule/` | Finish, cancel or resend a transfer |
| `POST` | `/v3/transactions/{uuid}/travel-rule/ownership/` | Confirm or deny wallet ownership |
| `GET`, `POST` | `/v3/travel-rule/wallet-addresses/` | Wallet address book |
| `PATCH`, `DELETE` | `/v3/travel-rule/wallet-addresses/{entry_uuid}/` | Update / delete an address entry |
| `GET` | `/v3/travel-rule/vasps/?search=` | VASP directory |
| `POST` | `/v3/travel-rule/inbound/` | Register an already-settled deposit (sunrise) |
| `POST` | `/v3/travel-rule/widget-session/` | Mint a wallet-ownership widget link |
| `GET` | `/v3/travel-rule/widget/{token}/` | Widget progress (no API key) |

---

## Create Transaction

`POST https://verification.didit.me/v3/transactions/`

### Body (JSON)

| Field | Type | Required | Notes |
|---|---|---|---|
| `transaction_id` | string | **Yes** | Your id, max 128 chars, unique per application. Alias `txnId`. |
| `transaction_category` | string | **Yes** | `finance`, `kyc`, `travel_rule`, `user_event`, `audit_trail_event`, `gambling_bet`, `gambling_limit_change`, `gambling_bonus_change`. camelCase also accepted: `travelRule`, `userPlatformEvent`, `auditTrailEvent`, `gamblingBet`, `gamblingLimitChange`, `gamblingBonusChange`. Alias key `type`. Multi-word values are echoed back camelCase in `transaction_type`. |
| `transaction_details.direction` | string | **Yes** | `inbound` / `outbound` (also `in` / `out`, any case). Echoed `INBOUND` / `OUTBOUND`. |
| `transaction_details.amount` | number or decimal string | **Yes** | Up to 18 decimals; send a string for exact precision. |
| `transaction_details.currency` | string | **Yes** | ISO 4217 code or crypto asset symbol. |
| `transaction_details.currency_kind` | string | No | `fiat` or `crypto`. `crypto` enables crypto screening. |
| `transaction_details.action_type` | string | No | e.g. `deposit`, `withdrawal`, `transfer`. Defaults to the category. |
| `transaction_details.payment_reference_id` | string | No | External reference; for crypto, the on-chain hash (switches to hash screening). |
| `transaction_details.crypto_params.crypto_chain` | string | No | Network for screening (`BTC`, `ETH`, `LTC`, `XRP`, `BCH`, `DOGE`, `TRX`, `SOL`, `MATIC`, `BNB`, `BASE`, `OP`, `ARB`; `LIGHTNING` only with a connected Elliptic or Chainalysis key). |
| `transaction_details.amount_in_default_currency`, `default_currency`, `payment_details` | | No | Pre-converted amount and its currency; free-text memo. |
| `subject.vendor_data` | string | **Yes** | Max 255 chars. Your user id: links the transaction to the same user profile your KYC sessions use (velocity, stored face for step-up). |
| `subject.full_name` | string | **Yes** | |
| `subject.entity_type` | string | No | `individual` (default) or `company`. |
| `subject.*` | | No | `first_name`, `last_name`, `date_of_birth` (YYYY-MM-DD), `address` (`country` ISO alpha-3, `town`, `state`, `street`, `post_code`), `institution_details`, `device_context`, `payment_method`. |
| `subject.payment_method` / `counterparty.payment_method` | object | No | `method_type` (`bank_card`, `bank_account`, `crypto_wallet`, `ewallet`, `unhosted_wallet`, `other`), `account_id` (IBAN, wallet address), `issuing_country`. |
| `counterparty` | object | No | Same shape as `subject`; nothing required. |
| `custom_properties` | object | No | Free key/values, readable in rules as `custom_values.<key>`. Alias `props`. |
| `travel_rule_details` | object | No | Alias `travelRule`. If sent, `status` is **required** (missing -> `400`). See Travel Rule. |
| `include_crypto_screening` | boolean | No | Per-call override of the application default (`null`/omitted = default). |
| `transaction_at`, `time_zone` | string | No | ISO timestamp (default now) and IANA zone. Aliases `txnDate`, `zoneId`. |

A subject or counterparty `vendor_data` on your user/business blocklist returns `400` (nothing is created). A blocklisted wallet, bank account, IP or device fingerprint is created and immediately `DECLINED` with `decision_reason_code: "blocklisted"`, before rules run.

### Example

```bash
curl -X POST https://verification.didit.me/v3/transactions/ \
  -H "x-api-key: $DIDIT_API_KEY" -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "tx-0001",
    "transaction_category": "finance",
    "transaction_details": {"direction": "outbound", "amount": "1500.50", "currency": "EUR", "action_type": "withdrawal"},
    "subject": {"entity_type": "individual", "vendor_data": "user-42", "full_name": "John Doe"},
    "counterparty": {"entity_type": "company", "full_name": "Acme Energy"},
    "custom_properties": {"order_id": "ORD-7891"}
  }'
```

```python
import os, requests

r = requests.post(
    "https://verification.didit.me/v3/transactions/",
    headers={"x-api-key": os.environ["DIDIT_API_KEY"]},
    json={
        "transaction_id": "tx-0001",
        "transaction_category": "finance",
        "transaction_details": {"direction": "outbound", "amount": "1500.50", "currency": "EUR"},
        "subject": {"vendor_data": "user-42", "full_name": "John Doe"},
    },
    timeout=60,
)
tx = r.json()
print(r.status_code, tx.get("uuid"), tx.get("status"), tx.get("score"))
```

### Response (201)

The full transaction detail (same shape as `GET /v3/transactions/{uuid}/`):

| Field | Notes |
|---|---|
| `uuid` | Didit id; use it in every follow-up path |
| `txn_id` | Your `transaction_id` |
| `transaction_type`, `action_type`, `direction` | As stored |
| `status` | `APPROVED`, `IN_REVIEW`, `DECLINED`, `AWAITING_USER` |
| `score`, `severity` | Rule score (typically 0-100); severity `UNKNOWN`/`LOW`/`MEDIUM`/`HIGH`/`CRITICAL` or `null` |
| `decision_reason_code`, `decision_reason_label` | Why the status is what it is |
| `amount`, `currency`, `currency_type`, `preferred_currency_amount`, `preferred_currency_code`, `payment_txn_id` | Amounts as decimal strings |
| `rule_runs[]`, `alerts[]`, `provider_results[]`, `tags[]`, `parties[]`, `payment_methods[]` | Evaluation detail; screening output is in `provider_results` |
| `travel_rule` | Short transfer object (`uuid`, `status`, `protocol`, `required`, `obligations_count`, `originator_data`, `beneficiary_data`, `metadata`) or `null` |
| `action_required` | Pending end-user action or `null` (below) |
| `cost_breakdown` | `total_price` and `items[]` |
| `environment` | `live` or `sandbox` |

## `action_required`

| `type` | When | Fields | What to do |
|---|---|---|---|
| `wallet_ownership` | Whenever the transaction's Travel Rule transfer has a pending (not completed, not expired) wallet-ownership widget session, whatever the transaction status | `url`, `widget_session_id`, `expires_at` | Open `url` in a real browser or custom tab, never a mobile webview |
| `verification_session` | Only while the transaction is `AWAITING_USER` and a rule created a remediation session | `url`, `session_id`, `session_token`, `status` | Send the user to `url` or start the session with `session_token` in a Didit SDK |

`wallet_ownership` wins when both apply. `action_required` returns to `null` once resolved. Remediation does not re-run rules: the session's decision sets the transaction status directly (`Approved` -> `APPROVED`, `Declined` -> `DECLINED`, `In Review` -> `IN_REVIEW`, with `decision_reason_code` `user_action_approved` / `user_action_declined` / `user_action_in_review`) and fires `transaction.status.updated`. An expired or abandoned session leaves the transaction `AWAITING_USER`.

## Crypto screening (transaction-coupled)

Runs when `transaction_details.currency_kind` is `crypto` and monitoring is on for the application (or `include_crypto_screening: true`); `false` skips it. The screened wallet depends on direction and on whether you send the on-chain hash in `payment_reference_id`:

| Direction | Before the transfer (no hash) | After the transfer (hash in `payment_reference_id`) |
|---|---|---|
| Inbound | Sender wallet in `counterparty.payment_method.account_id` | Hash scoped to **your deposit address** in `subject.payment_method.account_id` (missing -> `400`) |
| Outbound | Destination wallet in `counterparty.payment_method.account_id` | Hash scoped to `counterparty.payment_method.account_id` (missing -> `400`) |

Network: `transaction_details.crypto_params.crypto_chain`; without it the currency is used as the chain, and USDT/USDC default to Ethereum unless the hash identifies Tron or Solana. Always set it for tokens and never send `ETH` for another EVM chain. `LIGHTNING` without a connected Elliptic or Chainalysis key returns `400` before screening or billing. A created transaction is not proof of screening: check `provider_results`.

## Wallet Screening (on-demand)

`POST https://verification.didit.me/v3/wallet-screening/`: screens one address without creating a transaction. Needs a configured provider (**Transactions > Settings > Provider Preferences**), otherwise `409`.

| Field | Required | Notes |
|---|---|---|
| `wallet_address` | **Yes** | Must match the chain (e.g. `0x` + 40 hex for EVM). Alias `address`. |
| `blockchain` | **Yes** | `BTC`, `LIGHTNING`, `ETH`, `LTC`, `XRP`, `BCH`, `DOGE`, `TRX`, `SOL`, `MATIC`, `BNB`, `BASE`, `OP`, `ARB`, `USDT`, `USDC`. USDT/USDC are legacy aliases for Ethereum, not multi-chain searches. `LIGHTNING` needs a connected Elliptic or Chainalysis key (else `400`). Alias `currency`. |
| `direction` | No | `inbound`, `outbound`, `deposit`, `withdrawal`. Context only; does not change the score. |

Response `200`: `provider`, `screening_type` (`WALLET_SCREENING`), `risk_score` (0-100), `severity` (`0-9` UNKNOWN, `10-39` LOW, `40-69` MEDIUM, `70-89` HIGH, `90-100` CRITICAL; `UNKNOWN` is a band, never a pass), `status` (`SCREENED`, `PENDING`, `ERROR`: only `SCREENED` is a finished verdict, a `PENDING` result with score 0 is not clean), `summary`, `wallet_address`, `blockchain`, `sanctions_hit`, `pep_counterparty` (`null` = no PEP finding available), `dominant_risk_category`, `risk_factors[]` (top 5 drivers: `source`, `category`, `label`, `entity_name`, `direction`, `exposure_type`, `amount_usd`, `percentage`, `is_high_risk`, `description`), `source_of_funds[]`, `destination_of_funds[]`, `counterparty_connections[]`, `raw_response`, `report_signature`. Errors: `400` validation, `409` no provider, `502` provider failed (retry later). Billed once per successful screening.

**PDF:** `POST /v3/wallet-screening/pdf/` with the exact JSON the screening returned (including `report_signature`) returns `application/pdf` bytes. No provider call, no billing, nothing stored. A missing signature or any edited field returns `400`.

```bash
RESULT=$(curl -s -X POST https://verification.didit.me/v3/wallet-screening/ \
  -H "x-api-key: $DIDIT_API_KEY" -H "Content-Type: application/json" \
  -d '{"wallet_address": "0x94f1b9b64e2932f6a2db338f616844400cd58e8a", "blockchain": "ETH"}')
curl -X POST https://verification.didit.me/v3/wallet-screening/pdf/ \
  -H "x-api-key: $DIDIT_API_KEY" -H "Content-Type: application/json" \
  -d "$RESULT" -o wallet_screening_report.pdf
```

## Travel Rule (FATF / EU TFR)

### Settings

`GET` / `PUT /v3/travel-rule/settings/` (PUT is a partial update). Turning on `is_enabled` needs a non-blank `legal_name` (stored or in the same request), otherwise `400`.

| Field | Default | Notes |
|---|---|---|
| `is_enabled` | `false` | Managed exchange for `travelRule` transactions |
| `legal_name`, `lei`, `compliance_email` | `""` | Your VASP profile |
| `jurisdiction` | `"EU"` | Up to 8 chars; sets `custom_values.travel_rule_regime` |
| `threshold_amount` | `"0.00"` | Below it the transfer resolves to `NOT_APPLICABLE` (EU TFR has no minimum) |
| `name_matching_strictness` | `DEFAULT` | `NONE`, `STRICT`, `DEFAULT`, `FUZZY` |
| `confirmation_timeout_hours` | `48` | Min 1; then `AWAITING_COUNTERPARTY` -> `EXPIRED` |
| `timeout_outcome` | `HOLD` | On expiry: `HOLD` (review), `REJECT` (decline), `PROCEED` (untouched) |
| `inbound_auto_accept` | `true` | Auto-accept inbound transfers to a verified address-book entry with a name match |
| `auto_wallet_verification` | `true` | Auto-mint the ownership widget into `action_required` |
| `allow_screenshot_proof`, `allow_self_declaration` | `true` | Widget proof methods offered |
| `vasp_attribution_enabled` | `true` | Blockchain-analytics attribution when no rail resolves |
| `disabled_networks` | `[]` | `GTR`, `TRUST`, `VERIFYVASP`, `SYGNA` to skip over Didit's platform membership |
| `is_discoverable` | `true` | Listed in the VASP directory and reachable on the INTERNAL rail |
| `networks`, `travel_address` | | Read-only: per-network `{rail, mode, platform_available, connected}` (`mode` `own`/`didit`/`off`/`unavailable`) and your own travel address |

### Sending a transfer

Create a transaction with `transaction_category: "travelRule"` (or `travel_rule`) and `travel_rule_details`:
- `status` is required on every request. When Travel Rule is enabled it is ignored and Didit drives the exchange; send `"AWAITING_COUNTERPARTY"`. When Travel Rule is disabled, `travel_rule_details` is stored passively with the `status` you sent (current or legacy value), no rail runs.
- `beneficiary_data`: `wallet_address`, `name`, and optional routing fields `travel_address`, `counterparty_vasp_lei`, `counterparty_vasp_name`, `counterparty_vasp_email`, `counterparty_gtr_vasp_code`, `counterparty_trust_membership_id`, `counterparty_verifyvasp_id`, `counterparty_sygna_vasp_code`. `originator_data` is optional (IVMS 101-style, Latin script).
- A counterparty `payment_method.method_type: "unhosted_wallet"` declares a self-hosted wallet: no rail runs, the transfer starts in `UNCONFIRMED_OWNERSHIP` and (with `auto_wallet_verification`) the widget link lands in `action_required`.
- Otherwise rails run in priority order `INTERNAL` -> `TRP` -> `GTR` -> `TRUST` -> `VERIFYVASP` -> `SYGNA` -> `EMAIL`, then blockchain-analytics attribution re-runs them once.

```bash
curl -X POST https://verification.didit.me/v3/transactions/ \
  -H "x-api-key: $DIDIT_API_KEY" -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "trv-0001",
    "transaction_category": "travelRule",
    "transaction_details": {"direction": "outbound", "amount": "0.25", "currency": "ETH", "currency_kind": "crypto"},
    "subject": {"vendor_data": "user-42", "full_name": "Jane Doe"},
    "counterparty": {"full_name": "Ana Diaz", "payment_method": {"method_type": "crypto_wallet", "account_id": "0xBeneficiaryWallet01"}},
    "travel_rule_details": {
      "status": "AWAITING_COUNTERPARTY",
      "beneficiary_data": {"wallet_address": "0xBeneficiaryWallet01", "name": "Ana Diaz"}
    }
  }'
```

### Transfer status values (`travel_rule.status`)

| Status | Meaning / action |
|---|---|
| `AWAITING_COUNTERPARTY` | Sent; waiting on the counterparty VASP. Do not settle. |
| `UNCONFIRMED_OWNERSHIP` | Waiting on proof of wallet control (widget or `.../ownership/`). Not resendable. |
| `ON_HOLD` | Held for manual action (e.g. inbound with no matching address-book entry); the transaction shows `AWAITING_USER`. |
| `COMPLETED` | Data matched: **safe to broadcast on-chain now**. |
| `FINISHED` | Terminal. You reported the on-chain hash (outbound), or a sunrise deposit settled. |
| `CANCELLED` | Terminal. Cancelled with `action: "cancel"`. |
| `EXPIRED` | Terminal. `confirmation_timeout_hours` passed; `timeout_outcome` applied to the transaction. |
| `COUNTERPARTY_MISMATCHED_DATA` | Beneficiary name failed `name_matching_strictness`. |
| `COUNTERPARTY_VASP_GENERAL_DECLINE` | Counterparty declined or ownership was denied. |
| `COUNTERPARTY_VASP_NOT_FOUND` | No rail or attribution resolved a VASP. Resendable. |
| `COUNTERPARTY_VASP_NOT_REACHABLE` | VASP identified but its TRP endpoint failed. Resendable. |
| `NOT_ENOUGH_COUNTERPARTY_DATA` | Counterparty answered without enough data. Resendable. |
| `NOT_APPLICABLE` | Amount below `threshold_amount`, or the value you sent on a passive record. |

**Never broadcast before `COMPLETED`.** Then `PATCH /v3/transactions/{uuid}/travel-rule/`:
- `{"payment_txn_id": "0xhash"}` -> `FINISHED` (outbound and `COMPLETED` only, else `409`)
- `{"action": "resend"}` -> re-run routing (outbound, from the three resendable states, else `409`); improve counterparty data first
- `{"action": "cancel"}` -> cancel any non-terminal transfer (`409` if terminal)

The transaction's own `status` is separate (allow / hold / decline); the `travel_rule_eu_tfr` preset bundle moves it to review on mismatch, unverified self-hosted wallets (>= 1000 in default currency) and expiry.

### Receiving and wallet ownership

- **Address book:** `POST /v3/travel-rule/wallet-addresses/` with `address`, `chain`, `holder_name`, `holder_vendor_data`, `entity_type`, `travel_address`, `self_declared` (`true` creates it already verified). Duplicate `address` + `chain` -> `400`. `PATCH .../{entry_uuid}/` accepts `holder_name`, `holder_vendor_data`, `entity_type`, `travel_address`. `DELETE` deletes the entry (`204`). Matching is by address only.
- **Confirm ownership:** `POST /v3/transactions/{uuid}/travel-rule/ownership/` with `{"confirmed": true|false}` (beneficiary side, `UNCONFIRMED_OWNERSHIP` only, else `409`). `true` verifies the entry and runs the name match; `false` -> `COUNTERPARTY_VASP_GENERAL_DECLINE`. Inbound `originator_data`/`beneficiary_data` stay hidden until ownership is confirmed.
- **Widget:** `POST /v3/travel-rule/widget-session/` with `wallet_address`, `chain`, optional `holder_name`, `vendor_data`, `transaction_id` (Didit transaction uuid to advance), `satoshi_deposit_address` (enables Satoshi test), `callback_url`, `expires_in_minutes` (default 60, 5-10080) -> `{widget_session_id, token, url, expires_at}`. Open `url` verbatim in a browser. Poll `GET /v3/travel-rule/widget/{token}/` with no API key (`completed_at` non-null when verified; `404` unknown token, `410` expired) or wait for `travel_rule.status.updated`.
- **Sunrise (already-settled deposit):** `POST /v3/travel-rule/inbound/` with required `chain`, `txid`, `wallet_address`, `amount` (decimal string), `currency`, optional `originator_data`, `beneficiary_data`, `originating_vasp` (`{name, lei, travel_address}`). Dedupes on `txid` + `wallet_address`: `201` with `created: true` for a new inbound transaction, `200` with `created: false` when reused. Resolves to `ON_HOLD` (no entry), `UNCONFIRMED_OWNERSHIP`, `COUNTERPARTY_MISMATCHED_DATA`, or `COMPLETED` then `FINISHED`.
- **Directory:** `GET /v3/travel-rule/vasps/?search=<name>` (`limit` default 50, `offset`): `name`, `lei`, `jurisdiction`, `dd_status`, `dd_score`, `dd_score_breakdown`, `reachable_rails`, `is_didit_customer`.

## SDK transaction tokens (client-side submission)

Mint on your backend: `POST /v3/transactions/sdk-token/` with `vendor_data` (required), `ttl_seconds` (default 900, 60-86400), `max_uses` (>= 1; omit or `null` for unlimited within the TTL) -> `201 {"sdk_token", "expires_at"}`.
The device calls `POST https://verification.didit.me/v1/transactions/` and `GET /v1/transactions/{uuid}/` with header `X-Transaction-Token`. The subject is forced to the token's `vendor_data`, the server adds IP and user agent, and reads only return transactions of that `vendor_data`. A rejected token (missing, unknown, expired, over `max_uses`) is `401`. The Didit Web, iOS, Android, React Native and Flutter SDKs wrap this as `submitTransaction` and auto-launch `wallet_ownership` actions (see the **didit-sdk-integration** skill). Never ship an API key in an app.

## Rules API

Same rules as **Transactions > Rules** in the console. Create in `TEST`, backtest, then switch to `ACTIVE`. Rules never run on sandbox applications.

| Field | Notes |
|---|---|
| `title` | **Required**, unique per application (duplicate -> `400`) |
| `category` | **Required**, e.g. `finance`, `aml_ctf`, `crypto_monitoring`, `travel_rule` |
| `mode` | **Required**: `ACTIVE`, `TEST` (records runs, never changes score/status), `DISABLED` |
| `evaluation_mode` | `ALL` (default) or `ANY` for `conditions` |
| `scope` | `transaction_types`, `directions` (`INBOUND`/`OUTBOUND`), `action_types`; `record_types` (`["transaction"]` default, `["event"]`, or both) and `event_categories` for event rules |
| `conditions[]` | `{field, operator, value}`; operators `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `in`, `not_in`, `contains`, `not_contains`, `contains_any`, `regex`, `fuzzy_match` (needs `score`), `exists`, `not_exists` and aliases; optional `value_type` (`list`, `field`, `relative_date`) and `group_index` |
| `aggregation[]` | `{metric, field?, operator, value, window, filters}`; metrics `count`, `sum`, `avg`, `min`, `max`, `distinct_count`; window `<N>m`/`<N>h`/`<N>d`; `"__current__"` in filters means "same value as this transaction" |
| `actions[]` | `add_score` (`value`), `change_status` (`value` `APPROVED`/`IN_REVIEW`/`DECLINED`/`AWAITING_USER`; `AWAITING_USER` needs `workflow_id`), `add_tags`, `add_note`, `add_to_list` (`list_id`), `open_case` |

- `GET /v3/transactions/rules/` filters: `source` (`PRESET`/`CUSTOM`), `category`, `mode`, `bundle`, `search`, `ordering`, `limit`, `offset`.
- `PATCH .../rules/{rule_uuid}/`: custom rules accept every field; presets accept only `mode` (other fields -> `400`).
- `DELETE .../rules/{rule_uuid}/`: deletes a custom rule (`204`); a preset returns `400` (uninstall it instead).
- `POST .../rules/backtest/` with `conditions`, `aggregation`, `evaluation_mode` (default `ALL`), `scope`, `period_days` (default 90) -> `{evaluated, matched, affected_entities, period_days}`. Backtest the exact config you will activate.
- `GET .../rules/library/` (`bundle`, `category`, `search`) lists 150+ presets with `is_installed`. `POST .../rules/install/` with `{"library_keys": [...]}` or `{"bundle": "travel_rule_eu_tfr"}` -> `{installed_library_keys, installed_count}`; `DELETE` with the same body -> `{uninstalled_count}`. Neither key -> `400`.

```bash
curl -X POST https://verification.didit.me/v3/transactions/rules/ \
  -H "x-api-key: $DIDIT_API_KEY" -H "Content-Type: application/json" \
  -d '{
    "title": "High-value withdrawal step-up",
    "category": "finance",
    "mode": "TEST",
    "scope": {"directions": ["OUTBOUND"]},
    "conditions": [{"field": "preferred_currency_amount", "operator": "gte", "value": 5000}],
    "actions": [{"type": "change_status", "value": "AWAITING_USER", "workflow_id": "YOUR_BIOMETRIC_WORKFLOW_ID"}]
  }'
```

Cases opened by `open_case` are covered by the **didit-case-management** skill.

## Webhooks

Subscribe with `POST /v3/webhook/destinations/` (`subscribed_events`):
- `transaction.created` and `transaction.status.updated`: `transaction_id` (Didit uuid), `txn_id`, `status`, `score`, `severity`, `amount`, `currency`, `direction`, `action_required`. Fetch the full record for the reason.
- `travel_rule.status.updated`: `transaction_id`, `txn_id`, `travel_rule_status`, `rail`, `direction`.

Flat envelope with `webhook_type`, `event_id` (dedupe key, reused on retries), `timestamp`, `created_at`, `application_id`, `environment`; verify `X-Signature-V2` with `X-Timestamp`. Sandbox applications emit no transaction webhooks. Events have no webhooks.

## Error Responses

| Status | Meaning | Action |
|---|---|---|
| `400` | Invalid request: missing field, reused `transaction_id` (`{"transaction_id": "A transaction with this transaction_id already exists."}`), missing `travel_rule_details.status`, missing wallet for hash screening, blocklisted `vendor_data`, unsupported chain, edited PDF payload | Read the field errors in the response body |
| `401` | The API key has expired; or on `/v1/transactions/`, a missing, invalid, expired or used-up `X-Transaction-Token` | Rotate the key, or mint a new SDK token |
| `403` | Missing, wrong or revoked API key; a scoped key without access to this endpoint; a request from outside the key's IP allowlist; or not enough credits (transactions and wallet screening return `"code": "insufficient_credits"`) | Read the message in `detail` or `error`: fix the `x-api-key` header or the key's access, or top up |
| `404` | Unknown transaction, rule, address entry or widget token (or not a uuid) | Use the Didit `uuid` |
| `409` | Two creates with the same `transaction_id` raced; Travel Rule action not allowed in the current status; wallet screening with no provider configured | Re-read the record before retrying |
| `410` | Widget session expired | Mint a new widget session |
| `429` | Rate limit: 300 POST/PATCH/DELETE and 600 GET requests a minute per key | Wait the `Retry-After` seconds, then retry |
| `502` | Wallet screening provider failed | Retry later |

## Common Workflows

### Crypto withdrawal with Travel Rule (end to end)

1. `PUT /v3/travel-rule/settings/` once with `is_enabled: true` and `legal_name`.
2. `POST /v3/transactions/` with `transaction_category: "travelRule"`, crypto `transaction_details` (with `crypto_params.crypto_chain`), the user as `subject`, the destination as counterparty `payment_method` (`unhosted_wallet` if it is the user's own wallet), and `travel_rule_details` with `status` and `beneficiary_data`.
3. If `action_required.type == "wallet_ownership"`, send the user to its `url` in a browser.
4. Wait for `travel_rule.status == "COMPLETED"` (`travel_rule.status.updated` webhook or `GET /v3/transactions/{uuid}/`), and for a non-declined transaction `status`.
5. Broadcast on-chain, then `PATCH .../travel-rule/` with `payment_txn_id` -> `FINISHED`.

### Step-up biometrics for high-value transactions

1. Create a rule (Rules API or console) whose `change_status` action targets `AWAITING_USER` with a Biometric Authentication `workflow_id`; backtest, then `PATCH {"mode": "ACTIVE"}`.
2. Submit transactions as usual with the same `vendor_data` as the user's KYC; when the rule fires, `action_required.type == "verification_session"`.
3. Send the user to `url`: one live selfie is face-matched against the face verified at onboarding.
4. The session decision sets the transaction to `APPROVED`, `DECLINED` or `IN_REVIEW` and fires `transaction.status.updated`.

### Deposit screening after settlement

Send `direction: "inbound"`, `currency_kind: "crypto"`, the hash in `payment_reference_id`, your deposit address in `subject.payment_method.account_id`, and the network in `crypto_params.crypto_chain`; read `provider_results` and the transaction `status`.

## Utility Scripts

`scripts/submit_transaction.py` submits one transaction and prints the JSON plus a summary (`uuid`, `status`, `score`, `travel_rule.status`, `action_required.type`).

```bash
export DIDIT_API_KEY="your_api_key"

python scripts/submit_transaction.py --txn-id tx-0001 --amount 1500.50 --currency EUR \
    --vendor-data user-42 --subject-name "John Doe" --counterparty-name "Acme Energy" \
    --counterparty-entity-type company

# Outbound crypto withdrawal with wallet screening
python scripts/submit_transaction.py --txn-id wd-0001 --amount 0.25 --currency ETH --chain ETH \
    --vendor-data user-42 --subject-name "Jane Doe" --counterparty-name "Ana Diaz" \
    --wallet 0xBeneficiaryWallet01 --crypto

# Travel Rule transfer to the user's own self-hosted wallet
python scripts/submit_transaction.py --txn-id trv-0001 --amount 0.25 --currency ETH --chain ETH \
    --vendor-data user-42 --subject-name "Jane Doe" --counterparty-name "Jane Doe" \
    --wallet 0xJanesColdWallet01 --crypto --category travel_rule --unhosted
```
