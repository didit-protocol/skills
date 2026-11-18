# Didit plugin

Use your Didit account from Claude, Codex or Cursor. After you sign in with your Didit account, you can ask in plain words to create verification links, read decisions and the reasons behind them, work the review queue and cases, screen names against sanctions and PEP lists, verify businesses, monitor transactions, and read analytics, balance and exports.

The plugin connects your client to Didit's hosted MCP server (`https://mcp.didit.me/mcp`) and adds eight skills that teach the assistant how to use its tools safely: which application to act in, when to ask before a change, and when an action uses credits.

## Install

**Claude Code** (2.1.275 or later):

```
/plugin install didit --marketplace didit-protocol/skills
```

Or add the marketplace first, then install:

```
/plugin marketplace add didit-protocol/skills
/plugin install didit@didit
```

Then run `/mcp` and sign in to the `didit` server.

**claude.ai and Cowork** (manual marketplace; directory listing pending): open Customize, then Plugins, add the marketplace `didit-protocol/skills`, install Didit, then connect "didit" on the plugin's Connectors tab.

**Codex:**

```
codex plugin marketplace add didit-protocol/skills
codex plugin add didit@didit
```

**Cursor:** install the Didit plugin from github.com/didit-protocol/mcp, or use this folder's `.cursor-plugin/plugin.json`.

Already added the Didit server by hand (a custom connector or `claude mcp add`)? Keep it. The plugin uses the same server name, `didit`, and the same URL.

## Skills

| Skill | Use it to |
|---|---|
| didit-connect | Sign in, pick the organization and application, learn the rules every other skill follows |
| didit-verify-people | Create KYC workflows and verification links, read decisions and why, test in sandbox |
| didit-review-queue | Work sessions in review, approve or decline, add notes, manage cases |
| didit-run-checks | Run one check: AML, ID document, proof of address, database, face, liveness, email, phone |
| didit-verify-businesses | Look companies up in official registries and run full KYB |
| didit-monitor-transactions | Read flagged transactions, backtest and create rules, screen wallets |
| didit-reports | Analytics, credit balance, plan, and exports |
| didit-workspace-admin | Members and roles, webhooks, lists, branding, questionnaires |

## What this plugin does on your machine and where data goes

- The plugin runs no code on your machine. It has no hooks, no scripts and no binaries, and it sends nothing by itself.
- It contains text instructions (the skills) and one entry that points your client at `https://mcp.didit.me/mcp`.
- When you ask for something, the assistant calls the Didit MCP server over HTTPS as you, after you sign in with OAuth ("Log in with Didit"). It acts with the permissions of your role. You never give it a password or an API key.
- Data you ask about is read from, and changes you approve are written to, your Didit account.
- Billable operations (verification sessions, standalone checks) use your organization's Didit credits in live applications. Sandbox applications are free. The skills tell the assistant to say so before running anything billable in a live application. See https://didit.me/pricing.

## Requirements

- A Didit account. It is free to create at https://business.didit.me.
- A client that supports remote MCP servers with OAuth (Claude Code, claude.ai, Cowork, Codex or Cursor).

## Lighter or read-only connection

You can connect to `https://mcp.didit.me/mcp?toolsets=core` for a short list of about 30 tools, and add `read_only=true` to allow reads only. The skills explain to the assistant what changes on such a connection.

## Disconnect

- Claude Code: `/mcp`, select `didit`, and clear the authentication, or uninstall with `/plugin uninstall didit`.
- claude.ai and Cowork: disconnect "didit" on the plugin's Connectors tab, or remove the plugin.
- Codex: `codex plugin remove didit`.

## Support, privacy and terms

- Support: https://help.didit.me
- Documentation: https://docs.didit.me/integration/mcp/overview
- Privacy policy: https://didit.me/terms/privacy-policy
- Terms of service: https://didit.me/terms

## Building an integration instead?

This plugin is for working in your Didit account from chat. Developers who write backend code against the Didit REST API with an API key should use the `didit-api` plugin from the same marketplace, or the skills in the `skills/` folder of github.com/didit-protocol/skills.

## License

MIT. See `LICENSE`.
