---
name: didit-id-document-verification
description: >
  Verifies identity documents and digital ID wallets through Didit's standalone APIs. Use when
  an agent needs to verify a passport, ID card, driver's license or residence permit from an
  image or PDF, run OCR and MRZ or barcode extraction, detect screen captures, printed copies,
  portrait manipulation or covered fields, read document warnings, or start a digital ID wallet
  sign-in (MitID, BankID Sweden, iDIN, Finnish Trust Network, Smart-ID, Mobile-ID) without a
  workflow. Covers 14,000+ document types from 220+ countries and territories.
version: 1.3.0
metadata:
  openclaw:
    requires:
      env:
        - DIDIT_API_KEY
    primaryEnv: DIDIT_API_KEY
    emoji: "📋"
    homepage: https://docs.didit.me
---

# Didit ID Verification API

## Overview

Verifies an identity document from images (or PDFs) of its front and back in one synchronous call. Classifies the document automatically (you never declare the country or type), reads the visual zone with OCR, decodes the MRZ and barcodes, cross-checks dates, number formats and MRZ check digits, and by default screens both images for screen replays, printed copies and portrait manipulation. Returns the extracted fields, an `Approved` or `Declined` status and a `warnings` list.

**Key constraints:**
- Formats: **JPEG, PNG, WebP, TIFF or PDF** (extensions `jpg`, `jpeg`, `png`, `webp`, `tiff`, `pdf`). Encrypted PDFs need `front_image_password` / `back_image_password`
- Maximum upload size: **10 MB per side** (larger files get `400`). Images are compressed server-side
- Send the full, uncropped capture with all four corners visible; the service detects, aligns and crops the document itself
- Send `back_image` whenever the document has a back: many ID cards carry the MRZ or barcode there, and a missing back leaves those fields empty without a warning

**Coverage:** 14,000+ document types from 220+ countries and territories: passports, national ID cards, driver's licenses, residence permits and more.

