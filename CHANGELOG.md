# Changelog

All notable changes to the Didit Agent Skills collection will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [5.2.0] - 2026-11-18

Every skill re-checked against the Didit MCP server v5.1.67 source and the pricing pages as they stood on
2026-11-18. Skill versions: aml-screening 1.4.0, biometric-age-estimation 1.3.0, case-management 1.1.0,
database-validation 1.4.0, document-ai 1.1.0, email-verification 1.4.0, event-monitoring 1.1.0,
face-match 1.6.0, face-search 1.4.0, fraud-check 1.1.0, fraud-networks 1.1.0, id-document-verification 1.4.0,
kyc-onboarding 1.3.0, liveness-detection 1.4.0, mcp-server 1.1.0, phone-verification 1.5.0,
proof-of-address 1.4.0, sdk-integration 1.2.0 (after the 1.1.0 change below), transaction-monitoring 1.2.0, verification-management 5.2.0.

### Changed
- **didit-mcp-server (1.0.0 to 1.1.0):** matches server v5.1.67. Documents API key connections (one
  application, the key's own access, person-only tools refused) next to OAuth, which stays the default;
  the three advertised scopes, with `didit:staff` for Didit staff only; that a successful tool result is
  compact JSON plus `structuredContent` (arrays and scalars wrapped as `{value}`), with secrets redacted except
  the one-time secret from `didit_org_create_api_key` and large payloads summarized, while errors are sanitized
  text with no `structuredContent`; that revoking stops refresh while an accepted access token can reach the
  server for up to 60 seconds (separate from a rotated API key's grace period); device-code `login` and
  `logout` with stored, refreshed credentials (logout deletes the local copy even when revocation fails); what
  `GET` and `DELETE` on `/mcp` and the bare origin return, on the hosted server and on an open-source build
  without the connect page; which confirmations the server enforces per operation; tool
  coverage (167 tools for a signed-in person, 9 more on a local server, `?toolsets=core` with 29 tools,
  `read_only=true`, the discovery tools, `didit_docs_search`); the `organization_id`/`application_id` rules
  (tools that require ids, the six per-app lists with a cross-app fallback); the self-hosting and stdio
  triggers in the description; OpenAI Codex and the per-client docs pages; the Claude Code plugin install; launcher versions pinned;
  and which top-up and key tools are hosted or local only.
- **All skills, pricing (checked against https://docs.didit.me/getting-started/pricing and the pages it links
  on 2026-11-18):** removed the sentence about list prices until 1 November 2026. Each skill has one dated
  Pricing note ("as of 2026-11-18" with a link); prices and billing statements elsewhere in a skill point to
  that note, to a dated table heading, or to the skill that owns the price, so each price is stated in one
  place. The figures that changed are listed on the pricing page; this entry does not repeat them. Statements
  about 500 free checks a month and "no free tier" were replaced by the current credit rule, which lives in the
  didit-verification-management Pricing note. Prices were removed from the Document AI and Transaction
  Monitoring descriptions.
- **didit-database-validation:** coverage is 45 countries plus a Global group, 122 live services, with 60+
  countries tracked and activated on demand; the highest service price is $8.00, and the Argentina, Spain,
  Guatemala, Panama, Peru, Kenya and South Africa service prices match the current pricing table.
- **All REST skills:** each description starts with the integration boundary ("Use when writing backend or
  API-key integration code for ..."), and each body points people working inside a connected Didit account
  to the Didit plugin or MCP server tools instead of REST calls.
- **didit-sdk-integration (1.0.0 to 1.1.0):** adds a three-product prompt for all seven combinations of
  Identity verification, Transaction monitoring and end-user Authentication. Uses one server-owned
  `vendor_data`, separate credentials and backend-confirmed decisions; keeps unavailable Authentication,
  signals, issuer, automatic-event and step-up capabilities gated. An API key is required only for the
  selected verification/monitoring paths, not Authentication-only guidance.
- README lists the seven SK1 additions awaiting human ClawHub publication and the per-skill staging
  procedure. No ClawHub publication is performed by this change.
- Dedicated Authentication, electronic-signature and biometric-consent skills remain deferred until
  their APIs are merged and documented. The integration guidance does not certify runtime readiness.

### Security
- **didit-verification-management:** `setup_account.py` prints a fixed summary: no response body, server
  message or exception text. Credentials in it (API key, access and refresh tokens, and the temporary token of a
  second-factor challenge) are masked to the first 4 and last 4 characters. A second-factor challenge or an
  SSO-only organization is reported as such and exits 1. HTTP, transport and decoding failures report the
  status, an error code from a known list (anything else prints `unknown_error`) and fixed text only. UUIDs are
  echoed only in canonical 8-4-4-4-12 hex form and an email only when it equals the one supplied; success is
  announced only when the expected fields are present, otherwise it exits 1 with "unexpected response".
  `--write-env <path>` refuses symlinks and non-regular files and any credential with a character outside
  `[A-Za-z0-9._~+/=-]`, reads the old file without following links, writes unquoted `KEY=value` lines through a
  0600 temporary file and
  `os.replace`, and is checked before the single-use code is spent. `--show-secrets` prints full credentials
  only when spelled out in full (abbreviations are rejected on every parser).

### Fixed
- ClawHub bundles keep `scripts/`, so the helpers referenced by skills are included. Credential,
  cache and development exclusions remain in place. Manual installation now copies complete folders.
- **didit-verification-management:** `setup_account.py` reads the password from `DIDIT_PASSWORD` or a
  no-echo prompt instead of a command-line argument, which exposed it in the process list, shell history
  and agent logs (CWE-214), and the verification code from `DIDIT_VERIFICATION_CODE` or a no-echo prompt. A
  positional password or code still works for compatibility but prints a warning.

### Tests
- Offline tests feed synthetic responses to `setup_account.py` and scan stdout and stderr separately: masked
  verify and login output, abbreviated `--show` rejected, non-JSON and JSON error bodies and transport
  exception text not echoed, a second-factor `temp_token` masked, SSO reported, a symlink `--write-env`
  destination refused before the code is spent, the 0600 file written and parsed back with a minimal dotenv
  reader to the same values, values with unsupported characters rejected, credentials returned in an error
  code or a UUID field not echoed, and an empty success response refused.
- Offline publication-filter regression verifies that every skill's Python helpers survive the ignore
  policies and that credential, cache and development files stay excluded.

## [5.1.0] - 2026-10-12

Every skill re-checked against the Didit backend, the public OpenAPI spec and the docs. Fixes requests that
failed against the real API, documents the endpoints that were missing, and adds seven skills.

### Added
- **didit-event-monitoring (1.0.0):** account and device events (`/v3/events/`, batch, subject timelines, delete),
  device tokens (`POST /v3/events/sdk-token/`) and the device lane (`POST /v1/events/` with `X-Monitoring-Token`),
  and rules on events (`scope.record_types`). Includes `scripts/send_event.py`.
- **didit-fraud-check (1.0.0):** Fraud Check (`/v3/fraud/checks/`, `plan/`, get), profiles, modules, risk
  dimensions and recommendations, plus the IP Risk API. Includes `scripts/run_fraud_check.py`.
- **didit-case-management (1.0.0):** cases (create, assign, transfer, escalate, resolve, 4-eyes approval, notes,
  links, checklist, bulk, statistics), blueprints and presets, report templates and regulatory reports.
  Includes `scripts/manage_cases.py`.
- **didit-fraud-networks (1.0.0):** fraud networks (list, detail, graph, members, signals, timeline, map, report)
  and network lookups for sessions, users, businesses and transactions. Includes `scripts/list_networks.py`.
- **didit-sdk-integration (1.0.0):** redirect, iframe, WebView, Web SDK, iOS, Android, React Native and Flutter
  integration, result handling, `submitTransaction` on every SDK, and device events over HTTP. Includes
  `scripts/mint_sdk_tokens.py`.
- **didit-mcp-server (1.0.0):** connecting AI clients to the hosted Didit MCP server (`https://mcp.didit.me/mcp`),
  sign-in, headless use, file inputs and confirmation rules.
- **didit-document-ai (1.0.0):** Document AI extraction (`POST /v3/document-ai/`) with custom fields, name matching
  and tamper checks. Includes `scripts/extract_document.py`.

### Changed
- **All skills:** the API key is read from `application.api_key` in the verify-email response; the console path is
  **Developers > API keys**; a wrong key returns `403` (only an expired named key returns `401`); `429` and its
  limits are documented; list prices are stated with the 1 November 2026 pricing change; placeholder emails and
  real company names were removed; no em dashes.
- **didit-verification-management (5.0.0 to 5.1.0):** working webhook signature verifier (`X-Signature-V2` signs the
  canonical JSON with no timestamp prefix; `X-Signature-Simple` is deprecated); the real webhook event list;
  destinations use `secret_shared_key` and need `subscribed_events`; questionnaire element types (19, `checkbox` and
  `date` do not exist; repeatable groups and branching are built in the Console); paginated workflow, organization
  and review lists; workflow ordering rules and defaults; session delete, batch delete jobs, update-status rules,
  step and AML hit review, KYB data and parties, resubmission preview, share (`for_application_id` required), PDF
  trailing slash; imports need `workflow_id`; scoped API keys; AML monitoring, biometric templates, KYB shareholders
  and UBO. Scripts: `create_session.py` uses `limit`/`offset` and JSON metadata, `manage_workflows.py` reads
  paginated lists, `setup_account.py` handles re-registration, 2FA and code resend.
- **didit-kyc-onboarding (1.1.0 to 1.2.0):** reads `issuing_state` and `expiration_date`; polling stops on every final
  status (`Expired`, `Kyc Expired`, `Abandoned` included); `mrz` is an object and warnings sit on each feature;
  node ids are read from the decision; `run_kyc.py decision --poll` rejects an `--interval` below 1 second.
- **didit-id-document-verification (1.2.0 to 1.3.0):** 14,000+ document types, PDF input and 10 MB per side,
  `Approved` or `Declined` only, the per-request action options, corrected response keys and warning tables;
  digital ID wallet verifications.
- **didit-liveness-detection (1.2.0 to 1.3.0), didit-face-match (1.4.0 to 1.5.0), didit-face-search (1.2.0 to 1.3.0),
  didit-biometric-age-estimation (1.1.0 to 1.2.0):** decimal thresholds and their exact comparison, `Approved` or
  `Declined` only, the warnings each endpoint really raises, face search `search_type` and match fields, age
  estimation's `age_estimation` response key and threshold inputs. Fixed `search_faces.py` (similarity) and
  `estimate_age.py` (age key, threshold sent to the API).
- **didit-email-verification (1.2.0 to 1.3.0), didit-phone-verification (1.3.0 to 1.4.0):** removed the
  non-existent `undeliverable_email_action`; expired codes return `200` "Expired or Not Found"; phone channels
  (RCS, Viber, Zalo), resend rule and send statuses; email and phone risk endpoints.
- **didit-aml-screening (1.2.0 to 1.3.0):** nationality is ISO alpha-2 only; approve and review thresholds, adverse
  media, ongoing monitoring (off by default) and `Idempotency-Key`; a consistent scoring example; hit review. The
  KYC + AML recipes here and in didit-id-document-verification convert the alpha-3 nationality that ID verification
  returns to alpha-2 before calling `/v3/aml/`.
- **didit-proof-of-address (1.2.0 to 1.3.0):** WebP, per-type document age, `expected_*` inputs, the real response
  shape and warning names; uploads are limited to 50 MB for a PDF and 6 MB for an image (was 15 MB).
- **didit-database-validation (1.2.0 to 1.3.0):** `issuing_state` is ISO **alpha-3** again (the 5.0.0 change to
  alpha-2 made every request fail); per-country default services and required fields from the public catalog;
  per-service results and prices.
- **didit-transaction-monitoring (1.0.0 to 1.1.0):** a reused `transaction_id` is rejected (`400`/`409`);
  `entity_type` is `individual`; `travel_rule_details.status` is required (the script's Travel Rule example failed);
  Travel Rule statuses and settings, 16 wallet-screening chains, the wallet-screening PDF and the Rules API.
  `submit_transaction.py` takes `--counterparty-entity-type` (`individual` or `company`).

### Tests
- New `tests/test_skill_structure.py` (offline, no key): frontmatter and naming, README table and tree, scripts
  compile and are referenced, JSON and Python examples parse, API paths keep their trailing slash, no supplier
  names or em dashes, and the webhook verifier accepts signatures produced by Didit's signing code.
- `tests/test_all_skills.py` now checks each response's status code and JSON fields instead of accepting any
  `400`, covers the new endpoints, runs the case and network checks when `DIDIT_ORG_ID` and `DIDIT_APP_ID` are
  set, and no longer prints part of the API key.

## [5.0.0] - 2026-07-31

Accuracy sync with the audited Didit OpenAPI spec. Corrects API contracts that would
return `400`/`404` against production and expands the hub to the full platform surface.

### Changed (breaking - corrected request contracts)
- **didit-verification-management (4.1.0 → 5.0.0):**
  - **Workflow creation/update** now uses the required ordered `features` array (uppercase feature values) instead of `workflow_type` + flat `is_*_enabled` flags. The create API is a strict whitelist and rejects unknown keys (including `workflow_type`) with `400`. `scripts/manage_workflows.py` rewritten accordingly.
  - **Webhooks**: replaced the removed singular `GET/PATCH /v3/webhook/` config (with `secret_shared_key`/`rotate_secret_key`) with the **webhook destinations** model (`/v3/webhook/destinations/` CRUD; multiple destinations, each with its own URL, version, events, and signing secret).
  - **Lists**: replaced the removed `/v3/blocklist/add|remove` + `GET /v3/blocklist/` with the **Lists API** (`/v3/lists/` and `/v3/lists/{id}/entries/`, including `face-upload`).
  - **Users**: `status` corrected to the monitoring enum `ACTIVE`/`FLAGGED`/`BLOCKED` (was `Approved`/`Declined`/`Pending`); added `POST /v3/users/create/` and `PATCH .../update-status/` and the full update field set.
- **didit-kyc-onboarding (1.0.0 → 1.1.0):** workflow creation switched to the `features` array; "block fraudulent users" switched from `/v3/blocklist/add/` to the Lists API; `scripts/run_kyc.py` updated.
- **didit-database-validation (1.1.0 → 1.2.0):** `issuing_state` (ISO alpha-2) is the required field; removed the fabricated universal `id_number`; documented the real optional fields and country-specific number fields; country table converted alpha-3 → alpha-2. `scripts/validate_database.py` updated.

### Changed (corrections)
- Presigned image/document URL expiry corrected from "60 minutes" to **4 hours** across face-match, face-search, age-estimation, proof-of-address, and the hub.
- PDF generation rate limit corrected to **50/min**; session statuses completed (`Kyc Expired`, `Awaiting User`; removed the non-existent `Pending`).
- AML status `Rejected` → `Declined` (aml-screening).
- Removed an internal library name from a skill (confidentiality).
- Minor version bumps for the corrected standalone skills: face-match → 1.4.0, face-search → 1.2.0, biometric-age-estimation → 1.1.0, proof-of-address → 1.2.0, aml-screening → 1.2.0.

### Added
- **didit-verification-management** now documents **Businesses (KYB)**, **Transactions** (AML monitoring), **Bulk Import** (canonical schema; no provider request field), **Customization** (branding), and reviewer **session data overrides** (`update-data` / `update-poa-data`).

### Tests
- `tests/test_all_skills.py` updated to the corrected contracts (Lists API, webhook destinations CRUD, `features`-array workflow creation, database-validation `issuing_state`).

## [4.2.0] - 2026-07-09

### Added
- **New skill: didit-transaction-monitoring (1.0.0)** - real-time transaction monitoring (KYT), crypto wallet screening, and the FATF / EU TFR Travel Rule: create transactions (`POST /v3/transactions/`), on-demand wallet screening, Travel Rule settings + transfer lifecycle (rails, resend/cancel/finish), wallet address book, wallet-ownership widget, sunrise inbound registration, VASP directory, SDK transaction tokens (`POST /v3/transactions/sdk-token/`), `action_required` handling, and webhooks. Includes `scripts/submit_transaction.py` and live coverage in `tests/test_all_skills.py`.

## [4.1.0] - 2026-02-19

### Changed
- **Renamed all 11 skills** to gerund-based naming convention per Claude 2026 best practices:
  - `didit-identity-verification` → `didit-managing-verification`
  - `didit-id-verification` → `didit-verifying-documents`
  - `didit-passive-liveness` → `didit-detecting-liveness`
  - `didit-face-match` → `didit-comparing-faces`
  - `didit-face-search` → `didit-searching-faces`
  - `didit-age-estimation` → `didit-estimating-age`
  - `didit-email-verification` → `didit-verifying-email`
  - `didit-phone-verification` → `didit-verifying-phone`
  - `didit-aml-screening` → `didit-screening-aml`
  - `didit-proof-of-address` → `didit-verifying-address`
  - `didit-database-validation` → `didit-validating-database`
- All descriptions rewritten as concise, trigger-based, third-person statements.
- README updated with naming convention documentation and three-tier architecture explanation.

## [4.0.0] - 2026-02-19

### Added
- **didit-managing-verification** (v4.0.0) - Consolidated hub skill merging account-setup, sessions, workflows, questionnaires, users, and billing. 40+ endpoints across 8 categories. Includes `scripts/create_session.py` CLI.
- **Getting Started** section added to all 10 standalone skills with account creation and credit top-up instructions.
- New scripts for 5 standalone skills: `search_faces.py`, `estimate_age.py`, `screen_aml.py`, `verify_address.py`, `validate_database.py`.

### Changed
- Reduced from 16 skills to 11 skills (1 hub + 10 standalone) for clearer organization.
- All standalone skills now reference `didit-managing-verification` hub for platform management.
- README updated with new 11-skill table, repo structure, and endpoint coverage.

### Removed
- Separate `didit-account-setup`, `didit-sessions`, `didit-workflows`, `didit-questionnaires`, `didit-users`, `didit-billing` skills (consolidated into `didit-managing-verification`).

## [3.0.0] - 2026-02-19

### Added
- **didit-account-setup** (v1.0.0) - Programmatic account registration, email verification, login, and credential retrieval. 5 Auth API endpoints. Includes `scripts/setup_account.py` CLI.
- **didit-workflows** (v1.0.0) - Full CRUD for verification workflows: list, create, get, update, delete. 5 endpoints. Includes `scripts/manage_workflows.py` CLI.
- **didit-questionnaires** (v1.0.0) - Full CRUD for custom questionnaires with multi-language support and 7 element types. 5 endpoints.
- **didit-billing** (v1.0.0) - Credit balance check and Stripe checkout top-up. 2 endpoints.
- **didit-users** (v1.0.0) - User management: list, get, update, batch-delete verified users. 4 endpoints.
- Test coverage for all new management and auth API endpoints (43 total tests, up from 23).

### Changed
- **didit-sessions** bumped to v3.0.0 - Added 3 new endpoints: batch delete sessions (`POST /v3/sessions/delete/`), list session reviews (`GET /v3/sessions/{id}/reviews/`), create session review (`POST /v3/sessions/{id}/reviews/`). Total: 14 endpoints (was 11). Updated workflow section to reference the new Workflows API (no longer console-only). Added email/phone verification workflow types. Updated base URL to `https://apx.didit.me/v3`.
- README updated with 16 skills (was 11), 47 endpoints (was 23), and "Zero to Verifying" quick-start flow.
- Test suite base URL updated to `https://apx.didit.me`.

## [2.0.0] - 2026-02-14

### Added
- **didit-sessions** (v2.0.0) - Consolidated session & workflow skill covering 11 API endpoints: create, retrieve, list, delete, update-status, generate-pdf, share, import-shared, blocklist-add, blocklist-remove, blocklist-list.
- **didit-age-estimation** (v1.0.0) - Age estimation from facial images with liveness check.
- **didit-aml-screening** (v1.0.0) - Anti-Money Laundering screening with dual-score system.
- **didit-database-validation** (v1.0.0) - Government database validation for 18 countries.
- **didit-face-search** (v1.0.0) - 1:N face search with blocklist integration.
- **didit-proof-of-address** (v1.0.0) - Address document verification with OCR and geocoding.
- **didit-webhooks** (v1.0.0) - Webhook signature verification (V2, Simple, X-Signature).
- Comprehensive test suite (`tests/test_all_skills.py`) covering all 23 API endpoints.
- ClawHub manifests (`claw.json`) for every skill.
- Documentation scraper (`scripts/scrape_docs.py`) for `docs.didit.me`.

### Changed
- **didit-email-verification** bumped to v1.2.0 - Enhanced with full response schemas, rate limit details, retry logic patterns, and expanded error handling.
- **didit-phone-verification** bumped to v1.2.0 - Added SMS/WhatsApp channel details, code expiration timing, carrier-specific notes.
- **didit-id-verification** bumped to v1.2.0 - Added common workflows section, more warning tags, full identity pipeline example.
- **didit-passive-liveness** bumped to v1.2.0 - Added 99.9% accuracy stats, blocklist face warning, configurable thresholds.
- **didit-face-match** bumped to v1.2.0 - Added score interpretation table, NO_FACE_DETECTED warning tag.
- **didit-proof-of-address** - Fixed endpoint to correct `/v3/poa/` (was `/v3/proof-of-address/`), fixed field name to `document` (was `document_image`).
- **didit-sessions** - Fixed list endpoint to `GET /v3/sessions/` (was `/v3/session/`).

### Removed
- Separate `didit-workflows`, `didit-blocklist`, and `didit-reusable-kyc` skills (consolidated into `didit-sessions`).

## [1.0.0] - 2026-02-13

### Added
- Initial release with 6 standalone API skills: id-verification, passive-liveness, face-match, email-verification, phone-verification, workflows.
- Utility scripts for email, phone, face-match, id-verification, and passive-liveness.
