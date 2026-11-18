---
name: didit-document-ai
description: >
  Integrate the Didit Document AI standalone API to extract the fields you define from any
  document (PDF or image). Use when the user wants to read custom data from proof of funds,
  bank statements, payslips, tax documents, invoices, contracts or source-of-wealth letters;
  get typed values (text, number, date) for their own field list; compare the name on a
  document with an expected person or company; detect tampered or edited PDFs and images;
  decode QR codes and barcodes on a document; or add a DOCUMENT_AI step to a verification
  workflow using Didit. $0.20 per document, synchronous, multipart upload.
version: 1.0.0
metadata:
  openclaw:
    requires:
      env:
        - DIDIT_API_KEY
    primaryEnv: DIDIT_API_KEY
    emoji: "📄"
    homepage: https://docs.didit.me
---

# Didit Document AI API

## Overview

Send one document and the list of fields you want read from it. Didit runs its default extraction model, returns every field typed, decodes supported QR codes and barcodes, runs PDF/EXIF forensics for manipulation, optionally compares the name on the document with the person or company you expect, and returns a status with an itemized `warnings` list.

**Key constraints:**
- `multipart/form-data` only. `document` (the file) and `fields` (one JSON-encoded array string) are required
- `fields`: 1 to 30 items, at most 16 KB. Bracket-style form keys (`fields[0][key]=...`) return `400`
- Synchronous and model-based: typically 5 to 15 seconds, multi-page PDFs up to about 30 seconds. Use a client timeout of at least 45 seconds and do not retry before the call completes
- A readable but problematic document still returns `200` with `Declined` or `In Review`: always read `document_ai.status` and `document_ai.warnings`
- Only `200` responses are billed: `400` and `403` responses cost nothing

**Use cases:** proof of funds, bank statements, payslips, source-of-wealth letters, tax documents, invoices, contracts, any document without a fixed template.

