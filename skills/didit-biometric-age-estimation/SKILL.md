---
name: didit-biometric-age-estimation
description: >
  Estimates a person's age from one selfie with Didit's standalone Age Estimation API
  (POST /v3/age-estimation/), which also runs a passive liveness check in the same call.
  Use when implementing an age gate, checking whether someone looks over 18 or 21, detecting
  underage users, or adding low-friction age assurance. Returns the estimated age, a liveness
  score and an Approved/Declined status against configurable age and liveness thresholds.
  Also covers the AGE_ESTIMATION workflow feature, where borderline ages fall back to ID
  verification and per-country age limits apply.
version: 1.2.0
metadata:
  openclaw:
    requires:
      env:
        - DIDIT_API_KEY
    primaryEnv: DIDIT_API_KEY
    emoji: "🎂"
    homepage: https://docs.didit.me
---

# Didit Age Estimation API

## Overview

Estimates a person's age from a facial image and runs a passive liveness check in the same call to block spoofs. The age is **model-predicted from the face, not verified against a document**: use it for age gates and low-friction checks, not as legal proof of age.

**Key constraints:**
- Allowed file extensions: **tiff, jpg, jpeg, png, webp** (no PDF)
- Maximum file size: **5 MB** (images are compressed to about 0.3 MB before processing)
- One clear, front-facing, well-lit face. The **largest** detected face drives `age_estimation`
- Accuracy: mean absolute error (MAE) 3.5 years overall; 1.5 years for under-18 (see the table below)

