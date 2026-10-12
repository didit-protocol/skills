---
name: didit-case-management
description: >
  Integrate Didit Case Management through the API: open, triage, assign, resolve and audit
  compliance investigation cases, and file FIU regulatory reports. Use when the user wants to
  list or search cases, create a case for a user, business, session or transaction, assign or
  bulk-assign cases, resolve cases as false positive or valid threat, run 4-eyes
  (maker/checker) approval, add notes and attachments, work case checklists, escalate or
  transfer cases, configure case blueprints (review policies), presets, review teams and
  routing rules, pull case analytics and SLA metrics, or create, validate, finalize and
  download goAML SAR/STR reports using Didit. Cases come from AML screening hits,
  transaction rules, workflow builder nodes, or manual creation.
version: 1.0.0
metadata:
  openclaw:
    requires:
      env:
        - DIDIT_API_KEY
    primaryEnv: DIDIT_API_KEY
    emoji: "🗂️"
    homepage: https://docs.didit.me
---

# Didit Case Management API

## Overview

A **case** is a compliance investigation anchored to exactly one subject: one user or one business. Sessions, business sessions and transactions of that same subject can be linked to it. Your team (or your integration) works the case from `OPEN` to `RESOLVED` with a full audit trail, and can file a Financial Intelligence Unit (FIU) report from it.

**Key facts:**
- Lifecycle has three statuses: `OPEN`, `AWAITING_USER`, `RESOLVED`. Resolution is `FALSE_POSITIVE`, `VALID_THREAT`, `INCONCLUSIVE`, `REQUIREMENTS_NOT_MET` or `REQUIREMENTS_SATISFIED`; only `VALID_THREAT` feeds the shared fraud index. Priority is `LOW`, `MEDIUM` (default) or `HIGH`.
- One subject per case. Linking a session, business session or transaction that belongs to another user or business returns `400`.
- A **blueprint** (called a review policy in the console) decides assignment, escalation, transfer, 4-eyes approval, a required resolution note, the checklist and which sections the case page shows.
- Cases are created by four sources: `MANUAL` (console or API), `AML_SCREENING` (ongoing-monitoring hits), `TRANSACTION_RULE` (a rule with the **Create case** effect) and `WORKFLOW_BUILDER` (a **Create case** node). API-created cases are always `MANUAL`.
- Every endpoint is scoped to one organization and one application: `https://verification.didit.me/v3/organization/{organization_id}/application/{application_id}/...`
- Actions taken with an API key have no person attached: `actor_email` and `actor_name` on events and notes, and `resolved_by_email`, are `null`.

