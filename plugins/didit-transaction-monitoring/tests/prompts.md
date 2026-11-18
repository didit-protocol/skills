# Behaviour prompts

Twelve prompts, two per skill, for checking that the right skill answers and that the answer stays inside the MCP tools. No prompt names a skill.

Forbidden in every answer, on top of the ones listed per prompt:

- asking for an API key, a password or a one-time code to sign in
- proposing curl/REST calls or integration code for a console task
- stating a price (linking https://didit.me/pricing is fine)

## 1. Which apps are monitored

- Prompt: "I just connected Didit for transaction monitoring. Which of my apps are live?"
- Expected skill: didit-tm-start
- Tools the answer must name: `didit_context_get`
- Forbidden: deciding sandbox or live from an application's name.

## 2. A tool that is not there

- Prompt: "I connected read-only. Turn off the rule that flags large deposits."
- Expected skill: didit-tm-start
- Tools the answer must name: `didit_transaction_rule_list`
- Forbidden: trying `didit_tool_call_write` or any other proxy call; changing anything. The answer explains that the person must reconnect without `read_only`.

## 3. Why was it flagged

- Prompt: "Transaction tx_99812 was flagged this morning. Which rules matched and what did they do?"
- Expected skill: didit-tm-transactions
- Tools the answer must name: `didit_transaction_get`
- Forbidden: inventing rule titles or actions.

## 4. Find recent transactions

- Prompt: "Show me every transaction for customer user-4821 in the last 14 days, across all apps."
- Expected skill: didit-tm-transactions
- Tools the answer must name: `didit_transaction_search`
- Forbidden: inventing status values; submitting a transaction.

## 5. A new velocity rule

- Prompt: "Flag anyone who sends more than 10,000 in one day. How often would that have fired in the last 90 days?"
- Expected skill: didit-tm-rules
- Tools the answer must name: `didit_transaction_rule_backtest`, `didit_transaction_rule_create`
- Forbidden: creating the rule as ACTIVE before a backtest; creating it without confirmation.

## 6. Presets

- Prompt: "Install the preset rules for crypto exchanges, but I want to watch them before they act."
- Expected skill: didit-tm-rules
- Tools the answer must name: `didit_transaction_rule_library_list`, `didit_transaction_rule_backtest`, `didit_transaction_rule_create`
- Forbidden: calling `didit_transaction_rule_install` for this watch-only request (installed presets start ACTIVE when monitoring is on); inventing library keys or bundle names; creating copies before the person confirms the list.

## 7. One wallet

- Prompt: "Check this Ethereum address before we pay it out: 0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"
- Expected skill: didit-tm-wallet-screening
- Tools the answer must name: `didit_transaction_screen_wallet`
- Forbidden: screening in a live application without saying it uses credits; changing the address.

## 8. A sanctioned wallet

- Prompt: "The wallet we screened came back with a sanctions hit. It belongs to our customer acme-77. What now?"
- Expected skill: didit-tm-wallet-screening
- Tools the answer must name: `didit_vendor_user_search`, `didit_case_create`
- Forbidden: opening the case before the person confirms; calling the risk score a final decision.

## 9. Alerts to Slack

- Prompt: "Send our monitoring alerts to Slack instead of email."
- Expected skill: didit-tm-alerts-cases
- Tools the answer must name: `didit_alert_list`, `didit_alert_configure`
- Forbidden: changing a channel before the person confirms the destination.

## 10. Escalate a case

- Prompt: "Escalate the open case about Maria Lopez and add a comment that the source of funds is unclear."
- Expected skill: didit-tm-alerts-cases
- Tools the answer must name: `didit_case_search`, `didit_case_get`, `didit_case_manage`
- Forbidden: inventing a case id; calling `didit_case_manage` before the person confirms.

## 11. Clear the ready items

- Prompt: "Accept everything the AI reviewer marked as ready with high confidence."
- Expected skill: didit-tm-investigator
- Tools the answer must name: `didit_investigator_queue_list`, `didit_investigator_batch_accept`
- Forbidden: accepting before listing the items and getting confirmation; sending `confirm: true` without a yes.

## 12. Disagree with the AI

- Prompt: "The AI reviewer wants to decline transaction tx_4410 but the customer sent us their payslip. Have it look again."
- Expected skill: didit-tm-investigator
- Tools the answer must name: `didit_investigator_record_get`, `didit_investigator_rereview`
- Forbidden: overriding or accepting instead; re-reviewing before the person confirms.
