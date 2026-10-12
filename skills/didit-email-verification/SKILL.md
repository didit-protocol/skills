---
name: didit-email-verification
description: >
  Integrate the Didit Email Verification standalone API to verify email addresses with a one-time
  code, and to risk-score an address without sending a code. Use when the user wants to send email
  OTP codes, check email verification codes, detect breached, disposable or undeliverable emails,
  flag duplicate or blocklisted addresses, look up an email's social footprint, or score email risk
  with POST /v3/email/risk/ using Didit. Supports fraud signals (IP, device, user agent), 4-8
  character numeric or alphanumeric codes, 54 template languages, white-label branding, and
  per-call DECLINE policies for risky emails.
version: 1.3.0
metadata:
  openclaw:
    requires:
      env:
        - DIDIT_API_KEY
    primaryEnv: DIDIT_API_KEY
    emoji: "✉️"
    homepage: https://docs.didit.me
---

# Didit Email Verification API

## Overview

Three standalone endpoints:

1. **Send** a one-time code to an email address: `POST /v3/email/send/`
2. **Check** the code the user typed and get the email report: `POST /v3/email/check/`
3. **Risk** (no code sent): score an address in one call: `POST /v3/email/risk/`

**Key constraints (send + check):**
- The check finds the verification by your application + the `email` address. It does not take `request_id`.
- A pending verification lives **5 minutes from the first send**. Retries do not extend it.
- **3 code attempts** per verification. Wrong codes 1 and 2 return `"Failed"`; the 3rd wrong code finalizes it as `"Declined"` (`EMAIL_CODE_ATTEMPTS_EXCEEDED`).
- **One resend** per pending verification: a second send for the same address inside the window returns `"Retry"` with the same `request_id` and a fresh code (the previous code stops working). A further send starts a new verification with a new `request_id`.
- Codes are compared case-insensitively. Only the most recent code is valid.
- No pending verification (never sent, already finalized, undeliverable at send, or older than 5 minutes): the check returns HTTP `200` with `status: "Expired or Not Found"`.
- Each new verification is stored as an API session: `request_id` works with `GET /v3/session/{sessionId}/decision/`, shows in the Business Console, and fires `status.updated` webhooks as it progresses. Each risk call also creates an API session.

**Capabilities:** known data breaches (`breaches[]`), disposable providers, deliverability (syntax and DNS/MX), duplicates across your sessions (`matches[]`), your email blocklist/allowlist, optional social footprint (`enable_social`), fraud signals.

**Sandbox:** sandbox API keys skip delivery, billing and persistence. Send returns a static `"Success"` with a random `request_id`; on check use code `123456` (any well-formed code returns a simplified `"Approved"` payload). Risk returns deterministic approved data. Malformed input still returns `400`.

