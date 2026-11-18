---
name: didit-tm-start
description: Used when someone starts transaction monitoring work in their Didit account from chat, asks which applications they can monitor, wonders whether an application is sandbox or live, cannot find a Didit tool, hits a permission error, or asks what this plugin covers. Sets the rules every transaction monitoring skill follows and sends the request to the right skill.
---

# Didit transaction monitoring: start here

The Didit MCP server acts as the signed-in person, with the permissions of their role. These rules apply to every skill in this plugin.

## Rules

1. Call `didit_context_get` first. It returns every organization and application the person can use, and whether each application is sandbox or live. With one of each, use them; with several, ask which one or use the one the person named, then pass `organization_id` and `application_id` on later calls.
2. Read sandbox or live from that result only. Never decide it from an application's name.
3. Never ask for a password, an API key or a one-time code. Sign-in is OAuth; if a tool says the person is not signed in, tell them to reconnect the "didit" server in their client.
4. If a tool is in your tool list, call it directly. If it is not listed, use the discovery tools (`didit_tool_search`, `didit_tool_describe`, `didit_tool_call_read`, `didit_tool_call_write`), but only when they are themselves in your tool list. A read-only connection lists no write tool: tell the person to reconnect without `read_only`. A missing permission: tell them to ask an organization admin. In both cases never attempt a proxy call to get around it.
5. Tools that overwrite a decision or delete records take `confirm: true`. Send it only after the person agreed to that exact action in this conversation. For every other change, describe it and wait for a clear yes.
6. Wallet screening uses the organization's Didit credits in a live application. Say so and wait for a yes. Never state a price: link https://didit.me/pricing.
7. For how a feature works, a payload shape or a webhook, call `didit_docs_search` and cite the link it returns.

## Which skill handles what

| Request | Skill |
|---|---|
| Find, read or submit transactions, read a risk outcome | didit-tm-transactions |
| Rule library, custom rules, back-tests | didit-tm-rules |
| Screen one crypto wallet address | didit-tm-wallet-screening |
| Alert channels, webhook destinations, cases | didit-tm-alerts-cases |
| The AI Investigator queue, reports, policy questions | didit-tm-investigator |

## What good output looks like

- The organization and application in use, and whether it is sandbox or live, stated once at the start.
- The tool that was called, or the exact reason a tool is not available and what the person can change.
- A clear question before any billable or irreversible action.

## Do not

- Never ask for credentials or fall back to raw HTTP calls (curl/REST) for a task these tools cover.
- Never invent an organization, application, transaction, rule or case id. Read ids from tool results.
- Never state prices. Link https://didit.me/pricing.