**Pricing:** $0.20 per document (billed per `200` response, when the document is processed and a status is returned; standalone calls have no free tier). These are the list prices until 1 November 2026, when Didit pricing changes and the 500 free checks a month become $10 of free credit a month. Check [didit.me/pricing](https://didit.me/pricing) for current prices.

**API Reference:** https://docs.didit.me/standalone-apis/document-ai
**Feature Guide:** https://docs.didit.me/core-technology/document-ai/overview
**Rules & Warnings:** https://docs.didit.me/core-technology/document-ai/warnings-document-ai

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
POST https://verification.didit.me/v3/document-ai/
```

### Headers

| Header | Value | Required |
|---|---|---|
| `x-api-key` | Your API key | **Yes** |
| `Content-Type` | `multipart/form-data` (set by your HTTP client) | **Yes** |

### Body (multipart/form-data)

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `document` | file | **Yes** | - | The document to read (see Accepted files) |
| `fields` | string | **Yes** | - | One JSON-encoded array of 1 to 30 field definitions, max 16 KB |
| `expected_first_name` | string | No | - | Person name to compare. Use with `expected_last_name`. Not with `expected_company_name` |
| `expected_last_name` | string | No | - | Combined with `expected_first_name` for `name_match_score` |
| `expected_company_name` | string | No | - | Company name to compare. Not with the person fields |
| `expected_company_country` | string | No | - | Exactly 2 ASCII letters (ISO 3166-1 alpha-2, e.g. `FR`); tunes company-name normalization. Requires `expected_company_name` |
| `document_ai_name_match_score_threshold` | integer | No | `80` | 0-100. A lower `name_match_score` raises `DOCUMENT_AI_NAME_MISMATCH` |
| `document_ai_unreadable_document_action` | string | No | `"REVIEW"` | `DECLINE`, `REVIEW` or `NO_ACTION` |
| `document_ai_missing_required_fields_action` | string | No | `"REVIEW"` | `DECLINE`, `REVIEW` or `NO_ACTION` |
| `document_ai_document_tampering_action` | string | No | `"DECLINE"` | `DECLINE`, `REVIEW` or `NO_ACTION` |
| `document_ai_name_mismatch_action` | string | No | `"NO_ACTION"` | `DECLINE`, `REVIEW` or `NO_ACTION` |
| `document_ai_unsupported_file_action` | string | No | `"REVIEW"` | `DECLINE`, `REVIEW` or `NO_ACTION` |
| `save_api_request` | boolean | No | `true` | `true`: store the call as an API session (visible in the Business Console under **Manual Checks**, readable with `GET /v3/session/{request_id}/decision/`). `false`: store nothing; `request_id` is a transient id. Billed either way |
| `vendor_data` | string | No | - | Your id for the user, max 2,000 bytes. Echoed back |
| `metadata` | string (JSON object) | No | - | A JSON object sent as a JSON-encoded string field, e.g. `{"flow":"onboarding"}`. Parsed and echoed back |

### `fields` items

| Key | Type | Required | Default | Description |
|---|---|---|---|---|
| `key` | string | **Yes** | - | `^[a-z0-9_]{1,64}$`, unique in the request. The key you get back in `extracted_data` |
| `name` | string | No | the `key` | Human-readable label, max 100 chars. Used in warnings (e.g. `missing_fields`) |
| `instruction` | string | No | `""` | What the model should read, max 500 chars |
| `type` | string | No | `"text"` | `text`, `number` or `date` (`YYYY-MM-DD`) |
| `required` | boolean | No | `false` | If the value cannot be read, raises `DOCUMENT_AI_MISSING_REQUIRED_FIELDS` |
| `is_full_name` | boolean | No | `false` | Marks the value compared with the expected name. At most one per request |

```json
[
  {"key": "account_holder", "name": "Account holder", "instruction": "Full name of the person or company the account belongs to", "type": "text", "required": true, "is_full_name": true},
  {"key": "balance", "name": "Closing balance", "instruction": "Closing balance as a number without the currency symbol", "type": "number", "required": true},
  {"key": "currency", "name": "Currency", "instruction": "Three-letter currency code of the balance", "type": "text"},
  {"key": "statement_date", "name": "Statement date", "instruction": "Date the statement was issued", "type": "date", "required": true}
]
```

Invalid JSON, a non-array, duplicate keys, more than one `is_full_name`, or more than 30 items return `400` before any processing or billing.

### Accepted files

- Extensions: `pdf`, `jpg`, `jpeg`, `png`, `tiff`, `webp`, or a `zip` containing the document. Multi-page PDFs are supported (higher latency).
- Size: PDF and ZIP up to 50 MB; image files up to 6 MB (larger uploads return `400`). Files are compressed automatically before processing.
- Encrypted (password-protected) PDFs return `400`: upload a decrypted PDF or a photo instead.
- An empty file is processed as `DOCUMENT_AI_UNSUPPORTED_FILE`.

### Example

```python
import json
import requests

fields = [
    {"key": "employer_name", "name": "Employer name", "instruction": "The employer issuing the payslip.", "type": "text", "required": True},
    {"key": "employee_name", "name": "Employee name", "instruction": "Full name of the employee.", "type": "text", "required": True, "is_full_name": True},
    {"key": "net_pay", "name": "Net pay", "instruction": "Net amount paid for the period.", "type": "number", "required": True},
    {"key": "pay_date", "name": "Pay date", "instruction": "Payment date on the payslip.", "type": "date"},
]

with open("payslip.pdf", "rb") as document:
    response = requests.post(
        "https://verification.didit.me/v3/document-ai/",
        headers={"x-api-key": "YOUR_API_KEY"},
        files={"document": ("payslip.pdf", document, "application/pdf")},
        data={
            "fields": json.dumps(fields),
            "expected_first_name": "Jane",
            "expected_last_name": "Doe",
            "vendor_data": "user-123",
            "metadata": json.dumps({"flow": "onboarding"}),
        },
        timeout=90,
    )
result = response.json()
print(result["document_ai"]["status"], result["document_ai"]["extracted_data"])
```

```typescript
const form = new FormData();
form.append("document", fileBlob, "payslip.pdf");
form.append(
  "fields",
  JSON.stringify([
    { key: "employee_name", name: "Employee name", instruction: "Full name of the employee.", type: "text", required: true, is_full_name: true },
    { key: "net_pay", name: "Net pay", instruction: "Net amount paid for the period.", type: "number", required: true },
  ]),
);
form.append("expected_first_name", "Jane");
form.append("expected_last_name", "Doe");

const response = await fetch("https://verification.didit.me/v3/document-ai/", {
  method: "POST",
  headers: { "x-api-key": "YOUR_API_KEY" }, // let fetch set the multipart boundary
  body: form,
  signal: AbortSignal.timeout(90_000),
});
const result = await response.json();
```

### Response (200 OK)

```json
{
  "request_id": "9d6a3b1e-2f0c-4a8e-9b7d-1c2e3f4a5b6c",
  "document_ai": {
    "status": "In Review",
    "extracted_data": {
      "employer_name": "Acme Energy",
      "employee_name": "Jane Doe",
      "net_pay": null,
      "pay_date": "2026-07-31"
    },
    "detected_codes": [],
    "fields": [
      {"key": "employer_name", "name": "Employer name", "instruction": "The employer issuing the payslip.", "type": "text", "required": true, "is_full_name": false},
      {"key": "employee_name", "name": "Employee name", "instruction": "Full name of the employee.", "type": "text", "required": true, "is_full_name": true},
      {"key": "net_pay", "name": "Net pay", "instruction": "Net amount paid for the period.", "type": "number", "required": true, "is_full_name": false},
      {"key": "pay_date", "name": "Pay date", "instruction": "Payment date on the payslip.", "type": "date", "required": false, "is_full_name": false}
    ],
    "name_match_score": 100.0,
    "name_on_document": "Jane Doe",
    "warnings": [
      {
        "risk": "DOCUMENT_AI_MISSING_REQUIRED_FIELDS",
        "feature": "DOCUMENT_AI",
        "additional_data": {"missing_fields": ["Net pay"]},
        "log_type": "warning",
        "short_description": "Required fields could not be extracted",
        "long_description": "One or more fields configured as required could not be extracted from the uploaded document."
      }
    ]
  },
  "vendor_data": "user-123",
  "metadata": {"flow": "onboarding"},
  "created_at": "2026-08-19T16:41:05.002Z"
}
```

---

## Status Values & Handling

| `document_ai.status` | Meaning | Action |
|---|---|---|
| `"Approved"` | No warning resolved to `DECLINE` or `REVIEW` | Use `extracted_data` |
| `"In Review"` | At least one risk mapped to `REVIEW` (and none to `DECLINE`) | Manual review; read `warnings` |
| `"Declined"` | At least one risk mapped to `DECLINE` | Reject the document or ask for another one |

Precedence: `Declined` > `In Review` > `Approved`. Each warning's `log_type` follows its action: `error` (DECLINE), `warning` (REVIEW), `information` (NO_ACTION, listed but no status effect).

---

## Warning Tags

| Risk | Raised when | Action parameter | Default |
|---|---|---|---|
| `DOCUMENT_AI_UNREADABLE_DOCUMENT` | No field could be read from the document | `document_ai_unreadable_document_action` | `REVIEW` |
| `DOCUMENT_AI_MISSING_REQUIRED_FIELDS` | At least one `required` field is `null`; `additional_data.missing_fields` lists their names | `document_ai_missing_required_fields_action` | `REVIEW` |
| `DOCUMENT_AI_SUSPECTED_MANIPULATION` | PDF/EXIF forensics suspect editing: modified after digital signing, known PDF editor, overlay-text manipulation, suspicious re-export, image anomalies; `additional_data` has `detection_method` and the finding | `document_ai_document_tampering_action` | `DECLINE` |
| `DOCUMENT_AI_NAME_MISMATCH` | `name_match_score` is below the threshold; `additional_data` has `name_on_document`, `score`, `threshold` | `document_ai_name_mismatch_action` | `NO_ACTION` |
| `DOCUMENT_AI_UNSUPPORTED_FILE` | The upload is empty or not a processable file | `document_ai_unsupported_file_action` | `REVIEW` |

Every warning has `risk`, `feature` (always `DOCUMENT_AI`), `additional_data` (or `null`), `log_type`, `short_description`, `long_description`.

---

## Name Matching

| You are verifying | Send | Compared against |
|---|---|---|
| A person | `expected_first_name` + `expected_last_name` | The person's full name (fuzzy, transliteration-aware) |
| A company | `expected_company_name` (+ optional `expected_company_country`) | The company name |

- The compared value is the field marked `is_full_name`. If none is marked, Didit falls back to the first text field whose key looks like a name (`name`, `holder`, `full_name`, `account_holder`). Mark the field explicitly to control it.
- `name_match_score` (0-100) and `name_on_document` are returned whenever both a name value and an expected name exist, on matches and mismatches. With no expected name, `name_match_score` is `null` (and `name_on_document` may still be set); with no name value on the document, both are `null` and the check is skipped.
- Sending person and company fields together returns `400`.

---

## QR Codes and Barcodes

Every `200` includes `document_ai.detected_codes` (empty when none found, covering every processed PDF page). Detection failures never fail the request, and Didit never guesses a payload.

| Field | Description |
|---|---|
| `type` | Symbology, e.g. `QR_CODE`, `CODE_128`, `EAN_13`, `DATA_MATRIX`, `PDF_417` |
| `page_number` | 1-based page |
| `position` | Polygon `[[x, y], ...]` in rendered-page pixels, or `null` |
| `x`, `y`, `width`, `height` | Bounding box in rendered-page pixels, or `null` |
| `page_width`, `page_height` | Rendered page size used by the coordinates |
| `parsed_payload` | Decoded string or structured value; `null` when the code was located but not decoded |
| `raw_payload` | Raw decoder payload as base64, or `""` |

---

## Error Responses

| Code | Meaning | Action |
|---|---|---|
| `400` | Invalid request | Read the field errors in the response body |
| `400` | `{"error": "The PDF is encrypted. Please upload a decrypted PDF or a photo instead."}` | Upload a decrypted PDF or a photo |
| `400` | `{"error": ["Error extracting Document AI information"]}` or another `{"error": ...}` for an unreadable upload | The file could not be processed; send a clearer file |
| `401` | The API key has expired | Rotate it or create a new key in **Developers > API keys** |
| `403` | Missing, wrong or revoked API key; a scoped key without access to this endpoint; a request from outside the key's IP allowlist; or not enough credits | Read the message in `detail` or `error`: fix the `x-api-key` header or the key's access, or top up |
| `403` | `{"error": "Document AI API is not included in your contract rate card. ..."}` | Contract-billed organization: ask Didit to add Document AI to the rate card |
| `429` | Rate limit: 300 POST/PATCH/DELETE and 600 GET requests a minute per key | Wait the `Retry-After` seconds, then retry |

Typical `400` bodies: `{"document": ["No file was submitted."]}`, `{"fields": ["fields must be a valid JSON array string."]}`, `{"fields": ["Every fields item must have a unique key."]}`, `{"non_field_errors": ["Provide either person expected-name fields or expected_company_name, not both."]}`, `{"metadata": ["Metadata must be a JSON object."]}`, `{"vendor_data": ["vendor_data is too long (maximum 2000 bytes)."]}`.

The credit check runs before the upload is read: a key that cannot pay gets `403` before any processing.

---

## Response Field Reference

| Field | Type | Description |
|---|---|---|
| `request_id` | uuid | API session id when `save_api_request=true` (use with `GET /v3/session/{request_id}/decision/`); otherwise a transient correlation id |
| `document_ai.status` | string | `Approved`, `In Review`, `Declined` |
| `document_ai.extracted_data` | object | One entry per field `key`: string (`text`), number (`number`), `YYYY-MM-DD` string (`date`), or `null` when not readable |
| `document_ai.detected_codes` | array | QR codes and barcodes (see above) |
| `document_ai.fields` | array | Your field definitions after normalization (defaults filled in) |
| `document_ai.name_match_score` | number/null | 0-100 similarity with the expected name |
| `document_ai.name_on_document` | string/null | The name value that was compared |
| `document_ai.warnings` | array | One entry per detected risk; empty on a clean approval |
| `vendor_data` | string/null | Echo |
| `metadata` | object/null | Echo |
| `created_at` | datetime | When the request was processed (UTC, ISO 8601) |

---

## Sandbox

Sandbox API keys return a deterministic mock response with placeholder values and are not charged. Use them to test request building and parsing, not extraction quality.

---

## Document AI in Workflows (`DOCUMENT_AI`)

To have the user upload documents in the hosted flow instead, add the `DOCUMENT_AI` feature to a workflow (`POST /v3/workflows/`, see **didit-verification-management**). Differences from the standalone API:

- `config.document_ai_documents`: up to 3 documents, each `{document_key, title, description, fields[]}` (optional `title_i18n`, `description_i18n`; titles and descriptions are auto-translated). Field items use the same `key`, `name`, `instruction`, `type`, `required`, `is_full_name` (only `text` fields can be the full name).
- Same five action settings plus `document_ai_max_attempts_exceeded_action` and `document_ai_max_retry_attempts` (2 to 5); `document_ai_document_tampering_action` and `document_ai_max_attempts_exceeded_action` accept only `DECLINE` or `REVIEW`.
- The name is compared with the verified subject: the ID-verification name (or the session's expected details) on a person workflow, the verified company on a business workflow.
- `status_rules` can target `document_ai.<key>` and cross-reference other steps with `value_type: "field"` (e.g. `document_ai.account_holder` `fuzzy_match` `kyc.full_name`).
- Results arrive in the session decision (`GET /v3/session/{sessionId}/decision/`) and webhooks.
- Same $0.20 per document.

Full config reference: https://docs.didit.me/management-api/workflows/feature-configs

---

## Common Workflows

### Proof of funds check

```
1. POST /v3/document-ai/ with the bank statement, fields
   [account_holder (is_full_name, required), balance (number, required), currency, statement_date (date, required)]
   and expected_first_name + expected_last_name from your verified user
2. "Approved" -> use extracted_data.balance
   "In Review" -> read warnings (missing_fields, name mismatch) and review
   "Declined" -> DOCUMENT_AI_SUSPECTED_MANIPULATION by default: reject and ask for the original document
```

### Company document

```
1. POST /v3/document-ai/ with fields [company_name (is_full_name), registration_number, ...],
   expected_company_name + expected_company_country (2 letters)
2. Set document_ai_name_mismatch_action=REVIEW (default NO_ACTION only reports it)
```

### KYC + document cross-check

```
1. POST /v3/id-verification/ -> verified first_name / last_name
2. POST /v3/document-ai/ with expected_first_name / expected_last_name from step 1
3. Act on document_ai.status and name_match_score
```

---

## Utility Scripts

**extract_document.py**: upload a document with your field definitions and print the result.

```bash
# Requires: pip install requests
export DIDIT_API_KEY="your_api_key"
python scripts/extract_document.py statement.pdf --fields-file fields.json
python scripts/extract_document.py payslip.pdf \
    --fields '[{"key":"employee_name","type":"text","required":true,"is_full_name":true},{"key":"net_pay","type":"number","required":true}]' \
    --first-name Jane --last-name Doe --name-mismatch-action REVIEW
python scripts/extract_document.py deed.pdf --fields-file company_fields.json \
    --company-name "Acme Energy" --company-country FR --no-save
```
