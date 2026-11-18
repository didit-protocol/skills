---
name: didit-tm-start
description: Used when someone starts transaction monitoring work in their Didit account from chat, asks which applications they can monitor, wonders whether an application is sandbox or live, cannot find a Didit tool, hits a permission error, or asks what this plugin covers. Sets the rules every transaction monitoring skill follows and sends the request to the right skill.
---

# Didit transaction monitoring: start here

The Didit MCP server acts as the signed-in person, with the permissions of their role. These rules apply to every skill in this plugin.

## Rules

1. Call `didit_context_get` first. It returns the organizations and applications the person can use with their ids, each application's `mode` (`sandbox` or `live`) when the server knows it, and `default_organization_id` and `default_application_id`. A default is present only when there is exactly one; an organization whose applications could not be listed leaves `default_application_id` out. Without it, establish the target before any change or billable action: use the application the person named, or ask which one.
2. Read sandbox or live from `mode` only. Never decide it from an application's name. If `mode` is missing, say the environment is unknown and treat the application as live (billable) until the person confirms otherwise.
3. Scope ids follow each tool's schema. Always send the ids a tool requires. Send an optional `organization_id` or `application_id` only when the context shows several organizations or applications, or when it returned no default for that id: then ask the person which organization or application to use and pass the one they name. Never send an id the tool does not declare. Through a discovery proxy (`didit_tool_call_read` or `didit_tool_call_write`), put the target's arguments, ids included, inside `arguments`, never next to `name`. Most tools here take both ids as optional; `didit_docs_search` takes neither.
4. Never ask for a password, an API key or a one-time code. Sign-in is OAuth; if a tool says the person is not signed in, tell them to reconnect the "didit" server in their client.
5. If a tool is in your tool list, call it directly. If it is not listed, use the discovery tools (`didit_tool_search`, `didit_tool_describe`, `didit_tool_call_read`, `didit_tool_call_write`), but only when they are themselves in your tool list. A read-only connection lists no write tool: tell the person to reconnect without `read_only`. A missing permission: tell them to ask an organization admin. In both cases never attempt a proxy call to get around it.
6. Every change needs the person's agreement first: describe what will change and wait for a clear yes before calling the tool, and say plainly when it cannot be undone. Only some tools declare a `confirm` argument; in this plugin: `didit_case_manage` (filing a SAR), `didit_investigator_accept`, `didit_investigator_override`, `didit_investigator_batch_accept`, `didit_investigator_rereview`, `didit_investigator_question_answer` and `didit_investigator_question_dismiss`. Send `confirm: true` only to those, and only after the person agreed to that exact action in this conversation. Never add `confirm` to any other tool: rule and webhook deletions take none.
7. Sandbox applications are free to test in. In a live application this can use your Didit credits when you submit a transaction (past the plan's monthly allowance, or a Travel Rule charge in its place) or screen a wallet. In a live application, or one whose mode is unknown, say so before the call and wait for a yes. Never state a price: link https://didit.me/pricing.
8. For how a feature works, a payload shape or a webhook, call `didit_docs_search` and cite the link it returns.
9. Never display a Slack webhook URL, a webhook destination URL or an alert email in full. Show the host or domain and mask the rest.

## Which skill handles what

| Request | Skill |
|---|---|
| Find, read or submit transactions, read a risk outcome | didit-tm-transactions |
| Rule library, custom rules, back-tests | didit-tm-rules |
| Screen one crypto wallet address | didit-tm-wallet-screening |
| Alert channels, webhook destinations, cases | didit-tm-alerts-cases |
| The AI Investigator queue, reports, policy questions | didit-tm-investigator |

## What good output looks like

- The organization and application in use, and whether it is sandbox, live or unknown, stated once at the start.
- The tool that was called, or the exact reason a tool is not available and what the person can change.
- A clear question before any billable or irreversible action.

## Do not

- Never ask for credentials or fall back to raw HTTP calls (curl/REST) for a task these tools cover.
- Never invent an organization, application, transaction, rule or case id. Read ids from tool results.
- Never state prices. Link https://didit.me/pricing.
