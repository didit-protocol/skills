---
name: didit-users-start
description: Used when someone starts managing the people and companies they verify, their lists or their Didit workspace team from chat, asks which applications they can use, wonders whether an application is sandbox or live, cannot find a Didit tool, hits a permission error, or asks what this plugin covers. Sets the rules every user management skill follows and routes the request.
---

# Didit user management: start here

The Didit MCP server acts as the signed-in person, with the permissions of their role. This plugin covers two separate areas: the people and companies you verify (vendor users, vendor businesses, lists and blocklist), and your own Didit workspace (members, roles, API keys, applications).

## Rules

1. Call `didit_context_get` first. It returns every organization and application the person can use, and whether each application is sandbox or live. With one of each, use them; with several, ask which one or use the one the person named, then pass `organization_id` and `application_id` on later calls.
2. Read sandbox or live from that result only. Never decide it from an application's name.
3. Never ask for a password, an API key or a one-time code. Sign-in is OAuth; if a tool says the person is not signed in, tell them to reconnect the "didit" server in their client.
4. If a tool is in your tool list, call it directly. If it is not listed, use the discovery tools (`didit_tool_search`, `didit_tool_describe`, `didit_tool_call_read`, `didit_tool_call_write`), but only when they are themselves in your tool list. A read-only connection lists no write tool: tell the person to reconnect without `read_only`. A missing permission: tell them to ask an organization admin. In both cases never attempt a proxy call to get around it.
5. Tools that delete records or issue credentials take `confirm: true`. Send it only after the person agreed to that exact action in this conversation. For every other change (status, removal, invitation), describe it and wait for a clear yes.
6. Creating a verification session or a standalone check uses Didit credits in a live application; this plugin's tools do not do that. Never state a price: link https://didit.me/pricing. To see what is left, use `didit_org_get_balance`.
7. For how a feature works, call `didit_docs_search` and cite the link it returns.

## Which skill handles what

| Request | Skill |
|---|---|
| Find, create, update, flag, block or delete a verified person | didit-users-records |
| Find, create, flag, block or delete a verified company | didit-users-businesses |
| Custom lists, list entries, face entries, blocklist, allowlist | didit-users-lists |
| Members, roles, invitations, API keys, applications | didit-users-team |

## What good output looks like

- The organization and application in use, and whether it is sandbox or live, stated once at the start.
- The tool that was called, or the exact reason a tool is not available and what the person can change.
- A clear question before any deletion, removal or credential.

## Do not

- Never ask for credentials or fall back to raw HTTP calls (curl/REST) for a task these tools cover.
- Never invent an organization, application, user, business, list or member id. Read ids from tool results.
- Never state prices. Link https://didit.me/pricing.
