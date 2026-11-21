# Didit Transaction Monitoring plugin

For compliance and fraud teams. Use your Didit account from Claude, Codex or Cursor to search monitored transactions and see why they were flagged, build and back-test monitoring rules, screen crypto wallets, handle Travel Rule transfers with other VASPs, manage alert channels and webhooks, work cases, and review the AI Investigator queue.

The plugin connects your client to Didit's hosted MCP server (`https://mcp.didit.me/mcp`) and adds seven skills that teach the assistant to pick the right application, to back-test before changing a rule, and to ask before any decision or billable screening.

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
/plugin install didit-transaction-monitoring --marketplace didit-protocol/skills
```

Or add the marketplace first, then install:

```
/plugin marketplace add didit-protocol/skills
/plugin install didit-transaction-monitoring@didit
```

Then run `/mcp` and sign in to the `didit` server.

**claude.ai and Cowork** (manual marketplace; directory listing pending): open Customize, then Plugins, add the marketplace `didit-protocol/skills`, install Didit Transaction Monitoring, then connect "didit" on the plugin's Connectors tab.

**Codex:**

```
codex plugin marketplace add didit-protocol/skills
codex plugin add didit-transaction-monitoring@didit
```

**Cursor:** use this folder's `.cursor-plugin/plugin.json`.

Already added the Didit server by hand, or installed the `didit` plugin? Keep it. This plugin uses the same server name, `didit`, and the same URL, so your client keeps one connection.

## Skills

| Skill | Use it to |
|---|---|
| didit-tm-start | Sign in, pick the application, learn the rules every other skill follows |
| didit-tm-transactions | Search and read transactions and their rule results, submit a transaction |
| didit-tm-rules | Browse the rule library, install presets, create and change rules, back-test first |
| didit-tm-wallet-screening | Screen one crypto wallet and decide whether to open a case |
| didit-tm-alerts-cases | Alert channels, webhook destinations, and cases: open, assign, escalate, resolve |
| didit-tm-investigator | The AI Investigator queue: reports, accept or override, re-review, policy questions, performance |
| didit-tm-travel-rule | Travel Rule: settings, VASP directory, counterparty contacts, wallet address book and ownership, messages, transfer actions, networks, sandbox tests |

Checked against the live server with a customer account on 2026-11-18: 206 tools for a signed-in person on the hosted server (97 read, 75 write, 34 destructive), plus the six Authentication setup tools added in v5.1.78 on 2026-11-21, so 212 (100 read, 78 write, 34 destructive); 178 on an API key connection; the open-source build lists 173. `?toolsets=core` lists 29 and `read_only=true` lists 100. The `evals/` folder holds cases for `claude plugin eval`, with mocked tool results, so no real account is needed to run them.

## What this plugin does on your machine and where data goes

- The plugin runs no code on your machine. It has no hooks, no scripts and no executable binaries (the only binary file is the icon image), and it sends nothing by itself.
- It contains text instructions (the skills) and one entry that points your client at `https://mcp.didit.me/mcp`.
- When you ask for something, the assistant calls the Didit MCP server over HTTPS as you, after you sign in with OAuth ("Log in with Didit"). It acts with the permissions of your role. The list is the same for every role; a call your role does not allow is refused, with the missing permission in the error. You sign in with OAuth, so the plugin never asks for your Didit password or an API key.
- It reads data from your Didit account and writes back only the changes you approve.
- Submitting transactions and screening wallets: in a live application this can use your Didit credits. Sandbox applications are free to test in. The skills tell the assistant to say so and wait for your agreement before running anything billable in a live application. See https://didit.me/pricing.

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
| `didit-authentication` | `https://mcp.didit.me/mcp?toolsets=core,authentication,docs` |

`core` includes `didit_context_get` and `didit_docs_search`. When a shorter list leaves tools out, the discovery tools can still reach them. Add `read_only=true` to restrict the connection to read-only tools. The skills tell the assistant what changes on such a connection.

## Disconnect

- Claude Code: `/mcp`, select `didit`, and clear the authentication, or uninstall with `/plugin uninstall didit-transaction-monitoring`.
- claude.ai and Cowork: disconnect "didit" on the plugin's Connectors tab, or remove the plugin.
- Codex: `codex plugin remove didit-transaction-monitoring`.

## Support, privacy and terms

- Support: https://help.didit.me
- Documentation: https://docs.didit.me/integration/mcp/overview
- Privacy policy: https://didit.me/terms/privacy-policy
- Terms of service: https://didit.me/terms

## License

MIT. See `LICENSE`.
