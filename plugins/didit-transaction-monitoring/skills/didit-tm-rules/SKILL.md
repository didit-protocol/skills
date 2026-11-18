---
name: didit-tm-rules
description: Builds and tunes transaction monitoring rules in their Didit account, always back-testing first. Use when the user says "monitoring rule", "create a rule", "velocity rule", "back-test", "how often would this have fired", "install the preset rules", "rule library", "pause this rule", "turn the rule on", or "delete a rule" in Didit.
---

# Transaction monitoring rules

Follow the rules of didit-tm-start first: call `didit_context_get` and pick the application. Rules belong to one application.

## Modes

Every rule has a `mode`:

- `ACTIVE` evaluates transactions and runs its actions.
- `TEST` evaluates and records hits but skips every action.
- `DISABLED` is skipped.

`evaluation_mode` (`ALL` or `ANY`) is a different thing: it says how flat conditions combine.

## 1. Read what exists

- `didit_transaction_rule_list` lists the application's rules. Filters: `source` (`PRESET` or `CUSTOM`), `category`, `mode`, `bundle`, `search`, `ordering` (for example `-run_count` or `-latest_triggered_at`), `limit`, `offset`.
- `didit_transaction_rule_get` with `rule_uuid` returns one rule with its saved conditions, aggregation, scope, actions and counters.
- `didit_transaction_rule_library_list` lists Didit's preset library: each entry has its full config, bundle, tags, industries and `is_installed`. Filters: `bundle`, `category`, `search`.

## 2. Back-test before anything changes

`didit_transaction_rule_backtest` dry-runs a rule definition against up to the 10,000 most recent transactions of the application. It writes nothing and takes no `rule_uuid`.

- A back-test is a read, so it needs no agreement: when the person asks how often a rule would fire, build the definition below and run it at once. Use the application they named; if they named none and the context shows several, ask which one, once. Never ask them for field names.
- Pass the exact `conditions`, `aggregation`, `evaluation_mode` and `scope` you intend to save, and `period_days`.
- To test a saved rule, read it with `didit_transaction_rule_get` first and pass its definition.
- Report the hit count and rate in plain words before proposing to save anything.

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

Amounts are compared as stored on each transaction, with no currency conversion. When the person gives a threshold with no currency, say which reading you used and run the back-test: it changes nothing. The total example below adds raw amounts across every currency, so describe its result as a raw sum of mixed currencies. To total only in the evaluated transaction's own currency, add `"currency": "__current__"` to the aggregation `filters`. When they name one, add a `currency` condition and put the same `currency` in the aggregation `filters` so the historical total counts only that currency.

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

The fields above are the ones the schema names. For any other field path, call `didit_docs_search`; do not guess. Grouped conditions, list membership and a full create call are in `references/rule-definition.md`.

## 3. Create a custom rule

`didit_transaction_rule_create` saves a CUSTOM rule. Required: `title` (unique in the application), `category`, `mode` and `actions`.

- Put every outcome the person asked for in `actions`: `add_score`, `change_status` (`IN_REVIEW`, `DECLINED`, `AWAITING_USER` with a `workflow_id`, or `APPROVED`), `add_tags`, `add_note`, `add_to_list`, `open_case`. Pass an empty list only for a monitor-only rule the person asked for.
- Include the conditions and aggregation in this call. A back-test never saves them.

Recommended order:

1. Back-test the exact definition and report the hit rate.
2. Create the rule with `mode: "TEST"`.
3. Switch it to `ACTIVE` only after the person reviews the test hits.

Confirm the title, conditions, actions and mode with the person before creating the rule.

## 4. Change, pause or enable a rule

`didit_transaction_rule_update` with `rule_uuid` changes only the fields you send.

- PRESET rules only allow mode changes. To change a preset's conditions, read the preset with `didit_transaction_rule_get` and create a CUSTOM copy of its whole definition (conditions, aggregation, evaluation mode, scope and actions, changing only what the person asked) in `TEST`, with `metadata.based_on` (its library key) and `metadata.based_on_rule_uuid`. Leave the preset enforcing. Only after the person reviews the copy's test hits and agrees to the switch, set the copy to `ACTIVE` and then the preset to `DISABLED`, so nothing goes unenforced. These are two separate updates: before asking for agreement, say that while both are `ACTIVE` a transaction can match both and their actions can run twice, and that the overlap stays if the second update fails. Afterwards read both rules and report their modes; if the preset is still `ACTIVE`, report the switch as incomplete. See `references/rule-definition.md`.
- Before raising a rule's impact (new conditions, or `TEST` to `ACTIVE`), back-test the exact candidate definition.
- Ask the person to confirm the exact change, mode included, before calling it.

## 5. Install or remove presets

- `didit_transaction_rule_install` installs presets by `library_keys`, `bundle`, or both (at least one). It takes no `mode`: installed rules start `ACTIVE` when transaction monitoring is on for the application, otherwise `DISABLED`. With monitoring on, an installed preset acts at once.
- To watch presets before they act: read the entries with `didit_transaction_rule_library_list`, back-test each entry's config with `didit_transaction_rule_backtest` and report the hit rates. Then stop before installing, or offer CUSTOM copies created with `mode: "TEST"` and `metadata.based_on` (see section 3). Never install for a watch-only request while monitoring is on.
- Install only after the person confirms the list of rules and accepts the mode they will start in.
- `didit_transaction_rule_uninstall` removes installed presets by `library_keys` or `bundle`. To pause without removing, set `mode` to `DISABLED` instead. Name the rules that will go and wait for the person to confirm.

## 6. Delete a custom rule

`didit_transaction_rule_delete` with `rule_uuid` deletes a CUSTOM rule. PRESET rules are removed with `didit_transaction_rule_uninstall`. Show the rule's title and mode and wait for the person to confirm. Offer `DISABLED` as the reversible alternative.

## What good output looks like

- The back-test hit count and rate before anything is saved.
- The rule's title, mode, conditions and actions stated before each create, update, install, uninstall or delete.
- New and changed rules kept in `TEST` until the person says otherwise.

## Do not

- Never ask for credentials (password, API key, one-time code).
- Never fall back to raw HTTP calls (curl/REST) for a console task.
- Never create or enable a rule as `ACTIVE` before a back-test.
- Never invent rule ids, library keys, bundles or condition fields.
- Never state prices. Link https://didit.me/pricing.
