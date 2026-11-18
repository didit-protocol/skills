---
name: didit-aml-screening
description: >
  Integrate the Didit AML Screening standalone API to screen people or companies against
  sanctions, PEP, warning and adverse-media watchlists. Use when the user wants to run AML or
  KYC/AML compliance checks, screen against OFAC/UN/EU sanctions lists, check PEP status, search
  adverse media, tune match and risk scoring, review AML hits (Confirmed Match, False Positive,
  Inconclusive), or turn on ongoing AML monitoring using Didit. Covers POST /v3/aml/ (1,300+
  watchlists, fuzzy name matching, configurable weights and thresholds, idempotent retries) and
  the AML hit review endpoints.
version: 1.3.0
metadata:
  openclaw:
    requires:
      env:
        - DIDIT_API_KEY
    primaryEnv: DIDIT_API_KEY
    emoji: "🛡️"
    homepage: https://docs.didit.me
---

# Didit AML Screening API

## Overview

Screens a person or company against 1,300+ global watchlists and databases in one synchronous call. Two scores per hit: **Match Score** (is this the same person?) and **Risk Score** (how risky is the matched entity?).

**Key constraints:**
- `full_name` is the only required field (at least 2 characters).
- `entity_type`: `"person"` (default) or `"company"`.
- `nationality` is an ISO 3166-1 **alpha-2** code (`ES`, not `ESP`). Anything else returns `400`.
- `aml_name_weight` + `aml_dob_weight` + `aml_country_weight` must sum to exactly 100.
- `aml_score_approve_threshold` must be <= `aml_score_review_threshold`.
- `include_ongoing_monitoring: true` requires `save_api_request: true` (the default).
- `include_adverse_media: true` waits for adverse media (about 5 s plus up to 25 s): use a client timeout of at least 60 seconds.
- Send an `Idempotency-Key` header when retrying, so a timeout never runs or bills a second screening.

**Coverage (per the docs):** sanctions (e.g. OFAC SDN, UN, EU, HM Treasury), law-enforcement and most-wanted lists (e.g. FBI, Interpol), PEPs (Levels 1-4) and their relatives and close associates, warnings and regulatory enforcement, fitness and probity, insolvency, and adverse media from 50k+ news sources (only with `include_adverse_media: true`).

**Scoring:**
1. **Match Score** (0-100) per hit: below `aml_match_score_threshold` (default 93) the hit is `"False Positive"`, at or above it is `"Unreviewed"`. Hits below 75 are not returned.
2. **Risk Score** (0-100) per hit: the highest risk score among non-False-Positive hits becomes `aml.score`, which sets `aml.status` through your two thresholds.

**Persistence:** with `save_api_request: true` (default) the screening is stored as a session: `request_id` works with `GET /v3/session/{sessionId}/decision/`, it shows in the Business Console, a `status.updated` webhook fires, and hits can be reviewed later. With `false` nothing is stored and `request_id` is only a correlation id.

**Sandbox:** sandbox API keys skip screening and billing and return a mocked result: `"Approved"` with zero hits unless you pass `sandbox_scenario` (`decline_aml_hit` returns one hit and `"Declined"`, `review_aml_possible_match` returns `"In Review"`; catalog at `GET /v1/sandbox/scenarios/`). `sandbox_scenario` is rejected on live applications.

