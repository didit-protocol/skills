<p align="center">
  <strong>didit-agent-skills</strong><br>
  <em>Official AI Agent Skills for the Didit Identity Verification Platform</em>
</p>

<p align="center">
  <a href="https://didit.me">didit.me</a> · <a href="https://docs.didit.me">API Docs</a> · <a href="https://business.didit.me">Business Console</a> · <a href="https://clawhub.ai">ClawHub</a>
</p>

---

12 production-ready skills that teach AI agents how to call every Didit API — from account registration to identity verification, KYC workflows, AML screening, biometric checks, billing, and user management. Drop them into **Cursor**, install from **ClawHub**, or use with any `SKILL.md`-compatible agent.

## What's Inside

| Skill | v | What it does |
|---|---|---|
| [**didit-verification-management**](skills/didit-verification-management/) | 4.1.0 | **The hub** — account setup, sessions, workflows, questionnaires, users, billing, blocklist, webhook config. 45+ endpoints. |
| [**didit-kyc-onboarding**](skills/didit-kyc-onboarding/) | 1.0.0 | **KYC recipe** — creates a KYC workflow + session for full human identity verification (ID scan + selfie + face match). |
| [**didit-id-document-verification**](skills/didit-id-document-verification/) | 1.2.0 | Verifies passports, ID cards, driver's licenses. OCR, MRZ, NFC. 4000+ document types, 220+ countries. |
| [**didit-liveness-detection**](skills/didit-liveness-detection/) | 1.2.0 | Detects liveness from a single selfie. 99.9% accuracy. Anti-spoofing for print, screen, and mask attacks. |
| [**didit-face-match**](skills/didit-face-match/) | 1.2.0 | Compares two faces. Returns similarity score 0–100. Selfie-to-document matching. |
| [**didit-face-search**](skills/didit-face-search/) | 1.0.0 | Searches for matching faces across all verified sessions. 1:N deduplication and blocklist checks. |
| [**didit-biometric-age-estimation**](skills/didit-biometric-age-estimation/) | 1.0.0 | Estimates age from a selfie. Built-in liveness check. Configurable thresholds for age-gated services. |
| [**didit-email-verification**](skills/didit-email-verification/) | 1.2.0 | Verifies email addresses via OTP. Detects breached, disposable, and undeliverable addresses. |
| [**didit-phone-verification**](skills/didit-phone-verification/) | 1.2.0 | Verifies phone numbers via SMS, WhatsApp, or Telegram OTP. Detects VoIP and disposable numbers. |
| [**didit-aml-screening**](skills/didit-aml-screening/) | 1.0.0 | Screens against 1300+ sanctions, PEP, and adverse media databases. Dual-score risk system. |
| [**didit-proof-of-address**](skills/didit-proof-of-address/) | 1.0.0 | Verifies utility bills, bank statements, government documents. OCR extraction with geocoding. |
| [**didit-database-validation**](skills/didit-database-validation/) | 1.0.0 | Validates identity against government databases in 18 countries. |

> **Naming convention:** Domain-term names that match how users naturally ask — `face-match`, `proof-of-address`, `aml-screening`, `kyc-onboarding`. Lowercase kebab-case, `didit-` namespaced. Every standalone skill includes a **Getting Started** section for account creation + credits.

---

## Zero to Verifying (No Browser Needed)

Agents can go from nothing to a live verification link in **5 API calls**:

```
1. POST /programmatic/register/      → register with any email
2. POST /programmatic/verify-email/   → verify OTP, get api_key
3. POST /v3/workflows/               → create verification workflow
4. PATCH /v3/webhook/                 → set webhook URL (no console needed)
5. POST /v3/session/                  → create session → get verification URL
```

---

## Install

### Option 1: ClawHub

```bash
npx clawhub@latest install didit-verification-management
npx clawhub@latest install didit-id-document-verification
# ... etc for each skill you need
```

### Option 2: Git Clone

```bash
git clone https://github.com/didit-protocol/didit-agent-skills.git
```

Copy the skills you need from `skills/` into your agent's skill directory.

### Option 3: Manual

Copy any `skills/<name>/SKILL.md` into your agent's skill directory. Each skill is self-contained.

---

## Setup

### Option A: Programmatic Registration (recommended for agents)

No console needed — agents can self-register:

```bash
# 1. Register (any email works)
curl -X POST https://apx.didit.me/auth/v2/programmatic/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "dev@gmail.com", "password": "MyStr0ng!Pass"}'

# 2. Check email for 6-char code, then verify
curl -X POST https://apx.didit.me/auth/v2/programmatic/verify-email/ \
  -H "Content-Type: application/json" \
  -d '{"email": "dev@gmail.com", "code": "A3K9F2"}'
# → response includes api_key

export DIDIT_API_KEY="the_api_key_from_response"
```

