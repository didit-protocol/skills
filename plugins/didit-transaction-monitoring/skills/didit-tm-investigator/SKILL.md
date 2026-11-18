---
name: didit-tm-investigator
description: Used when someone wants to work the Didit AI Investigator queue, read why it recommended approving, declining, escalating or requesting information on an item, accept or override its recommendations, ask it to review an item again, answer its policy questions, back-test its policy, or read its performance, dashboard and activity log.
---

# The AI Investigator

Follow the rules of didit-tm-start first: call `didit_context_get` and pick the application.

The Investigator reviews verifications, businesses, transactions and cases and recommends an action. Every decision stays with a person. Get the person's agreement to the exact item and action before each decision tool. The tools that declare `confirm` are named below; send `confirm: true` to them only after that agreement in this conversation.

## 1. Read the queue and reports

- `didit_investigator_queue_list` lists open reports, Ready to accept first. Each row has `run_id`, the item, the recommendation (`approve`, `decline`, `escalate`, `request`), the confidence and `ready_to_accept`. Filters: `scope` (`all`, `identity`, `transactions`), `kind` (`session`, `business_session`, `transaction`, `case`), `queue` (`kyc`, `kyb`, `aml`, `transactions`, `cases`), `recommendation`, `confidence` (`high`, `moderate`, `low`), `ready`, `search`, `limit`, `offset`.
- `didit_investigator_report_get` with `run_id` returns the full report: recommendation, confidence, risk, narrative, the policy rules it relied on, evidence with sources, guardrails, similar past decisions, questions and provenance.
- `didit_investigator_record_get` with `session_id` or `transaction_id` returns the newest review of that record, open or decided, or null when there was none. A case's review is in `didit_case_get`.

When explaining a report, give the recommendation and confidence first, then the policy rules and evidence it cites, in plain words.

## 2. Decide

Before each call, state the item, the recommendation and the exact action, and wait for the person to confirm.

- `didit_investigator_accept`: `run_id`, optional edited `narrative` (an edit makes it "edited and accepted"), `confirm: true`. The item is decided through its normal route and logged under the person's name.
- `didit_investigator_override`: `run_id`, `action` (`approve`, `decline`, `escalate`, `request`), `category` (`missing_context`, `needs_information`, `policy_differs`, `evidence_misread`, `other`), `reason` (10 to 500 characters), `confirm: true`. Repeated overrides become policy questions.
- `didit_investigator_batch_accept`: `run_ids` (1 to 50 ready items), `confirm: true`. List every item and its recommendation first. Items that cannot be accepted are skipped with a reason: report them.

## 3. Add a fact or review again

- `didit_investigator_add_note`: `run_id` and `note` (up to 2,000 characters, in the person's words). The Investigator reads it on its next review; it does not re-evaluate by itself.
- `didit_investigator_rereview`: `run_id`, optional `note`, `confirm: true`. Name the report and wait for the person to confirm the re-review first. A fresh review starts in the background and replaces the open report. Only an open, finished report can be re-reviewed (`409 not_rereviewable`), one at a time (`409 rereview_pending`). Read the new report from the queue once it is ready.

## 4. Policy questions

- `didit_investigator_question_list` (filter `status`: `open`, `answered`, `dismissed`) and `didit_investigator_question_get` (`question_id`) show situations the policy does not cover, with the team's last 30 days on it.
- `didit_investigator_question_answer`: `question_id`, `answer` (`approve`, `decline`, `request`, `person`), optional `detail`, `confirm: true`. An answer writes a new policy version and re-checks waiting reports in that queue. Say so, then wait for the person to confirm.
- `didit_investigator_question_dismiss`: `question_id`, `confirm: true`. Closes it with no policy change. Ask the person to confirm first.

## 5. Back-tests and performance

- `didit_investigator_backtest_start`: `queues` (required), `period_days` (`30` or `90`), `source` (`policy`, `setup`, `sop_draft`). It is free, replays past decisions and decides nothing. Read it with `didit_investigator_backtest_get` (`backtest_id`).
- `didit_investigator_performance_get`: agreement with the team, volume, time saved, calibration, per-queue numbers and overrides over `period` 7, 30 or 90 days.
- `didit_investigator_dashboard_get`: 30-day automation, weekly history, spend, overrides and QA since go-live.
- `didit_investigator_activity_list`: the append-only activity log. Filters: `scope`, `group` (`agent`, `decisions`, `overrides`, `autonomy`), `actor` (`agent` or an email), `since`, `until`.

## What good output looks like

- For the queue: a table of item, recommendation, confidence and ready flag, ready items first.
- For a report: recommendation and confidence on the first line, then the reasons it cites.
- A clear question naming the exact item and action before every decision, re-review or policy answer.

## Do not

- Never ask for credentials (password, API key, one-time code).
- Never fall back to raw HTTP calls (curl/REST) for a console task.
- Never accept, override or answer anything the person did not approve in this conversation.
- Never invent run ids, question ids or report content.
- Never state prices. Link https://didit.me/pricing.
