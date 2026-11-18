---
name: didit-face-search
description: >
  Runs a 1:N face search with Didit's standalone Face Search API (POST /v3/face-search/)
  against every face enrolled in the application: verification sessions, saved standalone
  calls, faces uploaded to User profiles, face lists and retained biometric templates.
  Use when detecting duplicate accounts, checking whether a face already exists, preventing
  repeat registrations, screening a face against the face blocklist, or investigating
  fraud rings. Returns up to 5 ranked matches with similarity percentages, match source and
  session details, plus blocklist and duplicate-face warnings.
version: 1.3.0
metadata:
  openclaw:
    requires:
      env:
        - DIDIT_API_KEY
    primaryEnv: DIDIT_API_KEY
    emoji: "🔍"
    homepage: https://docs.didit.me
---

# Didit Face Search API (1:N)

## Overview

Searches the largest face in an image against your application's face search index and returns up to **5** ranked matches above the similarity floor, plus blocklist and duplicate warnings.

**What is searched:** faces enrolled from verification sessions of any status, saved standalone calls (e.g. Passive Liveness or Age Estimation with `save_api_request=true`), faces uploaded directly to User profiles, faces on your lists (blocklist, allowlist), and image-free biometric templates you chose to retain on a User. Faces enrolled by earlier Face Search calls are never returned, so repeated searches do not match each other.

**Search modes (`search_type`):**
- `most_similar` (default): ranks every enrolled face by similarity. Use for deduplication and fraud-ring investigation.
- `blocklisted_or_approved`: only blocklisted faces, allowlisted faces, faces from approved sessions, imported User faces and retained templates, with blocklisted entries ranked first. Use for blocklist screening.

**Key constraints:**
- Allowed file extensions: **tiff, jpg, jpeg, png, webp** (no PDF)
- Maximum file size: **5 MB** (images are compressed to about 0.5 MB before processing)
- The image must contain a detectable face, otherwise HTTP `400` `{"error": "No face detected in the image"}`
- With several faces the largest one is searched and `MULTIPLE_FACES_DETECTED` is added
- `vendor_data` does **not** exclude the same user's earlier faces from the results (unlike Passive Liveness)

