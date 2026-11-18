# Didit Authentication plugin

For developers adding Didit end-user sign-in (hosted pages, passkeys, codes, social sign-in and organization SSO) to their own app. Didit Authentication signs your customers into your application; it is separate from signing into the Didit console and from identity verification.

This plugin is guidance + documentation search; configuration happens in the Didit console. The Didit MCP server has no tools that configure Authentication: methods, redirect URLs, allowed origins, session and password settings are set in the console. The plugin's four skills help the assistant plan the integration and write code from the current Didit documentation, which it searches with `didit_docs_search`, and find your application with `didit_context_get`. The docs mark Authentication as new, so the skills tell the assistant to check the current page before writing code.

## Which Didit plugin should I install?

| Plugin | Install it if you want |
|---|---|
| `didit` | Everything: verification, review, checks, KYB, transaction monitoring, reports and workspace admin |
| `didit-transaction-monitoring` | Just transaction monitoring: transactions, rules, wallet screening, alerts, cases and the AI Investigator |
| `didit-user-management` | Just the people and companies you verify, your lists, and your workspace team and API keys |
| `didit-authentication` | Guidance for adding Didit end-user sign-in to your own app (not part of `didit`) |

Install either `didit` or the focused plugin for your product, not both. If both are installed nothing breaks: they use the same server and different skill names. The Authentication guidance is only in `didit-authentication`, so it can sit next to `didit`.

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

**claude.ai and Cowork** (manual marketplace): open Customize, then Plugins, add the marketplace `didit-protocol/skills`, install Didit Authentication, then connect "didit" on the plugin's Connectors tab.

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
| didit-auth-integrate | Hosted flow with PKCE, code exchange, token checks with the JWKS, refresh, sign-out |
| didit-auth-events | Sign-in timeline, auth webhooks, event rules, linking sign-in risk to other products |

## What this plugin does on your machine and where data goes

- The plugin runs no code on your machine. It has no hooks, no scripts and no binaries, and it sends nothing by itself.
- It contains text instructions (the skills) and one entry that points your client at `https://mcp.didit.me/mcp`.
- When you ask for something, the assistant calls the Didit MCP server over HTTPS as you, after you sign in with OAuth ("Log in with Didit"). It acts with the permissions of your role. You never give it a password or an API key.
- Data you ask about is read from, and changes you approve are written to, your Didit account.
- Authentication is billed by monthly active user. This plugin's skills do not run anything billable. See https://didit.me/pricing.

## Requirements

- A Didit account. It is free to create at https://business.didit.me.
- A client that supports remote MCP servers with OAuth (Claude Code, claude.ai, Cowork, Codex or Cursor).

## Shorter tool list (optional)

The plugin connects to the full server so it shares one connection with any other Didit plugin or connector. If you want only the tools this plugin uses, connect the `didit` server yourself to `https://mcp.didit.me/mcp?toolsets=core,docs`. The toolsets that fit this plugin are `core`, `docs`. `core` already includes `didit_docs_search` and `didit_context_get`. Add `read_only=true` to allow reads only. The skills explain to the assistant what changes on such a connection.

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
