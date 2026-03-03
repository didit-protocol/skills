# Changelog

All notable changes to the Didit Agent Skills collection will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- **didit-managing-verification** (v4.0.0) — Consolidated hub skill merging account-setup, sessions, workflows, questionnaires, users, and billing. 40+ endpoints across 8 categories. Includes `scripts/create_session.py` CLI.
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
- **didit-account-setup** (v1.0.0) — Programmatic account registration, email verification, login, and credential retrieval. 5 Auth API endpoints. Includes `scripts/setup_account.py` CLI.
- **didit-workflows** (v1.0.0) — Full CRUD for verification workflows: list, create, get, update, delete. 5 endpoints. Includes `scripts/manage_workflows.py` CLI.
- **didit-questionnaires** (v1.0.0) — Full CRUD for custom questionnaires with multi-language support and 7 element types. 5 endpoints.
- **didit-billing** (v1.0.0) — Credit balance check and Stripe checkout top-up. 2 endpoints.
- **didit-users** (v1.0.0) — User management: list, get, update, batch-delete verified users. 4 endpoints.
- Test coverage for all new management and auth API endpoints (43 total tests, up from 23).

### Changed
- **didit-sessions** bumped to v3.0.0 — Added 3 new endpoints: batch delete sessions (`POST /v3/sessions/delete/`), list session reviews (`GET /v3/sessions/{id}/reviews/`), create session review (`POST /v3/sessions/{id}/reviews/`). Total: 14 endpoints (was 11). Updated workflow section to reference the new Workflows API (no longer console-only). Added email/phone verification workflow types. Updated base URL to `https://apx.didit.me/v3`.
- README updated with 16 skills (was 11), 47 endpoints (was 23), and "Zero to Verifying" quick-start flow.
- Test suite base URL updated to `https://apx.didit.me`.

## [2.0.0] - 2026-02-14

### Added
- **didit-sessions** (v2.0.0) — Consolidated session & workflow skill covering 11 API endpoints: create, retrieve, list, delete, update-status, generate-pdf, share, import-shared, blocklist-add, blocklist-remove, blocklist-list.
- **didit-age-estimation** (v1.0.0) — Age estimation from facial images with liveness check.
- **didit-aml-screening** (v1.0.0) — Anti-Money Laundering screening with dual-score system.
- **didit-database-validation** (v1.0.0) — Government database validation for 18 countries.
- **didit-face-search** (v1.0.0) — 1:N face search with blocklist integration.
- **didit-proof-of-address** (v1.0.0) — Address document verification with OCR and geocoding.
- **didit-webhooks** (v1.0.0) — Webhook signature verification (V2, Simple, X-Signature).
- Comprehensive test suite (`tests/test_all_skills.py`) covering all 23 API endpoints.
- ClawHub manifests (`claw.json`) for every skill.
- Documentation scraper (`scripts/scrape_docs.py`) for `docs.didit.me`.

### Changed
- **didit-email-verification** bumped to v1.2.0 — Enhanced with full response schemas, rate limit details, retry logic patterns, and expanded error handling.
- **didit-phone-verification** bumped to v1.2.0 — Added SMS/WhatsApp channel details, code expiration timing, carrier-specific notes.
- **didit-id-verification** bumped to v1.2.0 — Added common workflows section, more warning tags, full identity pipeline example.
- **didit-passive-liveness** bumped to v1.2.0 — Added 99.9% accuracy stats, blocklist face warning, configurable thresholds.
- **didit-face-match** bumped to v1.2.0 — Added score interpretation table, NO_FACE_DETECTED warning tag.
- **didit-proof-of-address** — Fixed endpoint to correct `/v3/poa/` (was `/v3/proof-of-address/`), fixed field name to `document` (was `document_image`).
- **didit-sessions** — Fixed list endpoint to `GET /v3/sessions/` (was `/v3/session/`).

### Removed
- Separate `didit-workflows`, `didit-blocklist`, and `didit-reusable-kyc` skills (consolidated into `didit-sessions`).

## [1.0.0] - 2026-02-13

### Added
- Initial release with 6 standalone API skills: id-verification, passive-liveness, face-match, email-verification, phone-verification, workflows.
- Utility scripts for email, phone, face-match, id-verification, and passive-liveness.