**Pricing:** $0.05 (per successful call; standalone calls have no free tier). These are the list prices until 1 November 2026, when Didit pricing changes and the 500 free checks a month become $10 of free credit a month. Check [didit.me/pricing](https://didit.me/pricing) for current prices.

**Decision:** `Declined` only when `FACE_IN_BLOCKLIST` or `POSSIBLE_FACE_IN_BLOCKLIST` fires; otherwise `Approved`. Duplicate and multiple-face warnings never decline, and there is no `In Review`. `Approved` does **not** mean the face is new: check `total_matches` and the duplicate warnings. This endpoint returns no liveness verdict (use **didit-liveness-detection** for that).

**Saving and enrollment (`save_api_request`, default `true`):** the call is saved as an API session (Business Console, `GET /v3/session/{request_id}/decision/`, `status.updated` webhook), `match_image_url` values are presigned URLs, and the searched face is enrolled into the index (but never returned by later searches). With `false` nothing is stored, the face is not enrolled, and `match_image_url` values are internal storage paths that cannot be downloaded.

**Similarity guidance:** the Face Search docs read 90%+ as a strong likelihood of the same person and 70-89% as a possible match that may need review. Didit's own verdict is the warning: `DUPLICATED_FACE` / `FACE_IN_BLOCKLIST` for strong matches, `POSSIBLE_DUPLICATED_FACE` / `POSSIBLE_FACE_IN_BLOCKLIST` for weaker ones.

**Sandbox:** sandbox API keys return a static `Approved` payload after request validation; nothing is saved or billed.

**API Reference:** https://docs.didit.me/standalone-apis/face-search
**Feature Guide:** https://docs.didit.me/core-technology/face-search/overview

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
POST https://verification.didit.me/v3/face-search/
```

### Headers

| Header | Value | Required |
|---|---|---|
| `x-api-key` | Your API key | **Yes** |
| `Content-Type` | `multipart/form-data` (set by your HTTP client) | **Yes** |

### Request Parameters (multipart/form-data)

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `user_image` | file | **Yes** | - | Face image to search (tiff/jpg/jpeg/png/webp, max 5 MB) |
| `search_type` | string | No | `most_similar` | `most_similar` or `blocklisted_or_approved` (see Overview) |
| `rotate_image` | boolean | No | `false` | Try 90-degree rotations and use the orientation with the best face detection. Adds latency |
| `save_api_request` | boolean | No | `true` | Save as an API session and enroll the searched face (see Overview) |
| `vendor_data` | string | No | - | Your user identifier, stored and echoed back. Does not filter results |
| `metadata` | JSON object | No | - | Stored with the session (when saved) and echoed back. Send as a JSON-encoded string in multipart |

### Example

```python
import requests

with open("photo.jpg", "rb") as f:
    response = requests.post(
        "https://verification.didit.me/v3/face-search/",
        headers={"x-api-key": "YOUR_API_KEY"},
        files={"user_image": ("photo.jpg", f, "image/jpeg")},
        data={"search_type": "most_similar", "vendor_data": "user-123"},
        timeout=60,
    )
response.raise_for_status()
result = response.json()["face_search"]
for match in result["matches"]:
    print(match["similarity_percentage"], match["source"], match["session_id"], match["is_blocklisted"])
```

```typescript
const formData = new FormData();
formData.append("user_image", photoFile);
formData.append("search_type", "most_similar");

const response = await fetch("https://verification.didit.me/v3/face-search/", {
  method: "POST",
  headers: { "x-api-key": "YOUR_API_KEY" },
  body: formData,
});
const { face_search } = await response.json();
```

### Response (200 OK)

```json
{
  "request_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "face_search": {
    "status": "Approved",
    "total_matches": 1,
    "matches": [
      {
        "session_id": "882c42d5-8a4d-4d20-8080-a22f57822c86",
        "session_number": 323442,
        "similarity_percentage": 97.31,
        "source": "session",
        "vendor_data": "user-1",
        "vendor_user_id": "2f7c1a9e-4b28-4a6d-97f1-83576f80e1b4",
        "biometric_template_id": null,
        "verification_date": "2025-01-01T00:00:00Z",
        "user_details": {
          "full_name": "Jane Doe",
          "document_type": "ID",
          "document_number": "X1234567"
        },
        "match_image_url": "https://<media-host>/face/3f6a1c2e/reference.jpg",
        "status": "Approved",
        "is_blocklisted": false,
        "is_allowlisted": false,
        "api_service": null
      }
    ],
    "user_image": {
      "entities": [
        {"bbox": [40, 40, 120, 120], "confidence": 0.732973}
      ],
      "best_angle": 0
    },
    "warnings": [
      {
        "risk": "DUPLICATED_FACE",
        "feature": "LIVENESS",
        "additional_data": {
          "duplicated_session_id": "882c42d5-8a4d-4d20-8080-a22f57822c86",
          "duplicated_session_number": 323442,
          "api_service": null
        },
        "log_type": "information",
        "short_description": "Duplicated face from other approved session",
        "long_description": "The system identified a duplicated face from another approved session, requiring further investigation."
      }
    ]
  },
  "vendor_data": "user-123",
  "metadata": null,
  "created_at": "2026-06-12T01:04:42.763237+00:00"
}
```

### Status Values & Handling

| Status | Meaning | Action |
|---|---|---|
| `"Approved"` | No blocklist hit | Check `total_matches` and `DUPLICATED_FACE` / `POSSIBLE_DUPLICATED_FACE` before treating the user as new |
| `"Declined"` | `FACE_IN_BLOCKLIST` or `POSSIBLE_FACE_IN_BLOCKLIST` fired | Block or review; see `matches[].is_blocklisted` and the warning's `additional_data` |

### Error Responses

| Code | Meaning | Action |
|---|---|---|
| `400` | Invalid request | Read the field errors in the response body |
| `400` | `{"error": "No face detected in the image"}` | Ask for a new image with one clear, front-facing face (or retry with `rotate_image=true`) |
| `401` | The API key has expired | Rotate it or create a new key in **Developers > API keys** |
| `403` | Missing, wrong or revoked API key; a scoped key without access to this endpoint; a request from outside the key's IP allowlist; or not enough credits | Read the message in `detail` or `error`: fix the `x-api-key` header or the key's access, or top up |
| `429` | Rate limit: 300 POST/PATCH/DELETE and 600 GET requests a minute per key | Wait the `Retry-After` seconds, then retry |

---

## Response Field Reference

### Top level

| Field | Type | Description |
|---|---|---|
| `request_id` | uuid | Session id when `save_api_request=true` (use with `GET /v3/session/{request_id}/decision/`); otherwise a one-off correlation id |
| `face_search.status` | string | `"Approved"` or `"Declined"` |
| `face_search.total_matches` | integer | Number of entries in `matches` (0 to 5) |
| `face_search.matches[]` | array | Up to 5 matches, ordered by similarity (blocklisted first with `blocklisted_or_approved`). Empty when nothing is similar enough |
| `face_search.user_image.entities[]` | array | One entry per detected face, with only `bbox` `[x_min, y_min, x_max, y_max]` and `confidence` (0-1) |
| `face_search.user_image.best_angle` | integer | Rotation (degrees) that gave the best detection; `0` unless `rotate_image=true` corrected it |
| `face_search.warnings[]` | array | `{risk, feature, additional_data, log_type, short_description, long_description}`. `feature` is always `LIVENESS` |
| `vendor_data` / `metadata` | string / object or null | Echo of what you sent |
| `created_at` | string | ISO 8601 UTC time of the response |

### Match Object

| Field | Type | Description |
|---|---|---|
| `similarity_percentage` | float | 0-100 similarity between your face and the matched face |
| `source` | string | `session` (verification session or saved standalone call), `imported` (face uploaded to a User profile), `list_entry` (face on one of your lists), `retained_template` (retained image-free template, see `/v3/biometric-templates/`) |
| `session_id` | uuid or null | Matched session. `null` for `imported` and `retained_template`; for `list_entry` the session the entry was taken from, if any |
| `session_number` | integer or null | Session number shown in the Business Console, same rule as `session_id` |
| `vendor_data` | string or null | `vendor_data` of the matched session, or of the linked User for `imported` / `retained_template` |
| `vendor_user_id` | uuid or null | Linked User id. `null` for list entries and sessions without a User |
| `biometric_template_id` | uuid or null | Set only for `retained_template` |
| `verification_date` | string or null | When the matched face was captured (`YYYY-MM-DDThh:mm:ssZ`). `null` for `list_entry` |
| `user_details` | object or null | `{full_name, document_type, document_number}` from the matched session's document verification. `imported` matches carry only `full_name`. `null` when there is no identity data (e.g. liveness-only sessions) and for `retained_template` |
| `match_image_url` | string or null | Time-limited URL of the matched face (4 hours by default) when `save_api_request=true`; an internal storage path when `false`; `null` for `retained_template` |
| `status` | string or null | Status of the matched session (`Approved`, `Declined`, `In Review`, ...). `null` for non-session matches |
| `is_blocklisted` | boolean | Matched face is on your face blocklist |
| `is_allowlisted` | boolean | Matched face is on one of your allowlists. An allowlisted match suppresses the duplicate warnings |
| `api_service` | string or null | Set when the matched face came from a standalone API call (e.g. `PASSIVE_LIVENESS`) |

---

## Warning Tags

| Tag | Severity | Declines | When it fires |
|---|---|---|---|
| `FACE_IN_BLOCKLIST` | `error` | Yes | Strong match with a blocklisted face. `additional_data` includes `blocklisted_session_id`, `blocklisted_session_number`, `api_service` |
| `POSSIBLE_FACE_IN_BLOCKLIST` | `error` | Yes | Weaker match with a blocklisted face |
| `MULTIPLE_FACES_DETECTED` | `warning` | No | More than one face; the largest one was searched |
| `DUPLICATED_FACE` | `information` | No | Strong match with a face from an approved session, an imported face or a retained template. Not raised when `FACE_IN_BLOCKLIST` is. `additional_data` includes `duplicated_session_id`, `duplicated_session_number`, `api_service` |
| `POSSIBLE_DUPLICATED_FACE` | `information` | No | Weaker match of the same kind. Not raised when `POSSIBLE_FACE_IN_BLOCKLIST` is |

- There is no `NO_FACE_DETECTED` warning: an image without a face returns HTTP `400`.
- Base decisions on `status`, `warnings[].risk` and `matches[]`; treat the `log_type` echoed on each warning as informational.
- Manage the face blocklist and allowlists with the Lists API (see **didit-verification-management**).

---

## Common Workflows

### Duplicate Account Detection

```
1. New user signs up -> POST /v3/face-search/ with the selfie (search_type=most_similar)
2. status "Declined" -> blocklisted face: reject or send to manual review
3. DUPLICATED_FACE / POSSIBLE_DUPLICATED_FACE -> the face already passed on another account:
   compare matches[].vendor_data / vendor_user_id with the current user, then investigate
