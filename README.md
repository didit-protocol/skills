<p align="center">
  <strong>didit/skills</strong><br>
  <em>Official AI Agent Skills for the Didit Identity Verification Platform</em>
</p>

<p align="center">
  <a href="https://didit.me">didit.me</a> · <a href="https://docs.didit.me">API Docs</a> · <a href="https://business.didit.me">Business Console</a> · <a href="https://agentskills.io">Agent Skills Standard</a>
</p>

---

20 production-ready skills that teach AI agents how to call the Didit API: account registration, identity verification, KYC workflows, AML screening, biometric checks, fraud checks, transaction and event monitoring, cases, fraud networks, SDK integration, billing and user management. Works with **Cursor**, **Claude Code**, **Codex**, **OpenCode**, and any agent that supports the [Agent Skills](https://agentskills.io/) standard.

## What's Inside

| Skill | v | What it does |
|---|---|---|
| [**didit-verification-management**](skills/didit-verification-management/) | 5.1.0 | **The hub**: account setup, API keys, sessions, bulk imports, workflows, questionnaires, users (KYC), businesses (KYB), billing, customization, lists (block/allow), webhook destinations and signatures. |
| [**didit-kyc-onboarding**](skills/didit-kyc-onboarding/) | 1.2.0 | **KYC recipe**: creates a KYC workflow and a session for full identity verification (ID scan, selfie, face match) and reads the decision. |
| [**didit-id-document-verification**](skills/didit-id-document-verification/) | 1.3.0 | Verifies passports, ID cards and driver's licenses (OCR, MRZ, document liveness) and runs digital ID wallet verifications. |
| [**didit-liveness-detection**](skills/didit-liveness-detection/) | 1.3.0 | Detects liveness from a single selfie. Anti-spoofing for print, screen and mask attacks. |
| [**didit-face-match**](skills/didit-face-match/) | 1.5.0 | Compares two faces and returns a similarity score (0-100). Selfie-to-document matching. |
| [**didit-face-search**](skills/didit-face-search/) | 1.3.0 | Searches a face against every enrolled face of the application. 1:N deduplication and blocklist checks. |
| [**didit-biometric-age-estimation**](skills/didit-biometric-age-estimation/) | 1.2.0 | Estimates age from a selfie with a built-in liveness check. Decline thresholds for age-gated services. |
| [**didit-email-verification**](skills/didit-email-verification/) | 1.3.0 | Verifies email addresses with a one-time code and scores email risk (breached, disposable, undeliverable). |
| [**didit-phone-verification**](skills/didit-phone-verification/) | 1.4.0 | Verifies phone numbers by SMS, WhatsApp, Telegram, RCS, Viber, Zalo or voice code and scores phone risk. |
| [**didit-aml-screening**](skills/didit-aml-screening/) | 1.3.0 | Screens people and companies against sanctions, PEP and adverse media lists. Match and risk scores, hit review, ongoing monitoring. |
| [**didit-proof-of-address**](skills/didit-proof-of-address/) | 1.3.0 | Verifies utility bills, bank statements and government letters. Address extraction, geocoding, name and age checks. |
| [**didit-database-validation**](skills/didit-database-validation/) | 1.3.0 | Validates identity data against government and official databases in 60+ countries. |
| [**didit-document-ai**](skills/didit-document-ai/) | 1.0.0 | Extracts structured data from any document (invoices, contracts, certificates) with Document AI. |
| [**didit-transaction-monitoring**](skills/didit-transaction-monitoring/) | 1.1.0 | Transaction monitoring (KYT), rules, crypto wallet screening and the FATF / EU TFR Travel Rule. |
| [**didit-event-monitoring**](skills/didit-event-monitoring/) | 1.0.0 | Sends account and device events (logins, sessions, bonuses, payments) from your backend or the user's device and scores them with rules. |
| [**didit-fraud-check**](skills/didit-fraud-check/) | 1.0.0 | One call that scores a person's email, phone, IP, documents and links to other users, with a recommendation. Also IP risk. |
| [**didit-case-management**](skills/didit-case-management/) | 1.0.0 | Review cases: create, assign, resolve, 4-eyes approval, notes, blueprints, and regulatory reports (SAR, STR and others). |
| [**didit-fraud-networks**](skills/didit-fraud-networks/) | 1.0.0 | Fraud networks: clusters of users and businesses that share devices, IPs, faces, documents, phones, emails or addresses. |
| [**didit-sdk-integration**](skills/didit-sdk-integration/) | 1.1.0 | Three-product integration prompt for Identity verification, Transaction monitoring and end-user Authentication, with release checks; web/native verification, transactions and device events. |
| [**didit-mcp-server**](skills/didit-mcp-server/) | 1.0.0 | Connects AI assistants to Didit through the hosted MCP server (Claude, Cursor, VS Code, Windsurf, Zed). |

> **Naming convention:** Domain-term names that match how users naturally ask: `face-match`, `proof-of-address`, `aml-screening`, `kyc-onboarding`. Lowercase kebab-case, `didit-` namespaced. Every skill that uses an API key includes a **Getting Started** section for account creation and credits.

For any of the seven product combinations, start with the [three-product integration prompt](skills/didit-sdk-integration/SKILL.md#three-product-integration-prompt). It keeps credentials and decisions separate and links the person through server-owned `vendor_data`. Authentication SDKs, JWT/JWKS, automatic auth events and Authentication step-ups are release-dependent. Dedicated Authentication, electronic-signature and biometric-consent skills await merged, documented API contracts; they are not part of the 20-skill catalog yet.

---

## Zero to Verifying (No Browser Needed)

Agents can go from nothing to a live verification link in **5 API calls**:

```
1. POST /programmatic/register/           → register with your email
2. POST /programmatic/verify-email/        → verify the emailed code, get application.api_key
3. POST /v3/workflows/                     → create a workflow (features array)
4. POST /v3/webhook/destinations/          → register a webhook URL and the events it receives
5. POST /v3/session/                       → create a session → get the verification URL
```

---

## Install

### Option 1: npx skills (recommended)

Install all skills at once:

```bash
npx skills add didit-protocol/skills
```

Or install a specific skill:

```bash
npx skills add didit-protocol/skills --skill didit-face-match
```

Works with Cursor, Claude Code, Codex, and OpenCode. The CLI auto-detects your agent and installs to the correct directory.

### Option 2: Git Clone

```bash
git clone https://github.com/didit-protocol/skills.git
```

Copy the skills you need from `skills/` into your agent's skill directory.

### Option 3: Manual

Copy the entire `skills/<name>/` folder, including `SKILL.md` and `scripts/`, into your agent's skill directory. The helpers referenced by a skill must travel with it.

---

## Setup

### Option A: Programmatic Registration (recommended for agents)

No console needed: agents can register themselves.

```bash
# 1. Register
curl -X POST https://apx.didit.me/auth/v2/programmatic/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "you@yourdomain.com", "password": "MyStr0ng!Pass"}'

# 2. Check your email for the 6-character code, then verify
curl -X POST https://apx.didit.me/auth/v2/programmatic/verify-email/ \
  -H "Content-Type: application/json" \
  -d '{"email": "you@yourdomain.com", "code": "A3K9F2"}'
# → the API key is in the response at application.api_key

export DIDIT_API_KEY="the_api_key_from_response"
```

### Option B: Business Console

1. **Get an API key** in the [Didit Business Console](https://business.didit.me) under **Developers > API keys**. Use the primary secret or create a named key with only the access the agent needs.
2. **Set the environment variable:**

```bash
export DIDIT_API_KEY="your_api_key"
```

3. **(Optional)** For webhook verification, keep the destination's signing secret (`secret_shared_key`, returned when you create the destination and by `GET /v3/webhook/destinations/{id}/`):

```bash
export DIDIT_WEBHOOK_SECRET="your_secret"
```

4. **Talk to your agent.** Once skills are installed, just ask naturally:

> "Register a Didit account for me"
> "Create a KYC workflow with ID scan and liveness"
> "Create a verification session for this user"
> "Check my credit balance"
> "Screen John Smith against AML databases"
> "Add the Didit web SDK to my checkout page"

### Option C: MCP server

To let an AI assistant work in your Didit account as you (no API key), connect the hosted MCP server at `https://mcp.didit.me/mcp`. See the [**didit-mcp-server**](skills/didit-mcp-server/) skill.

---

## API Endpoints Covered

| Category | Skill | Endpoints |
|---|---|---|
| Account Setup | `didit-verification-management` | `POST /programmatic/register/`, `POST /programmatic/verify-email/`, `POST /programmatic/resend-otp/`, `POST /programmatic/login/`, `GET /organizations/me/`, `GET`+`POST /organizations/me/{org_id}/applications/`, `GET`+`PATCH /organizations/me/{org_id}/applications/{app_id}/` |
| KYC Flow | `didit-kyc-onboarding` | `POST /v3/workflows/` (features array), `POST /v3/session/`, `GET /v3/session/{id}/decision/`, `PATCH /v3/session/{id}/update-status/` |
| Workflows | `didit-verification-management` | `GET`+`POST /v3/workflows/`, `GET`+`PATCH`+`DELETE /v3/workflows/{id}/` |
| Sessions | `didit-verification-management` | `POST /v3/session/`, `GET /v3/session/{id}/decision/`, `GET /v3/sessions/`, `DELETE /v3/session/{id}/delete/`, `POST /v3/sessions/delete/`, `GET /v3/sessions/delete/{job_id}/`, `PATCH /v3/session/{id}/update-status/`, `PATCH /v3/session/{id}/features/{node_id}/update-status/`, `POST /v3/session/{id}/resubmission-preview/`, `PATCH /v3/session/{id}/update-data/`, `PATCH /v3/session/{id}/update-poa-data/`, `PATCH /v3/session/{id}/update-aml-hit-status/`, `PATCH /v3/session/{id}/bulk-update-aml-hit-status/`, `GET /v3/session/{id}/generate-pdf/`, `POST /v3/session/{id}/share/`, `POST /v3/session/import-shared/`, `GET`+`POST /v3/sessions/{id}/reviews/` |
| Bulk Import | `didit-verification-management` | `POST /v3/session/imports/`, `GET /v3/session/imports/template/`, `GET /v3/session/imports/{id}/`, `GET /v3/session/imports/{id}/errors/` |
| Lists (block/allow/custom) | `didit-verification-management` | `GET`+`POST /v3/lists/`, `GET`+`PATCH`+`DELETE /v3/lists/{id}/`, `GET`+`POST /v3/lists/{id}/entries/`, `POST /v3/lists/{id}/entries/face-upload/`, `DELETE /v3/lists/{id}/entries/{entry}/` |
| Questionnaires | `didit-verification-management` | `GET`+`POST /v3/questionnaires/`, `GET`+`PATCH`+`DELETE /v3/questionnaires/{id}/` |
| Users (KYC) | `didit-verification-management` | `GET /v3/users/`, `POST /v3/users/create/`, `GET`+`PATCH /v3/users/{vendor_data}/`, `PATCH /v3/users/{vendor_data}/update-status/`, `GET /v3/users/{vendor_data}/generate-pdf/`, `POST /v3/users/delete/`, `POST /v3/users/aml-monitoring/`, `GET /v3/aml-monitoring/jobs/{job_id}/`, `/v3/biometric-templates/` |
| Businesses (KYB) | `didit-verification-management` | `GET /v3/businesses/`, `POST /v3/businesses/create/`, `GET`+`PATCH /v3/businesses/{vendor_data}/`, `PATCH /v3/businesses/{vendor_data}/update-status/`, `POST /v3/businesses/delete/`, `POST /v3/businesses/aml-monitoring/`, `POST /v3/kyb/search/`, `POST /v3/kyb/select/`, `POST /v3/kyb/shareholders/`, `POST /v3/kyb/ubo/` |
| Billing | `didit-verification-management` | `GET /v3/billing/balance/`, `POST /v3/billing/top-up/` |
| Customization | `didit-verification-management` | `GET`+`PATCH /v3/customization/` |
| Webhook Destinations | `didit-verification-management` | `GET`+`POST /v3/webhook/destinations/`, `GET`+`PATCH`+`DELETE /v3/webhook/destinations/{id}/` |
| ID Verification | `didit-id-document-verification` | `POST /v3/id-verification/`, `GET /v3/id-verification/wallets/`, `POST /v3/id-verification/wallets/{slug}/`, `GET /v3/id-verification/wallets/verifications/{request_id}/` (+ `poll/`, `cancel/`) |
| Liveness | `didit-liveness-detection` | `POST /v3/passive-liveness/` |
| Face Match | `didit-face-match` | `POST /v3/face-match/` |
| Face Search | `didit-face-search` | `POST /v3/face-search/` |
| Age Estimation | `didit-biometric-age-estimation` | `POST /v3/age-estimation/` |
| Email | `didit-email-verification` | `POST /v3/email/send/`, `POST /v3/email/check/`, `POST /v3/email/risk/` |
| Phone | `didit-phone-verification` | `POST /v3/phone/send/`, `POST /v3/phone/check/`, `POST /v3/phone/risk/` |
| AML | `didit-aml-screening` | `POST /v3/aml/`, `PATCH /v3/session/{id}/update-aml-hit-status/`, `PATCH /v3/session/{id}/bulk-update-aml-hit-status/` |
| Proof of Address | `didit-proof-of-address` | `POST /v3/poa/` |
| Database Validation | `didit-database-validation` | `POST /v3/database-validation/` |
| Document AI | `didit-document-ai` | `POST /v3/document-ai/` |
| Transactions | `didit-transaction-monitoring` | `GET`+`POST /v3/transactions/`, `GET /v3/transactions/{uuid}/`, `POST /v3/transactions/sdk-token/`, `/v3/transactions/rules/` (CRUD, `library/`, `install/`, `backtest/`), `POST /v3/wallet-screening/`, `POST /v3/wallet-screening/pdf/`, `PATCH /v3/transactions/{uuid}/travel-rule/` (+ `ownership/`), `/v3/travel-rule/` (settings, wallet addresses, VASPs, widget, inbound) |
| Events | `didit-event-monitoring` | `GET`+`POST /v3/events/`, `POST /v3/events/batch/`, `GET /v3/events/{uuid}/`, `GET /v3/events/subjects/{vendor_data}/`, `DELETE /v3/events/{uuid}/delete/`, `POST /v3/events/sdk-token/`, `POST /v1/events/`, `POST /v1/events/batch/` |
| Fraud Check | `didit-fraud-check` | `POST /v3/fraud/checks/`, `POST /v3/fraud/checks/plan/`, `GET /v3/fraud/checks/{check_id}/`, `POST /v3/ip/risk/` |
| Cases | `didit-case-management` | `/v3/organization/{org}/application/{app}/cases/` (list, create, update, assign, transfer, escalate, resolve, reopen, approvals, notes, links, checklist, bulk, statistics), `.../cases/blueprints/`, `.../report-templates/`, `.../regulatory-reports/` |
| Fraud Networks | `didit-fraud-networks` | `/v3/organization/{org}/application/{app}/networks/` (list, get, graph, members, signals, timeline, map, report) and `.../{sessions,users,businesses,transactions}/{id}/networks/` |
| SDK clients | `didit-sdk-integration` | `POST /v1/transactions/` (`X-Transaction-Token`), `POST /v1/events/` (`X-Monitoring-Token`) |

**130 endpoint paths** across the platform, most with several methods.

---

## Testing

Offline checks (format, README, scripts, publication filters, code examples, webhook signatures). Python and Git are required; no key is needed:

```bash
python3 tests/test_skill_structure.py
```

Live checks against the real API (a sandbox application key is recommended; some calls are billed on live applications):

```bash
export DIDIT_API_KEY="your_key"
export DIDIT_WORKFLOW_ID="your_workflow_id"     # optional
export DIDIT_ORG_ID="your_organization_id"      # optional, enables case and network checks
export DIDIT_APP_ID="your_application_id"       # optional, enables case and network checks
python3 tests/test_all_skills.py
```

Each live check passes only when the endpoint answers with the documented status code and JSON fields.

---

## Repo Structure

```
skills/                              ← 20 skills (1 hub + 1 KYC recipe + 18 product skills)
├── didit-verification-management/    SKILL.md + scripts/{setup_account,manage_workflows,create_session}.py
├── didit-kyc-onboarding/             SKILL.md + scripts/run_kyc.py
├── didit-id-document-verification/   SKILL.md + scripts/verify_id.py
├── didit-liveness-detection/         SKILL.md + scripts/check_liveness.py
├── didit-face-match/                 SKILL.md + scripts/match_faces.py
├── didit-face-search/                SKILL.md + scripts/search_faces.py
├── didit-biometric-age-estimation/   SKILL.md + scripts/estimate_age.py
├── didit-email-verification/         SKILL.md + scripts/verify_email.py
├── didit-phone-verification/         SKILL.md + scripts/verify_phone.py
├── didit-aml-screening/              SKILL.md + scripts/screen_aml.py
├── didit-proof-of-address/           SKILL.md + scripts/verify_address.py
├── didit-database-validation/        SKILL.md + scripts/validate_database.py
├── didit-document-ai/                SKILL.md + scripts/extract_document.py
├── didit-transaction-monitoring/     SKILL.md + scripts/submit_transaction.py
├── didit-event-monitoring/           SKILL.md + scripts/send_event.py
├── didit-fraud-check/                SKILL.md + scripts/run_fraud_check.py
├── didit-case-management/            SKILL.md + scripts/manage_cases.py
├── didit-fraud-networks/             SKILL.md + scripts/list_networks.py
├── didit-sdk-integration/            SKILL.md + scripts/mint_sdk_tokens.py
└── didit-mcp-server/                 SKILL.md
tests/test_skill_structure.py        ← offline checks
tests/test_all_skills.py             ← live endpoint checks
```

Each `SKILL.md` follows the **three-tier information architecture**:

1. **Metadata (always loaded):** Domain-term name + trigger-based description in YAML frontmatter (~100 tokens)
2. **Skill body (loaded on invocation):** Full API documentation, examples, and workflows
3. **Scripts (lazy loaded):** Python CLI utilities referenced by the skill body

```yaml
---
name: didit-verification-management
description: >
  Full Didit identity verification platform management...
version: 5.1.0
metadata:
  openclaw:
    requires:
      env: []
    primaryEnv: DIDIT_API_KEY
    emoji: "🛡️"
    homepage: https://docs.didit.me
---
```

---

## Contributing

1. Fork the repo
2. Update or add a skill in `skills/`
3. Run `python3 tests/test_skill_structure.py`, and `python3 tests/test_all_skills.py` with a sandbox key
4. Open a PR

---

## ClawHub publication handoff

Publication is a human step. The seven SK1 additions below still need ClawHub publication; this repository change prepares their bundles and does not publish them.

| Skill | Prepared version | Required helper |
|---|---|---|
| `didit-case-management` | 1.0.0 | `scripts/manage_cases.py` |
| `didit-document-ai` | 1.0.0 | `scripts/extract_document.py` |
| `didit-event-monitoring` | 1.0.0 | `scripts/send_event.py` |
| `didit-fraud-check` | 1.0.0 | `scripts/run_fraud_check.py` |
| `didit-fraud-networks` | 1.0.0 | `scripts/list_networks.py` |
| `didit-mcp-server` | 1.0.0 | None |
| `didit-sdk-integration` | 1.1.0 | `scripts/mint_sdk_tokens.py` |

Before publishing, check the registry's existing version for each skill and choose an unused version if necessary. Previously published skills affected by the script exclusion also need corrected bundles.

Stage each complete skill folder in a clean temporary directory. Include the repository `.gitignore` and `.clawhubignore` at that folder's root, appending any skill-local policies after the repository policies. ClawHub reads these files from the publication folder; it does not inherit the repository's filters when publishing a nested skill directly. Keep `scripts/` included and exclude credentials, caches and development files. See the [ClawHub skill format](https://github.com/openclaw/clawhub/blob/main/docs/skill-format.md).

Run the offline checks above, inspect the staged file list and confirm every referenced helper is present. Publish each staged skill folder individually, using its name and reviewed version, only when the human publisher is ready. After publication, install into an empty directory and verify `SKILL.md`, the helper files and their `--help` commands before announcing availability.

---

## License

MIT, see [LICENSE](LICENSE).
