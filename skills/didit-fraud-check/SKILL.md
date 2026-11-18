---
name: didit-fraud-check
description: >
  Integrate the Didit Fraud Check API and the IP Risk API. Use when the user wants to run one
  server-side fraud or identity risk check over an email, phone, government ID number, tax
  number, IP address or selfie; quote a check's price before running it with the plan endpoint;
  combine email risk, phone risk, IP risk, social enrichment, database validation, private
  network history and the global fraud network in one request; read separate identity,
  contact, device/network, behavioral and fraud-network risk dimensions and an
  approve/review/reject recommendation; bind a selfie to a Brazilian CPF; retrieve a stored
  check by check_id; make idempotent retries with client_reference; or risk-score a single IP
  address (geolocation, VPN/Tor, data center, claimed-country mismatch) using Didit.
version: 1.0.0
metadata:
  openclaw:
    requires:
      env:
        - DIDIT_API_KEY
    primaryEnv: DIDIT_API_KEY
    emoji: "🕵️"
    homepage: https://docs.didit.me
---

# Didit Fraud Check API

## Overview

Submit typed identifiers (email, phone, government ID numbers, your own external id), claimed identity attributes and attempt context in one request, select which checks (modules) to run, and get every module's result, independent risk dimensions and a recommendation back in the same response.

**Key facts:**
- Synchronous: `POST /v3/fraud/checks/` returns the finished result. `GET /v3/fraud/checks/{check_id}/` re-reads it without re-running or charging.
- Call `POST /v3/fraud/checks/plan/` first with the same body: it validates inputs and returns per-module availability and estimated price, without running anything or charging.
- `subject.identifiers` is the only required input for a check (1 to 10 items). Everything else widens coverage.
- Each module reports its own `status` and `reason`. A source that could not answer is never reported as a mismatch or as zero risk.
- `risk` keeps five dimensions separate (`identity`, `contact`, `device_network`, `behavioral`, `fraud_network`); `recommendation` is `approve`, `review` or `reject`.
- `client_reference` is your idempotency key: same body returns the stored result with no new charge; a different body returns `409`.
- Sandbox applications get sample responses with no supplier calls and no charges.