**Pricing:** $0.20 per call that returns `200` (Approved or Declined); `400` responses are not billed, and standalone calls have no free tier. These are the list prices until 1 November 2026, when Didit pricing changes and the 500 free checks a month become $10 of free credit a month. Check [didit.me/pricing](https://didit.me/pricing) for current prices. Digital ID wallets are billed separately (see [Digital ID Wallets](#digital-id-wallets-standalone)).

**Sandbox:** sandbox API keys skip processing and billing and return a static `Approved` mock (a fictional "Sandbox User" USA identity card) after request validation. Nothing is stored.

**API Reference:** https://docs.didit.me/standalone-apis/id-verification
**Feature Guide:** https://docs.didit.me/core-technology/id-verification/overview
**Warnings:** https://docs.didit.me/core-technology/id-verification/warnings-id-verification
**Supported Documents:** https://docs.didit.me/core-technology/id-verification/supported-documents-id-verification

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

## Endpoint

```
POST https://verification.didit.me/v3/id-verification/
```

### Headers

| Header | Value | Required |
|---|---|---|
| `x-api-key` | Your API key | **Yes** |
| `Content-Type` | `multipart/form-data` (set by your HTTP client) | **Yes** |

### Request Parameters (multipart/form-data)

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `front_image` | file | **Yes** | - | Front of the document. JPEG/PNG/WebP/TIFF/PDF, max 10 MB |
| `front_image_password` | string | No | - | Password of an encrypted `front_image` PDF |
| `back_image` | file | No | - | Back of the document. Same formats and limit |
| `back_image_password` | string | No | - | Password of an encrypted `back_image` PDF |
| `perform_document_liveness` | boolean | No | `true` | Screen both images for screen capture, printed copy and portrait manipulation. Any hit declines. `false` skips it and lowers latency |
| `invalid_mrz_action` | string | No | `DECLINE` | `DECLINE` or `NO_ACTION` for `MRZ_VALIDATION_FAILED` |
| `inconsistent_data_action` | string | No | `DECLINE` | `DECLINE` or `NO_ACTION` for `DATA_INCONSISTENT` and `MRZ_AND_DATA_EXTRACTED_FROM_OCR_NOT_SAME` |
| `expiration_date_not_detected_action` | string | No | `NO_ACTION` | `DECLINE` or `NO_ACTION` for `EXPIRATION_DATE_NOT_DETECTED` (many documents print no expiry). A detected past expiry always declines |
| `critical_field_occlusion_action` | string | No | `DECLINE` | `DECLINE` or `NO_ACTION` for `CRITICAL_FIELD_OCCLUSION_DETECTED` |
| `document_or_personal_number_format_mismatch_action` | string | No | `NO_ACTION` | `DECLINE` or `NO_ACTION` for `DOCUMENT_NUMBER_FORMAT_MISMATCH` and `PERSONAL_NUMBER_FORMAT_MISMATCH` |
| `preferred_characters` | string | No | `latin` | `latin` or `non_latin`: which script to return for names and addresses on documents that print both |
| `save_api_request` | boolean | No | `true` | `true`: store the call as a session (see below). `false`: store nothing |
| `vendor_data` | string | No | - | Your identifier for the user, echoed back and stored on the session |
| `metadata` | JSON object | No | - | Send as a JSON-encoded string field (e.g. `{"flow":"onboarding"}`); echoed back and stored on the session |

Action fields accept only `DECLINE` or `NO_ACTION`; `REVIEW` returns `400`. `minimum_age` is accepted but not applied by this endpoint: enforce age rules from the returned `date_of_birth` / `age`, or use a workflow with age restrictions.

**`save_api_request=true` (default):** the call is stored as an API session, visible in the Business Console. `request_id` is a real session id usable with `GET /v3/session/{sessionId}/decision/`, the cropped images come back as short-lived media URLs, and a `status.updated` webhook is sent to your webhook destinations. **`false`:** nothing is stored, `request_id` is a one-off UUID, and `portrait_image`, `front_image` and `back_image` come back inline as base64 JPEG strings.

### Example

```python
import json
import requests

with open("front.jpg", "rb") as front, open("back.jpg", "rb") as back:
    response = requests.post(
        "https://verification.didit.me/v3/id-verification/",
        headers={"x-api-key": "YOUR_API_KEY"},
        files={
            "front_image": ("front.jpg", front, "image/jpeg"),
            "back_image": ("back.jpg", back, "image/jpeg"),
        },
        data={
            "vendor_data": "user-123",
            "perform_document_liveness": "true",
            "metadata": json.dumps({"flow": "onboarding"}),
        },
        timeout=120,
    )

if response.status_code != 200:
    raise SystemExit(f"{response.status_code}: {response.text}")
id_v = response.json()["id_verification"]
print(id_v["status"], id_v.get("full_name"), [w["risk"] for w in id_v["warnings"]])
```

```typescript
const formData = new FormData();
formData.append("front_image", frontImageFile);
formData.append("back_image", backImageFile);
formData.append("vendor_data", "user-123");
formData.append("metadata", JSON.stringify({ flow: "onboarding" }));

const response = await fetch("https://verification.didit.me/v3/id-verification/", {
  method: "POST",
  headers: { "x-api-key": "YOUR_API_KEY" },
  body: formData,
});
const body = await response.json();
console.log(body.id_verification.status, body.id_verification.warnings.map((w) => w.risk));
```

### Response (200 OK)

Images are media URLs here because `save_api_request` was `true`.

```json
{
  "request_id": "11111111-2222-3333-4444-555555555555",
  "id_verification": {
    "status": "Approved",
    "document_type": "Identity Card",
    "document_subtype": "ID_CARD_GENERIC",
    "document_number": "YZA123456",
    "personal_number": "X9876543L",
    "portrait_image": "https://<media-host>/ocr/11111111-2222-3333-4444-555555555555-portrait_image.jpg?signature=...",
    "front_image": "https://<media-host>/ocr/11111111-2222-3333-4444-555555555555-front_image.jpg?signature=...",
    "back_image": "https://<media-host>/ocr/11111111-2222-3333-4444-555555555555-back_image.jpg?signature=...",
    "front_image_camera_front": null,
    "back_image_camera_front": null,
    "front_image_camera_front_face_match_score": null,
    "back_image_camera_front_face_match_score": null,
    "front_image_quality_score": {
      "focus_score": 78.0,
      "brightness_score": 83.2,
      "brightness_issue": "ok",
      "is_document_fully_visible": true,
      "resolution_score": 40.7,
      "overall_score": 70.2
    },
    "back_image_quality_score": null,
    "date_of_birth": "1985-03-15",
    "age": 41,
    "expiration_date": "2030-08-21",
    "date_of_issue": "2020-08-21",
    "issuing_state": "ESP",
    "issuing_state_name": "Spain",
    "first_name": "Elena",
    "last_name": "Martinez Sanchez",
    "full_name": "Elena Martinez Sanchez",
    "gender": "F",
    "address": "Calle Mayor 10, Madrid",
    "formatted_address": "Calle Mayor 10, 28013 Madrid, Spain",
    "place_of_birth": "Valencia",
    "marital_status": "UNKNOWN",
    "nationality": "ESP",
    "extra_fields": {"first_surname": "Martinez", "second_surname": "Sanchez"},
    "mrz": {
      "surname": "MARTINEZ SANCHEZ",
      "name": "ELENA",
      "country": "ESP",
      "nationality": "ESP",
      "birth_date": "850315",
      "expiry_date": "300821",
      "sex": "F",
      "document_type": "ID",
      "document_number": "YZA123456",
      "personal_number": "X9876543L",
      "mrz_type": "TD1",
      "warnings": [],
      "errors": []
    },
    "parsed_address": {
      "street_1": "Calle Mayor 10",
      "street_2": null,
      "city": "Madrid",
      "region": "Comunidad de Madrid",
      "postal_code": "28013",
      "country": "ES",
      "formatted_address": "Calle Mayor 10, 28013 Madrid, Spain",
      "is_verified": true
    },
    "warnings": [],
    "barcodes": []
  },
  "vendor_data": "user-123",
  "metadata": {"flow": "onboarding"},
  "created_at": "2026-06-12T02:21:56.013573+00:00"
}
```

A declined result has the same shape, with `"status": "Declined"` and the reasons in `warnings`, for example:

```json
{
  "risk": "DOCUMENT_EXPIRED",
  "feature": "ID_VERIFICATION",
  "additional_data": null,
  "log_type": "error",
  "short_description": "Document expired",
  "long_description": "The document's expiration date has passed, rendering it no longer valid for use."
}
```

### Status Values

| Status | Meaning |
|---|---|
| `"Approved"` | No warning resolved to a decline |
| `"Declined"` | At least one warning has `log_type: "error"` (see `warnings`) |

This endpoint never returns `In Review`. A readable but problematic document still returns HTTP `200` with `Declined`: always check `id_verification.status`, not only the HTTP code.

### Error Responses

| Code | Meaning | Action |
|---|---|---|
| `400` | Invalid request | Read the field errors in the response body |
| `400` | `{"error": "COULD_NOT_RECOGNIZE_DOCUMENT"}` | No document found in the image: retake with all four corners visible |
| `400` | `{"detail": "The PDF is encrypted..."}` or `{"detail": "The PDF password is incorrect..."}` | Send `front_image_password` / `back_image_password`, or a photo |
| `400` | `{"error": "Failed to convert front image PDF."}` (or back) | Send an image or a valid PDF |
| `401` | The API key has expired | Rotate it or create a new key in **Developers > API keys** |
| `403` | Missing, wrong or revoked API key; a scoped key without access to this endpoint; a request from outside the key's IP allowlist; or not enough credits | Read the message in `detail` or `error`: fix the `x-api-key` header or the key's access, or top up |
| `429` | Rate limit: 300 POST/PATCH/DELETE and 600 GET requests a minute per key | Wait the `Retry-After` seconds, then retry |

The credit check runs before the images are processed: an empty balance returns `403` with `{"error": "You don't have enough credits to perform this request. ..."}`.

---

## Response Field Reference

All fields are inside `id_verification` unless noted.

| Field | Type | Description |
|---|---|---|
| `request_id` (top level) | uuid | Session id when `save_api_request=true`; otherwise a one-off UUID |
| `status` | string | `"Approved"` or `"Declined"` |
| `document_type` | string or null | `"Passport"`, `"Identity Card"`, `"Driver's License"`, `"Residence Permit"`, `"Health Insurance Card"`, `"Tax Card"`; `null` when the document could not be classified |
| `document_subtype` | string or null | Finer subtype, e.g. `ID_CARD_GENERIC`, `EPASSPORT` |
| `document_number`, `personal_number` | string or null | Document number and secondary personal/national number |
| `first_name`, `last_name`, `full_name` | string or null | Holder names |
| `date_of_birth`, `expiration_date`, `date_of_issue` | string or null | `YYYY-MM-DD` |
| `age` | integer or null | Age computed from `date_of_birth` |
| `gender` | string or null | `"M"`, `"F"` or `null` |
| `nationality`, `issuing_state` | string or null | ISO 3166-1 alpha-3; `issuing_state_name` is the country name |
| `address`, `formatted_address` | string or null | Address as printed, and its geocoded form |
| `parsed_address` | object or null | `street_1`, `street_2`, `city`, `region`, `postal_code`, `country` (alpha-2), `formatted_address`, `is_verified`, `document_location`, `label`, `category` |
| `place_of_birth`, `marital_status` | string or null | `marital_status` is `UNKNOWN` unless printed |
| `extra_fields` | object or null | Document-specific extras (e.g. `first_surname`, `second_surname`) |
| `mrz` | object | Parsed MRZ: `surname`, `name`, `country`, `nationality`, `birth_date` / `expiry_date` (raw `YYMMDD`), `sex`, `document_type`, `document_number`, `personal_number`, `optional_data`, check digits, `mrz_type` (`TD1`/`TD2`/`TD3`), `mrz_string`, `errors`, `warnings`. `{}` when the document has no MRZ or it could not be read |
| `barcodes` | array | Decoded barcodes: `type` (e.g. `PDF417`, `QR_CODE`), `data`, `data_raw`, `side`, `position` |
| `portrait_image`, `front_image`, `back_image` | string or null | Media URL (saved) or base64 JPEG (`save_api_request=false`); `back_image` is `null` without a back upload |
| `front_image_quality_score`, `back_image_quality_score` | object or null | `focus_score`, `brightness_score`, `brightness_issue`, `is_document_fully_visible`, `resolution_score`, `overall_score` (0-100) |
| `front_image_camera_front`, `back_image_camera_front` and their `*_face_match_score` | null | Always `null` on this endpoint (filled only in hosted sessions) |
| `warnings` | array | `{risk, feature, additional_data, log_type, short_description, long_description}`; `log_type` is `error` (declines) or `information` |
| `vendor_data`, `metadata`, `created_at` (top level) | | Echo of your values and the response timestamp |

---

## Warning Tags

Only `DECLINE` or `NO_ACTION` exist on this endpoint: a warning is either `log_type: "error"` (status becomes `Declined`) or `log_type: "information"` (reported, no effect on status).

### Always decline

| Tag | Description |
|---|---|
| `DOCUMENT_EXPIRED` | Expiration date is in the past |
| `SCREEN_CAPTURE_DETECTED` | Photo of a screen, not the physical document (only with `perform_document_liveness=true`) |
| `PRINTED_COPY_DETECTED` | Printed copy, not the original (only with `perform_document_liveness=true`) |
| `PORTRAIT_MANIPULATION_DETECTED` | Portrait replaced or altered (only with `perform_document_liveness=true`) |
| `PUBLIC_DOCUMENT_IMAGE_DETECTED` | Image matches a known public internet document image (specimen, press or stock photo) |
| `NAME_NOT_DETECTED` | First and/or last name could not be read |
| `DATE_OF_BIRTH_NOT_DETECTED` | Date of birth could not be read on a document that has one |
| `DOCUMENT_NUMBER_NOT_DETECTED` | Neither a document number nor a personal number could be read |
| `COULD_NOT_DETECT_DOCUMENT_TYPE` | Nothing could be read from the upload; comes with `PORTRAIT_IMAGE_NOT_DETECTED` when no portrait was found either |

### Configurable per request

| Request parameter (default) | Tags |
|---|---|
| `invalid_mrz_action` (`DECLINE`) | `MRZ_VALIDATION_FAILED` (MRZ check digits or format failed). A missing MRZ raises no warning here |
| `inconsistent_data_action` (`DECLINE`) | `DATA_INCONSISTENT` (front and back disagree), `MRZ_AND_DATA_EXTRACTED_FROM_OCR_NOT_SAME` (visual zone disagrees with the MRZ) |
| `critical_field_occlusion_action` (`DECLINE`) | `CRITICAL_FIELD_OCCLUSION_DETECTED`: an identity number, name, date of birth or expiry date was physically covered. `additional_data.covered_fields` lists them; the matching `*_NOT_DETECTED` warning usually follows |
| `expiration_date_not_detected_action` (`NO_ACTION`) | `EXPIRATION_DATE_NOT_DETECTED` |
| `document_or_personal_number_format_mismatch_action` (`NO_ACTION`) | `DOCUMENT_NUMBER_FORMAT_MISMATCH`, `PERSONAL_NUMBER_FORMAT_MISMATCH` (`additional_data` has `expected_format`, `extracted_value`) |

### Informational on this endpoint (never decline)

| Tag | Description |
|---|---|
| `POSSIBLE_DUPLICATED_USER` | Another document in your application has the same date of birth, issuing country and a very similar name under a different `vendor_data`. `additional_data.duplicated_session_id` |
| `ID_DOCUMENT_IN_BLOCKLIST` | The document matches your document blocklist. Informational here (it auto-declines in workflows): check for it and decide yourself |
| `ID_DOCUMENT_IN_ALLOWLIST` | The document number is on your allowlist |
| `DOCUMENT_SIDES_MISMATCH` | Front and back do not belong to the same document |
| `UNPARSED_ADDRESS` | The document has an address field that could not be parsed or geolocated |

Workflow-only tags (never produced here): `DOCUMENT_NOT_SUPPORTED_FOR_APPLICATION`, `MINIMUM_AGE_NOT_MET`, `MRZ_NOT_DETECTED`, `INVALID_DATE`, the `*_MISMATCH_WITH_PROVIDED` family (needs `expected_details` on a session) and the front-camera selfie tags.

---

## Digital ID Wallets (standalone)

Verify a person through a national or bank digital ID they already hold, from your own app, with no workflow. The user always authenticates in the wallet and approves sharing; you cannot verify someone from their identifier alone. Endpoints are v3 only.

**Wallets available in production** (per the docs; always confirm with the catalog call, which reports availability for your application and environment):

| Wallet | Start endpoint | Countries | Interaction | List price per verified sign-in |
|---|---|---|---|---|
| MitID | `POST /v3/id-verification/wallets/mitid/` | DNK | redirect | $0.25 |
| BankID Sweden | `POST /v3/id-verification/wallets/bankid-se/` | SWE | redirect | $0.20 |
| iDIN | `POST /v3/id-verification/wallets/idin/` | NLD | redirect | $0.85 (full identification) |
| Finnish Trust Network | `POST /v3/id-verification/wallets/ftn/` | FIN | redirect | $0.25 |
| Smart-ID | `POST /v3/id-verification/wallets/smart-id/` | EST, LVA, LTU, BEL | in app | see [pricing](https://docs.didit.me/getting-started/pricing#digital-id-wallet-pricing) |
| Mobile-ID | `POST /v3/id-verification/wallets/mobile-id/` | EST, LTU | in app | see [pricing](https://docs.didit.me/getting-started/pricing#digital-id-wallet-pricing) |

Other wallets have start endpoints but are **Coming soon**: they fail closed with `403` `wallet_unavailable`. Billing: once per request, only when the identity is verified; cancelled, expired or failed sign-ins are free, and the 500 free document checks do not apply.

| Operation | Endpoint |
|---|---|
| Catalog: every wallet with `id`, `name`, `path`, `countries`, `interaction`, `required_fields`, `available` | `GET /v3/id-verification/wallets/` |
| Start a sign-in | `POST /v3/id-verification/wallets/<wallet>/` (the catalog `path`) |
| Read status and result | `GET /v3/id-verification/wallets/verifications/{request_id}/` |
| Ask the wallet for a phone approval (Smart-ID, Mobile-ID) | `POST /v3/id-verification/wallets/verifications/{request_id}/poll/` |
| Cancel a pending sign-in (never billed) | `POST /v3/id-verification/wallets/verifications/{request_id}/cancel/` |

### Start request

| Field | Wallets | Required | Description |
|---|---|---|---|
| `return_url` | redirect wallets | **Yes** | HTTPS URL the browser returns to, with `request_id` and `result` appended. Its host must be registered first (below) |
| `device` | redirect wallets | No | `same_device` (default) or `cross_device` (e.g. a QR code scanned with the phone) |
| `country` | all | Yes for Smart-ID and Mobile-ID | ISO 3166-1 alpha-3; defaults to the only country of single-country wallets |
| `personal_code` | Smart-ID, Mobile-ID | **Yes** | The user's national personal identification code (digits and hyphens, 6 to 20 characters). Never collect the PIN |
| `phone_number` | Mobile-ID | **Yes** | E.164 number registered with Mobile-ID in that country |
| `vendor_data` | all | No | Your reference, up to 2,000 UTF-8 bytes |
| `metadata` | all | No | JSON object returned with the result and webhook |
| `sandbox_scenario` | all | No | Sandbox applications only: `wallet_cancelled`, `wallet_timeout` or `wallet_provider_error`; anything else verifies. Rejected on live applications |

Header `Idempotency-Key` (optional, max 255 characters): use a new key per attempt and resend the same key on retries; the same key with another wallet or body returns `409` `idempotency_key_reused`.

**Register the return host once** (redirect wallets): `PATCH https://verification.didit.me/v3/webhook/` with `{"allowed_return_hosts": ["app.example.com"]}`. Bare hostnames only (no scheme, path or wildcard), up to 20; the list is replaced on every update, and `GET /v3/webhook/` shows it. Your white-label domain is always allowed.

### Response (201 on start, 200 on read, poll and cancel)

```json
{
  "request_id": "00000000-0000-4000-8000-000000000001",
  "wallet_verification": {
    "wallet": {"id": "ftn", "name": "Finnish Trust Network", "issuing_authority": "Finnish banks and mobile operators (FTN)"},
    "country": "FIN",
    "status": "Not Finished",
    "outcome": "pending",
    "error": null,
    "interaction": "redirect",
    "simulated": false,
    "expires_at": "2026-01-01T10:10:00Z",
    "next_action": {"type": "redirect", "url": "https://wallet.example.com/authorize"},
    "identity": null,
    "attributes": null,
    "level_of_assurance": null,
    "verified_at": null,
    "signature_valid": null,
    "credential_type": "person_identification"
  },
  "vendor_data": "user-123",
  "metadata": null,
  "created_at": "2026-01-01T10:00:00Z"
}
```

- `next_action.type`: `redirect` (send the browser to `url`) or `confirm_in_app` (show `verification_code`, the 4-digit code the wallet app also shows; the user confirms in the app; poll every `poll_interval_seconds`). Didit also polls in the background, so the webhook fires even if you stop polling.
- `outcome`: `pending`, `verified`, `cancelled`, `timeout`, `failed`. `status` is `Not Finished`, then `Approved` (verified) or `Declined`.
- `identity` once verified: `full_name`, `first_name`, `last_name`, `date_of_birth`, `nationality` (only when the wallet asserts it), `issuing_state`. `attributes` holds the wallet's own claims and varies by wallet.
- **Use the identity only when `outcome` is `verified` and `simulated` is `false`.** Never trust the `result` query parameter on `return_url`; read the result from your backend.
- The `status.updated` webhook carries `session_id` equal to the `request_id`; the identity appears in `decision.id_verifications` with `verification_method: "wallet"`.

### Wallet errors

| Code | `error` | Meaning |
|---|---|---|
| `400` | field errors, `return_url_invalid`, `return_url_not_allowed`, `invalid_personal_code`, `invalid_phone_number`, `idempotency_key_invalid` | Fix the request; register the `return_url` host |
| `403` | `{"detail": ...}`, `wallet_unavailable`, `insufficient_credits` | Bad key, wallet not live for you, or top up |
| `404` | `not_found` | No wallet verification of this application has that `request_id` |
| `409` | `idempotency_key_reused`, `idempotency_key_in_progress`, `verification_in_progress` (cancel while the user is completing) | Use a new key, or wait `Retry-After` seconds |
| `502` | `wallet_provider_unavailable` | The wallet could not start; nothing was created or billed |
| `503` | `wallet_not_configured` | This environment cannot reach the wallet |

```python
import uuid
import requests

BASE = "https://verification.didit.me/v3/id-verification/wallets"
headers = {"x-api-key": "YOUR_API_KEY"}

catalog = requests.get(f"{BASE}/", headers=headers, timeout=30).json()
live = {w["id"]: w for w in catalog["wallets"] if w["available"]}

if "ftn" in live:
    start = requests.post(
        f"{BASE}/ftn/",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"return_url": "https://app.example.com/identity/complete", "vendor_data": "user-123"},
        timeout=30,
    ).json()
    request_id = start["request_id"]
    print("Send the browser to:", start["wallet_verification"]["next_action"]["url"])

    # After the user returns (or on the webhook), read the result server-side
    result = requests.get(f"{BASE}/verifications/{request_id}/", headers=headers, timeout=30).json()
    wv = result["wallet_verification"]
    if wv["outcome"] == "verified" and not wv["simulated"]:
        print("Verified:", wv["identity"]["full_name"], wv["identity"]["date_of_birth"])
```

**API Reference:** https://docs.didit.me/standalone-apis/digital-id-wallets

---

## Workflow-Only ID Methods

These are not available on the standalone endpoints; use a workflow and session (see the **didit-kyc-onboarding** skill):

- **NFC chip reading:** workflow feature `NFC`, placed after `OCR`. The chip is read by the native iOS/Android SDK during a session; web browsers skip it. $0.15 per completed read.
- **Non-document lookup and wallets inside a workflow:** set `config.methods` per country on the `OCR` feature (document capture, lookup against a government register or other authoritative source, digital ID wallets, with fallback rules). See https://docs.didit.me/management-api/workflows/feature-configs and https://docs.didit.me/core-technology/id-verification/non-doc-lookup.

---

## Common Workflows

### Basic ID Verification

```
1. POST /v3/id-verification/ -> front_image (+ back_image if the document has a back)
2. If 400 COULD_NOT_RECOGNIZE_DOCUMENT -> ask for a new photo with all corners visible
3. If "Approved" -> use first_name, last_name, date_of_birth, document_number, issuing_state
   If "Declined" -> read warnings with log_type "error":
     DOCUMENT_EXPIRED -> ask for a valid document
     SCREEN_CAPTURE_DETECTED / PRINTED_COPY_DETECTED -> ask for a photo of the physical document
     MRZ_VALIDATION_FAILED / NAME_NOT_DETECTED -> ask for a sharper image (and the back side)
4. Check informational warnings too: ID_DOCUMENT_IN_BLOCKLIST, POSSIBLE_DUPLICATED_USER
```

### Full Identity Verification Pipeline (standalone)

```
1. POST /v3/id-verification/ -> verify document, keep portrait_image
2. POST /v3/passive-liveness/ -> verify a real person took the selfie
3. POST /v3/face-match/ -> compare selfie to the document portrait
4. POST /v3/aml/ -> screen the extracted name, date of birth and nationality; convert nationality
   from alpha-3 (ESP) to alpha-2 (ES) first, or /v3/aml/ returns 400
5. All Approved -> verified identity
```

For a hosted flow that captures the document and selfie for you, use a workflow session (**didit-kyc-onboarding** skill).

---

## Utility Scripts

```bash
export DIDIT_API_KEY="your_api_key"

python scripts/verify_id.py front.jpg
python scripts/verify_id.py front.jpg back.jpg --vendor-data user-123
python scripts/verify_id.py scan.pdf --front-password secret --no-document-liveness
python scripts/verify_id.py front.jpg back.jpg --preferred-characters non_latin --no-save
python scripts/verify_id.py front.jpg --format-mismatch-action DECLINE --metadata '{"flow": "onboarding"}'
```
