---
name: didit-tm-alerts-cases
description: Used when someone wants to see or change where Didit monitoring alerts are sent (email or Slack), manage webhook destinations for monitoring events, or find, open, assign, escalate, comment on, resolve or reopen compliance cases and read case statistics in their Didit account.
---

# Alerts, webhooks and cases

Follow the rules of didit-tm-start first: call `didit_context_get` and pick the application.

## 1. Alert channels

- `didit_alert_list` lists the application's alerts, one per channel: `alert_type` (`email` or `slack`), the destination (`value`) and whether it is on (`is_active`).
- `didit_alert_configure` changes one channel: `alert_type` plus `data` with `value` (an email address, or a Slack webhook URL) and/or `is_active`. A channel with no destination is always off.
- If it answers `409 legacy_alerts_read_only`, that application's alerts are managed in the console's Notification settings. Say so; do not retry.

Show the channel, destination and on/off state, and wait for a yes before changing it.

## 2. Webhook destinations

- `didit_webhook_list` and `didit_webhook_get` (`destination_uuid`) show destinations with their URL, version, enabled flag and subscribed events. Signing secrets are redacted.
- `didit_webhook_create` needs `label` and an HTTPS `url`. Optional: `enabled`, `webhook_version` (`v1`, `v2`, `v3`), `subscribed_events` (omit to receive all). For event names, call `didit_docs_search`.
- `didit_webhook_update` overwrites the fields you send. A new URL redirects future deliveries, `enabled: false` stops them, and `subscribed_events` replaces the whole list.
- `didit_webhook_delete` removes a destination so it stops receiving events.

These send account data to an address outside Didit or stop deliveries. Show the destination, the URL and the events, and wait for the person to confirm each create, update or delete.

## 3. Find and read cases

- `didit_case_search` searches cases across every application, newest first: `status`, `search`, `date_from`/`date_to` or `last_n_days`, `limit`.
- `didit_case_list` lists the cases of one application (`status`, `cursor`).
- `didit_case_get` with `case_id` returns one case with its details, including the Investigator's run for it.
- `didit_case_statistics` gives totals, a series over time, the queue, outcomes and workload for a period (the last 30 days unless both `date_from` and `date_to` are given, two years at most). Filters: `status` (`OPEN`, `AWAITING_USER`, `RESOLVED`), `priority`, `source` (`MANUAL`, `AML_SCREENING`, `TRANSACTION_RULE`, `WORKFLOW_BUILDER`), `scope` (`identity` or `transactions`), `assigned_to`, `blueprint`.

## 4. Open a case

`didit_case_create` needs `title`, and `subject`, `links` or both.

- `subject`: `type` (`user` or `business`) and `uuid`, the record's `didit_internal_id` from `didit_vendor_user_get` or `didit_vendor_business_get`. It is not their `vendor_data`.
- `links`: up to 20 items with `entity_type` (`session`, `business_session`, `transaction`) and `entity_uuid`.
- Optional: `priority` (`LOW`, `MEDIUM` default, `HIGH`), `assigned_to` (a member's `user_id` from `didit_org_list_members`), `due_at`, `tags`, `blueprint`, `review_duplicates`.
- With `review_duplicates: true`, a `409 case_duplicate_review_required` means a case about the same subject is already open. Show it. Send `separate_incident_reason` only if the person still wants a separate case.

Confirm the title, subject or links, priority and assignee before creating it.

## 5. Work a case

`didit_case_manage` takes `case_id`, `action` (`assign`, `resolve`, `reopen`, `escalate`, `comment`, `update`) and `data` (for example the assignee or the comment).

- Describe the exact action and payload and wait for the person to confirm before each call.
- Filing a SAR is a regulatory action: it needs `confirm: true`, sent only after the person confirmed that exact filing in this conversation.
- Read ids (case, assignee) from tool results. Never invent them.

## What good output looks like

- Cases as a short table: id, title, status, priority, assignee, application.
- The exact change stated before every alert, webhook or case action.
- Statistics with the period they cover.

## Do not

- Never ask for credentials (password, API key, one-time code).
- Never fall back to raw HTTP calls (curl/REST) for a console task.
- Never print a webhook signing secret.
- Never invent case ids, member ids or event names.
- Never state prices. Link https://didit.me/pricing.
