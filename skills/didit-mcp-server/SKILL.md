---
name: didit-mcp-server
description: >
  Use when connecting an AI assistant or agent to a Didit account through the Didit MCP server
  (Model Context Protocol), not for backend REST integration code. Covers installing the hosted
  server in Claude Code, claude.ai, Claude Desktop, ChatGPT, OpenAI Codex, Cursor, VS Code,
  Windsurf, Zed or any MCP client; signing in with a Didit console account (OAuth 2.1) or
  connecting with an application API key; running the local stdio server or self-hosting the
  HTTP server, with device-code login; toolsets and
  read-only mode; and having an agent act in the Didit Business Console: workflows, sessions,
  standalone checks, users, transactions and rules, lists, cases, webhooks, reports and billing.
  Covers scopes, roles, confirmations and file inputs.
version: 1.1.0
metadata:
  openclaw:
    requires:
      env: []
    primaryEnv: DIDIT_ACCESS_TOKEN
    emoji: "🔌"
    homepage: https://docs.didit.me
---

# Didit MCP Server

> This skill is for an AI client working inside a Didit account. Writing backend code that calls the Didit REST API with an application API key? Use **didit-verification-management**, **didit-sdk-integration** and the standalone API skills instead.

## Overview

The Didit MCP server lets an MCP client call the Didit platform through tools. It is read-and-write: agents can create sessions, change workflows, update statuses and delete data. Facts and counts below are for server version 5.1.67 (`@didit-protocol/mcp-server@5.1.67`).

**Key facts:**
- Hosted endpoint: `https://mcp.didit.me/mcp` (Streamable HTTP, stateless). `GET https://mcp.didit.me/healthz` returns the server status, its version and the `features` it supports (for example `toolsets`, `read_only`, `api_key`).
- Two ways to connect:
  - **Log in with Didit** (OAuth 2.1 with PKCE, the default and recommended path): the server acts as the signed-in person, across every organization and application they belong to, with their console role permissions.
  - **Application API key** (headless agents and CI with no person present): the connection is that one application, with the key's own access. See Connect with an API key.
- Tool results are processed, not raw endpoint JSON. A successful call returns compact JSON text plus `structuredContent` (an object as is; an array or a scalar wrapped as `{"value": ...}`). Redaction is per handler and covers only these fields: on applications `api_key`, `client_secret` and `secret` (replaced by `*_set` and a masked `*_preview`); on API key lists `api_key`, `key`, `secret`, `token` and `value` (the same); on webhook destinations the signing secret (`secret_shared_key`, `signing_secret`, `secret`, replaced by `secret_set`). Nothing else is redacted: webhook destination URLs (path and query included) and alert destinations from `didit_alert_list` (for Slack, the posting URL in `value`) are returned as stored, so mask them before showing them to anyone (host plus the last 4 characters, for example `hooks.slack.com/...a1B2`). On the hosted server `didit_org_create_api_key` also returns the new key's secret once, on purpose; a local server also returns credentials from `didit_org_reveal_application_api_key` (the raw key) and `didit_account_verify_email` (the new applications' API keys and an access token). Large payloads (for example workflow feature configs) are summarized. A failed call returns no `structuredContent`: an error raised by a tool handler is sanitized text with a code and a message, plus field, hint and allowed values when there are any, while a refusal by the server itself (for example a write on a read-only connection) is plain text with no code.
- Open source (MIT): https://github.com/didit-protocol/mcp, published on npm as `@didit-protocol/mcp-server` (binary `didit-mcp-server`).

**When to use the REST skills instead:** a backend integration that runs with an application API key in your own code (creating sessions for your users, receiving webhooks, submitting transactions) calls the REST API directly; see **didit-verification-management**, **didit-sdk-integration** and the standalone API skills.