**Pricing:** $0.10 (per successful call; standalone calls have no free tier). These are the list prices until 1 November 2026, when Didit pricing changes and the 500 free checks a month become $10 of free credit a month. Check [didit.me/pricing](https://didit.me/pricing) for current prices.

**Decision:** **any** warning declines. `status` is `Approved` only when `warnings` is empty. There is no `In Review` on this endpoint. `method` is always `PASSIVE`.

**Not on this endpoint:** blocklist and duplicate-face screening, `MULTIPLE_FACES_DETECTED`, the ID verification fallback for borderline ages and per-country age limits. Those are workflow features (see [Adaptive Age Estimation](#adaptive-age-estimation-workflow-mode)).

**Saving (`save_api_request`, default `true`):** the call is saved as an API session (Business Console, `status.updated` webhook, and `GET /v3/session/{request_id}/decision/`, where the result appears in `liveness_checks[]` with `features: ["AGE_ESTIMATION"]`), the face crop and reference image are stored, and the face is added to your application's face search index (used by Face Search and duplicate detection). With `false` nothing is stored and `request_id` cannot be looked up.

**Sandbox:** sandbox API keys return a static `Approved` payload (`age_estimation: 30`, no warnings) after request validation; nothing is saved or billed.

**API Reference:** https://docs.didit.me/standalone-apis/age-estimation
**Feature Guide:** https://docs.didit.me/core-technology/age-estimation/overview

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
POST https://verification.didit.me/v3/age-estimation/
```

### Headers

| Header | Value | Required |
|---|---|---|
| `x-api-key` | Your API key | **Yes** |
| `Content-Type` | `multipart/form-data` (set by your HTTP client) | **Yes** |

### Request Parameters (multipart/form-data)

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `user_image` | file | **Yes** | - | Facial image (tiff/jpg/jpeg/png/webp, max 5 MB) |
| `age_estimation_decline_threshold` | integer | No | `18` | 0-100. An estimated age **strictly below** this value raises `AGE_BELOW_MINIMUM` and declines. `0` disables the age check |
| `face_liveness_score_decline_threshold` | float | No | `30` | 0-100. A liveness `score` **at or below** this value raises `LOW_LIVENESS_SCORE` and declines |
| `rotate_image` | boolean | No | `false` | Try 0/90/180/270 degrees and use the orientation with the best face detection. Adds latency |
| `save_api_request` | boolean | No | `true` | Save as an API session and add the face to the face search index (see Overview) |
| `vendor_data` | string | No | - | Your user identifier, stored and echoed back |
| `metadata` | JSON object | No | - | Stored with the session (when saved) and echoed back. Send as a JSON-encoded string in multipart |

### Example

```python
import requests

with open("selfie.jpg", "rb") as f:
    response = requests.post(
        "https://verification.didit.me/v3/age-estimation/",
        headers={"x-api-key": "YOUR_API_KEY"},
        files={"user_image": ("selfie.jpg", f, "image/jpeg")},
        data={"age_estimation_decline_threshold": "21", "vendor_data": "user-123"},
        timeout=60,
    )
response.raise_for_status()
result = response.json()["age_estimation"]
print(result["status"], result["age_estimation"], result["score"])
```

```typescript
const formData = new FormData();
formData.append("user_image", selfieFile);
formData.append("age_estimation_decline_threshold", "21");
formData.append("vendor_data", "user-123");

const response = await fetch("https://verification.didit.me/v3/age-estimation/", {
  method: "POST",
  headers: { "x-api-key": "YOUR_API_KEY" },
  body: formData,
});
const { age_estimation } = await response.json();
```

### Response (200 OK)

```json
{
  "request_id": "0c40ba43-64ab-4e2e-b4b8-7d1f12f81bc1",
  "age_estimation": {
    "status": "Approved",
    "method": "PASSIVE",
    "score": 97.5,
    "user_image": {
      "entities": [
        {"age": 27.33, "bbox": [40, 40, 100, 100], "confidence": 0.7177750468254089, "gender": "male"}
      ],
      "best_angle": 0
    },
    "age_estimation": 27.33,
    "warnings": []
  },
  "vendor_data": "user-123",
  "metadata": null,
  "created_at": "2026-06-12T02:24:11.512941+00:00"
}
```

The result object and the estimated age share the name: read the age at `age_estimation.age_estimation`.

### Status Values & Handling

| Status | Meaning | Action |
|---|---|---|
| `"Approved"` | No warnings: age at or above the threshold and liveness passed | Proceed with your flow |
| `"Declined"` | At least one warning fired | Read `warnings[].risk` (see Warning Tags) |

### Error Responses

| Code | Meaning | Action |
|---|---|---|
| `400` | Invalid request (missing image, file over 5 MB, unsupported extension, threshold out of range) | Read the field errors in the response body |
| `400` | `{"error": "Invalid user image format."}`: allowed extension but the file cannot be decoded | Re-encode the image (JPEG or PNG) and retry |
| `401` | The API key has expired | Rotate it or create a new key in **Developers > API keys** |
| `403` | Missing, wrong or revoked API key; a scoped key without access to this endpoint; a request from outside the key's IP allowlist; or not enough credits | Read the message in `detail` or `error`: fix the `x-api-key` header or the key's access, or top up |
| `429` | Rate limit: 300 POST/PATCH/DELETE and 600 GET requests a minute per key | Wait the `Retry-After` seconds, then retry |

---

## Response Field Reference

| Field | Type | Description |
|---|---|---|
| `request_id` | uuid | Session id when `save_api_request=true` (use with `GET /v3/session/{request_id}/decision/`); otherwise a one-off correlation id |
| `age_estimation.status` | string | `"Approved"` or `"Declined"` |
| `age_estimation.method` | string | Always `"PASSIVE"` |
| `age_estimation.score` | float or null | Passive liveness score 0-100. `null` when the model returned no confidence; a `null` score counts as 0, so it declines with `LOW_LIVENESS_SCORE` |
| `age_estimation.age_estimation` | float or null | Estimated age in years of the largest face (e.g. `27.33`). `null` when no age could be estimated (`AGE_NOT_DETECTED`) |
| `age_estimation.user_image.entities[]` | array | One entry per detected face: `age`, `bbox` `[x_min, y_min, x_max, y_max]`, `confidence` (0-1), `gender` (informational). Empty when no face was found |
| `age_estimation.user_image.best_angle` | integer or null | Rotation that gave the best detection; non-zero only when `rotate_image=true` corrected it |
| `age_estimation.warnings[]` | array | `{risk, feature, additional_data, log_type, short_description, long_description}`. `feature` is always `LIVENESS`, `additional_data` always `null`, `log_type` always `error` |
| `vendor_data` | string or null | Echo of what you sent |
| `metadata` | object or null | Echo of what you sent |
| `created_at` | string | ISO 8601 UTC time of the response |

### Accuracy by Age Range

| Age Range | MAE (years) | Confidence |
|---|---|---|
| Under 18 | 1.5 | High |
| 18-25 | 2.8 | High |
| 26-40 | 3.2 | High |
| 41-60 | 3.9 | Medium-High |
| 60+ | 4.5 | Medium |

---

## Warning Tags

Every warning on this endpoint is `error` severity and declines the call.

| Tag | When it fires |
|---|---|
| `NO_FACE_DETECTED` | The liveness model found no face |
| `LOW_LIVENESS_SCORE` | Liveness `score` at or below `face_liveness_score_decline_threshold`. Not raised together with `NO_FACE_DETECTED` |
| `LIVENESS_FACE_ATTACK` | Presentation attack detected (photo of a photo, screen, mask) |
| `AGE_NOT_DETECTED` | No face age could be estimated (`age_estimation` is `null`) |
| `AGE_BELOW_MINIMUM` | Estimated age strictly below `age_estimation_decline_threshold`. The unrounded estimate is compared, so `17.9` declines at `18` |

`FACE_IN_BLOCKLIST`, `POSSIBLE_DUPLICATED_FACE` and `MULTIPLE_FACES_DETECTED` are never raised by this endpoint; they only appear in workflow sessions.

---

## Common Workflows

### Basic Age Gate

```
1. Capture the user's selfie
2. POST /v3/age-estimation/ with user_image and age_estimation_decline_threshold=18 (or 21)
3. "Approved" -> estimated age is at or above the threshold and the selfie is live
   "Declined" -> check warnings[].risk:
     AGE_BELOW_MINIMUM                        -> under the threshold (see borderline note below)
     AGE_NOT_DETECTED / NO_FACE_DETECTED      -> ask for a retake: one clear, well-lit face
     LOW_LIVENESS_SCORE / LIVENESS_FACE_ATTACK -> possible spoof, do not approve
4. Read the estimate itself at age_estimation.age_estimation
```

Estimates close to your threshold deserve a document check: send borderline users to ID verification (**didit-id-document-verification**), or use the adaptive workflow below, which does this automatically.

### Adaptive Age Estimation (Workflow Mode)

Workflow-only: the ID verification fallback and per-country limits are **not** available on `POST /v3/age-estimation/`. Create a workflow with the `AGE_ESTIMATION` feature (see **didit-verification-management**) and run users through a hosted session:

1. `POST /v3/workflows/` with a body like:

```json
{
  "workflow_label": "Adaptive Age",
  "features": [
    {
      "feature": "AGE_ESTIMATION",
      "config": {
        "enable_id_verification_fallback": true,
        "minimum_age_threshold": 18,
        "borderline_minimum_age_threshold": 16,
        "borderline_maximum_age_threshold": 25,
        "face_liveness_method": "PASSIVE"
      }
    }
  ]
}
```

2. `POST /v3/session/` with the returned `workflow_id`, send the user to the session URL.
3. The user takes a selfie and the age is estimated (workflows compare the age in whole years):
   - **Fallback on** (`enable_id_verification_fallback: true`): an age below `borderline_minimum_age_threshold` raises `AGE_BELOW_MINIMUM` and declines; ages in the borderline band up to `borderline_maximum_age_threshold`, or an age that cannot be estimated, continue to ID verification; clear passes complete on the selfie.
   - **Fallback off**: no estimated age raises `AGE_NOT_DETECTED`; an age below `minimum_age_threshold` raises `AGE_BELOW_MINIMUM`.
4. When the fallback runs, the document's date of birth is checked against the per-country age limits, and the document portrait is face matched against the age-estimation selfie (reported in `face_matches[]` with the age estimation node as `node_id`, not billed as a separate Face Match).
5. `GET /v3/session/{sessionId}/decision/`: the estimate is in `liveness_checks[].age_estimation`.

Other `AGE_ESTIMATION` config fields: `face_liveness_method` (`ACTIVE_3D` = 3D Action & Flash, highest security; `FLASHING` = 3D Flash, high; `PASSIVE` = single frame, standard), `face_liveness_score_decline_threshold`, `face_liveness_score_review_threshold`. Workflow sessions also run blocklist and duplicate-face screening.

### Per-Country Age Restrictions (Workflow Mode)

Configured in the Business Console per document issuing country (with state/region overrides matched from the document), and applied when the workflow verifies an ID document, including the adaptive fallback. Out-of-range ages can **Decline** or go to **Review**. Example:

| Country | Min Age | Max Age | State Overrides |
|---|---|---|---|
| USA | 18 | - | Mississippi: 21, Alabama: 19 |
| KOR | 19 | - | - |
| GBR | 18 | 65 | - |
| ARE | 21 | - | - |

> Use the "Apply age of majority" button in the Console to fill in each country's legal age of majority, then adjust.

---

## Utility Scripts

**estimate_age.py**: Estimate age from a facial image via the command line. `--threshold` is sent as `age_estimation_decline_threshold`, so the API itself makes the age decision.

```bash
# Requires: pip install requests
export DIDIT_API_KEY="your_api_key"
python scripts/estimate_age.py selfie.jpg
python scripts/estimate_age.py photo.png --threshold 21 --vendor-data user-123
python scripts/estimate_age.py photo.png --liveness-threshold 50 --rotate --no-save
```
