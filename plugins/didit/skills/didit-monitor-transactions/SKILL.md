---
name: didit-monitor-transactions
description: Monitors transactions in their Didit account, from flagged transactions to rules, wallet screening and the Travel Rule. Use when the user asks "why was this transaction flagged", says "submit a transaction", "monitoring rule", "back-test this rule", "how often would it fire", "screen a wallet", "where do alerts go", or asks about Travel Rule transfers and VASPs with Didit.
---

# Monitor transactions

Follow the rules of didit-connect first: call `didit_context_get` and pick the application when there are several.

## 1. Look up transactions

- `didit_transaction_search` lists transactions across applications, newest first: `status`, `search`, `last_n_days` or `date_from` and `date_to`, `limit`.
- `didit_transaction_get` with `transaction_id` returns one transaction and its rule results.

Explain which rules fired, what each one checks, and the resulting status.

## 2. Submit a transaction

`didit_transaction_create` sends a transaction for monitoring and runs the rules on it.

- Required: `transaction_id` (the customer's own id), `transaction_category` (`finance`, `kyc`, `travel_rule`, `user_event`, `audit_trail_event`, `gambling_bet`, `gambling_limit_change`, `gambling_bonus_change`), `transaction_details` and `subject`.
- The shapes of `transaction_details` and `subject` depend on the category. Look them up with `didit_docs_search` before building one; do not guess field names.
- Optional: `counterparty`, `transaction_at`, `custom_properties`, `include_crypto_screening`.

This records a real transaction in the application. In a live application this can use your Didit credits: past the plan's monthly allowance a transaction is charged, an outbound Travel Rule transfer can be charged in its place, and `include_crypto_screening` adds a wallet screening billed on its own. Treat a mode that is unknown as live. Show the payload with that notice and wait for the person to agree before calling it. Never state a price: link https://didit.me/pricing.

## 3. Rules

- `didit_transaction_rule_list` shows the rules of one application. Filter by `source` (`PRESET` or `CUSTOM`), `mode` (`ACTIVE`, `TEST`, `DISABLED`), `category` or `search`.
- `didit_transaction_rule_backtest` dry-runs a rule definition (`conditions`, `aggregation`, `evaluation_mode`, `scope`, `period_days` from 1 to 365, default 90) against at most the 10,000 most recent transactions of the application. It writes nothing. The window is rolling days back from today, not a calendar period: for "last quarter" use `period_days: 90` and say it is the last 90 days, and mention the 10,000 cap when the application has more.
- `didit_transaction_rule_create` saves a custom rule. Required: `title` (unique in the application), `category`, `mode` and `actions`. Include every outcome the person asked for (review, decline, approve, score, case) in `actions`; pass an empty list only for a monitor-only rule.

Recommended order:

1. Back-test the exact conditions first and report the hit rate.
2. Create the rule with `mode: "TEST"` so it records hits without acting. Pass the same `conditions`, `aggregation`, `evaluation_mode` and `scope` that were back-tested, plus `actions`; the back-test saves none of them.
3. Switch it to `ACTIVE` only after the person reviews the test hits.

Confirm the title, conditions, actions and mode with the person before creating the rule.

## 4. Screen a wallet

`didit_transaction_screen_wallet` checks one crypto address without creating a transaction.

- `wallet_address` and `blockchain` (`BTC`, `ETH`, `LTC`, `XRP`, `BCH`, `DOGE`, `TRX`, `SOL`, `MATIC`, `BNB`, `USDT`, `USDC`) are required. Optional `direction`.
- It returns a risk score, severity, any sanctions hit and the source or destination of funds.
- It needs transaction monitoring configured for the application. In a live application this can use your Didit credits; treat a mode that is unknown as live. Say so and wait for a yes. Never state a price: link https://didit.me/pricing.

## 5. Alert channels

`didit_alert_list` lists where the application sends alerts (email or Slack), with the destination and whether each channel is on. A Slack webhook URL is a posting credential: show only `hooks.slack.com/...` and the last 4 characters, and mask email addresses to the first letter and the domain.

## 6. Travel Rule

The hosted server lists 23 Travel Rule tools (for example `didit_travel_rule_get_settings`) for crypto transfers between VASPs: settings, the VASP directory, counterparty contacts, the wallet address book and ownership confirmation, messages with the counterparty, transfer actions, networks and the due-diligence questionnaire, and sandbox tests.

- Read before acting: `didit_travel_rule_get_settings`, `didit_travel_rule_search_vasps`, `didit_travel_rule_list_networks` (only the states `own_membership` and `live_through_didit` route transfers; report each state as returned).
- Every Travel Rule change needs the person's agreement first. Sending a message, setting a counterparty VASP, confirming wallet ownership and finishing or cancelling a transfer reach the counterparty or cannot be undone: show the exact action and wait for a clear yes. None of these tools declares `confirm`.
- For the full recipes, install the `didit-transaction-monitoring` plugin and use its didit-tm-travel-rule skill, or read each tool's schema with `didit_tool_describe`.

## What good output looks like

- For a flagged transaction, the rules that fired and why, in plain words.
- For a new rule, the back-test hit count and rate before anything is saved.
- For a wallet, the risk score, severity and any sanctions hit on the first line.
- A clear question before any transaction, rule or billable screening is created.

## Do not

- Never ask for credentials (password, API key, one-time code).
- Never fall back to raw HTTP calls (curl/REST) for a console task.
- Never invent transaction ids, rule fields or wallet addresses.
- Never state prices. Link https://didit.me/pricing.
