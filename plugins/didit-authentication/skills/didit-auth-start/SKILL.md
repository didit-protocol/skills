---
name: didit-auth-start
description: Explains Didit Authentication (end-user sign-in for their own app) and routes the request. Use when the user asks "what is Didit sign-in", "is Authentication on for my app", "how does sign-in relate to KYC or transaction monitoring", or "what can this plugin do" with Didit. Sets the rules every Didit Authentication skill follows.
---

# Didit Authentication: start here

Didit Authentication signs a developer's own customers into the developer's application: hosted sign-in pages, passkeys, email and phone codes, social sign-in and organization SSO. It is separate from signing into the Didit console and from verifying someone's identity. Signing in does not approve a verification or authorize a payment.

## What this plugin can and cannot do

- No MCP tool configures Authentication. Methods, redirect URLs, allowed origins, session and password settings are set in the Didit console.
- This plugin is guidance plus documentation search: it helps plan and write the integration code.
- Docs mark Authentication as new. Treat details as subject to change and check them before writing code.

## Rules

1. Call `didit_context_get` first. It returns the organizations and applications the person can use with their ids, each application's `mode` (`sandbox` or `live`) when the server knows it, and `default_organization_id` and `default_application_id`. A default is present only when there is exactly one; an organization whose applications could not be listed leaves `default_application_id` out. Without it, establish the target before any change: use the application the person named, or ask which one.
2. Read sandbox or live from `mode` only. Never decide it from an application's name. If `mode` is missing, say the environment is unknown and treat the application as live (billable) until the person confirms otherwise.
3. Scope ids follow each tool's schema. Always send the ids a tool requires. Send an optional `organization_id` or `application_id` only when the context shows several organizations or applications, or when it returned no default for that id: then ask the person which organization or application to use and pass the one they name. Never send an id the tool does not declare. Through a discovery proxy (`didit_tool_call_read` or `didit_tool_call_write`), put the target's arguments, ids included, inside `arguments`, never next to `name`. `didit_docs_search` requires `query` and takes no `organization_id` or `application_id`.
4. Never ask for a password, an API key or a one-time code. Sign-in is OAuth; if a tool says the person is not signed in, tell them to reconnect the "didit" server in their client.
5. If a tool is in your tool list, call it directly. If it is not listed, use the discovery tools (`didit_tool_search`, `didit_tool_describe`, `didit_tool_call_read`, `didit_tool_call_write`), but only when they are themselves in your tool list. A read-only connection lists no write tool: tell the person to reconnect without `read_only`. A missing permission: tell them to ask an organization admin. In both cases never attempt a proxy call to get around it.
6. Every change needs the person's agreement first: describe what will change and wait for a clear yes before calling the tool, and say plainly when it cannot be undone. An instruction given in advance or with a condition ('if it is only X, approve') is not agreement. Report what you found, say exactly what you would change and in which application (sandbox or live), then wait for a yes. None of the tools these skills use declares a `confirm` argument; never add one. If a step needs a tool that declares it, send `confirm: true` only after the person agreed to that exact action in this conversation.
7. Before writing any code or naming any endpoint, parameter or claim, call `didit_docs_search` for the current page and cite the link. Never invent an endpoint, parameter or claim name.
8. Never put a verification API key, console token or end-user token in code, URLs or logs.
9. `didit_context_get` has no field that says whether Authentication is on. For a live application, tell the person to check the Products page of the Didit console; never assume it is on.
10. Authentication is billed per monthly active user. Never state a price: link https://didit.me/pricing.

## Sandbox first

A sandbox application has Authentication on from the start. A live application turns it on from the Products page of the console; until then its runtime routes answer `404`. Live and sandbox applications have separate sign-in origins, settings and identities.

## One person across products

Every identity carries `vendor_data`. Use the same value as `vendor_data` for verification sessions and transactions, so sign-in events land on the same person as their verifications and transactions. Derive it on the backend from a verified token, never from an unchecked browser field.

## Which skill handles what

| Request | Skill |
|---|---|
| Which sign-in methods, MFA, password reset, invitations | didit-auth-sign-in-methods |
| Hosted flow, PKCE, code exchange, token checks, refresh, sign-out | didit-auth-integrate |
| Sign-in timeline, auth webhooks, event rules, fraud views | didit-auth-events |

## What good output looks like

- The application named, with sandbox, live or unknown, and for a live application a pointer to the console's Products page to check Authentication is on.
- Every endpoint or claim backed by a cited docs link.

## Do not

- Never claim the plugin can change Authentication settings.
- Never ask for credentials or invent endpoints, parameters or claims.
- Never state prices. Link https://didit.me/pricing.
