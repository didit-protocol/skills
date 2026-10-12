---
name: didit-event-monitoring
description: >
  Integrate Didit Event Monitoring: send non-monetary activity events to the same rule engine
  that scores transactions. Use when the user wants to send logins, signups, failed logins,
  sessions, page views, gameplay rounds, bets, P2P settlements, bonus claims, affiliate
  attributions, deposit or withdrawal events, chargebacks and disputes, password or MFA
  changes, or self-exclusion registry checks to Didit; batch up to 500 events; capture events
  from a browser or mobile app with a scoped monitoring token instead of an API key; list,
  filter or read events and a user's event timeline; delete an event; or write velocity,
  ratio, sequence and correlation rules over events to detect account takeover, bonus abuse,
  multi-accounting, chip dumping, opposite betting, minimal-play laundering, friendly fraud
  and bot play using Didit.
version: 1.0.0
metadata:
  openclaw:
    requires:
      env:
        - DIDIT_API_KEY
    primaryEnv: DIDIT_API_KEY
    emoji: "📡"
    homepage: https://docs.didit.me
---

# Didit Event Monitoring API

## Overview

Events are everything your platform knows besides money movement: the login before a withdrawal, the poker hand that moved chips between two accounts, the bonus claimed twice, the chargeback a week later. Every category uses one envelope, every event is idempotent on your `event_id`, and events are evaluated by the same rule engine as transactions (rules opt in with `scope.record_types`).

**Key facts:**
- **Opt-in.** Turn it on in the Business Console under **Transactions > Settings > Event monitoring**. Until then every write (`POST /v3/events/`, `/v3/events/batch/`, `/v3/events/sdk-token/`, `/v1/events/`, `/v1/events/batch/`) returns `403` with `"code": "event_monitoring_disabled"` and nothing is stored. Reads are unaffected.
- **Two lanes, same records and rules.** Server lane `/v3/events/` with `x-api-key`; device lane `/v1/events/` with an `X-Monitoring-Token` minted by your backend (no API key in the browser or app).
- **Synchronous verdict.** The response carries `status` and `score`. Correlation rules and sequences longer than 24h run within minutes (`correlation_pending: true`), then update the event in place.
- **Same subject as transactions.** `subject.vendor_data` resolves to the same user (or business) record your KYC sessions and transactions use.
- No webhooks fire for events: read the response or the list endpoints.
- Money movement itself goes to `POST /v3/transactions/` (see the **didit-transaction-monitoring** skill).

