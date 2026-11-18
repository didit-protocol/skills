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
- `didit_transaction_rule_backtest` dry-runs a rule definition against at most the 10,000 most recent transactions of the application. It writes nothing and takes no `rule_uuid`.
- A back-test is a read, so it needs no agreement: when the person asks how often a rule would fire, build the definition below and run it at once. Use the application they named; if they named none and the context shows several, ask which one, once. Never ask them for field names.
- `didit_transaction_rule_create` saves a custom rule. Required: `title` (unique in the application), `category`, `mode` and `actions`. Include every outcome the person asked for (review, decline, approve, score, case) in `actions`; pass an empty list only for a monitor-only rule.

### Rule definition

The same fields go to `didit_transaction_rule_backtest`, `didit_transaction_rule_create` and `didit_transaction_rule_update`. All are optional on a back-test.

- `conditions`: a list of checks on the transaction being evaluated. Each has `field`, `operator` and usually `value`.
  - `field` examples: `amount`, `currency`, `direction`, `action_type`, `score`, `transaction_type`, `subject_country`, `counterparty_country`, `subject_vendor_data`, `subject_payment_method_type`, `travel_rule_status`, `tags`, `subject_days_since_previous_transaction`, or `custom_values.<key>` for a key sent in `custom_properties`.
  - `operator`: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `in`, `not_in`, `contains`, `not_contains`, `contains_any` (a list of strings), `regex`, `fuzzy_match` (needs `score` 0 to 100), and the presence checks `exists`, `is_not_empty`, `is_not_null`, `not_exists`, `is_empty`, `is_null` (no `value`).
  - Optional `value_type`: `list` (the value is a List UUID), `field` (the value is another field path) or `relative_date`. Leave it out for a literal value.
- `evaluation_mode`: `ALL` (default) or `ANY`, how flat conditions combine. Setting `group_index` on any condition switches to grouped evaluation (`group_logic` and `groups_logic`, each `AND` or `OR`).
- `aggregation`: a list of velocity checks over past transactions; every entry must match. Each needs `metric` (`count`, `sum`, `max`, `min`, `avg`, `distinct_count`, `unique_count`), `operator` (`eq`, `ne`, `gt`, `gte`, `lt`, `lte`), `value` (a number) and `window` (`<N>m` minutes, not months, `<N>h` hours or `<N>d` days). Optional `field` (default `amount`, ignored for `count`) and `filters`: `{"subject_vendor_data": "__current__"}` counts only the same customer's transactions. `scope` selects only the transaction being evaluated and never filters the history, so for a total of outbound funds also put `"direction": "OUTBOUND"` in `filters`.
- `scope`: `transaction_types`, `directions` (`INBOUND`, `OUTBOUND`) and `action_types`, each a list. Left out, nothing is restricted.
- `period_days` (back-test only): 1 to 365, default 90. "Last quarter" is `period_days: 90`; say it is the last 90 days, not a calendar quarter, and that at most the 10,000 most recent transactions are replayed.

Amounts are compared as stored on each transaction. When the person gives a threshold with no currency, say which reading you used (for example "10,000 in the transaction's own currency, every currency counted") and run the back-test: it changes nothing. When they name one, add a `currency` condition and put the same `currency` in the aggregation `filters` so the historical total counts only that currency.

Total sent by one customer in a day above 10,000:

```json didit_transaction_rule_backtest
{"scope": {"directions": ["OUTBOUND"]}, "aggregation": [{"metric": "sum", "field": "amount", "operator": "gt", "value": 10000, "window": "1d", "filters": {"subject_vendor_data": "__current__", "direction": "OUTBOUND"}}], "period_days": 90}
```

More than 5 transactions by one customer within an hour:

```json didit_transaction_rule_backtest
{"aggregation": [{"metric": "count", "operator": "gt", "value": 5, "window": "1h", "filters": {"subject_vendor_data": "__current__"}}], "period_days": 30}
```

One transaction above 5,000 in EUR:

```json didit_transaction_rule_backtest
{"conditions": [{"field": "amount", "operator": "gt", "value": 5000}, {"field": "currency", "operator": "eq", "value": "EUR"}], "evaluation_mode": "ALL", "period_days": 90}
```

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
