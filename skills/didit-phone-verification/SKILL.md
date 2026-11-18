---
name: didit-phone-verification
description: >
  Integrate the Didit Phone Verification standalone API to verify phone numbers with a one-time
  code, and to risk-score a number without sending a code. Use when the user wants to send SMS,
  WhatsApp, Telegram, voice, RCS, Viber or Zalo codes, check phone verification codes, detect
  disposable or VoIP numbers, flag duplicate or blocklisted numbers, look up a number's carrier,
  line type or social footprint, or score phone risk with POST /v3/phone/risk/ using Didit.
  Supports automatic SMS fallback, branded SMS sender names, fraud signals, and per-call DECLINE
  policies.
version: 1.4.0
metadata:
  openclaw:
    requires:
      env:
        - DIDIT_API_KEY
    primaryEnv: DIDIT_API_KEY
    emoji: "📱"
    homepage: https://docs.didit.me
---

# Didit Phone Verification API

## Overview

Three standalone endpoints:

1. **Send** a one-time code to a phone number: `POST /v3/phone/send/`
2. **Check** the code the user typed and get the phone report: `POST /v3/phone/check/`
3. **Risk** (no code sent): score a number in one call: `POST /v3/phone/risk/`

**Key constraints (send + check):**
- Phone numbers in **E.164** (e.g. `+14155552671`). They are validated and normalized; invalid numbers return `400`.
- The check finds the verification by your application + the `phone_number`. It does not take `request_id`.
- A pending verification lives **5 minutes from the first send**. Retries do not extend it.
- **One retry** per pending verification: a second send for the same number inside the window returns `"Retry"` with the same `request_id` (2 sends in total). A further send starts a new verification with a new `request_id`.
- **3 code attempts** per verification. Wrong codes 1 and 2 return `"Failed"`; the 3rd wrong code finalizes it as `"Declined"` (`VERIFICATION_CODE_ATTEMPTS_EXCEEDED`).
- `code` must be **4-8 digits** (`^[0-9]{4,8}$`). Anything else returns `400` without using an attempt.
- Anti-abuse cap: **4 send attempts per phone number per hour** (`429`).
- No pending verification (never sent, already finalized, blocked at send, or older than 5 minutes): the check returns HTTP `200` with `status: "Expired or Not Found"`.
- Phone verification stays **disabled until your organization's first top-up** (`403`).
- Each new verification is stored as an API session: `request_id` works with `GET /v3/session/{sessionId}/decision/`, shows in the Business Console, and fires `status.updated` webhooks as it progresses.

**Delivery channels:** `options.preferred_channel` is `whatsapp` (default), `sms`, `telegram`, `voice`, `rcs`, `viber` or `zalo` (availability varies by country). When the preferred channel is unavailable for the number, delivery falls back to SMS and the send still reports `"Success"`; the channel that delivered is in `phone.verification_method` and in the send events of `phone.lifecycle` (`details.actual_channel`).

**Branding:** SMS codes carry your application's SMS sender name (set in the Business Console) at no extra cost. `options.sms_sender_name` signs one code with another name; `options.use_white_label_customization: true` uses your white-label public name when no sender name is set. WhatsApp codes use a fixed message and are not branded.

**Capabilities:** carrier name and line type, VoIP/virtual and disposable numbers, duplicates across your sessions (`matches[]`), your phone blocklist/allowlist, anti-fraud blocking at send, optional social footprint (`enable_social`), fraud signals.

**Sandbox:** sandbox API keys skip delivery, billing and persistence. Send returns a static `"Success"` with a random `request_id`; on check use code `123456` (any well-formed code returns a simplified `"Approved"` payload with a flat `phone` object). Risk returns deterministic approved data. Malformed input still returns `400`.

