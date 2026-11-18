---
name: didit-mcp-server
description: >
  Connect an AI assistant to the Didit identity platform through the Didit MCP server
  (Model Context Protocol). Use when the user wants to install or configure the Didit MCP
  server in Claude Code, Claude Desktop or claude.ai, Cursor, VS Code, Windsurf, Zed or any
  MCP client; sign in with a Didit console account (OAuth 2.1); run the server headless over
  stdio with a user access token or self-host it; or have an agent act in the Didit Business
  Console as the signed-in user: build workflows, create and review verification sessions,
  run standalone checks, manage users, transactions and rules, lists, cases, webhooks,
  reports and billing. Covers scopes, roles, confirmations and file inputs.
version: 1.0.0
metadata:
  openclaw:
    requires:
      env: []
    primaryEnv: DIDIT_ACCESS_TOKEN
    emoji: "🔌"
    homepage: https://docs.didit.me
---

# Didit MCP Server

## Overview

The Didit MCP server lets an MCP client call the Didit platform through tools. It acts as the **signed-in Didit user**, across every organization and application that user belongs to, with that user's console role permissions. It is read-and-write: agents can create sessions, change workflows, update statuses and delete data.

**Key facts:**
- Hosted endpoint: `https://mcp.didit.me/mcp` (Streamable HTTP, stateless, `POST` only; `GET` and `DELETE` answer `405`). Health check: `GET https://mcp.didit.me/healthz` returns `{"status": "ok", "service": "didit-mcp-server", "version": "..."}`.
- Sign-in is OAuth 2.1 with PKCE against your Didit Business Console account (the docs call it **Log in with Didit**). There is **no API-key mode**: the server always calls Didit as the signed-in user, never with an application API key.
- Tools return the verbatim JSON of the underlying Didit endpoints.
- Open source (MIT): https://github.com/didit-protocol/mcp, published on npm as `@didit-protocol/mcp-server` (binary `didit-mcp-server`).

**When to use the REST skills instead:** a backend integration that runs with an application API key (creating sessions for your users, receiving webhooks, submitting transactions) does not use this server; see **didit-verification-management**, **didit-sdk-integration** and the standalone API skills. The MCP server is for an AI assistant working in the console on a person's behalf.

