---
name: didit-verification-management
description: >
  Manages the whole Didit identity verification platform over the API: programmatic account and
  application setup, API keys, workflows, verification sessions (create, retrieve, list, approve,
  decline, resubmit, correct data, AML hit review, PDF, share, delete), bulk imports, questionnaires,
  block/allow lists, users (KYC) and businesses (KYB) with AML monitoring and biometric templates,
  KYB registry lookups, billing and top-ups, branding, and webhook destinations with signature
  verification. Use when someone needs to create a Didit account or API key, build a verification
  workflow, create or poll verification sessions, review or resubmit a session, manage users,
  businesses or lists, check or top up credits, configure webhooks, or verify Didit webhook signatures.
version: 5.1.0
metadata:
  openclaw:
    requires:
      env: []
    primaryEnv: DIDIT_API_KEY
    emoji: "🛡️"
    homepage: https://docs.didit.me
---

# Didit Identity Verification Platform

## Overview

The hub skill for the Didit platform: account and application setup, workflows, sessions, bulk imports, questionnaires, lists, users (KYC), businesses (KYB), billing, branding and webhooks.

**Related skills:**

| Need | Skill |
|---|---|
| One standalone check (ID scan, liveness, face match, AML, PoA, email, phone, database validation, age, face search) | `didit-id-document-verification`, `didit-liveness-detection`, `didit-face-match`, `didit-aml-screening`, `didit-proof-of-address`, `didit-email-verification`, `didit-phone-verification`, `didit-database-validation`, `didit-biometric-age-estimation`, `didit-face-search` |
| End-to-end KYC onboarding flow | `didit-kyc-onboarding` |
| Create transactions, Travel Rule, wallet screening, transaction rules | `didit-transaction-monitoring` |
| Send user events (logins, account changes) for monitoring | `didit-event-monitoring` |
| Cases, case blueprints, regulatory reports | `didit-case-management` |
| Fraud networks (linked users, devices, documents) | `didit-fraud-networks` |
| Fraud checks | `didit-fraud-check` |
| Custom document extraction (Document AI) | `didit-document-ai` |
| Web and mobile SDKs, SDK tokens | `didit-sdk-integration` |
| Didit from an MCP client | `didit-mcp-server` |