**Pricing:** No list price is published for these endpoints; check [didit.me/pricing](https://didit.me/pricing).

**API Reference:** https://docs.didit.me/management-api/cases/list
**Feature guides:** https://docs.didit.me/console/case-management/cases | https://docs.didit.me/console/case-management/blueprints | https://docs.didit.me/console/case-management/four-eyes | https://docs.didit.me/console/case-management/fiu-reports

---

## Authentication

Every request needs the `x-api-key` header. Use your application's API key from the [Didit Business Console](https://business.didit.me) under **Developers > API keys**, or create an account and key programmatically (see Getting Started). Case endpoints need the application's primary key or a named key with full access: a named key with custom access gets `403` `"This API key has no access to this endpoint."`

The key only acts on its own application: `{application_id}` must be the application the key belongs to, otherwise `403` `"You do not have permission to perform this action."`

| Path ID | Where to find it |
|---|---|
| `{organization_id}` | `organization.uuid` in the verify-email response; Business Console > **Organization Settings** > **Organization ID**; or `GET https://apx.didit.me/auth/v2/organizations/me/` with `Authorization: Bearer <access_token>` |
| `{application_id}` | `application.uuid` in the verify-email response; or `GET https://apx.didit.me/auth/v2/organizations/me/{org_id}/applications/` with a Bearer token (each entry's `uuid`) |

## Getting Started (No Account Yet?)

If you don't have a Didit API key, create one in 2 API calls:

1. **Register:** `POST https://apx.didit.me/auth/v2/programmatic/register/` with `{"email": "you@yourdomain.com", "password": "MyStr0ng!Pass"}`
2. **Check email** for a 6-character verification code
3. **Verify:** `POST https://apx.didit.me/auth/v2/programmatic/verify-email/` with `{"email": "you@yourdomain.com", "code": "A3K9F2"}`. The key is in the response at `application.api_key`.

**To add credits:** `GET /v3/billing/balance/` to check, `POST /v3/billing/top-up/` with `{"amount_in_dollars": 50}` for a Stripe checkout link.

See the **didit-verification-management** skill for full platform management (workflows, sessions, users, billing).

The same verify-email response carries `organization.uuid` and `application.uuid`, the two path IDs every case endpoint needs (see Authentication).

---

## Endpoints

All paths below are relative to the base URL:

```
https://verification.didit.me/v3/organization/{organization_id}/application/{application_id}/
```

| Method | Path | Purpose |
|---|---|---|
| `GET` / `POST` | `cases/` | List and search cases / create a case |
| `GET` / `PATCH` / `DELETE` | `cases/{case_uuid}/` | Case detail / update title, priority, due date, tags / delete (`204`) |
| `POST` | `cases/{case_uuid}/assign/` | Assign or unassign |
| `POST` | `cases/{case_uuid}/resolve/` | Resolve, or stage for 4-eyes approval |
| `POST` | `cases/{case_uuid}/approve/` | Approve a staged resolution (4-eyes) |
| `POST` | `cases/{case_uuid}/reject-approval/` | Reject a staged resolution (4-eyes) |
| `POST` | `cases/{case_uuid}/reopen/` | `AWAITING_USER` or `RESOLVED` back to `OPEN` |
| `POST` | `cases/{case_uuid}/request-info/` | `OPEN` to `AWAITING_USER` |
| `POST` | `cases/{case_uuid}/escalate/` | Move to the blueprint's escalation target |
| `POST` | `cases/{case_uuid}/transfer/` | Move to another active blueprint |
| `GET` / `POST` | `cases/{case_uuid}/notes/` | List / add notes |
| `PATCH` / `DELETE` | `cases/{case_uuid}/notes/{note_uuid}/` | Pin or unpin / delete a note |
| `POST` / `GET` | `cases/{case_uuid}/notes/presign/` | Upload an attachment / mint a fresh download URL |
| `GET` / `POST` | `cases/{case_uuid}/links/` | List / attach a session, business session or transaction |
| `DELETE` | `cases/{case_uuid}/links/{link_uuid}/` | Detach a link |
| `GET` | `cases/{case_uuid}/events/` | Audit timeline |
| `GET` | `cases/{case_uuid}/checklist/` | Checklist items |
| `PATCH` | `cases/{case_uuid}/checklist/{item_uuid}/` | Tick or untick an item |
| `GET` | `cases/{case_uuid}/aml/` | AML screening results of the linked sessions |
| `GET` | `cases/{case_uuid}/print/` | Full-case PDF (presigned URL) |
| `POST` | `cases/{case_uuid}/entity-actions/` | Act on the subject (status, tags, note, blocklist) |
| `POST` | `cases/duplicates/` | Find existing cases for a subject before creating one |
| `GET` | `cases/statistics/` | Analytics: trends, breakdowns, SLA, queue depth |
| `POST` | `cases/bulk/status/` | Reopen, request info or resolve many cases |
| `POST` | `cases/bulk/assign/` | Assign or unassign many cases |
| `GET` | `cases/reviewers/` | Members who can be assigned cases |
| `*` | `cases/blueprints/...`, `cases/teams/...`, `cases/routing-rules/...` | Configuration (see Blueprints and Assignment) |
| `*` | `report-templates/...`, `regulatory-reports/...`, `cases/{case_uuid}/regulatory-reports/` | FIU reports (see FIU Reports) |

---

## List Cases

`GET .../cases/`

| Query param | Description |
|---|---|
| `status__in` | Comma-separated: `OPEN,AWAITING_USER,RESOLVED` |
| `priority` | Comma-separated: `LOW,MEDIUM,HIGH` |
| `source__in` | Comma-separated: `MANUAL,AML_SCREENING,TRANSACTION_RULE,WORKFLOW_BUILDER` |
| `blueprint` | Blueprint UUID |
| `assigned_to` | Assignee user UUID |
| `unassigned` | `true` = unassigned only, `false` = assigned only |
| `tag` | Exact tag |
| `search` | Matches title, `case_number`, tag, subject name, subject UUID, subject external ID (`vendor_data`), linked session UUID, linked transaction UUID |
| `date_from`, `date_to` | `YYYY-MM-DD`, inclusive range on `created_at` |
| `due_before` | ISO 8601 datetime, upper bound on `due_at` |
| `overdue` | `true`: only `OPEN`/`AWAITING_USER` cases whose `due_at` has passed |
| `ordering` | `created_at`, `-created_at` (default), `due_at`, `-due_at` (nulls last) |
| `limit`, `offset` | Page size (default 50) and offset |

Response: `{"count", "next", "previous", "results": [CaseListItem]}`. `count` is exact up to 100 and capped at 100 beyond that: page until `next` is `null`, never rely on `count`.

## Create Case

`POST .../cases/` returns `201` with the full case.

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | string | **Yes** | Max 255 chars. The console prefills `Manual - <subject name>` |
| `subject` | object | One of `subject` / `links` | `{"type": "user" or "business", "uuid": "<didit_internal_id>"}`: the `didit_internal_id` from `GET /v3/users/{vendor_data}/` or `GET /v3/businesses/{vendor_data}/` |
| `links` | array | One of `subject` / `links` | `[{"entity_type": "session" or "business_session" or "transaction", "entity_uuid": "<uuid>"}]`. Without `subject`, the subject is derived from the first link's owner |
| `blueprint` | UUID | No | Active blueprint. Seeds the checklist and drives routing, content and resolution rules |
| `priority` | string | No | `LOW`, `MEDIUM` (default), `HIGH` |
| `due_at` | datetime | No | SLA deadline. Without it, the blueprint's `default_deadline_hours` applies if set |
| `tags` | string[] | No | Free-form tags |
| `assigned_to` | UUID | No | Member user UUID from `GET .../cases/reviewers/` |
| `review_duplicates` | boolean | No | Default `false`. When `true`, creation returns `409` if the subject already has cases, unless `separate_incident_reason` is set |
| `separate_incident_reason` | string | No | Max 1000 chars. Why this is a separate incident; saved on the case |

Link IDs: a session's `session_id`, a business session's `session_id`, or a transaction's Didit `uuid` (from `POST /v3/transactions/`).

```python
import os

import requests

BASE = (
    "https://verification.didit.me/v3/organization/"
    f"{os.environ['DIDIT_ORG_ID']}/application/{os.environ['DIDIT_APP_ID']}"
)
HEADERS = {"x-api-key": os.environ["DIDIT_API_KEY"], "Content-Type": "application/json"}

response = requests.post(
    f"{BASE}/cases/",
    headers=HEADERS,
    json={
        "title": "Manual - Jane Doe",
        "priority": "HIGH",
        "subject": {"type": "user", "uuid": "8c0e5a3e-1f7b-4d55-9a0e-6b2f0c7d9e11"},
        "links": [{"entity_type": "transaction", "entity_uuid": "3b9d2c1a-7e4f-4a6b-8c5d-0e1f2a3b4c5d"}],
        "tags": ["review"],
    },
    timeout=30,
)
response.raise_for_status()
case = response.json()
print(case["uuid"], case["case_number"], case["status"])
```

```typescript
const BASE = `https://verification.didit.me/v3/organization/${orgId}/application/${appId}`;

const response = await fetch(`${BASE}/cases/`, {
  method: "POST",
  headers: { "x-api-key": "YOUR_API_KEY", "Content-Type": "application/json" },
  body: JSON.stringify({
    title: "Manual - Jane Doe",
    priority: "HIGH",
    subject: { type: "user", uuid: "8c0e5a3e-1f7b-4d55-9a0e-6b2f0c7d9e11" },
  }),
});
const caseDetail = await response.json();
```

### Response (201 Created)

```json
{
  "uuid": "6f1c2a9e-0b7d-4c3e-9a51-2d8e4f7b1c03",
  "case_number": "CS-0042",
  "title": "Manual - Jane Doe",
  "status": "OPEN",
  "resolution": null,
  "resolution_notes": null,
  "priority": "HIGH",
  "source": "MANUAL",
  "tags": ["review"],
  "subject": {"type": "user", "uuid": "8c0e5a3e-1f7b-4d55-9a0e-6b2f0c7d9e11", "name": "Jane Doe", "external_id": "user-42"},
  "assigned_to": null,
  "assigned_at": null,
  "due_at": null,
  "resolved_at": null,
  "resolved_by_email": null,
  "pending_resolution": null,
  "metadata": {},
  "blueprint": null,
  "notes": [],
  "events": [
    {
      "uuid": "0d4e7c2b-9a1f-4b3c-8e5d-6f7a8b9c0d1e",
      "event_type": "CREATED",
      "actor_email": null,
      "actor_name": null,
      "previous_status": null,
      "new_status": "OPEN",
      "metadata": {},
      "created_at": "2026-10-12T09:30:00Z"
    }
  ],
  "links": [
    {
      "uuid": "5a6b7c8d-9e0f-4a1b-8c2d-3e4f5a6b7c8d",
      "linked_entity_type": "transaction",
      "linked_entity_uuid": "3b9d2c1a-7e4f-4a6b-8c5d-0e1f2a3b4c5d",
      "linked_entity_summary": {"uuid": "3b9d2c1a-7e4f-4a6b-8c5d-0e1f2a3b4c5d", "txn_id": "tx-0001", "status": "IN_REVIEW"},
      "created_at": "2026-10-12T09:30:00Z"
    }
  ],
  "links_count": 1,
  "notes_count": 0,
  "checklist_items": [],
  "created_at": "2026-10-12T09:30:00Z",
  "updated_at": "2026-10-12T09:30:00Z"
}
```

### Duplicate review before creating

`POST .../cases/duplicates/` with `{"subject": {"type": "user", "uuid": "..."}}` or `{"links": [...]}` (optional `offset`) returns `{"count", "next_offset", "results": [{uuid, case_number, title, status, priority, created_at}]}`, open and resolved cases, at most 20 per page. Then create with `review_duplicates: true` (and `separate_incident_reason` when you still want a new case).

## Get, Update, Delete

- `GET .../cases/{case_uuid}/`: full case (CaseDetail), with the newest 50 notes, newest 100 events, all links and checklist items.
- `PATCH .../cases/{case_uuid}/`: any of `title`, `priority`, `due_at` (nullable), `tags`. Logs `PRIORITY_CHANGED`, `DUE_DATE_CHANGED`, `TAG_ADDED`, `TAG_REMOVED`.
- `DELETE .../cases/{case_uuid}/`: deletes the case, returns `204`. There is no undelete.

## Case Actions

Every action returns the updated CaseDetail (`200`) unless noted.

| Action | Body | Rules |
|---|---|---|
| `assign/` | `{"assignee_user_id": "<uuid>"}` (or `null` to unassign) | The assignee must be a member with case access to the application: list them with `GET .../cases/reviewers/` |
| `resolve/` | `{"resolution": "<resolution>", "note": "..."}` (any value from [Status Values](#status-values)) | `400` if a non-optional checklist item is incomplete (lists the labels) or the blueprint requires a note and none is given. On a 4-eyes blueprint it stages instead of closing (see below) |
| `reopen/` | none | Only from `AWAITING_USER` or `RESOLVED`, else `400`. Clears `resolution`, `resolution_notes`, `resolved_at`, `resolved_by_email` |
| `request-info/` | none | Only from `OPEN` and with no resolution pending approval, else `400` |
| `escalate/` | none | `400` unless the blueprint has `escalation_enabled` and an active `escalation_blueprint` |
| `transfer/` | `{"target_blueprint": "<uuid>"}` | `400` unless the current blueprint has `transfer_enabled` and the target is a different, active blueprint of the same application. Auto-assigns if the target uses `AUTOMATIC` assignment |
| `approve/` | none | 4-eyes only. `409` if nothing is pending or the linked evidence changed after submission; `403` for the officer who submitted it |
| `reject-approval/` | `{"notes": "..."}` (optional) | 4-eyes only. Clears the staged resolution and returns the case to the maker blueprint. Same `409` / `403` rules |

### Resolve and 4-eyes review

```python
r = requests.post(f"{BASE}/cases/{case_uuid}/resolve/", headers=HEADERS,
                  json={"resolution": "FALSE_POSITIVE", "note": "Documents confirm legitimate activity."},
                  timeout=30)
case = r.json()
if case["pending_resolution"]:
    print("Staged for 4-eyes approval; status is still", case["status"])
else:
    print("Resolved:", case["resolution"])
```

When the case's blueprint sets `four_eyes_checker_blueprint`, `resolve/` does not close the case: `status` stays `OPEN`, `pending_resolution` holds `{resolution, resolution_notes, maker_email, maker_name, maker_blueprint_id, staged_at}`, the case moves to the checker blueprint's queue and a `SUBMITTED_FOR_APPROVAL` event is logged. A different officer then calls `approve/` (case becomes `RESOLVED`, credited to the maker) or `reject-approval/`.

- Changing a checklist answer or adding or removing a link clears the pending decision (`APPROVAL_INVALIDATED`); submit a new one.
- `request-info/` is blocked while a resolution is pending.
- **With an API key:** a resolution staged by an API key has no recorded maker, so `approve/` and `reject-approval/` both return `403` for everyone. On 4-eyes blueprints, let a console user submit the resolution (or submit it again), then a second console user approves.

## Notes, Attachments, Links, Checklist

**Notes:** `POST .../cases/{case_uuid}/notes/` returns `201`.

| Field | Type | Description |
|---|---|---|
| `comment` | string | **Required**, plain text, max 10000 chars |
| `mentioned_emails` | email[] | Must be members with access to the application, else `400` |
| `is_internal` | boolean | Default `false` |
| `attachments` | object[] | Each needs the `s3_key` returned by the upload endpoint; the note stores what you send, so also pass `filename` and `file_size` |
| `tags` | string[] | Note tags |
| `reply_to` | UUID | A live note in the same case |
| `client_reference` | UUID | Idempotency key: an unchanged retry returns the existing note (`200`); reuse with different content, or after the note was deleted, returns `409` |

- `GET .../notes/` (`limit` default 50, `offset`): pinned notes first, then newest first.
- `PATCH .../notes/{note_uuid}/` with `{"is_pinned": true}`; `DELETE .../notes/{note_uuid}/` permanently deletes it (`204`).
- **Upload:** `POST .../notes/presign/` as `multipart/form-data` with `file` (PDF, JPEG, PNG, WebP, plain text or CSV, max 5 MB) returns `201` `{"s3_key", "url", "filename", "file_size"}`. The `s3_key` starts with `case-notes/{case_uuid}/`; a note whose attachment `s3_key` belongs to another case is rejected with `400`.
- **Download later:** `GET .../notes/presign/?s3_key=<key>` returns a fresh `{"s3_key", "url", "filename"}` (`404` if the key is not on this case).

**Links:** `GET .../links/` (array), `POST .../links/` with `{"entity_type", "entity_uuid"}` (`201`; `400` if it belongs to a different subject), `DELETE .../links/{link_uuid}/` (`204`).

**Checklist:** `GET .../checklist/` lists items copied from the blueprint when the case was created; `PATCH .../checklist/{item_uuid}/` with `{"is_completed": true}`.

**Other reads:** `GET .../events/` (paginated, newest first), `GET .../aml/` (array of the AML screening results of the sessions and business sessions linked to the case, newest first, each with its `status` and `hits`), `GET .../print/` (renders a new PDF of the whole case and returns `{"url": "<presigned URL>"}`; download promptly).

## Subject Actions

`POST .../cases/{case_uuid}/entity-actions/` acts on the case subject (the user or business):

| `action` | Extra fields | Effect |
|---|---|---|
| `set_status` | `status`: `ACTIVE`, `FLAGGED` or `BLOCKED` | Changes the user or business status |
| `add_tags` | `tags` | Adds tags to the subject |
| `add_note` | `note` | Adds an internal case note |
| `add_to_blocklist` | none | Adds the subject to the blocklist |

Send a unique `client_reference` (UUID) to get an idempotent receipt: the response then includes `receipt` with `status` `APPLIED` or `FAILED` (a `200` can carry a `FAILED` receipt, meaning nothing was applied). Reusing a reference with a different payload returns `409`. Retry a failed action with `retry: true`, or `POST .../action-receipts/{receipt_uuid}/retry/`; list receipts with `GET .../action-receipts/` (20 per page, `next_offset`).

## Customer Messages

Ask the verified user for information from a case (fixed email templates only):

| Step | Call |
|---|---|
| Options | `GET .../cases/{case_uuid}/requests/options/` returns verified `contacts`, allowed `purposes`, `languages` |
| Preview | `POST .../cases/{case_uuid}/requests/preview/` with `{"contact_id", "purpose", "language"}` returns `request_id`, `expires_at`, `preview_token` and the rendered email |
| Send | `POST .../cases/{case_uuid}/requests/` with the same `contact_id`, `purpose`, `language` plus `request_id`, `expires_at`, `preview_token`, within 15 minutes (`201`) |
| History / cancel | `GET .../cases/{case_uuid}/requests/`, `POST .../requests/{request_uuid}/cancel/` |

`purpose`: `identity_document`, `proof_of_address`, `business_document`, `confirm_details`, `review_in_progress`. `language`: `en` (default), `es`, `pt`. An actionable request moves the case to `AWAITING_USER`; `review_in_progress` leaves the status unchanged. Guide: https://docs.didit.me/console/case-management/customer-messages

## Bulk Operations

- `POST .../cases/bulk/status/` with `{"case_uuids": [...], "status": "OPEN" | "AWAITING_USER" | "RESOLVED", "resolution": "...", "note": "..."}`. `OPEN` reopens, `AWAITING_USER` requests info, `RESOLVED` resolves (`resolution` required, else `400`).
- `POST .../cases/bulk/assign/` with `{"case_uuids": [...], "assignee_user_id": "<uuid>" or null}`. All cases must share one blueprint.

Both return `{"updated": 3, "failures": [{"case_uuid": "...", "detail": "..."}]}`: each case is evaluated on its own, so one blocked case never rolls back the rest.

## Analytics

`GET .../cases/statistics/`

| Query param | Description |
|---|---|
| `date_from`, `date_to` | `YYYY-MM-DD`, send both. Default: the last 30 days. Max range 731 days |
| `blueprint`, `assigned_to` | UUID filters (current values) |
| `priority`, `source`, `status` | One value each |

Response: `series` (`[{date, created, reviewed}]`), `tables` (`officer`, `blueprint`, `source`, `status`: rows of `{key, created, assigned, resolved, threat_rate, false_positive_rate, unresolved, reassignment_rate, escalation_rate, avg_assign_hours, avg_resolve_hours, avg_handling_hours}`), `totals` (same metrics) and `queue` (`{open, overdue}`, a live snapshot independent of the date range). `400` for a bad date, `date_from` after `date_to`, or a range over 731 days.

---

## Status Values

| Case `status` | Meaning | Next |
|---|---|---|
| `OPEN` | Under investigation (also while a 4-eyes resolution is pending) | `resolve/`, `request-info/`, `escalate/`, `transfer/` |
| `AWAITING_USER` | Paused while information is collected from the user | `reopen/`, `resolve/` |
| `RESOLVED` | Closed with a `resolution` | `reopen/` |

| `resolution` | Meaning |
|---|---|
| `FALSE_POSITIVE` | No concern found: activity was legitimate |
| `VALID_THREAT` | Concern confirmed: suspicious or fraudulent activity. The only value that feeds the shared fraud index and counts toward `threat_rate` |
| `INCONCLUSIVE` | The evidence does not support either verdict |
| `REQUIREMENTS_NOT_MET` | The subject did not meet the review's requirements (not a fraud verdict) |
| `REQUIREMENTS_SATISFIED` | The subject met the review's requirements |

| `source` | Created by |
|---|---|
| `MANUAL` | Console or API |
| `AML_SCREENING` | An ongoing-monitoring AML hit, when **Create cases from ongoing monitoring hits** is on in the workflow's AML settings. A later hit on a subject with an open case attaches to it |
| `TRANSACTION_RULE` | A transaction rule with the **Create case** effect (grouping by applicant, or by rule and applicant) |
| `WORKFLOW_BUILDER` | A session reaching a **Create case** node |

**Event types** (`events[].event_type`): `CREATED`, `STATUS_CHANGED`, `ASSIGNED`, `UNASSIGNED`, `RESOLVED`, `REOPENED`, `LINK_ADDED`, `LINK_REMOVED`, `NOTE_ADDED`, `PRIORITY_CHANGED`, `DUE_DATE_CHANGED`, `TAG_ADDED`, `TAG_REMOVED`, `ESCALATED`, `TRANSFERRED`, `CHECKLIST_COMPLETED`, `REPORT_CREATED`, `REPORT_FINALIZED`, `SUBMITTED_FOR_APPROVAL`, `APPROVAL_GRANTED`, `APPROVAL_REJECTED`, `ENTITY_ACTION`, `APPROVAL_INVALIDATED`.

---

## Blueprints (Review Policies)

| Method | Path | Purpose |
|---|---|---|
| `GET` / `POST` | `cases/blueprints/` | List (`limit` default 50, `offset`) / create (`201`) |
| `GET` / `PATCH` / `DELETE` | `cases/blueprints/{blueprint_uuid}/` | Detail (adds `content_config`, `creation_sources`, `receives_escalation_from`) / update / delete (`204`) |
| `GET` | `cases/blueprints/presets/` | `{"results": [{preset_key, name, description, content_config, installed}]}` |
| `POST` | `cases/blueprints/presets/install/` | `{"preset_keys": [...]}` (omit to install all). `201` `{"created": [...]}`, or `200` when nothing new |
| `GET` / `PUT` / `DELETE` | `cases/blueprints/{blueprint_uuid}/draft/` | Read / save / discard an unpublished draft |
| `POST` | `cases/blueprints/{blueprint_uuid}/publish/` | Publish the draft: `{"expected_version", "expected_revision"}` |
| `GET` | `cases/blueprints/{blueprint_uuid}/history/` | Published versions |

**Create fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | **Yes** | Max 24 chars |
| `assignee_pool` | UUID[] | **Yes** | At least one member user UUID (`GET .../cases/reviewers/`), else `400` "Pick at least one assignee" |
| `description` | string | No | Free text |
| `assignment_method` | string | No | `MANUAL` (default) or `AUTOMATIC` (least-loaded authorized reviewer, up to capacity) |
| `max_active_cases` | integer | No | Capacity per reviewer for automatic assignment (min 1) |
| `escalation_enabled` / `escalation_blueprint` | boolean / UUID | No | Both are needed before `escalate/` works |
| `transfer_enabled` | boolean | No | Allows `transfer/` |
| `four_eyes_checker_blueprint` | UUID | No | Setting it turns on 4-eyes review |
| `require_resolution_note` | boolean | No | Makes `note` mandatory on resolve |
| `default_deadline_hours` | integer | No | 1-8760; `due_at` for new cases |
| `content_config` | object | No | Case page sections, validated strictly (unknown keys `400`) |
| `is_active` | boolean | No | Default `true`; only active blueprints accept new cases and transfers |
| `publish` | boolean | No | Default `true`. `false` saves an unpublished draft (version 0) that must be published through `.../publish/` |

A blueprint cannot point at itself as escalation target or checker, and cross-referenced blueprints must belong to the same application. `PATCH` publishes immediately; send `expected_version` to get `409` instead of overwriting a newer version. Deleting a blueprint does not touch its cases: they keep their blueprint and its settings.

**`content_config` sections:** `checklist` (`enabled`, `optional`, `items[{label, order}]`), `aml_control` (`enabled`, `financial`, `identity`), `identity` (`enabled`, `personal_information`, `applicant_tags`, `contact_information`, `risk_overview`, `poi_documents`, `poa_documents`), `verifications` (`enabled`, `summary`), `reporting` (`enabled`, `fiu_reports`), `financial` (`enabled`, `payment_methods`, `transactions`). With `checklist.optional` false, every item must be completed before resolving.

**Presets:** `screening_hit`, `aml_investigation`, `suspicious_activity`, `kyc`. Installing copies an editable blueprint (idempotent per key). Presets set no assignment, escalation, transfer or 4-eyes: configure those after installing.

## Assignment: Reviewers, Teams, Routing Rules

| Method | Path | Purpose |
|---|---|---|
| `GET` | `cases/reviewers/` | `{"results": [{user_id, email, name}]}`: members eligible for cases (`503` if access could not be verified; retry) |
| `GET` / `POST` | `cases/teams/` | Review teams: `{name, description, members[{user_id, availability, capacity, skills, available_from, available_until}], is_active}` |
| `GET` / `PATCH` | `cases/teams/{record_uuid}/` | Team detail / update |
| `GET` / `POST` | `cases/routing-rules/` | Rules: `{name, priority, conditions[{field, operator, value}], blueprint, team, required_skills, is_active, publish}` |
| `GET` / `PATCH` | `cases/routing-rules/{record_uuid}/` | Rule detail / update (`expected_version` for `409` on stale edits) |
| `POST` | `cases/routing-rules/preview/` | Test routing for `{source, priority, tags}` without saving or reserving capacity |
| `*` | `cases/routing-rules/{record_uuid}/draft/`, `.../publish/`, `.../history/` | Same draft lifecycle as blueprints |

Conditions: `field` is `source`, `priority` or `tags`; `operator` is `equals` or `in` (source, priority) or `contains` (one tag). Rules are evaluated in `priority` order on case creation; the first matching active rule picks the blueprint and team. An explicit `assigned_to` always wins. Guide: https://docs.didit.me/console/case-management/assignment

---

## FIU Reports (Regulatory Reports)

Draft a goAML filing from a case, validate it, finalize it (irreversible), then download the goAML XML for your FIU portal and a PDF for your records.

| Method | Path | Purpose |
|---|---|---|
| `GET` / `POST` | `report-templates/` | List / create a template (`201`) |
| `GET` / `PATCH` / `DELETE` | `report-templates/{template_uuid}/` | Detail / update / delete (reports already created stay) |
| `GET` / `POST` | `cases/{case_uuid}/regulatory-reports/` | Reports of a case / create a draft from the case (`201`) |
| `GET` / `POST` | `regulatory-reports/` | All reports (`status`, `report_type`, `case` filters) / standalone create (`case` and `template` required) |
| `GET` / `PATCH` / `DELETE` | `regulatory-reports/{report_uuid}/` | Detail / edit / delete. `409` once `FINALIZED` |
| `POST` | `regulatory-reports/{report_uuid}/validate/` | `{"status", "is_valid", "errors": [{field, message}]}`; sets status to `VALIDATED` or back to `DRAFT` |
| `POST` | `regulatory-reports/{report_uuid}/finalize/` | Re-validates, renders XML + PDF, sets `FINALIZED`. `400` with `errors` on failure, `409` if not finalizable |
| `GET` | `regulatory-reports/{report_uuid}/download-url/?file=pdf` | `{"download_url", "file"}`; `file` is `pdf` (default) or `xml`. `409` until finalized |

**Template** (`POST .../report-templates/`): `name`, `jurisdiction` (ISO 3166-1 alpha-2), `report_type`, `field_config`. `field_config` must contain `rentity_id` (reporting entity ID from your FIU), `submission_code` (`E` electronic or `M` manual) and `currency_code_local` (3 letters), else `400` `{"errors": [...]}` listing the missing ones. Optional: `enabled_fields`, `reporting_person`, `location`, `reason`, `action`.

**Report from a case** (`POST .../cases/{case_uuid}/regulatory-reports/`): `template`, or `report_type` + `jurisdiction` when no template. Optional `transactions` (UUIDs; default: the case's linked transactions) and header fields (`rentity_id`, `rentity_branch`, `submission_code`, `entity_reference`, `fiu_ref_number`, `currency_code_local`, `submission_date`, `reporting_person`, `location`, `reason`, `action`, `activity`, `narrative` `{who, what, when, where, why, how}`, `report_indicators`, `included_fields`). The draft is filled from the template, the case subject, the linked transactions and a five-Ws narrative (SAR, STR, TFR). Validation also requires `action`, `submission_date`, at least one transaction and a 2-letter jurisdiction.

| `report_type` | Report |
|---|---|
| `SAR` | Suspicious Activity Report |
| `STR` | Suspicious Transaction Report |
| `CTR` | Cash Transaction Report |
| `TTR` | Threshold Transaction Report |
| `UTR` | Unusual Transaction Report |
| `IFT` | International Funds Transfer Report |
| `CBR` | Cross-Border Report |
| `TFR` | Terrorism Financing Report |

Report `status`: `DRAFT` (editable), `VALIDATED` (passed validation), `FINALIZED` (files generated; no more edits or deletes). Finalizing a `SAR`, `STR` or `TFR` moves the case's transaction alerts from **Pending SAR** to **SAR filed**.

---

## Error Responses

| Code | Meaning | Action |
|---|---|---|
| `400` | Invalid request | Read the field errors in the response body |
| `401` | The API key has expired | Rotate it or create a new key in **Developers > API keys** |
| `403` | Missing, wrong or revoked API key; a scoped key without access to this endpoint; a request from outside the key's IP allowlist; or not enough credits | Read the message in `detail` or `error`: fix the `x-api-key` header or the key's access, or top up |
| `403` | `"This API key has no access to this endpoint."` | Named key with custom access: use the primary key or a full-access key |
| `403` | `"You do not have permission to perform this action."` | `{application_id}` is not the key's application |
| `403` | On `approve/` / `reject-approval/` | The maker cannot approve their own resolution; a key-staged resolution has no recorded maker |
| `404` | Case, blueprint, note, link, report, template or attachment not found in this application | Check the UUIDs and `{application_id}` |
| `409` | Duplicate review required; nothing pending approval or evidence changed; stale `expected_version`; note `client_reference` reused; report already finalized or not finalized yet | Read `detail` |
| `429` | Rate limit: 300 POST/PATCH/DELETE and 600 GET requests a minute per key | Wait the `Retry-After` seconds, then retry |

---

## Response Field Reference

### CaseListItem / CaseDetail

| Field | Type | Description |
|---|---|---|
| `uuid` | UUID | Case ID used in every case path |
| `case_number` | string | Human-readable, e.g. `CS-0001` |
| `title` | string | Case title |
| `status` / `resolution` / `priority` / `source` | string | See Status Values |
| `tags` | string[] | Case tags |
| `subject` | object | `{type, uuid, name, external_id}`; `external_id` is the subject's `vendor_data` |
| `assigned_to` | object | `{uuid, full_name, email}` or `null` |
| `assigned_at` / `due_at` / `resolved_at` | datetime | Timestamps (nullable) |
| `blueprint` | object | List: `{uuid, name}`. Detail: the blueprint with `content_config` |
| `links_count` / `notes_count` | integer | Live links and notes |
| `created_by_email` / `created_by_name` | string | List only |
| `application_id` / `application_name` / `organization_id` / `organization_name` | string | List only |
| `resolution_notes` / `resolved_by_email` | string | Detail only |
| `pending_resolution` | object | Detail only. Staged 4-eyes resolution or `null` |
| `metadata` | object | Detail only. For example `separate_incident_reason` |
| `notes` / `events` / `links` / `checklist_items` | array | Detail only. Newest 50 notes, newest 100 events |

### Note, Link, Checklist item

| Object | Fields |
|---|---|
| Note | `uuid`, `comment`, `actor_email`, `actor_name`, `mentioned_emails`, `is_internal`, `attachments`, `tags`, `created_at`, `reply_to`, `is_pinned`, `client_reference` |
| Link | `uuid`, `linked_entity_type`, `linked_entity_uuid`, `linked_entity_summary` (`session_id`, `session_number`, `status` for sessions; `uuid`, `txn_id`, `status` for transactions), `created_at` |
| Checklist item | `uuid`, `label`, `is_completed`, `completed_by`, `completed_at`, `order` |

---

## Common Workflows

### Work the open queue

```
1. GET  .../cases/?status__in=OPEN,AWAITING_USER&ordering=due_at  -> most urgent first
2. GET  .../cases/{case_uuid}/                                     -> subject, links, checklist
3. GET  .../cases/{case_uuid}/aml/                                 -> AML results of linked sessions
4. PATCH .../cases/{case_uuid}/checklist/{item_uuid}/  {"is_completed": true}
5. POST .../cases/{case_uuid}/notes/  {"comment": "Reviewed source of funds."}
6. POST .../cases/{case_uuid}/resolve/  {"resolution": "FALSE_POSITIVE", "note": "..."}
   If pending_resolution is set -> a second console user approves (4-eyes)
```

### Open a case for a flagged transaction

```
1. POST /v3/transactions/ returns uuid and status IN_REVIEW
2. POST .../cases/duplicates/  {"links": [{"entity_type": "transaction", "entity_uuid": "<uuid>"}]}
3. Existing open case -> POST .../cases/{case_uuid}/links/ with the transaction
   No case          -> POST .../cases/ {"title": "...", "links": [...], "review_duplicates": true}
```

### File a SAR from a case

```
1. POST .../report-templates/  {"name": "US SAR", "jurisdiction": "US", "report_type": "SAR",
     "field_config": {"rentity_id": "FIU-US-00123", "submission_code": "E", "currency_code_local": "USD"}}
2. POST .../cases/{case_uuid}/regulatory-reports/  {"template": "<template_uuid>"}   -> DRAFT
3. PATCH .../regulatory-reports/{report_uuid}/  {"action": "...", "submission_date": "...", "narrative": {...}}
4. POST .../regulatory-reports/{report_uuid}/validate/   -> fix every errors[].field
5. POST .../regulatory-reports/{report_uuid}/finalize/   -> FINALIZED (irreversible)
6. GET  .../regulatory-reports/{report_uuid}/download-url/?file=xml  -> upload to the FIU portal
```

### Bootstrap case management

```
1. GET  .../cases/reviewers/                        -> member user_id values
2. POST .../cases/blueprints/presets/install/  {"preset_keys": ["aml_investigation", "kyc"]}
3. PATCH .../cases/blueprints/{uuid}/  {"assignee_pool": ["<user_id>"], "assignment_method": "AUTOMATIC"}
4. Turn on case creation in the AML settings, transaction rules or workflow builder (Business Console)
```

---

## Utility Scripts

**manage_cases.py**: list, inspect, create, resolve, annotate cases and pull analytics from the command line.

```bash
# Requires: pip install requests
export DIDIT_API_KEY="your_api_key"
export DIDIT_ORG_ID="your_organization_uuid"
export DIDIT_APP_ID="your_application_uuid"
python scripts/manage_cases.py list --status OPEN,AWAITING_USER --ordering due_at
python scripts/manage_cases.py get 6f1c2a9e-0b7d-4c3e-9a51-2d8e4f7b1c03
python scripts/manage_cases.py create --title "Manual - Jane Doe" --user 8c0e5a3e-1f7b-4d55-9a0e-6b2f0c7d9e11 --priority HIGH
python scripts/manage_cases.py create --title "Flagged payout" --transaction 3b9d2c1a-7e4f-4a6b-8c5d-0e1f2a3b4c5d
python scripts/manage_cases.py resolve 6f1c2a9e-0b7d-4c3e-9a51-2d8e4f7b1c03 --resolution FALSE_POSITIVE --note "Verified"
python scripts/manage_cases.py note 6f1c2a9e-0b7d-4c3e-9a51-2d8e4f7b1c03 --comment "Called the customer"
python scripts/manage_cases.py stats --date-from 2026-09-01 --date-to 2026-09-30
```