**Pricing:** No list price is published for Fraud Check or the IP Risk API; check [didit.me/pricing](https://didit.me/pricing). Each paid module bills at your organization's current prepaid or contract rate for that check, skipped and unavailable modules are not billed, and `networks_same_org` and `networks_cross_org` have no per-check charge. Read the exact amount from `estimated_price` in the plan response.

**API Reference:** [Fraud Check](https://docs.didit.me/standalone-apis/fraud-check) | [Plan](https://docs.didit.me/standalone-apis/fraud-check-plan) | [Get](https://docs.didit.me/standalone-apis/fraud-check-result) | [IP Risk](https://docs.didit.me/standalone-apis/ip-risk)

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

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `https://verification.didit.me/v3/fraud/checks/plan/` | Dry run: availability, selection and estimated price per module. No check, no session, no charge |
| `POST` | `https://verification.didit.me/v3/fraud/checks/` | Run a Fraud Check |
| `GET` | `https://verification.didit.me/v3/fraud/checks/{check_id}/` | Read a stored check of your application |
| `POST` | `https://verification.didit.me/v3/ip/risk/` | Standalone IP risk score (see [IP Risk API](#ip-risk-api)) |

Email and phone risk also exist as single-purpose endpoints: `POST /v3/email/risk/` (see **didit-email-verification**, [docs](https://docs.didit.me/standalone-apis/email-risk)) and `POST /v3/phone/risk/` (see **didit-phone-verification**, [docs](https://docs.didit.me/standalone-apis/phone-risk)).

### Headers

| Header | Value | Required |
|---|---|---|
| `x-api-key` | Your API key | **Yes** |
| `Content-Type` | `application/json` | **Yes** (POST) |

---

## Profiles

A profile version is frozen: its modules, defaults and decision policy never change. Pin `profile_version` so the behaviour is explicit. `profile` is `standard` (the only profile); an unknown `profile` or `profile_version` returns `400`.

| `profile_version` | What it adds | Omitting `checks.include` runs |
|---|---|---|
| `2026-08-27` (default when omitted) | Email risk, phone risk, IP risk, eligible database validation, private network history | Every module whose input is present, paid ones included |
| `2026-09-14` | Optional `email_social` / `phone_social` enrichment; every completed check is recorded as a native verification session (`request_id`) | Normalization and the network modules only; paid modules are opt-in |
| `2026-09-14.1` | Enables `networks_cross_org` (global fraud network) for participating, entitled organizations | Same as `2026-09-14` |
| `2026-09-14.2` | Enables `biometric_identity` (selfie to Brazilian CPF reference check) | Same as `2026-09-14`, plus `biometric_identity` when a selfie, CPF and consent are supplied |

Selecting `networks_cross_org` before `2026-09-14.1`, or `biometric_identity` before `2026-09-14.2`, reports the module as skipped with reason `not_available_in_profile_version`.

---

## Run a Fraud Check

```
POST https://verification.didit.me/v3/fraud/checks/
```

### Body (JSON)

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `subject` | object | **Yes** | - | Who is being checked (see below) |
| `subject.identifiers` | array | **Yes** | - | 1 to 10 typed identifiers. One is enough |
| `subject.attributes` | object | No | - | Claimed attributes, compared where a selected source supports them. Claims, not verified facts |
| `subject.selfie` | string | No | - | Base64 JPEG, PNG or WebP (a matching `data:image/...;base64,` URI is accepted), up to 6 MB. Only used by `biometric_identity`. No URLs or storage keys |
| `context` | object | No | - | The attempt, not the person (see below) |
| `checks.include` | array | No | profile defaults | Modules to run. An explicit `[]` turns off all optional work; normalization still runs |
| `checks.exclude` | array | No | - | Modules to skip. Takes precedence over `include` |
| `client_reference` | string | No | - | Your reference, max 255 chars. Doubles as the idempotency key |
| `profile` | string | No | `"standard"` | Orchestration profile id |
| `profile_version` | string | No | `"2026-08-27"` | Frozen profile version to run |
| `vendor_data` | string | No | - | Your id for the user, max 1000 chars. Echoed back |
| `metadata` | any JSON | No | - | Echoed back |

**`subject.identifiers[]` item:**

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | string | **Yes** | `email`, `phone`, `national_id`, `tax_number`, `passport_number`, `driving_licence_number`, `residence_permit_number`, `voter_id`, `external_id` |
| `value` | string | **Yes** | The value in any customary format, max 255 chars. Blank values return `400`. Send phones in E.164 (`+14155552671`) |
| `country` | string | For government types | ISO 3166-1 alpha-2 or alpha-3 issuing country. Required for every type except `email`, `phone` and `external_id`: the same digits mean different people in different countries. A government identifier without it is not usable |
| `issuer` | string | No | Issuing authority or sub-national issuer (max 128 chars), when the country alone is not unique |

`external_id` is scoped to your application. Brazilian CPF is `{"type": "tax_number", "country": "BR"}`.

**`subject.attributes`** (all optional): `first_name` (max 128), `last_name` (max 128), `full_name` (max 256), `date_of_birth` (`YYYY-MM-DD`), `nationality` (max 3), `gender` (max 16), `address` (max 512), `city` (max 128), `state` (max 128), `postal_code` (max 32).

**`context`** (all optional):

| Field | Type | Description |
|---|---|---|
| `ip_address` | string | The attempt's IP address (IPv4 or IPv6). `ip_risk` needs a public address; private or reserved addresses skip it with `missing_required_input` |
| `user_agent` | string | Max 512 chars |
| `country` | string | Country the subject claims to be in (max 3). Contextual only, never proof of identity |
| `purpose` | string | Max 128 chars |
| `consent_obtained` | boolean | Your assertion that the user consented. Required by `biometric_identity` and by registry sources that need consent |

### Modules

| Module | Needs | Feeds | Billing |
|---|---|---|---|
| `normalization` | Runs even with `include: []` | `inputs[]` | Free |
| `email_risk` | An `email` identifier | `contact` | Paid |
| `phone_risk` | A `phone` identifier | `contact` | Paid |
| `email_social` | A valid `email` identifier (profile `2026-09-14`+). No OTP is sent | `enrichment` | Paid add-on |
| `phone_social` | A valid `phone` identifier (profile `2026-09-14`+). No OTP is sent | `enrichment` | Paid add-on |
| `ip_risk` | A public `context.ip_address` | `device_network` | Paid |
| `database_validation` | A government identifier with its `country`, where Didit has a registry source for it, plus the attributes that source needs | `identity` | Paid, price varies by country ([Database Validation pricing](https://docs.didit.me/getting-started/database-validation-pricing)) |
| `networks_same_org` | Something to look up in your private network history (identifier or public IP) | `behavioral` | Free |
| `networks_cross_org` | An email, phone or properly namespaced document identifier; organization participation and entitlement (profile `2026-09-14.1`+) | `fraud_network` | Free, uses the organization's network read budget |
| `biometric_identity` | `subject.selfie` + a `tax_number` with `country: "BR"` + `context.consent_obtained: true`; organization entitlement (profile `2026-09-14.2`) | `identity`, `identity_relationship` | Paid per check at your Database Validation rate |

### Example

```python
import requests

client_ip = "<the user's public IP>"  # private/reserved addresses skip ip_risk

response = requests.post(
    "https://verification.didit.me/v3/fraud/checks/",
    headers={"x-api-key": "YOUR_API_KEY", "Content-Type": "application/json"},
    json={
        "profile_version": "2026-09-14.1",
        "client_reference": "signup-attempt-001",
        "subject": {
            "identifiers": [
                {"type": "email", "value": "user@example.com"},
                {"type": "phone", "value": "+14155552671"},
            ],
            "attributes": {"first_name": "Alex", "last_name": "Example"},
        },
        "context": {"ip_address": client_ip, "user_agent": "Mozilla/5.0"},
        "checks": {
            "include": ["email_risk", "phone_risk", "ip_risk", "networks_same_org", "networks_cross_org"]
        },
        "vendor_data": "user-42",
    },
    timeout=60,
)
check = response.json()
print(check["recommendation"], check["next_action"])
```

```typescript
const clientIp = "<the user's public IP>";
const response = await fetch("https://verification.didit.me/v3/fraud/checks/", {
  method: "POST",
  headers: { "x-api-key": "YOUR_API_KEY", "Content-Type": "application/json" },
  body: JSON.stringify({
    profile_version: "2026-09-14.1",
    client_reference: "signup-attempt-001",
    subject: {
      identifiers: [{ type: "email", value: "user@example.com" }],
      attributes: { first_name: "Alex", last_name: "Example" },
    },
    context: { ip_address: clientIp },
    checks: { include: ["email_risk", "ip_risk", "networks_same_org"] },
  }),
});
const check = await response.json();
```

### Response (200 OK)

Abbreviated. A real response lists every module of the profile in `modules` and all five dimensions in `risk`, and also carries `inputs`, `attribute_evidence`, `compound_evidence`, `network`, `coverage`, `usage` (and `enrichment` from `2026-09-14`); see the field reference.

```json
{
  "check_id": "6f1c2d3e-4a5b-4c6d-8e9f-0a1b2c3d4e5f",
  "request_id": "0b9a8c7d-6e5f-4a3b-9c2d-1e0f9a8b7c6d",
  "client_reference": "signup-attempt-001",
  "processing_status": "completed",
  "profile_id": "standard",
  "profile_version": "2026-09-14.1",
  "created_at": "2026-10-12T09:30:00.123456+00:00",
  "completed_at": "2026-10-12T09:30:02.456789+00:00",
  "modules": [
    {"module": "biometric_identity", "status": "skipped", "reason": "not_requested", "latency_ms": 0, "freshness": null, "billable_units": 0}
  ],
  "risk": [
    {"dimension": "contact", "score": 12, "band": "low", "availability": "available",
     "requested_but_unavailable": false, "reason_codes": [], "evidence_indexes": [0]}
  ],
  "recommendation": "approve",
  "next_action": "none",
  "decision_reasons": [],
  "vendor_data": "user-42",
  "metadata": null
}
```

---

## Plan a Fraud Check

```
POST https://verification.didit.me/v3/fraud/checks/plan/
```

Send the same body you will send to `POST /v3/fraud/checks/`. `subject` is optional for a plan; running a check still needs at least one identifier. Planning creates no check or session, calls no supplier, reads no network history and charges nothing.

Sandbox example (live applications get prices from their own rate card; sandbox prices are `0`):

```json
{
  "profile_id": "standard",
  "profile_version": "2026-09-14.1",
  "modules": [
    {"module": "email_risk", "available": true, "availability_reason": null,
     "will_run": true, "selection_reason": null, "estimated_price": "0"},
    {"module": "phone_risk", "available": false, "availability_reason": "missing_required_input",
     "will_run": false, "selection_reason": "missing_required_input", "estimated_price": "0"}
  ],
  "estimated_price": "0",
  "currency": "USD",
  "is_sandbox": true,
  "can_afford": true
}
```

| Field | Meaning |
|---|---|
| `modules[].available` / `availability_reason` | Whether the supplied inputs can support the module, and why not |
| `modules[].will_run` / `selection_reason` | Whether your selection will run it, and why not (`not_requested`, `excluded_by_caller`, ...) |
| `modules[].estimated_price` | Decimal string in `currency`. `null` means unavailable or unpriced, **not free** (e.g. `database_validation` before an identifier's country is known, since its price varies by country) |
| `estimated_price` | Total of the selected runnable modules; `null` if any of them is unpriced |
| `can_afford` | Whether your balance or billing arrangement covers the total |
| `is_sandbox` | `true` for sandbox applications (prices are `0`) |

A plan is not a reservation: execution re-checks eligibility and pricing, and an external source may still not answer. Re-plan after changing identifiers, context or selections.

---

## Get a Fraud Check

```
GET https://verification.didit.me/v3/fraud/checks/{check_id}/
```

Returns the stored result (same shape as the run response). No re-run, no charge. Returns `404` for an unknown, unfinished or deleted check, or one that belongs to another application. If your organization loses global network access, reads hide the shared aggregates and their derived risk evidence; the original `recommendation` is kept.

---

## Recommendation Handling

| `recommendation` | `next_action` | Action |
|---|---|---|
| `approve` | `none` | Proceed |
| `review` | `manual_review` | Queue for an analyst; read `decision_reasons`, `risk[]` and `modules[]` |
| `reject` | `none` | Block or escalate per your policy |

`next_action` can also be `step_up` (ask the user for stronger verification) or `resubmit_capture` (ask the user to capture again). Branch on every value.

- A check where nothing could be evaluated is `review`, never `approve`.
- `risk[].requested_but_unavailable: true` means you supplied everything the dimension needed and the source still could not answer; such a check is never approved on the strength of the other dimensions.
- A disclosed global-network signal triggers `review`, never an automatic reject or an identity match.
- `recommendation` is advisory: it does not change the status of any other record.

### Module status and reason

`modules[].status`: `planned`, `completed`, `skipped`, `failed`. When not completed, `reason` says why:

| `reason` | Meaning |
|---|---|
| `not_requested` | Not in your selection (or the profile defaults) |
| `excluded_by_caller` | Listed in `checks.exclude` |
| `missing_required_input` | The input it needs was not supplied or not usable |
| `not_available_in_profile_version` | The pinned profile version does not offer it |
| `consent_required` | `context.consent_obtained` was not `true` |
| `unsupported_region` | The identifier's country is not covered |
| `source_unavailable` | The source could not answer (timeout or error). Not billed. Not a mismatch |

### Risk bands and availability

`band`: `low`, `medium`, `high`, `unknown` (`unknown` means no evidence, not low risk). `availability`: `available`, `not_requested`, `no_reference`, `insufficient_history`, `unsupported_region`, `source_unavailable`. A shared email, device or identifier is an observed connection, not proof that two accounts are the same person or committed fraud.

---

## Selfie to CPF (`biometric_identity`)

Pin `2026-09-14.2`, select `biometric_identity`, send a `tax_number` identifier with `country: "BR"`, `subject.selfie`, and `context.consent_obtained: true`. Missing consent gives `consent_required`; a non-Brazilian identifier gives `unsupported_region`.

`identity_relationship.result` is `match`, `mismatch`, `inconclusive` or `no_reference`. `inconclusive` needs review and is never a mismatch. The result only establishes the selfie-to-CPF relationship: it does not validate names or birth date, prove liveness, or search faces. Timeouts and source errors are unavailable and not billed; completed inconclusive answers are billed. The selfie is not returned or stored as session media by this check.

## Global fraud network (`networks_cross_org`)

Queries supported email, phone and namespaced document identifiers against the shared network. Needs organization participation and entitlement; no per-lookup charge; the plan never queries it. On completion `network.cross_organization` has `signals_checked` and disclosed aggregate `insights` (signal type, outcome classes, contributor count, recency bucket, and industry categories when disclosure is enabled). It never identifies another organization, account, person or verification; results below the disclosure threshold are omitted, so an empty list does not prove absence of fraud history. See the **didit-fraud-networks** skill for network participation and settings.

---

## Idempotency and Retries

- `client_reference` + same body: returns the stored result (same status code), no new execution, no new charge, while that check exists.
- `client_reference` + different body: `409`.
- Same `client_reference` while the first call is still running: `409` with `Retry-After: 30`. Retry the same request after that many seconds.
- Without `client_reference` every call runs and bills again.
- Deleting the associated verification session deletes the Fraud Check result; `GET` then returns `404`.

---

## Error Responses

| Code | Meaning | Action |
|---|---|---|
| `400` | Invalid request | Read the field errors in the response body |
| `400` | `{"error": "Unknown profile or profile_version."}` | Use `standard` and a published version |
| `401` | The API key has expired | Rotate it or create a new key in **Developers > API keys** |
| `403` | Missing, wrong or revoked API key; a scoped key without access to this endpoint; a request from outside the key's IP allowlist; or not enough credits | Read the message in `detail` or `error`: fix the `x-api-key` header or the key's access, or top up |
| `403` | Contract-billed organization whose rate card does not price a selected module | Remove the module or contact Didit to add it |
| `404` | `GET`: check unknown, unfinished, deleted or another application's | Check the `check_id` and the key's application |
| `409` | `client_reference` reused with a different body; a check with that reference is still running (`Retry-After` header); or the verification was deleted before the check completed | Use a new reference, or retry the identical request after `Retry-After` |
| `429` | Rate limit: 300 POST/PATCH/DELETE and 600 GET requests a minute per key | Wait the `Retry-After` seconds, then retry |

The credit check runs before any module: a check is never half-run on an account that cannot pay. `409` responses are not charged.

---

## Response Field Reference

| Field | Type | Description |
|---|---|---|
| `check_id` | uuid | Use with `GET /v3/fraud/checks/{check_id}/` |
| `request_id` | uuid | Native verification session for this check, when one was created (always from `2026-09-14`) |
| `client_reference` | string/null | Echo |
| `processing_status` | string | `pending`, `running`, `completed`, `failed` (returned results are `completed`) |
| `profile_id` / `profile_version` | string | The profile that produced the result |
| `created_at` / `completed_at` | datetime | ISO 8601 |
| `inputs[]` | array | One per submitted identifier: `reference` (redacted handle, never the raw value), `type`, `namespace`, `quality`, `normalization`, `availability` |
| `modules[]` | array | `module`, `status`, `reason`, `latency_ms`, `freshness`, `billable_units` |
| `attribute_evidence[]` | array | Field-level evidence from the sources that ran |
| `compound_evidence[]` | array | Evidence combining several inputs |
| `risk[]` | array | One per dimension: `dimension`, `score` (integer or `null`), `band`, `availability`, `requested_but_unavailable`, `reason_codes`, `evidence_indexes` (positions in `attribute_evidence`) |
| `network` | object | `same_organization` (private history) and `cross_organization` (global network); each says why it is unavailable when it did not complete |
| `enrichment` | object | Profiles `2026-09-14`+: `email_social` / `phone_social` results, `null` when not completed |
| `identity_relationship` | object | Only when `biometric_identity` produced an answer: `result`, `reference_type`, `country`, `availability`, `reason_codes` |
| `recommendation` | string | `approve`, `review`, `reject` |
| `next_action` | string | `none`, `manual_review`, `step_up`, `resubmit_capture` |
| `decision_reasons` | array | Reason codes behind the recommendation |
| `coverage` | object | Which sources and inputs could be covered |
| `usage[]` | array | Per-module usage lines, billable and not billable |
| `vendor_data` / `metadata` | | Echo |

---

## IP Risk API

```
POST https://verification.didit.me/v3/ip/risk/
```

Server-to-server IP scoring: geolocation, network ownership, VPN/Tor and data-center flags, threat data and claimed-country mismatch. Creates an API session (`request_id`). Live calls are billable once the lookup starts; no list price is published (check [didit.me/pricing](https://didit.me/pricing)). Sandbox keys return deterministic approved data without credits, sessions or network contribution.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `ip_address` | string | **Yes** | IPv4 or IPv6 address |
| `claimed_country` | string | No | ISO 3166-1 alpha-2 or alpha-3 country the user claims (max 3). Enables `country_mismatch` |
| `user_agent` | string | No | Max 512 chars. Stored as context; not device fingerprinting |
| `vendor_data` | string | No | Stored on the API session and echoed |
| `metadata` | object | No | Stored on the API session and echoed |

```python
import requests

client_ip = "<the IP address to score>"
response = requests.post(
    "https://verification.didit.me/v3/ip/risk/",
    headers={"x-api-key": "YOUR_API_KEY", "Content-Type": "application/json"},
    json={"ip_address": client_ip, "claimed_country": "ESP", "vendor_data": "lead-123"},
    timeout=15,
)
result = response.json()
print(result["status"], result["ip"]["country_mismatch"])
```

```json
{
  "request_id": "9a96ed2a-721e-4b86-8cbf-d61eda529279",
  "status": "Approved",
  "ip": {
    "status": "Approved",
    "ip_address": "192.0.2.10",
    "ip_country": "Spain",
    "ip_country_code": "ES",
    "ip_state": "Madrid",
    "ip_city": "Madrid",
    "latitude": 40.4168,
    "longitude": -3.7038,
    "isp": "Example Telecom",
    "organization": "Example Telecom SA",
    "is_vpn_or_tor": false,
    "is_data_center": false,
    "time_zone": "Europe/Madrid",
    "time_zone_offset": "+0200",
    "asn_number": 3352,
    "asn_organization": "EXAMPLE-TELECOM",
    "connection_type": "broadband",
    "carrier": "Example Telecom",
    "proxy_type": null,
    "claimed_country": "ESP",
    "country_mismatch": false,
    "threat": {}
  },
  "vendor_data": "lead-123",
  "metadata": null,
  "created_at": "2026-09-01T10:30:00.123456+00:00"
}
```

| `status` | Meaning |
|---|---|
| `Approved` | No VPN/Tor, no data center, no country conflict (or no enrichment data) |
| `In Review` | Resolved country conflicts with `claimed_country`, or the address is VPN, Tor or data-center infrastructure |

- Compare countries with `ip.country_mismatch`, not by string-comparing `ip_country_code`. It is `null` when no enrichment data came back.
- Enrichment is best effort: with no usable data the response is `Approved` with `ip.ip_address: null`, `ip.country_mismatch: null` and `ip.threat: {}`. Any single field can be `null`.
- `latitude` / `longitude` are approximate network geolocation, not device location. `threat` is free-form diagnostic detail, not a stable contract.
- Errors: the shared `400` / `401` / `403` / `429` rows above apply (`403` with `{"error": "You don't have enough credits to perform this request."}` when the balance is too low).
- Device fingerprints are not available server-to-server; for hosted and SDK sessions they are on the session decision. See the **didit-event-monitoring** skill for the device lane.

---

## Common Workflows

### Signup risk gate

```
1. POST /v3/fraud/checks/plan/ with the body you intend to send
   -> check will_run per module, estimated_price, can_afford
2. POST /v3/fraud/checks/ with the same body + a unique client_reference
3. approve -> continue onboarding
   review  -> manual review queue (decision_reasons, risk[], modules[])
   reject  -> block or escalate
4. Store check_id (and request_id) with your user; re-read with GET /v3/fraud/checks/{check_id}/
```

### Safe retry after a timeout

```
1. Resend the identical body with the same client_reference
2. 200 -> stored result, no new charge
   409 + Retry-After -> still running: wait, then resend the identical request
   409 without Retry-After -> the body differs: use a new client_reference
```

### Brazil selfie to CPF

```
1. Collect consent and a selfie
2. POST /v3/fraud/checks/plan/ with profile_version "2026-09-14.2",
   identifiers [{"type": "tax_number", "value": "<CPF>", "country": "BR"}],
   subject.selfie, context.consent_obtained true, checks.include ["biometric_identity"]
3. Run it; read identity_relationship.result (inconclusive -> review)
```

---

## Utility Scripts

**run_fraud_check.py**: plan, run and read Fraud Checks from the command line.

```bash
# Requires: pip install requests
export DIDIT_API_KEY="your_api_key"
python scripts/run_fraud_check.py plan --email user@example.com --phone +14155552671 \
    --include email_risk,phone_risk --profile-version 2026-09-14.1
python scripts/run_fraud_check.py run --email user@example.com --ip "$USER_PUBLIC_IP" \
    --include email_risk,ip_risk,networks_same_org --client-reference signup-001
python scripts/run_fraud_check.py run --tax-number 12345678909 --country BR \
    --selfie selfie.jpg --consent --include biometric_identity --profile-version 2026-09-14.2
python scripts/run_fraud_check.py get 6f1c2d3e-4a5b-4c6d-8e9f-0a1b2c3d4e5f
```
