---
name: didit-kyc-onboarding
description: >
  End-to-end KYC (Know Your Customer) identity verification for onboarding real users through a
  hosted Didit verification link. Use when someone needs to perform KYC, onboard users with ID
  scan + selfie + face match, create a KYC workflow or a verification session for a user, add
  AML screening, NFC chip reading, phone or email verification, active liveness, non-document
  lookup or digital ID wallets to the flow, poll or receive the decision, or approve, decline or
  request resubmission of a session. Creates the workflow, generates the verification URL and
  reads the decision.
version: 1.2.0
metadata:
  openclaw:
    requires:
      env:
        - DIDIT_API_KEY
    primaryEnv: DIDIT_API_KEY
    emoji: "✅"
    homepage: https://docs.didit.me
---

# Running KYC with Didit

End-to-end Know Your Customer (KYC) verification. This skill creates a KYC workflow, generates a session URL where a real user completes ID scan + selfie + face match, and retrieves the verification decision.

**What the user experiences:**
1. Receives a verification link (or opens it inside your app)
2. Scans their ID document (passport, ID card, driver's license, residence permit)
3. Takes a live selfie
4. The selfie is matched to the document portrait
5. Gets approved, declined, or flagged for review

**Pricing:** in a workflow you pay per feature that completes: ID Verification (document capture) $0.15, Passive Liveness $0.10 and Face Match $0.05, each with 500 free checks a month per organization; Active liveness (`ACTIVE_3D` or `FLASHING`) $0.15, NFC $0.15, AML Screening $0.20, Email Verification $0.03, Phone Verification $0.04 + carrier fee. These are the list prices until 1 November 2026, when Didit pricing changes and the 500 free checks a month become $10 of free credit a month. Check [didit.me/pricing](https://didit.me/pricing) for current prices.

**API Reference:**
- Workflows: https://docs.didit.me/management-api/workflows/create
- Workflow feature configs: https://docs.didit.me/management-api/workflows/feature-configs
- Sessions: https://docs.didit.me/sessions-api/create-session
- Decisions: https://docs.didit.me/sessions-api/retrieve-session
- Statuses: https://docs.didit.me/integration/verification-statuses
- Programmatic Registration: https://docs.didit.me/integration/programmatic-registration

Related skills: **didit-sdk-integration** (embed the session in a web or mobile app instead of sending a link), **didit-case-management** (review queues for `In Review` sessions), **didit-verification-management** (webhooks, users, billing).

---

## Authentication

Every request needs the `x-api-key` header. Use your application's API key from the [Didit Business Console](https://business.didit.me) under **Developers > API keys**, or create an account and key programmatically (see Getting Started). Named keys with custom access need **Workflows** write to create workflows, **Sessions** write to create sessions (without it `url` and `session_token` come back `null`), **Decisions** read for results and **Media** read for image URLs and PDF reports.

## Getting Started (No Account Yet?)

If you don't have a Didit API key, create one in 2 API calls:

1. **Register:** `POST https://apx.didit.me/auth/v2/programmatic/register/` with `{"email": "you@yourdomain.com", "password": "MyStr0ng!Pass"}`
2. **Check email** for a 6-character verification code
3. **Verify:** `POST https://apx.didit.me/auth/v2/programmatic/verify-email/` with `{"email": "you@yourdomain.com", "code": "A3K9F2"}`. The key is in the response at `application.api_key`.

**To add credits:** `GET /v3/billing/balance/` to check, `POST /v3/billing/top-up/` with `{"amount_in_dollars": 50}` for a Stripe checkout link.

See the **didit-verification-management** skill for full platform management (workflows, sessions, users, billing).

---

## Quick Start: KYC in 3 API Calls

```python
import requests, time

API_KEY = "your_api_key"
headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
BASE = "https://verification.didit.me/v3"
TERMINAL = {"Approved", "Declined", "In Review", "Expired", "Kyc Expired", "Abandoned"}

# 1. Create a KYC workflow (one-time setup: reuse the workflow id for all users)
workflow = requests.post(f"{BASE}/workflows/", headers=headers, json={
    "workflow_label": "KYC Onboarding",
    "max_retry_attempts": 3,
    "features": [
        {"feature": "OCR"},
        {"feature": "LIVENESS", "config": {"face_liveness_method": "PASSIVE"}},
        {"feature": "FACE_MATCH", "config": {"face_match_score_decline_threshold": 50}},
    ],
}).json()
workflow_id = workflow["uuid"]

# 2. Create a session for a specific user
session = requests.post(f"{BASE}/session/", headers=headers, json={
    "workflow_id": workflow_id,
    "vendor_data": "user-abc-123",
    "callback": "https://yourapp.com/verification-done",
    "language": "en",
}).json()

print(f"Send user to: {session['url']}")
# User opens this URL, scans their ID, takes a selfie

# 3. Poll for the decision (or use webhooks)
while True:
    decision = requests.get(
        f"{BASE}/session/{session['session_id']}/decision/",
        headers={"x-api-key": API_KEY},
    ).json()
    status = decision["status"]
    if status in TERMINAL:
        break
    time.sleep(15)

print(f"Result: {status}")
if status == "Approved":
    id_data = decision["id_verifications"][0]
    print(f"Name: {id_data['first_name']} {id_data['last_name']}")
    print(f"DOB: {id_data['date_of_birth']}")
    print(f"Document: {id_data['document_type']} ({id_data['issuing_state']})")
```

---

## Step 1: Create a KYC Workflow

A workflow defines what checks run. Create one per use case and reuse it for all users. Maximum 50 workflows per application; each call creates a new workflow.

```
POST https://verification.didit.me/v3/workflows/
```

**API Reference:** https://docs.didit.me/management-api/workflows/create

### Request Body

The body accepts only these keys; any other key (including `workflow_type`) returns `400`.

| Field | Type | Default | Description |
|---|---|---|---|
| `features` | array | **Required** | Steps in execution order: `{"feature": "...", "config": {...}, "label": "..."}` |
| `workflow_label` | string | `"ID Verification"` | Display name, max 50 characters |
| `max_retry_attempts` | integer 0-10 | `3` | Retries allowed after a decline; `0` blocks after the first decline |
| `retry_window_days` | integer 1-365 or `null` | `7` | Rolling window for counting retries; `null` = all-time |
| `session_expiration_time` | integer 3600-2419200 | `604800` (7 days) | Seconds before an unfinished session expires |
| `face_liveness_max_attempts` | integer 1-3 | `3` | Liveness submissions per session |
| `face_match_max_attempts` | integer 1-3 | `3` | Face match submissions per session |
| `is_default` | boolean | - | Make it the application's default workflow |
| `status` | `draft` or `published` | published | Omit to publish immediately |
| `is_white_label_enabled` | boolean | `false` | Apply your white-label customization |
| `is_desktop_allowed` | boolean | `false` | Allow the flow to run in desktop browsers |

### KYC features and their main config

| `feature` | Config | Notes |
|---|---|---|
| `OCR` | `documents_allowed`, `methods`, `duplicated_user_action`, age and risk actions | ID document capture. Put it first so later steps can use its data |
| `LIVENESS` | `face_liveness_method`: `PASSIVE`, `ACTIVE_3D` (3D action and flash) or `FLASHING` (3D flash) | Active methods bill as Active Liveness ($0.15) |
| `FACE_MATCH` | `face_match_score_decline_threshold`, `face_match_score_review_threshold` (0-100) | Must come after `OCR` |
| `NFC` | `allow_nfc_skip`, `skip_nfc_action`, `unverified_chip_action` | Must come after `OCR`; chip read by the native iOS/Android SDK, skipped in web browsers |
| `AML` | `aml_score_review_threshold`, `aml_score_approve_threshold` | Needs `OCR` before it |
| `PHONE_VERIFICATION`, `EMAIL_VERIFICATION` | see feature configs | Contact verification |

Actions in configs take `DECLINE`, `REVIEW` or `NO_ACTION`. Other features (`IP_ANALYSIS`, `PROOF_OF_ADDRESS`, `DATABASE_VALIDATION`, `QUESTIONNAIRE`, `AGE_ESTIMATION`, `DOCUMENT_AI`) and every config key are in the [feature configs reference](https://docs.didit.me/management-api/workflows/feature-configs).

### Response (201)

The response is the full workflow configuration (about 190 fields). Key fields:

```json
{
  "uuid": "c3d4e5f6-7890-12cd-ef34-333333333333",
  "workflow_id": "c3d4e5f6-7890-12cd-ef34-333333333333",
  "workflow_label": "KYC Onboarding",
  "features": "OCR + LIVENESS + FACE_MATCH",
  "total_price": 0.3,
  "min_price": 0.3,
  "max_price": 0.3,
  "workflow_url": "https://verify.didit.me/u/w9TkPOx8RWG3UAz5ZRQGVQ",
  "max_retry_attempts": 3,
  "retry_window_days": 7,
  "session_expiration_time": 604800,
  "status": "published",
  "version": 1
}
```

Save `uuid` (same value as `workflow_id`). `features` is one `" + "`-joined string; prices are JSON numbers in USD (the sum of the enabled features at your rates).

---

## Step 2: Create a Session for Each User

Each user gets their own session with a unique verification URL.

```
POST https://verification.didit.me/v3/session/
```

**API Reference:** https://docs.didit.me/sessions-api/create-session

### Key Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `workflow_id` | uuid | **Yes** | From Step 1 |
| `vendor_data` | string | Recommended | Your user ID: groups sessions per user and powers duplicate detection. An unfinished session with the same `vendor_data` on the same workflow version is returned instead of a new one |
| `callback` | url | Recommended | Redirect after verification. Didit appends `verificationSessionId` and `status` as query parameters |
| `callback_method` | string | No | `initiator`, `completer` or `both` (which device follows the callback) |
| `language` | string | No | UI language (ISO 639-1). Auto-detected if omitted |
| `contact_details` | object | No | `email`, `send_notification_emails`, `email_lang`, `phone` (E.164) |
| `expected_details` | object | No | `first_name`, `last_name`, `date_of_birth` (`YYYY-MM-DD`), `gender`, `nationality`, `id_country`, `identification_number`, `expected_document_types`, ... Mismatches add `*_MISMATCH_WITH_PROVIDED` warnings |
| `metadata` | any JSON | No | Stored with the session and echoed in responses and webhooks. Any JSON value is accepted; an object is recommended |

### Response (201)

```json
{
  "session_id": "11111111-2222-3333-4444-555555555555",
  "session_number": 43762,
  "session_token": "3FaJ9wLqX2Mz",
  "url": "https://verify.didit.me/session/3FaJ9wLqX2Mz",
  "vendor_data": "user-abc-123",
  "metadata": null,
  "status": "Not Started",
  "workflow_id": "c3d4e5f6-7890-12cd-ef34-333333333333",
  "workflow_version": 1,
  "callback": "https://yourapp.com/verification-done"
}
```

**Send the user to `url`** (web or mobile), or embed the session with the SDKs (**didit-sdk-integration** skill). Treat `session_token` as a secret: whoever holds it can complete the verification.

---

## Step 3: Get the Decision

```
GET https://verification.didit.me/v3/session/{sessionId}/decision/
```

**API Reference:** https://docs.didit.me/sessions-api/retrieve-session

### Two Ways to Know When It's Ready

**Option A: Webhooks (recommended for production)**
Add a destination in the Business Console (**Webhooks**) or with `POST /v3/webhook/destinations/` (`label`, `url`, `webhook_version: "v3"`, `subscribed_events: ["status.updated"]`). Didit sends a signed POST with `session_id`, `status` and, when the status is `Approved`, `Declined`, `In Review` or `Abandoned`, the full `decision`. Verify the signature (see **didit-verification-management**) and make the handler idempotent on `event_id`.

**Option B: Polling**
Poll `GET /v3/session/{sessionId}/decision/` every 10 to 30 seconds. Stop on a terminal status: `Approved`, `Declined`, `In Review`, `Expired`, `Kyc Expired` or `Abandoned`. `In Review` can still change after a manual review, so keep a webhook for that.

### Decision Response Fields

Each feature has its own array with its own `status`, `node_id` and `warnings`. There is no top-level `warnings` key.

```json
{
  "session_id": "11111111-2222-3333-4444-555555555555",
  "session_number": 43762,
  "status": "Approved",
  "workflow_id": "c3d4e5f6-7890-12cd-ef34-333333333333",
  "features": ["ID_VERIFICATION", "LIVENESS", "FACE_MATCH"],
  "vendor_data": "user-abc-123",
  "metadata": null,
  "id_verifications": [{
    "node_id": "ocr",
    "verification_method": "document",
    "status": "Approved",
    "document_type": "Passport",
    "document_number": "ABC123456",
    "issuing_state": "USA",
    "issuing_state_name": "United States",
    "first_name": "Alex",
    "last_name": "Sample",
    "full_name": "Alex Sample",
    "date_of_birth": "1990-01-15",
    "age": 36,
    "expiration_date": "2030-06-01",
    "gender": "M",
    "nationality": "USA",
    "mrz": {"surname": "SAMPLE", "name": "ALEX", "document_type": "P", "document_number": "ABC123456", "birth_date": "900115", "expiry_date": "300601", "sex": "M"},
    "portrait_image": "https://<media-host>/...",
    "warnings": []
  }],
  "liveness_checks": [{
    "node_id": "liveness",
    "status": "Approved",
    "method": "PASSIVE",
    "score": 92.5,
    "warnings": []
  }],
  "face_matches": [{
    "node_id": "face_match",
    "status": "Approved",
    "score": 97.3,
    "warnings": []
  }],
  "aml_screenings": [],
  "created_at": "2026-05-17T10:30:00Z"
}
```

Field notes:
- `document_type` is a display name: `Passport`, `Identity Card`, `Driver's License`, `Residence Permit`, ...
- `issuing_state` and `nationality` are ISO 3166-1 alpha-3. Dates are `YYYY-MM-DD`; MRZ dates are raw `YYMMDD`. `mrz` is an object, or `null` when no MRZ was read.
- Feature statuses (`Approved`, `Declined`, `In Review`, `Not Finished`, ...) are independent of the session `status`.
- `verification_method` on `id_verifications` is `document`, `id_lookup` or `wallet`.
- Warnings: `{feature, risk, additional_data, log_type, short_description, long_description, node_id}`. See the **didit-id-document-verification** skill and https://docs.didit.me/core-technology/id-verification/warnings-id-verification.

### Session Statuses

| Status | Meaning | Action |
|---|---|---|
| `Not Started` | Session created, link not opened yet | Wait or remind the user |
| `In Progress` | User is completing the steps | Wait |
| `Awaiting User` | Business (KYB) session waiting for its people's KYC sessions | Wait |
| `Resubmitted` | User was asked to redo specific steps | Wait for the new result |
| `Approved` | All checks passed | User is verified |
| `Declined` | One or more checks failed | Read each feature's `warnings` |
| `In Review` | Needs manual review | Review in the console, or decide via the API (below) |
| `Expired` | Session expired before completion (default 7 days, `session_expiration_time`) | Create a new session |
| `Abandoned` | User started but did not finish in time | Create a new session |
| `Kyc Expired` | A previously approved session passed its KYC expiration policy | Re-verify the user |

Values are exact, case-sensitive strings (`Kyc Expired` has a single capital K).

---

## Optional: Post-Decision Actions

### Approve or Decline Manually

```
PATCH https://verification.didit.me/v3/session/{sessionId}/update-status/
```

**API Reference:** https://docs.didit.me/sessions-api/update-status

The session must be `Approved`, `Declined`, `In Review`, `Kyc Expired`, `Abandoned` or `Resubmitted`, and the new status must differ from the current one (otherwise `400`).

```python
requests.patch(f"{BASE}/session/{session_id}/update-status/",
    headers=headers,
    json={"new_status": "Approved", "comment": "Manual review passed"})
```

### Request Resubmission

If the ID photo was blurry, ask the user to redo just that step. Take `node_id` from the decision: workflows created through this API use ids like `ocr`, `liveness`, `face_match`; console-built workflows use ids like `feature_ocr`.

```python
decision = requests.get(f"{BASE}/session/{session_id}/decision/", headers=headers).json()
ocr_node = decision["id_verifications"][0]["node_id"]

requests.patch(f"{BASE}/session/{session_id}/update-status/",
    headers=headers,
    json={
        "new_status": "Resubmitted",
        "nodes_to_resubmit": [{"node_id": ocr_node, "feature": "OCR"}],
        "send_email": True,
        "email_address": "user@example.com",
    })
```

Omit `nodes_to_resubmit` to resubmit every attempted step that is `Declined`, `In Review`, `Not Finished` or `Expired` (NFC and IP analysis are never auto-selected). The captured data of those steps is deleted, the expiration window restarts and the original verification URL becomes usable again.

### Block Fraudulent Users

Add the session's face or document to a system blocklist (every application has one per entry type) via the Lists API:

```python
lists = requests.get(f"{BASE}/lists/", headers=headers,
                     params={"list_type": "blocklist", "entry_type": "face"}).json()
list_uuid = lists["results"][0]["uuid"]
requests.post(f"{BASE}/lists/{list_uuid}/entries/",
    headers=headers,
    json={"reference_session_id": session_id})
```

**API Reference:** https://docs.didit.me/management-api/lists/create-entry

### Generate PDF Report

Available for sessions in `Approved`, `Declined`, `In Review` or `Kyc Expired`. Returns `application/pdf` bytes.

```python
response = requests.get(f"{BASE}/session/{session_id}/generate-pdf/",
    headers={"x-api-key": API_KEY})
with open("report.pdf", "wb") as f:
    f.write(response.content)
```

**API Reference:** https://docs.didit.me/sessions-api/generate-pdf

### Error Responses

| Code | Meaning | Action |
|---|---|---|
| `400` | Invalid request | Read the field errors in the response body |
| `401` | The API key has expired | Rotate it or create a new key in **Developers > API keys** |
| `403` | Missing, wrong or revoked API key; a scoped key without access to this endpoint; a request from outside the key's IP allowlist; or not enough credits | Read the message in `detail` or `error`: fix the `x-api-key` header or the key's access, or top up |
| `404` | Session not found (or outside a scoped key's workflows) | Check the `sessionId` |
| `429` | Rate limit: 300 POST/PATCH/DELETE and 600 GET requests a minute per key | Wait the `Retry-After` seconds, then retry |

---

## KYC Workflow Variants

### KYC + AML Screening

```python
requests.post(f"{BASE}/workflows/", headers=headers, json={
    "workflow_label": "KYC + AML",
    "features": [
        {"feature": "OCR"},
        {"feature": "LIVENESS", "config": {"face_liveness_method": "PASSIVE"}},
        {"feature": "FACE_MATCH"},
        {"feature": "AML"},
    ],
})
```

### KYC + Phone + Email

```python
requests.post(f"{BASE}/workflows/", headers=headers, json={
    "workflow_label": "KYC + Contact",
    "features": [
        {"feature": "OCR"},
        {"feature": "LIVENESS", "config": {"face_liveness_method": "PASSIVE"}},
        {"feature": "FACE_MATCH"},
        {"feature": "PHONE_VERIFICATION"},
        {"feature": "EMAIL_VERIFICATION"},
    ],
})
```

### KYC + NFC (Chip Reading)

Highest assurance for passports and eIDs with a chip. Needs the native iOS/Android SDK; web flows skip NFC.

```python
requests.post(f"{BASE}/workflows/", headers=headers, json={
    "workflow_label": "KYC + NFC",
    "features": [
        {"feature": "OCR"},
        {"feature": "NFC"},
        {"feature": "LIVENESS", "config": {"face_liveness_method": "PASSIVE"}},
        {"feature": "FACE_MATCH"},
    ],
})
```

### Stricter Liveness and Session Settings

```python
requests.post(f"{BASE}/workflows/", headers=headers, json={
    "workflow_label": "KYC High Assurance",
    "max_retry_attempts": 1,
    "retry_window_days": 30,
    "session_expiration_time": 86400,
    "face_liveness_max_attempts": 2,
    "features": [
        {"feature": "OCR"},
        {"feature": "LIVENESS", "config": {"face_liveness_method": "FLASHING"}},
        {"feature": "FACE_MATCH", "config": {"face_match_score_decline_threshold": 60}},
    ],
})
```

### Non-Document Lookup and Digital ID Wallets per Country

The `OCR` feature's `config.methods` chooses, per ISO 3166-1 alpha-3 country, which ID Verification methods the user may use: document capture, a lookup against a government register or other authoritative source (the user types their national ID number), and digital ID wallets. Omitted countries stay document capture only. Every method and wallet must be marked available for that country in the capability catalog (console **Countries** tab), or the whole save is rejected.

```python
requests.post(f"{BASE}/workflows/", headers=headers, json={
    "workflow_label": "KYC with lookup",
    "features": [
        {"feature": "OCR", "config": {"methods": {
            "ZAF": {
                "document": {"enabled": True},
                "id_lookup": {"enabled": True, "max_attempts": 2,
                              "on_no_match": "fallback_to_document"},
            },
        }}},
        {"feature": "LIVENESS", "config": {"face_liveness_method": "PASSIVE"}},
        {"feature": "FACE_MATCH"},
    ],
})
```

| Key | Default | Values |
|---|---|---|
| `<ISO3>.document.enabled` | `true` | Accept a photographed document |
| `<ISO3>.id_lookup.enabled` | `false` | Offer the lookup |
| `<ISO3>.id_lookup.max_attempts` | `1` | `1` to `5` answered lookups |
| `<ISO3>.id_lookup.skip_liveness_and_face_match` | `true` | Skip later Liveness/Face Match when the source returned a portrait and matched the selfie |
| `<ISO3>.id_lookup.on_partial_match` / `on_no_match` / `on_provider_error` | `fallback_to_document` | or `decline` |
| `<ISO3>.wallet.enabled` | `false` | Offer wallet sign-in |
| `<ISO3>.wallet.providers` | `[]` | Catalog wallet ids accepted in that country, e.g. `["mitid"]` (an accept-list, not a ranking) |
| `<ISO3>.wallet.on_failure` | `fallback_to_document` | or `decline` |

Lookups are priced per country and wallets per completed verification, outside the 500 free document checks. See https://docs.didit.me/core-technology/id-verification/non-doc-lookup and https://docs.didit.me/core-technology/id-verification/digital-id-wallets.

---

## Utility Scripts

### run_kyc.py: Full KYC setup from the command line

```bash
# Requires: pip install requests
export DIDIT_API_KEY="your_api_key"

# Create a KYC workflow (one-time)
python scripts/run_kyc.py setup --label "My KYC" --liveness --face-match
python scripts/run_kyc.py setup --label "KYC + AML" --aml --liveness-method FLASHING

# Create a session for a user
python scripts/run_kyc.py session --workflow-id <uuid> --vendor-data user-123

# Get the decision (or poll until a terminal status)
python scripts/run_kyc.py decision <session_id>
python scripts/run_kyc.py decision <session_id> --poll --interval 15

# Full flow: create workflow + session in one command
python scripts/run_kyc.py full --vendor-data user-123 --callback https://myapp.com/done
```

Can also be imported:

```python
from scripts.run_kyc import setup_kyc_workflow, create_kyc_session, get_decision, poll_decision
```