4. total_matches == 0 -> no similar face is enrolled
```

### Blocklist Screening Only

```
1. POST /v3/face-search/ with search_type=blocklisted_or_approved
2. "Declined" -> blocklist hit (matches[] lists blocklisted entries first)
```

### Combined Verification + Dedup

```
1. POST /v3/face-search/ -> check for existing accounts (run it BEFORE any call that saves this selfie)
2. POST /v3/passive-liveness/ -> verify the user is live (also enrolls the face when saved)
3. POST /v3/id-verification/ -> verify the identity document
4. POST /v3/face-match/ -> compare the selfie to the document portrait
5. All Approved and no duplicate warning -> verified, unique, real user
```

Run the search first: a selfie already saved by Passive Liveness or Age Estimation is in the index and comes back as a near-100% match whose `api_service` names that standalone API (e.g. `PASSIVE_LIVENESS`).

> **Security:** match image URLs expire (4 hours by default). Store only `request_id`, `session_id` and `similarity_percentage`; keep biometric images off your servers.

---

## Utility Scripts

**search_faces.py**: Search for matching faces from the command line.

```bash
# Requires: pip install requests
export DIDIT_API_KEY="your_api_key"
python scripts/search_faces.py selfie.jpg
python scripts/search_faces.py photo.png --search-type blocklisted_or_approved
python scripts/search_faces.py photo.png --rotate --vendor-data user-123 --no-save
```
