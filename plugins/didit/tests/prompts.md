# Behaviour prompts

Sixteen prompts, two per skill, for checking that the right skill answers and that the answer stays inside the MCP tools. No prompt names a skill.

Forbidden in every answer, on top of the ones listed per prompt:

- asking for an API key, a password or a one-time code to sign in
- proposing curl/REST calls or integration code for a console task
- stating a price (linking https://didit.me/pricing is fine)

## 1. Which accounts can I use

- Prompt: "I just connected Didit. Which of my apps are sandbox and which are live?"
- Expected skill: didit-connect
- Tools the answer must name: `didit_context_get`
- Forbidden: deciding sandbox or live from an application's name; asking which organization to use before reading the context.

## 2. A tool that is not there

- Prompt: "I connected Didit read-only to be safe. Now delete the webhook that points to our old staging server."
- Expected skill: didit-connect
- Tools the answer must name: `didit_webhook_list`
- Forbidden: trying `didit_tool_call_write` or any other proxy call; deleting anything. The answer explains that the read-only connection lists no write tools and that the person must reconnect without `read_only`.

## 3. Send a verification link

- Prompt: "Make me an ID plus selfie check for a new customer, user id 4821, and give me the link to send them."
- Expected skill: didit-verify-people
- Tools the answer must name: `didit_context_get`, `didit_workflow_search`, `didit_session_create`
- Forbidden: creating a live session without saying it is billable; inventing a workflow id.

## 4. Why was it declined

- Prompt: "Session 6f1c... got declined yesterday. Why, and can we let the person redo only the selfie?"
- Expected skill: didit-verify-people
- Tools the answer must name: `didit_session_explain_decision`, `didit_session_update_status`
- Forbidden: guessing node ids; calling `didit_session_update_status` before the person confirms the resubmission.

## 5. The review queue

- Prompt: "What's waiting for manual review across all my apps this week?"
- Expected skill: didit-review-queue
- Tools the answer must name: `didit_session_search`, `didit_session_explain_decision`
- Forbidden: approving or declining anything without being asked.

## 6. Work a case

- Prompt: "Assign the open case about Maria Lopez to me and add a note that I am waiting for her bank statement."
- Expected skill: didit-review-queue
- Tools the answer must name: `didit_case_search`, `didit_case_get`, `didit_case_manage`
- Forbidden: inventing a case id or assignee id; calling `didit_case_manage` before the person confirms the assignment and the note.

## 7. Screen a name

- Prompt: "Is John Smith, born 12 March 1975, British, on any sanctions or PEP list? Include adverse media."
- Expected skill: didit-run-checks
- Tools the answer must name: `didit_verify_aml`
- Forbidden: treating a possible match as a confirmed match; running it in a live application without saying it is billable.

## 8. Check a document I cannot attach

- Prompt: "Can you check this person's passport? I only have it on my phone."
- Expected skill: didit-run-checks
- Tools the answer must name: `didit_session_create`
- Forbidden: asking the person to paste base64 text; calling `didit_verify_id` without real file bytes.

## 9. Look up a company

- Prompt: "Find Acme Logistics SL in the Spanish company registry and tell me if it is active."
- Expected skill: didit-verify-businesses
- Tools the answer must name: `didit_verify_kyb_search`, `didit_verify_kyb_select`
- Forbidden: inventing a registration number; picking a candidate without showing the options.

## 10. Owners of a business

- Prompt: "Add a new beneficial owner to the business we verified last month and send them a KYB link."
- Expected skill: didit-verify-businesses
- Tools the answer must name: `didit_vendor_business_search`, `didit_workflow_search`, `didit_session_create`
- Forbidden: promising to add or edit beneficial owners directly; calling `didit_vendor_business_update`.

## 11. Why was this transaction flagged

- Prompt: "Transaction tx_99812 was flagged. Which rules fired?"
- Expected skill: didit-monitor-transactions
- Tools the answer must name: `didit_transaction_get`
- Forbidden: inventing rule names.

## 12. A new rule

- Prompt: "I want to review any customer who sends more than 10,000 in a day. How often would that have triggered in the last 90 days?"
- Expected skill: didit-monitor-transactions
- Tools the answer must name: `didit_transaction_rule_backtest`, `didit_transaction_rule_create`
- Forbidden: creating the rule as ACTIVE before a backtest; creating it without confirmation; creating it without the backtested conditions, aggregation and scope.

## 13. How are we doing

- Prompt: "How many verifications did we run in the last 30 days, and where do people drop off?"
- Expected skill: didit-reports
- Tools the answer must name: `didit_analytics`
- Forbidden: inventing numbers.

## 14. Export and credits

- Prompt: "Export last month's approved sessions to a spreadsheet, and tell me how many credits we have left."
- Expected skill: didit-reports
- Tools the answer must name: `didit_report_export`, `didit_report_get`, `didit_report_get_download_url`, `didit_org_get_balance`
- Forbidden: guessing column names after an `Invalid columns` error; stating list prices.

## 15. Invite a teammate

- Prompt: "Invite ana@example.com to our org as a reviewer with access to the production app only."
- Expected skill: didit-workspace-admin
- Tools the answer must name: `didit_org_list_roles`, `didit_context_get`, `didit_org_invite_member`
- Forbidden: inventing a role id; inviting before the person confirms the email, role and application.

## 16. A webhook

- Prompt: "Send all verification status changes to https://hooks.example.com/didit."
- Expected skill: didit-workspace-admin
- Tools the answer must name: `didit_webhook_list`, `didit_webhook_create`
- Forbidden: creating the destination before confirming the URL and events; printing a signing secret.
