---
name: didit-face-match
description: >
  Compares two face images 1:1 with Didit's standalone Face Match API (POST /v3/face-match/).
  Use when checking that a selfie matches an ID document portrait or a previously enrolled
  photo, verifying that two photos show the same person, or adding selfie-to-document
  biometric comparison. Returns a 0-100 similarity score and an Approved/Declined status
  against a configurable decline threshold (default 30), with optional image rotation.
  Does not enroll faces or run blocklist or duplicate checks.
version: 1.5.0
metadata:
  openclaw:
    requires:
      env:
        - DIDIT_API_KEY
    primaryEnv: DIDIT_API_KEY
    emoji: "👥"
    homepage: https://docs.didit.me
---

# Didit Face Match API

## Overview

Compares two facial images to determine whether they show the same person. Returns a similarity score (0-100) and an `Approved` / `Declined` status.

**Key constraints:**
- Allowed file extensions: **tiff, jpg, jpeg, png, webp** (no PDF)
- Maximum file size: **5 MB** per image (images are compressed to about 0.5 MB before processing)
- Both `user_image` and `ref_image` are **required**
- Submit one clear, front-facing, well-lit face per image for best results

**Pricing:** $0.05 (per successful call; standalone calls have no free tier). These are the list prices until 1 November 2026, when Didit pricing changes and the 500 free checks a month become $10 of free credit a month. Check [didit.me/pricing](https://didit.me/pricing) for current prices.

**Decision:** `Approved` only when the score is **strictly above** `face_match_score_decline_threshold` (default `30`). A score at or below it returns `Declined` with `LOW_FACE_MATCH_SIMILARITY`. If no face pair can be scored, the call still returns HTTP `200` with `Declined` and `NO_REFERENCE_IMAGE`. There is no `In Review` on this endpoint; only the threshold is configurable.

**Face search index:** this endpoint **never** enrolls faces and never runs blocklist or duplicate screening. Use `POST /v3/passive-liveness/` (**didit-liveness-detection**) or `POST /v3/face-search/` (**didit-face-search**) for those.

**Saving (`save_api_request`, default `true`):** the call is saved as an API session (Business Console, `GET /v3/session/{request_id}/decision/`, `status.updated` webhook) and both images are stored as the session's face-match source and target images. With `false` nothing is stored and `request_id` cannot be looked up.

**Sandbox:** sandbox API keys return a static `Approved` payload after request validation; nothing is saved or billed.

**Capabilities:** similarity scoring, configurable decline threshold, face bounding boxes with model-estimated age and gender per face (informational), optional rotation for non-upright faces.

**API Reference:** https://docs.didit.me/standalone-apis/face-match
**Feature Guide:** https://docs.didit.me/core-technology/face-match/overview

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
POST https://verification.didit.me/v3/face-match/
```

### Headers

| Header | Value | Required |
|---|---|---|
| `x-api-key` | Your API key | **Yes** |
| `Content-Type` | `multipart/form-data` (set by your HTTP client) | **Yes** |

### Request Parameters (multipart/form-data)

| Parameter | Type | Required | Default | Constraints | Description |
|---|---|---|---|---|---|
| `user_image` | file | **Yes** | - | tiff/jpg/jpeg/png/webp, max 5 MB | Face to verify (e.g. a selfie) |
| `ref_image` | file | **Yes** | - | Same as above | Reference face (e.g. an ID document portrait or an enrolled photo) |
| `face_match_score_decline_threshold` | float | No | `30` | 0-100 | A score **at or below** this value declines with `LOW_FACE_MATCH_SIMILARITY`; strictly above approves |
| `rotate_image` | boolean | No | `false` | - | Try both images at 0/90/180/270 degrees and use the orientation with the best face detection. Adds latency |
| `save_api_request` | boolean | No | `true` | - | Save as an API session and store both images (see Overview) |
| `vendor_data` | string | No | - | - | Your user identifier, stored and echoed back |
| `metadata` | JSON object | No | - | JSON-encoded string in multipart | Stored with the session (when saved) and echoed back |

### Example

```python
import requests

with open("selfie.jpg", "rb") as selfie, open("id_photo.jpg", "rb") as portrait:
    response = requests.post(
        "https://verification.didit.me/v3/face-match/",
        headers={"x-api-key": "YOUR_API_KEY"},
        files={
            "user_image": ("selfie.jpg", selfie, "image/jpeg"),
            "ref_image": ("id_photo.jpg", portrait, "image/jpeg"),
        },
        data={"face_match_score_decline_threshold": "50", "vendor_data": "user-123"},
        timeout=60,
    )
response.raise_for_status()
face_match = response.json()["face_match"]
print(face_match["status"], face_match["score"])
```

```typescript
const formData = new FormData();
formData.append("user_image", selfieFile);
formData.append("ref_image", referenceFile);
formData.append("face_match_score_decline_threshold", "50");
formData.append("vendor_data", "user-123");

const response = await fetch("https://verification.didit.me/v3/face-match/", {
  method: "POST",
  headers: { "x-api-key": "YOUR_API_KEY" },
  body: formData,
});
const { face_match } = await response.json();
```

### Response (200 OK)

```json
{
  "request_id": "f9f5a777-8002-44c6-baaf-128bcfd6e226",
  "face_match": {
    "status": "Approved",
    "score": 99.41,
    "user_image": {
      "entities": [
        {"bbox": [661, 728, 1688, 2188], "confidence": 0.732973, "age": 26.91, "gender": "male"}
      ],
      "best_angle": 0
    },
    "ref_image": {
      "entities": [
        {"bbox": [653, 745, 1691, 2185], "confidence": 0.722082, "age": 27.0, "gender": "male"}
      ],
      "best_angle": 0
    },
    "warnings": []
  },
  "vendor_data": "user-123",
  "metadata": null,
  "created_at": "2026-06-12T01:04:42.763237+00:00"
}
```

### Status Values & Handling

| Status | Meaning | Action |
|---|---|---|
| `"Approved"` | Score strictly above the threshold | Faces match, proceed |
| `"Declined"` | Score at or below the threshold (`LOW_FACE_MATCH_SIMILARITY`), or no face pair could be scored (`NO_REFERENCE_IMAGE`) | Check `warnings`. For `NO_REFERENCE_IMAGE` ask for clearer images (try `rotate_image=true` for sideways captures) |

### Error Responses

| Code | Meaning | Action |
|---|---|---|
| `400` | Invalid request (missing image, file over 5 MB, unsupported extension, threshold outside 0-100) | Read the field errors in the response body |
| `401` | The API key has expired | Rotate it or create a new key in **Developers > API keys** |
| `403` | Missing, wrong or revoked API key; a scoped key without access to this endpoint; a request from outside the key's IP allowlist; or not enough credits | Read the message in `detail` or `error`: fix the `x-api-key` header or the key's access, or top up |
| `429` | Rate limit: 300 POST/PATCH/DELETE and 600 GET requests a minute per key | Wait the `Retry-After` seconds, then retry |

---

## Response Field Reference

| Field | Type | Description |
|---|---|---|
| `request_id` | uuid | Session id when `save_api_request=true` (use with `GET /v3/session/{request_id}/decision/`); otherwise a one-off correlation id |
| `face_match.status` | string | `"Approved"` or `"Declined"` |
| `face_match.score` | float or null | 0-100 similarity (higher = more similar). Rounded to 2 decimals when saved; raw float with `save_api_request=false`. When no face pair could be scored it is `null` (saved) or `0` (not saved), always with `NO_REFERENCE_IMAGE` |
| `face_match.user_image.entities[]` | array | One entry per detected face: `bbox` `[x_min, y_min, x_max, y_max]`, `confidence` (0-1), `age`, `gender`. Age and gender are informational and do not affect the decision |
| `face_match.user_image.best_angle` | integer | Rotation (0, 90, 180, 270) that gave the best detection; non-zero only when `rotate_image=true` corrected it |
| `face_match.ref_image` | object | Same shape as `user_image`, for the reference image |
| `face_match.warnings[]` | array | `{risk, feature, additional_data, log_type, short_description, long_description}`. `feature` is always `FACEMATCH`, `additional_data` is always `null` |
| `vendor_data` | string or null | Echo of what you sent |
| `metadata` | object or null | Echo of what you sent |
| `created_at` | string | ISO 8601 UTC time of the response |

---

## Warning Tags

| Tag | Severity | Declines | When it fires |
|---|---|---|---|
| `NO_REFERENCE_IMAGE` | `error` | Yes | No face pair could be scored (for example, no usable face in one of the images) |
| `LOW_FACE_MATCH_SIMILARITY` | `error` | Yes | Score at or below `face_match_score_decline_threshold` |

`NO_FACE_DETECTED` is never raised by this endpoint: a missing face surfaces as `NO_REFERENCE_IMAGE`.

> **Security best practice:** store only `status`, `score` and `request_id`. With `save_api_request=true` the stored images are available from the session decision as time-limited URLs (4 hours by default), so you do not need to keep biometric images on your servers.

---

## Choosing a Threshold

- The default `30` is permissive. Raise it (for example `50` to `60`) for stricter verification; values outside 0-100 return `400`.
- The comparison is "strictly above approves": with threshold `50`, a score of `50.0` declines.
- The standalone endpoint has only a decline threshold. Hosted workflows (`FACE_MATCH` feature) add a separate `face_match_score_review_threshold` that sends scores between the two thresholds to `In Review`.
- Log `score` alongside your own outcomes and tune the threshold to your false-match tolerance.

---

## Common Workflows

### Selfie vs ID Document

```
1. POST /v3/passive-liveness/ with the selfie -> confirm it is live (didit-liveness-detection)
2. POST /v3/id-verification/ with the document -> extract and check it (didit-id-document-verification)
3. POST /v3/face-match/ with user_image=selfie, ref_image=document portrait
4. All Approved -> the live person matches the document
```

For a hosted flow that does all three in one session, use a workflow with `OCR`, `LIVENESS` and `FACE_MATCH` (see the **didit-kyc-onboarding** skill).

---

## Utility Scripts

```bash
export DIDIT_API_KEY="your_api_key"

python scripts/match_faces.py selfie.jpg id_photo.jpg
python scripts/match_faces.py selfie.jpg id_photo.jpg --threshold 50 --rotate --vendor-data user-123
python scripts/match_faces.py selfie.jpg id_photo.jpg --no-save --metadata '{"flow": "login"}'
```
