---
name: didit-verify-businesses
description: Used when someone needs to verify a company (KYB), look a business up in an official company registry, check which registry data is available for a country, send a business a verification link, or find and read a business that was already verified in their Didit account.
---

# Verify businesses (KYB)

Follow the rules of didit-connect first: call `didit_context_get`, pick the application, and note whether it is sandbox or live.

## 1. See what registries cover

`didit_workflow_get_kyb_registry_catalog` shows, per country, which company data the registries offer (basic profile, shareholders, beneficial owners) and whether ongoing registry monitoring is available.

- Without arguments it returns a summary. Pass `countries` (ISO alpha-2, for example `["ES","DE"]`) for the exact table.
- Read it before promising shareholder or beneficial-owner data for a country.
- The catalog also lists prices. Do not repeat them; link https://didit.me/pricing.

## 2. Quick registry lookup

For a one-off lookup without a verification flow:

1. `didit_verify_kyb_search` with `country_code` (required, ISO alpha-2) and `name` and/or `registration_number`. Optional `search_type`: `contains`, `start_with` or `fuzzy`.
2. Show the candidates and let the person pick the right company.
3. `didit_verify_kyb_select` with the chosen candidate's `kyb_response_id`. The record carries `registry_status` and `verification_status` (verified, failed or unknown).

Both calls are writes and are billable in a live application. Say so and wait for a yes before the first one.

## 3. Full KYB with a verification link

When the business itself should submit details and documents, use a KYB workflow and a session. The tools are the ones described in didit-verify-people:

1. `didit_workflow_search` to find an existing KYB workflow.
2. If none exists, `didit_workflow_create` with KYB features only, for example `[{"feature":"KYB_REGISTRY"},{"feature":"KYB_DOCUMENTS"},{"feature":"KYB_KEY_PEOPLE"}]`. Do not mix in person-only features such as `OCR` or `LIVENESS`. To verify the people behind the company, create a separate KYC workflow and link it from the `KYB_KEY_PEOPLE` step. Check config keys with `didit_workflow_get_feature_config_schema` first. Confirm the workflow with the person before creating it.
3. `didit_session_create` with the KYB `workflow_id` and the business's id as `vendor_data`. Give the person the returned `url` to send to the business.
4. Read the result with `didit_session_get_decision` and the reason with `didit_session_explain_decision`. Summarize the registry match, the documents received, the key people found and any warning.

## 4. Businesses already verified

- `didit_vendor_business_search` finds businesses across applications by `search` (name, registration number, `vendor_data`), `status` or date.
- `didit_vendor_business_get` with `vendor_data` returns one business with its details.

## Limits

- These tools do not add or edit beneficial owners or business documents directly. Ownership and documents come from the registry and from the business through the verification flow.
- Do not edit a business record. To correct one, point the person to the Business Console at https://business.didit.me.

## What good output looks like

- The company name, country and registration number exactly as the registry returned them.
- The registry and verification status in plain words.
- For a full KYB, the verification URL on its own line.
- What data the registry covers for that country, read from the catalog, when the person asks about owners.

## Do not

- Never ask for credentials (password, API key, one-time code).
- Never fall back to raw HTTP calls (curl/REST) for a console task.
- Never invent registration numbers, candidate handles or business ids.
- Never state prices. Link https://didit.me/pricing.