**Pricing:** The MCP server has no list price of its own. Tools that run billable operations (for example `didit_session_create` on a live application and the `didit_verify_*` standalone checks) use your credits like the same API calls. These are the list prices until 1 November 2026, when Didit pricing changes and the 500 free checks a month become $10 of free credit a month. Check [didit.me/pricing](https://didit.me/pricing) for current prices.

**Docs:** https://docs.didit.me/integration/mcp/overview · Installation: https://docs.didit.me/integration/mcp/installation · Authentication: https://docs.didit.me/integration/mcp/authentication · Tools reference: https://docs.didit.me/integration/mcp/tools · Advanced: https://docs.didit.me/integration/mcp/advanced

---

## Authentication

The hosted server is an OAuth 2.1 resource server; the Didit Business Console (`https://business.didit.me`) is the authorization server. Your client runs the whole flow:

1. `POST /mcp` without a token answers `401` with `WWW-Authenticate: Bearer ... resource_metadata="https://mcp.didit.me/.well-known/oauth-protected-resource/mcp"`.
2. The client reads that metadata, then `https://business.didit.me/.well-known/oauth-authorization-server`, and registers itself with dynamic client registration if it has no client id.
3. It opens the browser for the authorization code flow with an S256 PKCE challenge; the user signs in (or registers) and approves the scopes. Clients are public: no client secret.
4. It sends `Authorization: Bearer <access_token>` on every `POST /mcp`. Access tokens are short-lived and refreshed automatically with the refresh token.

| Scope | Grants |
|---|---|
| `didit:verification` | Run and review verifications: sessions, businesses, cases, transactions, blocklist, analytics |
| `didit:management` | Manage the workspace: organization, members, subscription, users, applications, workflows, customization, questionnaires, lists, webhooks, integrations, API keys, audit logs, roles, analytics |

- Effective access is the **intersection** of the approved scopes and the user's console role in each organization. A `READER` can list and read; an `OWNER` or `ADMIN` can write and delete.
- `didit_session_create` needs the `didit:verification` scope **and** a role with `create:sessions` or `write:sessions` (the Developer role has `create:sessions`).
- Disconnect an app in the console under **Settings > Authentication > Connected apps**: its access and refresh tokens stop working at once. A client can also revoke its own token (RFC 7009):

```bash
curl -X POST https://business.didit.me/api/auth/oauth-revoke \
  -H "Content-Type: application/json" \
  -d '{"token": "<refresh-or-access-token>", "token_type_hint": "refresh_token", "client_id": "<your-client-id>"}'
```

`200` is returned whether or not the token was still live; `503` means it was not revoked (retry).

## Getting Started (No Account Yet?)

No key or install is needed for the hosted server. Add `https://mcp.didit.me/mcp` to your client (next section); on first use the browser opens **Log in with Didit**, where you can also create a Didit account. For a headless run you need a user access token (see Headless and self-hosting).

---

## Install in a Client

| Client | Setup |
|---|---|
| Claude Code | `claude mcp add --transport http didit https://mcp.didit.me/mcp`, then run `/mcp` in Claude Code to sign in |
| claude.ai and Claude Desktop | **Settings > Connectors > Add custom connector**, name `Didit`, URL `https://mcp.didit.me/mcp`, then **Connect**. Pre-filled link: `https://claude.ai/customize/connectors?modal=add-custom-connector&connectorName=Didit&connectorUrl=https://mcp.didit.me/mcp` |
| Cursor | `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project), see below |
| VS Code (agent mode) | `.vscode/mcp.json`, see below, or **MCP: Add Server** > **HTTP**. Use the full `/mcp` URL, not the bare origin |
| Windsurf | `~/.codeium/windsurf/mcp_config.json` with the `mcp-remote` bridge, see below |
| Zed | `settings.json` `context_servers` with the `mcp-remote` bridge, see below |
| Any other client | Streamable HTTP + OAuth 2.1 directly against `https://mcp.didit.me/mcp`; a stdio-only client uses `npx -y mcp-remote@latest https://mcp.didit.me/mcp` |

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
{"mcpServers": {"didit": {"command": "npx", "args": ["-y", "mcp-remote@latest", "https://mcp.didit.me/mcp"]}}}
```

Zed:

```json
{"context_servers": {"didit": {"source": "custom", "command": "npx", "args": ["-y", "mcp-remote@latest", "https://mcp.didit.me/mcp"]}}}
```

Any MCP client that supports remote HTTP servers, or stdio through `mcp-remote`, works the same way. Keep the client's "review tool calls before running" setting on.

## Headless and Self-Hosting

**Stdio with a user token** (local agents and CI that cannot run a browser sign-in):

```bash
DIDIT_ACCESS_TOKEN=<user-access-token> npx -y @didit-protocol/mcp-server

# Register it in Claude Code
claude mcp add didit-local -e DIDIT_ACCESS_TOKEN=<user-access-token> -- npx -y @didit-protocol/mcp-server
```

```json
{"mcpServers": {"didit-local": {"command": "npx", "args": ["-y", "@didit-protocol/mcp-server"], "env": {"DIDIT_ACCESS_TOKEN": "<user-access-token>"}}}}
```

- `DIDIT_ACCESS_TOKEN` is a Didit **user** access token, not an application API key. Treat it as a secret: keep it in the client's env config, never in a prompt or a repository.
- Without a token, a stdio server can sign in with `didit_account_login` (then `didit_account_verify_2fa` when the account has two-factor authentication).
- `MCP_DEFAULT_ORG` and `MCP_DEFAULT_APP` pin the organization and application for single-tenant setups.

**Self-hosted HTTP server:** clone https://github.com/didit-protocol/mcp, `npm install && npm run build`, then `node dist/http.js` (or `docker build -t didit-mcp .` and `docker run -p 3000:3000 --env-file .env didit-mcp`). It is an OAuth resource server only and still acts as a Didit user.

| Variable | Mode | Purpose |
|---|---|---|
| `DIDIT_ACCESS_TOKEN` | stdio | User Bearer token for headless runs |
| `DIDIT_API_BASE_URL` | both | Verification API base (default `https://verification.didit.me/v3`) |
| `DIDIT_AUTH_BASE_URL` | both | Auth API base (default `https://apx.didit.me/auth/v2`) |
| `MCP_PORT` | HTTP | Listen port (default `3000`) |
| `MCP_RESOURCE_URI` | HTTP | Full public URL of the transport, path included (`https://mcp.example.com/mcp`) |
| `MCP_AUTHORIZATION_SERVER_ORIGIN` | HTTP | Authorization server (default `https://business.didit.me`) |
| `MCP_TOKEN_VERIFY_MODE` | HTTP | `introspection` (default, opaque tokens) or `jwks` |
| `MCP_OAUTH_INTROSPECT_URL`, `MCP_OAUTH_CLIENT_ID`, `MCP_OAUTH_CLIENT_SECRET` | HTTP | RFC 7662 introspection endpoint and its credentials (from a secret manager) |
| `MCP_SCOPES_SUPPORTED` | HTTP | Scopes advertised (default `didit:management didit:verification`) |
| `MCP_DEFAULT_ORG`, `MCP_DEFAULT_APP` | both | Default organization and application |
| `DIDIT_AUTH_ISSUER`, `DIDIT_OIDC_DISCOVERY_URL`, `DIDIT_OIDC_AUTHORIZE_URL`, `DIDIT_OIDC_TOKEN_URL`, `DIDIT_OIDC_REGISTRATION_URL`, `DIDIT_JWKS_URL` | HTTP | Authorization server overrides; `DIDIT_JWKS_URL` for `jwks` mode |
| `MCP_PERMISSION_MODE` | both | Per-tool role pre-check: `shadow` (default: list everything, the backend answers `403`), `enforce` (hide tools the role cannot run; calls return `missing_scope`), `off` |
| `MCP_JSON_BODY_LIMIT` | HTTP | JSON-RPC body limit (default `25mb`) |

---

## Tools

Tool names start with `didit_`. Annotations mark each tool read-only, write or destructive (`destructiveHint`), and clients ask before running destructive ones.

| Group | Main tools |
|---|---|
| Discovery and cross-app | `didit_context_get` (call first: every organization and application, with each app's `mode` `live` or `sandbox`), `didit_session_search`, `didit_transaction_search`, `didit_case_search`, `didit_vendor_user_search`, `didit_vendor_business_search`, `didit_workflow_search`, `didit_analytics` |
| Sessions (KYC and KYB) | `didit_session_create` (returns `session_id`, `url`, `session_token`), `_list`, `_get_decision`, `_explain_decision`, `_update_status`, `_update_data`, `_update_poa_data`, `_add_review`, `_list_reviews`, `_generate_pdf`, `_share`, `_import_shared`, `_create_import`, `_get_import`, `_get_import_errors`, `_get_import_template`, `_webhooks`, `_webhook_resend`, `_delete`, `_batch_delete` |
| Workflows | `didit_workflow_list`, `_get`, `_create`, `_update`, `_delete` (drafts), `_get_graph`, `_edit_graph`, `_set_graph`, `_validate_graph`, `_build_graph`, `_get_branch_fields`, `_get_field_definitions`, `_get_feature_config_schema`, `_get_id_verification_methods_catalog`, `_get_kyb_registry_catalog`, `_create_draft`, `_publish` |
| Questionnaires | `didit_questionnaire_list`, `_get`, `_create`, `_append_choices`, `_update`, `_delete` |
| Standalone verification APIs | `didit_verify_id`, `_poa`, `_database`, `_kyb_search`, `_kyb_select`, `_passive_liveness`, `_face_match`, `_face_search`, `_age`, `_aml`, `_email_send`, `_email_check`, `_phone_send`, `_phone_check` |
| Vendor users and businesses | `didit_vendor_user_list`, `_get`, `_create`, `_update`, `_update_status`, `_delete`, and the same set for `didit_vendor_business_*` |
| Transaction monitoring | `didit_transaction_list`, `_get`, `_create`, `_screen_wallet`, `didit_transaction_rule_list`, `_get`, `_create`, `_update`, `_delete`, `_backtest`, `_library_list`, `_install`, `_uninstall` |
| Cases | `didit_case_list`, `_get`, `_create`, `_statistics`, `_manage` |
| Lists, blocklist and allowlist | `didit_lists_list`, `_get`, `_create`, `_update`, `_delete`, `_entries_list`, `_entry_create`, `_entry_upload_face`, `_entry_delete`, `didit_blocklist_get`, `_add`, `_remove`, `didit_allowlist_add` |
| Webhooks | `didit_webhook_list`, `_get`, `_create`, `_update`, `_delete` |
| Reports, audit log and alerts | `didit_report_list`, `_get`, `_get_download_url`, `_export`, `didit_audit_log_list`, `didit_alert_list`, `didit_alert_configure` |
| Organization, members, billing and branding | `didit_org_list`, `_list_applications`, `_get_application`, `_get_balance`, `_list_members`, `_invite_member`, `_update_member`, `_remove_member`, `_list_roles`, `_list_api_keys` (values redacted), `didit_branding_get`, `didit_branding_update` |
| Local stdio only | `didit_org_top_up` (Stripe checkout link), `didit_org_reveal_application_api_key` (raw key), `didit_account_register`, `didit_account_verify_email`, `didit_account_resend_otp`, `didit_account_login`, `didit_account_verify_2fa` |

The public tools reference also lists Compliance assistant, Fraud networks, Travel Rule and Marketplace groups on the hosted server: see https://docs.didit.me/integration/mcp/tools for the full per-tool table with the scope and role permission of each tool.

### Scope resolution

Every tool accepts optional `organization_id` and `application_id`. With one organization and one application they are filled in for you. With several, the `*_search` tools and `didit_analytics` aggregate over all of them (each row tagged with its organization and application), and the per-app `*_list` tools span every app when you pass no scope. Pass both ids to narrow to one app. Read the environment from `didit_context_get` (`mode`), never from an app's name; on a sandbox application `didit_session_create` accepts `sandbox_scenario` (`approve`, `decline_*`, `review_*`) for unbilled test runs.

### Confirmations

These tools refuse to run without `confirm: true` (a real boolean) in their arguments: `didit_session_delete`, `didit_session_batch_delete`, `didit_vendor_user_delete` and `didit_vendor_business_delete` with `delete_all: true`, `didit_case_manage` when filing a SAR, and on stdio `didit_org_reveal_application_api_key` and `didit_org_top_up`. **An agent must ask the human and get explicit approval for that exact action before passing `confirm: true`.** Deletion is permanent.

### File inputs

Tools that take files (ID, proof of address, liveness, face match, face search, age, list face entries, branding) accept each file as either `<name>_path` or `<name>_base64`, exactly one:
- `*_path`: absolute path on the machine running the server; only works with a local stdio server.
- `*_base64`: raw base64 or a `data:` URL; use this with the hosted server.
- Maximum 15 MB; PNG, JPG/JPEG, WebP, GIF, BMP, ICO or PDF, checked by file content, not extension.

### Session PDF reports

`didit_session_generate_pdf` returns `download_url`, `expires_at` and `expires_in` (300 seconds). Fetch the URL without an `Authorization` header to get the PDF. Treat the link as a secret.

### Responses

Synchronous tools (workflows, billing, `didit_verify_*`, lists) return the final result. `didit_session_create` returns a `url` the end user must complete; the decision arrives later by webhook or `didit_session_get_decision`. Decision keys are plural arrays (`id_verifications[]`, `liveness_checks[]`, `face_matches[]`, `aml_screenings[]`, ...), one entry per workflow node. API keys and webhook signing secrets are redacted in tool output: copy the signing secret from **Webhooks** in the console.

---

## Error Responses

| Error | Meaning | Action |
|---|---|---|
| `401` from `/mcp` (`WWW-Authenticate: Bearer error="invalid_token"`) | Token missing, expired or revoked | Let the client refresh, or re-run **Log in with Didit** |
| `403` from a tool | The user's role in that organization lacks the permission | Ask an owner or admin for the permission; an API key does not help |
| `missing_scope` | The role lacks the named permission (`enforce` mode), or the connection was approved without the scope the tool needs | Change the role, or reconnect and approve both scopes |
| `405` | `GET` or `DELETE` on `/mcp` | Use `POST` |
| `unsafe_operation` / `bad_request` on a delete | `confirm: true` missing or not a boolean | Ask the human, then retry with `confirm: true` |
| File rejected | `*_path` sent to the hosted server, both forms sent, over 15 MB, or not an allowed file type | Send one `*_base64` value of an allowed type |
| `organization_id is required` or empty results | Several apps and no scope | Use a `*_search` tool or `didit_context_get`, then pass `organization_id` and `application_id` |
| Every tool fails | The app was disconnected in **Connected apps** | Approve the connection again |
| `invalid_redirect_uri` at sign-in | A remote client callback URL Didit has not reviewed | That client must be registered by an operator first |

---

## Common Workflows

### Connect and check access

1. Add the server (Install in a Client) and sign in.
2. `didit_context_get` lists organizations and applications with their `mode`.
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
