---
name: didit-tm-rules
description: Used when someone wants to see, install or remove preset transaction monitoring rules from the Didit rule library, create, change, pause or delete a custom rule, or test how often a rule would have fired on past transactions before turning it on. Always back-tests first and confirms before enabling or removing anything.
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

- Pass the exact `conditions`, `aggregation`, `evaluation_mode` and `scope` you intend to save, and `period_days` (1 to 365, default 90).
- To test a saved rule, read it with `didit_transaction_rule_get` first and pass its definition.
- Each aggregation entry needs `metric`, `operator`, `value` and `window` (`<N>m` minutes, `<N>h` hours or `<N>d` days). All aggregation entries must match together.
- Report the hit count and rate in plain words before proposing to save anything.

For field names in conditions, call `didit_docs_search`. Do not guess field paths.

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

- PRESET rules only allow mode changes. To change a preset's conditions, create a CUSTOM copy with `metadata.based_on` (its library key) and `metadata.based_on_rule_uuid`, then set the preset to `DISABLED` so a transaction does not alert twice.
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
