---
name: didit-users-lists
description: Used when someone wants to see, create, rename or delete Didit lists (allowlists and custom lists), add or remove list entries, add a face to a face list from a photo, block or unblock the face, document, phone or email of a verification session, read the blocklist, or trust a session's phone number.
---

# Lists, blocklist and allowlist

Follow the rules of didit-users-start first: call `didit_context_get` and pick the application. Lists belong to one application.

## 1. Read lists

- `didit_lists_list` lists the application's lists. Filters: `list_type` (`blocklist`, `allowlist`, `custom`), `entry_type`, `limit`, `offset`.
- `didit_lists_get` with `list_uuid` returns one list.
- `didit_lists_entries_list` with `list_uuid` lists its entries. Filters: `search` (value or label), `reference_session_id` (only entries created from that session), `limit`, `offset`.

Entry types: `face`, `document`, `phone`, `email`, `ip_address`, `device_fingerprint`, `wallet_address`, `bank_account`, `user`, `business`, `country`, `key`.

## 2. Create, rename or delete a list

- `didit_lists_create`: `name` (unique in the application), `list_type` (`allowlist` or `custom`), `entry_type`, optional `description`. System blocklists exist already, one per entry type, and cannot be created.
- `didit_lists_update`: `list_uuid` plus a new `name` and/or `description`. System blocklists cannot be changed.
- `didit_lists_delete`: `list_uuid`. It deletes the list and all its entries; system blocklists cannot be deleted. Say how many entries it holds and wait for the person to confirm.

Show the name, type and entry type and wait for a yes before creating or renaming.

## 3. Add and remove entries

- `didit_lists_entry_create`: `list_uuid`, then either `value` (for example a phone, email or IP) or `reference_session_id` to take the value from a session. Optional: `reference_object_uuid`, `display_label`, `comment`, `metadata`. For a face list with a session, `face_image_source` picks which face (`liveness` by default, or `front_image_camera_front` / `back_image_camera_front`), and `reference_node_id` picks the ID verification step when there are several.
- `didit_lists_entry_upload_face`: `list_uuid` of a face list plus the image as `image_base64` (or an attachment reference) on the hosted server. Use it only with real image bytes the person attached; never ask them to paste base64 text.
- `didit_lists_entry_delete`: `list_uuid` and `entry_uuid`. It also unblocks the underlying user or business when that applies. Show the entry and wait for the person to confirm.

Show the list and the value or session before adding an entry and wait for a yes.

## 4. Blocklist from a session

- `didit_blocklist_get` lists what is blocked (faces, documents, phones, emails), newest first, each with the `session_id` it came from. Filter `item_type`; page with `limit` and `offset`.
- `didit_blocklist_add`: `session_id` and at least one of `blocklist_face`, `blocklist_document`, `blocklist_phone`, `blocklist_email` set to true. A flag works only if the session holds that item. Later sessions of the application with the same item are caught.
- `didit_blocklist_remove`: the `session_id` of the blocklist entry and at least one of `unblock_face`, `unblock_document`, `unblock_phone`, `unblock_email`. Name what will be unblocked and wait for the person to confirm.

## 5. Allowlist a phone

`didit_allowlist_add`: `session_id` and `allowlist_phone: true`. It marks that session's phone number as trusted so phone verification does not turn it away as high risk. A phone number is the only thing that can be allowlisted, and a blocked number stays blocked. Wait for a yes before calling.

## What good output looks like

- Lists as a table: name, type, entry type, number of entries when shown.
- For a block: the session, and exactly which items (face, document, phone, email) are blocked or unblocked.
- A clear question before every deletion, removal or unblock.

## Do not

- Never ask for credentials (password, API key, one-time code).
- Never fall back to raw HTTP calls (curl/REST) for a console task.
- Never try to create, rename or delete a system blocklist.
- Never invent list ids, entry ids or session ids.
- Never state prices. Link https://didit.me/pricing.