**Pricing:** No list price is published for events; check [didit.me/pricing](https://didit.me/pricing).

**Guides:** https://docs.didit.me/transaction-monitoring/events | https://docs.didit.me/transaction-monitoring/sdk-event-submission | https://docs.didit.me/transaction-monitoring/event-rules | https://docs.didit.me/transaction-monitoring/rules-library

---

## Authentication

Every server-lane request needs the `x-api-key` header. Use your application's API key from the [Didit Business Console](https://business.didit.me) under **Developers > API keys**, or create an account and key programmatically (see Getting Started). Named keys with custom access need **Transactions** access (read for GET, write for POST and DELETE); a key limited to some workflows or to approved sessions cannot have Transactions access.

The device lane (`/v1/events/`) takes no API key: it uses the `X-Monitoring-Token` header (see Device lane).

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

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/v3/events/` | API key | One event from your backend |
| `POST` | `/v3/events/batch/` | API key | Up to 500 events |
| `POST` | `/v3/events/sdk-token/` | API key | Mint a scoped device credential |
| `POST` | `/v1/events/` | `X-Monitoring-Token` | One event from the device |
| `POST` | `/v1/events/batch/` | `X-Monitoring-Token` | A flushed device buffer (up to 500) |
| `GET` | `/v3/events/` | API key | List and filter events |
| `GET` | `/v3/events/{event_uuid}/` | API key | One event with its rule evidence |
| `GET` | `/v3/events/subjects/{vendor_data}/` | API key | One subject's timeline (`?entity_type=`) |
| `GET` | `/v3/events/enrichment-metrics/` | API key | IP-enrichment cache health |
| `DELETE` | `/v3/events/{event_uuid}/delete/` | API key | Delete one event (`204`) |

---

## Send an Event

`POST https://verification.didit.me/v3/events/`

### Headers

| Header | Value | Required |
|---|---|---|
| `x-api-key` | Your API key | **Yes** |
| `Content-Type` | `application/json` | **Yes** |

### Body (JSON)

| Field | Type | Required | Notes |
|---|---|---|---|
| `event_id` | string | **Yes** | Your id, max 128 chars, unique per application. The idempotency key. |
| `event_category` | string | **Yes** | `auth`, `session`, `gameplay`, `bonus`, `affiliate`, `payment`, `dispute`, `security`, `responsible_gambling`, `custom` |
| `action_type` | string | **Yes** | Open string, max 128 chars (see Categories) |
| `occurred_at` | ISO 8601 datetime | **Yes** | When it happened on your side: at most 7 days in the past, at most 5 minutes in the future |
| `subject.vendor_data` | string | **Yes** | Your user id, max 255 chars |
| `subject.entity_type` | string | No | `individual` (default) or `company`. Anything other than `company` is treated as `individual`. |
| `time_zone` | string | No | e.g. `UTC`, `Europe/Madrid` |
| `business.vendor_data` | string | No | The business the event belongs to |
| `session` | object | No | `session_id` (string), `sequence` (integer), `page_url`, `referrer` |
| `device_context` | object | No | `fingerprint` (string), `persistent_device_id` (string), `bot_score` (integer), `network_context.ip_address` (valid IPv4/IPv6). Wrong types return `400`. |
| `transaction_context` | object | No | `amount`, `currency`, `direction`, `payment_reference_id`. Its values also satisfy required payload keys. |
| `payload` | object | No | The category's domain fields, max 16 KB |
| `custom_values` | object | No | Max 100 keys, scalar values only; readable in rules as `custom_values.<key>` |

Send references and hashes, never raw secrets: no card numbers, full withdrawal addresses, password hashes or MFA secrets.

### Categories

| Category | Typical `action_type` values |
|---|---|
| `auth` | `signup`, `login`, `login_failed`, `logout`, `password_reset`, `mfa_reset`, `mfa_challenge` |
| `session` | `session_started`, `session_ended`, `page_view`, `sdk_loaded`, `sdk_heartbeat`, `device_seen`, `bot_signal_observed` |
| `gameplay` | `round_started`, `round_completed`, `bet_placed`, `bet_settled`, `cashout`, `limit_change`, `p2p_settlement` |
| `bonus` | `bonus_claimed`, `bonus_wagered`, `bonus_released`, `promotion_viewed` |
| `affiliate` | `affiliate_attributed`, `referral_clicked`, `campaign_joined`, `commission_event` |
| `payment` | `deposit_initiated`, `deposit_completed`, `withdrawal_requested`, `withdrawal_completed`, `withdrawal_address_changed`, `payment_instrument_seen` |
| `dispute` | `chargeback_opened`, `chargeback_won`, `chargeback_lost`, `refund_issued`, `payment_dispute_updated` |
| `security` | `login_attempt`, `login_succeeded`, `login_failed`, `password_changed`, `mfa_changed`, `credential_reset`, `country_changed`, `device_changed` |
| `responsible_gambling` | `self_exclusion_checked`, `self_exclusion_match`, `re_registration_attempt`, `limit_breach_attempt`, `registry_status_changed` |
| `custom` | Anything you define |

`auth` is the broad product category; `security` is the risk-grade lifecycle that account-takeover rules read.

### Required payload keys

Missing keys return `400`, e.g. `{"payload": "gameplay.p2p_settlement requires: role."}`. Keys may sit in `payload` or `transaction_context`.

| Action | Required |
|---|---|
| `gameplay.p2p_settlement` | `game_id`, `counterparty_vendor_data`, `stake_amount`, `net_result_amount`, `role`, and one of `hand_id` / `round_id` / `match_id` |
| `gameplay.bet_placed`, `gameplay.bet_settled` | `game_id` |
| `payment.deposit_initiated`, `payment.deposit_completed`, `payment.withdrawal_requested`, `payment.withdrawal_completed` | `payment_reference_id`, `amount`, `currency`, `payment_method`, `status` |
| `payment.withdrawal_address_changed` | `withdrawal_address_hash` |
| `dispute.chargeback_opened`, `chargeback_won`, `chargeback_lost` | `payment_reference_id`, and one of `dispute_id` / `chargeback_id` |
| `security.*_changed` | `changed_field`; account or payout-control changes (`password`, `mfa`, `mfa_method`, `email`, `phone`, `withdrawal_address`, `payout_method`, `api_key`) also need `previous_reference_hash` or `new_reference_hash` |
| `session.bot_signal_observed` | `telemetry_schema_version`, plus `bot_score` or one telemetry metric (`actions_per_minute`, `timing_variance_ms`, `pointer_entropy`, `keystroke_entropy`, `reaction_time_ms_p50`) |
| `responsible_gambling.self_exclusion_match` | `registry_source`, `exclusion_status`, `identity_match_ref` |

### Example

```bash
curl -X POST https://verification.didit.me/v3/events/ \
  -H "x-api-key: $DIDIT_API_KEY" -H "Content-Type: application/json" \
  -d '{
    "event_id": "login-2026-10-12-000001",
    "event_category": "security",
    "action_type": "login_failed",
    "occurred_at": "2026-10-12T20:40:31.123Z",
    "subject": {"entity_type": "individual", "vendor_data": "user_391"},
    "session": {"session_id": "web-session-abc", "sequence": 142},
    "device_context": {"fingerprint": "didit-fp-v2:a8c1", "network_context": {"ip_address": "203.0.113.42"}},
    "payload": {"method": "password"}
  }'
```

```python
import os, requests
from datetime import datetime, timezone

r = requests.post(
    "https://verification.didit.me/v3/events/",
    headers={"x-api-key": os.environ["DIDIT_API_KEY"]},
    json={
        "event_id": "chargeback-cb_921-opened",
        "event_category": "dispute",
        "action_type": "chargeback_opened",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "subject": {"vendor_data": "user_391"},
        "transaction_context": {"amount": "1000.00", "currency": "EUR", "payment_reference_id": "dep_735"},
        "payload": {"dispute_id": "disp_498", "chargeback_id": "cb_921", "reason_code": "fraudulent"},
    },
    timeout=30,
)
print(r.status_code, r.json())
```

### Response (`201` new, `200` replay)

```json
{
  "event_uuid": "0f2b...",
  "event_id": "login-2026-10-12-000001",
  "status": "ACCEPTED",
  "score": 0,
  "rules_evaluated_count": 6,
  "rules_matched_count": 0,
  "correlation_pending": false,
  "retention_class": "risk_relevant",
  "expires_at": "2027-01-10T20:40:31.123Z",
  "idempotent_replay": false,
  "rule_matches": []
}
```

| Field | Notes |
|---|---|
| `event_uuid` | Didit id for `GET` / `DELETE` |
| `status` | See Status values |
| `score` | Sum of matched rules' `add_score` |
| `rules_evaluated_count`, `rules_matched_count` | Event rules that ran / matched |
| `correlation_pending` | `true` while asynchronous rules still have to run |
| `retention_class`, `expires_at` | See Retention (`expires_at` is `null` for `monetary_or_compliance`) |
| `idempotent_replay` | `true` when this `event_id` was already stored with the same content |
| `rule_matches[]` | `rule_id`, `library_key`, `mode`, `is_async` per matched rule |

### Idempotency

- Same `event_id`, same content: `200`, `idempotent_replay: true`, the originally stored event. Retry freely.
- Same `event_id`, different content: `409` with `{"event_id": "event_id '<id>' already exists with a different payload."}`. Content means `event_category`, `action_type`, `occurred_at`, `subject.vendor_data` and `payload`.

Disputes are append-only: send a correction as a new `dispute` event with a new `event_id`.

## Batch

`POST /v3/events/batch/` with `{"events": [ ... ]}` (1 to 500 envelopes). Items are independent: a bad item never rolls back a good one. Returns `201` when every item landed, `207` when any was rejected. An empty list, a non-list or more than 500 items returns `400`.

```json
{
  "accepted_count": 2,
  "replayed_count": 0,
  "rejected_count": 1,
  "results": [
    {"index": 0, "event_id": "pv-1", "outcome": "rejected", "errors": {"occurred_at": ["This field is required."]}},
    {"index": 1, "outcome": "accepted", "event_uuid": "...", "event_id": "login-1", "status": "ACCEPTED", "score": 0},
    {"index": 2, "outcome": "accepted", "event_uuid": "...", "event_id": "cb-1", "status": "IN_REVIEW", "score": 80}
  ]
}
```

`outcome` is `accepted`, `replayed` or `rejected`; accepted and replayed items carry the full single-event response fields.

## Device Lane (browser and app)

1. **Mint on your backend:** `POST /v3/events/sdk-token/`

| Field | Default | Notes |
|---|---|---|
| `vendor_data` | required | Every event sent with the token belongs to this subject |
| `entity_type` | `individual` | `individual` or `company` |
| `allowed_event_categories` | all | List of categories the token may write; others are rejected with `400` |
| `ttl_seconds` | `900` | 60 to 86400 |
| `max_uses` | `1000` | One use per **event** (a 500-event batch spends 500) |
| `bind_to_origin` | none | When set, the request `Origin` header must match exactly; a request with no `Origin` (e.g. a native app) is refused |

Response `201`: `{"monitoring_token", "expires_at", "allowed_event_categories", "max_uses", "bind_to_origin"}`. Returns `403 event_monitoring_disabled` instead of a token while the feature is off.

2. **Send from the device:** `POST https://verification.didit.me/v1/events/` (or `/v1/events/batch/`) with header `X-Monitoring-Token` and the same envelope minus `subject`. The server overwrites `subject` with the token's binding and derives IP address, user agent and origin from the request; those server values win over client hints. `409` and `200` replay behave as on the server lane.

```typescript
const res = await fetch("https://verification.didit.me/v1/events/", {
  method: "POST",
  headers: { "X-Monitoring-Token": monitoringToken, "Content-Type": "application/json" },
  body: JSON.stringify({
    event_id: `session-abc-login-${Date.now()}`,
    event_category: "auth",
    action_type: "login",
    occurred_at: new Date().toISOString(),
    session: { session_id: "web-session-abc", sequence: 1 },
    device_context: { fingerprint: "didit-fp-v2:a8c1" },
    payload: { method: "password" },
  }),
});
```

No Didit SDK has an events method yet: send with plain HTTP (`fetch`, `URLSession`, OkHttp). `401` means the token was rejected: `Missing X-Monitoring-Token header.`, `Invalid monitoring token.`, `Monitoring token has expired.`, `Monitoring token exceeded its maximum number of uses.`, or `Monitoring token is not valid for this origin.` `X-Transaction-Token` is accepted only as a temporary header **name** alias and will be removed before general availability; a transaction SDK token value is rejected. Use `X-Monitoring-Token`.

**Flushing:** a good default is 25 events, 5 seconds, or page/app backgrounding. Under backpressure drop only `session.page_view`, `session.sdk_heartbeat`, `session.sdk_loaded`, `session.device_seen`, `session.bot_signal_observed`, `bonus.promotion_viewed`, `affiliate.referral_clicked` (list rows expose this as `is_droppable`); never drop `security`, `payment`, `dispute`, `responsible_gambling`, `gameplay.bet_placed`, `gameplay.bet_settled`, `gameplay.p2p_settlement`.

Use the server lane for payments, disputes, ledger-derived events and whenever no end user is present.

## Reading and Deleting Events

- `GET /v3/events/`: newest `occurred_at` first, `limit` / `offset` pagination (`count`, `next`, `previous`, `results`). Filters: `event_category`, `action_type`, `status`, `retention_class`, `subject_vendor_data`, `business_vendor_data`, `session_id`, `device_fingerprint`, `ip_address`, `game_id`, `round_id`, `affiliate_code`, `payment_reference_id`, `counterparty_vendor_data`, `matched_only`, `occurred_from`, `occurred_to`, `search`. Repeat a parameter for several values (`?status=IN_REVIEW&status=DECLINED`). Rows include `event_uuid`, `event_id`, `event_category`, `action_type`, `occurred_at`, `status`, `score`, `subject_vendor_data`, `retention_class`, `rules_matched_count`, `correlation_pending`, `is_droppable`.
- `GET /v3/events/subjects/{vendor_data}/?entity_type=company`: one subject's timeline with the same filters. `vendor_data` is unique only within an entity type; omitting `entity_type` returns the `individual` timeline.
- `GET /v3/events/{event_uuid}/`: adds `payload`, `custom_values`, `device_context`, `ip_enrichment`, `subject_profile` (cached email/phone risk signals), `tags`, `field_sources`, and `rule_runs[]` with each run's evidence (`matched_payload`) and the source of each matched field (`server`, `sdk`, `customer`).
- `GET /v3/events/enrichment-metrics/`: `events_ingested`, `enrichment_lookups`, `enrichment_cache_hits`, `enrichment_provider_calls`, `enrichment_skipped_low_value`, `unique_ips_seen`, `cache_hit_rate`, `unique_ip_ratio`, `provider_calls_per_1k_events`, `period_days`. IP enrichment runs once per unique IP, never per event.
- `DELETE /v3/events/{event_uuid}/delete/`: deletes the event (`204`); it is no longer returned by any read. Irreversible. Unknown uuid: `404`.

## Status Values

| Status | Meaning |
|---|---|
| `ACCEPTED` | Stored; no rule changed its standing (the normal answer) |
| `APPROVED` | A rule ran and the score stayed under your review threshold |
| `IN_REVIEW` | A rule pushed it over the review threshold or set the status |
| `DECLINED` | A rule declined it |

## Retention

| `retention_class` | Default hot retention | What lands here |
|---|---|---|
| `low_value` | 14 days | Page views, heartbeats, device-seen pings, bot telemetry, promotion views, referral clicks |
| `standard` | 30 days | Auth, session, gameplay, bonus, affiliate, custom |
| `risk_relevant` | 90 days | Security and responsible-gambling events, and any event a rule matched |
| `monetary_or_compliance` | Transaction retention | Payment and dispute events (never expired on the event schedule) |

Override the three expirable classes (1 to 730 days each) in **Transactions > Settings > Event monitoring**.

## Rules on Events

Event rules use the transaction Rules API (`/v3/transactions/rules/`, see the **didit-transaction-monitoring** skill) with the same fields, operators and actions. `scope.record_types` decides what a rule fires on:

| `scope.record_types` | Fires on |
|---|---|
| omitted or `["transaction"]` | Transactions only (default) |
| `["event"]` | Events only |
| `["transaction", "event"]` | Both |

Narrow further with `scope.event_categories` (the ten categories) and `scope.action_types`.

**Event fields** for `conditions`, aggregation `field` and `filters`:

| Group | Paths |
|---|---|
| Event | `event.category`, `event.action_type`, `event.occurred_at`, `event.amount`, `event.currency`, `event.direction`, `event.session_id`, `event.session_sequence` |
| Device and network | `event.device.fingerprint`, `event.device.persistent_device_id`, `event.device.bot_score`, `event.ip.address`, `event.ip.country`, `event.ip.asn_number`, `event.ip.asn_organization`, `event.ip.is_vpn_or_tor`, `event.ip.is_data_center`, `event.ip.proxy_type` |
| Gameplay | `event.gameplay.game_id`, `event.gameplay.table_id`, `event.gameplay.round_id`, `event.gameplay.hand_id`, `event.gameplay.match_id`, `event.gameplay.market_id`, `event.gameplay.side`, `event.gameplay.role`, `event.gameplay.counterparty_vendor_data`, `event.gameplay.net_result_amount` |
| Payment and dispute | `event.payment.reference_id`, `event.payment.payment_fingerprint`, `event.payment.instrument_reference_hash`, `event.payment.withdrawal_address_hash`, `event.dispute.dispute_id`, `event.dispute.chargeback_id` |
| Security, responsible gambling | `event.security.changed_field`, `event.responsible_gambling.identity_match_ref` |
| Bot telemetry (read from `payload`) | `event.bot.timing_variance_ms`, `event.bot.actions_per_minute`, `event.bot.pointer_entropy`, `event.bot.reaction_time_ms_p50`, `event.bot.assistance_indicator` |
| Subject signals | `subject.email.risk_score`, `subject.email.social_count`, `subject.email.is_disposable`, `subject.phone.risk_score`, `subject.phone.line_type`, `subject.phone.social_count` |
| Anything else | `event.payload.<key>`, `custom_values.<key>` |

Transaction fields such as `action_type`, `subject_vendor_data` and `subject_ip_country` also resolve on events.

**Aggregations** (`window` like `30m`, `24h`, `7d`; `"__current__"` = same value as the event being evaluated):

| `metric` | Shape | Use |
|---|---|---|
| `count`, `sum`, `avg`, `min`, `max`, `distinct_count` | `{metric, field?, operator, value, window, filters}` | Velocity |
| `ratio` | `numerator` and `denominator` reducers over one `window` | Wager-to-deposit, chargeback rate. No denominator events = never matches. |
| `sequence` | `key`, `window`, ordered `steps[]` (`event_category`, `action_type`, or `match`, optional `min_count`) | Ordered chains such as account takeover |
| `correlation` | `group_by[]`, `pair`, `filters`, `correlate` reducer | Cross-subject joins (chip dumping, opposite betting, self-referral). Always give narrowing `filters`. |

Velocity, ratio and sequences up to 24h run inside the request; correlation and longer sequences run asynchronously within minutes (`correlation_pending: true`), idempotently.

**Actions** are the transaction ones (`add_score`, `change_status`, `add_tags`, `add_note`, `add_to_list`, `open_case`), except: `change_status` to `AWAITING_USER` is applied as `IN_REVIEW` on events, and `open_case` links the case to the subject and records the event id (see the **didit-case-management** skill).

```json
{
  "title": "Failed login burst",
  "category": "anomaly_detection",
  "mode": "TEST",
  "scope": {"record_types": ["event"], "event_categories": ["security"]},
  "aggregation": [{
    "metric": "count", "operator": "gte", "value": 3, "window": "30m",
    "filters": {"subject_vendor_data": "__current__", "event.action_type": "login_failed"}
  }],
  "actions": [{"type": "add_score", "value": 40}, {"type": "change_status", "value": "IN_REVIEW"}]
}
```

**Presets:** the `igaming_fraud` library bundle ships 12 event rules (`igaming-account-takeover-drain`, `igaming-minimal-play-laundering`, `igaming-chargeback-deposit-ratio`, `igaming-chip-dumping-pair-net-winner`, `igaming-opposite-betting-same-market`, `igaming-bot-rta-cadence`, `igaming-self-exclusion-evasion`, `igaming-chat-rain-farming`, `igaming-repeated-bonus-claims-one-device`, `igaming-affiliate-self-referral`, `igaming-multi-accounting-device`, `igaming-shared-proxy-ip`). Install with `POST /v3/transactions/rules/install/` and `{"bundle": "igaming_fraud"}` or `{"library_keys": [...]}`. A rule whose required event fields are absent simply does not match.

## Error Responses

| Status | Meaning | Action |
|---|---|---|
| `400` | Invalid request: missing envelope field, `occurred_at` outside -7 days / +5 minutes, `payload` over 16 KB, `custom_values` over 100 keys or nested, missing required payload keys, category not allowed by the monitoring token, bad batch list | Read the field errors in the response body |
| `401` | The API key has expired; on `/v1/events/`, the monitoring token was missing, invalid, expired, used up or used from the wrong origin | Rotate the key, or mint a new monitoring token |
| `403` | `"code": "event_monitoring_disabled"` on any write while the feature is off. Otherwise: missing, wrong or revoked API key; a scoped key without access to this endpoint; a request from outside the key's IP allowlist; or not enough credits | Turn on **Transactions > Settings > Event monitoring**; otherwise read the message in `detail` or `error`: fix the `x-api-key` header or the key's access, or top up |
| `404` | Unknown `event_uuid` | Check the id |
| `409` | Same `event_id` with different content | Use a new `event_id`, or resend the original content |
| `429` | Rate limit: 300 POST/PATCH/DELETE and 600 GET requests a minute per key | Wait the `Retry-After` seconds, then retry |

Batch endpoints answer `207` (not an error) when some items were rejected: read `results[].errors`.

## Common Workflows

### Account-takeover drain

1. Send `security.login_failed`, `security.mfa_changed` (`changed_field: "mfa"` plus a reference hash), `payment.withdrawal_address_changed` (`withdrawal_address_hash`) and `payment.withdrawal_requested` events as they happen.
2. Install `igaming-account-takeover-drain` (or write a `sequence` rule over those four steps in `24h`).
3. The event that completes the chain comes back `DECLINED` with `score` raised; hold the payout in your system.

### Login and gameplay telemetry from the browser

1. Backend: `POST /v3/events/sdk-token/` with the user's `vendor_data`, `allowed_event_categories: ["auth", "session", "gameplay"]`, `bind_to_origin: "https://app.example.com"`.
2. Browser: buffer events and flush to `/v1/events/batch/` with `X-Monitoring-Token`; mint a new token before `expires_at` or when `max_uses` runs out (`401`).
3. Backend: send payments and chargebacks on the server lane; read verdicts with `GET /v3/events/?matched_only=true`.

### Minimal-play laundering check before a withdrawal

1. Send `payment.deposit_completed`, `gameplay.bet_placed` (with `amount`) and `payment.withdrawal_requested` events.
2. Use `igaming-minimal-play-laundering` or a `ratio` rule (sum of `bet_placed` amount over sum of `deposit_completed` amount, `lte 0.1`, `24h`).
3. Hold the withdrawal while the `withdrawal_requested` event is `IN_REVIEW`.

## Utility Scripts

`scripts/send_event.py` sends one server-lane event or mints a device token, then prints the JSON and a one-line summary.

```bash
export DIDIT_API_KEY="your_api_key"

python scripts/send_event.py send --event-id login-0001 --category security --action-type login_failed \
    --vendor-data user_391 --ip 203.0.113.42 --fingerprint didit-fp-v2:a8c1

python scripts/send_event.py send --event-id dep-735-completed --category payment --action-type deposit_completed \
    --vendor-data user_391 --amount 1000.00 --currency EUR --payment-reference-id dep_735 \
    --payload '{"payment_method": "card", "status": "completed"}'

python scripts/send_event.py token --vendor-data user_391 --categories auth,session,gameplay \
    --ttl 900 --max-uses 1000 --bind-to-origin https://app.example.com
```
