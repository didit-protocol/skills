---
name: didit-reports
description: Reads usage, analytics, credits and plan details and exports data from their Didit account. Use when the user asks "how many verifications this month", "approval rate", "where do people drop off", "compare with last month", "how many credits are left", "what is my balance", "which plan are we on", "top up", or says "export sessions" or "export transactions" from Didit.
---

# Reports, analytics and billing

Follow the rules of didit-connect first: call `didit_context_get`. Everything here is read-only except starting an export, which is a write that needs the person's agreement.

## 1. Analytics

`didit_analytics` aggregates verification numbers across applications in one call:

- Window: `last_n_days`, or `date_from` and `date_to` (YYYY-MM-DD). `include_timeseries: true` adds per-day series.
- It returns status counts, a funnel of how many sessions reached each step (OCR, LIVENESS, FACE_MATCH, AML and others), warnings by risk code, the previous period's counts, per-workflow totals and a conversion rate.
- Leave out `organization_id` and `application_id` to cover everything; pass them to narrow.

Answer the question asked first (for example "312 sessions, 81% approved"), then the comparison with the previous period, then the biggest drop-off step.

## 2. Balance and plan

Needs a person sign-in: on an API key connection `didit_billing_get_plan` is not available (see didit-connect); `didit_org_get_balance` is.

- `didit_org_get_balance` returns the credit balance, auto-refill settings and the monthly credit the organization receives. Answer from its fields. If a field is missing, say you could not read it.
- `didit_billing_get_plan` returns the plan, its status, the next charge, the last payment and any unpaid invoice. `next_steps.plans_url` is where the person changes plan.

Report balances and plan details only as the tools return them. For list prices, link https://didit.me/pricing.

To add credit: `didit_org_top_up` is local server only; on the hosted server credit is added in the Didit console. Give the person `next_steps.top_up_url` from `didit_org_get_balance`, which opens the top-up dialog, and never charge or top up from chat.

## 3. Exports

1. `didit_report_list` shows existing reports, newest first (`status`, `report_type`, `q`, `limit`, `offset`). Check here before starting a new one.
2. `didit_report_export` starts an export job. `kind` is `sessions`, `transactions`, `businesses`, `vendor-users` or `vendor-businesses`, and `data` holds filters and `columns`. For `sessions`, `vendor-users` and `vendor-businesses` an unknown column is refused and the error lists the allowed ones: retry from that list instead of guessing. For `transactions` and `businesses` nothing checks the columns and an unknown one just comes out blank, so take column names from `didit_docs_search` and never guess them. The schema declares no filter keys for `data`: look them up with `didit_docs_search` too, or export without filters. A sessions export with known-good columns:

   ```json didit_report_export
   {"kind": "sessions", "data": {"columns": ["session_number", "vendor_data", "session_status", "workflow_type", "created_at"]}}
   ```

3. `didit_report_get` with `report_id` shows its status (`PENDING`, `PROCESSING`, `READY`, `FAILED`).
4. When it is `READY`, `didit_report_get_download_url` with `report_id` returns a signed link. Give the person the link; do not try to download or paste the file.

Starting an export is a write. Tell the person what will be exported (kind, filters, columns) and start it after they agree.

## What good output looks like

- The number that answers the question, with its date window and application scope.
- A comparison with the previous period when the tool returned one.
- For exports, the report id, its status, and the download link once ready.

## Do not

- Never ask for credentials (password, API key, one-time code).
- Never fall back to raw HTTP calls (curl/REST) for a console task.
- Never invent numbers, report ids or download links.
- Never state prices. Link https://didit.me/pricing.
