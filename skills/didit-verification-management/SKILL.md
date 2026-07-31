---
name: didit-verification-management
description: >
  Full Didit identity verification platform management — account creation, API keys,
  sessions, bulk imports, workflows, questionnaires, users (KYC), businesses (KYB),
  transactions, billing, branding, lists (block/allow), and webhooks. Use when someone
  needs to create a Didit account, get API keys, set up verification workflows, create or
  retrieve verification sessions, approve or decline sessions, manage users or businesses,
  monitor transactions, check credit balance, top up credits, configure lists, configure
  webhooks programmatically, handle webhook signatures, or perform any platform
  administration. 60+ endpoints across 13 categories.
version: 5.0.0
metadata:
  openclaw:
    requires:
      env: []
    primaryEnv: DIDIT_API_KEY
    emoji: "🛡️"
    homepage: https://docs.didit.me
---

# Didit Identity Verification Platform

The single skill for the entire Didit verification platform. Covers account creation, session management, bulk imports, workflow configuration, questionnaires, user (KYC) and business (KYB) management, transaction monitoring, billing, branding customization, lists (block/allow), and webhook configuration — 60+ endpoints across 13 categories.

**For standalone verification APIs** (ID scan, liveness, face match, AML, etc.), see the individual `didit-*` skills.

