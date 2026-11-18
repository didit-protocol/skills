---
name: didit-proof-of-address
description: >
  Integrate the Didit Proof of Address standalone API (POST /v3/poa/) to verify address
  documents. Use when the user wants to verify a proof of address, validate a utility bill,
  bank statement or government letter, extract and geocode the address on a document,
  enforce a maximum document age, cross-check a document against an expected name, address
  or country, detect edited PDFs, or perform PoA checks using Didit. Returns Approved or
  Declined with itemized warnings, the parsed address with coordinates, issuer, dates,
  holder name, bank fields and QR/barcode data.
version: 1.3.0
metadata:
  openclaw:
    requires:
      env:
        - DIDIT_API_KEY
    primaryEnv: DIDIT_API_KEY
    emoji: "🏠"
    homepage: https://docs.didit.me
---

# Didit Proof of Address API

## Overview

Verifies an address document (image or PDF) in one call. The document is classified (type and subtype), the issuer, dates, holder name and address are extracted, the address is parsed and geocoded, PDF/EXIF forensics look for tampering, and optional `expected_*` values are cross-checked. The answer is `Approved` or `Declined` with a `warnings` list explaining every issue found.

**Pricing:** $0.20 per call (every `200` response is billed, `Approved` or `Declined`; standalone calls have no free tier). These are the list prices until 1 November 2026, when Didit pricing changes and the 500 free checks a month become $10 of free credit a month. Check [didit.me/pricing](https://didit.me/pricing) for current prices.

**Key constraints:**
- Formats: **JPG, JPEG, PNG, TIFF, PDF, WEBP**. Multi-page PDFs are supported. Encrypted PDFs need `document_password`.
- Maximum upload size: **50 MB** for a PDF, **6 MB** for an image (larger files return `400`)
- Latency: typically **5-15 s**, multi-page PDFs up to **~30 s**. Use a client timeout of **at least 45 s** and do not retry before the call completes.
- Maximum document age, by type (defaults): **3 months** for utility bills and bank statements, **12 months** for government-issued and other documents. A month counts as 30 days. Change it per request with `poa_document_age_months` (1-120, or -1 for no age check). A printed expiry date that has passed also expires the document.
- Capture guidance: full color, all corners and all pages visible, no digital editing.

**Capabilities:** document classification, LLM-based extraction, address parsing and geocoding (latitude/longitude), language detection, issue-date and age checks, name/address/country cross-checks, PDF and EXIF tamper forensics, bank detail extraction, QR code and barcode detection.

**Accepted document types (`document_type`):**

| Type | Examples (`document_subtype`) |
|---|---|
| `UTILITY_BILL` | Electricity, water, gas, internet, phone, combined utilities bill |
| `BANK_STATEMENT` | Account statement, credit card statement, mortgage or loan statement |
| `GOVERNMENT_ISSUED_DOCUMENT` | Tax assessment, residency certificate, voter registration card |
| `OTHER_POA_DOCUMENT` | Lease or rental agreement, insurance policy, employer letter |

A document that cannot be classified gets `document_type: "UNKNOWN"` and is declined with `INVALID_DOCUMENT_TYPE`.

**API Reference:** https://docs.didit.me/standalone-apis/proof-of-address
**Feature Guide:** https://docs.didit.me/core-technology/proof-of-address/overview
**Warnings:** https://docs.didit.me/core-technology/proof-of-address/warnings-proof-of-address

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
POST https://verification.didit.me/v3/poa/
```

### Headers

| Header | Value | Required |
|---|---|---|
| `x-api-key` | Your API key | **Yes** |
| `Content-Type` | `multipart/form-data` | **Yes** |

### Request Parameters (multipart/form-data)

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `document` | file | **Yes** | - | The PoA document: `tiff`, `jpg`, `jpeg`, `png`, `pdf` or `webp`. PDF max 50 MB, image max 6 MB |
| `document_password` | string | No | - | Password of an encrypted PDF. Missing or wrong password returns `400` |
| `expected_address` | string | No | - | Address to check. It is geocoded and compared with the document address; a mismatch, or an expected address that cannot be verified, adds `ADDRESS_MISMATCH_WITH_PROVIDED` |
| `expected_country` | string | No | - | ISO 3166-1 alpha-2 or alpha-3 code (`ES` or `ESP`). A different document country adds `POA_COUNTRY_MISMATCH_WITH_PROVIDED` |
| `expected_first_name` | string | No | - | First name to check against `name_on_document` (fuzzy, transliteration-aware). Send it with `expected_last_name`: the name check runs only when both are set |
| `expected_last_name` | string | No | - | Last name for the same check. A score below 86 (0-100) adds `NAME_MISMATCH_WITH_PROVIDED` |
| `poa_languages_allowed` | string | No | all 51 supported languages | Comma-separated ISO 639-1 codes, e.g. `en,es`. Another language adds `UNSUPPORTED_DOCUMENT_LANGUAGE`; an unknown code returns `400` with the supported list |
| `poa_document_age_months` | string | No | `utility_bill:3,bank_statement:3,government_issued_document:12,other_poa_document:12` | Maximum age per type as `key:value` pairs. Values `1`-`120`, or `-1` for no age check. **When you send it, list every type you accept:** omitted types count as not accepted (informational `POA_DOCUMENT_NOT_SUPPORTED_FOR_APPLICATION`) and get no age check |
| `poa_address_mismatch_action` | `DECLINE` / `NO_ACTION` | No | `DECLINE` | Applies to `ADDRESS_MISMATCH_WITH_PROVIDED`, `NAME_MISMATCH_WITH_PROVIDED` and `POA_COUNTRY_MISMATCH_WITH_PROVIDED` |
| `poa_document_issues_action` | `DECLINE` / `NO_ACTION` | No | `DECLINE` | Applies to `DOCUMENT_METADATA_MISMATCH` |
| `poa_document_authenticity_action` | `DECLINE` / `NO_ACTION` | No | `DECLINE` | Applies to `SUSPECTED_DOCUMENT_MANIPULATION` |
| `poa_unsupported_language_action` | `DECLINE` / `NO_ACTION` | No | `DECLINE` | Applies to `UNSUPPORTED_DOCUMENT_LANGUAGE` |
| `poa_issuer_not_identified_action` | `DECLINE` / `NO_ACTION` | No | `DECLINE` | Applies to `ISSUER_NOT_IDENTIFIED` |
| `poa_name_mismatch_action` | `DECLINE` / `NO_ACTION` | No | `DECLINE` | Accepted but not applied: name mismatches follow `poa_address_mismatch_action` |
| `save_api_request` | boolean | No | `true` | `true`: stored as a session (Business Console, `GET /v3/session/{sessionId}/decision/` with the returned `request_id`, `status.updated` webhook). `false`: nothing is stored and `request_id` cannot be looked up |
| `vendor_data` | string | No | - | Your identifier for the user, echoed back and stored on the session |
| `metadata` | JSON string | No | - | JSON object sent as a string field, e.g. `{"flow":"onboarding"}`. Echoed back and stored |

**Sandbox:** sandbox API keys skip processing and billing. After request validation (bad input still returns `400`) they get a fixed `Approved` mock response and nothing is stored.

### Example

```python
import requests

with open("bill.pdf", "rb") as f:
    response = requests.post(
        "https://verification.didit.me/v3/poa/",
        headers={"x-api-key": "YOUR_API_KEY"},
        files={"document": ("bill.pdf", f, "application/pdf")},
        data={
            "expected_first_name": "Jane",
            "expected_last_name": "Doe",
            "expected_country": "ESP",
            "poa_languages_allowed": "en,es",
            "vendor_data": "user-123",
        },
        timeout=60,  # extraction takes 5-15 s, up to ~30 s for multi-page PDFs
    )
response.raise_for_status()
poa = response.json()["poa"]
print(poa["status"], poa["poa_formatted_address"], [w["risk"] for w in poa["warnings"]])
```

```typescript
const formData = new FormData();
formData.append("document", documentFile); // File or Blob
formData.append("expected_first_name", "Jane");
formData.append("expected_last_name", "Doe");
formData.append("expected_country", "ESP");
formData.append("vendor_data", "user-123");

const response = await fetch("https://verification.didit.me/v3/poa/", {
  method: "POST",
  headers: { "x-api-key": "YOUR_API_KEY" },
  body: formData,
  signal: AbortSignal.timeout(60_000),
});
if (!response.ok) throw new Error(`PoA failed: ${response.status} ${await response.text()}`);
const { poa } = await response.json();
console.log(poa.status, poa.warnings.map((w: { risk: string }) => w.risk));
```

### Response (200 OK)

```json
{
  "request_id": "4b523a8d-ed32-45e4-8aa8-a89eda459d88",
  "poa": {
    "issuing_state": "ESP",
    "document_type": "UTILITY_BILL",
    "document_subtype": "ELECTRICITY_BILL",
    "document_language": "es",
    "issuer": "Acme Energy",
    "issue_date": "2026-09-15",
    "expiration_date": null,
    "poa_address": "C/ Mayor 10, 2B, 28013 Madrid",
    "poa_formatted_address": "Calle Mayor 10, 2B, 28013 Madrid, Spain",
    "poa_parsed_address": {
      "street_1": "Calle Mayor 10",
      "street_2": "2B",
      "city": "Madrid",
      "region": "Comunidad de Madrid",
      "country": "ES",
      "postal_code": "28013",
      "document_location": {"latitude": 40.4155, "longitude": -3.7074}
    },
    "expected_details_address": null,
    "expected_details_formatted_address": null,
    "expected_details_parsed_address": null,
    "name_on_document": "JANE DOE",
    "extra_fields": {
      "bank_account_number": null,
      "bank_iban": null,
      "bank_sort_code": null,
      "bank_routing_number": null,
      "bank_swift_bic": null,
      "bank_branch_name": null,
      "bank_branch_address": null,
      "document_phone_number": null,
      "additional_names": []
    },
    "detected_codes": [],
    "status": "Approved",
    "warnings": []
  },
  "vendor_data": "user-123",
  "metadata": null,
  "created_at": "2026-10-12T09:30:00.000000+00:00"
}
```

A declined document still returns `200`. Example warning for a bill older than the allowed age:

```json
{
  "risk": "POA_DOCUMENT_EXPIRED",
  "feature": "PROOF_OF_ADDRESS",
  "additional_data": {
    "expiration_reason": "age_window",
    "max_age_months": 3,
    "document_subtype": "ELECTRICITY_BILL",
    "document_type": "UTILITY_BILL",
    "issue_date": "2026-02-10"
  },
  "log_type": "error",
  "short_description": "Document expired",
  "long_description": "The submitted document is older than the maximum accepted age of 3 months from its issue date, which exceeds the acceptable time period for validity."
}
```

The response does not include the document file or the forensic metadata. With `save_api_request=true`, `GET /v3/session/{request_id}/decision/` returns them in `poa_verifications[]` (`document_file` is a temporary URL that expires after about 4 hours).

### Status Values & Handling

| Status | Meaning | Action |
|---|---|---|
| `"Approved"` | No warning resolved to a decline | Use the parsed address; `information` warnings may still be present |
| `"Declined"` | At least one warning has `log_type: "error"` | Read `warnings[].risk` and ask for another document or fix the `expected_*` input |

This endpoint never returns `In Review` or `Not Finished`. Always read `poa.status` and `poa.warnings`, not just the HTTP code.

### Error Responses

| Code | Meaning | Action |
|---|---|---|
| `400` | Invalid request | Read the field errors in the response body |
| `401` | The API key has expired | Rotate it or create a new key in **Developers > API keys** |
| `403` | Missing, wrong or revoked API key; a scoped key without access to this endpoint; a request from outside the key's IP allowlist; or not enough credits | Read the message in `detail` or `error`: fix the `x-api-key` header or the key's access, or top up |
| `429` | Rate limit: 300 POST/PATCH/DELETE and 600 GET requests a minute per key | Wait the `Retry-After` seconds, then retry |

`400` causes on this endpoint: no `document`, an extension outside the allowed list, a PDF over 50 MB or an image over 6 MB, an encrypted PDF without (or with a wrong) `document_password`, an unknown code in `poa_languages_allowed`, a bad `poa_document_age_months` pair, or a document the extraction cannot process (`{"error": ["Error extracting POA information"]}`). The credit check runs before any processing; a not-enough-credits `403` body is `{"error": "You don't have enough credits to perform this request. ..."}`.

---

## Response Field Reference

| Field | Type | Description |
|---|---|---|
| `request_id` | uuid | Session id when `save_api_request=true`; otherwise a one-off correlation id |
| `poa.status` | string | `"Approved"` or `"Declined"` |
| `poa.issuing_state` | string/null | Country of the document, usually ISO 3166-1 alpha-3 (`ESP`) |
| `poa.document_type` | string | `UTILITY_BILL`, `BANK_STATEMENT`, `GOVERNMENT_ISSUED_DOCUMENT`, `OTHER_POA_DOCUMENT` or `UNKNOWN` |
| `poa.document_subtype` | string | e.g. `ELECTRICITY_BILL`, `WATER_BILL`, `ACCOUNT_STATEMENT`, `CREDIT_CARD_STATEMENT`, `TAX_ASSESSMENT`; `UNKNOWN` when not determined |
| `poa.document_language` | string/null | ISO 639-1 code |
| `poa.issuer` | string/null | Issuing company or organization; `null` adds `ISSUER_NOT_IDENTIFIED` |
| `poa.issue_date` | date/null | `YYYY-MM-DD`; `null` declines with `UNABLE_TO_EXTRACT_ISSUE_DATE` |
| `poa.expiration_date` | date/null | Expiry date printed on the document, if any |
| `poa.poa_address` | string/null | Address as printed; `null` declines with `MISSING_ADDRESS_INFORMATION` |
| `poa.poa_formatted_address` | string/null | Geocoded, normalized address |
| `poa.poa_parsed_address` | object/null | `{street_1, street_2, city, region, country, postal_code, document_location}`; `country` is ISO alpha-2 |
| `poa.poa_parsed_address.document_location` | object/null | `{latitude, longitude}` of the document address |
| `poa.expected_details_address` | string/null | Echo of `expected_address` |
| `poa.expected_details_formatted_address` | string/null | Geocoded `expected_address` |
| `poa.expected_details_parsed_address` | object/null | Geocoding result for `expected_address`, including an `is_verified` flag |
| `poa.name_on_document` | string/null | Primary holder name; `null` declines with `POA_NAME_NOT_DETECTED` |
| `poa.extra_fields` | object | `bank_account_number`, `bank_iban`, `bank_sort_code`, `bank_routing_number`, `bank_swift_bic`, `bank_branch_name`, `bank_branch_address`, `document_phone_number` (null when absent), `additional_names` (array) |
| `poa.detected_codes` | array | QR codes and barcodes: `type`, `page_number`, `position`, `x`, `y`, `width`, `height`, `page_width`, `page_height`, `raw_payload` (base64), `parsed_payload` (null when undecodable) |
| `poa.warnings` | array | `{risk, feature, additional_data, log_type, short_description, long_description}`; `feature` is always `PROOF_OF_ADDRESS` |
| `vendor_data` | string/null | Echo of your `vendor_data` |
| `metadata` | object/null | Echo of your `metadata` |
| `created_at` | string | ISO 8601 UTC timestamp |

---

## Warning Tags

`log_type` is `error` (sets `Declined`) or `information` (no effect). `warning` is never produced on this endpoint.

### Always decline

| Tag | Cause |
|---|---|
| `MISSING_ADDRESS_INFORMATION` | No address could be extracted |
| `POA_DOCUMENT_EXPIRED` | Older than the allowed age for its type, or a printed expiry date has passed. `additional_data`: `expiration_reason` (`age_window` or `printed_expiration`), `document_type`, `document_subtype`, `issue_date`, plus `max_age_months` or `expiration_date` |
| `INVALID_DOCUMENT_TYPE` | Not classifiable as a PoA document (`document_type: "UNKNOWN"`) |
| `UNABLE_TO_VALIDATE_DOCUMENT_AGE` | The age check itself failed |
| `UNABLE_TO_EXTRACT_ISSUE_DATE` | No issue date found (not configurable on this endpoint) |
| `POA_NAME_NOT_DETECTED` | No holder name found (not configurable on this endpoint) |

### Configurable (`DECLINE` by default, `NO_ACTION` makes them `information`)

| Tag | Cause | Option |
|---|---|---|
| `NAME_MISMATCH_WITH_PROVIDED` | `name_on_document` does not match `expected_first_name` + `expected_last_name` | `poa_address_mismatch_action` |
| `ADDRESS_MISMATCH_WITH_PROVIDED` | Document address differs from `expected_address`, or either address could not be verified | `poa_address_mismatch_action` |
| `POA_COUNTRY_MISMATCH_WITH_PROVIDED` | Document country differs from `expected_country`. `additional_data`: `expected_country`, `extracted_country` | `poa_address_mismatch_action` |
| `DOCUMENT_METADATA_MISMATCH` | Empty file, unreadable file metadata, or malformed EXIF dates | `poa_document_issues_action` |
| `SUSPECTED_DOCUMENT_MANIPULATION` | Forensics found edits: modified after digital signing, overlay-text manipulation, a known PDF editor, inconsistent EXIF dates or a suspicious re-export. `additional_data`: `reason`, `detection_method` | `poa_document_authenticity_action` |
| `UNSUPPORTED_DOCUMENT_LANGUAGE` | Language not in `poa_languages_allowed` | `poa_unsupported_language_action` |
| `ISSUER_NOT_IDENTIFIED` | No issuing organization found | `poa_issuer_not_identified_action` |

### Informational on this endpoint (never decline)

| Tag | Cause |
|---|---|
| `POA_DOCUMENT_NOT_SUPPORTED_FOR_APPLICATION` | The detected type was left out of `poa_document_age_months` |
| `UNPARSABLE_OR_INVALID_ADDRESS` | An address was read but could not be parsed and geocoded into a valid residential address |

`FUTURE_ISSUE_DATE`, `POOR_DOCUMENT_QUALITY`, `NAME_MISMATCH_ID_VERIFICATION`, `POA_NAME_MISMATCH_BETWEEN_DOCUMENTS` and `POA_MAX_ATTEMPTS_EXCEEDED` are never produced by this endpoint (they belong to workflow sessions). A future-dated document is not auto-declined here.

---

## Common Workflows

### Basic Address Verification

```
1. POST /v3/poa/ with the document (client timeout >= 45 s)
2. "Approved" -> store poa_formatted_address / poa_parsed_address
   "Declined" -> branch on warnings[].risk:
     POA_DOCUMENT_EXPIRED            -> ask for a more recent document
     MISSING_ADDRESS_INFORMATION     -> ask for a clearer, complete document
     INVALID_DOCUMENT_TYPE           -> ask for a utility bill, bank statement or official letter
     UNABLE_TO_EXTRACT_ISSUE_DATE    -> ask for a document with a visible issue date
     SUSPECTED_DOCUMENT_MANIPULATION -> do not accept; ask for the original file
```

### Address Plus Identity Cross-Check

Standalone calls are not linked to an ID check, so pass the data you already trust:

```
1. POST /v3/id-verification/ -> read id_verification.first_name, last_name, issuing_state
   (see the didit-id-document-verification skill)
2. POST /v3/poa/ with expected_first_name, expected_last_name, expected_country
   (and expected_address if the user typed one)
3. NAME_MISMATCH_WITH_PROVIDED / ADDRESS_MISMATCH_WITH_PROVIDED / POA_COUNTRY_MISMATCH_WITH_PROVIDED
   -> Declined by default; send poa_address_mismatch_action=NO_ACTION to only flag them
```

### Retrieve or Correct a Stored Result

```
1. Call with save_api_request=true (default); keep request_id
2. GET /v3/session/{request_id}/decision/ -> poa_verifications[] with document_file and forensics
3. To fix extracted fields after a manual review, PATCH /v3/session/{sessionId}/update-poa-data/
   (documented in the didit-verification-management skill)
```

---

## Utility Scripts

**verify_address.py**: Verify a proof of address document from the command line. Prints the JSON response, then the status, address and warning risks.

```bash
# Requires: pip install requests
export DIDIT_API_KEY="your_api_key"
python scripts/verify_address.py utility_bill.pdf
python scripts/verify_address.py bank_statement.jpg --vendor-data user-123
python scripts/verify_address.py bill.pdf --first-name Jane --last-name Doe --country ESP
python scripts/verify_address.py bill.pdf --expected-address "Calle Mayor 10, 28013 Madrid" --languages en,es
python scripts/verify_address.py bill.pdf --document-age utility_bill:6,bank_statement:6,government_issued_document:12,other_poa_document:12
python scripts/verify_address.py locked.pdf --password "pdf-password" --no-save
```
