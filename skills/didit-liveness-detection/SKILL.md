---
name: didit-liveness-detection
description: >
  Runs Didit's standalone passive liveness check on a single selfie image
  (POST /v3/passive-liveness/). Use when checking that a person is physically present,
  detecting spoofing or presentation attacks (printed photos, screen replays, masks,
  deepfakes), adding anti-spoofing to a selfie step, or screening a selfie against the
  face blocklist and earlier approved faces. Returns a 0-100 liveness score, an
  Approved/Declined status against a configurable decline threshold, face quality and
  luminance, and blocklist and duplicate-face warnings.
version: 1.3.0
metadata:
  openclaw:
    requires:
      env:
        - DIDIT_API_KEY
    primaryEnv: DIDIT_API_KEY
    emoji: "🧑"
    homepage: https://docs.didit.me
---

# Didit Passive Liveness API

## Overview

Verifies that a user is physically present by analyzing a single captured image. No video, movement or user interaction is required.

**Key constraints:**
- Allowed file extensions: **tiff, jpg, jpeg, png, webp** (no PDF)
- Maximum file size: **5 MB** (images are compressed to about 0.5 MB before processing, so higher resolutions do not improve accuracy)
- One clearly visible face. With several faces the largest one is scored and `MULTIPLE_FACES_DETECTED` is added
- Original real-time capture (no screenshots, prints or photos of screens)

