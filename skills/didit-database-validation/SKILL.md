---
name: didit-database-validation
description: >
  Integrate Didit Database Validation API to verify personal data against government
  databases. Use when the user wants to validate identity against government records,
  verify national ID numbers, check CPF/CURP/DNI/cedula numbers, perform identity database
  lookups, validate identity documents against official sources, or implement database
  verification for Latin American or Spanish identity documents using Didit.
  Supports 18 countries with 1x1 and 2x2 matching methods.
version: 1.2.0
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

Verifies personal data and identity documents against trusted government and financial databases. Prevents synthetic identity fraud and ensures identity authenticity.

**Key constraints:**
- Requires `issuing_state` (ISO alpha-2) to select the data sources, plus the country-specific number field
- Coverage: **18 countries** (primarily Latin America + Spain)
- Results: `full_match`, `partial_match`, or `no_match`
- Only charged per **successful query** — no charge if insufficient data

**Matching methods:**

| Method | Description | Starting Price |
|---|---|---|
| **1x1** | Single data source validation | $0.05 |
| **2x2** | Two data sources cross-validation | $0.30 |

**API Reference:** https://docs.didit.me/standalone-apis/database-validation
**Feature Guide:** https://docs.didit.me/core-technology/database-validation/overview
**Supported Countries:** https://docs.didit.me/core-technology/database-validation/database-validation-supported-countries

---

## Authentication

