---
name: didit-tm-transactions
description: Used when someone wants to find monitored transactions, read one transaction and why it was flagged or which rules fired, list the transactions of one application, or submit a new transaction for monitoring in their Didit account. Covers search filters, the rule-evaluation result and the submit payload.
---

# Transactions

Follow the rules of didit-tm-start first: call `didit_context_get` and pick the application when there are several.

## 1. Find transactions

- `didit_transaction_search` searches across every organization and application the person can open, newest first. Leave out `organization_id` and `application_id` to span everything, or pass them to narrow. Filters: `status`, `search` (free text), `date_from` and `date_to` (ISO dates) or `last_n_days`, and `limit` (default 20, at most 200). Each hit is tagged with its organization and application.
- `didit_transaction_list` lists the transactions of one application, with `limit` and `offset` for paging. Use it when the person works inside one application and wants to page through it.

Prefer the search for "find the transaction for this customer" or "what was flagged this week". Status values come from the results: read them there instead of guessing a list.

## 2. Read one transaction and its risk outcome

`didit_transaction_get` with `transaction_id` returns one transaction and its rule-evaluation result.

When you explain it:

1. Say the transaction's status first.
2. List the rules that matched, by the titles the result gives, and what each one checks.
3. Say what the matches did (for example a score added, a status change, a tag or a case opened), as the result shows it.
4. If a rule is only in TEST mode, say it recorded the hit without acting.

To read a rule in full, pass its id to `didit_transaction_rule_get` (see didit-tm-rules). To see whether the AI Investigator reviewed this transaction, use `didit_investigator_record_get` with `transaction_id` (see didit-tm-investigator).

## 3. Submit a transaction

`didit_transaction_create` records a transaction in the application and runs its rules on it.

- Required: `transaction_id` (the customer's own unique id), `transaction_category`, `transaction_details` and `subject` (the party that started the transaction, usually a `vendor_data` reference).
- `transaction_category` is one of `finance`, `kyc`, `travel_rule`, `user_event`, `audit_trail_event`, `gambling_bet`, `gambling_limit_change`, `gambling_bonus_change`. The shapes of `transaction_details` and `subject` depend on it.
- Optional: `counterparty`, `transaction_at` (ISO timestamp), `time_zone`, `custom_properties` (values rules read as `custom_values.<key>`), `travel_rule_details`, `network_snapshot`, `include_crypto_screening`.

Before building a payload, call `didit_docs_search` for the category's field names. Do not guess them.

This writes a real transaction that real rules act on. In a live application this can use your Didit credits: past the plan's monthly allowance a transaction is charged, and an outbound Travel Rule transfer can be charged in its place. In a live application, or one whose mode is unknown, say so with the full payload and wait for the person to agree before calling it. `include_crypto_screening` adds a wallet screening that is billed on its own: name it separately in the same question. Never state a price: link https://didit.me/pricing.

## 4. Next steps after a flagged transaction

- Open a case about it with `didit_case_create`, passing a link with `entity_type: "transaction"` (see didit-tm-alerts-cases). Confirm the title and priority first.
- Screen the counterparty wallet (see didit-tm-wallet-screening).
- Tune the rule that fired, after a back-test (see didit-tm-rules).

## What good output looks like

- For a flagged transaction: the status, then each rule that fired and why, in plain words.
- For a search: a short table with transaction id, status, date, application, and a count of results.
- For a new transaction: the payload shown, the billing notice in a live application, and a clear question before it is sent.

## Do not

- Never ask for credentials (password, API key, one-time code).
- Never fall back to raw HTTP calls (curl/REST) for a console task.
- Never invent transaction ids, rule titles, status values or payload fields.
- Never state prices. Link https://didit.me/pricing.
