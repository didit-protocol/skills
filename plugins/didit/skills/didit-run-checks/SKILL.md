---
name: didit-run-checks
description: Used when someone wants a single check on one person without a full verification flow, such as screening a name against sanctions, PEP and adverse media lists, checking an ID document or a proof of address, validating identity data against official databases, comparing two faces, searching a face against past users, checking a selfie for liveness, or confirming an email address or phone number with a one-time code.
---

# Run one-off checks

Follow the rules of didit-connect first: call `didit_context_get`, pick the application, and note whether it is sandbox or live.

## Before any check

- Every tool in this skill is a write. In a live application each check uses Didit credits. Say so and wait for the person to agree before the first one. Sandbox checks are free.
- Use `vendor_data` (the person's id in the customer's system) when the person gives one, so the result links to that user.

## Checks that take text

**AML screening:** `didit_verify_aml`
- `full_name` (required). `entity_type` is `person` (default) or `company`.
- `date_of_birth` (YYYY-MM-DD) and `nationality` improve the match. Optional `document_number`.
- `include_adverse_media: true` adds adverse media. `include_ongoing_monitoring: true` enrols the entity for ongoing monitoring; ask before setting it.
- Report the hits by list type (sanctions, PEP, adverse media) with their match scores. A possible match is not a confirmed match: say so.

**Database validation:** `didit_verify_database`
- `issuing_state` (required, ISO 3166-1 alpha-3, for example `ESP`) selects the official sources.
- Add what the person has: `first_name`, `last_name`, `date_of_birth`, `document_number`, `document_type` (`P`, `ID`, `DL` and others), `personal_number`, `tax_number`.
- Optional `partial_match_action` and `no_match_action` (`DECLINE` or `NO_ACTION`).

## Checks that take files

On the hosted server, every file goes in a `<field>_base64` argument, as raw base64 or a data URL:

| Tool | File arguments |
|---|---|
| `didit_verify_id` | `front_image_base64` (and `back_image_base64`), optional `perform_document_liveness`, `minimum_age` |
| `didit_verify_poa` | `document_image_base64`, optional `expected_address`, `expected_country` (ISO alpha-2), `expected_first_name`, `expected_last_name` |
| `didit_verify_face_match` | `image_1_base64`, `image_2_base64` (order does not matter) |
| `didit_verify_face_search` | `image_base64` (searches every enrolled face of the application) |
| `didit_verify_passive_liveness` | `image_base64` (one selfie, no interaction) |

Use a file check only when your client can pass the real bytes of a file the person attached. Never ask the person to paste base64 text, and never make up image content.

If the client cannot pass the file, create a verification session instead (see didit-verify-people) with a workflow that has the right step, and share its link. The person being checked then uploads the document or takes the selfie themselves.

## Email and phone codes

These reach a real person. Confirm the address or number, and that the person being checked expects a code, before sending.

1. `didit_verify_email_send` with `email`, or `didit_verify_phone_send` with `phone_number` (with country code, for example `+34600000000`). Phone codes go by WhatsApp first and fall back to SMS. A code is valid for 5 minutes.
2. The person being checked reads the code they received and tells the operator.
3. `didit_verify_email_check` with `email` and `code`, or `didit_verify_phone_check` with `phone_number` and `code`. Each code allows 3 attempts.

In a sandbox application the phone send is mocked and the check approves any code. In a live application a phone send answers an error until the organization has credits.

## Reading results

Lead with the outcome (approved, declined, needs review, match or no match), then the two or three facts that decided it. Keep personal data to what the person needs.

## What good output looks like

- One line naming the check, the application, and sandbox or live.
- The outcome first, then the key evidence, then any warning.
- For file checks the client could not pass, a verification link instead of a request for base64.
- A clear question before any billable check or any code sent to a real person.

## Do not

- Never ask for credentials (password, API key, one-time code to sign in). The verification code a checked person receives is not a credential of the operator.
- Never fall back to raw HTTP calls (curl/REST) for a console task.
- Never invent ids, names or image data.
- Never state prices. Link https://didit.me/pricing.
