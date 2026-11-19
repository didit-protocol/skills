---
name: didit-users-businesses
description: Finds and manages the companies they verified with Didit (business records, KYB). Use when the user says "find this business", "look up a company we verified", "create a business record", "flag this business", "block a company", or "delete business records" in their Didit account.
---

# Vendor businesses (the companies you verify)

Follow the rules of didit-users-start first: call `didit_context_get` and pick the application.

A vendor business is a company you verify, identified by `vendor_data`, your own identifier for it.

## 1. Find a business

- `didit_vendor_business_search` finds businesses across every organization and application the person can open. Filters: `search` (company name, registration number or `vendor_data`), `vendor_data`, `status`, `date_from`/`date_to` or `last_n_days`, `limit` (default 20, at most 200).
- `didit_vendor_business_list` lists the businesses of one application, with `limit` and `offset`.
- `didit_vendor_business_get` with `vendor_data` returns one business's details, including its `didit_internal_id`.

## 2. Create a business record

`didit_vendor_business_create` creates a record by hand. Fields: `vendor_data`, `display_name`, `legal_name`, `registration_number`, `country_code` (ISO 3166-1 alpha-2), `status`, `metadata`.

Show the fields and wait for a yes before creating it. To verify the company against official registries, use the `didit` plugin's business verification skill.

## 3. Change the status

`didit_vendor_business_update_status` with `vendor_data` and `status` (`ACTIVE`, `FLAGGED` or `BLOCKED`). State the old and new status and wait for a clear yes.

Profile fields of an existing business (names, registration number, country) cannot be edited from this plugin. Tell the person to change them in the Didit console.

## 4. Delete businesses

`didit_vendor_business_delete` permanently deletes businesses.

- Pass `vendor_data_list` and/or `didit_internal_id_list`. List each business by name and id and ask the person to confirm before calling.
- `delete_all: true` deletes every business of the application. It needs `confirm: true`, sent only after the person confirmed deleting every business in this conversation. Say it cannot be undone.
- A `409` (`in_filed_report` or `subject_deletion_in_progress`) means nothing was deleted. Explain which and suggest repeating once the other deletion has finished.

## Related tasks

- To open a compliance case about a business, use its `didit_internal_id` as `subject.uuid` with `didit_case_create` (in the `didit` or `didit-transaction-monitoring` plugin).

## What good output looks like

- For a search: a short table of `vendor_data`, company name, status and application.
- For one business: status first, then the fields the tool returned.
- A clear question naming each business before a status change or deletion.

## Do not

- Never ask for credentials (password, API key, one-time code).
- Never fall back to raw HTTP calls (curl/REST) for a console task.
- Never invent a `vendor_data` value, registration number or business field.
- Never promise to edit a business's profile fields from chat.
- Never state prices. Link https://didit.me/pricing.