**Pricing:** Email Verification $0.03 per successful send (`"Success"`); `"Retry"` and `"Undeliverable"` sends and checks are free (apart from the optional social add-on); standalone calls have no free tier. No list price is published for `POST /v3/email/risk/` (the docs say it is lower than Email Verification) or for the social footprint add-on (`enable_social`, billed per request on top of the endpoint price, not billed when the lookup could not complete). These are the list prices until 1 November 2026, when Didit pricing changes and the 500 free checks a month become $10 of free credit a month. Check [didit.me/pricing](https://didit.me/pricing) for current prices.

**API Reference:** [Send Code](https://docs.didit.me/standalone-apis/email-send) | [Check Code](https://docs.didit.me/standalone-apis/email-check) | [Email Risk](https://docs.didit.me/standalone-apis/email-risk)
**Feature Guide:** https://docs.didit.me/core-technology/email-verification/overview

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

## Step 1: Send Email Code

```
POST https://verification.didit.me/v3/email/send/
```

### Headers

| Header | Value | Required |
|---|---|---|
| `x-api-key` | Your API key | **Yes** |
| `Content-Type` | `application/json` | **Yes** |

### Body (JSON)

| Parameter | Type | Required | Default | Constraints | Description |
|---|---|---|---|---|---|
| `email` | string | **Yes** | - | Valid email, max 254 | Address to send the code to |
| `options.code_size` | integer | No | `6` | 4-8 | Code length |
| `options.alphanumeric_code` | boolean | No | `false` | - | `true` = uppercase A-Z + 0-9 instead of digits only |
| `options.locale` | string | No | `en` | One of 54 codes | Template language, e.g. `en`, `es`, `fr`, `pt-BR`, `zh-CN`, `zh-TW`. Unsupported values return `400` listing the supported set |
| `options.use_white_label_customization` | boolean | No | `false` | - | Use your application's white-label branding instead of the Didit template |
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
    "https://verification.didit.me/v3/email/send/",
    headers={"x-api-key": "YOUR_API_KEY", "Content-Type": "application/json"},
    json={
        "email": "user@example.com",
        "options": {"code_size": 6, "locale": "en"},
        "signals": {"ip": "203.0.113.42"},
        "vendor_data": "user-1234",
    },
    timeout=30,
)
print(response.status_code, response.json())
```

```typescript
const response = await fetch("https://verification.didit.me/v3/email/send/", {
  method: "POST",
  headers: { "x-api-key": "YOUR_API_KEY", "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "user@example.com",
    options: { code_size: 6, locale: "en" },
    signals: { ip: "203.0.113.42" },
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
| `"Success"` | Code emailed for a new verification (billed) | Wait for the user's code, then call Check |
| `"Retry"` | Second send inside the 5-minute window: fresh code for the same verification, same `request_id`, previous code invalid (free) | Wait for the new code, then call Check |
| `"Undeliverable"` | The address failed syntax or DNS/MX validation, or the email could not be sent. `reason` is `"email_can_not_be_delivered"`. No email sent, nothing billed, the verification is already finalized as `Declined` (a check returns `"Expired or Not Found"`) | Ask the user for a different address |

### Error Responses

| Code | Meaning | Action |
|---|---|---|
| `400` | Invalid request | Read the field errors in the response body (malformed `email`, `options.code_size` outside 4-8, unsupported `options.locale`) |
| `401` | The API key has expired | Rotate it or create a new key in **Developers > API keys** |
| `403` | Missing, wrong or revoked API key; a scoped key without access to this endpoint; a request from outside the key's IP allowlist; or not enough credits | Read the message in `detail` or `error`: fix the `x-api-key` header or the key's access, or top up |
| `429` | Rate limit: 300 POST/PATCH/DELETE and 600 GET requests a minute per key | Wait the `Retry-After` seconds, then retry |

The credit check runs before any send: `403` with `{"error": "You don't have enough credits to perform this request."}`.

---

## Step 2: Check Email Code

Verifies the code and returns the email report. **Call Send first**, with the same `email`.

```
POST https://verification.didit.me/v3/email/check/
```

Headers: same as Step 1.

### Body (JSON)

| Parameter | Type | Required | Default | Values | Description |
|---|---|---|---|---|---|
| `email` | string | **Yes** | - | Valid email | Same address used in Step 1 (this links check to send) |
| `code` | string | **Yes** | - | Max 10 chars | The code the user received (4-8 characters, case-insensitive) |
| `duplicated_email_action` | string | No | `"NO_ACTION"` | `"NO_ACTION"` / `"DECLINE"` | Address already approved for a different user (different `vendor_data`) of your application |
| `breached_email_action` | string | No | `"NO_ACTION"` | `"NO_ACTION"` / `"DECLINE"` | Address found in known data breaches |
| `disposable_email_action` | string | No | `"NO_ACTION"` | `"NO_ACTION"` / `"DECLINE"` | Domain is a disposable or temporary-mail provider |
| `enable_social` | boolean | No | `false` | - | Also look up the address's social footprint (adds `email.email_social`; billed per request as an add-on) |
| `email_no_social_presence_action` | string | No | `"NO_ACTION"` | `"NO_ACTION"` / `"DECLINE"` | Decline when the social footprint check finds the address on no platform (`profiles_registered: 0`). Needs `enable_social: true` |

> **Policy note:** `DECLINE` turns a correct code into `"Declined"` when the risk is found. `NO_ACTION` records the risk in `email.warnings` (log type `information`) without changing the status. Blocklisted and undeliverable addresses always decline. Only `NO_ACTION` and `DECLINE` are accepted here.

### Example

```python
response = requests.post(
    "https://verification.didit.me/v3/email/check/",
    headers={"x-api-key": "YOUR_API_KEY", "Content-Type": "application/json"},
    json={
        "email": "user@example.com",
        "code": "123456",
        "breached_email_action": "DECLINE",
        "disposable_email_action": "DECLINE",
    },
    timeout=30,
)
result = response.json()
if result["status"] in ("Approved", "Declined"):
    print(result["email"]["is_breached"], result["email"]["is_disposable"])
```

```typescript
const response = await fetch("https://verification.didit.me/v3/email/check/", {
  method: "POST",
  headers: { "x-api-key": "YOUR_API_KEY", "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "user@example.com",
    code: "123456",
    breached_email_action: "DECLINE",
    disposable_email_action: "DECLINE",
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
  "email": {
    "status": "Approved",
    "email": "user@example.com",
    "is_breached": false,
    "breaches": [],
    "is_disposable": false,
    "is_undeliverable": false,
    "verification_attempts": 1,
    "verified_at": "2026-06-12T01:24:47.311323Z",
    "warnings": [],
    "lifecycle": [
      {"type": "EMAIL_VERIFICATION_MESSAGE_SENT", "timestamp": "2026-06-12T01:23:39.580554+00:00", "details": {"status": "Success", "reason": null}, "fee": 0.03},
      {"type": "VALID_CODE_ENTERED", "timestamp": "2026-06-12T01:24:47.311201+00:00", "details": {"code_tried": "123456", "status": "Approved"}, "fee": 0},
      {"type": "EMAIL_VERIFICATION_APPROVED", "timestamp": "2026-06-12T01:24:47.384292+00:00", "details": null, "fee": 0}
    ],
    "matches": []
  },
  "vendor_data": "user-1234",
  "metadata": null,
  "created_at": "2026-06-12T01:24:47.401719+00:00"
}
```

A wrong code with attempts left:

```json
{
  "request_id": "11111111-2222-3333-4444-555555555555",
  "status": "Failed",
  "message": "The verification code is incorrect. Attempts remaining: 2",
  "email": null,
  "vendor_data": "user-1234",
  "metadata": null,
  "created_at": "2026-06-12T01:24:21.512340+00:00"
}
```

### Status Values & Handling

| Status | Meaning | `request_id` / `email` | Action |
|---|---|---|---|
| `"Approved"` | Correct code, no declining risk | Session id of the send / full report | Email verified, proceed |
| `"Declined"` | Terminal: correct code but a declining risk matched (a `DECLINE` action, blocklisted or undeliverable address), or the 3rd wrong code | Session id of the send / full report | Read `email.warnings`; block or ask for another address |
| `"Failed"` | Wrong code, attempts remaining (`message` says how many) | One-off UUID / `null` | Ask the user to re-enter the code |
| `"Expired or Not Found"` | No pending verification for this address in the last 5 minutes | One-off UUID / absent | Send a new code (Step 1) |

### Error Responses

| Code | Meaning | Action |
|---|---|---|
| `400` | Invalid request | Read the field errors in the response body (malformed `email`, missing `code`, action not `NO_ACTION`/`DECLINE`) |
| `401` | The API key has expired | Rotate it or create a new key in **Developers > API keys** |
| `403` | Missing, wrong or revoked API key; a scoped key without access to this endpoint; a request from outside the key's IP allowlist; or not enough credits | Read the message in `detail` or `error`: fix the `x-api-key` header or the key's access, or top up |
| `429` | Rate limit: 300 POST/PATCH/DELETE and 600 GET requests a minute per key | Wait the `Retry-After` seconds, then retry |

Checks are free; the only credit check is for the `enable_social` add-on (`403` with `error` when the balance cannot cover it).

---

## Email Risk (no code sent)

Scores an address in one synchronous call: deliverability, disposable domain, breaches, duplicates and normalized risk intelligence. No email is sent and the user does nothing. Creates an API session (`request_id`).

```
POST https://verification.didit.me/v3/email/risk/
```

### Body (JSON)

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `email` | string | **Yes** | - | Address to score |
| `country_code` | string | No | - | ISO 3166-1 alpha-2 or alpha-3 country hint (max 3 chars) for intelligence coverage |
| `signals` | object | No | - | Same fields as `signals` in Step 1 (`ip`, `device_id`, `device_platform`, `device_model`, `os_version`, `app_version`, `user_agent`) |
| `enable_social` | boolean | No | `false` | Add the `email.email_social` block (billed per request as an add-on) |
| `vendor_data` | string | No | - | Your reference, stored and echoed |
| `metadata` | object | No | `null` | Your JSON metadata, stored and echoed |

### Example

```python
response = requests.post(
    "https://verification.didit.me/v3/email/risk/",
    headers={"x-api-key": "YOUR_API_KEY", "Content-Type": "application/json"},
    json={"email": "user@example.com", "country_code": "US", "vendor_data": "lead-123"},
    timeout=30,
)
result = response.json()
print(result["status"], result["email"]["is_breached"], result["email"]["is_disposable"])
```

```typescript
const response = await fetch("https://verification.didit.me/v3/email/risk/", {
  method: "POST",
  headers: { "x-api-key": "YOUR_API_KEY", "Content-Type": "application/json" },
  body: JSON.stringify({ email: "user@example.com", country_code: "US", vendor_data: "lead-123" }),
});
const result = await response.json();
```

### Response (200 OK)

```json
{
  "request_id": "82397be9-5921-4970-a979-2d5b43e08b33",
  "status": "Approved",
  "email": {
    "status": "Approved",
    "email": "user@example.com",
    "is_breached": false,
    "breaches": [],
    "is_disposable": false,
    "is_undeliverable": false,
    "verification_attempts": 0,
    "verified_at": null,
    "warnings": [],
    "lifecycle": [],
    "matches": [],
    "email_intelligence": {
      "score": 4.0,
      "deliverable": "high",
      "breach_risk_level": "Low",
      "breach_risk_index": 4,
      "is_recent_breach": false,
      "is_frequent_breached": false,
      "is_disposable": false,
      "is_free_domain": false,
      "is_breached": false,
      "no_of_breaches": 0,
      "reason_codes": []
    },
    "enrichment": {
      "score": 4.0,
      "deliverable": "high",
      "breach_risk_level": "Low",
      "breach_risk_index": 4,
      "is_recent_breach": false,
      "is_frequent_breached": false,
      "is_disposable": false,
      "is_free_domain": false,
      "is_breached": false,
      "no_of_breaches": 0,
      "reason_codes": []
    }
  },
  "vendor_data": "lead-123",
  "metadata": null,
  "created_at": "2026-09-01T10:30:00.123456+00:00"
}
```

- `status` (top level and `email.status`): `"Approved"`, `"In Review"` or `"Declined"`. Normally `"Approved"`; your application's email-risk rules can produce the others. HTTP is `200` for every completed lookup.
- `email.email_intelligence` and `email.enrichment` are the same object (compatibility alias). They are best-effort: both keys are absent when no usable intelligence came back. Build rules on `is_breached`, `is_disposable` and `is_undeliverable` first and treat a missing block as "unknown", not "safe".
- Billed once the lookup starts, even when best-effort fields are missing.

Errors: same table as Step 2 (`400` field errors, `401`, `403` including the credit check for the call plus the `enable_social` add-on, `429`).

---

## Response Field Reference

### `email` Object (check and risk)

| Field | Type | Description |
|---|---|---|
| `status` | string | Check: `"Approved"` or `"Declined"` on finalized checks. Risk: `"Approved"`, `"In Review"`, `"Declined"` |
| `email` | string | The address |
| `is_breached` | boolean | Found in known data breaches |
| `breaches` | array | Up to 5 most recent breaches: `{name, domain, breach_date, breach_emails_count, description, logo_path, data_classes, is_verified}`. `description` may contain HTML |
| `is_disposable` | boolean | Domain is a disposable or temporary-mail provider |
| `is_undeliverable` | boolean | Cannot receive mail (syntax, DNS/MX, or bounced) |
| `verification_attempts` | integer | Number of code sends for this verification (1, or 2 after a retry). `0` on risk lookups |
| `verified_at` | string or null | When the correct code was entered |
| `warnings` | array | `{feature, risk, additional_data, log_type, short_description, long_description}`. `log_type`: `error` declines, `warning` flags for review, `information` is recorded only |
| `lifecycle` | array | `{type, timestamp, details, fee}`. Types: `EMAIL_VERIFICATION_MESSAGE_SENT`, `EMAIL_VERIFICATION_RETRY_MESSAGE_SENT`, `VALID_CODE_ENTERED`, `INVALID_CODE_ENTERED`, `EMAIL_VERIFICATION_APPROVED`, `EMAIL_VERIFICATION_DECLINED`, `EMAIL_VERIFICATION_IN_REVIEW`, `EMAIL_VERIFICATION_EXPIRED`. `fee` (USD) is non-zero only on the first successful send |
| `matches` | array | Up to 5 other sessions of your application where a different user (`vendor_data`) used this address: `{session_id, session_number, vendor_data, verification_date, email, status, is_blocklisted, api_service, source}`. `source` is `session`, or `list_entry` for a blocklist entry (null `session_id`/`session_number`) |
| `email_intelligence` / `enrichment` | object | Risk endpoint only, best-effort: `score` (0-100, higher is riskier), `deliverable`, `breach_risk_level` (`Low`/`Medium`/`High`), `breach_risk_index`, `is_recent_breach`, `is_frequent_breached`, `is_disposable`, `is_free_domain`, `is_breached`, `no_of_breaches`, `reason_codes` (open list; do not reject unknown codes) |
| `email_social` | object | Only with `enable_social: true` and a completed lookup. See below |

### `email_social` Object

| Field | Description |
|---|---|
| `profiles_registered` / `profiles_checked` | Platforms where the address is registered, out of the platforms checked. `0` registered is a real, billable answer (a common synthetic-identity signal) |
| `names_found`, `photos_found`, `communication_breadth`, `digital_footprint_diversity` | Counts |
| `digital_sophistication_index`, `engagement_depth_index`, `subscription_affordability_index` | 0-10 composites |
| `free_platforms`, `full_paid_platforms`, `partial_paid_platforms` | Registrations by platform pricing model |
| `registered_platforms`, `not_registered_platforms` | Platform lists with `category` and `scope` (`global` or `local`) |
| `categories`, `profiles` | Per-category registered count and ratio; per-platform profile details when exposed |

Every count can be `null` when the lookup returned no data for it.

---

## Warning Tags

| Tag | Severity | Description |
|---|---|---|
| `EMAIL_CODE_ATTEMPTS_EXCEEDED` | `error` (always declines) | The 3rd wrong code on the standalone check |
| `EMAIL_IN_BLOCKLIST` | `error` (always declines) | Address on your email blocklist (Lists API) or matched a blocklisted verification. `additional_data`: `blocklisted_session_id`, `blocklisted_session_number`, `api_service` (all `null` for a pure list hit) |
| `UNDELIVERABLE_EMAIL_DETECTED` | `error` (always declines) | Address cannot receive mail |
| `BREACHED_EMAIL_DETECTED` | Per `breached_email_action` | Found in known breaches (see `breaches[]`) |
| `DISPOSABLE_EMAIL_DETECTED` | Per `disposable_email_action` | Disposable or temporary-mail domain |
| `DUPLICATED_EMAIL` | Per `duplicated_email_action` | Already approved for a different user. `additional_data`: `duplicated_session_id`, `duplicated_session_number`, `api_service` |
| `EMAIL_IN_ALLOWLIST` | `information` | Address is on your email allowlist, so the duplicate action was skipped |

At most one of `EMAIL_IN_BLOCKLIST`, `DUPLICATED_EMAIL` and `EMAIL_IN_ALLOWLIST` fires per attempt (blocklist first, then duplicate, then allowlist). On this API a `DECLINE` action gives log type `error`, `NO_ACTION` gives `information`.

---

## Common Workflows

### Basic Email Verification

```
1. POST /v3/email/send/   -> {"email": "user@example.com"}
   If "Undeliverable"     -> ask for another address (nothing billed)
2. Wait for the user to type the code (valid 5 minutes from the first send)
3. POST /v3/email/check/  -> {"email": "user@example.com", "code": "123456"}
4. If "Approved"             -> email verified
   If "Failed"               -> ask the user to retry (3 attempts in total)
   If "Declined"             -> read email.warnings
   If "Expired or Not Found" -> go back to step 1
```

### Strict Security Verification

```
1. POST /v3/email/send/   -> include signals.ip, signals.device_id, signals.user_agent and vendor_data
2. Wait for the user's code
3. POST /v3/email/check/  -> duplicated_email_action, breached_email_action, disposable_email_action = "DECLINE"
4. If "Approved"  -> safe to proceed
   If "Declined"  -> email.warnings[].risk says why; block or ask for another address
```

### Pre-screen Without a Code

```
1. POST /v3/email/risk/   -> {"email": "user@example.com", "vendor_data": "lead-123"}
2. If email.is_undeliverable or email.is_disposable -> reject before sending any OTP
3. Otherwise continue with the send/check flow above
```

---

## Utility Scripts

**verify_email.py**: Send codes, check codes and score email risk from the command line.

```bash
# Requires: pip install requests
export DIDIT_API_KEY="your_api_key"

python scripts/verify_email.py send user@example.com --locale es
python scripts/verify_email.py check user@example.com 123456 --decline-breached --decline-disposable
python scripts/verify_email.py risk user@example.com --country-code US
```

Can also be imported as a library:

```python
from scripts.verify_email import send_code, check_code, score_email_risk

send_result = send_code("user@example.com")
check_result = check_code("user@example.com", "123456", decline_breached=True)
risk_result = score_email_risk("user@example.com")
```