**Pricing:** Phone Verification $0.04 + carrier fee per message sent, by destination country and the channel that delivers it ([price table](https://docs.didit.me/getting-started/phone-verification-pricing)); every send except `"Blocked"` is billed, including `"Retry"`; checks are free (apart from the optional social add-on); standalone calls have no free tier. No list price is published for `POST /v3/phone/risk/` (the docs say it is lower than Phone Verification) or for the social footprint add-on (`enable_social`, billed per request on top of the endpoint price, not billed when the lookup could not complete). These are the list prices until 1 November 2026, when Didit pricing changes and the 500 free checks a month become $10 of free credit a month. Check [didit.me/pricing](https://didit.me/pricing) for current prices.

**API Reference:** [Send Code](https://docs.didit.me/standalone-apis/phone-send) | [Check Code](https://docs.didit.me/standalone-apis/phone-check) | [Phone Risk](https://docs.didit.me/standalone-apis/phone-risk)
**Feature Guide:** https://docs.didit.me/core-technology/phone-verification/overview

---

## Authentication

Every request needs the `x-api-key` header. Use your application's API key from the [Didit Business Console](https://business.didit.me) under **Developers > API keys**, or create an account and key programmatically (see Getting Started). Named keys with custom access need **Sessions** write to run standalone checks; a key limited to some workflows or to approved sessions cannot run them.

## Getting Started (No Account Yet?)

If you don't have a Didit API key, create one in 2 API calls:

1. **Register:** `POST https://apx.didit.me/auth/v2/programmatic/register/` with `{"email": "you@yourdomain.com", "password": "MyStr0ng!Pass"}`
2. **Check email** for a 6-character verification code
3. **Verify:** `POST https://apx.didit.me/auth/v2/programmatic/verify-email/` with `{"email": "you@yourdomain.com", "code": "A3K9F2"}`. The key is in the response at `application.api_key`.

**To add credits:** `GET /v3/billing/balance/` to check, `POST /v3/billing/top-up/` with `{"amount_in_dollars": 50}` for a Stripe checkout link.

See the **didit-verification-management** skill for full platform management (workflows, sessions, users, billing).

---

## Step 1: Send Phone Code

```
POST https://verification.didit.me/v3/phone/send/
```

### Headers

| Header | Value | Required |
|---|---|---|
| `x-api-key` | Your API key | **Yes** |
| `Content-Type` | `application/json` | **Yes** |

### Body (JSON)

| Parameter | Type | Required | Default | Constraints | Description |
|---|---|---|---|---|---|
| `phone_number` | string | **Yes** | - | E.164, max 20 | Phone number (e.g. `+14155552671`) |
| `options.code_size` | integer | No | `6` | 4-8 | Number of digits |
| `options.locale` | string | No | - | Max 5, BCP-47 (`^[a-z]{2,3}(-[A-Z]{2,3})?$`) | Message language, e.g. `en-US`, `fr`, `es` |
| `options.preferred_channel` | string | No | `"whatsapp"` | `whatsapp`, `sms`, `telegram`, `voice`, `rcs`, `viber`, `zalo` | Preferred channel; falls back to SMS when unavailable |
| `options.sms_sender_name` | string or null | No | your app's SMS sender name | 1-30 chars: letters, digits, spaces and `' & - !`, not only digits, single spaces | Name this code's SMS carries ("123456 is your verification code for Example Bank"). Invalid values return `400` and no code is sent. Each application can start using up to two new names per day (UTC); past that the app's name is used. Free |
| `options.use_white_label_customization` | boolean | No | `false` | - | Without an SMS sender name, sign the SMS with your white-label public name |
| `signals.ip` | string | No | - | IPv4 or IPv6 | End user's IP for fraud detection |
| `signals.device_id` | string | No | - | Max 255 | Android `ANDROID_ID`, iOS `identifierForVendor` |
| `signals.device_platform` | string | No | - | `android`, `ios`, `ipados`, `tvos`, `web` | Device platform |
| `signals.device_model` | string | No | - | Max 255 | e.g. `iPhone17,2` |
| `signals.os_version` | string | No | - | Max 64 | e.g. `18.0.1` |
| `signals.app_version` | string | No | - | Max 64 | e.g. `1.2.34` |
| `signals.user_agent` | string | No | - | Max 512 | Browser or app user agent |
| `vendor_data` | string | No | - | - | Your user id. Stored on the session (from the first send) and echoed in send, check and webhooks |
| `metadata` | object | No | `null` | JSON object | Free-form data stored on the session and echoed back |

### Example

```python
import requests

response = requests.post(
    "https://verification.didit.me/v3/phone/send/",
    headers={"x-api-key": "YOUR_API_KEY", "Content-Type": "application/json"},
    json={
        "phone_number": "+14155552671",
        "options": {"preferred_channel": "sms", "code_size": 6, "sms_sender_name": "Example Bank"},
        "signals": {"ip": "203.0.113.42", "device_platform": "ios"},
        "vendor_data": "user-1234",
    },
    timeout=30,
)
print(response.status_code, response.json())
```

```typescript
const response = await fetch("https://verification.didit.me/v3/phone/send/", {
  method: "POST",
  headers: { "x-api-key": "YOUR_API_KEY", "Content-Type": "application/json" },
  body: JSON.stringify({
    phone_number: "+14155552671",
    options: { preferred_channel: "whatsapp", code_size: 6, locale: "en-US" },
    vendor_data: "user-1234",
  }),
});
const data = await response.json(); // { request_id, status, reason, vendor_data, metadata }
```

### Response (200 OK)

```json
{
  "request_id": "e39cb057-92fc-4b59-b84e-02fec29a0f24",
  "status": "Success",
  "reason": null,
  "vendor_data": "user-1234",
  "metadata": null
}
```

### Status Values & Handling

| Status | Meaning | Action |
|---|---|---|
| `"Success"` | Code sent for a new verification (possibly by SMS fallback) | Wait for the user's code, then call Check |
| `"Retry"` | Second send inside the 5-minute window: code re-sent for the same pending verification, same `request_id` (billed) | Wait for the code, then call Check |
| `"Blocked"` | The anti-fraud layer refused to send. `reason` says why (e.g. `suspicious`, `spam`). Not billed. The verification is finalized at once (`Declined` with `HIGH_RISK_PHONE_NUMBER`, or `In Review` for an allowlisted number), so a later check returns `"Expired or Not Found"` | Do not retry the same number; ask for another number or review |

### Error Responses

| Code | Meaning | Action |
|---|---|---|
| `400` | Invalid request | Read the field errors in the response body. A number that parses but cannot receive a code returns `{"detail": "Invalid phone number provided."}` or `{"detail": "Invalid phone line type provided."}` (e.g. a short code) |
| `401` | The API key has expired | Rotate it or create a new key in **Developers > API keys** |
| `403` | Missing, wrong or revoked API key; a scoped key without access to this endpoint; a request from outside the key's IP allowlist; or not enough credits | Read the message in `detail` or `error`: fix the `x-api-key` header or the key's access, or top up |
| `429` | Rate limit: 300 POST/PATCH/DELETE and 600 GET requests a minute per key | Wait the `Retry-After` seconds, then retry |
| `502` | Phone provider temporarily unavailable: `{"detail": "...", "code": "phone_provider_unavailable"}` | Retry with a short backoff. Nothing billed, no attempt used |

Phone-specific cases: `403` with a `detail` saying phone verification is disabled until your organization's first top-up (sandbox applications can still test it for free), and `403` with `error` when the balance cannot cover the destination's send price. A `429` for too many attempts on the same number (4 an hour) carries no `Retry-After` header: wait, or use a different number.

---

## Step 2: Check Phone Code

Verifies the code and returns the phone report. **Call Send first**, with the same `phone_number`.

```
POST https://verification.didit.me/v3/phone/check/
```

Headers: same as Step 1.

### Body (JSON)

| Parameter | Type | Required | Default | Values | Description |
|---|---|---|---|---|---|
| `phone_number` | string | **Yes** | - | E.164 | Same number used in Step 1 (this links check to send) |
| `code` | string | **Yes** | - | 4-8 digits | The code the user received |
| `duplicated_phone_number_action` | string | No | `"NO_ACTION"` | `"NO_ACTION"` / `"DECLINE"` | Number already used by a different user (different `vendor_data`) of your application |
| `disposable_number_action` | string | No | `"NO_ACTION"` | `"NO_ACTION"` / `"DECLINE"` | Temporary or burner number (`phone.is_disposable`) |
| `voip_number_action` | string | No | `"NO_ACTION"` | `"NO_ACTION"` / `"DECLINE"` | Virtual line: `voip`, `isp` or `vpn` (`phone.is_virtual`) |
| `enable_social` | boolean | No | `false` | - | Also look up the number's social footprint (adds `phone.phone_social`; billed per request as an add-on) |
| `phone_no_social_presence_action` | string | No | `"NO_ACTION"` | `"NO_ACTION"` / `"DECLINE"` | Decline when the social footprint check finds the number on no platform (`profiles_registered: 0`). Needs `enable_social: true` |

> **Policy note:** `DECLINE` turns a correct code into `"Declined"` when the risk is found. `NO_ACTION` records the risk in `phone.warnings` (log type `information`) without changing the status. Blocklisted numbers always decline. Only `NO_ACTION` and `DECLINE` are accepted here.

### Example

```python
response = requests.post(
    "https://verification.didit.me/v3/phone/check/",
    headers={"x-api-key": "YOUR_API_KEY", "Content-Type": "application/json"},
    json={
        "phone_number": "+14155552671",
        "code": "123456",
        "disposable_number_action": "DECLINE",
        "voip_number_action": "DECLINE",
    },
    timeout=30,
)
result = response.json()
if result["status"] in ("Approved", "Declined"):
    print(result["phone"]["carrier"], result["phone"]["is_virtual"])
```

```typescript
const response = await fetch("https://verification.didit.me/v3/phone/check/", {
  method: "POST",
  headers: { "x-api-key": "YOUR_API_KEY", "Content-Type": "application/json" },
  body: JSON.stringify({
    phone_number: "+14155552671",
    code: "123456",
    voip_number_action: "DECLINE",
  }),
});
const result = await response.json(); // inspect result.status, not the HTTP code
```

### Response (200 OK)

```json
{
  "request_id": "e39cb057-92fc-4b59-b84e-02fec29a0f24",
  "status": "Approved",
  "message": "The verification code is correct.",
  "phone": {
    "status": "Approved",
    "phone_number_prefix": "+1",
    "phone_number": "4155552671",
    "full_number": "+14155552671",
    "country_code": "US",
    "country_name": "United States",
    "carrier": {"name": "Example Mobile", "type": "mobile"},
    "is_disposable": false,
    "is_virtual": false,
    "verification_method": "whatsapp",
    "verification_attempts": 1,
    "verified_at": "2026-06-12T01:24:47.311323Z",
    "warnings": [],
    "lifecycle": [
      {"type": "PHONE_VERIFICATION_MESSAGE_SENT", "timestamp": "2026-06-12T01:23:39.580554+00:00", "details": {"status": "Success", "reason": null, "channel": "whatsapp", "actual_channel": "whatsapp"}, "fee": 0.0709},
      {"type": "PHONE_DELIVERY_DELIVERED", "timestamp": "2026-06-12T01:23:43.118220+00:00", "details": {"channel": "whatsapp", "status": "delivered"}, "fee": 0},
      {"type": "VALID_CODE_ENTERED", "timestamp": "2026-06-12T01:24:47.311201+00:00", "details": {"code_tried": "123456", "status": "Approved"}, "fee": 0},
      {"type": "PHONE_VERIFICATION_APPROVED", "timestamp": "2026-06-12T01:24:47.384292+00:00", "details": null, "fee": 0}
    ],
    "matches": []
  },
  "vendor_data": "user-1234",
  "metadata": null,
  "created_at": "2026-06-12T01:24:47.401719+00:00"
}
```

A wrong code with attempts left returns `"status": "Failed"`, `"message": "The verification code is incorrect. Attempts remaining: 2"` and `"phone": null`.

### Status Values & Handling

| Status | Meaning | `request_id` / `phone` | Action |
|---|---|---|---|
| `"Approved"` | Correct code, no declining risk | Session id of the send / full report | Phone verified, proceed |
| `"Declined"` | Terminal: correct code but a declining risk matched (a `DECLINE` action, blocklisted or high-risk number), or the 3rd wrong code | Session id of the send / full report | Read `phone.warnings`; block or ask for another number |
| `"Failed"` | Wrong code, attempts remaining (`message` says how many) | One-off UUID / `null` | Ask the user to re-enter the code |
| `"Expired or Not Found"` | No pending verification for this number in the last 5 minutes | One-off UUID / absent | Send a new code (Step 1) |

### Error Responses

| Code | Meaning | Action |
|---|---|---|
| `400` | Invalid request | Read the field errors in the response body (code not 4-8 digits, invalid number, action not `NO_ACTION`/`DECLINE`). No attempt is used |
| `401` | The API key has expired | Rotate it or create a new key in **Developers > API keys** |
| `403` | Missing, wrong or revoked API key; a scoped key without access to this endpoint; a request from outside the key's IP allowlist; or not enough credits | Read the message in `detail` or `error`: fix the `x-api-key` header or the key's access, or top up |
| `429` | Rate limit: 300 POST/PATCH/DELETE and 600 GET requests a minute per key | Wait the `Retry-After` seconds, then retry |
| `502` | Phone provider temporarily unavailable (`"code": "phone_provider_unavailable"`) | Retry with a short backoff. No attempt is used |

Checks are free; the only credit check is for the `enable_social` add-on (`403` with `error` when the balance cannot cover it).

---

## Phone Risk (no code sent)

Scores a number in one synchronous call: carrier, line type, porting, disposable number, duplicates and normalized risk intelligence. No code is sent and the user does nothing. Creates an API session (`request_id`).

```
POST https://verification.didit.me/v3/phone/risk/
```

### Body (JSON)

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `phone_number` | string | **Yes** | - | Number to score (max 20, normalized to E.164) |
| `country_code` | string | No | - | ISO 3166-1 alpha-2 or alpha-3 country hint (max 3 chars) |
| `signals` | object | No | - | Same fields as `signals` in Step 1 |
| `enable_social` | boolean | No | `false` | Add the `phone.phone_social` block (billed per request as an add-on) |
| `vendor_data` | string | No | - | Your reference, stored and echoed |
| `metadata` | object | No | `null` | Your JSON metadata, stored and echoed |

### Example

```python
response = requests.post(
    "https://verification.didit.me/v3/phone/risk/",
    headers={"x-api-key": "YOUR_API_KEY", "Content-Type": "application/json"},
    json={"phone_number": "+14155552671", "country_code": "US", "vendor_data": "lead-123"},
    timeout=30,
)
result = response.json()
print(result["status"], result["phone"]["is_virtual"], result["phone"].get("phone_intelligence"))
```

```typescript
const response = await fetch("https://verification.didit.me/v3/phone/risk/", {
  method: "POST",
  headers: { "x-api-key": "YOUR_API_KEY", "Content-Type": "application/json" },
  body: JSON.stringify({ phone_number: "+14155552671", country_code: "US", vendor_data: "lead-123" }),
});
const result = await response.json();
```

### Response (200 OK)

```json
{
  "request_id": "4fd09d2e-9bc9-4c4e-9c46-7f625ac0ab62",
  "status": "Approved",
  "phone": {
    "status": "Approved",
    "phone_number_prefix": "+1",
    "phone_number": "4155552671",
    "full_number": "+14155552671",
    "country_code": "US",
    "country_name": "United States",
    "carrier": {"name": "Example Mobile", "type": "mobile"},
    "is_disposable": false,
    "is_virtual": false,
    "verification_method": null,
    "verification_attempts": 0,
    "verified_at": null,
    "warnings": [],
    "lifecycle": [],
    "matches": [],
    "phone_intelligence": {
      "score": 3.0,
      "phone_type_risk": "Low",
      "phone_trust_index": 97,
      "network_stability_index": 95,
      "is_disposable": false,
      "is_ported": false,
      "is_recently_ported": false,
      "carrier_type": "mobile",
      "reason_codes": []
    },
    "enrichment": {
      "score": 3.0,
      "phone_type_risk": "Low",
      "phone_trust_index": 97,
      "network_stability_index": 95,
      "is_disposable": false,
      "is_ported": false,
      "is_recently_ported": false,
      "carrier_type": "mobile",
      "reason_codes": []
    }
  },
  "vendor_data": "lead-123",
  "metadata": null,
  "created_at": "2026-09-01T10:30:00.123456+00:00"
}
```

- `status` (top level and `phone.status`): `"Approved"`, `"In Review"` or `"Declined"`. Normally `"Approved"`; your application's phone-risk rules can produce the others. HTTP is `200` for every completed lookup.
- `phone.phone_intelligence` and `phone.enrichment` are the same object (compatibility alias). They are best-effort: both keys are absent when no usable intelligence came back. Build rules on `is_disposable` and `is_virtual` first and treat a missing block as "unknown", not "safe". `phone.carrier` can be `null` when no carrier was resolved.
- Billed once the lookup starts, even when best-effort fields are missing.

Errors: `400` field errors, `401`, `403` (including the credit check for the call plus the `enable_social` add-on), `429`, as in Step 2.

---

## Response Field Reference

### `phone` Object (check and risk)

| Field | Type | Description |
|---|---|---|
| `status` | string | Check: `"Approved"` or `"Declined"` on finalized checks (enum also has `"In Review"`, `"Not Finished"`, `"Expired"`). Risk: `"Approved"`, `"In Review"`, `"Declined"` |
| `phone_number_prefix` | string | Country calling code with `+` (e.g. `+1`) |
| `phone_number` | string | National number without the calling code |
| `full_number` | string | Full E.164 number |
| `country_code` / `country_name` | string | ISO 3166-1 alpha-2 country of the number, and its name |
| `carrier.name` | string | Carrier name (empty string when unknown) |
| `carrier.type` | string | `mobile`, `fixed_line`, `voip`, `isp`, `vpn`, `toll_free`, `premium_rate`, `pager`, `payphone`, `satellite`, `service`, `shared_cost`, `short_codes_commercial`, `calling_cards`, `local_rate`, `universal_access`, `voice_mail`, `other`, `unknown` |
| `is_disposable` | boolean | Temporary or burner number service |
| `is_virtual` | boolean | Line type is `voip`, `isp` or `vpn` |
| `verification_method` | string | Channel that delivered the code once delivery is confirmed, otherwise the requested channel. `null` on risk lookups |
| `verification_attempts` | integer | Number of code sends for this verification (1, or 2 after a retry). `0` on risk lookups |
| `verified_at` | string or null | When the correct code was entered |
| `warnings` | array | `{feature, risk, additional_data, log_type, short_description, long_description}`. `log_type`: `error` declines, `warning` flags for review, `information` is recorded only |
| `lifecycle` | array | `{type, timestamp, details, fee}`. Types: `PHONE_VERIFICATION_MESSAGE_SENT`, `PHONE_VERIFICATION_RETRY_MESSAGE_SENT`, `PHONE_VERIFICATION_BLOCKED`, `PHONE_DELIVERY_DELIVERED`, `PHONE_DELIVERY_UNDELIVERABLE`, `VALID_CODE_ENTERED`, `INVALID_CODE_ENTERED`, `PHONE_VERIFICATION_APPROVED`, `PHONE_VERIFICATION_DECLINED`, `PHONE_VERIFICATION_IN_REVIEW`, `PHONE_VERIFICATION_EXPIRED`. Send events carry `{status, reason, channel, actual_channel}`; `fee` (USD) is non-zero only on send events |
| `matches` | array | Up to 5 other sessions of your application where a different user (`vendor_data`) used this number: `{session_id, session_number, vendor_data, verification_date, phone_number, status, is_blocklisted, api_service, source}`. `source` is `session`, or `list_entry` for a blocklist entry |
| `phone_intelligence` / `enrichment` | object | Risk endpoint only, best-effort: `score` (0-100, higher is riskier), `phone_type_risk` (`Low`/`Medium`/`High`), `phone_trust_index` (inverse of the score), `network_stability_index`, `is_disposable`, `is_ported`, `is_recently_ported`, `carrier_type`, `reason_codes` (open list; do not reject unknown codes) |
| `phone_social` | object | Only with `enable_social: true` and a completed lookup: `profiles_registered` / `profiles_checked` (`0` registered is a real, billable answer), counts, 0-10 indexes, `whatsapp_profile_completeness` (`Basic`, `Partial`, `Complete`, `Not Present`), `registered_platforms`, `not_registered_platforms`, `categories`, `profiles`. Counts can be `null` |

---

## Warning Tags

| Tag | Severity | Description |
|---|---|---|
| `VERIFICATION_CODE_ATTEMPTS_EXCEEDED` | `error` (always declines) | The 3rd wrong code on the standalone check |
| `PHONE_NUMBER_IN_BLOCKLIST` | `error` (always declines) | Number on your phone blocklist (Lists API) or matched a blocklisted session. `additional_data`: `blocklisted_session_id`, `blocklisted_session_number`, `api_service` |
| `HIGH_RISK_PHONE_NUMBER` | `error` by default | Raised at send when the anti-fraud layer blocks it (`"Blocked"`); declines. A number on your phone allowlist goes to `In Review` instead (`log_type: "warning"`, `additional_data.phone_number_in_allowlist: true`). `additional_data.blocked_reason` holds the send `reason` |
| `DISPOSABLE_NUMBER_DETECTED` | Per `disposable_number_action` | Temporary or burner number |
| `VOIP_NUMBER_DETECTED` | Per `voip_number_action` | Line type `voip`, `isp` or `vpn` |
| `DUPLICATED_PHONE_NUMBER` | Per `duplicated_phone_number_action` | Number used by a different user in another session (any status). `additional_data`: `duplicated_session_id`, `duplicated_session_number`, `api_service` |
| `PHONE_NUMBER_IN_ALLOWLIST` | `information` | Number matched other sessions but is on your phone allowlist, so the duplicate action was skipped. `additional_data`: `phone_number` |

On this API a `DECLINE` action gives log type `error`, `NO_ACTION` gives `information`.

---

## Common Workflows

### Basic Phone Verification

```
1. POST /v3/phone/send/   -> {"phone_number": "+14155552671"}
   If "Blocked"           -> ask for another number (nothing billed)
2. Wait for the user to type the code (valid 5 minutes from the first send)
3. POST /v3/phone/check/  -> {"phone_number": "+14155552671", "code": "123456"}
4. If "Approved"             -> phone verified
   If "Failed"               -> ask the user to retry (3 attempts in total)
   If "Declined"             -> read phone.warnings
   If "Expired or Not Found" -> send again (step 1)
```

### Strict Security Verification

```
1. POST /v3/phone/send/   -> include signals.ip, signals.device_platform, vendor_data,
                             options.preferred_channel: "sms"
2. POST /v3/phone/check/  -> disposable_number_action, voip_number_action,
                             duplicated_phone_number_action = "DECLINE"
3. If "Declined" -> phone.warnings[].risk says why; block or ask for another number
```

### Pre-screen Without a Code

```
1. POST /v3/phone/risk/   -> {"phone_number": "+14155552671", "vendor_data": "lead-123"}
2. If phone.is_virtual or phone.is_disposable -> reject before sending any OTP
3. Otherwise continue with the send/check flow above
```

---

## Utility Scripts

**verify_phone.py**: Send codes, check codes and score phone risk from the command line.

```bash
# Requires: pip install requests
export DIDIT_API_KEY="your_api_key"

python scripts/verify_phone.py send +14155552671 --channel sms --sms-sender-name "Example Bank"
python scripts/verify_phone.py check +14155552671 123456 --decline-voip --decline-disposable
python scripts/verify_phone.py risk +14155552671 --country-code US
```

Can also be imported as a library:

```python
from scripts.verify_phone import send_code, check_code, score_phone_risk

send_result = send_code("+14155552671", channel="sms")
check_result = check_code("+14155552671", "123456", decline_voip=True)
risk_result = score_phone_risk("+14155552671")
```
