---
name: didit-database-validation
description: >
  Integrate the Didit Database Validation API (POST /v3/database-validation/) to check
  identity data against government and authoritative registries. Use when the user wants
  to validate a national ID, CPF, CURP, DNI, RUT or cedula number against official records,
  confirm a person's name and date of birth with a civil registry, run a registry face match
  (Argentina RENAPER, Panama SIB), choose database validation services per country, or
  implement government database lookups using Didit. Covers 100+ services in 45 countries
  (strongest in Latin America, plus Spain, South Africa, Kenya and other markets) with
  per-service pricing and per-field match results.
version: 1.3.0
metadata:
  openclaw:
    requires:
      env:
        - DIDIT_API_KEY
    primaryEnv: DIDIT_API_KEY
    emoji: "🗄️"
    homepage: https://docs.didit.me
---

# Didit Database Validation API

## Overview

Verifies personal data against the authoritative source for a country (civil registry, tax authority, electoral roll or biometric registry) and returns a per-field comparison, a per-service outcome code and the registry record. Use it to catch synthetic identities and ID numbers that do not belong to the person.

**Pricing:** per service, from $0.05 (Dominican Republic `dom_cedula`) to $7.00 per query; most Latin American national ID services are $0.20 (billed once per service the registry answered, including no-match and not-found answers; `400` rejections and services the source never answered are free; standalone calls have no free tier). These are the list prices until 1 November 2026, when Didit pricing changes and the 500 free checks a month become $10 of free credit a month. Check [didit.me/pricing](https://didit.me/pricing) for current prices.

**Key constraints:**
- `issuing_state` is ISO 3166-1 **alpha-3** (`BRA`, `PER`, `ARG`). Alpha-2 codes (`BR`) return `400` "Invalid issuing state".
- Each country exposes one or more **services** (`service_id`). Without `services`, exactly **one** default service runs. Spain, Kenya, Zambia and most non-Latin-American services have no default: name them in `services`.
- Required fields depend on the selected services. Missing or malformed fields return `400` before any registry call (never billed).
- Send JSON, or `multipart/form-data` when a service needs a `selfie` (Argentina `arg_renaper`, Panama `pan_cedula_sib`, other biometric services).
- Results per field: `full_match`, `partial_match`, `no_match`. Overall `status`: `Approved`, `Declined` or `In Review`.

**Coverage:** the public catalog listed 123 live services in 45 countries plus a global (`GLB`) group on 2026-10-12: 17 Latin American countries, Spain, South Africa, Kenya, Zambia, Nigeria and identity, credit, residential and phone datasets in Europe, North America and Asia-Pacific. Read the live list (no API key needed):

```
GET https://verification.didit.me/v1/organization/database-validation-countries/
```

It returns `{ "<ISO3>": { "country_iso3", "country_name", "region", "services": [ { "service_id", "service_name", "coverage", "default_price_usd", "required_fields", "requires_any_fields", "optional_fields", "requires_consent", "requires_onboarding", "supports_selfie", ... } ] } }`. Services with `requires_onboarding: true` return `400` until Didit support activates them for your organization.

**API Reference:** https://docs.didit.me/standalone-apis/database-validation
**Feature Guide:** https://docs.didit.me/core-technology/database-validation/overview
**Supported Countries:** https://docs.didit.me/core-technology/database-validation/database-validation-supported-countries
**Prices per service:** https://docs.didit.me/getting-started/database-validation-pricing

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
POST https://verification.didit.me/v3/database-validation/
```

### Headers

| Header | Value | Required |
|---|---|---|
| `x-api-key` | Your API key | **Yes** |
| `Content-Type` | `application/json`, or `multipart/form-data` when sending `selfie` | **Yes** |

### Body

| Parameter | Type | Required | Description |
|---|---|---|---|
| `issuing_state` | string | **Yes** | ISO 3166-1 alpha-3 country of the registry (`BRA`, `ESP`, `COL`) |
| `services` | array of strings | No | `service_id`s to run (e.g. `["bra_cpf"]`); a comma-separated or JSON-encoded string is also accepted. Omitted or empty: exactly one default service runs (see table). Sending it adds `services_used` and `match_score` to the response. Each id must be live for `issuing_state` |
| `identification_number` | string | No | Shortcut that fills the country's number field (see table) for ARG, BOL, BRA, CHL, COL, CRI, DOM, ECU, GTM, HND, MEX, PAN, PER, PRY, SLV, URY, VEN. Never overrides an explicit field; ignored for other countries |
| `document_number` | string | Depends | Number field for ARG, BOL, GTM, HND, PRY, SLV, VEN |
| `personal_number` | string | Depends | Number field for CHL, COL, CRI, DOM, ECU, MEX, PAN, PER, URY |
| `tax_number` | string | Depends | Number field for BRA (CPF) |
| `national_id` | string | Depends | National ID number for services in KEN, ZMB, ZAF and other markets; optional for ESP `esp_dni` |
| `first_name` / `last_name` | string | Depends | Names to compare; required by some services |
| `middle_name` / `full_name` | string | No | Used by some services (`full_name` instead of first/last for some) |
| `date_of_birth` | string | Depends | `YYYY-MM-DD` |
| `date_of_issue` | string | Depends | Document issue date `YYYY-MM-DD`; required by COL `col_cedula` |
| `expiration_date` | string | No | Document expiry date `YYYY-MM-DD` |
| `document_type` | string | No | `P`, `DL`, `ID`, `RP`, `SSC`, `HIC`, `WP`, `TC`, `VISA`, `PSC`, `BC`, `OTHER` |
| `gender` | string | Depends | `M`, `F` or `X`; required by `arg_renaper` and `arg_renaper_data` |
| `nationality` | string | Depends | ISO 3166-1 alpha-3; required by COL `col_migracion` |
| `address` | object or string | Depends | `{"street_1", "street_2", "city", "region", "postal_code", "country"}` or one complete line. Required by address services (ESP `esp_dni` needs at least street and postal code) |
| `address_element_1` to `address_element_5`, `postal_code` | string | No | Address parts sent separately: street, unit, city/locality, state/region, postal code (`postal_code` is an alias of element 5) |
| `selfie` | file | Depends | Multipart only. `jpg`, `jpeg`, `png`, `webp`, max 2 MB. Required by biometric services |
| `consent` | boolean | Depends | Default `false`. Must be `true` for services with `requires_consent` (e.g. `esp_dni`); otherwise `400` with `services_requiring_consent` |
| `partial_match_action` | string | No | `DECLINE` or `NO_ACTION` (default `NO_ACTION`: partial match stays `Approved`) |
| `no_match_action` | string | No | `DECLINE` (default) or `NO_ACTION` |
| `save_api_request` | boolean | No | Default `true`: stored as a session (Business Console, `GET /v3/session/{sessionId}/decision/` with `request_id`, `status.updated` webhook) and `validations` is a per-service array. `false`: nothing stored, `validations` is one merged field map |
| `vendor_data` | string | No | Your identifier for the user, echoed back |
| `metadata` | object | No | Free-form JSON stored and echoed back |
| `validation_type` | string | No | Deprecated and ignored |

Other identifiers used by specific services: `passport_number`, `passport_expiration_date`, `passport_issue_country`, `passport_file_number`, `driver_license_number`, `driver_license_card_number`, `driver_license_state`, `driver_license_version`, `medicare_card_number`, `immi_card_number`, `immi_card_expiry_date`, `citizenship_certificate_number`, `birth_registration_number`, `birth_registration_date`, `birth_registration_state`, `marriage_certificate_number`, `change_of_name_certificate_number`, `first_partner_name`, `last_partner_name`, `voter_id`, `epic_card`, `pan`, `cic`, `identificador_ciudadano`, `ocr`, `voter_number`, `emission_number`, `bvn`, `bank_card_number`, `ssn`, `phone`, `landline`, `email`, `country_of_residence`. The catalog's `required_fields` / `requires_any_fields` say which a service needs.

**Sandbox:** sandbox API keys skip the registry calls and billing and return a fixed `full_match` response (it always includes `services_used` and `match_score: 100`, so do not test the live response shape against it).

### Example

```python
import requests

response = requests.post(
    "https://verification.didit.me/v3/database-validation/",
    headers={"x-api-key": "YOUR_API_KEY"},
    json={
        "issuing_state": "BRA",
        "services": ["bra_cpf"],
        "tax_number": "12345678900",
        "date_of_birth": "1980-01-01",
        "first_name": "John",
        "last_name": "Doe",
        "vendor_data": "user-1234",
    },
    timeout=60,
)
print(response.status_code, response.json())
```

```typescript
// Biometric service: multipart with a selfie (Argentina RENAPER)
const form = new FormData();
form.append("issuing_state", "ARG");
form.append("services", "arg_renaper");
form.append("document_number", "12345678");
form.append("gender", "F");
form.append("first_name", "Jane");
form.append("last_name", "Doe");
form.append("selfie", selfieFile); // jpg/jpeg/png/webp, max 2 MB

const response = await fetch("https://verification.didit.me/v3/database-validation/", {
  method: "POST",
  headers: { "x-api-key": "YOUR_API_KEY" },
  body: form,
});
const data = await response.json();
if (!response.ok) throw new Error(`${response.status}: ${JSON.stringify(data)}`);
console.log(data.database_validation.status, data.database_validation.match_type);
```

### Response (200 OK)

```json
{
  "request_id": "b3e7c1a2-9d4f-4f0b-8a6c-5e2d1f0a9b3e",
  "database_validation": {
    "status": "Approved",
    "issuing_state": "BRA",
    "validation_type": "one_by_one",
    "screened_data": {
      "tax_number": "12345678900",
      "first_name": "John",
      "last_name": "Doe",
      "date_of_birth": "1980-01-01"
    },
    "match_type": "full_match",
    "validations": [
      {
        "service_id": "bra_cpf",
        "service_name": "Brazil - CPF status check",
        "validation": {
          "full_name": "full_match",
          "date_of_birth": "full_match",
          "identification_number": "full_match"
        },
        "outcome_code": "MATCH",
        "outcome_detail": "200",
        "source_data": {
          "identification_number": "12345678900",
          "first_name": "JOHN",
          "last_name": "DOE",
          "date_of_birth": "1980-01-01",
          "lgpd_minor": false,
          "minor_under_16": false,
          "minor_under_18": false
        }
      }
    ],
    "warnings": [],
    "services_used": ["bra_cpf"],
    "match_score": 1.0
  },
  "vendor_data": "user-1234",
  "metadata": null,
  "created_at": "2026-10-12T10:30:00.000000+00:00"
}
```

With `save_api_request=false`, `validations` is a merged map instead, e.g. `{"full_name": "full_match", "date_of_birth": "full_match", "identification_number": "full_match"}`.

### Status Values & Handling

| Status | Meaning | Action |
|---|---|---|
| `"Approved"` | `full_match`, or a `partial_match`/`no_match` whose action is `NO_ACTION` (partial match is `NO_ACTION` by default) | Proceed; still read `warnings` and `errors` |
| `"Declined"` | A warning resolved to `DECLINE`: `no_match` or a superseded document (`no_match_action`, default `DECLINE`), or a partial match with `partial_match_action=DECLINE` | Identity data does not match the registry |
| `"In Review"` | Only `COULD_NOT_PERFORM_DATABASE_VALIDATION`: the services answered but nothing could be confirmed (e.g. the only service returned `INCONCLUSIVE` or `REGISTRY_UNAVAILABLE`) | Review manually or retry later |

A decline wins over review. A multi-service request can be `Approved` on one service while another failed: always check `errors[]` and each `outcome_code`.

### Error Responses

| Code | Meaning | Action |
|---|---|---|
| `400` | Invalid request | Read the field errors in the response body |
| `401` | The API key has expired | Rotate it or create a new key in **Developers > API keys** |
| `403` | Missing, wrong or revoked API key; a scoped key without access to this endpoint; a request from outside the key's IP allowlist; or not enough credits | Read the message in `detail` or `error`: fix the `x-api-key` header or the key's access, or top up |
| `429` | Rate limit: 300 POST/PATCH/DELETE and 600 GET requests a minute per key | Wait the `Retry-After` seconds, then retry |
| `502` | No selected service returned a usable result. Body: `error` plus `validation_errors[]` (`service_id`, `code` e.g. `empty_provider_response`, `message`, `retryable: true`). Nothing is billed | Retry later; with `save_api_request=true` the attempt is still recorded as a session |

`400` bodies on this endpoint (never billed):
- `{"error": ["Invalid issuing state. Valid options are: ARE, ARG, ..."]}`: wrong or alpha-2 `issuing_state`
- `{"error": ["No database validation services configured for ESP."]}`: no default service for the country; send `services`
- `{"error": ["Missing required fields: tax_number (or use 'identification_number' ...)"], "fields_required_by": {"tax_number": ["bra_cpf"]}}`; also `any_field_required_by`, `field_dependencies_required_by`, `address_fields_required_by` for the same family of problems
- `{"services": [...]}`: unknown service id, a service not live for that country, or one needing onboarding (`requires_onboarding`)
- `{"consent": [...], "services_requiring_consent": [...]}`: send `consent: true`
- `{"tax_number": ["Invalid tax number for BRA: Brazilian CPF (exactly 11 digits). ..."]}` or `invalid_fields_by_service`: format rule failed
- `{"error": "...", "validation_errors": [{"code": "provider_rejected_input", "retryable": false, ...}]}`: every source refused the submitted data; correct it, retrying the same values cannot succeed

The credit check covers the sum of the selected services' prices and runs before any registry call; the not-enough-credits `403` body is `{"error": "You don't have enough credits to perform this request. ..."}`.

---

## Response Field Reference

| Field | Type | Description |
|---|---|---|
| `request_id` | uuid | Session id when `save_api_request=true`; otherwise a one-off correlation id |
| `database_validation.status` | string | `Approved`, `Declined` or `In Review` |
| `database_validation.issuing_state` | string | Echo of the alpha-3 country |
| `database_validation.validation_type` | string | `one_by_one`, or `two_by_two` when 2+ services full-matched |
| `database_validation.screened_data` | object | Input sent to the services (dates as `YYYY-MM-DD`, `selfie` as a temporary URL, `consent_obtained: true` when consent was given) |
| `database_validation.match_type` | string/null | `full_match`, `partial_match` or `no_match` across services; `null` for outcome-only services |
| `database_validation.validations` | array or object | Per service: `service_id`, `service_name`, `validation` (field to `full_match`/`partial_match`/`no_match`), `outcome_code`, `outcome_detail`, `source_data` (registry record). Merged map when `save_api_request=false` |
| `database_validation.warnings` | array | `{feature, risk, additional_data, log_type, short_description, long_description}`; empty on a clean full match |
| `database_validation.errors` | array | Only when some services failed: `service_id`, `code`, `message`, `retryable`. Those services are not billed |
| `database_validation.services_used` | array | Services that returned a result (only when the request sent `services`) |
| `database_validation.match_score` | number | 0.0-1.0 share of attempted services with a full match (only when the request sent `services`) |
| `vendor_data` / `metadata` | string/object | Echo of your values |
| `created_at` | string | ISO 8601 UTC timestamp |

**`outcome_code` values:** `MATCH`, `PARTIAL_MATCH`, `NO_MATCH` (definitive mismatch), `DOCUMENT_NOT_FOUND` (number not in the registry), `INVALID_DOCUMENT_FORMAT` / `INVALID_INPUT` (the registry rejected the data), `MINOR_BLOCKED`, `DECEASED`, `BIOMETRIC_NO_MATCH` (face does not match), `BIOMETRIC_IMAGE_UNUSABLE` (retake the selfie), `INCONCLUSIVE` (review, not a no-match), `DOCUMENT_SUPERSEDED` (a newer edition of the document exists), `REGISTRY_UNAVAILABLE` / `REGISTRY_ERROR` (source failure, not billed).

---

## Matching Logic

| Rule | Behaviour |
|---|---|
| Names | Fuzzy match per name part (small typos still match: "Christophel" vs "Christopher" is a full match, "Chris" is not) |
| Date of birth, ID number | Exact match only |
| `match_type` | Any service `full_match` gives `full_match`; else any `partial_match` gives `partial_match`; else `no_match` |
| `validation_type` | `two_by_two` when two or more distinct services full-matched; otherwise `one_by_one`. There is no separate 2x2 price: each service is billed at its own price |
| Decisive fields | A service only compares the fields it holds and the fields you send; a required field is not always a compared one |

---

## Warning Tags

| Tag | When | Effect |
|---|---|---|
| `DATABASE_VALIDATION_NO_MATCH` | `match_type` is `no_match`, or a service gave a definitive negative (e.g. `DOCUMENT_NOT_FOUND`, `DECEASED`) without field comparisons | `no_match_action` (default `DECLINE`) |
| `DATABASE_VALIDATION_PARTIAL_MATCH` | `match_type` is `partial_match` | `partial_match_action` (default `NO_ACTION`: `information`, status stays `Approved`) |
| `DATABASE_VALIDATION_DOCUMENT_SUPERSEDED` | A service returned `DOCUMENT_SUPERSEDED`: the person matched but a newer document edition exists (`match_type` can still be `full_match`) | Follows `no_match_action` |
| `COULD_NOT_PERFORM_DATABASE_VALIDATION` | The services ran but confirmed nothing: an inconclusive answer, an unavailable or failing source, or a registry that could not use the data sent. `additional_data` names the services. Missing or invalid fields never get here: they return `400` | Always `In Review` (`log_type: warning`) |
| `DATABASE_VALIDATION_NOT_APPLICABLE` | Workflow sessions only (the document has no identifier the services need) | Not produced by this endpoint |

`log_type` mirrors the action: `DECLINE` gives `error`, `NO_ACTION` gives `information`. The automatic re-run after missing data is filled in exists only in workflow sessions, not on this endpoint.

---

## Supported Countries

Main countries, from the public catalog and pricing table (2026-10-12). "Default" is the service that runs when `services` is omitted.

| `issuing_state` | Default service | Required fields | Number format | Coverage | Price | Other services |
|---|---|---|---|---|---|---|
| `ARG` | `arg_renaper` (biometric) | `document_number`, `selfie`, `gender` | DNI, 7-8 digits, optional M/F prefix | - | $0.20 | `arg_renaper_data` (`document_number`, `gender`, no selfie, $0.20); `arg_citizens` $1.90, `arg_credit_bureau` $2.15 |
| `BOL` | `bol_cedula` | `document_number`, `date_of_birth` | CI, 6-10 digits | 90-95% | $0.20 | - |
| `BRA` | `bra_cpf` | `tax_number`, `date_of_birth` | CPF, exactly 11 digits | ~100% | $0.20 | 9 more, e.g. `bra_cpf_facial` (selfie, consent, $0.45), `bra_unico_idcloud` (selfie, consent, $0.20), `bra_death_check`, `bra_tax_registration` $0.15 |
| `CHL` | `chl_rut` | `personal_number` | RUT, e.g. `12345678-9` | - | $0.20 | - |
| `COL` | `col_cedula` | `personal_number`, `date_of_issue` | Cedula, 6-10 digits | 90-95% | $0.20 | `col_migracion` (`personal_number`, `date_of_birth`, `nationality`, $1.20) |
| `CRI` | `cri_cedula` | `personal_number` | Cedula, 9-12 digits | 90-95% | $0.20 | - |
| `DOM` | `dom_cedula` | `personal_number` | Cedula, exactly 11 digits | - | $0.05 | - |
| `ECU` | `ecu_cedula` | `personal_number` | Cedula, exactly 10 digits | - | $0.20 | - |
| `ESP` | none: send `services: ["esp_dni"]` and `consent: true` | `first_name`, `last_name`, `date_of_birth`, `address` (street + postal code) | No number field; optional `national_id` (DNI/NIE) is also compared | ~75% | $1.26 | - |
| `GTM` | `gtm_dpi` | `document_number`, `date_of_birth` | DPI, exactly 13 digits | 90-95% | $0.20 | `gtm_dpi_facial` (`document_number`, `selfie`, consent, $0.35) |
| `HND` | `hnd_dni` | `document_number` | DNI, exactly 13 digits | 90-95% | $0.20 | - |
| `MEX` | `mex_curp` | `personal_number` | CURP, exactly 18 characters | ~100% | $0.20 | `mex_ine_vigencia` (INE credential: `cic`, `identificador_ciudadano`, `ocr` or `voter_number` + `emission_number`, $0.20) |
| `PAN` | `pan_cedula_sib` (biometric) | `personal_number`, `selfie` | Cedula, 5-20 characters | - | $0.75 | `pan_cedula_sib_plus` (same fields, $1.50) |
| `PER` | `per_dni` | `personal_number` | DNI, exactly 8 digits | - | $0.20 | `per_tax_registration` (`first_name`, `last_name`, `date_of_birth`, `personal_number`, $1.75) |
| `PRY` | `pry_cedula` | `document_number` | CI, 6-10 digits | 90-95% | $0.20 | - |
| `SLV` | `slv_dui` | `document_number`, `date_of_birth` | DUI, exactly 9 digits | 90-95% | $0.20 | - |
| `URY` | `ury_cedula` | `personal_number`, `date_of_birth` | CI, 7-9 digits | 90-95% | $0.20 | - |
| `VEN` | `ven_cedula` | `document_number` | Cedula, 7-10 digits, optional V/E prefix | 90-95% | $0.20 | - |
| `KEN` | none: `ken_national_id` | `first_name`, `last_name`, `date_of_birth`, `national_id` | - | ~90% | $0.65 | - |
| `ZMB` | none: `zmb_national_id` | `national_id`, `first_name`, `last_name` | - | - | $0.20 | - |
| `ZAF` | `zaf_africa_national_id` | `first_name`, `last_name`, `date_of_birth`, `national_id` | - | ~100% | $1.10 | 12 more (driving licence, bank account holder, company registry, fraud prevention, ...) |

Other countries (Australia, Austria, Canada, China, Denmark, Finland, France, Germany, India, Indonesia, Italy, Cambodia, Malaysia, Netherlands, New Zealand, Nigeria, Norway, Philippines, Singapore, Sweden, Switzerland, Thailand, United Kingdom, United States) and the `GLB` group: read the catalog and always send `services`; most of them have no default service. Optional fields (usually `first_name`, `last_name`) add name comparison where the service supports it.

---

## Common Workflows

### Validate the Data From an ID Document

```
1. POST /v3/id-verification/ -> id_verification.issuing_state (alpha-3), document_number,
   personal_number, first_name, last_name, date_of_birth, gender, date_of_issue
   (see the didit-id-document-verification skill)
2. Look up the country in the table (or the catalog) and pick services
3. POST /v3/database-validation/ with issuing_state, services and the required fields
   (identification_number fills the country's number field)
4. Approved -> data confirmed by the registry
   Declined -> DATABASE_VALIDATION_NO_MATCH / _DOCUMENT_SUPERSEDED: do not trust the identity data
   In Review -> COULD_NOT_PERFORM_DATABASE_VALIDATION: review or retry later
   502 -> no service answered (not billed): retry later
```

### Spain DNI/NIE

```json
{
  "issuing_state": "ESP",
  "services": ["esp_dni"],
  "consent": true,
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1990-01-01",
  "address": {"street_1": "Calle Mayor 10", "city": "Madrid", "postal_code": "28013", "country": "ES"}
}
```

### Biometric Registry Check (Argentina, Panama)

Send `multipart/form-data` with `selfie` (max 2 MB). `arg_renaper` also needs `document_number` and `gender`; `pan_cedula_sib` needs `personal_number`. `BIOMETRIC_NO_MATCH` is a real face mismatch; `BIOMETRIC_IMAGE_UNUSABLE` means retake the selfie.

### Retrieve a Stored Result

With `save_api_request=true` (default), `GET /v3/session/{request_id}/decision/` returns the result in `database_validations[]`.

---

## Utility Scripts

**validate_database.py**: Validate identity data against government databases from the command line. Prints the JSON response, then status, match type, per-service outcomes, warnings and errors.

```bash
# Requires: pip install requests
export DIDIT_API_KEY="your_api_key"
# issuing_state is ISO alpha-3. Use the number field the country needs (see the table) or --identification-number.
python scripts/validate_database.py --issuing-state PER --personal-number 12345678 --first-name Carlos --last-name Garcia
python scripts/validate_database.py --issuing-state BRA --tax-number 12345678900 --dob 1980-01-01 --services bra_cpf
python scripts/validate_database.py --issuing-state MEX --identification-number GARC850315HDFRRL09
python scripts/validate_database.py --issuing-state COL --personal-number 1234567890 --date-of-issue 2015-06-20
python scripts/validate_database.py --issuing-state ARG --document-number 12345678 --gender F --selfie selfie.jpg
python scripts/validate_database.py --issuing-state ESP --services esp_dni --consent --first-name John --last-name Doe \
  --dob 1990-01-01 --address '{"street_1": "Calle Mayor 10", "city": "Madrid", "postal_code": "28013", "country": "ES"}'
```
