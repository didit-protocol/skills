---
name: didit-users-start
description: Starts managing verified users, businesses, lists and the team in their Didit account, picks the application and sets the shared rules. Use when the user begins user management with Didit, asks "which apps do I have", "is this sandbox or live", "what can you manage", cannot find a Didit tool, or hits a permission or read-only error.
---

# Didit user management: start here

The Didit MCP server acts as the signed-in person, with the permissions of their role. This plugin covers two separate areas: the people and companies you verify (vendor users, vendor businesses, lists and blocklist), and your own Didit workspace (members, roles, API keys, applications).

## Rules

1. Call `didit_context_get` first. It returns the organizations and applications the person can use with their ids, each application's `mode` (`sandbox` or `live`) when the server knows it, and `default_organization_id` and `default_application_id`. A default is present only when there is exactly one; an organization whose applications could not be listed leaves `default_application_id` out. Without it, establish the target before any change: use the application the person named, or ask which one.
2. Read sandbox or live from `mode` only. Never decide it from an application's name. If `mode` is missing, say the environment is unknown and treat the application as live (billable) until the person confirms otherwise.
3. Scope ids follow each tool's schema. Always send the ids a tool requires. Send an optional `organization_id` or `application_id` only when the context shows several organizations or applications, or when it returned no default for that id: then ask the person which organization or application to use and pass the one they name. Never send an id the tool does not declare. Through a discovery proxy (`didit_tool_call_read` or `didit_tool_call_write`), put the target's arguments, ids included, inside `arguments`, never next to `name`. For example `didit_org_create_api_key` requires `organization_id` and `application_id`; `didit_docs_search` takes neither; the member tools take only `organization_id`.
4. Never ask for a password, an API key or a one-time code. Sign-in is OAuth; if a tool says the person is not signed in, tell them to reconnect the "didit" server in their client.
5. If a tool is in your tool list, call it directly. If it is not listed, use the discovery tools (`didit_tool_search`, `didit_tool_describe`, `didit_tool_call_read`, `didit_tool_call_write`), but only when they are themselves in your tool list. A read-only connection lists no write tool: tell the person to reconnect without `read_only`. The list is the same for every role; a call your role does not allow is refused, with the missing permission in the error. Name that permission and tell them to ask an organization admin. In both cases never attempt a proxy call to get around it.
6. Every change needs the person's agreement first: describe what will change and wait for a clear yes before calling the tool, and say plainly when it cannot be undone. An instruction given in advance or with a condition ('if it is only X, approve') is not agreement. Report what you found, say exactly what you would change and in which application (sandbox or live), then wait for a yes. Send `confirm: true` only to a tool whose schema declares `confirm`, and only after the person agreed to that exact action. In this plugin's recipes those tools are: `didit_vendor_user_delete`, `didit_vendor_business_delete` and `didit_org_create_api_key`. Any other tool you reach by name or through discovery follows its own schema: if it declares `confirm`, the same rule applies. List, entry and member removals take none.
7. For how a feature works, call `didit_docs_search` and cite the link it returns.
8. This plugin's tools create no verification session and run no standalone check. Never state a price: link https://didit.me/pricing. To see the credit balance, use `didit_org_get_balance`.
9. A newly issued API key is returned once. Where you can write files in the person's project, write it straight to the project's secret store or `.env` and do not print it; otherwise show it once. Never repeat it later and never keep it in notes or memory.
10. If `didit_context_get` shows `connection.type: api_key`, this connection is one application with no person: member, role, API key, billing-detail (`didit_billing_*`), compliance and audit-log tools are not available; the credit balance (`didit_org_get_balance`) still is. Say so and point the person to sign in with OAuth for the missing ones.

## Which skill handles what

| Request | Skill |
|---|---|
| Find, create, update, flag, block or delete a verified person | didit-users-records |
| Find, create, flag, block or delete a verified company | didit-users-businesses |
| Custom lists, list entries, face entries, blocklist, allowlist | didit-users-lists |
| Members, roles, invitations, API keys, applications | didit-users-team |

## What good output looks like

- The organization and application in use, and whether it is sandbox, live or unknown, stated once at the start.
- The tool that was called, or the exact reason a tool is not available and what the person can change.
- A clear question before any deletion, removal or credential.

## Do not

- Never ask for credentials or fall back to raw HTTP calls (curl/REST) for a task these tools cover.
- Never invent an organization, application, user, business, list or member id. Read ids from tool results.
- Never state prices. Link https://didit.me/pricing.
