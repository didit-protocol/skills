---
name: didit-workspace-admin
description: Administers their Didit workspace (members, webhooks, lists, branding and questionnaires). Use when the user says "invite a teammate", "change someone's role", "remove a member", "set up a webhook", "change the webhook URL", "create a blocklist or allowlist", "custom list", "update the logo", "SMS sender name", or "edit the questionnaire" in their Didit account.
---

# Workspace admin

Follow the rules of didit-connect first: call `didit_context_get` and pick the organization and application when there are several.

Every change in this skill is confirmed with the person first: show what will change and call the tool only after they agree. Most of these tools need an admin role; if one is missing, say so as didit-connect describes.

## 1. Members and roles

Needs a person sign-in: on an API key connection these member and role tools are not available (see didit-connect).

- `didit_org_list_members` lists members. `didit_org_list_roles` lists roles with their ids.
- `didit_org_invite_member`: `emails` (1 to 5), `role` (a role id from `didit_org_list_roles`) and `app_ids` (the applications they may access, from `didit_context_get`). The invitees receive an email.

  ```json didit_org_invite_member
  {"emails": ["name@example.com"], "role": "<role_id from didit_org_list_roles>", "app_ids": ["<application_id>"]}
  ```

  `emails` is a list even for one person, `role` is the role's id (match the role the person named against `didit_org_list_roles`), and `app_ids` lists application ids. All three are required. When the person did not say which applications, list them from `didit_context_get` and ask which ones; never pick for them. With only one application, name it in the confirmation.
- `didit_org_update_member`: `member_id`, `role` and `accessible_applications`.
- `didit_org_remove_member`: `member_id` is the `uuid` of the member's row in `didit_org_list_members`, not the user id or email. It cannot be undone; the person must be invited again to come back.

Confirm the emails, role and applications before inviting, and the member's name before a change or removal.

## 2. Webhooks

- `didit_webhook_list` lists destinations with URL, version, enabled flag and events. Signing secrets come back redacted.
- `didit_webhook_create`: `label` and `url` (HTTPS) are required. Optional `webhook_version` (`v3` is recommended), `subscribed_events` (for example `status.updated`; omit for all) and `enabled`.
- `didit_webhook_update`: `destination_uuid` plus the fields to change. A new URL redirects future deliveries, and `subscribed_events` replaces the whole list.
- `didit_webhook_delete`: `destination_uuid`, plus the optional `organization_id` and `application_id` as didit-connect says. Deliveries stop.

Show each URL masked (the host, then `...` and the last 4 characters), never in full. Confirm the destination and each field change before updating or deleting.

## 3. Lists

- `didit_lists_list` shows blocklists, allowlists and custom lists (filter by `list_type` or `entry_type`).
- `didit_lists_create`: `name` (unique), `list_type` (`allowlist` or `custom`; blocklists already exist, one per entry type) and `entry_type` (for example `email`, `phone`, `face`, `document`, `ip_address`, `wallet_address`, `country`).

## 4. Branding

- `didit_branding_get` returns the current logos and colors of the verification screens.
- `didit_branding_update` sets `sms_sender_name` (1 to 30 characters: letters, digits, spaces and `' & - !`) and the logo images. Images go in `image_square_base64`, `image_rectangular_base64` or `image_favicon_base64`, only when your client can pass the real file bytes. Never ask the person to paste base64.

## 5. Questionnaires

- `didit_questionnaire_list` lists the application's questionnaires.
- `didit_questionnaire_create`: `title` and `form_elements`, an ordered list of questions, each with an uppercase `element_type`, a `title`, `is_required` and, for choice questions, `choices`. The questionnaire's own `title` is a string; each question's `title` is an object of locale to text, for example `{"en": "Main source of funds"}`. `status: "draft"` keeps it unpublished. Each choice is `{ value, label }`.

  ```json didit_questionnaire_create
  {"title": "Source of funds", "status": "draft", "form_elements": [{"element_type": "SINGLE_CHOICE", "title": {"en": "Main source of funds"}, "is_required": true, "choices": [{"value": "salary", "label": "Salary"}, {"value": "savings", "label": "Savings"}]}, {"element_type": "LONG_TEXT", "title": {"en": "Anything else we should know?"}, "is_required": false}]}
  ```

- `didit_questionnaire_update`: `questionnaire_id` plus the fields to change. Sending `form_elements` replaces the whole question list, so include every question to keep, in order. Show the full new list before calling it.

## What good output looks like

- Members, webhooks or lists as a short table.
- The exact change proposed and a clear question before it is made.
- After a change, the new state read back from the tool result.

## Do not

- Never ask for credentials (password, API key, one-time code).
- Never fall back to raw HTTP calls (curl/REST) for a console task.
- Never invent member, role, application, destination or questionnaire ids.
- Never state prices. Link https://didit.me/pricing.
