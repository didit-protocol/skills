---
name: didit-connect
description: Used when someone starts working with their Didit account from chat, asks which organizations or applications they can use, wonders whether an application is sandbox or live, cannot find a Didit tool, hits a permission error, or asks how Didit works. Sets the rules every other Didit skill follows (sign-in, picking the application, confirmations, billable actions, tools that are not loaded) and sends the request to the right skill.
---

# Didit: connect and route

The Didit MCP server acts as the signed-in person, with the permissions of their role. These rules apply to every Didit skill in this plugin.

## Sign-in

- Sign-in is OAuth ("Log in with Didit"). The host opens it the first time a Didit tool is used, or through `/mcp` in Claude Code.
- Never ask the person for a password, an API key or a one-time code to sign in. If a tool answers that the person is not signed in, tell them to reconnect the "didit" server from their client's connector or MCP settings.
- A person without an account can create one for free at https://business.didit.me.

## Always start with the context

1. Call `didit_context_get` first. It returns the organizations and applications the person can use with their ids, each application's `mode` (`sandbox` or `live`) when the server knows it, and `default_organization_id` and `default_application_id` when there is exactly one of each.
2. When the defaults are present, use them and pass no ids. When `default_application_id` is missing (several applications, or an organization whose applications could not be listed), ask which application to use, or use the one the person named.
3. Pass `organization_id` and `application_id` only to tools whose arguments declare them. Some tools take only `organization_id` (for example `didit_org_get_balance`), some take neither (for example `didit_docs_search`, `didit_session_get_decision`). For a call through `didit_tool_call_read` or `didit_tool_call_write`, put the ids inside `arguments`, never next to `name`.
4. Read sandbox or live from `mode` only. Never decide it from an application's name. If `mode` is missing, say the environment is unknown and treat the application as live (billable) until the person confirms otherwise.

## Calling tools

- If a tool is in your tool list, call it directly.
- If it is not listed, use the discovery tools, but only when they are themselves in your tool list: `didit_tool_search` to find it, `didit_tool_describe` to read its arguments, then `didit_tool_call_read` for a read or `didit_tool_call_write` for a change.
- The discovery tools are listed only when the connection does not load every toolset (for example `?toolsets=core`). A full connection lists every tool directly.
- A tool can also be missing for two other reasons. Say which one, and tell the person what to change:
  - The connection is read-only. On a read-only connection that loads every toolset, no write tool and no discovery tool is listed. Tell the person to reconnect without `read_only` to make changes.
  - Their role lacks the permission. Tell them to ask an organization admin for a role that allows it.
- In both cases never attempt a proxy call through another tool to get around it.

## Confirmations

- Every change (status updates, deletions, invitations, webhooks, exports) needs the person's agreement first: describe what will change and wait for a clear yes before calling the tool. Irreversible ones (overwriting a decision, deleting a webhook or a member) get the same question, said plainly as irreversible.
- A few tools also declare a `confirm` argument, for example `didit_case_manage` (filing a SAR), `didit_session_delete` and `didit_org_create_api_key`. Send `confirm: true` only to a tool whose arguments declare it, and only after the person has agreed to that exact action in this conversation. Never add `confirm` to a tool that does not declare it.

## Billable actions

- Checks in a sandbox application are free.
- In a live application, sessions and standalone checks use the organization's Didit credits. Say so before running anything billable in a live application, and wait for the person to agree.
- Never state a price. For pricing, link https://didit.me/pricing. To see what is left, use `didit_org_get_balance` (see didit-reports).

## How-to questions

For any question about how Didit works, a feature, a webhook payload or an SDK, call `didit_docs_search` and cite the link it returns. Do not answer from memory.

## Lighter connections (optional)

The server URL accepts two query parameters. The person adds them when they connect:

- `https://mcp.didit.me/mcp?toolsets=core` loads a short list of about 30 tools. The rest stays reachable through the discovery tools.
- `read_only=true` lists only tools that read data, for example `https://mcp.didit.me/mcp?toolsets=core&read_only=true`. Nothing can be changed on such a connection.

## Integration code is a different job

If the person wants backend code that calls the Didit REST API with an API key, these tools are the wrong fit. Point them to the developer skills (the `didit-api` plugin, or the `skills/` folder of github.com/didit-protocol/skills) and to https://docs.didit.me.

## Which skill handles what

| Request | Skill |
|---|---|
| Create a verification workflow or link, read a decision, test in sandbox | didit-verify-people |
| Sessions in review, approve or decline, add notes, work cases | didit-review-queue |
| One-off checks: AML, document, address, database, face, phone code (email through a session) | didit-run-checks |
| Verify a company (KYB), look up existing business records | didit-verify-businesses |
| Transactions, monitoring rules, backtests, wallet screening | didit-monitor-transactions |
| Analytics, balance, plan, exports | didit-reports |
| Members, roles, webhooks, lists, branding, questionnaires | didit-workspace-admin |

## What good output looks like

- The organization and application in use, and whether it is sandbox, live or unknown, stated once at the start.
- The tool that was called, or the exact reason a tool is not available and what the person can change.
- A clear question before any billable or irreversible action.

## Do not

- Never ask for a password, an API key or a one-time code.
- Never fall back to raw HTTP calls (curl/REST) for a task these tools cover.
- Never invent an organization, application, session or workflow id. Read ids from tool results.
- Never state prices. Link https://didit.me/pricing.