**Pricing:** AML Screening $0.20 per screening (one credit charged after a successful screening; idempotent replays are not charged again; standalone calls have no free tier). AML Monitoring $0.07 per monitored profile per year. These are the list prices until 1 November 2026, when Didit pricing changes and the 500 free checks a month become $10 of free credit a month. Check [didit.me/pricing](https://didit.me/pricing) for current prices.

**API Reference:** https://docs.didit.me/standalone-apis/aml-screening
**Feature Guide:** https://docs.didit.me/core-technology/aml-screening/overview
**Match Score:** https://docs.didit.me/core-technology/aml-screening/aml-match-score
**Risk Score:** https://docs.didit.me/core-technology/aml-screening/aml-risk-score

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
POST https://verification.didit.me/v3/aml/
```

### Headers

| Header | Value | Required |
|---|---|---|
| `x-api-key` | Your API key | **Yes** |
| `Content-Type` | `application/json` | **Yes** |
| `Idempotency-Key` | Your retry key, max 255 characters | No |

`Idempotency-Key` is scoped to your application and the exact request body. A retry with the same key and body returns the stored response without screening or billing again; the same key with a different body returns `409`; a retry while the first request is still running returns `409` with `Retry-After: 30`.

### Body (JSON)

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `full_name` | string | **Yes** | - | Person or company name, min 2 characters |
| `entity_type` | string | No | `"person"` | `"person"` or `"company"` |
| `date_of_birth` | string | No | - | `YYYY-MM-DD`: date of birth (person) or incorporation date (company) |
| `nationality` | string | No | - | ISO 3166-1 alpha-2 country code, e.g. `US` |
| `document_number` | string | No | - | ID document number. Not weighted: acts as a "golden key" (see Match Score). Used as a search filter only when 2-50 characters; outside that range the screening still runs and is billed, just not narrowed |
| `aml_match_score_threshold` | integer | No | `93` | 0-100. Hits below it are `"False Positive"`, at or above `"Unreviewed"` |
| `aml_name_weight` | integer | No | `60` | 0-100. Name weight in the match score |
| `aml_dob_weight` | integer | No | `25` | 0-100. DOB weight in the match score |
| `aml_country_weight` | integer | No | `15` | 0-100. Country weight in the match score (the three weights must sum to 100) |
| `aml_score_approve_threshold` | number | No | `80` | 0-100. `aml.score` at or below it is `"Approved"` |
| `aml_score_review_threshold` | number | No | `100` | 0-100. `aml.score` above it is `"Declined"`; between the two thresholds is `"In Review"` |
| `include_adverse_media` | boolean | No | `false` | Also search news media for negative coverage (adds up to about 30 s) |
| `include_ongoing_monitoring` | boolean | No | `false` | Keep re-screening this profile and report changes by webhook. Billed as AML Monitoring. Requires `save_api_request: true` |
| `save_api_request` | boolean | No | `true` | Store the screening as a session (console, decision endpoint, webhooks, hit review) |
| `vendor_data` | string | No | - | Your identifier for the screened user, stored and echoed |
| `metadata` | object | No | `null` | Free-form JSON stored with the request and echoed back |
| `sandbox_scenario` | string | No | - | Sandbox keys only: `decline_aml_hit`, `review_aml_possible_match`, ... |

### Example

```python
import requests

response = requests.post(
    "https://verification.didit.me/v3/aml/",
    headers={
        "x-api-key": "YOUR_API_KEY",
        "Content-Type": "application/json",
        "Idempotency-Key": "aml-user-1234-2026-10-12",
    },
    json={
        "full_name": "Jane Doe",
        "date_of_birth": "1985-03-15",
        "nationality": "US",
        "document_number": "AB1234567",
        "entity_type": "person",
        "vendor_data": "user-1234",
    },
    timeout=90,
)
aml = response.json()["aml"]
print(aml["status"], aml["score"], aml["total_hits"])
```

```typescript
const response = await fetch("https://verification.didit.me/v3/aml/", {
  method: "POST",
  headers: {
    "x-api-key": "YOUR_API_KEY",
    "Content-Type": "application/json",
    "Idempotency-Key": "aml-user-1234-2026-10-12",
  },
  body: JSON.stringify({
    full_name: "Jane Doe",
    date_of_birth: "1985-03-15",
    nationality: "US",
    vendor_data: "user-1234",
  }),
});
const { aml } = await response.json();
```

### Response (200 OK, trimmed)

One Unreviewed sanctions hit (match 97, risk 86) and one False Positive PEP hit (match 88) that is left out of `aml.score`. With the default thresholds, 86 is above 80 and not above 100, so the status is `"In Review"`.

```json
{
  "request_id": "a1b2c3d4-5e6f-4a7b-8c9d-0e1f2a3b4c5d",
  "aml": {
    "status": "In Review",
    "total_hits": 2,
    "entity_type": "person",
    "hits": [
      {
        "id": "hit-001",
        "url": "https://sanctions.example.org/entry/123",
        "match": false,
        "score": 0.97,
        "match_score": 97.0,
        "risk_score": 86.0,
        "caption": "Jane Doe",
        "datasets": ["Sanctions"],
        "review_status": "Unreviewed",
        "rca_name": "",
        "first_seen": "2024-01-07T00:00:00",
        "last_seen": "2026-05-02T00:00:00",
        "properties": {"name": ["Jane Doe"], "birthDate": ["1985-03-15"], "nationality": ["United States"]},
        "score_breakdown": {
          "name_score": 95, "name_weight": 60, "name_weight_normalized": 60.0, "name_contribution": 57.0,
          "dob_score": 100, "dob_weight": 25, "dob_weight_normalized": 25.0, "dob_contribution": 25.0,
          "country_score": 100, "country_weight": 15, "country_weight_normalized": 15.0, "country_contribution": 15.0,
          "document_number_match_type": "NEUTRAL",
          "document_number_effect": "Hit has no document number data",
          "total_score": 97
        },
        "pep_matches": [],
        "sanction_matches": [{"list_name": ["Example Sanctions List"], "matched_name": "Jane Doe", "source_url": "https://sanctions.example.org/entry/123"}],
        "warning_matches": [],
        "adverse_media_matches": [],
        "adverse_media_details": null,
        "linked_entities": []
      },
      {
        "id": "hit-002",
        "match_score": 88.0,
        "risk_score": 47.5,
        "caption": "Jane A. Doe",
        "datasets": ["PEP Level 2"],
        "review_status": "False Positive",
        "score_breakdown": {
          "name_score": 80, "name_weight": 60, "name_weight_normalized": 60.0, "name_contribution": 48.0,
          "dob_score": 100, "dob_weight": 25, "dob_weight_normalized": 25.0, "dob_contribution": 25.0,
          "country_score": 100, "country_weight": 15, "country_weight_normalized": 15.0, "country_contribution": 15.0,
          "document_number_match_type": "NEUTRAL",
          "document_number_effect": "Hit has no document number data",
          "total_score": 88
        }
      }
    ],
    "score": 86.0,
    "screened_data": {
      "full_name": "Jane Doe",
      "date_of_birth": "1985-03-15",
      "nationality": "US",
      "document_number": "AB1234567"
    },
    "warnings": [
      {
        "feature": "AML",
        "risk": "POSSIBLE_MATCH_FOUND",
        "additional_data": null,
        "log_type": "warning",
        "short_description": "Possible match found in AML screening",
        "long_description": "The Anti-Money Laundering (AML) screening process identified potential matches with watchlists or high-risk databases, requiring further review."
      }
    ]
  },
  "vendor_data": "user-1234",
  "metadata": null,
  "created_at": "2026-10-12T10:23:44.812000+00:00"
}
```

### Status Values & Handling

| `aml.status` | Rule (defaults) | Action |
|---|---|---|
| `"Approved"` | `aml.score` <= approve threshold (80). Includes no hits and all hits False Positive (score 0) | Safe to proceed |
| `"In Review"` | approve threshold < `aml.score` <= review threshold (100) | Manual compliance review of the Unreviewed hits |
| `"Declined"` | `aml.score` > review threshold. With the default of 100 this never happens: lower `aml_score_review_threshold` to auto-decline | Block or escalate per your policy |

The standalone API only returns these three statuses.

### Error Responses

| Code | Meaning | Action |
|---|---|---|
| `400` | Invalid request | Read the field errors in the response body. Cross-field rules return `{"error": [...]}`: weights not summing to 100, approve threshold above review threshold, monitoring without `save_api_request`. Also an `Idempotency-Key` longer than 255 characters |
| `401` | The API key has expired | Rotate it or create a new key in **Developers > API keys** |
| `403` | Missing, wrong or revoked API key; a scoped key without access to this endpoint; a request from outside the key's IP allowlist; or not enough credits | Read the message in `detail` or `error`: fix the `x-api-key` header or the key's access, or top up |
| `409` | `Idempotency-Key` reused with a different body, or the first request with that key is still running | Use a new key for a new request; for a running one, wait `Retry-After` and retry with the same key and body |
| `429` | Rate limit: 300 POST/PATCH/DELETE and 600 GET requests a minute per key | Wait the `Retry-After` seconds, then retry |

The credit check runs before validation and before any screening: `403` with `{"error": "You don't have enough credits to perform this request. Please top up at https://business.didit.me"}`.

---

## Match Score System

`match_score` = sum of each component's score x its weight, with the weights re-normalized over the components both sides have data for (name only: name weight becomes 100%). Clamped to 0-100.

| Component | Default Weight | Scoring |
|---|---|---|
| Name | 60 | Fuzzy similarity 0-100 (typos, word order, middle names) |
| Date of birth | 25 | Same full date 100%. Hit has only the year and it matches 100%. Same year, different month or day 50%. Different year -100% |
| Country | 15 | Match 100%. Mismatch -50%. Country names and alpha-3 codes on the hit are normalized before comparing |

**Document number "golden key"** (not weighted; numbers are compared after removing spaces, `-`, `.` and `_`, uppercase):

| Case | Effect |
|---|---|
| Your `document_number` equals one of the hit's numbers | `match_score` set to **100** (`MATCH`) |
| Missing on either side, or the numbers differ | Score unchanged (`NEUTRAL`). A different number is not penalized, because it may be a different document type |

`score_breakdown.document_number_match_type` is `MATCH` or `NEUTRAL` today; the enum also lists `HARD_MISMATCH`, which the current scoring does not produce.

**Classification:** `match_score` < `aml_match_score_threshold` (93) -> `"False Positive"` (left out of `aml.score`); >= threshold -> `"Unreviewed"`. Hits below 75 are not returned at all.

---

## Risk Score System

Per the docs: `risk_score = (Country x 0.30) + (Category x 0.50) + (Criminal records x 0.20)`, 0-100. The per-dimension view is in `hits[].risk_view`.

**Category scores** (the highest category of the hit is used):

| Category (`datasets` value) | Score |
|---|---|
| `Sanctions`, `PEP`, `PEP Level 1` | 100 |
| `Warnings and Regulatory Enforcement` | 95 |
| `Insolvency`, `PEP Level 2` | 80 |
| `SIE`, `SIP` | 75 |
| `PEP Level 3` | 70 |
| `Fitness and Probity` | 65 |
| `Adverse Media` | 60 |
| `PEP Level 4` | 55 |

**Final status:** `aml.score` = highest `risk_score` among hits that are not `"False Positive"` (0 when there are none), then the thresholds in Status Values. Changing a hit's review status later (see Reviewing Hits) does not recompute `aml.status`.

---

## Warning Tags

| Tag | When | `log_type` |
|---|---|---|
| `POSSIBLE_MATCH_FOUND` | `aml.score` is non-zero and >= `aml_score_approve_threshold` (a score exactly at the threshold warns but stays `"Approved"`) | `warning`; `error` when the score is above `aml_score_review_threshold` |

Warning objects: `{feature, risk, additional_data, log_type, short_description, long_description}`. `COULD_NOT_PERFORM_AML_SCREENING` exists only in workflow sessions (KYC data missing full name, date of birth or issuing state); the standalone API never returns it.

---

## Response Field Reference

### Top level

| Field | Type | Description |
|---|---|---|
| `request_id` | string | Session id when `save_api_request` is `true`, otherwise a correlation UUID |
| `aml.status` | string | `"Approved"`, `"In Review"`, `"Declined"` |
| `aml.total_hits` | integer | Number of entries in `hits` (False Positives included) |
| `aml.entity_type` | string | `"person"` or `"company"` |
| `aml.score` | number | Highest `risk_score` among non-False-Positive hits |
| `aml.screened_data` | object | `{full_name, date_of_birth, nationality, document_number}` as screened (`null` when absent) |
| `aml.warnings` | array | See Warning Tags |
| `vendor_data`, `metadata`, `created_at` | | Echoes and response timestamp |

### Hit Object

| Field | Type | Description |
|---|---|---|
| `id` | string | Hit id. Use it as `hit_id` when reviewing |
| `caption` | string | Display name of the matched entity |
| `match_score` | number | 0-100 identity confidence |
| `risk_score` | number | 0-100 entity risk |
| `score` | number | Deprecated: match score on a 0-1 scale |
| `match` | boolean | Legacy flag. Use `match_score` + `review_status` |
| `review_status` | string | `"False Positive"`, `"Unreviewed"`, `"Confirmed Match"`, `"Inconclusive"` |
| `datasets` | array | `PEP`, `PEP Level 1`-`PEP Level 4`, `Sanctions`, `Adverse Media`, `Warnings and Regulatory Enforcement`, `Fitness and Probity`, `SIP`, `SIE`, `Insolvency` |
| `properties` | object | Profile arrays: `name`, `alias`, `notes`, `gender`, `birthDate`, `birthPlace`, `nationality`, `position`, ... |
| `rca_name` | string | Related close associate through which the entity matched |
| `url` | string | Source URL, when available |
| `pep_matches` | array | `{list_name, publisher, source_url, description, matched_name, pep_position, date_of_birth, place_of_birth, aliases, education, other_sources}` |
| `sanction_matches` | array | Sanctions list entries (e.g. `list_name`, `matched_name`, `reason`, `legal_basis`, `sanction_program`, `sanctioning_authority`, `listed_on`, `source_url`) |
| `warning_matches` | array | Warning and regulatory enforcement entries |
| `adverse_media_matches` | array | Only with `include_adverse_media: true`: `{headline, summary, sentiment, sentiment_score, source_url, thumbnail, country, author_name, publication_date, adverse_keywords, other_sources}` |
| `adverse_media_details` | object | Only with `include_adverse_media: true`: aggregated `sentiment`, `sentiment_score`, `adverse_keywords` |
| `linked_entities` | array | Relationships: `{name, relation, status, details, active}` |
| `risk_view` | object | Per-dimension risk (`crimes`, `countries`, `categories`, `custom_list`), each with `score`, `weightage`, `risk_level`, `risk_scores` |
| `additional_information` | object | Extra context, e.g. a `flag_summary` array |
| `first_seen` / `last_seen` | string | First appearance and latest refresh in the datasets |
| `score_breakdown` | object | `{name,dob,country}_score`, `_weight`, `_weight_normalized`, `_contribution`, `document_number_match_type`, `document_number_effect`, `total_score` (= `match_score`) |

---

## Reviewing Hits

Saved screenings (`save_api_request: true`) and workflow sessions can have their hits reviewed. Both endpoints need an API key with Sessions write (`write:sessions`), fire a `data.updated` webhook and add an entry to the session's review trail. They do not change the session or AML status. Reviewer decisions are kept when ongoing monitoring re-screens. Add `?node_id=<node>` (or `node_id` in the body) only when a workflow session has several AML checks.

**One hit:**

```
PATCH https://verification.didit.me/v3/session/{sessionId}/update-aml-hit-status/
{"hit_id": "hit-001", "review_status": "Confirmed Match"}
-> 200 {"message": "Hit status updated successfully", "hit_id": "hit-001", "review_status": "Confirmed Match"}
```

**Several hits (all-or-nothing):**

```
PATCH https://verification.didit.me/v3/session/{sessionId}/bulk-update-aml-hit-status/
{"hit_updates": [{"hit_id": "hit-001", "review_status": "Confirmed Match"},
                 {"hit_id": "hit-002", "review_status": "False Positive"}]}
-> 200 {"message": "Updated 2 hit(s) successfully", "updated_hits": ["hit-001", "hit-002"]}
```

`review_status`: `Unreviewed`, `Confirmed Match`, `False Positive`, `Inconclusive`. Errors: `400` (empty `hit_id` or `hit_updates`, invalid status), `403` (key, privilege), `404` (session not found, no AML check, or an unknown `hit_id`; in bulk, nothing is changed).

---

## Continuous Monitoring

Off by default. Once on, the profile is re-screened as the watchlists update; a status change fires `status.updated` and a hit change fires `data.updated`. Billed as AML Monitoring ($0.07 per monitored profile per year).

Ways to turn it on:
- `include_ongoing_monitoring: true` on `POST /v3/aml/` (with `save_api_request: true`).
- `is_aml_ongoing_monitoring_enabled` in a workflow's AML feature config, for sessions created from that workflow (see the **didit-verification-management** skill).
- In bulk for existing profiles: `POST /v3/users/aml-monitoring/` or `POST /v3/businesses/aml-monitoring/` (see the **didit-verification-management** skill).

Proof that monitoring ran (per the docs): `GET /v1/session/{sessionId}/aml-screening-history/` lists every completed re-screen, newest first, including runs with `outcome: "NO_CHANGE"`.

---

## Common Workflows

### Basic AML Check

```
1. POST /v3/aml/ -> {"full_name": "Jane Doe", "date_of_birth": "1985-03-15", "nationality": "US"}
2. If "Approved"  -> no credible watchlist match
   If "In Review" -> review hits with review_status "Unreviewed" (datasets, risk_score, score_breakdown)
   If "Declined"  -> block or escalate (only when you lowered aml_score_review_threshold)
3. Record the decision per hit: PATCH /v3/session/{request_id}/update-aml-hit-status/
```

### Comprehensive KYC + AML

```
1. POST /v3/id-verification/ -> read name, date of birth, nationality and document number
2. Convert nationality from ISO alpha-3 (what ID verification returns, e.g. ESP) to alpha-2 (ES):
   /v3/aml/ returns 400 for an alpha-3 code
3. POST /v3/aml/ with all four fields -> more data means fewer False Positives;
   an exact document number match sets match_score to 100
4. Optional: include_ongoing_monitoring=true to keep the profile under monitoring
```

### Safe Retries

```
1. POST /v3/aml/ with header Idempotency-Key: <unique per screening>
2. On timeout or 5xx, resend the same body with the same key -> stored response, no second charge
3. On 409 with Retry-After -> the first request is still running; wait and retry with the same key
```

---

## Utility Scripts

**screen_aml.py**: Screen against AML watchlists from the command line.

```bash
# Requires: pip install requests
export DIDIT_API_KEY="your_api_key"
python scripts/screen_aml.py --name "Jane Doe"
python scripts/screen_aml.py --name "Jane Doe" --dob 1985-03-15 --nationality US --doc-number AB1234567
python scripts/screen_aml.py --name "Acme Energy Ltd" --entity-type company --adverse-media
python scripts/screen_aml.py --name "Jane Doe" --approve-threshold 70 --review-threshold 90 --idempotency-key user-1234-aml
```