**Pricing (as of 2026-11-18, [pricing page](https://docs.didit.me/getting-started/pricing)):** the pricing page lists no separate price for the MCP server. Tools that run billable operations (for example `didit_session_create` on a live application and the `didit_verify_*` standalone checks) use your credit at the same prices as the matching API calls. The sandbox is free on every plan (500 test sessions per sandbox application every 24 hours), and the server describes a sandbox application as never billed. Other skills point here or to the pricing page instead of repeating these terms.

**Docs:** https://docs.didit.me/integration/mcp/overview · Per client: [Claude](https://docs.didit.me/integration/mcp/claude), [ChatGPT](https://docs.didit.me/integration/mcp/chatgpt), [Cursor](https://docs.didit.me/integration/mcp/cursor), [VS Code](https://docs.didit.me/integration/mcp/vscode), [OpenAI Codex](https://docs.didit.me/integration/mcp/codex) · Toolsets: https://docs.didit.me/integration/mcp/toolsets · Authentication: https://docs.didit.me/integration/mcp/authentication · Tools reference: https://docs.didit.me/integration/mcp/tools

---

## Authentication

### Log in with Didit (OAuth 2.1)

The hosted server is an OAuth 2.1 resource server; the Didit Business Console (`https://business.didit.me`) is the authorization server. Your client runs the whole flow:

1. `POST /mcp` without a token answers `401` with `WWW-Authenticate: Bearer ... resource_metadata="https://mcp.didit.me/.well-known/oauth-protected-resource/mcp"`.
2. The client reads that metadata, then `https://business.didit.me/.well-known/oauth-authorization-server`, and registers itself with dynamic client registration if it has no client id.
3. It opens the browser for the authorization code flow with an S256 PKCE challenge; the user signs in (or registers) and approves the scopes. A public client uses PKCE with no client secret; the server metadata also lists `client_secret_post` and `client_secret_basic` for confidential clients.
4. It sends `Authorization: Bearer <access_token>` on every `POST /mcp`. Access tokens are short-lived and refreshed automatically with the refresh token.

The server advertises three scopes. Which resources each one covers is taken from the [tools reference](https://docs.didit.me/integration/mcp/tools) (checked 2026-11-18):

| Scope | Covers (per the tools reference) |
|---|---|
| `didit:verification` | Sessions, businesses, cases, networks, transactions and the blocklist |
| `didit:management` | Workflows, questionnaires, lists, webhooks, integrations, members, roles, API keys, audit logs, the organization, applications, subscription and users |
| `didit:staff` | Didit staff accounts only: the authorization server grants it to no one else. The local server's device login asks for it along with the other two, and a customer account simply does not receive it. A client you configure yourself should request only the first two |

- Access is limited by both the approved scopes and the person's console role in each organization; the Didit backend checks the role on every call. The tools reference lists the role permission each tool needs.
- Per the tools reference, `didit_session_create` needs a role with `create:sessions` or `write:sessions`. The server declares no local pre-check for it and leaves that check to the backend.
- Disconnect an app in the console under **Settings > Authentication > Connected apps**, or revoke its refresh token yourself (RFC 7009), which stops it from getting new access tokens. The hosted server remembers an accepted access token for up to 60 seconds (default `MCP_INTROSPECTION_CACHE_TTL_MS`), so a revoked access token can keep reaching the server for that long; each Didit API call a tool makes re-checks the token at the API.

The local server's `logout` revokes this way: a form-encoded `POST` to the `revocation_endpoint` that `https://business.didit.me/.well-known/oauth-authorization-server` advertises, sent by the client that obtained the token.

```bash
# The refresh token is read from stdin (here a file readable only by you), never from the arguments.
curl -X POST "$REVOCATION_ENDPOINT" \
  --data-urlencode 'token@-' \
  --data-urlencode "token_type_hint=refresh_token" \
  --data-urlencode "client_id=<your-client-id>" < refresh-token.txt
```

Under RFC 7009 a success answer does not tell you whether the token was still live.

### Connect with an API key

An agent that runs with no person present (CI, a scheduled job, a backend agent) can connect to the hosted server with an application API key instead of signing in. Send it as `x-api-key: <key>` (or `Authorization: Bearer <key>`) on every request to `https://mcp.didit.me/mcp`. Put the key in the client's config as an environment reference that the client expands itself. Claude Code, in `.mcp.json`:

```json
{"mcpServers": {"didit": {"type": "http", "url": "https://mcp.didit.me/mcp", "headers": {"x-api-key": "${DIDIT_API_KEY}"}}}}
```

Cursor (`${env:...}` syntax):

```json
{"mcpServers": {"didit": {"url": "https://mcp.didit.me/mcp", "headers": {"x-api-key": "${env:DIDIT_API_KEY}"}}}}
```

Do not write `--header "x-api-key: $DIDIT_API_KEY"` on a command line: the shell expands `$DIDIT_API_KEY` before the client starts, so the full key sits in the process arguments (visible to other local users in the process list) and in shell history.

- **One application.** The connection acts on the key's application; no ids to pass. `didit_context_get` reports `connection.type: "api_key"` and the app's `mode` when it is available. A call that names another organization or application is refused.
- **The key's own access.** The key is forwarded to the Didit API as on a direct call; a restricted key reaches only what it was given. Give an agent a restricted key with an expiry.
- **Sandbox first.** Build and test with the sandbox application's key.
- **Not for person-only tools.** Members, roles and API key management, plan, cards, receipts and billing details, the audit log, `didit_workflow_build_graph`, and PDF or e-signature download links are neither listed nor run on an API key connection.
- A key limited to specific IP addresses is refused (the API would see the server's address). A revoked key stops working once the server's cached check expires (up to 60 seconds by default). A rotated key is different: its old secret keeps working until the rotation's grace period ends, because the key's `expires_at` is the earlier of its own expiry and that grace period.

## Getting Started (No Account Yet?)

No key or install is needed for the hosted server. Add `https://mcp.didit.me/mcp` to your client (next section); on first use the browser opens **Log in with Didit**, where you can also create a Didit account. For a machine with no browser, use the device code login (Local server and self-hosting).

---

## Install in a Client

In Claude Code, the Didit plugin bundles the server connection and these skills: `/plugin install didit --marketplace didit-protocol/skills`.

| Client | Setup |
|---|---|
| Claude Code | `claude mcp add --transport http didit https://mcp.didit.me/mcp`, then run `/mcp` in Claude Code to sign in |
| claude.ai and Claude Desktop | **Settings > Connectors > Add custom connector**, name `Didit`, URL `https://mcp.didit.me/mcp`, then **Connect**. Pre-filled link: `https://claude.ai/customize/connectors?modal=add-custom-connector&connectorName=Didit&connectorUrl=https://mcp.didit.me/mcp`. Guide: https://docs.didit.me/integration/mcp/claude |
| ChatGPT | Guide: https://docs.didit.me/integration/mcp/chatgpt |
| OpenAI Codex | `codex mcp add didit --url https://mcp.didit.me/mcp`. Guide: https://docs.didit.me/integration/mcp/codex |
| Cursor | `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project), see below. Guide: https://docs.didit.me/integration/mcp/cursor |
| VS Code (agent mode) | `.vscode/mcp.json`, see below, or **MCP: Add Server** > **HTTP**. Guide: https://docs.didit.me/integration/mcp/vscode |
| Windsurf | `~/.codeium/windsurf/mcp_config.json` with the `mcp-remote` bridge, see below |
| Zed | `settings.json` `context_servers` with the `mcp-remote` bridge, see below |
| Any other client | Streamable HTTP + OAuth 2.1 directly against `https://mcp.didit.me/mcp`; a stdio-only client uses `npx -y mcp-remote@0.16.6 https://mcp.didit.me/mcp` |

The client commands and file locations follow Didit's [installation guide](https://docs.didit.me/integration/mcp/installation) (checked 2026-11-18). That guide marks the Zed config as manual and unverified, so confirm it against your Zed version.

Cursor:

```json
{"mcpServers": {"didit": {"url": "https://mcp.didit.me/mcp"}}}
```

VS Code:

```json
{"servers": {"didit": {"type": "http", "url": "https://mcp.didit.me/mcp"}}}
```

Windsurf:

```json
{"mcpServers": {"didit": {"command": "npx", "args": ["-y", "mcp-remote@0.16.6", "https://mcp.didit.me/mcp"]}}}
```

Zed:

```json
{"context_servers": {"didit": {"source": "custom", "command": "npx", "args": ["-y", "mcp-remote@0.16.6", "https://mcp.didit.me/mcp"]}}}
```

The guide and the server README use `mcp-remote@latest`. This skill pins `mcp-remote@0.16.6` (the npm `latest` release on 2026-11-18) and `@didit-protocol/mcp-server@5.1.67`; change them deliberately when you upgrade. Keep the client's "review tool calls before running" setting on.

### Endpoint behaviour

- `POST /mcp` carries the MCP protocol. The bare origin `https://mcp.didit.me` answers MCP `POST` requests exactly like `/mcp`, so a client given the address without the path still connects.
- `GET /mcp`: the hosted server at mcp.didit.me shows a page with connect links to a browser navigation and answers `405` to any other `GET` (for example a client asking for a stream: the server is stateless and has no server-initiated stream). The open-source build ships no page, so a self-hosted server built from it answers `405` to every `GET /mcp`.
- `GET` on the bare origin: where the deployment supplies the page, every request that does not name an MCP media type in `Accept` gets it (crawlers and `curl` included) and one that does gets `405`. Without a page (the open-source build) it is always `405`.
- `DELETE` on `/mcp` or the bare origin answers `405`: there is no session to end.

## Toolsets and Read-Only Mode

By default a connection lists every tool. In the default `shadow` permission mode that includes tools the person's role will be refused when called (the backend answers `403`); only `enforce` mode hides them, and only when the token carries role permissions the server can evaluate. Tool definitions are sent to the model on every request, so a shorter list saves tokens. Name toolsets on the server URL:

```
https://mcp.didit.me/mcp?toolsets=core
https://mcp.didit.me/mcp?toolsets=core,workflows
https://mcp.didit.me/mcp?toolsets=core,transactions,cases&read_only=true
```

| Toolset | What it holds |
|---|---|
| `core` | The short list: organizations and applications, sessions (create, find, decide, explain, simulate in the sandbox, webhook deliveries), finding workflows, analytics and balance, the application's API key and webhooks, finding cases, users, businesses and transactions, documentation search (29 tools in v5.1.67, discovery tools included) |
| `account` | Organizations, applications, API keys, members and roles |
| `billing` | Plan, credit balance, payment methods, receipts and billing details |
| `sessions` | Verification sessions: create, find, decide, review, share, import, PDFs and webhook deliveries |
| `workflows` | Verification workflows and questionnaires: build, edit, validate and publish |
| `lists` | Custom lists, the blocklist and the allowlist |
| `vendors` | Vendor users and vendor businesses |
| `transactions` | Transactions, wallet screening and rules with back-testing |
| `cases` | Case management |
| `investigator` | The AI Investigator: review queue, reports, decisions, policy questions and performance |
| `webhooks` | Webhook destinations and alerts |
| `reports` | Analytics, exports and the audit log |
| `branding` | White-label branding of the verification flow |
| `verification` | Standalone verification APIs: ID document, face, AML, proof of address, phone, email, database and business checks |
| `docs` | Search the Didit documentation |
| `all` | Every tool (the default) |

- A toolset decides what is **listed**, not what may run: a tool outside the selection still runs when called by name, with the same permission checks.
- When the listed selection leaves out tools the connection could use, it also gets the discovery tools: `didit_tool_search` (find a tool or list a toolset), `didit_tool_describe` (its full schema), `didit_tool_call_read` and, unless the connection is read-only, `didit_tool_call_write` (run it). Calls through them are checked exactly like direct calls.
- `read_only=true` lists only tools that read and refuses every call that would change data, whatever the client remembers. In v5.1.67 a signed-in person with every toolset sees 77 tools in read-only mode.
- Clients that cannot edit the URL send the `X-MCP-Toolsets` and `X-MCP-Readonly` headers. The local server takes `--toolsets=core,workflows` and `--read-only`, or `DIDIT_TOOLSETS` and `DIDIT_READ_ONLY`. An unknown toolset is ignored, not an error.
- `didit_docs_search` searches the live documentation at docs.didit.me; use it for "how does Didit work" questions instead of answering from memory.

## Local Server and Self-Hosting

### Device code login (no browser on this machine)

For the local (stdio) server on a remote machine, in a container or in CI:

```bash
npx -y @didit-protocol/mcp-server@5.1.67 login
```

The terminal prints a short code and a link to `https://business.didit.me/device`. Open it on any device, sign in, check that the code matches and approve. Approve only a code you started yourself.

- Credentials are stored in `~/.config/didit/mcp-credentials.json` (override with `DIDIT_MCP_CREDENTIALS_FILE`), readable by you only. The command prints the granted scopes, never the token.
- The local server uses the stored credentials when `DIDIT_ACCESS_TOKEN` is not set, and refreshes them before they expire. Refresh tokens rotate, so do not share one credentials file between jobs that run at the same time.
- `npx -y @didit-protocol/mcp-server@5.1.67 logout` revokes the stored refresh token at the authorization server and deletes the stored credentials. The local copy is deleted even when the revocation fails (for example offline); then end the grant in the console under **Connected apps**.
- With no shell, an agent can call `didit_account_device_login_start`, show the link and code, then `didit_account_device_login_poll` after approval.
- Local server only: `didit_account_register` creates an account and `didit_account_verify_email` confirms it with the emailed code; `didit_account_login` signs in with an email and password, followed by `didit_account_verify_2fa` when the account has an authenticator. The sign-in is kept in the same credentials file, or in memory for the life of the process when that file cannot be written. The hosted server never takes a password.

### Stdio with a user token

```bash
# DIDIT_ACCESS_TOKEN is already exported in this shell (for example read with `read -rs`).
npx -y @didit-protocol/mcp-server@5.1.67
```

Register it in Claude Code through `.mcp.json`, with an environment reference Claude Code expands when it starts the server:

```json
{"mcpServers": {"didit-local": {"command": "npx", "args": ["-y", "@didit-protocol/mcp-server@5.1.67"], "env": {"DIDIT_ACCESS_TOKEN": "${DIDIT_ACCESS_TOKEN}"}}}}
```

`claude mcp add ... -e DIDIT_ACCESS_TOKEN=<token>` puts the token in the process arguments and shell history; use the config file instead.

- `DIDIT_ACCESS_TOKEN` is a Didit **user** access token, not an application API key, and takes precedence over stored credentials. Treat it as a secret: keep it in the client's env config, never in a prompt or a repository.
- `MCP_DEFAULT_ORG` and `MCP_DEFAULT_APP` set the default organization and application for single-tenant setups; an `organization_id` or `application_id` passed in a call wins.

### Self-hosted HTTP server

Clone https://github.com/didit-protocol/mcp at a release tag, `npm install && npm run build`, then `node dist/http.js` (or `docker build -t didit-mcp .` and `docker run -p 3000:3000 --env-file .env didit-mcp`). It is an OAuth resource server and also accepts application API keys in the default `introspection` verify mode.

| Variable | Mode | Purpose |
|---|---|---|
| `DIDIT_ACCESS_TOKEN` | stdio | User Bearer token for headless runs |
| `DIDIT_MCP_CREDENTIALS_FILE` | stdio | Where `login` stores credentials (default `~/.config/didit/mcp-credentials.json`) |
| `DIDIT_TOOLSETS`, `DIDIT_READ_ONLY` | stdio | Toolsets and read-only mode for the local server |
| `DIDIT_API_BASE_URL` | both | Verification API base (default `https://verification.didit.me/v3`) |
| `DIDIT_AUTH_BASE_URL` | both | Auth API base (default `https://apx.didit.me/auth/v2`) |
| `MCP_PORT` | HTTP | Listen port (default `3000`) |
| `MCP_RESOURCE_URI` | HTTP | Full public URL of the transport, path included (`https://mcp.example.com/mcp`) |
| `MCP_AUTHORIZATION_SERVER_ORIGIN` | HTTP | Authorization server (default `https://business.didit.me`) |
| `MCP_TOKEN_VERIFY_MODE` | HTTP | `introspection` (default, opaque tokens and API keys) or `jwks` |
| `MCP_OAUTH_INTROSPECT_URL`, `MCP_OAUTH_CLIENT_ID`, `MCP_OAUTH_CLIENT_SECRET` | HTTP | RFC 7662 introspection endpoint and its credentials (from a secret manager) |
| `MCP_INTROSPECTION_CACHE_TTL_MS` | HTTP | How long an accepted token is remembered before it is introspected again (default `60000`) |
| `MCP_SCOPES_SUPPORTED` | HTTP | Scopes advertised (default `didit:management didit:verification didit:staff`) |
| `MCP_DEFAULT_TOOLSETS` | HTTP | Toolsets a connection gets when it names none |
| `MCP_DEFAULT_ORG`, `MCP_DEFAULT_APP` | both | Default organization and application |
| `DIDIT_AUTH_ISSUER`, `DIDIT_OIDC_DISCOVERY_URL`, `DIDIT_OIDC_AUTHORIZE_URL`, `DIDIT_OIDC_TOKEN_URL`, `DIDIT_OIDC_REGISTRATION_URL`, `DIDIT_JWKS_URL` | HTTP | Authorization server overrides; `DIDIT_JWKS_URL` for `jwks` mode |
| `MCP_PERMISSION_MODE` | both | Per-tool role pre-check: `shadow` (default: list everything, the backend answers `403`), `enforce` (hide tools the role cannot run and refuse calls with `missing_scope`, when the token carries role permissions the server can evaluate), `off` |
| `MCP_JSON_BODY_LIMIT` | HTTP | JSON-RPC body limit (default `25mb`) |
| `MCP_PDF_DOWNLOAD_KEY` | HTTP | 64 hex characters, shared by all replicas; required for session PDF and e-signature download links |

---

## Tools

Tool names start with `didit_`. Annotations mark each tool read-only, write or destructive (`readOnlyHint`, `destructiveHint`). Whether a client asks before running a destructive tool depends on the client and its settings; the server does not prompt. Get the human's approval yourself (see Confirmations).

**Coverage in v5.1.67:** a signed-in person on the hosted server with every toolset sees 167 tools: 77 read, 62 write and 28 destructive (fewer only when the server runs with `MCP_PERMISSION_MODE=enforce` and can evaluate the person's role permissions from the token). The local stdio server adds 9 more: the 7 account sign-in tools (`didit_account_register`, `_verify_email`, `_resend_otp`, `_login`, `_verify_2fa`, `_device_login_start`, `_device_login_poll`), `didit_org_top_up` and `didit_org_reveal_application_api_key`. With `?toolsets=core` the list is 29 tools.

| Group | Main tools |
|---|---|
| Discovery and cross-app | `didit_context_get` (call first: every organization and application, with each app's `mode` `live` or `sandbox` when it is known), `didit_session_search`, `didit_transaction_search`, `didit_case_search`, `didit_vendor_user_search`, `didit_vendor_business_search`, `didit_workflow_search`, `didit_analytics`, `didit_docs_search` |
| Sessions, imports and signatures | `didit_session_create` (returns `session_id`, `url`, `session_token`), `_simulate` (finish a sandbox session with a chosen outcome), `_list`, `_get_decision`, `_explain_decision`, `_update_status`, `_update_data`, `_update_poa_data`, `_add_review`, `_list_reviews`, `_generate_pdf`, `_share`, `_import_shared`, `_get_location_evidence`, `_webhooks`, `_webhook_resend`, `_delete`, `_batch_delete`; imports: `_create_import`, `_get_import`, `_get_import_errors`, `_get_import_template`, `_manage_import`, `_list_import_providers`, `_check_import_provider`; e-signatures: `_get_signature_evidence`, `_get_signed_document`, `_get_signature_field_image`, `_validate_signatures` (re-checks the signed documents and saves the result in each signer's validation) |
| Workflows and questionnaires | `didit_workflow_list`, `_get`, `_create`, `_update`, `_delete`, `_get_graph`, `_edit_graph`, `_set_graph`, `_validate_graph`, `_build_graph`, `_get_branch_fields`, `_get_field_definitions`, `_get_feature_config_schema`, `_get_id_verification_methods_catalog`, `_get_kyb_registry_catalog`, `_create_draft`, `_publish`; `didit_questionnaire_list`, `_get`, `_create`, `_append_choices`, `_update`, `_delete` |
| Vendors | `didit_vendor_user_list`, `_get`, `_create`, `_update`, `_update_status`, `_delete`, and the same set for `didit_vendor_business_*` |
| Transactions, rules and wallet screening | `didit_transaction_list`, `_get`, `_create`, `_screen_wallet`, `didit_transaction_rule_list`, `_get`, `_create`, `_update`, `_delete`, `_backtest`, `_library_list`, `_install`, `_uninstall` |
| Cases | `didit_case_list`, `_get`, `_create`, `_statistics`, `_manage` |
| Investigator | `didit_investigator_queue_list`, `_report_get`, `_record_get`, `_add_note`, `_question_list`, `_question_get`, `_backtest_start`, `_backtest_get`, `_performance_get`, `_dashboard_get`, `_activity_list`; decisions (`_accept`, `_batch_accept`, `_override`, `_question_answer`, `_question_dismiss`, `_rereview`) need `confirm: true` |
| Lists | `didit_lists_list`, `_get`, `_create`, `_update`, `_delete`, `_entries_list`, `_entry_create`, `_entry_upload_face`, `_entry_delete`, `didit_blocklist_get`, `_add`, `_remove`, `didit_allowlist_add` |
| Webhooks and alerts | `didit_webhook_list`, `_get`, `_create`, `_update`, `_delete`, `didit_alert_list`, `didit_alert_configure` |
| Reports and audit log | `didit_report_list`, `_get`, `_get_download_url`, `_export`, `didit_audit_log_list` |
| Account and organization | `didit_org_list`, `_list_applications`, `_get_application` (API key masked), `_list_members`, `_invite_member`, `_update_member`, `_remove_member`, `_list_roles`, `_list_api_keys` (values redacted), `_create_api_key` (one scoped key per connected app and application; the secret is returned once) |
| Billing | `didit_org_get_balance`, `didit_billing_get_plan`, `_quote_plan`, `_list_payment_methods`, `_list_receipts`, `_get_details`, `_update_details` |
| Branding | `didit_branding_get`, `didit_branding_update` |
| Standalone verification | `didit_verify_id`, `_poa`, `_database`, `_kyb_search`, `_kyb_select`, `_passive_liveness`, `_face_match`, `_face_search`, `_age`, `_aml`, `_email_send`, `_email_check`, `_phone_send`, `_phone_check`, `_account_check` |

See https://docs.didit.me/integration/mcp/tools for the per-tool table with each tool's type, scope and role permission (a dash where the backend has no per-role check).

### Top-ups and secrets: hosted vs local

- On the hosted `/mcp` endpoint no tool charges a card. When credit is needed, `didit_org_get_balance` and the billing tools return console links (`next_steps.top_up_url` opens the top-up dialog with the amount filled in) and the person pays in the console.
- `didit_org_top_up` is offered by the local stdio server and by the separate, unlisted `https://mcp.didit.me/mcp/payments` endpoint; it is not in the `/mcp` catalog, and a call to it there is refused with the console link. Charging a saved card also needs a person to turn on agent top-ups in the console (off by default).
- `didit_org_reveal_application_api_key` (the raw key of an application) is local stdio only. On the hosted server, `didit_org_create_api_key` creates a new scoped key instead.

### Scope resolution

`organization_id` and `application_id` default to the person's only organization and application (or to `MCP_DEFAULT_ORG` and `MCP_DEFAULT_APP` on a self-hosted server). An organization whose applications could not be listed gives no default application, even when it is the only one.

Scope ids follow each tool's schema. Always send the ids a tool requires. Send an optional `organization_id` or `application_id` only when the context shows several organizations or applications, or when it returned no default for that id: then ask the person which organization or application to use and pass the one they name. Never send an id the tool does not declare. Through a discovery proxy (`didit_tool_call_read` or `didit_tool_call_write`), put the target's arguments, ids included, inside `arguments`, never next to `name`.

Rules that matter with several:
- **Ids required:** `didit_org_list_applications` needs `organization_id`, `didit_org_list_api_keys` needs `application_id`, and `didit_org_get_application` and `didit_org_create_api_key` need both ids.
- **Cross-app without ids:** the six aggregate searches `didit_session_search`, `didit_transaction_search`, `didit_case_search`, `didit_vendor_user_search`, `didit_vendor_business_search` and `didit_workflow_search` (rows tagged with their organization and application), and `didit_analytics` (aggregate totals over the apps it scanned). Six per-app lists fall back to the matching cross-app search when you pass no scope: `didit_session_list`, `didit_workflow_list`, `didit_case_list`, `didit_transaction_list`, `didit_vendor_user_list` and `didit_vendor_business_list`.
- **Everything else that is per app needs both ids then**, record reads included (for example `didit_case_get`, `didit_workflow_get`, `didit_session_validate_signatures`). Other tools whose names end in `_search` are not cross-app discovery: `didit_verify_kyb_search`, for example, starts a company registry check in one application.
- **No ids at all:** for example `didit_context_get`, `didit_docs_search`, and the session tools keyed by `session_id` alone such as `didit_session_get_decision`.
- When unsure, read the tool's own schema (`didit_tool_describe`, or the tools reference). On an API key connection ids are never needed.

Read the environment from `didit_context_get` (`mode`), never from an app's name. In a sandbox application, `didit_session_create` accepts `sandbox_scenario` and `didit_session_simulate` finishes a session with the outcome you choose (sandbox billing: see Pricing above).

### Confirmations

The server refuses these calls without `confirm: true` (a real boolean):
- `didit_session_delete` (one session): `session_id` and `confirm: true`, always.
- `didit_session_batch_delete` (several sessions): `session_numbers` (a non-empty list) or `delete_all: true`, plus `confirm: true`, always.
- `didit_vendor_user_delete` and `didit_vendor_business_delete`: only with `delete_all: true`. An explicit id list is deleted without `confirm`.
- `didit_case_manage` when it files a SAR: action `resolve` with `data.status: "SAR_FILED"` and `confirm: true`.
- `didit_org_create_api_key`, the Investigator decision tools, and on the local server `didit_org_reveal_application_api_key` and `didit_org_top_up`.

**Whatever the server enforces, an agent must ask the human and get explicit approval for that exact action before any delete, decision or credential call, and before passing `confirm: true`.** Deletion is permanent.

### File inputs

Tools that take files (ID, proof of address, liveness, face match, face search, age, list face entries, branding) accept each file as either `<name>_path` or `<name>_base64`, exactly one:
- `*_path`: absolute path on the machine running the server; only works with a local stdio server.
- `*_base64`: raw base64 or a `data:` URL; use this with the hosted server.
- Maximum 15 MB; PNG, JPG/JPEG, WebP, GIF, BMP, ICO or PDF. File content is checked; a `*_path` file must also have one of those extensions.

### Session PDF reports and e-signature files

`didit_session_generate_pdf` returns `download_url`, `expires_at` and `expires_in` (300 seconds). Fetch the URL without an `Authorization` header to get the PDF. The three e-signature file tools (`didit_session_get_signature_evidence`, `_get_signed_document`, `_get_signature_field_image`) return the same kind of link plus `content_type`. Treat the links as secrets.

### Responses

A successful call returns compact JSON text (the channel the model reads) and the same result as `structuredContent`: an object as is, an array or a scalar wrapped as `{"value": ...}`. Results are shaped by the server, not passed through raw: API keys and webhook signing secrets are redacted (copy the signing secret from **Webhooks** in the console). On the hosted server the one deliberate exception is `didit_org_create_api_key`, which returns the new secret once; a local server also returns credentials from `didit_org_reveal_application_api_key` and `didit_account_verify_email`. Large workflow configs are summarized. A failed call has no `structuredContent`. An error from a tool handler is sanitized text: a code and a message, plus field, hint and allowed values when present, without backend secrets or local paths. A refusal by the server itself (a write on a read-only connection, a tool this connection cannot call) is plain text without a code. Synchronous tools (workflows, billing, `didit_verify_*`, lists) return the final result. `didit_session_create` returns a `url` the end user must complete; the decision arrives later by webhook or `didit_session_get_decision`. Decision keys are plural arrays (`id_verifications[]`, `liveness_checks[]`, `face_matches[]`, `aml_screenings[]`, ...), one entry per workflow node.

---

## Error Responses

| Error | Meaning | Action |
|---|---|---|
| `401` from `/mcp` (`WWW-Authenticate: Bearer error="invalid_token"`) | Token or API key missing, expired or revoked | Let the client refresh, re-run **Log in with Didit**, or send a valid API key |
| `403` from a tool | Often the person's role in that organization lacks the permission; it can also be another refusal by the backend | Read the error code and hint; for a missing role permission, ask an owner or admin |
| `missing_scope` | Read its `field` and hint. With a permission named, the role in that organization lacks it (the server checks this before calling in `enforce` mode). On `didit_org_create_api_key` it can instead mean `organization_id` or `application_id` was not passed | Missing ids: read them from `didit_context_get` and pass them, no role change needed. Missing permission: ask an owner or admin to grant it |
| `405` | `GET` (other than a browser navigation on a deployment that serves the page) or `DELETE` on `/mcp` or the bare origin | Use `POST` |
| `unsafe_operation` / `bad_request` on a delete | Read the error's `field`. `confirm`: the confirmation is missing or not a boolean. Another field (for example `session_numbers` or `vendor_data_list`): the id list is missing, empty or too long | Retry with `confirm: true` only when the tool declares `confirm` and the error names it, after the human approved that exact deletion; otherwise fix the named field |
| File rejected | `*_path` sent to the hosted server, both forms sent, over 15 MB, or not an allowed file type | Send one `*_base64` value of an allowed type |
| `organization_id is required` or empty results | Several apps, or no default, and no scope | Use one of the six aggregate searches or `didit_context_get`, ask the person which organization and application, then pass the ids the tool declares |
| Every tool fails | Possible causes include the app being disconnected in **Connected apps** or a sign-in that can no longer refresh | Reconnect and approve the connection again |
| Refused on an API key connection | The tool needs a person (members, billing, audit log, downloads) or names another application | Use an OAuth connection, or the console |
| `invalid_redirect_uri` at sign-in | The authorization server does not accept the client's callback URL; for a remote client this can mean it has not been reviewed yet | Check the redirect URI the client sends; if it is right, contact Didit support |

---

## Common Workflows

### Connect and check access

1. Add the server (Install in a Client) and sign in.
2. `didit_context_get` lists organizations and applications with their `mode` when it is known.
3. `didit_org_get_balance` before running billable tools on a live application.

### Build a KYC workflow and send a link

1. `didit_workflow_get_feature_config_schema` for the config keys each feature accepts.
2. `didit_workflow_create` with the ordered features (published unless `status: "draft"`).
3. `didit_session_create` with `workflow_id` and `vendor_data`; give the user the returned `url`.
4. Later: `didit_session_get_decision`, or `didit_session_explain_decision` to see why it ended Approved, Declined or In Review.

### Edit a large workflow safely

1. `didit_workflow_search` to find it, `didit_workflow_get_graph` (large configs are summarized).
2. `didit_workflow_get_field_definitions` for branchable fields and operators.
3. `didit_workflow_edit_graph` with small operations (`set_next`, `set_node`, `set_branches`, `merge_node_config`): the server applies them to the full graph and saves a draft. A branch always needs an explicit else branch with empty `rules`.
4. `didit_workflow_publish` only after the human approves.

### Work the review queue

1. `didit_session_search` with `status: "In Review"`.
2. `didit_session_get_decision` and `didit_session_list_reviews` for each.
3. After the reviewer decides, `didit_session_update_status` or `didit_session_add_review` with a note.

### Wire a webhook

1. `didit_webhook_create` with a `label`, your public HTTPS `url`, `webhook_version: "v3"` and `subscribed_events` (for example `["status.updated", "data.updated"]`).
2. Copy the signing secret from the console and verify `X-Signature-V2` on your backend (see **didit-verification-management**).
3. `didit_session_webhooks` shows deliveries for a session; `didit_session_webhook_resend` resends one.