**Pricing:** $0.05 (per successful call; standalone calls have no free tier). These are the list prices until 1 November 2026, when Didit pricing changes and the 500 free checks a month become $10 of free credit a month. Check [didit.me/pricing](https://didit.me/pricing) for current prices.

**Accuracy:** 99.9% liveness detection accuracy, <0.1% false acceptance rate (FAR).

**Decision:** `status` is `Declined` when any `error` warning fires (no face, score at or below the threshold, presentation attack, blocklist hit) and `Approved` otherwise. There is no `In Review` on this endpoint. Only the score threshold is configurable.

**Blocklist and duplicate screening:** runs on **every** call, also with `save_api_request=false`. The face is compared with your application's face search index (your face blocklist and allowlist, faces from approved sessions, faces uploaded to User profiles and retained biometric templates). Earlier faces with the same `vendor_data` are skipped for the duplicate check, so re-verifying the same user does not raise `DUPLICATED_FACE`. A blocklisted face is still caught when it carries the same `vendor_data`. A match on your face allowlist suppresses the duplicate warnings.

**Saving and enrollment (`save_api_request`, default `true`):** the call is saved as an API session (Business Console, `GET /v3/session/{request_id}/decision/`, `status.updated` webhook), the image and face crop are stored, and the face is **enrolled into your face search index** so later Face Search calls and duplicate checks can match it. With `false` nothing is stored, the face is not enrolled and `request_id` cannot be looked up.

**Sandbox:** sandbox API keys return a static `Approved` payload after request validation; nothing is saved or billed.

**Liveness methods:** this endpoint always uses `PASSIVE` (single-frame CNN). Hosted workflows can also use `ACTIVE_3D` (3D Action & Flash, highest security) and `FLASHING` (3D Flash, high security) through the `face_liveness_method` workflow setting.

**API Reference:** https://docs.didit.me/standalone-apis/passive-liveness
**Feature Guide:** https://docs.didit.me/core-technology/liveness/overview

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
POST https://verification.didit.me/v3/passive-liveness/
```

### Headers

| Header | Value | Required |
|---|---|---|
| `x-api-key` | Your API key | **Yes** |
| `Content-Type` | `multipart/form-data` (set by your HTTP client) | **Yes** |

### Request Parameters (multipart/form-data)

| Parameter | Type | Required | Default | Constraints | Description |
|---|---|---|---|---|---|
| `user_image` | file | **Yes** | - | tiff/jpg/jpeg/png/webp, max 5 MB | Front-facing face image (selfie) |
| `face_liveness_score_decline_threshold` | float | No | `30` | 0-100 | A score **at or below** this value raises `LOW_LIVENESS_SCORE` and declines. Raise it for a stricter anti-spoofing posture |
| `rotate_image` | boolean | No | `false` | - | Try 90-degree rotations and use the orientation with the best face detection. Adds latency |
| `save_api_request` | boolean | No | `true` | - | Save as an API session and enroll the face (see Overview) |
| `vendor_data` | string | No | - | - | Your user identifier. Stored, echoed back, and used to skip the same user's earlier faces in the duplicate check |
| `metadata` | JSON object | No | - | JSON-encoded string in multipart | Stored with the session (when saved) and echoed back |

### Example

```python
import json

import requests

with open("selfie.jpg", "rb") as f:
    response = requests.post(
        "https://verification.didit.me/v3/passive-liveness/",
        headers={"x-api-key": "YOUR_API_KEY"},
        files={"user_image": ("selfie.jpg", f, "image/jpeg")},
        data={
            "face_liveness_score_decline_threshold": "50",
            "vendor_data": "user-123",
            "metadata": json.dumps({"flow": "withdrawal"}),
        },
        timeout=60,
    )
response.raise_for_status()
liveness = response.json()["liveness"]
print(liveness["status"], liveness["score"], [w["risk"] for w in liveness["warnings"]])
```

```typescript
const formData = new FormData();
formData.append("user_image", selfieFile);
formData.append("face_liveness_score_decline_threshold", "50");
formData.append("vendor_data", "user-123");
formData.append("metadata", JSON.stringify({ flow: "withdrawal" }));

const response = await fetch("https://verification.didit.me/v3/passive-liveness/", {
  method: "POST",
  headers: { "x-api-key": "YOUR_API_KEY" },
  body: formData,
});
const { liveness } = await response.json();
```

### Response (200 OK)

```json
{
  "request_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "liveness": {
    "status": "Approved",
    "method": "PASSIVE",
    "score": 95.0,
    "user_image": {
      "entities": [
        {"bbox": [661, 728, 1688, 2188], "confidence": 0.732973, "age": 26.91, "gender": "male"}
      ],
      "best_angle": 0
    },
    "warnings": [],
    "face_quality": 84.21,
    "face_luminance": 50.33
  },
  "vendor_data": "user-123",
  "metadata": {"flow": "withdrawal"},
  "created_at": "2026-06-12T01:04:42.763237+00:00"
}
```

A spoofed or blocklisted face still returns HTTP `200`: always read `liveness.status` and `liveness.warnings`.

### Status Values & Handling

| Status | Meaning | Action |
|---|---|---|
| `"Approved"` | No `error` warning fired | Proceed. Still check `warnings` for `DUPLICATED_FACE` / `POSSIBLE_DUPLICATED_FACE` / `MULTIPLE_FACES_DETECTED` |
| `"Declined"` | At least one `error` warning fired | Read `warnings[].risk`: retake for capture problems, block or review for attacks and blocklist hits |

### Error Responses

| Code | Meaning | Action |
|---|---|---|
| `400` | Invalid request | Read the field errors in the response body |
| `400` | `{"error": "Invalid user image format."}`: allowed extension but the file cannot be decoded | Re-encode the image (JPEG or PNG) and retry |
| `401` | The API key has expired | Rotate it or create a new key in **Developers > API keys** |
| `403` | Missing, wrong or revoked API key; a scoped key without access to this endpoint; a request from outside the key's IP allowlist; or not enough credits | Read the message in `detail` or `error`: fix the `x-api-key` header or the key's access, or top up |
| `429` | Rate limit: 300 POST/PATCH/DELETE and 600 GET requests a minute per key | Wait the `Retry-After` seconds, then retry |

---

## Response Field Reference

| Field | Type | Description |
|---|---|---|
| `request_id` | uuid | Session id when `save_api_request=true` (use with `GET /v3/session/{request_id}/decision/`); otherwise a one-off correlation id |
| `liveness.status` | string | `"Approved"` or `"Declined"` |
| `liveness.method` | string | Always `"PASSIVE"` |
| `liveness.score` | float or null | 0-100 (two decimals), higher means more likely a live person. `null` when the model returned no confidence; a `null` score counts as 0 against the threshold |
| `liveness.user_image.entities[]` | array | One entry per detected face: `bbox` `[x_min, y_min, x_max, y_max]`, `confidence` (0-1), `age`, `gender`. Age and gender are informational and do not affect the decision |
| `liveness.user_image.best_angle` | integer or null | Rotation (degrees) that gave the best detection; non-zero only when `rotate_image=true` corrected it |
| `liveness.warnings[]` | array | `{risk, feature, additional_data, log_type, short_description, long_description}`. `feature` is always `LIVENESS` |
| `liveness.face_quality` | float or null | Capture quality of the face, 0-100. `null` when no reliable value |
| `liveness.face_luminance` | float or null | Brightness of the face, 0-100. `null` when unavailable |
| `vendor_data` | string or null | Echo of what you sent |
| `metadata` | object or null | Echo of what you sent |
| `created_at` | string | ISO 8601 UTC time of the response |

---

## Warning Tags

| Tag | Severity | Declines | When it fires |
|---|---|---|---|
| `NO_FACE_DETECTED` | `error` | Yes | The liveness model found no face |
| `LOW_LIVENESS_SCORE` | `error` | Yes | `score` at or below `face_liveness_score_decline_threshold`. Not raised together with `NO_FACE_DETECTED` |
| `LIVENESS_FACE_ATTACK` | `error` | Yes | Presentation attack detected (print, screen replay, mask, deepfake) |
| `FACE_IN_BLOCKLIST` | `error` | Yes | Strong match with a face on your face blocklist. `additional_data` includes `blocklisted_session_id`, `blocklisted_session_number`, `api_service` |
| `POSSIBLE_FACE_IN_BLOCKLIST` | `error` | Yes | Weaker match with a blocklisted face. This endpoint declines it (workflows send it to review) |
| `MULTIPLE_FACES_DETECTED` | `warning` | No | More than one face; the largest one was scored |
| `DUPLICATED_FACE` | `information` | No | Strong match with a face from another approved session (or an imported face or retained template). `additional_data` includes `duplicated_session_id`, `duplicated_session_number`, `api_service` |
| `POSSIBLE_DUPLICATED_FACE` | `information` | No | Weaker match of the same kind |

- `LOW_FACE_QUALITY`, `LOW_FACE_LUMINANCE` and `HIGH_FACE_LUMINANCE` are **never** raised by this endpoint (they are workflow warnings). Apply your own rule to `face_quality` / `face_luminance` if you need one.
- Base decisions on `status` and `warnings[].risk`. The severities above are this endpoint's rules; treat the `log_type` echoed on each warning as informational.

---

## Common Workflows

### Basic Liveness Check

```
1. Capture the user's selfie
2. POST /v3/passive-liveness/ with user_image and vendor_data=<your user id>
3. "Approved" -> the user is live, proceed
   "Declined" -> check warnings[].risk:
     NO_FACE_DETECTED / LOW_LIVENESS_SCORE -> ask for a retake: one well-lit, centered face
     LIVENESS_FACE_ATTACK                  -> suspected spoof, do not approve
     FACE_IN_BLOCKLIST / POSSIBLE_FACE_IN_BLOCKLIST -> block or send to manual review
4. "Approved" with DUPLICATED_FACE -> this face already passed under another vendor_data:
   look up additional_data.duplicated_session_id before creating a new account
```

### Liveness + Face Match (combined)

```
1. POST /v3/passive-liveness/ -> verify the selfie is live
2. If Approved -> POST /v3/face-match/ with user_image=selfie, ref_image=ID portrait
3. Both Approved -> the live person matches the document photo
```

Need a ranked list of every similar face rather than a blocklist/duplicate verdict? Use the **didit-face-search** skill, and run it before saving the same selfie here (a saved liveness face is itself searchable).

---

## Utility Scripts

```bash
export DIDIT_API_KEY="your_api_key"

python scripts/check_liveness.py selfie.jpg
python scripts/check_liveness.py selfie.jpg --threshold 50 --vendor-data user-123
python scripts/check_liveness.py selfie.jpg --rotate --no-save --metadata '{"flow": "withdrawal"}'
```
