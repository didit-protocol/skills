---
name: didit-tm-alerts-cases
description: Manages monitoring alerts, webhook destinations and compliance cases in their Didit account. Use when the user asks "where do alerts go", says "send alerts to Slack", "change the alert email", "set up a webhook", "open a case", "assign this case", "escalate", "resolve the case", "file a SAR", "reopen", or asks for case statistics in Didit.
---

# Alerts, webhooks and cases

Follow the rules of didit-tm-start first: call `didit_context_get` and pick the application.

## 1. Alert channels

- `didit_alert_list` lists the application's alerts, one per channel: `alert_type` (`email` or `slack`), the destination (`value`) and whether it is on (`is_active`).
- `didit_alert_configure` changes one channel: `alert_type` plus `data` with `value` (an email address, or a Slack webhook URL) and/or `is_active`. A channel with no destination is always off.
- If it answers `409 legacy_alerts_read_only`, that application's alerts are managed in the console's Notification settings. Say so; do not retry.

A Slack webhook URL is a posting credential, and an email address is personal data. Show the channel, the on/off state and a masked destination (for Slack only `hooks.slack.com/...` plus the last 4 characters, for email the first letter and the domain), never the full value. Describe the change and wait for the person to confirm before changing it.

## 2. Webhook destinations

- `didit_webhook_list` and `didit_webhook_get` (`destination_uuid`) show destinations with their URL, version, enabled flag and subscribed events. Signing secrets are redacted. Show each URL masked: the host, then `...` and the last 4 characters.
- `didit_webhook_create` needs `label` and an HTTPS `url`. Optional: `enabled`, `webhook_version` (`v1`, `v2`, `v3`), `subscribed_events` (omit to receive all). For event names, call `didit_docs_search`.
- `didit_webhook_update` needs `destination_uuid` (from the list) and overwrites the fields you send. A new URL redirects future deliveries, `enabled: false` stops them, and `subscribed_events` replaces the whole list.
- `didit_webhook_delete` needs `destination_uuid` and removes a destination so it stops receiving events. It also declares the optional `organization_id` and `application_id`; send them as the start rules say. It takes no `confirm`.

These send account data to an address outside Didit or stop deliveries. Show the label, the masked URL and the events, and wait for the person to confirm each create, update or delete.

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
- Never print a webhook signing secret, a full webhook URL or a full alert destination.
- Never invent case ids, member ids or event names.
- Never state prices. Link https://didit.me/pricing.