### Option B: Business Console

1. **Get an API key** from [Didit Business Console](https://business.didit.me) → API & Webhooks
2. **Set the environment variable:**

```bash
export DIDIT_API_KEY="your_api_key"
```

3. **(Optional)** For webhook verification:

```bash
export DIDIT_WEBHOOK_SECRET="your_secret"      # from Console → API & Webhooks
```

4. **Talk to your agent.** Once skills are installed, just ask naturally:

> "Register a Didit account for me"
> "Create a KYC workflow with ID scan and liveness"
> "Create a verification session for this user"
> "Check my credit balance"
> "Screen John Smith against AML databases"

---

## API Endpoints Covered

| Category | Skill | Endpoints |
|---|---|---|
| Account Setup | `didit-verification-management` | `POST /programmatic/register/`, `POST /programmatic/verify-email/`, `POST /programmatic/login/`, `GET /organizations/me/`, `GET /organizations/me/{org_id}/applications/{app_id}/` |
| KYC Flow | `didit-kyc-onboarding` | `POST /v3/workflows/` (KYC type), `POST /v3/session/`, `GET /v3/session/{id}/decision/`, `PATCH /v3/session/{id}/update-status/` |
| Workflows | `didit-verification-management` | `GET /v3/workflows/`, `POST /v3/workflows/`, `GET /v3/workflows/{id}/`, `PATCH /v3/workflows/{id}/`, `DELETE /v3/workflows/{id}/` |
| Sessions & Blocklist | `didit-verification-management` | `POST /v3/session/`, `GET /v3/session/{id}/decision/`, `GET /v3/sessions/`, `DELETE /v3/session/{id}/delete/`, `POST /v3/sessions/delete/`, `PATCH /v3/session/{id}/update-status/`, `GET /v3/session/{id}/generate-pdf`, `POST /v3/session/{id}/share/`, `POST /v3/session/import-shared/`, `GET /v3/sessions/{id}/reviews/`, `POST /v3/sessions/{id}/reviews/`, `POST /v3/blocklist/add/`, `POST /v3/blocklist/remove/`, `GET /v3/blocklist/` |
| Questionnaires | `didit-verification-management` | `GET /v3/questionnaires/`, `POST /v3/questionnaires/`, `GET /v3/questionnaires/{id}/`, `PATCH /v3/questionnaires/{id}/`, `DELETE /v3/questionnaires/{id}/` |
| Users | `didit-verification-management` | `GET /v3/users/`, `GET /v3/users/{vendor_data}/`, `PATCH /v3/users/{vendor_data}/`, `POST /v3/users/delete/` |
| Billing | `didit-verification-management` | `GET /v3/billing/balance/`, `POST /v3/billing/top-up/` |
| Webhook Config | `didit-verification-management` | `GET /v3/webhook/`, `PATCH /v3/webhook/` |
| ID Verification | `didit-id-document-verification` | `POST /v3/id-verification/` |
| Liveness | `didit-liveness-detection` | `POST /v3/passive-liveness/` |
| Face Match | `didit-face-match` | `POST /v3/face-match/` |
| Face Search | `didit-face-search` | `POST /v3/face-search/` |
| Age Estimation | `didit-biometric-age-estimation` | `POST /v3/age-estimation/` |
| Email | `didit-email-verification` | `POST /v3/email/send/`, `POST /v3/email/check/` |
| Phone | `didit-phone-verification` | `POST /v3/phone/send/`, `POST /v3/phone/check/` |
| AML | `didit-aml-screening` | `POST /v3/aml/` |
| Proof of Address | `didit-proof-of-address` | `POST /v3/poa/` |
| Database Validation | `didit-database-validation` | `POST /v3/database-validation/` |

**50+ endpoints total** (including webhook configuration), all tested.

---

## Testing

```bash
export DIDIT_API_KEY="your_key"
export DIDIT_WORKFLOW_ID="your_workflow_id"
python3 tests/test_all_skills.py
```

```
RESULTS: 48/48 passed, 0 failed
```

---

## Repo Structure

```
skills/                              ← 12 skills (1 hub + 1 KYC recipe + 10 standalone)
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
└── didit-database-validation/        SKILL.md + scripts/validate_database.py
tests/test_all_skills.py            ← 48+ endpoint test suite (grows to 51 when webhook API deploys)
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
version: 4.1.0
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
3. Run `python3 tests/test_all_skills.py` to verify
4. Open a PR

---

## License

MIT — see [LICENSE](LICENSE).
