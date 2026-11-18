---
name: didit-verify-people
description: Verifies people (KYC) in their Didit account with verification links, workflows and decisions. Use when the user says "verify a customer", "send a KYC link", "create a verification session", "set up an ID and selfie check", "what is the status of this verification", "why was it declined", "ask them to redo the selfie", or wants to test a verification flow in a Didit sandbox.
---

# Verify people (KYC)

Follow the rules of didit-connect first: call `didit_context_get`, pick the application, and note whether it is sandbox or live.

## 1. Pick or create a workflow

A workflow defines the steps a person goes through.

1. Call `didit_workflow_search` (optional `search` on the label) to list the workflows. Each row has a stable `workflow_id`; use that one for sessions.
2. If one fits, use it. Tell the person its label and steps.
3. If none fits, build one with `didit_workflow_create`:
   - `features`: the steps in execution order, each as `{ "feature": "OCR" }` with an optional `config` and `label`. Put dependencies first, for example `OCR` before `FACE_MATCH`. Example: `[{"feature":"OCR"},{"feature":"LIVENESS"},{"feature":"FACE_MATCH"},{"feature":"AML"}]`.
   - `workflow_label`: a name of at most 50 characters.
   - `status: "draft"` keeps it unpublished; omit it to publish.
   - A workflow verifies a person or a business, never both. For a company use didit-verify-businesses.

   A complete call, kept as a draft:

   ```json didit_workflow_create
   {"workflow_label": "ID and selfie with AML", "status": "draft", "features": [{"feature": "OCR"}, {"feature": "LIVENESS", "config": {"face_liveness_method": "PASSIVE"}}, {"feature": "FACE_MATCH"}, {"feature": "AML"}]}
   ```

4. Before setting a `config` key you have not used before, call `didit_workflow_get_feature_config_schema` with `feature` (for example `LIVENESS` or `AML`). It lists every accepted key. A key outside it is dropped silently.

Describe the workflow you are about to create and wait for the person to agree before calling `didit_workflow_create`.

If the person asked only for a draft, stop after creating it: report its `workflow_id` and that it is unpublished, and do not create a session. A session with a stable `workflow_id` runs the workflow's live published version, so before issuing a link check in `didit_workflow_search` that the row has `is_live_version: true` (or `status` published). If nothing is published yet, say so and ask whether to publish before creating the session.

## 2. Create the session and share the link

Call `didit_session_create` with:

- `workflow_id` (required): the stable `workflow_id` from step 1.
- `vendor_data`: the person's id in the customer's own system, so later sessions group under one user.
- Optional: `callback` (where to send the person afterwards), `language`, `contact_details`, `expected_details`, `metadata`.
- Sandbox only: `sandbox_scenario` (for example `approve`, `decline_aml_hit`, `review_aml_possible_match`) fixes the outcome so nothing runs for real.

In a live application this can use your Didit credits: say so and wait for a yes before creating a session.

The result carries `session_id` and `url`. Give the person the `url` first: that is the link to send to the customer.

## 3. Read the status and the decision

- `didit_session_get_decision` with `session_id` returns the status and everything that was extracted. Summarize it in plain words: the status, which steps passed or failed, and the main warnings. Do not paste raw images or long field lists.
- `didit_session_explain_decision` with `session_id` answers "why was it declined / in review / approved". It names the feature that decided it, each warning that had an effect, triggered rules, and any reviewer override. Use it for every "why" question instead of reading the whole decision. If it returns `unexplained: true`, say that the record shows no cause; never invent one.

## 4. Change a decision or ask for a resubmission

`didit_session_update_status` overwrites a decision and is irreversible.

- `session_id` and `new_status` (`Approved`, `Declined` or `Resubmitted`) are required. Add a `comment` for the audit trail.
- For a resubmission, set `new_status: "Resubmitted"` and `nodes_to_resubmit` to the node ids of the steps to redo. Take them from the `node_id` values that `didit_session_explain_decision` returns; never guess them. Steps already approved are kept.
- `send_email: true` sends a notification that cannot be recalled. `email_address` overrides the recipient.

Confirm the session, the new status, and any email recipient with the person before calling it. Only call it after they agree to that exact change.

## 5. Test in sandbox

`didit_session_simulate` finishes a session of a sandbox application without anyone going through the flow. It works only in a sandbox application (sandbox applications are free to test in), never in a live one.

- `session_id` (required), then either `new_status` (`Approved`, `Declined`, `In Review`, `Expired`, `Abandoned`) or a `scenario` slug, and optional `risk` or `comment`.
- `send_webhooks` defaults to true, so the customer's webhook endpoint receives the same events as a real run.
- Read the result with `didit_session_get_decision`.

If the application is live, do not try it: offer to switch to a sandbox application.

## What good output looks like

- The verification URL to share, on its own line, right after creating the session.
- The application (sandbox or live) and the workflow label that was used.
- Status and decision in plain words, with the reason from `didit_session_explain_decision` when it was not approved.
- A clear question before any billable session or decision change.

## Do not

- Never ask for credentials (password, API key, one-time code).
- Never fall back to raw HTTP calls (curl/REST) for a console task.
- Never invent workflow, session or node ids. Read them from tool results.
- Never state prices. Link https://didit.me/pricing.