All requests require `x-api-key` header. Get your key from [Didit Business Console](https://business.didit.me) → API & Webhooks, or via programmatic registration (see below).

## Getting Started (No Account Yet?)

If you don't have a Didit API key, create one in 2 API calls:

1. **Register:** `POST https://apx.didit.me/auth/v2/programmatic/register/` with `{"email": "you@gmail.com", "password": "MyStr0ng!Pass"}`
2. **Check email** for a 6-character OTP code
3. **Verify:** `POST https://apx.didit.me/auth/v2/programmatic/verify-email/` with `{"email": "you@gmail.com", "code": "A3K9F2"}` → response includes `api_key`

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
| `Content-Type` | `application/json` | **Yes** |

### Body (JSON)

| Parameter | Type | Required | Description |
|---|---|---|---|
| `issuing_state` | string | **Yes** | ISO 3166-1 alpha-2 country code — selects which data sources run |
| `first_name` | string | No | First name for matching |
| `last_name` | string | No | Last name for matching |
| `middle_name` | string | No | Middle name for matching |
| `full_name` | string | No | Full name for matching |
| `date_of_birth` | string | No | DOB in `YYYY-MM-DD` (required for some countries) |
| `document_number` | string | No | Country-specific document number (see table below) |
| `personal_number` | string | No | Country-specific personal number (see table below) |
| `tax_number` | string | No | Country-specific tax number (see table below) |
| `document_type` | string | No | Document type for matching |
| `gender` | string | No | `M`, `F`, or `X` |
| `nationality` | string | No | ISO country code |
| `services` | array | No | `service_id`s to restrict which sources run |
| `save_api_request` | boolean | No | Save in Business Console |
| `vendor_data` | string | No | Your identifier for session tracking |

Send the country-specific number field for the target country (the table shows which field name each country expects). `issuing_state` selects the data sources to query:

| Country | Number Field | Document | Format |
|---|---|---|---|
| AR | `document_number` | DNI | — |
| BO | `document_number` | CI | — |
| BR | `tax_number` | CPF | 11 digits |
| CL | `personal_number` | RUT | — |
| CO | `personal_number` | Cedula | — |
| CR | `personal_number` | Cedula | — |
| DO | `personal_number` | Cedula | 11 digits |
| EC | `personal_number` | Cedula | 10 digits |
| ES | `personal_number` | DNI/NIE | — |
| GT | `document_number` | DPI | — |
| HN | `document_number` | DNI | — |
| MX | `personal_number` | CURP | 18 chars |
| PA | `document_number` | Cedula | — |
| PE | `personal_number` | DNI | 8 digits |
| PY | `document_number` | CI | — |
| SV | `document_number` | DUI | — |
| UY | `personal_number` | CI | — |
| VE | `document_number` | Cedula | — |

### Example

```python
import requests

response = requests.post(
    "https://verification.didit.me/v3/database-validation/",
    headers={"x-api-key": "YOUR_API_KEY", "Content-Type": "application/json"},
    json={
        "issuing_state": "PE",
        "personal_number": "12345678",
        "first_name": "Carlos",
        "last_name": "Garcia",
    },
)
print(response.json())
```

```typescript
const response = await fetch("https://verification.didit.me/v3/database-validation/", {
  method: "POST",
  headers: { "x-api-key": "YOUR_API_KEY", "Content-Type": "application/json" },
  body: JSON.stringify({
    issuing_state: "PE",
    personal_number: "12345678",
    first_name: "Carlos",
    last_name: "Garcia",
  }),
});
```

### Response (200 OK)

```json
{
  "request_id": "a1b2c3d4-...",
  "database_validation": {
    "status": "Approved",
    "match_type": "full_match",
    "issuing_state": "PE",
    "validation_type": "1x1",
    "screened_data": {
      "personal_number": "12345678",
      "first_name": "Carlos",
      "last_name": "Garcia"
    },
    "validations": {
      "full_name": "full_match",
      "identification_number": "full_match"
    }
  }
}
```

### Status Values & Handling

| Status | Meaning | Action |
|---|---|---|
| `"Approved"` | Full match against government records | Identity confirmed |
| `"Declined"` | No match found | Identity could not be verified |
| `"In Review"` | Partial match or insufficient data | Review screened_data and validations |

### Error Responses

| Code | Meaning | Action |
|---|---|---|
| `400` | Invalid request | Check ID number format for target country |
| `401` | Invalid API key | Verify `x-api-key` header |
| `403` | Insufficient credits | Top up at business.didit.me |

---

## Matching Logic

### Name Matching

| Result | Criteria |
|---|---|
| **Full Match** | Full name concatenation at **85% similarity** (Levenshtein), OR First + Last both full match |
| **Partial Match** | Any single name component full match |
| **No Match** | No component reaches 70% similarity |

> Individual name components use **70% Levenshtein threshold**. Example: "Christophel" vs "Christopher" = Full Match; "Chris" vs "Christopher" = No Match.

### 1x1 Decision

| Match Type | Name | ID Number |
|---|---|---|
| `full_match` | Full Match | Full Match |
| `partial_match` | Partial Match | Full Match |
| `no_match` | All other combinations | — |

### 2x2 Decision

Requires matching against **2 independent data sources**:

| Match Type | Condition |
|---|---|
| `full_match` | Both sources confirm name + ID |
| `partial_match` | One source confirms |
| `no_match` | Neither source confirms |

> DOB and ID number matching is **exact only** — no fuzzy matching.

---

## Warning Tags

| Tag | Description |
|---|---|
| `COULD_NOT_PERFORM_DATABASE_VALIDATION` | Missing required data — provide the country-specific number field, name, and `issuing_state` |
| `DATABASE_VALIDATION_PARTIAL_MATCH` | Partial match found — requires investigation |
| `DATABASE_VALIDATION_NO_MATCH` | No match found in government records |

> When `COULD_NOT_PERFORM_DATABASE_VALIDATION` fires, session goes to "In Review". Validation **auto-retriggers** once missing data is provided.

---

## Supported Countries

| Country | Method | Coverage | Required Input |
|---|---|---|---|
| Argentina | 1x1 | 95% | Document number |
| Bolivia | 1x1 | 95% | Document number + DOB |
| Brazil | 1x1 | 95% | Tax number (CPF) |
| Chile | 1x1 | 95% | Personal number (RUT) |
| Colombia | 1x1 | 95% | Document number + type |
| Costa Rica | 1x1 | 95% | Personal number |
| Dominican Republic | 1x1 | 95% | Personal number |
| Ecuador | 1x1 / 2x2 | 90-96% | Personal number |
| El Salvador | 1x1 | 95% | Document number + DOB |
| Guatemala | 1x1 | 95% | Document number |
| Honduras | 1x1 | 95% | Document number |
| Mexico | 1x1 | 95% | Personal number (CURP) |
| Panama | 1x1 | 95% | Document number + DOB |
| Paraguay | 1x1 | 95% | Document number |
| Peru | 1x1 / 2x2 | 95-99% | Personal number |
| Spain | 1x1 | 95% | Personal number + doc type + expiry |
| Uruguay | 1x1 | 95% | Personal number + DOB |
| Venezuela | 1x1 | 95% | Document number |

---

## Utility Scripts

**validate_database.py**: Validate identity against government databases from the command line.

```bash
# Requires: pip install requests
export DIDIT_API_KEY="your_api_key"
# Use the number field that matches the country (see the table above):
# PE/MX/CL/CO/CR/DO/EC/ES/UY → --personal-number, BR → --tax-number, AR/BO/GT/HN/PA/PY/SV/VE → --document-number
python scripts/validate_database.py --issuing-state PE --personal-number 12345678 --first-name Carlos --last-name Garcia
python scripts/validate_database.py --issuing-state MX --personal-number GARC850315HDFRRL09
python scripts/validate_database.py --issuing-state BR --tax-number 12345678901
```
