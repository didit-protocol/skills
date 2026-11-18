---
name: didit-review-queue
description: Used when a compliance analyst or operator wants to see verifications waiting for manual review, look up a person's session by name, email or number, decide whether to approve or decline a session in review, add a review note, read a session's review history, or work on compliance cases (assign, comment, escalate, resolve, reopen).
---

# Review queue and cases

Follow the rules of didit-connect first: call `didit_context_get` and pick the application when there are several.

## 1. Find what needs review

Call `didit_session_search`:

- `status: "In Review"` for the queue. Several statuses can be combined with commas, for example `"In Review,Resubmitted"`.
- `search` matches name, email, `vendor_data`, document or phone number. `S-<number>` finds a user verification by its number, and `B-<number>` with `session_kind: "business"` finds a business one.
- `last_n_days`, or `date_from` and `date_to`, narrow the window. `limit` defaults to 20.
- Leave out `organization_id` and `application_id` to search every application at once.

Show the results as a short table: session number or id, name, status, date, application.

## 2. Understand one session

- `didit_session_explain_decision` with `session_id` gives the reason it is in review: the deciding feature, the warnings that had an effect with their values, triggered rules, and the setting that controls each cause. Start here.
- `didit_session_list_reviews` with `session_id` lists the review history and activity log, newest first (`limit`, `offset`).

Summarize: what triggered the review, what the evidence shows, and what a reviewer usually needs to check. Leave the decision to the person.

## 3. Record a review note

`didit_session_add_review` adds a note to the audit trail:

- `session_id` (required) and `comment`.
- An optional `new_status` records a status with the note. Show the note and status to the person and wait for them to agree before calling it with a status.

## 4. Approve, decline or ask for a resubmission

`didit_session_update_status` overwrites the decision and cannot be undone.

- `session_id`, `new_status` (`Approved`, `Declined` or `Resubmitted`) and a `comment`.
- For `Resubmitted`, pass `nodes_to_resubmit` with the `node_id` values from `didit_session_explain_decision`.
- `send_email: true` sends a notification that cannot be recalled.

Before calling it, confirm the session, the new status and any email recipient with the person. Call it only after they agree to that exact change.

## 5. Work cases

- `didit_case_search` lists cases across applications (`status`, `search`, `last_n_days`, `limit`).
- `didit_case_get` with `case_id` returns one case with its details.
- `didit_case_manage` acts on a case: `case_id`, `action` (`assign`, `resolve`, `reopen`, `escalate`, `comment`, `update`) and a `data` payload, for example `{ "assignee_id": "..." }` or `{ "comment": "..." }`.

Every `didit_case_manage` call changes the case, so confirm the action and its payload with the person first. Filing a regulatory report (a SAR: any action whose `data.status` is `SAR_FILED`, for example `resolve` with that status) also needs `confirm: true`: send it only after the person has agreed to that exact filing in this conversation. No other tool in this skill takes `confirm`; `didit_session_update_status` is irreversible but is confirmed by asking, not by a flag.

## What good output looks like

- A short table of the queue with the newest first.
- For each session discussed, the reason it is in review in one or two sentences, from `didit_session_explain_decision`.
- The exact change proposed (session, new status, note, email) and a clear question before it is made.
- After a change, the new status read back from the tool result.

## Do not

- Never ask for credentials (password, API key, one-time code).
- Never fall back to raw HTTP calls (curl/REST) for a console task.
- Never invent session, case, node or member ids. Read them from tool results.
- Never approve or decline on your own judgment. The person decides.
- Never state prices. Link https://didit.me/pricing.
