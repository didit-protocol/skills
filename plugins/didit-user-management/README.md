# Didit User Management plugin

For operations teams and workspace admins. Use your Didit account from Claude, Codex or Cursor to find and manage the people and companies you verify, keep your blocklist and custom lists, and manage your own Didit workspace.

The plugin covers two separate areas:

- **The people and companies you verify:** vendor users and vendor businesses (search, read, create, change status, delete), custom lists and their entries, the blocklist and the phone allowlist.
- **Your Didit workspace:** organization members and roles (invite, change, remove), API keys for your applications, and your organizations and applications.

It connects your client to Didit's hosted MCP server (`https://mcp.didit.me/mcp`) and adds five skills that teach the assistant which application to act in and to ask before any deletion, removal or new API key.

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
/plugin install didit-user-management --marketplace didit-protocol/skills
```

Or add the marketplace first, then install:

```
/plugin marketplace add didit-protocol/skills
/plugin install didit-user-management@didit
```

Then run `/mcp` and sign in to the `didit` server.

**claude.ai and Cowork** (manual marketplace): open Customize, then Plugins, add the marketplace `didit-protocol/skills`, install Didit User Management, then connect "didit" on the plugin's Connectors tab.

**Codex:**

```
codex plugin marketplace add didit-protocol/skills
codex plugin add didit-user-management@didit
```

**Cursor:** use this folder's `.cursor-plugin/plugin.json`.

Already added the Didit server by hand, or installed the `didit` plugin? Keep it. This plugin uses the same server name, `didit`, and the same URL, so your client keeps one connection.

## Skills

| Skill | Area | Use it to |
|---|---|---|
| didit-users-start | Both | Sign in, pick the application, learn the rules every other skill follows |
| didit-users-records | People you verify | Search, read, create, update, flag, block or delete vendor users |
| didit-users-businesses | People you verify | Search, read, create, flag, block or delete vendor businesses |
| didit-users-lists | People you verify | Custom lists and entries, face entries, blocklist and allowlist |
| didit-users-team | Your workspace | Members and roles, invitations, API keys, applications |

## What this plugin does on your machine and where data goes

- The plugin runs no code on your machine. It has no hooks, no scripts and no executable binaries (the only binary file is the icon image), and it sends nothing by itself.
- It contains text instructions (the skills) and one entry that points your client at `https://mcp.didit.me/mcp`.
- When you ask for something, the assistant calls the Didit MCP server over HTTPS as you, after you sign in with OAuth ("Log in with Didit"). It acts with the permissions of your role. You never give it a password or an API key.
- Data you ask about is read from, and changes you approve are written to, your Didit account.
- The tools this plugin uses do not run verification sessions or checks, which are what use Didit credits in live applications. See https://didit.me/pricing.

## Requirements

- A Didit account. It is free to create at https://business.didit.me.
- A client that supports remote MCP servers with OAuth (Claude Code, claude.ai, Cowork, Codex or Cursor).

## Shorter tool list (optional)

The plugin connects to the full server so it shares one connection with any other Didit plugin or connector. For a shorter tool list, connect the `didit` server yourself to `https://mcp.didit.me/mcp?toolsets=core,vendors,lists,account`. The toolsets that fit this plugin are `core`, `vendors`, `lists`, `account`. Add `read_only=true` to allow reads only. The skills explain to the assistant what changes on such a connection.

## Disconnect

- Claude Code: `/mcp`, select `didit`, and clear the authentication, or uninstall with `/plugin uninstall didit-user-management`.
- claude.ai and Cowork: disconnect "didit" on the plugin's Connectors tab, or remove the plugin.
- Codex: `codex plugin remove didit-user-management`.

## Support, privacy and terms

- Support: https://help.didit.me
- Documentation: https://docs.didit.me/integration/mcp/overview
- Privacy policy: https://didit.me/terms/privacy-policy
- Terms of service: https://didit.me/terms

## License

MIT. See `LICENSE`.
