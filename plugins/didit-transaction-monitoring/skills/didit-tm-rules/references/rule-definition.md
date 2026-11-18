# Rule definition: more examples

Every example is the full argument object of the tool named on its code fence. Replace each `<...>` placeholder with the value read from a tool result; never invent one. Use a UUID only for a UUID field; text placeholders such as `<preset title>`, `<preset category>` and `<library_key>` take the preset's returned `title`, `category` and `library_key`. The field rules are in section 2 of SKILL.md.

## Grouped conditions

Setting `group_index` on any condition turns on grouped evaluation for the whole list, and `evaluation_mode` is then ignored. `group_logic` combines the conditions inside a group (default `AND`). `groups_logic` combines the groups (default `OR`) and is read from the first condition only.

Outbound transfers to two countries above 2,000, or any transaction with a risk score of 80 or more. The direction is a condition of group 0, not a `scope`: a scope would apply to both groups and drop high-scoring inbound transactions. Country codes are normalized before comparison.

```json didit_transaction_rule_backtest
{"conditions": [{"field": "direction", "operator": "eq", "value": "OUTBOUND", "group_index": 0, "group_logic": "AND", "groups_logic": "OR"}, {"field": "counterparty_country", "operator": "in", "value": ["IRN", "PRK"], "group_index": 0}, {"field": "amount", "operator": "gt", "value": 2000, "group_index": 0}, {"field": "score", "operator": "gte", "value": 80, "group_index": 1}], "period_days": 90}
```

## A list as the comparison set

With `value_type: "list"`, `value` is the UUID of a List (from `didit_lists_list`) and its entries become the set `in` or `not_in` compares against.

```json didit_transaction_rule_backtest
{"conditions": [{"field": "subject_vendor_data", "operator": "in", "value": "<list_uuid>", "value_type": "list"}], "period_days": 30}
```

## Several distinct counterparties in a day

`distinct_count` (alias `unique_count`) counts different values of `field`. More than 3 different counterparty countries for one customer in 24 hours:

```json didit_transaction_rule_backtest
{"aggregation": [{"metric": "distinct_count", "field": "counterparty_country", "operator": "gt", "value": 3, "window": "24h", "filters": {"subject_vendor_data": "__current__"}}], "period_days": 90}
```

## Saving the back-tested rule

Send the same definition that was back-tested, plus `title`, `category`, `mode` and `actions`. Start in `TEST`. Each action type has its own shape: `add_score` takes an integer `value`; `change_status` takes `value` (`IN_REVIEW`, `DECLINED`, `AWAITING_USER` with a `workflow_id`, or `APPROVED`); `add_tags` takes `tag_uuid` or `tag_name`; `add_note` takes `note`; `add_to_list` takes `list_id`; `open_case` takes optional `blueprint`, `grouping` (`by_applicant` or `by_rule_and_applicant`) and `attach_matched_transaction`. Only the first `open_case` action runs.

Confirm the title, definition, actions and mode with the person, and wait for a clear yes before this call:

```json didit_transaction_rule_create
{"title": "Daily outbound total above 10,000", "category": "finance", "mode": "TEST", "scope": {"directions": ["OUTBOUND"]}, "aggregation": [{"metric": "sum", "field": "amount", "operator": "gt", "value": 10000, "window": "1d", "filters": {"subject_vendor_data": "__current__", "direction": "OUTBOUND"}}], "actions": [{"type": "change_status", "value": "IN_REVIEW"}, {"type": "add_score", "value": 20}, {"type": "open_case", "grouping": "by_applicant", "attach_matched_transaction": true}]}
```

To change a PRESET rule, read it with `didit_transaction_rule_get` and build a CUSTOM copy of its whole definition: keep its `conditions`, `aggregation`, `evaluation_mode`, `scope` and `actions`, change only what the person asked for, and point at the original in `metadata`. Create the copy in `TEST` and leave the preset as it is, so it keeps enforcing while the copy records hits. In this example the preset's only change is a higher amount threshold; its actions are copied unchanged:

```json didit_transaction_rule_create
{"title": "<preset title> (custom)", "category": "<preset category>", "mode": "TEST", "conditions": [{"field": "amount", "operator": "gt", "value": 15000}], "actions": [{"type": "change_status", "value": "IN_REVIEW"}], "metadata": {"based_on": "<library_key>", "based_on_rule_uuid": "<rule_uuid>"}}
```

Back-test the copy's exact definition before it goes `ACTIVE`. The switch is two separate `didit_transaction_rule_update` calls, one per rule: set the copy to `ACTIVE` first, then the preset to `DISABLED`, so one of them is always enforcing. Before asking for agreement, say that between the two calls both rules are `ACTIVE`, so a transaction can match both and their actions can run twice, and that this overlap stays if the second call fails. After the person agrees, set the copy to `ACTIVE`, then read the copy with `didit_transaction_rule_get`. Disable the preset only if that read shows the copy is `ACTIVE`. If the copy is not `ACTIVE` (the first call failed or it is still `TEST`), stop: leave the preset enforcing and report that nothing was switched. After disabling, read both rules and report each mode. If the copy is `ACTIVE` and the preset is still `ACTIVE`, report the switch as incomplete and offer to retry disabling the preset. Never disable or retry disabling the preset while the copy is not confirmed `ACTIVE`, or no rule would be enforcing.

Source: the rule schemas of the Didit MCP server (`conditions`, `aggregation`, `scope`, `actions`, `evaluation_mode`, `period_days`).
