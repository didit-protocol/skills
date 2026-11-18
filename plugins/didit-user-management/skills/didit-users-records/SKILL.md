---
name: didit-users-records
description: Finds and manages the people they verified with Didit (user records). Use when the user says "find this customer", "look up a user", "pre-register a user", "update their email or phone", "flag this user", "block a user", "unblock", or "delete user records" in their Didit account.
---

# Vendor users (the people you verify)

Follow the rules of didit-users-start first: call `didit_context_get` and pick the application.

A vendor user is one of your end customers, identified by `vendor_data`, your own identifier for them. Their verification sessions are grouped under that `vendor_data`.

## 1. Find a person

- `didit_vendor_user_search` finds people across every organization and application the person can open, when you do not know which application a customer is in. Filters: `search` (name, email or `vendor_data`), `vendor_data`, `status`, `date_from`/`date_to` or `last_n_days`, `limit` (default 20, at most 200). Each hit is tagged with its organization and application.
- `didit_vendor_user_list` lists the users of one application, with `limit` and `offset`.
- `didit_vendor_user_get` with `vendor_data` returns one user's details.

Report what the tools return about the user's sessions and status. Do not assume fields that are not in the result. The record's `didit_internal_id` is what `didit_case_create` takes as `subject.uuid`.

## 2. Create a user

`didit_vendor_user_create` pre-registers a person. Required: `vendor_data`. Optional: `full_name`, `display_name`, `date_of_birth` (YYYY-MM-DD), `status`, `metadata`, `approved_emails`, `approved_phones`, `issuing_states`.

Show the fields and wait for a yes before creating it.

## 3. Update a user

- `didit_vendor_user_update` with `vendor_data` changes only the fields you send (the same fields as create).
- `didit_vendor_user_update_status` with `vendor_data` and `status` (`ACTIVE`, `FLAGGED` or `BLOCKED`) changes only the monitoring status. Prefer it when only the status changes.

State the old and new values and wait for a clear yes before each change.

## 4. Delete users

`didit_vendor_user_delete` permanently deletes users.

- Pass `vendor_data_list` for specific users. List them by `vendor_data` and name and ask the person to confirm before calling.
- `delete_all: true` deletes every user of the application. It needs `confirm: true`, sent only after the person confirmed deleting every user in this conversation. Say plainly that it cannot be undone.
- A `409` means nothing was deleted: `in_filed_report` (a selected person is in a finalized regulatory report) or `subject_deletion_in_progress` (another deletion is still running). Explain which and suggest repeating once the other deletion has finished.

## Related tasks

- To block the face, document, phone or email of one of their sessions, see didit-users-lists.
- To start a new verification for them, use the `didit` plugin's verification skills or the Didit console.

## What good output looks like

- For a search: a short table of `vendor_data`, name, status and application, with the number of results.
- For one user: status first, then the fields the tool returned.
- A clear question naming each user before any update or deletion.

## Do not

- Never ask for credentials (password, API key, one-time code).
- Never fall back to raw HTTP calls (curl/REST) for a console task.
- Never invent a `vendor_data` value or a user field.
- Never use `delete_all` unless the person explicitly asked to delete every user.
- Never state prices. Link https://didit.me/pricing.
