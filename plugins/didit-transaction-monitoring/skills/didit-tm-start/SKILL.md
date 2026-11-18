---
name: didit-tm-start
description: Starts transaction monitoring work in their Didit account, picks the application and sets the rules every monitoring action follows. Use when the user begins monitoring work with Didit, asks "which apps are monitored", "is this sandbox or live", "what can you do for transaction monitoring", cannot find a Didit tool, or hits a permission or read-only error.
---

# Didit transaction monitoring: start here

The Didit MCP server acts as the signed-in person, with the permissions of their role. These rules apply to every skill in this plugin.

## Rules

1. Call `didit_context_get` first. It returns the organizations and applications the person can use with their ids, each application's `mode` (`sandbox` or `live`) when the server knows it, and `default_organization_id` and `default_application_id`. A default is present only when there is exactly one; an organization whose applications could not be listed leaves `default_application_id` out. Without it, establish the target before any change or billable action: use the application the person named, or ask which one.
2. Read sandbox or live from `mode` only. Never decide it from an application's name. If `mode` is missing, say the environment is unknown and treat the application as live (billable) until the person confirms otherwise.
3. Scope ids follow each tool's schema. Always send the ids a tool requires. Send an optional `organization_id` or `application_id` only when the context shows several organizations or applications, or when it returned no default for that id: then ask the person which organization or application to use and pass the one they name. Never send an id the tool does not declare. Through a discovery proxy (`didit_tool_call_read` or `didit_tool_call_write`), put the target's arguments, ids included, inside `arguments`, never next to `name`. Most tools here take both ids as optional; `didit_docs_search` takes neither.
4. Never ask for a password, an API key or a one-time code. Sign-in is OAuth; if a tool says the person is not signed in, tell them to reconnect the "didit" server in their client.
5. If a tool is in your tool list, call it directly. If it is not listed, use the discovery tools (`didit_tool_search`, `didit_tool_describe`, `didit_tool_call_read`, `didit_tool_call_write`), but only when they are themselves in your tool list. A read-only connection lists no write tool: tell the person to reconnect without `read_only`. The list is the same for every role; a call your role does not allow is refused, with the missing permission in the error. Name that permission and tell them to ask an organization admin. In both cases never attempt a proxy call to get around it.
6. Every change needs the person's agreement first: describe what will change and wait for a clear yes before calling the tool, and say plainly when it cannot be undone. An instruction given in advance or with a condition ('if it is only X, approve') is not agreement. Report what you found, say exactly what you would change and in which application (sandbox or live), then wait for a yes. Send `confirm: true` only to a tool whose schema declares `confirm`, and only after the person agreed to that exact action. In this plugin's recipes those tools are: `didit_case_manage` (filing a SAR), `didit_investigator_accept`, `didit_investigator_override`, `didit_investigator_batch_accept`, `didit_investigator_rereview`, `didit_investigator_question_answer` and `didit_investigator_question_dismiss`. Any other tool you reach by name or through discovery follows its own schema: if it declares `confirm`, the same rule applies. Rule and webhook deletions take none.
7. Sandbox applications are free to test in. In a live application this can use your Didit credits when you submit a transaction (past the plan's monthly allowance, or a Travel Rule charge in its place) or screen a wallet. In a live application, or one whose mode is unknown, say so before the call and wait for a yes. Never state a price: link https://didit.me/pricing.
8. For how a feature works, a payload shape or a webhook, call `didit_docs_search` and cite the link it returns.
9. Never display a Slack webhook URL, a webhook destination URL or an alert email in full. Show the host or domain and mask the rest.
10. If `didit_context_get` shows `connection.type: api_key`, this connection is one application with no person: member, role, API key, billing-detail (plan, payment methods, receipts), compliance and audit-log tools are not available; the credit balance (`didit_org_get_balance`) still is. Say so and point the person to sign in with OAuth for the missing ones.
11. If `didit_context_get` shows an organization with zero applications, do not conclude there are none. Today only the Owner and Admin roles can list applications; for other roles (Reader, Developer, Compliance Officer) the context comes back with none even when the person can work in several. Read the person's own row in `didit_org_list_members`: `accessible_applications` gives the application ids and names. The `mode` is not in that row, so treat each application as live (billable) until the person says which one is the sandbox, and send the ids each tool's schema declares. A call the person's role does not allow is refused with `forbidden` (sometimes `missing_scope`): say the role does not allow it and that an organization admin can change the role. After a role change the person must reconnect Didit, because a connection keeps the permissions it was approved with.

## Which skill handles what

| Request | Skill |
|---|---|
| Find, read or submit transactions, read a risk outcome | didit-tm-transactions |
| Rule library, custom rules, back-tests | didit-tm-rules |
| Screen one crypto wallet address | didit-tm-wallet-screening |
| Alert channels, webhook destinations, cases | didit-tm-alerts-cases |
| The AI Investigator queue, reports, policy questions | didit-tm-investigator |
| Travel Rule: settings, VASPs, counterparty contacts, wallet address book, messages, networks, sandbox tests | didit-tm-travel-rule |

## What good output looks like

- The organization and application in use, and whether it is sandbox, live or unknown, stated once at the start.
- The tool that was called, or the exact reason a tool is not available and what the person can change.
- A clear question before any billable or irreversible action.

## Do not

- Never ask for credentials or fall back to raw HTTP calls (curl/REST) for a task these tools cover.
- Never invent an organization, application, transaction, rule or case id. Read ids from tool results.
- Never state prices. Link https://didit.me/pricing.
