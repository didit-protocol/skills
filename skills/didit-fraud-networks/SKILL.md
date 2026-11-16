---
name: didit-fraud-networks
description: >
  Integrate Didit Fraud Networks (fraud ring detection) through the API. Use when the user
  wants to detect fraud rings, multi-accounting or identity fraud clusters, list networks
  of users, businesses or transaction parties linked by a shared device, IP address, face,
  document number, phone, email or address, filter networks by status, risk band, signal type
  or pattern, inspect a network's members, signals, graph, timeline or map, download a
  network PDF report, or check whether a session, user, business, transaction or transaction
  party belongs to a fraud network using Didit. Networks are built automatically from
  production verifications and transactions; the API is read-only.
version: 1.0.0
metadata:
  openclaw:
    requires:
      env:
        - DIDIT_API_KEY
    primaryEnv: DIDIT_API_KEY
    emoji: "🕸️"
    homepage: https://docs.didit.me
---

# Didit Fraud Networks API

## Overview

A **network** is a cluster of subjects (users, businesses and transaction parties) in your organization that share one or more signals. A network forms when two or more subjects match on a signal, so a ring of accounts surfaces as one investigation instead of many unrelated flags.

**Key facts:**
- Built automatically as verification sessions, business sessions and transactions complete. Nothing to submit: the API reads networks.
- Clustering runs across every application of your organization; an application sees a network only if at least one of its own subjects is in it.
- With an API key, `members`, `graph`, `map` and `report` can include subjects from other applications in your organization.
- Production data only: sandbox applications get an empty list (and `404` on a network), and sandbox sessions never create or join a network.
- Signal values are never returned. Exact-match signals are identified by a keyed hash of the normalized value; `face` is matched by similarity.
- A shared signal is a reason to investigate, not proof of fraud. A signal linking an unusually large number of subjects (office IP, kiosk device, data-center IP) is flagged `is_hub` rather than treated as fraud evidence.
- Status changes, dismissing, blocklisting, creating a case from a network and network notes are done in the Business Console (notes are for console users only; API keys get `403`).

