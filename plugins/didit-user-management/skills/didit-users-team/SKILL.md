---
name: didit-users-team
description: Used when someone wants to see who is in their Didit organization, list roles, invite a teammate, change a member's role or the applications they can access, remove a member, list or create an API key for an application, or read their organizations and applications.
---

# Workspace team, API keys and applications

Follow the rules of didit-users-start first: call `didit_context_get` and pick the organization. This skill is about your own Didit workspace, not the people you verify.

## 1. Organizations and applications

- `didit_context_get` is the quickest way to see every organization and application with their ids and whether each application is sandbox or live.
- `didit_org_list` lists organizations; `didit_org_list_applications` with `organization_id` lists its applications.
- `didit_org_get_application` with `organization_id` and `application_id` returns application details. The API key in it is redacted: a masked preview and an `api_key_set` flag.
- `didit_org_get_balance` returns the organization's credit balance. Report the fields it returns; never state prices, link https://didit.me/pricing.

## 2. Members and roles

- `didit_org_list_members` lists members. Each row has a `uuid` (what remove and update take) and a `user_id` (what case assignment takes).
- `didit_org_list_roles` lists the roles with their ids.
- `didit_org_invite_member`: `emails` (1 to 5), `role` (a role id from `didit_org_list_roles`) and `app_ids` (application ids from `didit_context_get` or `didit_org_list_applications`). Repeat the emails, role name and applications and wait for the person to confirm before inviting.
- `didit_org_update_member`: `member_id`, `role` and `accessible_applications` (the full list after the change). State the old and new role and applications and wait for a yes.
- `didit_org_remove_member`: `member_id`, the member row's `uuid` (not `user_id`, not the email). It cannot be undone; the person would need a new invitation. Name the member and wait for the person to confirm.

## 3. API keys

- `didit_org_list_api_keys` with `application_id` lists one application's key metadata. Raw key values are redacted.
- `didit_org_create_api_key` issues a credential for one application. Required: `organization_id`, `application_id`, `confirm: true`. Optional: `label`, `scopes` (resource to `read` or `write`), `workflow_ids` (needs `scopes`), `expires_at`.

Before creating a key:

1. Pick the application by its mode in `didit_context_get`: a sandbox key to build and test, a live key to go live.
2. State the application, label, scopes and expiry, and ask the person to confirm. Send `confirm: true` only after that yes.
3. The secret is returned once. Show it to the person once, or write it straight to the project's secret store or `.env` if they asked. Never store it in notes or memory, never repeat it later in the chat.

Didit allows one live key per connected app and application, scoped to what the signed-in person can do. The person can revoke it in the console.

## What good output looks like

- Members as a table: name or email, role, applications.
- The exact invitation, role change or removal stated before it runs.
- For a new API key: the application and its mode named, and the secret shown once.

## Do not

- Never ask for credentials (password, API key, one-time code).
- Never fall back to raw HTTP calls (curl/REST) for a console task.
- Never invent role ids, member ids or application ids.
- Never repeat, log or store an API key secret after showing it once.
- Never state prices. Link https://didit.me/pricing.