**API Reference Links:**
- **Account Setup:** [Register](https://docs.didit.me/auth-api/register) | [Verify Email](https://docs.didit.me/auth-api/verify-email) | [Login](https://docs.didit.me/auth-api/login) | [Get Credentials](https://docs.didit.me/auth-api/get-credentials)
- **Sessions:** [Create](https://docs.didit.me/sessions-api/create-session) | [Retrieve](https://docs.didit.me/sessions-api/retrieve-session) | [List](https://docs.didit.me/sessions-api/list-sessions) | [Delete](https://docs.didit.me/sessions-api/delete-session) | [Update Status](https://docs.didit.me/sessions-api/update-status) | [PDF](https://docs.didit.me/sessions-api/generate-pdf) | [Share](https://docs.didit.me/sessions-api/share-session/share) | [Import](https://docs.didit.me/sessions-api/share-session/import)
- **Workflows:** [Create](https://docs.didit.me/management-api/workflows/create) | [List](https://docs.didit.me/management-api/workflows/list) | [Get](https://docs.didit.me/management-api/workflows/get) | [Update](https://docs.didit.me/management-api/workflows/update) | [Delete](https://docs.didit.me/management-api/workflows/delete)
- **Questionnaires:** [Create](https://docs.didit.me/management-api/questionnaires/create) | [List](https://docs.didit.me/management-api/questionnaires/list) | [Get](https://docs.didit.me/management-api/questionnaires/get) | [Update](https://docs.didit.me/management-api/questionnaires/update) | [Delete](https://docs.didit.me/management-api/questionnaires/delete)
- **Users (KYC):** [List](https://docs.didit.me/management-api/users/list) | [Create](https://docs.didit.me/management-api/users/create) | [Get](https://docs.didit.me/management-api/users/get) | [Update](https://docs.didit.me/management-api/users/update) | [Update Status](https://docs.didit.me/management-api/users/update-status) | [Delete](https://docs.didit.me/management-api/users/delete)
- **Businesses (KYB):** [List](https://docs.didit.me/management-api/businesses/list) | [Create](https://docs.didit.me/management-api/businesses/create) | [Get](https://docs.didit.me/management-api/businesses/get) | [Update](https://docs.didit.me/management-api/businesses/update) | [Update Status](https://docs.didit.me/management-api/businesses/update-status) | [Delete](https://docs.didit.me/management-api/businesses/delete)
- **Transactions:** [List](https://docs.didit.me/management-api/transactions/list) | [Create](https://docs.didit.me/management-api/transactions/create) | [Get](https://docs.didit.me/management-api/transactions/get)
- **Billing:** [Balance](https://docs.didit.me/management-api/billing/balance) | [Top Up](https://docs.didit.me/management-api/billing/top-up)
- **Customization:** [Get](https://docs.didit.me/management-api/customization/get) | [Update](https://docs.didit.me/management-api/customization/update)
- **Lists (block/allow/custom):** [List](https://docs.didit.me/management-api/lists/list) | [Create](https://docs.didit.me/management-api/lists/create) | [Get](https://docs.didit.me/management-api/lists/get) | [Update](https://docs.didit.me/management-api/lists/update) | [Delete](https://docs.didit.me/management-api/lists/delete) | [Entries](https://docs.didit.me/management-api/lists/list-entries) | [Add Entry](https://docs.didit.me/management-api/lists/create-entry) | [Upload Face](https://docs.didit.me/management-api/lists/upload-face) | [Delete Entry](https://docs.didit.me/management-api/lists/delete-entry)
- **Session Operations:** [Batch Delete](https://docs.didit.me/management-api/sessions/batch-delete) | [List Reviews](https://docs.didit.me/management-api/sessions/list-reviews) | [Create Review](https://docs.didit.me/management-api/sessions/create-review)
- **Bulk Import:** [Import Verifications](https://docs.didit.me/sessions-api/import-verifications)
- **Webhook Destinations:** [List](https://docs.didit.me/management-api/webhook/list-destinations) | [Create](https://docs.didit.me/management-api/webhook/create-destination) | [Get](https://docs.didit.me/management-api/webhook/get-destination) | [Update](https://docs.didit.me/management-api/webhook/update-destination) | [Delete](https://docs.didit.me/management-api/webhook/delete-destination)
- **Guides:** [Programmatic Registration](https://docs.didit.me/integration/programmatic-registration) | [Webhooks](https://docs.didit.me/integration/webhooks) | [AI Agent Integration](https://docs.didit.me/integration/ai-agent-integration) | [API Overview](https://docs.didit.me/sessions-api/management-api)

---

## Getting Started — Zero to Verifying

Go from nothing to a live verification link in **4 API calls**, no browser needed:

```python
import requests

# 1. Register (any email, no business email required)
requests.post("https://apx.didit.me/auth/v2/programmatic/register/",
    json={"email": "you@gmail.com", "password": "MyStr0ng!Pass"})

# 2. Check email for 6-char OTP, then verify → get api_key
resp = requests.post("https://apx.didit.me/auth/v2/programmatic/verify-email/",
    json={"email": "you@gmail.com", "code": "A3K9F2"})
api_key = resp.json()["application"]["api_key"]
headers = {"x-api-key": api_key, "Content-Type": "application/json"}

# 3. Create a KYC workflow — pass an ordered `features` array (not is_*_enabled flags)
wf = requests.post("https://verification.didit.me/v3/workflows/",
    headers=headers,
    json={"workflow_label": "My KYC", "features": [
        {"feature": "OCR"},
        {"feature": "LIVENESS", "config": {"face_liveness_method": "PASSIVE"}},
        {"feature": "FACE_MATCH"},
    ]}).json()

# 4. Create a session → send user to the URL
session = requests.post("https://verification.didit.me/v3/session/",
    headers=headers,
    json={"workflow_id": wf["uuid"], "vendor_data": "user-123"}).json()
print(f"Send user to: {session['url']}")
```

**To add credits:** `GET /v3/billing/balance/` to check, `POST /v3/billing/top-up/` with `{"amount_in_dollars": 50}` for a Stripe checkout link.

---

## Authentication

Two auth schemes are used across the platform:

| Endpoints | Auth | Header |
|---|---|---|
| Register, Verify Email, Login | **None** | (unauthenticated) |
| List Organizations, Get Credentials | **Bearer** | `Authorization: Bearer <access_token>` |
| Everything else (sessions, workflows, etc.) | **API Key** | `x-api-key: <api_key>` |

Get your `api_key` via programmatic registration (above) or from [Didit Business Console](https://business.didit.me) → API & Webhooks.

---

## Account Setup

**Base URL:** `https://apx.didit.me/auth/v2`

### 1. Register

```
POST /programmatic/register/
```

| Body | Type | Required | Description |
|---|---|---|---|
| `email` | string | **Yes** | Any email address |
| `password` | string | **Yes** | Min 8 chars, 1 upper, 1 lower, 1 digit, 1 special |

**Response (201):** `{"message": "Registration successful...", "email": "..."}`

Rate limit: 5 per IP per hour.

### 2. Verify Email & Get Credentials

```
POST /programmatic/verify-email/
```

| Body | Type | Required | Description |
|---|---|---|---|
| `email` | string | **Yes** | Same email from register |
| `code` | string | **Yes** | 6-character alphanumeric OTP from email |

**Response (200):**

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 86400,
  "organization": {"uuid": "...", "name": "..."},
  "application": {"uuid": "...", "client_id": "...", "api_key": "YOUR_KEY_HERE"}
}
```

**`application.api_key`** is the `x-api-key` for all subsequent calls.

### 3. Login (Existing Accounts)

```
POST /programmatic/login/
```

| Body | Type | Required | Description |
|---|---|---|---|
| `email` | string | **Yes** | Account email |
| `password` | string | **Yes** | Account password |

**Response (200):** `{"access_token": "...", "refresh_token": "...", "expires_in": 86400}`

Progressive lockout: 5 fails = 15min, 10 = 1hr, 20 = 24hr.

### 4. List Organizations

```
GET /organizations/me/
```

**Auth:** `Authorization: Bearer <access_token>`

**Response (200):** Array of `{"uuid": "...", "name": "...", "contact_email": "..."}`

### 5. Get Application Credentials

```
GET /organizations/me/{org_id}/applications/{app_id}/
```

**Auth:** `Authorization: Bearer <access_token>`

**Response (200):** `{"uuid": "...", "client_id": "...", "api_key": "..."}`

---

## Workflows

**Base URL:** `https://verification.didit.me/v3`

Workflows define verification steps, thresholds, and accepted documents. Each has a UUID used as `workflow_id` when creating sessions. You compose a workflow by listing **features in execution order** — there is no `workflow_type` field on the create API (sending one returns `400`). KYC vs KYB is determined by which features you include.

**Feature values** (use the exact uppercase strings in the `features` array):
`OCR`, `NFC`, `LIVENESS`, `FACE_MATCH`, `PROOF_OF_ADDRESS`, `QUESTIONNAIRE`, `PHONE_VERIFICATION`, `EMAIL_VERIFICATION`, `DATABASE_VALIDATION`, `AML`, `IP_ANALYSIS`, `AGE_ESTIMATION`, `KYB_REGISTRY`, `KYB_DOCUMENTS`, `KYB_KEY_PEOPLE`.

**Common compositions:**

| Goal | Feature list (in order) |
|---|---|
| Full KYC (ID + selfie) | `OCR`, `LIVENESS`, `FACE_MATCH`, optionally `AML`, `NFC` |
| Age gating | `AGE_ESTIMATION`, `LIVENESS` (add `OCR` for an ID fallback) |
| Biometric re-auth (no document) | `LIVENESS`, `FACE_MATCH` (against a stored portrait) |
| Proof of address | `PROOF_OF_ADDRESS` |
| Questionnaire | `QUESTIONNAIRE` (set `config.questionnaire_uuid`) |
| Email / phone only | `EMAIL_VERIFICATION` / `PHONE_VERIFICATION` |
| KYB (business) | `KYB_REGISTRY`, `KYB_DOCUMENTS`, `KYB_KEY_PEOPLE`, optionally `AML` |

**Ordering rule:** put dependency features first — `OCR` before `FACE_MATCH`, `NFC`, `DATABASE_VALIDATION`, or any `AML` check that relies on document data.

### 1. List Workflows

```
GET /v3/workflows/
```

**Response (200):** Array of workflow objects with `uuid`, `workflow_label`, `workflow_type`, `is_default`, `features`, `total_price`.

### 2. Create Workflow

```
POST /v3/workflows/
```

The body is a **strict whitelist** — only the fields below are accepted, and any unknown key (including `workflow_type` or flat `is_*_enabled` flags) is rejected with `400`. The only required field is `features`.

| Body | Type | Default | Description |
|---|---|---|---|
| `features` | array | — | **Required.** Verification features in execution order. Each item: `{ "feature": "<UPPERCASE>", "config": { ... }, "label": "optional" }`. |
| `workflow_label` | string | `ID Verification` | Display name (max 50 chars) — always set it |
| `is_default` | boolean | `false` | Set as default workflow for new sessions |
| `status` | string | `published` | `"published"` (default when omitted) or `"draft"` to save without publishing |
| `is_white_label_enabled` | boolean | `false` | White-label the verification UI |
| `is_desktop_allowed` | boolean | — | Allow desktop verification |
| `max_retry_attempts` | integer | — | Max retries per session |
| `retry_window_days` | integer | — | Days within which retries are allowed |
| `face_liveness_max_attempts` | integer | — | Max liveness attempts |
| `face_match_max_attempts` | integer | — | Max face-match attempts |
| `session_expiration_time` | integer | — | Session lifetime (seconds) |

**Per-feature `config`** (see the [feature configs reference](https://docs.didit.me/management-api/workflows/feature-configs)): e.g. `LIVENESS` → `face_liveness_method` (`"PASSIVE"`, `"ACTIVE_3D"`, `"FLASHING"`), `face_liveness_score_decline_threshold`; `FACE_MATCH` → `face_match_score_decline_threshold`, `face_match_score_review_threshold`; `AML` → `aml_score_approve_threshold` (default 80); `OCR` → `duplicated_user_action` (`no_action`/`review`/`decline`), `documents_allowed` (omit or `{}` to accept all); `QUESTIONNAIRE` → `questionnaire_uuid`.

**Response (201):** Workflow object with `uuid`.

```python
wf = requests.post("https://verification.didit.me/v3/workflows/",
    headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
    json={"workflow_label": "KYC + AML", "features": [
        {"feature": "OCR"},
        {"feature": "LIVENESS", "config": {"face_liveness_method": "PASSIVE"}},
        {"feature": "FACE_MATCH", "config": {"face_match_score_decline_threshold": 40,
                                             "face_match_score_review_threshold": 60}},
        {"feature": "AML", "config": {"aml_score_approve_threshold": 80}},
    ]}).json()
```

### 3. Get Workflow

```
GET /v3/workflows/{settings_uuid}/
```

### 4. Update Workflow

```
PATCH /v3/workflows/{settings_uuid}/
```

Partial update — only send fields to change.

### 5. Delete Workflow

```
DELETE /v3/workflows/{settings_uuid}/
```

**Response:** `204 No Content`. Existing sessions are not affected.

---

## Sessions

**Base URL:** `https://verification.didit.me/v3`

Sessions are the core unit of verification. Every verification starts by creating a session linked to a workflow.

**Lifecycle:** `Create → User verifies at URL → Webhook/poll decision → Optionally update status`

**Statuses:** `Not Started`, `In Progress`, `In Review`, `Approved`, `Declined`, `Expired`, `Abandoned`, `Kyc Expired`, `Resubmitted`, `Awaiting User` (there is no `Pending` status)

**Rate limits:** generic GET and session creation 600/min; writes 300/min; decision polling 100/min; PDF generation 50/min.

### 1. Create Session

```
POST /v3/session/
```

| Body | Type | Required | Description |
|---|---|---|---|
| `workflow_id` | uuid | **Yes** | Workflow UUID |
| `vendor_data` | string | No | Your user identifier |
| `callback` | url | No | Redirect URL (Didit appends `verificationSessionId` + `status`) |
| `callback_method` | string | No | `"initiator"`, `"completer"`, or `"both"` |
| `metadata` | JSON string | No | Custom data stored with session |
| `language` | string | No | ISO 639-1 UI language |
| `contact_details.email` | string | No | Pre-fill email for email verification step |
| `contact_details.phone` | string | No | Pre-fill phone (E.164) for phone verification step |
| `contact_details.send_notification_emails` | boolean | No | Send status update emails to user |
| `contact_details.email_lang` | string | No | Language for email notifications (ISO 639-1) |
| `expected_details.first_name` | string | No | Triggers mismatch warning if different (fuzzy match) |
| `expected_details.last_name` | string | No | Expected last name (fuzzy match) |
| `expected_details.date_of_birth` | string | No | `YYYY-MM-DD` |
| `expected_details.gender` | string | No | `"M"`, `"F"`, or `null` |
| `expected_details.nationality` | string | No | ISO 3166-1 alpha-3 country code |
| `expected_details.id_country` | string | No | ISO alpha-3 for expected ID document country (overrides nationality) |
| `expected_details.poa_country` | string | No | ISO alpha-3 for expected PoA document country |
| `expected_details.address` | string | No | Expected address (human-readable, for PoA matching) |
| `expected_details.identification_number` | string | No | Expected document/personal/tax number |
| `expected_details.ip_address` | string | No | Expected IP address (logs warning if different) |
| `portrait_image` | base64 | No | Reference portrait for Biometric Auth (max 1MB) |

**Response (201):**

```json
{
  "session_id": "...",
  "session_number": 1234,
  "session_token": "abcdef123456",
  "url": "https://verify.didit.me/session/abcdef123456",
  "status": "Not Started",
  "workflow_id": "..."
}
```

Send the user to `url` to complete verification.

### 2. Retrieve Session (Get Decision)

```
GET /v3/session/{sessionId}/decision/
```

Returns all verification results. Presigned image URLs expire after 4 hours.

**Response (200):** Full decision with `status`, `features`, `id_verifications`, `liveness_checks`, `face_matches`, `aml_screenings`, `phone_verifications`, `email_verifications`, `poa_verifications`, `database_validations`, `ip_analyses`, `reviews`.

### 3. List Sessions

```
GET /v3/sessions/
```

| Query | Type | Default | Description |
|---|---|---|---|
| `vendor_data` | string | — | Filter by your user identifier |
| `status` | string | — | Filter by status (e.g. `Approved`, `Declined`, `In Review`) |
| `session_kind` | string | — | `user` (KYC), `business` (KYB), or `all` |
| `country` | string | — | Filter by ISO 3166-1 alpha-3 country code |
| `workflow_id` | string | — | Filter by workflow UUID |
| `search` | string | — | Free-text search |
| `date_from` / `date_to` | string | — | ISO date range bounds |
| `offset` | integer | `0` | Number of items to skip |
| `limit` | integer | `50` | Max items to return |

**Response (200):** Paginated list with `count`, `next`, `previous`, `results[]`.

### 4. Delete Session

```
DELETE /v3/session/{sessionId}/delete/
```

**Response:** `204 No Content`. Permanently deletes all associated data.

### 5. Batch Delete Sessions

```
POST /v3/sessions/delete/
```

| Body | Type | Description |
|---|---|---|
| `session_numbers` | array | List of session numbers to delete |
| `delete_all` | boolean | Delete all sessions (use with caution) |

### 6. Update Session Status

```
PATCH /v3/session/{sessionId}/update-status/
```

| Body | Type | Required | Description |
|---|---|---|---|
| `new_status` | string | **Yes** | `"Approved"`, `"Declined"`, or `"Resubmitted"` |
| `comment` | string | No | Reason for change |
| `send_email` | boolean | No | Send notification email |
| `email_address` | string | Conditional | Required when `send_email` is `true` |
| `email_language` | string | No | Email language (default: `"en"`) |
| `nodes_to_resubmit` | array | No | For Resubmitted: `[{"node_id": "feature_ocr", "feature": "OCR"}]` |

Resubmit requires session to be Declined, In Review, or Abandoned.

**Reviewer data overrides** — correct extracted data on a session (only send fields to change):
- `PATCH /v3/session/{sessionId}/update-data/` — KYC/ID fields (`document_type`, `document_number`, `date_of_birth`, `first_name`, `last_name`, `gender` `M`/`F`/`U`, `address`, `nationality`, `extra_fields`, …).
- `PATCH /v3/session/{sessionId}/update-poa-data/` — Proof of Address fields (`document_type`, `issuer`, `issue_date`, `poa_address`, `name_on_document`, …).

### 7. Generate PDF Report

```
GET /v3/session/{sessionId}/generate-pdf
```

Rate limit: 50 req/min.

### 8. Share Session

```
POST /v3/session/{sessionId}/share/
```

Generates a `share_token` for B2B KYC sharing. Only works for finished sessions.

### 9. Import Shared Session

```
POST /v3/session/import-shared/
```

| Body | Type | Required | Description |
|---|---|---|---|
| `share_token` | string | **Yes** | Token from sharing partner |
| `trust_review` | boolean | **Yes** | `true`: keep original status; `false`: set to "In Review" |
| `workflow_id` | string | **Yes** | Your workflow ID |
| `vendor_data` | string | No | Your user identifier |

A session can only be imported once per partner application.

### 10. List Session Reviews

```
GET /v3/sessions/{session_id}/reviews/
```

**Response (200):** Array of review activity items:

```json
[
  {
    "id": 1,
    "action": "status_change",
    "old_status": "In Review",
    "new_status": "Approved",
    "note": "Document verified manually",
    "created_at": "2025-06-01T15:00:00Z"
  }
]
```

### 11. Create Session Review

```
POST /v3/sessions/{session_id}/reviews/
```

| Body | Type | Required | Description |
|---|---|---|---|
| `new_status` | string | **Yes** | `"Approved"`, `"Declined"`, or `"In Review"` |
| `comment` | string | No | Review note |

**Response (201):** The created review item.

---

## Bulk Import (Migration)

Import historical verifications in bulk — e.g. migrating from another provider — from a hosted CSV or NDJSON file. All imports use Didit's canonical schema regardless of source.

```
POST /v3/session/imports/
```

| Body | Type | Required | Description |
|---|---|---|---|
| `source_file_url` | string | **Yes*** | Publicly fetchable URL of the file (JSON body). *The multipart variant accepts a `file` upload instead. |
| `import_type` | string | No | `user_verification` (default), `business_verification`, `status_rules`, or `transactions` |
| `source_format` | string | No | `csv` (default) or `ndjson` |
| `workflow_id` | string | No | Workflow to associate imported sessions with |

There is no provider request field — all imports use Didit's canonical schema. To label where a record came from, include the optional per-row `provider` column in the file itself (defaults to `generic`, stored as `metadata.imported_from`).

Track and inspect jobs:

```
GET /v3/session/imports/template/            # canonical column template
GET /v3/session/imports/{importId}/          # job status + summary
GET /v3/session/imports/{importId}/errors/   # per-row errors
```

---

## Lists (Block / Allow / Custom)

Lists drive automatic enforcement: a **blocklist** match auto-declines future sessions, an **allowlist** match fast-tracks/suppresses duplicate actions, and **custom** lists feed workflow conditions and monitoring rules.

- `list_type`: `blocklist` (system, auto-provisioned per entry type, **immutable** — you can't create or delete these) · `allowlist` · `custom`
- `entry_type`: `face`, `document`, `phone`, `email`, `ip_address`, `device_fingerprint`, `wallet_address`, `bank_account`, `user`, `business`, `country`, `key`

### 1. List Lists

```
GET /v3/lists/
```

Filters: `list_type`, `entry_type`, `limit`, `offset`.

### 2. Create List

```
POST /v3/lists/
```

| Body | Type | Required | Description |
|---|---|---|---|
| `name` | string | **Yes** | Unique per application |
| `list_type` | string | **Yes** | `allowlist` or `custom` (blocklists are auto-provisioned) |
| `entry_type` | string | **Yes** | One of the entry types above |
| `description` | string | No | Optional description |

### 3. Get / Update / Delete List

```
GET    /v3/lists/{list_uuid}/
PATCH  /v3/lists/{list_uuid}/          # body: name, description (system blocklists are immutable)
DELETE /v3/lists/{list_uuid}/          # allowlist/custom only
```

### 4. Add an Entry

```
POST /v3/lists/{list_uuid}/entries/
```

| Body | Type | Required | Description |
|---|---|---|---|
| `value` | string | Conditional | The value to add (phone, email, IP, etc.). Required unless `reference_session_id` is given. |
| `reference_session_id` | uuid | Conditional | Auto-extracts the value from a session based on the list's `entry_type` (face, document, phone, email, ip_address, device_fingerprint) and marks the underlying model blocklisted. |
| `reference_object_uuid` | uuid | No | Source entity (transaction / vendor user / business) for traceability |
| `display_label` | string | No | Human-readable label |
| `comment` | string | No | Reason / note |
| `metadata` | object | No | e.g. `{ "reference_type": "vendor_user" }` |

**Blocklist a session's face + document:** add one entry to the face blocklist and one to the document blocklist, each with `reference_session_id`. On future matches Didit raises `FACE_IN_BLOCKLIST` / `ID_DOCUMENT_IN_BLOCKLIST` / `PHONE_NUMBER_IN_BLOCKLIST` / `EMAIL_IN_BLOCKLIST` and auto-declines.

### 5. Upload a Face Entry (no session)

```
POST /v3/lists/{list_uuid}/entries/face-upload/
```

For face lists when you have an image but no session. Body: `image` (base64 JPG/PNG/WebP, no `data:` prefix), optional `comment`. Requires a `face`-type list; returns `400` if no/multiple faces are detected.

### 6. List / Delete Entries

```
GET    /v3/lists/{list_uuid}/entries/        # query: search, limit, offset
DELETE /v3/lists/{list_uuid}/entries/{entry_uuid}/   # also unblocks the underlying user/business
```

---

## Questionnaires

Custom forms attached to verification workflows. Support 7 element types: `short_text`, `long_text`, `multiple_choice`, `checkbox`, `file_upload`, `date`, `number`.

### 1. List Questionnaires

```
GET /v3/questionnaires/
```

### 2. Create Questionnaire

```
POST /v3/questionnaires/
```

| Body | Type | Required | Description |
|---|---|---|---|
| `title` | string | **Yes** | Display title |
| `description` | string | No | Description shown to users |
| `default_language` | string | No | Default language code |
| `languages` | array | No | Supported languages |
| `form_elements` | array | **Yes** | Question objects |

**Form element:**

| Field | Type | Required | Description |
|---|---|---|---|
| `element_type` | string | **Yes** | One of the 7 types above |
| `label` | object | **Yes** | Translations: `{"en": "Question?", "es": "¿Pregunta?"}` |
| `is_required` | boolean | No | Mandatory answer |
| `options` | array | Conditional | Required for `multiple_choice`/`checkbox` |

```python
requests.post("https://verification.didit.me/v3/questionnaires/",
    headers=headers,
    json={
        "title": "Employment Details",
        "default_language": "en",
        "form_elements": [
            {"element_type": "short_text",
             "label": {"en": "Occupation?"}, "is_required": True},
            {"element_type": "multiple_choice",
             "label": {"en": "Employment status"},
             "options": [{"label": {"en": "Employed"}}, {"label": {"en": "Student"}}]},
        ]
    })
```

### 3. Get Questionnaire

```
GET /v3/questionnaires/{questionnaire_uuid}/
```

### 4. Update Questionnaire

```
PATCH /v3/questionnaires/{questionnaire_uuid}/
```

### 5. Delete Questionnaire

```
DELETE /v3/questionnaires/{questionnaire_uuid}/
```

**Response:** `204 No Content`.

---

## Users (KYC)

Manage verified individuals identified by `vendor_data`. A user's `status` is a **monitoring status** — `ACTIVE`, `FLAGGED`, or `BLOCKED` (not a verification decision).

### 1. List Users

```
GET /v3/users/
```

| Query | Type | Description |
|---|---|---|
| `limit` | integer | Results per page |
| `offset` | integer | Pagination offset |

**Response (200):** Paginated list with `vendor_data`, `full_name`, `status`, `session_count`, `issuing_states`, `approved_emails`, `approved_phones`.

### 2. Create User

```
POST /v3/users/create/
```

| Body | Type | Required | Description |
|---|---|---|---|
| `vendor_data` | string | **Yes** | Your unique identifier |
| `full_name` | string | No | |
| `display_name` | string | No | |
| `date_of_birth` | string | No | `YYYY-MM-DD` |
| `status` | string | No | `ACTIVE`, `FLAGGED`, or `BLOCKED` |
| `metadata` | object | No | Custom JSON |
| `approved_emails` | array | No | Allowlisted emails |
| `approved_phones` | array | No | Allowlisted phones |
| `issuing_states` | array | No | Allowed issuing states |

### 3. Get User

```
GET /v3/users/{vendor_data}/
```

### 4. Update User

```
PATCH /v3/users/{vendor_data}/
```

Send only the fields to change: `full_name`, `display_name`, `date_of_birth`, `status` (`ACTIVE`/`FLAGGED`/`BLOCKED`), `metadata`, `approved_emails`, `approved_phones`, `issuing_states`.

### 5. Update User Status

```
PATCH /v3/users/{vendor_data}/update-status/
```

| Body | Type | Required | Description |
|---|---|---|---|
| `status` | string | **Yes** | `ACTIVE`, `FLAGGED`, or `BLOCKED` |

### 6. Batch Delete Users

```
POST /v3/users/delete/
```

| Body | Type | Description |
|---|---|---|
| `vendor_data_list` | array | List of vendor_data strings |
| `delete_all` | boolean | Delete all users |

---

## Businesses (KYB)

Manage verified businesses identified by `vendor_data`. Same `ACTIVE`/`FLAGGED`/`BLOCKED` monitoring status as users.

```
GET    /v3/businesses/                          # list (limit, offset)
POST   /v3/businesses/create/                   # vendor_data, display_name, legal_name, registration_number, country_code (ISO alpha-2), status, metadata
GET    /v3/businesses/{vendor_data}/            # get
PATCH  /v3/businesses/{vendor_data}/            # update (same fields as create)
PATCH  /v3/businesses/{vendor_data}/update-status/   # body: status (ACTIVE|FLAGGED|BLOCKED)
POST   /v3/businesses/delete/                   # vendor_data_list[], didit_internal_id_list[], delete_all
```

**Standalone KYB registry lookup** (no session): `POST /v3/kyb/search/` with `country_code` (required) + `name`/`registration_number` returns candidates; pass a candidate's `kyb_response_id` to `POST /v3/kyb/select/` to pull the full company record.

---

## Transactions (AML monitoring)

Submit transactions for rule evaluation and ongoing monitoring.

```
GET   /v3/transactions/                  # list (limit, offset)
POST  /v3/transactions/                  # create
GET   /v3/transactions/{transaction_id}/ # get + rule-evaluation result
```

Create body — required: `transaction_id`, `transaction_category` (`finance`, `kyc`, `travel_rule`, `user_event`, `audit_trail_event`, `gambling_bet`, `gambling_limit_change`, `gambling_bonus_change`), `transaction_details` (object), `subject` (object). Optional: `counterparty`, `transaction_at`, `time_zone`, `custom_properties` (referenced in rules as `custom_values.<key>`), `travel_rule_details`, `network_snapshot`, `include_crypto_screening`.

---

## Billing

### 1. Get Credit Balance

```
GET /v3/billing/balance/
```

**Response (200):**

```json
{
  "balance": "142.5000",
  "auto_refill_enabled": true,
  "auto_refill_amount": "100.0000",
  "auto_refill_threshold": "10.0000"
}
```

### 2. Top Up Credits

```
POST /v3/billing/top-up/
```

| Body | Type | Required | Description |
|---|---|---|---|
| `amount_in_dollars` | number | **Yes** | Minimum $50 |
| `success_url` | string | No | Redirect after payment |
| `cancel_url` | string | No | Redirect on cancel |

**Response (200):**

```json
{
  "checkout_session_id": "cs_live_...",
  "checkout_session_url": "https://checkout.stripe.com/..."
}
```

Present `checkout_session_url` to the user for payment.

---

## Customization (Branding)

Brand the hosted verification UI with your own logos.

```
GET   /v3/customization/      # current branding
PATCH /v3/customization/      # multipart/form-data
```

Update fields (image files, `multipart/form-data`): `image_square`, `image_rectangular`, `image_favicon`. Send only the images you want to change.

---

## Webhook Destinations

Configure webhooks **programmatically** — no console needed. You can register **multiple destinations**, each with its own URL, payload version, enabled flag, subscribed events, and signing secret.

### 1. List Destinations

```
GET /v3/webhook/destinations/
```

**Response (200):** Array of destinations, each with `uuid`, `label`, `url`, `enabled`, `webhook_version`, `subscribed_events`, and the signing `secret`.

### 2. Create Destination

```
POST /v3/webhook/destinations/
```

| Body | Type | Required | Description |
|---|---|---|---|
| `label` | string | **Yes** | Human-readable name |
| `url` | string | **Yes** | HTTPS endpoint to receive events |
| `enabled` | boolean | No | Whether the destination receives events (default `true`) |
| `webhook_version` | string | No | `"v1"`, `"v2"`, or `"v3"` (v3 recommended) |
| `subscribed_events` | array | No | Event types to deliver (omit to receive all) |

**Response (201):** the created destination, including the `secret` used to verify the `X-Signature` header. Store it securely.

```python
dest = requests.post(
    "https://verification.didit.me/v3/webhook/destinations/",
    headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
    json={"label": "Prod", "url": "https://myapp.com/webhooks/didit",
          "webhook_version": "v3", "subscribed_events": ["status.updated", "data.updated"]},
).json()
secret = dest["secret"]
```

### 3. Get / Update / Delete Destination

```
GET    /v3/webhook/destinations/{destination_uuid}/   # includes the signing secret
PATCH  /v3/webhook/destinations/{destination_uuid}/   # label, url, enabled, webhook_version, subscribed_events
DELETE /v3/webhook/destinations/{destination_uuid}/   # stop delivering to this endpoint
```

**Example — disable a destination without deleting it:**

```python
requests.patch(
    f"https://verification.didit.me/v3/webhook/destinations/{dest['uuid']}/",
    headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
    json={"enabled": False},
)
```

---

## Webhook Events & Signatures

Didit sends `POST` requests to your webhook URL when session status changes. Retries up to 2 times with exponential backoff (1 min, 4 min).

### Payload

```json
{
  "session_id": "...",
  "status": "Approved",
  "webhook_type": "status.updated",
  "vendor_data": "user-123",
  "timestamp": 1627680000,
  "decision": { ... }
}
```

**Event types:** `status.updated` (session status change), `data.updated` (KYC/POA data manually updated), `user.created`, `user.updated`, `business.created`, `business.updated`, `transaction.created`, `transaction.updated`. Subscribe a destination to specific events via `subscribed_events`, or omit it to receive all.

**Idempotency:** dedupe on `session_id` + `status` + `webhook_type` (not `timestamp`). The `event_id` is stable across retries.

### Signature Verification (recommended)

Two headers: `X-Signature` (HMAC-SHA256 hex) and `X-Timestamp` (Unix seconds). The canonical string is the JSON body with floats shortened, keys sorted, compact separators, and `ensure_ascii=False`; the signed message is `{timestamp}:{canonical}`.

```python
import hashlib, hmac, time, json

def verify_webhook_v2(body_dict: dict, signature: str, timestamp: str, secret: str) -> bool:
    if abs(time.time() - int(timestamp)) > 300:
        return False
    def process_value(v):
        if isinstance(v, float) and v == int(v):
            return int(v)
        if isinstance(v, dict):
            return {k: process_value(val) for k, val in v.items()}
        if isinstance(v, list):
            return [process_value(i) for i in v]
        return v
    canonical = json.dumps(process_value(body_dict), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    message = f"{timestamp}:{canonical}"
    expected = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### Simple Signature (Fallback)

Header: `X-Signature-Simple` — HMAC of key fields only.

```python
def verify_webhook_simple(session_id, status, webhook_type, timestamp, signature, secret):
    message = f"{timestamp}:{session_id}:{status}:{webhook_type}"
    expected = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)
```

---

## Error Responses (All Endpoints)

| Code | Meaning | Action |
|---|---|---|
| `400` | Invalid request | Check required fields and formats |
| `401` | Invalid or missing API key | Verify `x-api-key` header |
| `403` | Insufficient credits or no permission | Check balance, API key permissions |
| `404` | Resource not found | Verify IDs |
| `429` | Rate limited | Check `Retry-After` header, exponential backoff |

---

## Common Workflows

### Full KYC Onboarding

```
1. POST /programmatic/register/          → register
2. POST /programmatic/verify-email/      → get api_key
3. POST /v3/workflows/                    → create KYC workflow (features array)
4. POST /v3/webhook/destinations/         → register webhook URL + version "v3"
5. POST /v3/session/                      → create session → get URL
6. User completes verification at URL
7. Webhook fires → GET /v3/session/{id}/decision/ → read results
```

### Programmatic Review + Blocklist

```
1. Webhook: status "In Review"
2. GET /v3/session/{id}/decision/   → inspect results
3. If fraud: PATCH update-status → Declined, then
   POST /v3/lists/{blocklist_uuid}/entries/ with reference_session_id
   If legit: PATCH update-status → Approved
```

### B2B KYC Sharing

```
Service A: POST /v3/session/{id}/share/       → get share_token
Service B: POST /v3/session/import-shared/    → import with trust_review=true
```

### Check Balance Before Sessions

```
1. GET /v3/billing/balance/    → check if balance > 0
2. If low: POST /v3/billing/top-up/ → get Stripe checkout URL
3. POST /v3/session/           → create session
```

### Questionnaire + Workflow

```
1. POST /v3/questionnaires/  → create form → save uuid
2. POST /v3/workflows/       → questionnaire_verification type
3. POST /v3/session/         → session with workflow_id
```

---

## Utility Scripts

### setup_account.py — Register and verify accounts

```bash
pip install requests
python scripts/setup_account.py register you@gmail.com 'MyStr0ng!Pass'
# (check email for code)
python scripts/setup_account.py verify you@gmail.com A3K9F2
# Prints api_key, org_uuid, app_uuid
python scripts/setup_account.py login you@gmail.com 'MyStr0ng!Pass'
```

### manage_workflows.py — CRUD workflows

```bash
export DIDIT_API_KEY="your_key"
python scripts/manage_workflows.py list
python scripts/manage_workflows.py create --label "My KYC" --liveness --face-match
python scripts/manage_workflows.py get <uuid>
python scripts/manage_workflows.py update <uuid> --label "Renamed KYC"
python scripts/manage_workflows.py delete <uuid>
```

### create_session.py — Create verification sessions

```bash
export DIDIT_API_KEY="your_key"
python scripts/create_session.py --workflow-id <uuid> --vendor-data user-123
python scripts/create_session.py --workflow-id <uuid> --vendor-data user-123 --callback https://myapp.com/done
```

All scripts can be imported as libraries:

```python
from scripts.setup_account import register, verify_email, login
from scripts.manage_workflows import list_workflows, create_workflow
from scripts.create_session import create_session
```