**Pricing:** No list price is published for these endpoints; check [didit.me/pricing](https://didit.me/pricing).

**API Reference:** https://docs.didit.me/management-api/networks/list
**Feature guide:** https://docs.didit.me/console/networks

---

## Authentication

Every request needs the `x-api-key` header. Use your application's API key from the [Didit Business Console](https://business.didit.me) under **Developers > API keys**, or create an account and key programmatically (see Getting Started). Network endpoints need the application's primary key or a named key with full access: a named key with custom access gets `403` `"This API key has no access to this endpoint."`

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

The same verify-email response carries `organization.uuid` and `application.uuid`, the two path IDs every network endpoint needs (see Authentication). A new account has no networks until production verifications share signals.

---

## Endpoints

All paths are relative to:

```
https://verification.didit.me/v3/organization/{organization_id}/application/{application_id}/
```

| Method | Path | Returns |
|---|---|---|
| `GET` | `networks/` | Paginated networks with KPIs |
| `GET` | `networks/{network_uuid}/` | One network with stats, fraud tags, risk signals, review fields |
| `GET` | `networks/{network_uuid}/graph/` | Subject nodes, signal nodes and edges |
| `GET` | `networks/{network_uuid}/members/` | `{"results": [NetworkMember]}`, not paginated |
| `GET` | `networks/{network_uuid}/signals/` | `{"results": [NetworkSignal]}`, not paginated |
| `GET` | `networks/{network_uuid}/timeline/` | `{"results": [event]}`, oldest first, not paginated |
| `GET` | `networks/{network_uuid}/map/` | Geographic points and convergence |
| `GET` | `networks/{network_uuid}/report/` | PDF report (`application/pdf`) |
| `GET` | `sessions/{session_id}/networks/` | Networks of the session's user |
| `GET` | `business-sessions/{business_session_id}/networks/` | Networks of the business session's business |
| `GET` | `users/{vendor_user_uuid}/networks/` | Networks of a user |
| `GET` | `businesses/{vendor_business_uuid}/networks/` | Networks of a business |
| `GET` | `transactions/{transaction_uuid}/networks/` | Networks of the transaction's KYC/KYB subject |
| `GET` | `transactions/{transaction_uuid}/parties/{transaction_party_uuid}/networks/` | Networks of one transaction party |

---

## List Networks

`GET .../networks/`

| Query param | Description |
|---|---|
| `status` | Comma-separated: `active,in_review,resolved,dismissed`. Omitted: everything except `dismissed` |
| `signal_type` | Comma-separated: `ip_address,device,face,document_number,phone,email,address` |
| `pattern_type` | Comma-separated pattern types (see Status Values); a network must have every pattern given |
| `risk_band` | Comma-separated: `low,medium,high` |
| `min_size`, `max_size` | Member count bounds (integers) |
| `date_from` | ISO 8601 date or datetime; networks with `last_activity_at` on or after it |
| `date_to` | ISO 8601 date or datetime; networks with `first_activity_at` on or before it |
| `q` | Free text: network name, member names, network id (`N-0001`), or an exact pattern type |
| `ordering` | `risk_score`, `-risk_score`, `last_activity_at`, `-last_activity_at`, `first_activity_at`, `-first_activity_at`, `network_number`, `-network_number`. Default: `-risk_score` then `-last_activity_at` |
| `limit` | 1-500, default 100 |
| `offset` | Default 0 |

```python
import os

import requests

BASE = (
    "https://verification.didit.me/v3/organization/"
    f"{os.environ['DIDIT_ORG_ID']}/application/{os.environ['DIDIT_APP_ID']}"
)
HEADERS = {"x-api-key": os.environ["DIDIT_API_KEY"]}

response = requests.get(
    f"{BASE}/networks/",
    headers=HEADERS,
    params={"status": "active,in_review", "risk_band": "high", "ordering": "-risk_score"},
    timeout=30,
)
response.raise_for_status()
page = response.json()
for network in page["results"]:
    print(network["network_id"], network["status"], network["risk"]["score"], network["signal_types"])
```

```typescript
const BASE = `https://verification.didit.me/v3/organization/${orgId}/application/${appId}`;

const response = await fetch(`${BASE}/networks/?status=active,in_review&risk_band=high`, {
  headers: { "x-api-key": "YOUR_API_KEY" },
});
const { count, next, results, kpis } = await response.json();
```

### Response (200 OK)

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "uuid": "2b7e1f0c-4d3a-4e5b-9c6d-7e8f9a0b1c2d",
      "network_id": "N-0007",
      "name": "Shared device ring",
      "status": "active",
      "risk": {"score": 82, "band": "high", "bar": 0.82},
      "pattern_types": ["exact_same_device", "same_ip_address"],
      "signal_types": ["device", "ip_address"],
      "member_counts": {"total": 5},
      "member_status": {"approved": 3, "declined": 1, "in_review": 1, "not_completed": 0},
      "first_activity_at": "2026-09-28T10:02:11Z",
      "last_activity_at": "2026-10-11T18:45:03Z"
    }
  ],
  "kpis": {
    "active": {"value": 1, "delta": 1},
    "in_review": {"value": 0, "delta": 0},
    "applicants_involved": {"value": 5, "delta": 5},
    "detected_this_period": {"value": 1, "delta": 1},
    "false_positive_rate": {"value": 0, "delta": 0}
  }
}
```

`next` and `previous` are **offsets** (integers), not URLs: `null` `next` means the last page. `kpis` keys are each `{value, delta}`, computed over the networks matching the filters. `member_counts` includes `total`; `member_status` counts members per outcome (`approved`, `declined`, `in_review`, `not_completed`); each item also carries `signal_coverage`, a per-signal-type coverage object (omitted above).

## Get Network

`GET .../networks/{network_uuid}/` returns every list field plus:

| Field | Type | Description |
|---|---|---|
| `stats` | object | Aggregate stats (for example member totals) |
| `fraud_tags` | object[] | Fraud-pattern tags surfaced on the network |
| `risk_signals` | object | Summaries: `residential_proxy_reuse`, `email_intelligence`, `phone_intelligence` |
| `reviewed_at` / `reviewed_by` / `review_reason` | string | Last status review (nullable) |
| `notes_count` | integer | Private analyst notes on the network |

`404` when the network does not exist or has no member visible to this application.

## Graph

`GET .../networks/{network_uuid}/graph/`

| Query param | Description |
|---|---|
| `depth` | `1`, `2`, `3` or `all` (default): hops from the focus subject |
| `focus_kind` | `vendor_user`, `vendor_business` or `transaction_party`. Must come with `focus_id`, else `400` |
| `focus_id` | Subject UUID to center on. With a bounded `depth` and no focus, an arbitrary member is used |

Response: `{network, depth, truncated, nodes, edges, metrics: {node_count, edge_count, hub_signal_count}}`. `depth` is `null` when unbounded; `truncated` is `true` when the depth cut the neighborhood.

| Node `kind` | Fields |
|---|---|
| `vendor_user`, `vendor_business`, `transaction_party` | `id`, `kind`, `subject`, `node_status` (`approved`, `in_review`, `declined`, `not_completed`), `tags` |
| `signal` | `id`, `kind`, `uuid`, `signal_type`, `subject_count`, `coverage`, `is_hub`, `is_datacenter_ip`, `is_high_collision_device`, `node_status` (`signal_active`, `signal_guarded`), `tags`, `risk_evidence`, `first_seen_at`, `last_seen_at` |

Edge: `id`, `source` (subject node id), `target` (signal node id), `subject_kind`, `signal_type`, `confidence` (`1.0` for an exact match), `observation_count`, `first_seen_at`, `last_seen_at`.

## Members, Signals, Timeline, Map, Report

- **Members** `GET .../members/`: each `{subject, outcome_status, node_status, tags, risk, signal_coverage, shared_infrastructure, joined_at, last_seen_at, provenance: {session_ids, business_session_ids, transaction_ids}}`. `node_status` is the member's own verification outcome (`approved`, `in_review`, `declined`, `not_completed`), not the network's status. `provenance` lists the records that placed the member in the network.
- **Signals** `GET .../signals/`: each `{uuid, signal_type, subject_count, coverage, is_hub, is_datacenter_ip, is_high_collision_device, node_status, tags, risk_evidence, first_seen_at, last_seen_at}`.
- **Timeline** `GET .../timeline/`: each `{event_type, occurred_at, label, metadata}`, oldest first. `event_type` examples: `network_detected`, `signal_observed`, `network_in_review`, `network_resolved`, `network_dismissed`; `metadata` is event-specific (for example `{reason}` on a status change).
- **Map** `GET .../map/`: `{network, convergence_count, countries, points: [{uuid, country, country_code, city, latitude, longitude, observed_at}]}`. Points come from IP geolocation and proof-of-address data of the member records; `convergence_count` is the number of distinct points members converge on.
- **Report** `GET .../report/`: a PDF of the network, its connected accounts, signal references and review status (`Cache-Control: no-store`). It excludes private notes, says when a list is incomplete, and does not change the network status. Errors come back as JSON.

```python
r = requests.get(f"{BASE}/networks/{network_uuid}/report/", headers=HEADERS, timeout=60)
r.raise_for_status()
with open("network-report.pdf", "wb") as handle:
    handle.write(r.content)
```

## Membership Lookup

Point any ID you already hold at the matching endpoint. All return `{"results": [EntityNetworkMembership]}`, not paginated; an entity in no network returns `"results": []`, not `404`.

| Entity | Path | ID to use | Resolves through |
|---|---|---|---|
| Session | `sessions/{session_id}/networks/` | The session's `session_id` | The session's user |
| Business session | `business-sessions/{business_session_id}/networks/` | The business session's `session_id` | The session's business |
| User | `users/{vendor_user_uuid}/networks/` | `didit_internal_id` from `GET /v3/users/{vendor_data}/` | The user |
| Business | `businesses/{vendor_business_uuid}/networks/` | `didit_internal_id` from `GET /v3/businesses/{vendor_data}/` | The business |
| Transaction | `transactions/{transaction_uuid}/networks/` | The transaction's Didit `uuid` | The subject of the transaction's backing KYC/KYB session |
| Transaction party | `transactions/{transaction_uuid}/parties/{transaction_party_uuid}/networks/` | `parties[].uuid` of the transaction | The party itself (applicant, remitter, beneficiary or counterparty) |

EntityNetworkMembership: `network` (list-item shape), `subject`, `signal_types` (the signal types connecting this entity), `signal_count`, `joined_at`, `last_seen_at`.

`404` when the record does not exist in this application, or (session, business session and transaction variants) has no linked user or business to look up. Use the transaction party variant for a remitter or beneficiary that is not the transaction's own KYC subject.

```python
r = requests.get(f"{BASE}/sessions/{session_id}/networks/", headers=HEADERS, timeout=30)
r.raise_for_status()
for membership in r.json()["results"]:
    network = membership["network"]
    print(network["network_id"], network["risk"]["band"], membership["signal_types"])
```

---

## Status Values

**Network `status`** (the investigation):

| Status | Meaning |
|---|---|
| `active` | Newly detected or still accumulating members, not yet reviewed |
| `in_review` | An analyst is investigating |
| `resolved` | Investigation complete |
| `dismissed` | Reviewed and not worth action; hidden from the list unless `status` includes it |

Every status change is recorded with a reason and the analyst (see `timeline`).

**Risk `band`:** `high` from score 70, `medium` from 40, otherwise `low` (`risk.score` is 0-100, `risk.bar` is the score as 0-1).

**Member `node_status`:** `approved`, `in_review`, `declined`, `not_completed`. **Signal `node_status`:** `signal_active`, `signal_guarded`.

| `signal_type` | Connection |
|---|---|
| `device` | Same device fingerprint |
| `ip_address` | Shared connection address |
| `document_number` | Same government identifier within its issuing namespace |
| `phone` / `email` | Same normalized contact identifier |
| `address` | Same normalized physical address |
| `face` | Biometric similarity (evidence for review, not proof of the same person) |

**`pattern_types`:** `exact_same_device`, `similar_device`, `same_ip_address`, `same_address`, `similar_selfie_backgrounds`, `similar_poa_documents`, `same_document_number`, `same_phone_number`, `same_email`.

**Node tag `source`:** `subject_tag`, `session_tag`, `transaction_tag`, `signal_guard` (`category` `customer` for your tags, `quality` for signal-quality guards such as hub or data-center IP).

---

## Error Responses

| Code | Meaning | Action |
|---|---|---|
| `400` | Invalid request | Read the field errors in the response body |
| `400` | Bad filter: `limit` outside 1-500, non-integer `min_size`/`max_size`, unknown `risk_band` or `ordering`, invalid date, bad `depth`, `focus_kind` without `focus_id` | Fix the query parameter |
| `401` | The API key has expired | Rotate it or create a new key in **Developers > API keys** |
| `403` | Missing, wrong or revoked API key; a scoped key without access to this endpoint; a request from outside the key's IP allowlist; or not enough credits | Read the message in `detail` or `error`: fix the `x-api-key` header or the key's access, or top up |
| `403` | `"This API key has no access to this endpoint."` | Named key with custom access: use the primary key or a full-access key |
| `403` | `"You do not have permission to perform this action."` | `{application_id}` is not the key's application |
| `404` | Network not found or not visible to this application; lookup entity not found or without a linked subject | Check the IDs; sandbox applications have no networks |
| `429` | Rate limit: 300 POST/PATCH/DELETE and 600 GET requests a minute per key | Wait the `Retry-After` seconds, then retry |

---

## Response Field Reference

### NetworkListItem

| Field | Type | Description |
|---|---|---|
| `uuid` | UUID | Network ID used in every network path |
| `network_id` | string | Per-organization sequential id, e.g. `N-0001` |
| `name` | string | Network name (nullable) |
| `status` | string | `active`, `in_review`, `resolved`, `dismissed` |
| `risk` | object | `{score, band, bar}` |
| `pattern_types` | string[] | Clustering patterns detected |
| `signal_types` | string[] | Distinct signal types present |
| `member_counts` | object | Member counts by category |
| `member_status` | object | Members by outcome status |
| `signal_coverage` | object | Coverage per signal type |
| `first_activity_at` / `last_activity_at` | datetime | Activity window (nullable) |

### NetworkSignal

| Field | Type | Description |
|---|---|---|
| `uuid` | UUID | Signal ID (graph signal nodes carry the same `uuid`) |
| `signal_type` | string | See Status Values |
| `subject_count` | integer | Subjects sharing the signal |
| `coverage` | number | Share of the network's members carrying it |
| `is_hub` | boolean | Links an unusually large number of subjects |
| `is_datacenter_ip` / `is_high_collision_device` | boolean | Signal-quality guards |
| `node_status` | string | `signal_active` or `signal_guarded` |
| `risk_evidence` | object | Evidence attached to the signal |
| `first_seen_at` / `last_seen_at` | datetime | Observation window |

---

## Common Workflows

### Check a new user for ring membership

```
1. Session completes (webhook status.updated with session_id)
2. GET .../sessions/{session_id}/networks/
3. results empty           -> no shared signals so far
   network.risk.band high  -> route to manual review or open a case (didit-case-management skill)
4. GET .../networks/{network_uuid}/members/ -> who else shares the signal, and their node_status
```

### Daily triage of high-risk rings

```
1. GET .../networks/?status=active&risk_band=high&ordering=-last_activity_at
2. For each network: GET .../networks/{uuid}/signals/  -> skip rings held together only by is_hub signals
3. GET .../networks/{uuid}/timeline/ and .../map/       -> when it formed, where members converge
4. Review in the Business Console: change status, dismiss, blocklist a member or signal, or create a case
```

### Screen a payout beneficiary

```
1. POST /v3/transactions/ returns uuid and parties[]
2. GET .../transactions/{uuid}/parties/{party_uuid}/networks/  -> networks of the beneficiary itself
```

---

## Utility Scripts

**list_networks.py**: list and filter networks, inspect one network and its members, or look up the networks of a session, user, business, transaction or transaction party.

```bash
# Requires: pip install requests
export DIDIT_API_KEY="your_api_key"
export DIDIT_ORG_ID="your_organization_uuid"
export DIDIT_APP_ID="your_application_uuid"
python scripts/list_networks.py list --status active,in_review --risk-band high
python scripts/list_networks.py list --signal-type device,ip_address --min-size 3 --ordering=-last_activity_at
python scripts/list_networks.py get 2b7e1f0c-4d3a-4e5b-9c6d-7e8f9a0b1c2d
python scripts/list_networks.py members 2b7e1f0c-4d3a-4e5b-9c6d-7e8f9a0b1c2d
python scripts/list_networks.py lookup --session-id 11111111-2222-4333-8444-555555555555
python scripts/list_networks.py lookup --transaction-id 3b9d2c1a-7e4f-4a6b-8c5d-0e1f2a3b4c5d --party-id b1111111-2222-4333-8444-555555555555
```
