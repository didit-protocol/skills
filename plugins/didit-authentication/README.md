# Didit Authentication plugin

For developers adding Didit end-user sign-in (hosted pages, passkeys, codes, social sign-in and organization SSO) to their own app. Didit Authentication signs your customers into your application; it is separate from signing into the Didit console and from identity verification.

This plugin provides guidance and documentation search; configuration happens in the Didit console. The Didit MCP server has no tools that configure Authentication: methods, redirect URLs, allowed origins, session and password settings are set in the console. The plugin's four skills help the assistant plan the integration and write code from the current Didit documentation, which it searches with `didit_docs_search`, and find your application with `didit_context_get`. Authentication is new, so the skills tell the assistant to check the current documentation page before writing code.

## Which Didit plugin should I install?

| Plugin | Install it if you want |
|---|---|
| `didit` | Everything: verification, review, checks, KYB, transaction monitoring, reports and workspace admin |
| `didit-transaction-monitoring` | Just transaction monitoring: transactions, rules, wallet screening, alerts, cases and the AI Investigator |
| `didit-user-management` | Just the people and companies you verify, your lists, and your workspace team and API keys |
| `didit-authentication` | Guidance for adding Didit end-user sign-in to your own app (not part of `didit`) |

You can install `didit` on its own or a focused plugin alongside it; they share the same `didit` server, so you keep a single connection. Their skill names differ, so nothing conflicts.

## Install

**Claude Code** (2.1.275 or later):

```
/plugin install didit-authentication --marketplace didit-protocol/skills
```

Or add the marketplace first, then install:

```
/plugin marketplace add didit-protocol/skills
/plugin install didit-authentication@didit
```

Then run `/mcp` and sign in to the `didit` server.

**claude.ai and Cowork** (manual marketplace; directory listing pending): open Customize, then Plugins, add the marketplace `didit-protocol/skills`, install Didit Authentication, then connect "didit" on the plugin's Connectors tab.

**Codex:**

```
codex plugin marketplace add didit-protocol/skills
codex plugin add didit-authentication@didit
```

**Cursor:** use this folder's `.cursor-plugin/plugin.json`.

Already added the Didit server by hand, or installed the `didit` plugin? Keep it. This plugin uses the same server name, `didit`, and the same URL, so your client keeps one connection.

## Skills

| Skill | Use it to |
|---|---|
| didit-auth-start | Learn what Didit Authentication is, how it links to verification and monitoring, what this plugin can and cannot do |
| didit-auth-sign-in-methods | Choose sign-in methods, MFA, password reset, sign-up policy |
| didit-auth-integrate | Hosted flow with PKCE, code exchange, token validation as the docs specify, refresh, sign-out |
| didit-auth-events | Sign-in timeline, auth webhooks, event rules, linking sign-in risk to other products |

Checked against the live server on 2026-11-18: 208 tools on the hosted server as of 2026-11-18 (97 read, 75 write, 36 destructive); the open-source build lists 167. `?toolsets=core` lists 29 and `read_only=true` lists 97. The `evals/` folder holds cases for `claude plugin eval`, with mocked tool results, so no real account is needed to run them.

## What this plugin does on your machine and where data goes

- The plugin runs no code on your machine. It has no hooks, no scripts and no executable binaries (the only binary file is the icon image), and it sends nothing by itself.
- It contains text instructions (the skills) and one entry that points your client at `https://mcp.didit.me/mcp`.
- When you ask for something, the assistant calls the Didit MCP server over HTTPS as you, after you sign in with OAuth ("Log in with Didit"). It acts with the permissions of your role. You sign in with OAuth, so the plugin never asks for your Didit password or an API key.
- It reads data from your Didit account and writes back only the changes you approve.
- Authentication is billed per monthly active user. Nothing in this plugin triggers that billing. See https://didit.me/pricing.

## Requirements

- A Didit account. Create one at https://business.didit.me.
- A client that supports remote MCP servers with OAuth (Claude Code, claude.ai, Cowork, Codex or Cursor).

## Shorter tool list (optional)

The plugins connect to the full server so they share one connection with any other Didit plugin or connector. For a shorter tool list, connect the `didit` server yourself to the URL for your plugin:

| Plugin | Shorter connection |
|---|---|
| `didit` | `https://mcp.didit.me/mcp?toolsets=core` |
| `didit-transaction-monitoring` | `https://mcp.didit.me/mcp?toolsets=core,transactions,cases,investigator,webhooks` |
| `didit-user-management` | `https://mcp.didit.me/mcp?toolsets=core,vendors,lists,account` |
| `didit-authentication` | `https://mcp.didit.me/mcp?toolsets=core,docs` |

`core` includes `didit_context_get` and `didit_docs_search`. When a shorter list leaves tools out, the discovery tools can still reach them. Add `read_only=true` to restrict the connection to read-only tools. The skills tell the assistant what changes on such a connection.

## Disconnect

- Claude Code: `/mcp`, select `didit`, and clear the authentication, or uninstall with `/plugin uninstall didit-authentication`.
- claude.ai and Cowork: disconnect "didit" on the plugin's Connectors tab, or remove the plugin.
- Codex: `codex plugin remove didit-authentication`.

## Support, privacy and terms

- Support: https://help.didit.me
- Documentation: https://docs.didit.me/authentication/overview
- Privacy policy: https://didit.me/terms/privacy-policy
- Terms of service: https://didit.me/terms

## License

MIT. See `LICENSE`.
