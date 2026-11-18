# Didit Transaction Monitoring plugin

For compliance and fraud teams. Use your Didit account from Claude, Codex or Cursor to search monitored transactions and see why they were flagged, build and back-test monitoring rules, screen crypto wallets, manage alert channels and webhooks, work cases, and review the AI Investigator queue.

The plugin connects your client to Didit's hosted MCP server (`https://mcp.didit.me/mcp`) and adds six skills that teach the assistant how to use the transaction monitoring tools safely: which application to act in, to back-test before a rule changes, and to ask before any decision or billable screening.

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
/plugin install didit-transaction-monitoring --marketplace didit-protocol/skills
```

Or add the marketplace first, then install:

```
/plugin marketplace add didit-protocol/skills
/plugin install didit-transaction-monitoring@didit
```

Then run `/mcp` and sign in to the `didit` server.

**claude.ai and Cowork** (manual marketplace): open Customize, then Plugins, add the marketplace `didit-protocol/skills`, install Didit Transaction Monitoring, then connect "didit" on the plugin's Connectors tab.

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

## What this plugin does on your machine and where data goes

- The plugin runs no code on your machine. It has no hooks, no scripts and no binaries, and it sends nothing by itself.
- It contains text instructions (the skills) and one entry that points your client at `https://mcp.didit.me/mcp`.
- When you ask for something, the assistant calls the Didit MCP server over HTTPS as you, after you sign in with OAuth ("Log in with Didit"). It acts with the permissions of your role. You never give it a password or an API key.
- Data you ask about is read from, and changes you approve are written to, your Didit account.
- Wallet screening uses your organization's Didit credits in live applications. Sandbox applications are free. The skills tell the assistant to say so before running anything billable in a live application. See https://didit.me/pricing.

## Requirements

- A Didit account. It is free to create at https://business.didit.me.
- A client that supports remote MCP servers with OAuth (Claude Code, claude.ai, Cowork, Codex or Cursor).

## Shorter tool list (optional)

The plugin connects to the full server so it shares one connection with any other Didit plugin or connector. If you want only the tools this plugin uses, connect the `didit` server yourself to `https://mcp.didit.me/mcp?toolsets=core,transactions,cases,investigator,webhooks`. The toolsets that fit this plugin are `core`, `transactions`, `cases`, `investigator`, `webhooks`. Add `read_only=true` to allow reads only. The skills explain to the assistant what changes on such a connection.

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
