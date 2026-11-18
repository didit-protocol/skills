---
name: didit-auth-start
description: Used when a developer asks what Didit Authentication is, how end-user sign-in relates to Didit identity verification and transaction monitoring, whether it is on for their application, or what this plugin can and cannot do. Sets the rules every Didit Authentication skill follows and routes the request.
---

# Didit Authentication: start here

Didit Authentication signs a developer's own customers into the developer's application: hosted sign-in pages, passkeys, email and phone codes, social sign-in and organization SSO. It is separate from signing into the Didit console and from verifying someone's identity. Signing in does not approve a verification or authorize a payment.

## What this plugin can and cannot do

- No MCP tool configures Authentication. Methods, redirect URLs, allowed origins, session and password settings are set in the Didit console.
- This plugin is guidance plus documentation search: it helps plan and write the integration code.
- Docs mark Authentication as new. Treat details as subject to change and check them before writing code.

## Rules

1. Call `didit_context_get` first to find the organization and application, and whether it is sandbox or live. Read that from the result only. Never decide it from an application's name.
2. Before writing any code or naming any endpoint, parameter or claim, call `didit_docs_search` for the current page and cite the link. Never invent an endpoint, parameter or claim name.
3. If a tool is not in your tool list, use the discovery tools (`didit_tool_search`, `didit_tool_describe`, `didit_tool_call_read`) only when they are themselves in your tool list. Never attempt a proxy call around a missing permission or a read-only connection.
4. Never ask for a password, an API key or a one-time code. Never put a verification API key, console token or end-user token in code, URLs or logs.
5. If a step would change something in the person's Didit account (for example a webhook destination), describe it and wait for a clear yes. Tools that delete records or issue credentials take `confirm: true`, sent only after the person agreed to that exact action.
6. Authentication is billed by monthly active user. Never state a price: link https://didit.me/pricing.

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

- The application named, with sandbox or live, and whether Authentication must be turned on first.
- Every endpoint or claim backed by a cited docs link.

## Do not

- Never claim the plugin can change Authentication settings.
- Never ask for credentials or invent endpoints, parameters or claims.
- Never state prices. Link https://didit.me/pricing.