**Pricing:** a session costs the sum of the features its workflow runs, and only features that finish are charged (the workflow's `total_price`, which excludes variable-priced features such as `DATABASE_VALIDATION` and `PHONE_VERIFICATION`); each organization gets 500 free checks a month for each core KYC feature (document capture, passive liveness, face match, Device & IP Analysis). No list price is published for the management endpoints themselves. These are the list prices until 1 November 2026, when Didit pricing changes and the 500 free checks a month become $10 of free credit a month. Check [didit.me/pricing](https://didit.me/pricing) for current prices.

**Base URLs:** `https://verification.didit.me/v3` (everything with `x-api-key`), `https://apx.didit.me/auth/v2` (account setup).

**API Reference Links:**
- **Account Setup:** [Register](https://docs.didit.me/auth-api/register) | [Verify Email](https://docs.didit.me/auth-api/verify-email) | [Login](https://docs.didit.me/auth-api/login) | [Get Credentials](https://docs.didit.me/auth-api/get-credentials) | [Create Application](https://docs.didit.me/auth-api/create-application) | [Update Application](https://docs.didit.me/auth-api/update-application)
- **Sessions:** [Create](https://docs.didit.me/sessions-api/create-session) | [Retrieve](https://docs.didit.me/sessions-api/retrieve-session) | [List](https://docs.didit.me/sessions-api/list-sessions) | [Delete](https://docs.didit.me/sessions-api/delete-session) | [Update Status](https://docs.didit.me/sessions-api/update-status) | [Preview Resubmission](https://docs.didit.me/sessions-api/preview-resubmission) | [Update Feature Status](https://docs.didit.me/sessions-api/update-feature-status) | [Update AML Hit Status](https://docs.didit.me/sessions-api/update-aml-hit-status) | [Update Data](https://docs.didit.me/sessions-api/update-data) | [PDF](https://docs.didit.me/sessions-api/generate-pdf) | [Share](https://docs.didit.me/sessions-api/share-session/share) | [Import](https://docs.didit.me/sessions-api/share-session/import)
- **Session Operations:** [Batch Delete](https://docs.didit.me/management-api/sessions/batch-delete) | [Deletion Job](https://docs.didit.me/management-api/sessions/get-deletion-job) | [List Reviews](https://docs.didit.me/management-api/sessions/list-reviews) | [Create Review](https://docs.didit.me/management-api/sessions/create-review)
- **Workflows:** [Create](https://docs.didit.me/management-api/workflows/create) | [List](https://docs.didit.me/management-api/workflows/list) | [Get](https://docs.didit.me/management-api/workflows/get) | [Update](https://docs.didit.me/management-api/workflows/update) | [Delete](https://docs.didit.me/management-api/workflows/delete) | [Feature Configs](https://docs.didit.me/management-api/workflows/feature-configs)
- **Questionnaires:** [Create](https://docs.didit.me/management-api/questionnaires/create) | [List](https://docs.didit.me/management-api/questionnaires/list) | [Get](https://docs.didit.me/management-api/questionnaires/get) | [Update](https://docs.didit.me/management-api/questionnaires/update) | [Delete](https://docs.didit.me/management-api/questionnaires/delete)
- **Users (KYC):** [List](https://docs.didit.me/management-api/users/list) | [Create](https://docs.didit.me/management-api/users/create) | [Get](https://docs.didit.me/management-api/users/get) | [Update](https://docs.didit.me/management-api/users/update) | [Update Status](https://docs.didit.me/management-api/users/update-status) | [Delete](https://docs.didit.me/management-api/users/delete) | [PDF](https://docs.didit.me/management-api/users/generate-pdf) | [Upload Face](https://docs.didit.me/management-api/users/upload-face)
- **Businesses (KYB):** [List](https://docs.didit.me/management-api/businesses/list) | [Create](https://docs.didit.me/management-api/businesses/create) | [Get](https://docs.didit.me/management-api/businesses/get) | [Update](https://docs.didit.me/management-api/businesses/update) | [Update Status](https://docs.didit.me/management-api/businesses/update-status) | [Delete](https://docs.didit.me/management-api/businesses/delete) | [KYB Registry](https://docs.didit.me/standalone-apis/kyb-registry)
- **AML Monitoring:** [Toggle Users](https://docs.didit.me/management-api/aml-monitoring/toggle-users) | [Toggle Businesses](https://docs.didit.me/management-api/aml-monitoring/toggle-businesses) | [Get Job](https://docs.didit.me/management-api/aml-monitoring/get-job)
- **Biometric Templates:** [Overview](https://docs.didit.me/management-api/biometric-templates/overview) | [List](https://docs.didit.me/management-api/biometric-templates/list) | [Count](https://docs.didit.me/management-api/biometric-templates/count) | [Get](https://docs.didit.me/management-api/biometric-templates/get) | [Purge](https://docs.didit.me/management-api/biometric-templates/purge) | [Batch Purge](https://docs.didit.me/management-api/biometric-templates/batch-purge)
- **Transactions:** [List](https://docs.didit.me/management-api/transactions/list) | [Create](https://docs.didit.me/management-api/transactions/create) | [Get](https://docs.didit.me/management-api/transactions/get)
- **Billing:** [Balance](https://docs.didit.me/management-api/billing/balance) | [Top Up](https://docs.didit.me/management-api/billing/top-up)
- **Customization:** [Get](https://docs.didit.me/management-api/customization/get) | [Update](https://docs.didit.me/management-api/customization/update)
- **Lists (block/allow/custom):** [Overview](https://docs.didit.me/management-api/lists/overview) | [List](https://docs.didit.me/management-api/lists/list) | [Create](https://docs.didit.me/management-api/lists/create) | [Get](https://docs.didit.me/management-api/lists/get) | [Update](https://docs.didit.me/management-api/lists/update) | [Delete](https://docs.didit.me/management-api/lists/delete) | [Entries](https://docs.didit.me/management-api/lists/list-entries) | [Add Entry](https://docs.didit.me/management-api/lists/create-entry) | [Upload Face](https://docs.didit.me/management-api/lists/upload-face) | [Delete Entry](https://docs.didit.me/management-api/lists/delete-entry)
- **Bulk Import:** [Import Verifications](https://docs.didit.me/sessions-api/import-verifications)
- **Webhook Destinations:** [List](https://docs.didit.me/management-api/webhook/list-destinations) | [Create](https://docs.didit.me/management-api/webhook/create-destination) | [Get](https://docs.didit.me/management-api/webhook/get-destination) | [Update](https://docs.didit.me/management-api/webhook/update-destination) | [Delete](https://docs.didit.me/management-api/webhook/delete-destination)
- **Guides:** [Programmatic Registration](https://docs.didit.me/integration/programmatic-registration) | [API Keys](https://docs.didit.me/console/api-keys) | [Webhooks](https://docs.didit.me/integration/webhooks) | [Rate Limiting](https://docs.didit.me/integration/rate-limiting) | [Verification Statuses](https://docs.didit.me/integration/verification-statuses) | [Sandbox Testing](https://docs.didit.me/integration/sandbox-testing) | [MCP Server](https://docs.didit.me/integration/mcp/overview) | [API Overview](https://docs.didit.me/sessions-api/management-api)

---

## Authentication

| Endpoints | Auth | Header |
|---|---|---|
| Register, Verify Email, Resend Code, Login | None | (unauthenticated) |
| Organizations and applications (`/organizations/me/...`) | Bearer | `Authorization: Bearer <access_token>` (from verify-email or login) |
| Everything on `verification.didit.me/v3` | API key | `x-api-key: <api_key>` |

Every request to `verification.didit.me` needs the `x-api-key` header. Use your application's API key from the [Didit Business Console](https://business.didit.me) under **Developers > API keys**, or create an account and key programmatically (see Getting Started). Named keys with custom access need read or write on the resource each section uses (Sessions, Decisions, Media, Users, Businesses, Transactions, Workflows, Webhooks, Application settings); a key limited to some workflows or to approved sessions only works on the session endpoints.

### API keys

| Topic | Behaviour |
|---|---|
| Primary secret | Every application has one with full access. It can't be edited or revoked, only rotated. `application.api_key` from verify-email is this key. |
| Named keys | One per service or partner. Created, edited, rotated and revoked only in the console (no API). Expiry: never, 30 days, 90 days, a year or a chosen date (ends that day, UTC). |
| Access | None, Read or Write per resource. Read covers `GET`; write covers `POST`, `PUT`, `PATCH`, `DELETE`. Resources: **Sessions** (write also runs standalone checks and imports), **Decisions** (write: approve, decline, review, feature and AML hit statuses), **Media** (read only), **Users**, **Businesses**, **Transactions**, **Workflows** (also questionnaires and lists), **Webhooks**, **Application settings** (customization, balance, top-up), **Analytics** (read only). |
| Limits | **Workflows**: only sessions of the chosen workflows are visible and can be created; others answer `404`. **Only approved sessions**: declined, in-review and unfinished sessions are hidden. A key with either limit can't access users, businesses, transactions or analytics, and can't run standalone checks. |
| IP allowlist | Up to 20 IPv4/IPv6 addresses or CIDR ranges; requests from elsewhere answer `403`. |
| Rotation | The new secret is shown once; the previous secret keeps working for 24 hours. |
| Reduced output | Without **Media** read, every image, video and PDF URL in a decision is `null` and PDF endpoints answer `403`. Without **Sessions** write, the session URL and `session_token` come back `null`. |
| Status codes | `401` expired key; `403` missing, wrong or revoked key, no access to the resource, or outside the IP list; `404` session outside the key's limits. |

---

## Getting Started (No Account Yet?)

If you don't have a Didit API key, create one in 2 API calls:

1. **Register:** `POST https://apx.didit.me/auth/v2/programmatic/register/` with `{"email": "you@yourdomain.com", "password": "MyStr0ng!Pass"}`
2. **Check email** for a 6-character verification code
3. **Verify:** `POST https://apx.didit.me/auth/v2/programmatic/verify-email/` with `{"email": "you@yourdomain.com", "code": "A3K9F2"}`. The key is in the response at `application.api_key`.

**To add credits:** `GET /v3/billing/balance/` to check, `POST /v3/billing/top-up/` with `{"amount_in_dollars": 50}` for a Stripe checkout link.

**Zero to a live verification link in 4 calls:**

```python
import requests

AUTH = "https://apx.didit.me/auth/v2"
API = "https://verification.didit.me/v3"

# 1. Register: emails a 6-character code (valid 10 minutes)
requests.post(f"{AUTH}/programmatic/register/",
              json={"email": "you@yourdomain.com", "password": "MyStr0ng!Pass"}).raise_for_status()

# 2. Verify the code: the response carries the application's API key
resp = requests.post(f"{AUTH}/programmatic/verify-email/",
                     json={"email": "you@yourdomain.com", "code": "A3K9F2"})
resp.raise_for_status()
headers = {"x-api-key": resp.json()["application"]["api_key"]}

# 3. Create a KYC workflow from an ordered `features` array
wf = requests.post(f"{API}/workflows/", headers=headers, json={
    "workflow_label": "My KYC",
    "features": [
        {"feature": "OCR"},
        {"feature": "LIVENESS", "config": {"face_liveness_method": "PASSIVE"}},
        {"feature": "FACE_MATCH"},
    ],
}).json()

# 4. Create a session and send the user to its URL
session = requests.post(f"{API}/session/", headers=headers,
                        json={"workflow_id": wf["uuid"], "vendor_data": "user-123"}).json()
print("Send the user to:", session["url"])
```

---

## Account Setup

**Base URL:** `https://apx.didit.me/auth/v2`

| Step | Endpoint | Body | Success response |
|---|---|---|---|
| 1. Register | `POST /programmatic/register/` | `email`, `password` | `201` `{"message", "email"}`. Re-registering an email that is not verified yet returns `200` "A new verification code has been sent to your email." |
| 2. Verify email | `POST /programmatic/verify-email/` | `email`, `code` (6 characters) | `200` `{access_token, refresh_token, expires_in, organization{uuid, name}, application{uuid, name, client_id, api_key}}` |
| Resend code | `POST /programmatic/resend-otp/` | `email`, `password` | `200`. `400` when the credentials are wrong or the email is already verified. |
| 3. Login | `POST /programmatic/login/` | `email`, `password` | `200` `{access_token, refresh_token, expires_in, message}` |
| 4. List organizations | `GET /organizations/me/` (Bearer) | - | `200` paginated `{count, next, previous, results[]}`; each result has `uuid`, `name`, `contact_email`, `created_at` |
| 5. List applications | `GET /organizations/me/{org_id}/applications/` (Bearer) | - | `200` paginated list of application records |
| Create application | `POST /organizations/me/{org_id}/applications/` (Bearer) | optional: `name`, `website_url`, `redirect_uris`, `terms_url`, `privacy_url`, `description` | `201` application record with its own `api_key` (default name "&lt;organization name&gt; App") |
| 6. Get credentials | `GET /organizations/me/{org_id}/applications/{app_id}/` (Bearer) | - | `200` `{uuid, name, client_id, api_key, website_url, redirect_uris, terms_url, privacy_url, description, created_at}` |
| Update application | `PATCH /organizations/me/{org_id}/applications/{app_id}/` (Bearer) | any of the create fields | `200` full record; `uuid`, `client_id` and `api_key` do not change |

| Rule | Value |
|---|---|
| Password | At least 8 characters with an uppercase letter, a lowercase letter, a digit and a special character |
| Verification code | 6 alphanumeric characters, expires 10 minutes after the most recent code was sent; 10 attempts per email per hour with growing backoff |
| Register / resend | 5 per IP per hour (shared); resend also has a 60-second cooldown per email |
| Login | Account lockout after 5 failures (15 min), 10 (1 h), 20 (24 h); per IP 20 a minute and 100 an hour. `403` when the organization enforces SSO. |
| Access token | `expires_in` 86400 (24 h); send it as `Authorization: Bearer`, never to `verification.didit.me` |
| Applications | Only organization owners and admins can create, read or update them (`403` otherwise); `404` for an organization or application you can't see |
| Errors | `429` carries a `Retry-After` header |

**Recover a lost API key:** login, `GET /organizations/me/`, `GET /organizations/me/{org_id}/applications/`, then read `api_key` from the application record.

---

## Workflows

**Base URL:** `https://verification.didit.me/v3`

A workflow is the ordered list of checks a session runs. Each version has a `uuid` (pass it as `workflow_id` when creating sessions and as `{settings_uuid}` here) and a `workflow_id` shared by all versions of the same workflow (equal to `uuid` for version 1). New sessions use the latest `published` version. There is no `workflow_type` field on create: KYC vs KYB follows from the features.

| Method | Path | Notes |
|---|---|---|
| `GET` | `/v3/workflows/` | Paginated `{count, next, previous, results[]}`, newest first; `limit` (default 50), `offset` |
| `POST` | `/v3/workflows/` | `201` with the full configuration. Not idempotent. Max 50 workflows per application. |
| `GET` | `/v3/workflows/{settings_uuid}/` | Full configuration of one version (feature toggles, thresholds, `documents_allowed`, `workflow_graph`, retry policy, prices) |
| `PATCH` | `/v3/workflows/{settings_uuid}/` | Same field whitelist as create; `200` with the resulting version (see versioning below) |
| `DELETE` | `/v3/workflows/{settings_uuid}/` | `204`. Deletes that version only (other versions stay). Sessions keep their results; their workflow reference becomes `null`. |

**List row fields:** `uuid`, `workflow_id`, `version`, `status` (`draft`/`published`), `has_draft`, `workflow_label`, `workflow_type` (`null` for graph workflows), `is_default`, `is_archived`, `is_white_label_enabled`, `features` (one `" + "`-joined string, e.g. `"OCR + LIVENESS + FACE_MATCH"`), `total_price`, `min_price`, `max_price`, `is_simple_workflow`, `is_editable`, `workflow_url`, `max_retry_attempts`, `retry_window_days`, `session_expiration_time`, `created_by`, `updated_at`.

### Create body (strict whitelist: any other key, including `workflow_type` or flat `is_*_enabled` flags, is `400`)

| Body | Type | Default | Description |
|---|---|---|---|
| `features` | array | - | **Required**, at least 1. Items `{"feature": "<UPPERCASE>", "config": {...}, "label": "optional"}` in execution order |
| `workflow_label` | string | `ID Verification` | Max 50 chars; always set it |
| `status` | string | published | Omit to publish; `"draft"` to save without publishing |
| `is_default` | boolean | - | Default workflow for new sessions |
| `is_white_label_enabled` | boolean | `false` | Apply white-label branding |
| `is_desktop_allowed` | boolean | `false` | Allow the flow on desktop browsers |
| `max_retry_attempts` | integer | `3` | 0-10 retries after a decline (`0` blocks after the first decline) |
| `retry_window_days` | integer or null | `7` | 1-365; `null` = all-time limit |
| `face_liveness_max_attempts` | integer | `3` | 1-3 liveness submissions per session |
| `face_match_max_attempts` | integer | `3` | 1-3 face-match submissions per session |
| `session_expiration_time` | integer | `604800` | Seconds before an unfinished session expires: 3600 to 2419200 |

**Feature values:** `OCR`, `NFC`, `LIVENESS`, `FACE_MATCH`, `PROOF_OF_ADDRESS`, `QUESTIONNAIRE`, `DOCUMENT_AI`, `PHONE_VERIFICATION`, `EMAIL_VERIFICATION`, `DATABASE_VALIDATION`, `AML`, `IP_ANALYSIS`, `AGE_ESTIMATION`, `KYB_REGISTRY`, `KYB_DOCUMENTS`, `KYB_KEY_PEOPLE`.

| Goal | Features (in order) |
|---|---|
| Full KYC (ID + selfie) | `OCR`, `LIVENESS`, `FACE_MATCH`, optionally `NFC`, `AML`, `IP_ANALYSIS` |
| Age gating | `AGE_ESTIMATION` (runs liveness itself; `config.enable_id_verification_fallback` sends borderline ages to ID verification) |
| Proof of address | `PROOF_OF_ADDRESS` |
| Questionnaire | `QUESTIONNAIRE` with `config.questionnaire_uuid` |
| Custom documents | `DOCUMENT_AI` (see the `didit-document-ai` skill) |
| Email / phone only | `EMAIL_VERIFICATION` / `PHONE_VERIFICATION` |
| KYB (business) | `KYB_REGISTRY`, `KYB_DOCUMENTS`, `KYB_KEY_PEOPLE`, optionally `AML` |

**Ordering and combination rules (`400` otherwise):**
- `IP_ANALYSIS`, `AML`, `DATABASE_VALIDATION` and `KYB_KEY_PEOPLE` can't be the first feature.
- `FACE_MATCH` and `NFC` come after `OCR`; put `DATABASE_VALIDATION` and person `AML` after `OCR` too (or `AML` after `KYB_REGISTRY` in KYB).
- `KYB_DOCUMENTS` and `KYB_KEY_PEOPLE` come after `KYB_REGISTRY`.
- KYB features may only be combined with `AML`, `DOCUMENT_AI`, `QUESTIONNAIRE`, `PHONE_VERIFICATION`, `EMAIL_VERIFICATION`, `IP_ANALYSIS`; never with person features (`OCR`, `LIVENESS`, `FACE_MATCH`, `NFC`, `PROOF_OF_ADDRESS`, `DATABASE_VALIDATION`, `AGE_ESTIMATION`).
- `QUESTIONNAIRE` needs `config.questionnaire_uuid` (a questionnaire of this application); `KYB_DOCUMENTS` needs `config.kyb_required_document_groups` with at least one group.

**Common per-feature `config` keys** (full list in [feature configs](https://docs.didit.me/management-api/workflows/feature-configs); scores and thresholds are 0-100; action values are uppercase `DECLINE`, `REVIEW`, `NO_ACTION`):

| Feature | Keys |
|---|---|
| `OCR` | `documents_allowed` (`{"USA": {"DL": {"enabled": 1, "sides": 2}}}`; omit, `null` or `{}` = all countries and documents), `duplicated_user_action` |
| `LIVENESS` | `face_liveness_method` (`PASSIVE`, `ACTIVE_3D`, `FLASHING`; uppercase), `face_liveness_score_decline_threshold`, `face_liveness_score_review_threshold` |
| `FACE_MATCH` | `face_match_score_decline_threshold`, `face_match_score_review_threshold` |
| `AML` | `aml_score_approve_threshold`, `aml_score_review_threshold` |
| `AGE_ESTIMATION` | `minimum_age_threshold`, `borderline_minimum_age_threshold`, `borderline_maximum_age_threshold` (1-100), `enable_id_verification_fallback` |
| `QUESTIONNAIRE` | `questionnaire_uuid` (the `questionnaire_id` returned by create questionnaire) |

```python
wf = requests.post("https://verification.didit.me/v3/workflows/",
    headers={"x-api-key": API_KEY},
    json={"workflow_label": "KYC + AML", "features": [
        {"feature": "OCR", "config": {"duplicated_user_action": "REVIEW"}},
        {"feature": "LIVENESS", "config": {"face_liveness_method": "PASSIVE"}},
        {"feature": "FACE_MATCH", "config": {"face_match_score_decline_threshold": 40,
                                             "face_match_score_review_threshold": 60}},
        {"feature": "AML", "config": {"aml_score_approve_threshold": 80}},
    ]}).json()
workflow_uuid = wf["uuid"]
```

**Versioning on PATCH:**

| Current version | `status` sent | Result |
|---|---|---|
| published | none | Updated in place (same `uuid` and `version`) |
| published | `"published"` | New published version (new `uuid`, `version` + 1) returned; any draft in the group is deleted. Use the returned `uuid` from now on. |
| published | `"draft"` | `400` "Cannot revert a published version to draft." |
| draft | `"published"` | The draft is updated and published |
| draft | none or `"draft"` | The draft is updated and stays a draft |

---

## Sessions

**Base URL:** `https://verification.didit.me/v3`

**Lifecycle:** create session, user verifies at `url`, webhook or poll the decision, optionally review (update status, resubmit, correct data).

**Statuses:** `Not Started`, `In Progress`, `Approved`, `Declined`, `In Review`, `Expired`, `Abandoned`, `Kyc Expired`, `Resubmitted`, `Awaiting User` (KYB waiting for its key people). There is no `Pending` status.

**Rate limits (per key, per minute):** all `GET` 600; all `POST`/`PATCH`/`DELETE` 300. `POST /v3/session/` has its own 600 limit but also counts toward the 300 write limit, so plan for 300. `update-data` and `update-poa-data` 10 each; `generate-pdf` 50. A `429` carries `Retry-After`.

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/v3/session/` | Create a session |
| `GET` | `/v3/session/{sessionId}/decision/` | Full results |
| `GET` | `/v3/sessions/` | List and filter sessions |
| `DELETE` | `/v3/session/{sessionId}/delete/` | Delete one KYC or KYB session |
| `POST` | `/v3/sessions/delete/` | Delete KYC sessions in bulk |
| `GET` | `/v3/sessions/delete/{job_id}/` | Poll a bulk deletion job |
| `PATCH` | `/v3/session/{sessionId}/update-status/` | Approve, decline or resubmit |
| `POST` | `/v3/session/{sessionId}/resubmission-preview/` | Preview the resubmission email |
| `PATCH` | `/v3/session/{sessionId}/features/{nodeId}/update-status/` | Set one step's status |
| `PATCH` | `/v3/session/{sessionId}/update-aml-hit-status/` | Review one AML hit |
| `PATCH` | `/v3/session/{sessionId}/bulk-update-aml-hit-status/` | Review several AML hits |
| `PATCH` | `/v3/session/{sessionId}/update-data/` | Correct extracted ID data |
| `PATCH` | `/v3/session/{sessionId}/update-poa-data/` | Correct Proof of Address data |
| `PATCH` | `/v3/session/{sessionId}/kyb/{companyUuid}/update-data/` | Correct KYB company data |
| `PATCH` | `/v3/session/{sessionId}/kyb/parties/{partyUuid}/` | Skip or restore a KYB key person |
| `GET` | `/v3/session/{sessionId}/generate-pdf/` | PDF report |
| `POST` | `/v3/session/{sessionId}/share/` | Share token for another application |
| `POST` | `/v3/session/import-shared/` | Import a shared session |
| `GET`/`POST` | `/v3/sessions/{session_id}/reviews/` | Activity feed / add a note |
| `POST` | `/v3/session/{sessionId}/sandbox/arm/` | Sandbox only: arm a test scenario |

### 1. Create Session

```
POST /v3/session/
```

| Body | Type | Required | Description |
|---|---|---|---|
| `workflow_id` | uuid | **Yes** | Workflow `uuid` |
| `vendor_data` | string | No | Your user or business id. Links the session to a User/Business entity and drives duplicate detection. An unfinished session with the same `vendor_data` and workflow is returned (`201`, `callback` and `metadata` updated) instead of a new one. |
| `callback` | url | No | Redirect after the flow; Didit appends `verificationSessionId` and `status` |
| `callback_method` | string | No | `initiator` (default), `completer` or `both` |
| `metadata` | JSON | No | Any JSON (an object is recommended); echoed in the decision and webhooks |
| `language` | string | No | UI language: ISO 639-1 code or `pt-BR`, `zh-CN`, `zh-TW`, `cnr`; defaults to browser detection |
| `contact_details` | object | No | `email`, `phone` (E.164), `send_notification_emails`, `email_lang`: pre-fill the email/phone steps and send status emails |
| `expected_details` | object | No | Values to compare with what the user submits (mismatches become warnings), see below |
| `portrait_image` | base64 | Conditional | Reference face, max 2 MB, JPEG/PNG/WebP/TIFF. Required for biometric-authentication workflows and graph workflows where face match runs before ID verification, unless the `vendor_data` user already has a stored face (`400` otherwise). |
| `multi_account_segment` | string | No | Max 64 chars. Duplicate-face checks only compare sessions with the same segment; blocklists ignore it. |
| `sandbox_scenario` | string | No | Sandbox applications only (`400` on live): scenario slug from [sandbox testing](https://docs.didit.me/integration/sandbox-testing) |

| `expected_details` key | Description |
|---|---|
| `first_name`, `last_name` | Fuzzy-matched |
| `date_of_birth` | `YYYY-MM-DD` |
| `gender` | `M` or `F` |
| `nationality`, `country`, `id_country`, `poa_country` | ISO 3166-1 alpha-3; `id_country` takes priority over `country` for the ID document |
| `address` | Human-readable address for PoA matching; needs `country` or `poa_country` (`400` otherwise) |
| `identification_number` | Expected document, personal or tax number |
| `ip_address` | Expected IP |
| `expected_document_types` | Array of `P`, `ID`, `DL`, `RP`, `HIC`, `TC`, `SSC` |
| `company_name`, `registry_country`, `registration_number` | KYB sessions: pre-fill the registry search; `registry_country` is ISO alpha-2 or a subdivision such as `US-CA` |

**Response (201):**

```json
{
  "session_id": "11111111-2222-3333-4444-555555555555",
  "session_number": 1234,
  "session_token": "abcdef123456",
  "url": "https://verify.didit.me/session/abcdef123456",
  "vendor_data": "user-123",
  "metadata": {"plan": "pro"},
  "status": "Not Started",
  "workflow_id": "a1b2c3d4-5678-90ab-cdef-111111111111",
  "workflow_version": 1,
  "callback": "https://yourdomain.com/verified"
}
```

Send the user to `url`, or pass `session_token` to an SDK (see `didit-sdk-integration`).

### 2. Retrieve Session (Get Decision)

```
GET /v3/session/{sessionId}/decision/
```

Top-level keys: `session_id`, `session_kind`, `session_number`, `session_url`, `status`, `workflow_id`, `features`, `vendor_data`, `metadata`, `expected_details`, `contact_details`, `callback`, `created_at`, `expires_at`, `environment`, `resubmissions`, `reviews`, plus one array per feature: `id_verifications`, `nfc_verifications`, `liveness_checks`, `face_matches`, `phone_verifications`, `email_verifications`, `poa_verifications`, `document_ai_documents`, `questionnaire_responses`, `aml_screenings`, `ip_analyses`, `database_validations` (KYB: `registry_checks`, `key_people_checks`, `document_verifications`). Each feature block carries its `node_id`, which the review endpoints below take. Media URLs are presigned and expire (about 4 hours): re-fetch the decision instead of storing them.

### 3. List Sessions

```
GET /v3/sessions/
```

| Query | Description |
|---|---|
| `session_kind` | `user` (default), `business` or `all` |
| `status` | e.g. `Approved`, `Declined`, `In Review` |
| `vendor_data` | Exact match |
| `workflow_id`, `country`, `search`, `date_from`, `date_to` | Common filters |
| `limit` / `offset` | Page size (default 50) / rows to skip |

**Response (200):** `{count, next, previous, results[]}`, newest first. Each row has `session_kind` (`user` or `business`).

### 4. Delete Sessions

```
DELETE /v3/session/{sessionId}/delete/      # one KYC or KYB session (KYB also deletes its key-people verifications)
POST   /v3/sessions/delete/                 # KYC sessions in bulk
GET    /v3/sessions/delete/{job_id}/        # poll a bulk job
```

Deletion is permanent: the session, its media, extracted data, reviews and its face embedding are deleted (unless a face template is retained). No webhook is sent. Blocklist entries made from the session and the User/Business entity are not removed (use the lists and users/businesses endpoints).

| Body (both endpoints, optional) | Description |
|---|---|
| `retain_face_embeddings` | `true` keeps one image-free face template on the session's User (duplicate detection keeps working); `false` deletes it; omit to use the application policy |
| `face_retention_days` | 1-3650; required when a template is retained and the application sets no period |
| `face_retention_deadline` | Future date-time hard expiry for the template |
| `deletion_instruction` | `operational_session_delete` (default) or `privacy_erasure` (data-subject requests: purges every retained template of that User; can't be combined with `retain_face_embeddings: true`) |
| `instruction_id` | Your reference (max 255), kept on the audit trail |
| `session_numbers` | Bulk only: digit-only strings, e.g. `["1201", "1202"]` (required unless `delete_all`) |
| `delete_all` | Bulk only: delete every KYC session of the application |

- Single delete: `200` `{session_id, session_number, face_retention_outcome, biometric_template_uuid, biometric_template_expires_at, deleted_child_verifications}`; `face_retention_outcome` is `deleted`, `retained_with_user`, `none` or `ineligible_no_vendor_user`. A repeat call returns `404`; after a `503` repeat the request.
- Bulk delete: up to 20 sessions `200` `{"results": [...]}`; more `202` with `{job_id, status, ...}`. Poll the job until `status` is `COMPLETED` or `FAILED` (`PENDING`, `PROCESSING` before that); it reports `total`, `processed`, `outcomes`, `deleted_child_verifications`, `error`.

### 5. Update Session Status (approve, decline, resubmit)

```
PATCH /v3/session/{sessionId}/update-status/
```

| Body | Type | Required | Description |
|---|---|---|---|
| `new_status` | string | **Yes** | `Approved`, `Declined` or `Resubmitted` |
| `comment` | string | No | Reason, stored in the session's reviews |
| `nodes_to_resubmit` | array | No | For `Resubmitted`: `[{"node_id": "ocr", "feature": "OCR"}]`. Omit to auto-select steps already attempted that need it. |
| `send_email` | boolean | No | Email the user (default `false`) |
| `email_address` | string | Conditional | Required when `send_email` is `true` |
| `email_language` | string | No | Default `en` |
| `email_preview_token` | string | No | `preview_token` from resubmission-preview; with `send_email` only. `409` if the email content changed or the token expired (15 minutes). |

- **Allowed current statuses:** `Approved`, `Declined`, `In Review`, `Kyc Expired`, `Abandoned`, `Resubmitted`. `Not Started`, `In Progress`, `Awaiting User` and `Expired` sessions return `400`. The new status must differ from the current one.
- **Response (200):** `{"session_id": "..."}`. Fires `status.updated`.
- **`node_id`:** read it from the decision's feature blocks. Workflows built with `POST /v3/workflows/` use the slug of the feature (`ocr`, `liveness`, `face_match`, ...); console-built graphs use ids such as `feature_ocr_1`.
- **Resubmitted:** the selected steps' data is deleted, the expiry restarts and the same `url` works again. Server-side steps (`AML`, `DATABASE_VALIDATION`, `IP_ANALYSIS`) re-run without the user; `KYB_REGISTRY` and `KYB_KEY_PEOPLE` can't be resubmitted directly.

**Preview the resubmission email first (optional):** `POST /v3/session/{sessionId}/resubmission-preview/` with `nodes_to_resubmit`, `email_address`, `email_language`. Changes nothing and sends nothing; returns `recipient`, `sender`, `subject`, `html`, `nodes_to_resubmit`, `requires_user_action` and `preview_token`. Then call update-status with `new_status: "Resubmitted"`, the same selection, `send_email: true` and `email_preview_token`.

### 6. Step and AML Hit Review

| Endpoint | Body | Notes |
|---|---|---|
| `PATCH /v3/session/{sessionId}/features/{nodeId}/update-status/` | `new_status` (`Approved`, `Declined`, `In Review`; required), `comment` | One step's status (use `default` as `nodeId` for non-graph workflows). Must differ from the current one. Returns `{session_id, node_id, feature_type, new_status}`. Not available for standalone API sessions. Fires `data.updated`. |
| `PATCH /v3/session/{sessionId}/update-aml-hit-status/` | `hit_id`, `review_status` (both required), `node_id` | `hit_id` is the `id` of an entry in the AML check's `hits`. Fires `data.updated`. |
| `PATCH /v3/session/{sessionId}/bulk-update-aml-hit-status/` | `hit_updates: [{"hit_id", "review_status"}]`, `node_id` | All or nothing: an unknown `hit_id` returns `404` and nothing changes. |

`review_status`: `Unreviewed`, `Confirmed Match`, `False Positive`, `Inconclusive`. Reviewer decisions survive ongoing-monitoring re-screens. `node_id` (body or query) targets one AML check when the workflow has several.

### 7. Correct Extracted Data

Send only the fields to change. Pass `node_id` (body or query) when the workflow has several checks of the same kind. KYC and PoA corrections fire `data.updated` (trigger `manual_review`).

| Endpoint | Session statuses | Fields |
|---|---|---|
| `PATCH /v3/session/{sessionId}/update-data/` | `Approved`, `Declined`, `In Review`, `Kyc Expired` | `document_type`, `document_subtype`, `document_number`, `personal_number`, `date_of_birth`, `date_of_issue`, `expiration_date`, `issuing_state`, `first_name`, `last_name`, `gender` (`M`/`F`/`U`), `address`, `place_of_birth`, `nationality`, `marital_status`, `extra_fields`, `parsed_address` |
| `PATCH /v3/session/{sessionId}/update-poa-data/` | same | `issuing_state`, `document_type`, `document_language`, `issuer`, `issue_date`, `poa_address`, `name_on_document`, `extra_fields`, `poa_parsed_address` |
| `PATCH /v3/session/{sessionId}/kyb/{companyUuid}/update-data/` | any | `company_name`, `registration_number`, `country_code`, `region`, `incorporation_date`, `registration_date`, `dissolution_date`, `tax_number`, `legal_address`, `company_type`, `registry_status`, `verification_status`, `alternative_names`, `nature_of_business`, `registered_capital`, `registered_capital_amount`, `registered_capital_currency`, `website`, `email`, `phone`, `legal_entity_identifier`, `location_of_registration`, `vat_number`, `control_scheme`. `{}` echoes the company without changes. Needs **Businesses** write. |
| `PATCH /v3/session/{sessionId}/kyb/parties/{partyUuid}/` | any | `is_skipped` (required): `true` drops a key person from the Key People check (e.g. their KYC session was deleted) and recomputes the business session; `false` puts them back. Needs **Businesses** write. |

### 8. Generate PDF Report

```
GET /v3/session/{sessionId}/generate-pdf/
```

Returns `application/pdf` (attachment). Only for KYC sessions that are `Approved`, `Declined`, `In Review` or `Kyc Expired` and KYB sessions that are `Approved`, `Declined` or `In Review`; other statuses return `403`. Needs **Media** read on a scoped key. 50 per minute.

### 9. Share and Import (reusable KYC between applications)

```
POST /v3/session/{sessionId}/share/
POST /v3/session/import-shared/
```

| Share body | Required | Description |
|---|---|---|
| `for_application_id` | **Yes** | UUID of the Didit application that will import (not your own) |
| `ttl_in_seconds` | No | 60-86400, default 3600 |

Share works for `Approved`, `Declined` or `In Review` sessions (`400` otherwise) and returns `200` `{share_token, for_application_id, session_kind}`.

| Import body | Required | Description |
|---|---|---|
| `share_token` | **Yes** | Token from the sharing application |
| `trust_review` | **Yes** | `true` keeps the original status; `false` puts the imported session `In Review` |
| `workflow_id` | **Yes** | A workflow `uuid` of the importing application (`404` otherwise) |
| `vendor_data` | No | Your user id |

Import returns `201` with the decision of the new session. A session can be imported once per application (`403` on a second import); an expired, invalid or other-application token returns `400`.

### 10. Session Reviews (activity feed)

```
GET  /v3/sessions/{session_id}/reviews/
POST /v3/sessions/{session_id}/reviews/
```

- **GET** (KYC sessions): paginated `{count, next, previous, results[]}`; each item has `uuid`, `activity_type` (`COMMENT`, `STATUS_UPDATED`, `KYC_DATA_UPDATED`, `POA_DATA_UPDATED`, `AML_HIT_STATUS_UPDATED`, ...), `actor_display`, `actor_email`, `actor_type` (`API_KEY`, `CONSOLE_USER`, `SYSTEM`), `previous_status`, `new_status`, `comment`, `mentioned_emails`, `previous_value`, `new_value`, `changed_fields`, `metadata`, `created_at`.
- **POST** adds a note only: `comment` and `new_status` are both optional, `new_status` (any session status) is just a label. It **never changes the session status and sends no webhook**. Response `201` `{user, new_status, comment, created_at}`. To approve or decline, use update-status.

### 11. Sandbox: Arm a Scenario

`POST /v3/session/{sessionId}/sandbox/arm/` with header `Session-Token: <session_token>` (not `x-api-key`) and body `{"scenario": "<slug>"}` applies a sandbox scenario before the user starts. Returns `{session_id, scenario, status}`; `400` once the verification has started, `404` on live applications. Scenario slugs and magic values: [sandbox testing](https://docs.didit.me/integration/sandbox-testing).

---

## Bulk Import (Migration)

Import historical verifications from a CSV or NDJSON file in Didit's canonical schema (map your previous provider's export to it first).

```
POST /v3/session/imports/                       # JSON {source_file_url, ...} or multipart with `file`
GET  /v3/session/imports/template/?import_type=  # canonical CSV header for that import type
GET  /v3/session/imports/{importId}/            # job status and counters
GET  /v3/session/imports/{importId}/errors/     # per-row errors (row_number, external_id, error, raw_row)
```

| Body | Required | Description |
|---|---|---|
| `source_file_url` or `file` | **Yes** (one) | Public URL of the file, or a multipart upload. Both or neither: `400`. Max 25 MB. |
| `import_type` | No | `user_verification` (default), `business_verification` (needs a KYB workflow), `status_rules`, `transactions` |
| `workflow_id` | **Yes** except `transactions` | Workflow `uuid`; `user_verification` rejects KYB workflows |
| `source_format` | No | `csv` or `ndjson`. An uploaded file's format comes from its extension (`.csv`, `.ndjson`); other extensions return `400`. |

- Imports are off by default and enabled per organization by Didit (`403` otherwise); sandbox applications get `403`.
- One active import job per application (`429` while one runs).
- `201` job: `uuid`, `status` (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`, `PAUSED`, `CANCELLED`), `import_type`, `source_format`, `source_filename`, `total_rows`, `processed_rows`, `created_count`, `updated_count`, `skipped_count`, `failed_count`, `last_error`, timestamps.
- Imported records are tagged `metadata.imported_from: "generic"`.

---

## Lists (Block / Allow / Custom)

A **blocklist** match declines future verifications or screenings; **allowlists** and **custom** lists feed workflow conditions and rules. Lists are documented in the docs pages linked above.

- `list_type`: `blocklist` (one system list per entry type, created automatically; can't be created, renamed or deleted), `allowlist`, `custom`.
- `entry_type`: `face`, `document`, `phone`, `email`, `ip_address`, `device_fingerprint`, `wallet_address`, `bank_account`, `user`, `business`, `country`, `key`.

| Method | Path | Notes |
|---|---|---|
| `GET` | `/v3/lists/` | Filters `list_type`, `entry_type`; `ordering` `created_at`, `entry_count`, `last_entry_added_at` (prefix `-` for descending; default `-created_at`); `limit`, `offset` |
| `POST` | `/v3/lists/` | `name` (unique per application, `400` if taken), `list_type` (`allowlist` or `custom`), `entry_type`, `description` |
| `GET` | `/v3/lists/{list_uuid}/` | One list |
| `PATCH` | `/v3/lists/{list_uuid}/` | `name`, `description`; system lists return `400` |
| `DELETE` | `/v3/lists/{list_uuid}/` | `204`; allowlist and custom lists only |
| `GET` | `/v3/lists/{list_uuid}/entries/` | `search`, `reference_session_id`, `limit`, `offset` |
| `POST` | `/v3/lists/{list_uuid}/entries/` | Add an entry (below); `201` |
| `POST` | `/v3/lists/{list_uuid}/entries/face-upload/` | Add a face from an image |
| `DELETE` | `/v3/lists/{list_uuid}/entries/{entry_uuid}/` | `204`; on a system blocklist it also unblocks the matching entity |

**Find a blocklist uuid:** `GET /v3/lists/?list_type=blocklist&entry_type=face` (or `document`, `phone`, ...).

| Entry body | Required | Description |
|---|---|---|
| `value` | Conditional | The value (email, E.164 phone, IP or CIDR, alpha-3 country, ...). Required unless `reference_session_id` is sent. |
| `reference_session_id` | Conditional | Take the value from a session according to the list's `entry_type` (face, document, phone, email, ip_address, device_fingerprint) |
| `face_image_source` | No | Face blocklist with `reference_session_id`: `liveness` (default), `front_image_camera_front`, `back_image_camera_front` (selfie taken while the user photographed the document) |
| `reference_node_id` | No | With a document-capture `face_image_source`: which ID verification node's selfie to use |
| `reference_object_uuid` | No | Source transaction, user or business, for traceability |
| `display_label`, `comment` | No | Label and reason |
| `metadata` | No | e.g. `{"reference_type": "vendor_user"}` |

**Face upload body:** `image` (base64 JPG or PNG without a `data:` prefix, max 2 MB) and optional `comment`. Face blocklist or face allowlist only (custom lists and other entry types return `400`). No face: `400`; several faces: the largest is used.

**Blocklist matches raise warnings** such as `FACE_IN_BLOCKLIST`, `POSSIBLE_FACE_IN_BLOCKLIST`, `ID_DOCUMENT_IN_BLOCKLIST`, `PHONE_NUMBER_IN_BLOCKLIST`, `EMAIL_IN_BLOCKLIST`, `IP_ADDRESS_IN_BLOCKLIST`, `DEVICE_FINGERPRINT_IN_BLOCKLIST`.

---

## Questionnaires

Custom forms run by the `QUESTIONNAIRE` workflow feature.

| Method | Path | Notes |
|---|---|---|
| `GET` | `/v3/questionnaires/` | Paginated `{count, next, previous, results[]}` |
| `POST` | `/v3/questionnaires/` | `201`; the response's `questionnaire_id` is the value for `config.questionnaire_uuid` |
| `GET` | `/v3/questionnaires/{questionnaire_uuid}/` | One questionnaire |
| `PATCH` | `/v3/questionnaires/{questionnaire_uuid}/` | Partial update |
| `DELETE` | `/v3/questionnaires/{questionnaire_uuid}/` | `204` |

| Body | Required | Description |
|---|---|---|
| `title` | **Yes** | Max 255 chars |
| `languages` | **Yes** | Must include `"en"` |
| `form_elements` | **Yes** | At least one element |
| `default_language` | No | Default `en`; must be in `languages` |
| `description` | No | Shown to users |
| `is_active` | No | Default `true` |
| `status` | No | Omit to publish; `draft` to save without publishing |

| Element field | Description |
|---|---|
| `element_type` | **Required.** `short_text`, `long_text`, `paragraph`, `dropdown`, `single_choice`, `multiple_choice`, `number`, `image`, `file_upload`, `time`, `email`, `address`, `phone`, `country`, `date_picker`, `consent`, `section_header`, `separator`, `heading` (there is no `checkbox` or `date`) |
| `label` | **Required.** Translations for every language in `languages`: `{"en": "Occupation?"}` |
| `id` | Optional stable id (auto `q1`, `q2`, ...) |
| `description`, `placeholder` | Translation objects |
| `is_required` | Default `false` |
| `options` | Required for `dropdown`, `single_choice`, `multiple_choice`: `[{"value": "employed", "label": {"en": "Employed"}}]` (`value` optional) |
| `max_files` | 1-5, for `file_upload` and `image` |
| `validation` | `short_text`/`long_text`: `pattern`, `min_length`, `max_length`; `number`: `min`, `max` |

The API builds simple, linear questionnaires. Branching, conditional questions and repeatable groups are built in the Console: `element_type: "repeatable_group"` and the `branches`, `required_if` and `repeatable_config` fields return `400`. Answers to a Console-built repeatable group come back in the decision as `REPEATABLE_GROUP` elements.

```python
q = requests.post("https://verification.didit.me/v3/questionnaires/",
    headers={"x-api-key": API_KEY},
    json={
        "title": "Employment Details",
        "languages": ["en"],
        "default_language": "en",
        "form_elements": [
            {"element_type": "short_text", "label": {"en": "Occupation?"}, "is_required": True},
            {"element_type": "single_choice", "label": {"en": "Employment status"},
             "options": [{"label": {"en": "Employed"}}, {"label": {"en": "Student"}}]},
        ],
    }).json()
questionnaire_uuid = q["questionnaire_id"]
```

---

## Users (KYC)

Verified individuals keyed by your `vendor_data`. A user's `status` is a monitoring status, not a verification decision: `ACTIVE`, `FLAGGED` or `BLOCKED`.

| Method | Path | Notes |
|---|---|---|
| `GET` | `/v3/users/` | `limit` (default 50), `offset` |
| `POST` | `/v3/users/create/` | `201` full user record; duplicate `vendor_data` returns `400` |
| `GET` | `/v3/users/{vendor_data}/` | One user |
| `PATCH` | `/v3/users/{vendor_data}/` | Send only fields to change (`metadata` is replaced whole) |
| `PATCH` | `/v3/users/{vendor_data}/update-status/` | `status` (required), optional `reason`; `BLOCKED` also adds the `vendor_data` to the system blocklist. Fires `user.status.updated`. |
| `POST` | `/v3/users/delete/` | `vendor_data_list`, `didit_internal_id_list` (combinable), or `delete_all: true`; returns `{deleted}` |
| `GET` | `/v3/users/{vendor_data}/generate-pdf/` | PDF with the user's reportable KYC sessions (newest 20); `403` if none |
| `POST` | `/v3/organization/{organization_id}/application/{application_id}/vendor-users/by-id/{didit_internal_id}/faces/upload/` | Attach a trusted face: `image` (base64 JPG/PNG, max 2 MB), `comment`. Indexed for duplicate detection and face search, not blocklisted. `201`. |

**Create / update fields:** `vendor_data` (required on create), `full_name`, `display_name`, `date_of_birth` (`YYYY-MM-DD`), `status` (default `ACTIVE`), `metadata` (object), `approved_emails`, `approved_phones`, `issuing_states`.

**List row fields:** `didit_internal_id`, `vendor_data`, `display_name`, `full_name`, `effective_name`, `date_of_birth`, `status`, `portrait_image_url`, `session_count`, `approved_count`, `declined_count`, `in_review_count`, `issuing_states`, `approved_emails`, `approved_phones`, `features`, `features_list`, `first_session_at`, `last_session_at`, `last_activity_at`, `tags`, `created_at`.

### AML Ongoing Monitoring (users and businesses)

```
POST /v3/users/aml-monitoring/
POST /v3/businesses/aml-monitoring/
GET  /v3/aml-monitoring/jobs/{job_id}/
```

Body: `is_enabled` (required), `estimate_only` (default `false`: return the cost estimate without changing anything), `vendor_data_list` and/or `didit_internal_id_list` (up to 1000 identifiers in total). Up to 20 profiles run inline (`200` with the finished job); more return `202` and run in the background. Job: `job_id`, `status` (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`), `is_enabled`, `target_type`, `total`, `processed`, `outcomes`, `results[]`, `error`, `created_at`, `completed_at`. Not enough credits: `403` with the `estimate`. AML Monitoring is listed at $0.07 a year on the pricing page.

### Biometric Templates

Image-free face templates an application keeps after deleting sessions (`retain_face_embeddings` or the application's retention policy), so duplicate detection keeps working. API keys only.

| Method | Path | Notes |
|---|---|---|
| `GET` | `/v3/biometric-templates/` | Filters `vendor_data` (substring), `vendor_user_uuid`, `status`, `source_type` (`session_delete`, `automatic_retention`, `backfill`), `retained_from`, `retained_to`, `ordering` (`retained_at`, `expires_at`, with `-`); `limit`, `offset` |
| `GET` | `/v3/biometric-templates/count/` | `{count}` with the same filters |
| `GET` | `/v3/biometric-templates/{template_uuid}/` | One template |
| `DELETE` | `/v3/biometric-templates/{template_uuid}/` | Purge: `{uuid, outcome}` (`purged` or `already_purged`) |
| `POST` | `/v3/biometric-templates/delete/` | `template_uuids` or `delete_all: true` (plus the filters to narrow it): `{results: [{uuid, outcome}]}` |

---

## Businesses (KYB)

Verified companies keyed by `vendor_data`, with the same `ACTIVE` / `FLAGGED` / `BLOCKED` monitoring status.

```
GET    /v3/businesses/                              # limit, offset
POST   /v3/businesses/create/                       # vendor_data, display_name, legal_name, registration_number, country_code (ISO alpha-2), status, metadata
GET    /v3/businesses/{vendor_data}/
PATCH  /v3/businesses/{vendor_data}/                # display_name, legal_name, registration_number, country_code, status, metadata
PATCH  /v3/businesses/{vendor_data}/update-status/  # status (required), optional reason; fires business.status.updated
POST   /v3/businesses/delete/                       # vendor_data_list, didit_internal_id_list, or delete_all: true -> {deleted}
POST   /v3/businesses/aml-monitoring/               # see AML Ongoing Monitoring above
```

### KYB Registry (no session)

| Endpoint | Body | Price |
|---|---|---|
| `POST /v3/kyb/search/` | `country_code` (required; ISO alpha-2, US needs a state such as `US-CA`), `name` and/or `registration_number`, `search_type` (`contains`), `vendor_data`, `metadata`, `webhook_url` | $0.50 per successful search with paid-source results |
| `POST /v3/kyb/select/` | `kyb_response_id` (required), `vendor_data`, `metadata` | Lite profile and officers, $2.00 (prices by country) |
| `POST /v3/kyb/shareholders/` | same as select | Lite plus direct shareholders, $5.00-$22.00 by country |
| `POST /v3/kyb/ubo/` | same as select | Shareholders plus ultimate beneficial owners, $9.00-$96.00 by country |

`kyb_response_id` comes from a search of the same application and is short-lived: select soon, re-search instead of storing it. With `webhook_url` the search returns at once (`search_status: "pending"`) and Didit later POSTs an **unsigned** `kyb.registry_search.resolved` callback (header `X-Didit-Unsigned-Callback: true`); match it by `request_id`. Shareholders and UBO calls can return `202` while the registry is still resolving.

---

## Transactions

Transaction monitoring has its own skill: use **didit-transaction-monitoring** to create transactions, run Travel Rule exchanges, screen wallets and manage rules, and **didit-event-monitoring** for user events. The basic routes:

```
GET   /v3/transactions/          # limit, offset
POST  /v3/transactions/          # required: transaction_id, transaction_category, transaction_details, subject{vendor_data, full_name, ...}
GET   /v3/transactions/{uuid}/   # Didit's transaction uuid from the create response, NOT your transaction_id
```

`transaction_category`: `finance`, `kyc`, `travel_rule`, `user_event`, `audit_trail_event`, `gambling_bet`, `gambling_limit_change`, `gambling_bonus_change`.

---

## Billing

| Endpoint | Body | Response |
|---|---|---|
| `GET /v3/billing/balance/` | - | `{"balance": "142.5000", "auto_refill_enabled": true, "auto_refill_amount": "100.0000", "auto_refill_threshold": "10.0000"}`; the auto-refill values are `null` when unset |
| `POST /v3/billing/top-up/` | `amount_in_dollars` (required, minimum 50), `success_url`, `cancel_url` (pass both explicitly) | `200` `{"checkout_session_id": "cs_...", "checkout_session_url": "https://checkout.stripe.com/..."}` |

Present `checkout_session_url` to the user to pay; the balance rises when the payment settles. Top-up errors (`400`) come as a JSON array, e.g. `["Amount must be at least $50."]`. Organizations on an annual plan get `400` and top up through their account manager.

---

## Customization (Branding)

```
GET   /v3/customization/
PATCH /v3/customization/     # application/json for settings, multipart/form-data for images
```

| PATCH fields | Notes |
|---|---|
| `color_primary`, `color_secondary`, `color_background`, `color_panel`, `color_panel_10`, `color_on_panel_1`, `color_on_panel_2`, `color_on_background`, `color_button_1`, `color_button_2`, `color_button_text_1`, `color_button_text_2`, `color_pill_text` | Hex colors |
| `border_radius_panel`, `border_radius_buttons`, `font_family`, `font_weight` | Layout and font |
| `app_public_name`, `privacy_policy_url`, `skip_welcome_screen`, `disable_login_with_didit`, `hide_progress_bar`, `callback_seconds` | Flow options |
| `image_square`, `image_rectangular`, `image_favicon` | Multipart uploads (logos and favicon) |
| `delete_logo_square`, `delete_logo_rectangular`, `delete_favicon` | `true` removes the image |

Only the fields you send change. A custom domain and white-label email can only be set in the Business Console (`400` here).

---

## Webhook Destinations

Register any number of destinations, each with its own URL, payload version, events and signing secret.

| Method | Path | Notes |
|---|---|---|
| `GET` | `/v3/webhook/destinations/` | Array (oldest first) of `uuid`, `label`, `url`, `enabled`, `webhook_version`, `subscribed_events`, `subscribed_events_count`, `deliveries_count`, `failed_deliveries_count`, `average_response_time_ms`, `error_rate_percentage`, `last_delivery_at`, `created_at`, `updated_at`. No secret in list rows. |
| `POST` | `/v3/webhook/destinations/` | `201` with `secret_shared_key` and a delivery `summary` |
| `GET` | `/v3/webhook/destinations/{destination_uuid}/` | Includes `secret_shared_key` |
| `PATCH` | `/v3/webhook/destinations/{destination_uuid}/` | Same fields as create; `subscribed_events` is replaced, not merged. The secret is not rotated. |
| `DELETE` | `/v3/webhook/destinations/{destination_uuid}/` | `204`; a repeat returns `404` |

| Create body | Required | Description |
|---|---|---|
| `label` | **Yes** | Name, max 255 |
| `url` | **Yes** | HTTPS endpoint, unique per application (`400` if already used) |
| `subscribed_events` | **Effectively yes** | Events to deliver (list below). `[]` returns `400`; omitting it creates a destination that receives **nothing**. |
| `webhook_version` | No | `v1`, `v2` or `v3`; use `v3` |
| `enabled` | No | Default `true`; `false` parks the destination |

```python
dest = requests.post(
    "https://verification.didit.me/v3/webhook/destinations/",
    headers={"x-api-key": API_KEY},
    json={"label": "Prod", "url": "https://yourdomain.com/webhooks/didit", "webhook_version": "v3",
          "subscribed_events": ["status.updated", "data.updated"]},
).json()
secret = dest["secret_shared_key"]   # store it in your secrets manager

# Pause a destination without deleting it
requests.patch(f"https://verification.didit.me/v3/webhook/destinations/{dest['uuid']}/",
               headers={"x-api-key": API_KEY}, json={"enabled": False})
```

---

## Webhook Events & Signatures

Didit `POST`s JSON to every enabled destination subscribed to the event (`User-Agent: DiditWebhook/2.0 +https://didit.me`).

| Event (`webhook_type`) | Fires when |
|---|---|
| `status.updated` | A KYC or KYB session's status changes (KYB payloads add `session_kind: "business"` and `business_session_id`) |
| `data.updated` | Session data is edited after the fact (reviewer corrections, step or AML hit status changes) |
| `user.status.updated` / `user.data.updated` | A user's `ACTIVE`/`FLAGGED`/`BLOCKED` status / profile data changes |
| `business.status.updated` / `business.data.updated` | Same for a business |
| `activity.created` | Accepted in `subscribed_events` but not sent for live traffic |
| `transaction.created` / `transaction.status.updated` | A transaction is created with its first verdict / its status changes |
| `travel_rule.status.updated` | A Travel Rule exchange's status changes |

**Session event envelope:**

| Field | Notes |
|---|---|
| `event_id` | Same across destinations and retries: dedupe on it |
| `webhook_type` | One of the events above |
| `timestamp` | Unix seconds at dispatch (refreshed on each retry; equals `X-Timestamp`) |
| `created_at` | Unix seconds when the record was last updated |
| `application_id`, `environment` | `environment` is `live` or `sandbox` |
| `session_id`, `status` | Status uses the session labels (`Approved`, `Kyc Expired`, ...) |
| `workflow_id`, `workflow_version`, `vendor_data`, `metadata` | When set |
| `sandbox_scenario` | Armed scenario on sandbox sessions, else `null` |
| `trigger` | Optional: `manual_review`, `manual_step_update`, `ongoing_monitoring` |
| `decision` | Only when `status` is `Approved`, `Declined`, `In Review` or `Abandoned`; same schema as the decision endpoint |
| `resubmit_info` | `{nodes_to_resubmit, reasons}` when `status` is `Resubmitted` |

**Delivery:** respond `2xx` fast and process asynchronously. A `5xx`, `404`, timeout or connection failure is retried up to 2 times (about 1 minute, then about 4 minutes later); other `3xx`/`4xx` responses are not retried.

### Signature headers

| Header | Signed content | Use |
|---|---|---|
| `X-Timestamp` | Unix seconds at dispatch | Reject if more than 300 seconds from now |
| `X-Signature-V2` | HMAC-SHA256 (hex) of the canonical JSON: body parsed, whole-number floats turned into ints, `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=False)`. No timestamp prefix. | **Recommended**: survives frameworks that re-encode JSON |
| `X-Signature` | HMAC-SHA256 (hex) of the exact raw body bytes | When you can read the raw body |
| `X-Signature-Simple` | HMAC-SHA256 of `"{timestamp}:{session_id}:{status}:{webhook_type}"` (`"{timestamp}::{status}:{webhook_type}"` for events without a `session_id`) | **Deprecated**: covers the envelope only, not `decision`. If you rely on it, re-fetch the record from the API before acting. |

The key is the destination's `secret_shared_key`.

```python
import hashlib
import hmac
import json
import time


def shorten_floats(value):
    """Whole-number floats become ints, recursively (87.0 -> 87), as Didit does before signing."""
    if isinstance(value, dict):
        return {k: shorten_floats(v) for k, v in value.items()}
    if isinstance(value, list):
        return [shorten_floats(v) for v in value]
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def verify_webhook(body: bytes, headers: dict, secret: str, now: int | None = None, tolerance: int = 300) -> bool:
    """Verify a Didit webhook. `body` is the raw request body, `headers` the request headers (any casing)."""
    h = {str(k).lower(): v for k, v in headers.items()}
    try:
        ts = int(h.get("x-timestamp", ""))
    except (TypeError, ValueError):
        return False
    current = now if now is not None else int(time.time())
    if abs(current - ts) > tolerance:
        return False

    if isinstance(body, str):
        body = body.encode("utf-8")
    key = secret.encode("utf-8")
    candidates = []
    try:
        canonical = json.dumps(
            shorten_floats(json.loads(body)), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        v2 = hmac.new(key, canonical.encode("utf-8"), hashlib.sha256).hexdigest()
        candidates.append((h.get("x-signature-v2"), v2))
    except (ValueError, TypeError):
        pass
    raw = hmac.new(key, body, hashlib.sha256).hexdigest()
    candidates.append((h.get("x-signature"), raw))
    return any(sig and hmac.compare_digest(str(sig), expected) for sig, expected in candidates)
```

```python
# Minimal Flask receiver
import os
from flask import Flask, request, abort

app = Flask(__name__)

@app.post("/webhooks/didit")
def didit_webhook():
    body = request.get_data()  # raw bytes, before any JSON parsing
    if not verify_webhook(body, dict(request.headers), os.environ["DIDIT_WEBHOOK_SECRET"]):
        abort(401)
    event = request.get_json()
    # dedupe on event["event_id"], then queue work by event["webhook_type"]
    return {"ok": True}
```

---

## Error Responses (All Endpoints)

| Code | Meaning | Action |
|---|---|---|
| `400` | Invalid request | Read the field errors in the response body |
| `401` | The API key has expired | Rotate it or create a new key in **Developers > API keys** |
| `403` | Missing, wrong or revoked API key; a scoped key without access to this endpoint; a request from outside the key's IP allowlist; or not enough credits | Read the message in `detail` or `error`: fix the `x-api-key` header or the key's access, or top up |
| `404` | Resource not found, or a session outside a scoped key's workflow/approved-only limits | Check the id and the key's limits |
| `409` | update-status: the `email_preview_token` no longer matches (content changed or older than 15 minutes) | Preview again, then retry |
| `429` | Rate limit: 300 POST/PATCH/DELETE and 600 GET requests a minute per key | Wait the `Retry-After` seconds, then retry |
| `503` | Session or user deletion: a storage dependency is unavailable | Repeat the same request |

Account-setup endpoints (`apx.didit.me/auth/v2`) use Bearer tokens: `401` for a malformed or expired token, `403` without a token or when you are not an owner or admin of the organization, `429` with `Retry-After`.

---

## Common Workflows

### Full KYC Onboarding

```
1. POST /programmatic/register/ + POST /programmatic/verify-email/  -> application.api_key
2. POST /v3/workflows/                -> features [OCR, LIVENESS, FACE_MATCH, AML]; keep wf["uuid"]
3. POST /v3/webhook/destinations/     -> url + subscribed_events ["status.updated", "data.updated"]; store secret_shared_key
4. POST /v3/session/                  -> workflow_id + vendor_data; send the user to url
5. Webhook status.updated             -> verify_webhook(), dedupe on event_id
6. GET /v3/session/{id}/decision/     -> read results (re-fetch for fresh media URLs)
```

### Manual Review and Blocklist

```
1. Webhook: status "In Review"
2. GET /v3/session/{id}/decision/                     -> inspect warnings, AML hits, node_ids
3. AML hits: PATCH .../update-aml-hit-status/         -> False Positive / Confirmed Match
4. Legit:  PATCH .../update-status/ {"new_status": "Approved", "comment": "..."}
   Fraud:  PATCH .../update-status/ {"new_status": "Declined", "comment": "..."}
           GET /v3/lists/?list_type=blocklist&entry_type=face   -> blocklist uuid
           POST /v3/lists/{uuid}/entries/ {"reference_session_id": "<session_id>"}
           (repeat with entry_type=document for the ID document)
```

### Ask the User to Redo a Step

```
1. GET /v3/session/{id}/decision/                     -> node_id of the failed step (e.g. "ocr")
2. POST /v3/session/{id}/resubmission-preview/        -> preview_token (optional)
3. PATCH /v3/session/{id}/update-status/              -> new_status "Resubmitted", nodes_to_resubmit,
                                                         send_email true, email_address, email_preview_token
4. The same url works again; status.updated fires when the user finishes
```

### Reusable KYC Between Applications

```
App A: POST /v3/session/{id}/share/ {"for_application_id": "<app B uuid>"}  -> share_token
App B: POST /v3/session/import-shared/ {"share_token", "trust_review": true, "workflow_id": "<app B workflow uuid>"}
```

### Questionnaire in a Workflow

```
1. POST /v3/questionnaires/  -> questionnaire_id
2. POST /v3/workflows/       -> {"features": [{"feature": "OCR"}, {"feature": "QUESTIONNAIRE",
                                 "config": {"questionnaire_uuid": "<questionnaire_id>"}}]}
3. POST /v3/session/         -> workflow_id = the new workflow's uuid
```

### Data-Subject Erasure

```
1. DELETE /v3/session/{id}/delete/ {"deletion_instruction": "privacy_erasure", "instruction_id": "ticket-123"}
2. POST /v3/users/delete/ {"vendor_data_list": ["user-123"]}
```

### Check Balance Before Creating Sessions

```
1. GET /v3/billing/balance/     -> balance
2. If low: POST /v3/billing/top-up/ {"amount_in_dollars": 50, "success_url": ..., "cancel_url": ...}
3. POST /v3/session/
```

---

## Utility Scripts

### setup_account.py: register, verify, resend the code, log in

```bash
pip install requests
python scripts/setup_account.py register you@yourdomain.com 'MyStr0ng!Pass'
# (check email for the 6-character code)
python scripts/setup_account.py verify you@yourdomain.com A3K9F2      # prints org uuid, app uuid, api_key
python scripts/setup_account.py resend-otp you@yourdomain.com 'MyStr0ng!Pass'
python scripts/setup_account.py login you@yourdomain.com 'MyStr0ng!Pass'
```

### manage_workflows.py: workflow CRUD

```bash
export DIDIT_API_KEY="your_key"
python scripts/manage_workflows.py list --limit 50
python scripts/manage_workflows.py create --label "My KYC" --liveness --face-match
python scripts/manage_workflows.py create --label "Age check" --features '[{"feature": "AGE_ESTIMATION"}]'
python scripts/manage_workflows.py get <uuid>
python scripts/manage_workflows.py update <uuid> --label "Renamed KYC"
python scripts/manage_workflows.py update <uuid> --features '[{"feature":"OCR"},{"feature":"AML"}]' --status published
python scripts/manage_workflows.py delete <uuid>
```

### create_session.py: create, get and list sessions

```bash
export DIDIT_API_KEY="your_key"
python scripts/create_session.py create --workflow-id <uuid> --vendor-data user-123
python scripts/create_session.py create --workflow-id <uuid> --vendor-data user-123 \
    --callback https://yourdomain.com/verified --metadata '{"plan": "pro"}'
python scripts/create_session.py get <session_id>
python scripts/create_session.py list --status Approved --limit 20 --offset 0
```

All scripts can be imported as libraries:

```python
from scripts.setup_account import register, verify_email, resend_otp, login
from scripts.manage_workflows import list_workflows, create_workflow, update_workflow
from scripts.create_session import create_session, get_decision, list_sessions
```
