#!/usr/bin/env python3
"""
Live test suite for the Didit Agent Skills: calls the real API with your key and checks
that every documented endpoint answers with the documented status code and JSON fields.

Covers the hub (account setup, sessions, workflows, questionnaires, lists, users, billing,
webhook destinations), the KYC recipe, the standalone verification APIs, transaction
monitoring, event monitoring, fraud checks, Document AI, and (when organization and
application IDs are set) cases and fraud networks.

Usage:
    export DIDIT_API_KEY="your_api_key"           # a sandbox application key is recommended
    export DIDIT_WORKFLOW_ID="your_workflow_id"   # optional, for session tests
    export DIDIT_ORG_ID="your_organization_id"    # optional, enables case and network tests
    export DIDIT_APP_ID="your_application_id"     # optional, enables case and network tests
    python3 tests/test_all_skills.py

The offline checks (format, README, scripts, webhook signatures) are in
tests/test_skill_structure.py and need no key.

NOTE: image-based APIs get a tiny test image, so they answer "Declined" or a documented
      400. That confirms the API is reachable, authenticated and processing requests.
      Some calls are billed on non-sandbox applications.
"""

import base64
import io
import os
import sys
import time

import requests

API_KEY = os.environ.get("DIDIT_API_KEY", "")
WORKFLOW_ID = os.environ.get("DIDIT_WORKFLOW_ID", "")
ORG_ID = os.environ.get("DIDIT_ORG_ID", "")
APP_ID = os.environ.get("DIDIT_APP_ID", "")
BASE_URL = "https://verification.didit.me"
AUTH_BASE_URL = "https://apx.didit.me/auth/v2"

# Tiny 1x1 red PNG for image-based tests
TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
)

HEADERS_JSON = {"x-api-key": API_KEY, "Content-Type": "application/json"}
HEADERS_KEY = {"x-api-key": API_KEY}

MISSING = object()
results = []


def make_image_file(name="test.png"):
    return (name, io.BytesIO(TINY_PNG), "image/png")


def get_path(body, dotted):
    current = body
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return MISSING
        current = current[part]
    return current


def log(skill, endpoint, status, detail, passed, skipped=False):
    icon = "SKIP" if skipped else ("PASS" if passed else "FAIL")
    results.append({"skill": skill, "endpoint": endpoint, "status": status, "detail": detail,
                    "passed": passed, "skipped": skipped})
    print(f"  [{icon}] {endpoint} -> {status} {detail}")


def skip(skill, endpoint, reason):
    log(skill, endpoint, "SKIP", reason, True, skipped=True)


def check(skill, endpoint, response, *outcomes, show=()):
    """Pass when the response matches one of the documented outcomes.

    Each outcome is (status_code, expectations); expectations maps a dotted JSON path to
    None (the key must be present) or to a set of allowed values. A non-JSON body only
    matches an outcome with no expectations. Returns the parsed body.
    """
    try:
        body = response.json()
    except ValueError:
        body = MISSING
    passed = False
    for status_code, expectations in outcomes:
        if response.status_code != status_code:
            continue
        if not expectations:
            passed = True
            break
        if body is MISSING:
            continue
        ok = True
        for path, allowed in expectations.items():
            value = body if path == "$" else get_path(body, path)
            if value is MISSING or (allowed is not None and value not in allowed):
                ok = False
                break
        if ok:
            passed = True
            break
    shown = []
    for path in show:
        value = get_path(body, path) if isinstance(body, dict) else MISSING
        shown.append(f"{path}={'-' if value is MISSING else value}")
    if not passed:
        snippet = response.text[:200].replace("\n", " ")
        shown.append(f"body={snippet}")
    log(skill, endpoint, response.status_code, ", ".join(shown), passed)
    return body if isinstance(body, (dict, list)) else {}


def run(skill, endpoint, fn):
    """Run one request, logging an error instead of stopping the suite."""
    try:
        return fn()
    except Exception as error:  # noqa: BLE001 - a test harness reports every failure
        log(skill, endpoint, "ERR", str(error), False)
        return {}


def org_path(suffix):
    return f"{BASE_URL}/v3/organization/{ORG_ID}/application/{APP_ID}/{suffix}"


# ---------------------------------------------------------------------------
# Standalone verification APIs
# ---------------------------------------------------------------------------

def test_id_verification():
    print("\n1. ID Verification (didit-id-document-verification)")
    endpoint = "POST /v3/id-verification/"
    run("id-verification", endpoint, lambda: check(
        "id-verification", endpoint,
        requests.post(f"{BASE_URL}/v3/id-verification/", headers=HEADERS_KEY,
                      files={"front_image": make_image_file()},
                      data={"vendor_data": "skill-test-suite"}, timeout=60),
        (200, {"request_id": None, "id_verification.status": {"Approved", "Declined"}}),
        (400, {"error": {"COULD_NOT_RECOGNIZE_DOCUMENT"}}),
        show=("id_verification.status", "error"),
    ))

    endpoint = "GET /v3/id-verification/wallets/"
    run("id-verification", endpoint, lambda: check(
        "id-verification", endpoint,
        requests.get(f"{BASE_URL}/v3/id-verification/wallets/", headers=HEADERS_KEY, timeout=30),
        (200, {"wallets": None}),
    ))


def test_passive_liveness():
    print("\n2. Passive Liveness (didit-liveness-detection)")
    endpoint = "POST /v3/passive-liveness/"
    run("passive-liveness", endpoint, lambda: check(
        "passive-liveness", endpoint,
        requests.post(f"{BASE_URL}/v3/passive-liveness/", headers=HEADERS_KEY,
                      files={"user_image": make_image_file()},
                      data={"vendor_data": "skill-test-suite"}, timeout=60),
        (200, {"request_id": None, "liveness.status": {"Approved", "Declined"}}),
        show=("liveness.status", "liveness.score"),
    ))


def test_face_match():
    print("\n3. Face Match (didit-face-match)")
    endpoint = "POST /v3/face-match/"
    run("face-match", endpoint, lambda: check(
        "face-match", endpoint,
        requests.post(f"{BASE_URL}/v3/face-match/", headers=HEADERS_KEY,
                      files={"user_image": make_image_file("user.png"), "ref_image": make_image_file("ref.png")},
                      data={"vendor_data": "skill-test-suite"}, timeout=60),
        (200, {"request_id": None, "face_match.status": {"Approved", "Declined"}}),
        show=("face_match.status", "face_match.score"),
    ))


def test_face_search():
    print("\n4. Face Search (didit-face-search)")
    endpoint = "POST /v3/face-search/"
    run("face-search", endpoint, lambda: check(
        "face-search", endpoint,
        requests.post(f"{BASE_URL}/v3/face-search/", headers=HEADERS_KEY,
                      files={"user_image": make_image_file()},
                      data={"vendor_data": "skill-test-suite"}, timeout=60),
        (200, {"request_id": None, "face_search.status": {"Approved", "Declined"}}),
        (400, {"error": {"No face detected in the image"}}),
        show=("face_search.status", "error"),
    ))


def test_age_estimation():
    print("\n5. Age Estimation (didit-biometric-age-estimation)")
    endpoint = "POST /v3/age-estimation/"
    run("age-estimation", endpoint, lambda: check(
        "age-estimation", endpoint,
        requests.post(f"{BASE_URL}/v3/age-estimation/", headers=HEADERS_KEY,
                      files={"user_image": make_image_file()},
                      data={"vendor_data": "skill-test-suite", "age_estimation_decline_threshold": "18"},
                      timeout=60),
        (200, {"request_id": None, "age_estimation.status": {"Approved", "Declined"}}),
        show=("age_estimation.status", "age_estimation.age_estimation"),
    ))


def test_email_verification():
    print("\n6. Email Verification (didit-email-verification)")
    email = "test-didit-skill@example.com"
    endpoint = "POST /v3/email/send/"
    run("email-verification", endpoint, lambda: check(
        "email-verification", endpoint,
        requests.post(f"{BASE_URL}/v3/email/send/", headers=HEADERS_JSON,
                      json={"email": email, "options": {"code_size": 6}, "vendor_data": "skill-test-suite"},
                      timeout=30),
        (200, {"request_id": None, "status": {"Success", "Retry", "Undeliverable"}}),
        show=("status", "reason"),
    ))

    endpoint = "POST /v3/email/check/ (wrong code)"
    run("email-verification", endpoint, lambda: check(
        "email-verification", endpoint,
        requests.post(f"{BASE_URL}/v3/email/check/", headers=HEADERS_JSON,
                      json={"email": email, "code": "000000"}, timeout=30),
        (200, {"request_id": None, "status": {"Approved", "Failed", "Declined", "Expired or Not Found"}}),
        show=("status",),
    ))

    endpoint = "POST /v3/email/risk/"
    run("email-verification", endpoint, lambda: check(
        "email-verification", endpoint,
        requests.post(f"{BASE_URL}/v3/email/risk/", headers=HEADERS_JSON,
                      json={"email": email, "vendor_data": "skill-test-suite"}, timeout=30),
        (200, {"request_id": None, "status": {"Approved", "In Review", "Declined"}, "email": None}),
        show=("status",),
    ))


def test_phone_verification():
    print("\n7. Phone Verification (didit-phone-verification)")
    phone = "+15550000000"
    endpoint = "POST /v3/phone/send/"
    run("phone-verification", endpoint, lambda: check(
        "phone-verification", endpoint,
        requests.post(f"{BASE_URL}/v3/phone/send/", headers=HEADERS_JSON,
                      json={"phone_number": phone, "options": {"preferred_channel": "sms", "code_size": 6}},
                      timeout=30),
        (200, {"request_id": None, "status": {"Success", "Retry", "Blocked"}}),
        (400, {"detail": None}),
        show=("status", "reason", "detail"),
    ))

    endpoint = "POST /v3/phone/check/ (wrong code)"
    run("phone-verification", endpoint, lambda: check(
        "phone-verification", endpoint,
        requests.post(f"{BASE_URL}/v3/phone/check/", headers=HEADERS_JSON,
                      json={"phone_number": phone, "code": "000000"}, timeout=30),
        (200, {"request_id": None, "status": {"Approved", "Failed", "Declined", "Expired or Not Found"}}),
        (400, {"detail": None}),
        show=("status", "detail"),
    ))

    endpoint = "POST /v3/phone/risk/"
    run("phone-verification", endpoint, lambda: check(
        "phone-verification", endpoint,
        requests.post(f"{BASE_URL}/v3/phone/risk/", headers=HEADERS_JSON,
                      json={"phone_number": "+14155550100", "vendor_data": "skill-test-suite"}, timeout=30),
        (200, {"request_id": None, "status": {"Approved", "In Review", "Declined"}, "phone": None}),
        (400, {"phone_number": None}),
        show=("status",),
    ))


def test_aml_screening():
    print("\n8. AML Screening (didit-aml-screening)")
    endpoint = "POST /v3/aml/"
    run("aml-screening", endpoint, lambda: check(
        "aml-screening", endpoint,
        requests.post(f"{BASE_URL}/v3/aml/", headers=HEADERS_JSON,
                      json={"full_name": "John Test Smith", "date_of_birth": "1990-01-01",
                            "nationality": "US", "vendor_data": "skill-test-suite"}, timeout=60),
        (200, {"request_id": None, "aml.status": {"Approved", "In Review", "Declined"}, "aml.hits": None}),
        show=("aml.status", "aml.total_hits", "aml.score"),
    ))

    endpoint = "POST /v3/aml/ (alpha-3 nationality is rejected)"
    run("aml-screening", endpoint, lambda: check(
        "aml-screening", endpoint,
        requests.post(f"{BASE_URL}/v3/aml/", headers=HEADERS_JSON,
                      json={"full_name": "John Test Smith", "nationality": "USA"}, timeout=30),
        (400, {"nationality": None}),
    ))


def test_proof_of_address():
    print("\n9. Proof of Address (didit-proof-of-address)")
    endpoint = "POST /v3/poa/"
    run("proof-of-address", endpoint, lambda: check(
        "proof-of-address", endpoint,
        requests.post(f"{BASE_URL}/v3/poa/", headers=HEADERS_KEY,
                      files={"document": make_image_file("doc.png")},
                      data={"vendor_data": "skill-test-suite"}, timeout=60),
        (200, {"request_id": None, "poa.status": {"Approved", "Declined"}}),
        (400, {"error": None}),
        show=("poa.status", "poa.document_type", "error"),
    ))


def test_database_validation():
    print("\n10. Database Validation (didit-database-validation)")
    endpoint = "POST /v3/database-validation/ (alpha-2 issuing_state is rejected)"
    run("database-validation", endpoint, lambda: check(
        "database-validation", endpoint,
        requests.post(f"{BASE_URL}/v3/database-validation/", headers=HEADERS_JSON,
                      json={"issuing_state": "PE", "personal_number": "12345678",
                            "first_name": "Test", "last_name": "User"}, timeout=30),
        (400, {"error": None}),
    ))

    endpoint = "POST /v3/database-validation/ (PER)"
    run("database-validation", endpoint, lambda: check(
        "database-validation", endpoint,
        requests.post(f"{BASE_URL}/v3/database-validation/", headers=HEADERS_JSON,
                      json={"issuing_state": "PER", "personal_number": "12345678", "first_name": "Test",
                            "last_name": "User", "vendor_data": "skill-test-suite"}, timeout=60),
        (200, {"request_id": None, "database_validation.status": None}),
        (502, {}),
        show=("database_validation.status", "database_validation.match_type"),
    ))


def test_document_ai():
    print("\n11. Document AI (didit-document-ai)")
    endpoint = "POST /v3/document-ai/"
    run("document-ai", endpoint, lambda: check(
        "document-ai", endpoint,
        requests.post(f"{BASE_URL}/v3/document-ai/", headers=HEADERS_KEY,
                      files={"document": make_image_file("doc.png")},
                      data={"vendor_data": "skill-test-suite"}, timeout=90),
        (200, {"request_id": None, "document_ai.status": None}),
        (400, {"error": None}),
        show=("document_ai.status", "error"),
    ))


def test_fraud_check():
    print("\n12. Fraud Check and IP risk (didit-fraud-check)")
    endpoint = "POST /v3/fraud/checks/plan/"
    run("fraud-check", endpoint, lambda: check(
        "fraud-check", endpoint,
        requests.post(f"{BASE_URL}/v3/fraud/checks/plan/", headers=HEADERS_JSON,
                      json={"subject": {"identifiers": [{"type": "email", "value": "user@example.com"}]}},
                      timeout=30),
        (200, {"modules": None, "estimated_price": None, "currency": None, "can_afford": None}),
        show=("profile_id", "estimated_price", "can_afford"),
    ))

    endpoint = "POST /v3/ip/risk/"
    run("fraud-check", endpoint, lambda: check(
        "fraud-check", endpoint,
        requests.post(f"{BASE_URL}/v3/ip/risk/", headers=HEADERS_JSON,
                      json={"ip_address": "203.0.113.10", "vendor_data": "skill-test-suite"}, timeout=30),
        (200, {"request_id": None, "status": {"Approved", "In Review"}, "ip": None}),
        show=("status",),
    ))


# ---------------------------------------------------------------------------
# Sessions, lists, reviews (didit-verification-management)
# ---------------------------------------------------------------------------

def resolve_workflow_id():
    if WORKFLOW_ID:
        return WORKFLOW_ID
    try:
        r = requests.get(f"{BASE_URL}/v3/workflows/", headers=HEADERS_KEY, timeout=30)
        rows = r.json().get("results", []) if r.status_code == 200 else []
        if rows:
            chosen = next((w for w in rows if w.get("is_default")), rows[0])
            print(f"  (using workflow {chosen['uuid']})")
            return chosen["uuid"]
    except Exception:  # noqa: BLE001
        pass
    return ""


def test_sessions():
    print("\n13. Sessions")
    wf_id = resolve_workflow_id()
    if not wf_id:
        skip("sessions", "POST /v3/session/", "no workflow found (set DIDIT_WORKFLOW_ID)")
        return

    endpoint = "POST /v3/session/ (create)"
    body = run("sessions", endpoint, lambda: check(
        "sessions", endpoint,
        requests.post(f"{BASE_URL}/v3/session/", headers=HEADERS_JSON,
                      json={"workflow_id": wf_id, "vendor_data": "test-skill-suite",
                            "metadata": {"source": "skill-test-suite"}}, timeout=30),
        (201, {"session_id": None, "session_token": None, "url": None, "status": None}),
        show=("status",),
    ))
    session_id = body.get("session_id")

    endpoint = "GET /v3/sessions/ (list)"
    run("sessions", endpoint, lambda: check(
        "sessions", endpoint,
        requests.get(f"{BASE_URL}/v3/sessions/", headers=HEADERS_KEY,
                     params={"vendor_data": "test-skill-suite", "limit": 5}, timeout=30),
        (200, {"results": None}),
        show=("count",),
    ))

    if not session_id:
        return

    endpoint = "GET /v3/session/{id}/decision/"
    run("sessions", endpoint, lambda: check(
        "sessions", endpoint,
        requests.get(f"{BASE_URL}/v3/session/{session_id}/decision/", headers=HEADERS_KEY, timeout=30),
        (200, {"session_id": None, "status": None}),
        show=("status",),
    ))

    endpoint = "GET /v3/session/{id}/generate-pdf/ (not finished yet)"
    run("sessions", endpoint, lambda: check(
        "sessions", endpoint,
        requests.get(f"{BASE_URL}/v3/session/{session_id}/generate-pdf/", headers=HEADERS_KEY, timeout=30),
        (403, {}),
    ))

    endpoint = "GET /v3/sessions/{id}/reviews/"
    run("sessions", endpoint, lambda: check(
        "sessions", endpoint,
        requests.get(f"{BASE_URL}/v3/sessions/{session_id}/reviews/", headers=HEADERS_KEY, timeout=30),
        (200, {"results": None}),
        show=("count",),
    ))

    endpoint = "POST /v3/sessions/{id}/reviews/ (note only)"
    run("sessions", endpoint, lambda: check(
        "sessions", endpoint,
        requests.post(f"{BASE_URL}/v3/sessions/{session_id}/reviews/", headers=HEADERS_JSON,
                      json={"comment": "Skill test suite note"}, timeout=30),
        (201, {"comment": None}),
    ))

    endpoint = "PATCH /v3/session/{id}/update-status/ (Not Started cannot be updated)"
    run("sessions", endpoint, lambda: check(
        "sessions", endpoint,
        requests.patch(f"{BASE_URL}/v3/session/{session_id}/update-status/", headers=HEADERS_JSON,
                       json={"new_status": "Declined", "comment": "Test suite cleanup"}, timeout=30),
        (400, {"detail": None}),
    ))

    skip("sessions", "DELETE /v3/session/{id}/delete/", "kept so the session stays visible in the console")

    endpoint = "POST /v3/sessions/delete/ (unknown session number)"
    run("sessions", endpoint, lambda: check(
        "sessions", endpoint,
        requests.post(f"{BASE_URL}/v3/sessions/delete/", headers=HEADERS_JSON,
                      json={"session_numbers": ["999999999"]}, timeout=30),
        (200, {"results": None}),
        (400, {}),
        (404, {}),
    ))


def test_lists():
    print("\n14. Lists (block/allow/custom)")
    endpoint = "GET /v3/lists/"
    run("lists", endpoint, lambda: check(
        "lists", endpoint,
        requests.get(f"{BASE_URL}/v3/lists/", headers=HEADERS_KEY, params={"list_type": "blocklist"}, timeout=30),
        (200, {"results": None}),
        show=("count",),
    ))

    endpoint = "POST /v3/lists/{uuid}/entries/ (unknown list)"
    run("lists", endpoint, lambda: check(
        "lists", endpoint,
        requests.post(f"{BASE_URL}/v3/lists/00000000-0000-0000-0000-000000000000/entries/", headers=HEADERS_JSON,
                      json={"reference_session_id": "00000000-0000-0000-0000-000000000000"}, timeout=30),
        (404, {}),
    ))


# ---------------------------------------------------------------------------
# Account setup, workflows, questionnaires, billing, users
# ---------------------------------------------------------------------------

def test_auth_api():
    print("\n15. Auth API (account setup)")
    endpoint = "POST /programmatic/login/ (wrong credentials)"
    run("account-setup", endpoint, lambda: check(
        "account-setup", endpoint,
        requests.post(f"{AUTH_BASE_URL}/programmatic/login/",
                      json={"email": "nonexistent-test@example.com", "password": "FakeP@ss123"}, timeout=30),
        (401, {"detail": None}),
        (429, {"detail": None}),
    ))

    endpoint = "GET /organizations/me/ (invalid token)"
    run("account-setup", endpoint, lambda: check(
        "account-setup", endpoint,
        requests.get(f"{AUTH_BASE_URL}/organizations/me/",
                     headers={"Authorization": "Bearer invalid_token_for_testing"}, timeout=30),
        (401, {}),
        (403, {}),
    ))

    endpoint = "POST /programmatic/register/ (invalid email)"
    run("account-setup", endpoint, lambda: check(
        "account-setup", endpoint,
        requests.post(f"{AUTH_BASE_URL}/programmatic/register/",
                      json={"email": "not-an-email", "password": "FakeP@ss123"}, timeout=30),
        (400, {"email": None}),
    ))


def test_workflows():
    print("\n16. Workflows")
    endpoint = "GET /v3/workflows/ (paginated)"
    run("workflows", endpoint, lambda: check(
        "workflows", endpoint,
        requests.get(f"{BASE_URL}/v3/workflows/", headers=HEADERS_KEY, timeout=30),
        (200, {"count": None, "results": None}),
        show=("count",),
    ))

    endpoint = "POST /v3/workflows/ (create)"
    body = run("workflows", endpoint, lambda: check(
        "workflows", endpoint,
        requests.post(f"{BASE_URL}/v3/workflows/", headers=HEADERS_JSON,
                      json={"workflow_label": "Skill Test Suite", "features": [
                          {"feature": "OCR"},
                          {"feature": "LIVENESS", "config": {"face_liveness_method": "PASSIVE"}},
                      ]}, timeout=30),
        (201, {"uuid": None, "features": None}),
        show=("features", "total_price"),
    ))
    created = body.get("uuid")
    if not created:
        return

    endpoint = "GET /v3/workflows/{id}/"
    run("workflows", endpoint, lambda: check(
        "workflows", endpoint,
        requests.get(f"{BASE_URL}/v3/workflows/{created}/", headers=HEADERS_KEY, timeout=30),
        (200, {"uuid": None, "workflow_label": None}),
    ))

    endpoint = "PATCH /v3/workflows/{id}/"
    run("workflows", endpoint, lambda: check(
        "workflows", endpoint,
        requests.patch(f"{BASE_URL}/v3/workflows/{created}/", headers=HEADERS_JSON,
                       json={"workflow_label": "Skill Test Suite (updated)"}, timeout=30),
        (200, {"uuid": None}),
    ))

    endpoint = "DELETE /v3/workflows/{id}/"
    run("workflows", endpoint, lambda: check(
        "workflows", endpoint,
        requests.delete(f"{BASE_URL}/v3/workflows/{created}/", headers=HEADERS_KEY, timeout=30),
        (204, {}),
        (200, {}),
    ))


def test_questionnaires():
    print("\n17. Questionnaires")
    endpoint = "POST /v3/questionnaires/ (create)"
    body = run("questionnaires", endpoint, lambda: check(
        "questionnaires", endpoint,
        requests.post(f"{BASE_URL}/v3/questionnaires/", headers=HEADERS_JSON, json={
            "title": "Skill Test Suite Questionnaire",
            "default_language": "en",
            "languages": ["en"],
            "form_elements": [
                {"id": "occupation", "element_type": "short_text",
                 "label": {"en": "What is your occupation?"}, "is_required": True},
                {"id": "source_of_funds", "element_type": "single_choice",
                 "label": {"en": "Source of funds"}, "is_required": True,
                 "options": [{"value": "employment", "label": {"en": "Employment"}},
                             {"value": "other", "label": {"en": "Other"}}]},
            ],
        }, timeout=30),
        (201, {"uuid": None}),
    ))
    created = body.get("uuid")

    endpoint = "POST /v3/questionnaires/ (checkbox is not an element type)"
    run("questionnaires", endpoint, lambda: check(
        "questionnaires", endpoint,
        requests.post(f"{BASE_URL}/v3/questionnaires/", headers=HEADERS_JSON, json={
            "title": "Invalid", "default_language": "en", "languages": ["en"],
            "form_elements": [{"id": "x", "element_type": "checkbox", "label": {"en": "X"}}],
        }, timeout=30),
        (400, {}),
    ))

    endpoint = "GET /v3/questionnaires/"
    run("questionnaires", endpoint, lambda: check(
        "questionnaires", endpoint,
        requests.get(f"{BASE_URL}/v3/questionnaires/", headers=HEADERS_KEY, timeout=30),
        (200, {}),
    ))

    if not created:
        return

    endpoint = "GET /v3/questionnaires/{id}/"
    run("questionnaires", endpoint, lambda: check(
        "questionnaires", endpoint,
        requests.get(f"{BASE_URL}/v3/questionnaires/{created}/", headers=HEADERS_KEY, timeout=30),
        (200, {"uuid": None, "title": None}),
    ))

    endpoint = "PATCH /v3/questionnaires/{id}/"
    run("questionnaires", endpoint, lambda: check(
        "questionnaires", endpoint,
        requests.patch(f"{BASE_URL}/v3/questionnaires/{created}/", headers=HEADERS_JSON,
                       json={"title": "Skill Test Suite Questionnaire (updated)"}, timeout=30),
        (200, {"uuid": None}),
    ))

    endpoint = "DELETE /v3/questionnaires/{id}/"
    run("questionnaires", endpoint, lambda: check(
        "questionnaires", endpoint,
        requests.delete(f"{BASE_URL}/v3/questionnaires/{created}/", headers=HEADERS_KEY, timeout=30),
        (204, {}),
        (200, {}),
    ))


def test_billing():
    print("\n18. Billing")
    endpoint = "GET /v3/billing/balance/"
    run("billing", endpoint, lambda: check(
        "billing", endpoint,
        requests.get(f"{BASE_URL}/v3/billing/balance/", headers=HEADERS_KEY, timeout=30),
        (200, {"balance": None, "auto_refill_enabled": None}),
        show=("balance",),
    ))
    skip("billing", "POST /v3/billing/top-up/", "not called, to avoid creating a real checkout")


def test_users():
    print("\n19. Users (KYC)")
    endpoint = "GET /v3/users/"
    run("users", endpoint, lambda: check(
        "users", endpoint,
        requests.get(f"{BASE_URL}/v3/users/", headers=HEADERS_KEY, params={"limit": 5}, timeout=30),
        (200, {"results": None}),
        show=("count",),
    ))

    endpoint = "GET /v3/users/{vendor_data}/ (unknown)"
    run("users", endpoint, lambda: check(
        "users", endpoint,
        requests.get(f"{BASE_URL}/v3/users/nonexistent-test-vendor-data/", headers=HEADERS_KEY, timeout=30),
        (404, {}),
    ))

    endpoint = "GET /v3/biometric-templates/count/"
    run("users", endpoint, lambda: check(
        "users", endpoint,
        requests.get(f"{BASE_URL}/v3/biometric-templates/count/", headers=HEADERS_KEY, timeout=30),
        (200, {}),
    ))


# ---------------------------------------------------------------------------
# Webhook destinations
# ---------------------------------------------------------------------------

def test_webhook_destinations():
    print("\n20. Webhook Destinations")
    endpoint = "POST /v3/webhook/destinations/ (create)"
    body = run("webhook-destinations", endpoint, lambda: check(
        "webhook-destinations", endpoint,
        requests.post(f"{BASE_URL}/v3/webhook/destinations/", headers=HEADERS_JSON, json={
            "label": "Skill Test Suite",
            "url": f"https://example.com/didit-skill-test-{int(time.time())}",
            "webhook_version": "v3",
            "subscribed_events": ["status.updated", "data.updated"],
        }, timeout=30),
        (201, {"uuid": None, "secret_shared_key": None}),
    ))
    created = body.get("uuid")

    endpoint = "GET /v3/webhook/destinations/"
    run("webhook-destinations", endpoint, lambda: check(
        "webhook-destinations", endpoint,
        requests.get(f"{BASE_URL}/v3/webhook/destinations/", headers=HEADERS_KEY, timeout=30),
        (200, {}),
    ))

    if created:
        endpoint = "DELETE /v3/webhook/destinations/{uuid}/"
        run("webhook-destinations", endpoint, lambda: check(
            "webhook-destinations", endpoint,
            requests.delete(f"{BASE_URL}/v3/webhook/destinations/{created}/", headers=HEADERS_KEY, timeout=30),
            (204, {}),
            (200, {}),
        ))


# ---------------------------------------------------------------------------
# Transaction monitoring, Travel Rule, rules (didit-transaction-monitoring)
# ---------------------------------------------------------------------------

def test_transaction_monitoring():
    print("\n21. Transaction Monitoring and Travel Rule")
    txn_id = f"skill-test-{int(time.time())}"
    payload = {
        "transaction_id": txn_id,
        "transaction_category": "finance",
        "transaction_details": {"direction": "outbound", "amount": "10.00", "currency": "EUR"},
        "subject": {"entity_type": "individual", "vendor_data": "skill-test-suite", "full_name": "John Test Smith"},
        "counterparty": {"entity_type": "company", "full_name": "Skill Test Counterparty"},
    }
    endpoint = "POST /v3/transactions/"
    body = run("transaction-monitoring", endpoint, lambda: check(
        "transaction-monitoring", endpoint,
        requests.post(f"{BASE_URL}/v3/transactions/", headers=HEADERS_JSON, json=payload, timeout=60),
        (201, {"uuid": None, "status": {"APPROVED", "IN_REVIEW", "DECLINED", "AWAITING_USER"}}),
        show=("status", "score"),
    ))
    txn_uuid = body.get("uuid")

    endpoint = "POST /v3/transactions/ (same transaction_id is rejected)"
    run("transaction-monitoring", endpoint, lambda: check(
        "transaction-monitoring", endpoint,
        requests.post(f"{BASE_URL}/v3/transactions/", headers=HEADERS_JSON, json=payload, timeout=60),
        (400, {"transaction_id": None}),
        (409, {}),
    ))

    if txn_uuid:
        endpoint = "GET /v3/transactions/{uuid}/"
        run("transaction-monitoring", endpoint, lambda: check(
            "transaction-monitoring", endpoint,
            requests.get(f"{BASE_URL}/v3/transactions/{txn_uuid}/", headers=HEADERS_KEY, timeout=30),
            (200, {"uuid": None, "status": None}),
            show=("status",),
        ))

    endpoint = "GET /v3/transactions/"
    run("transaction-monitoring", endpoint, lambda: check(
        "transaction-monitoring", endpoint,
        requests.get(f"{BASE_URL}/v3/transactions/", headers=HEADERS_KEY, params={"limit": 5}, timeout=30),
        (200, {"results": None}),
    ))

    endpoint = "POST /v3/transactions/sdk-token/"
    run("transaction-monitoring", endpoint, lambda: check(
        "transaction-monitoring", endpoint,
        requests.post(f"{BASE_URL}/v3/transactions/sdk-token/", headers=HEADERS_JSON,
                      json={"vendor_data": "skill-test-suite", "ttl_seconds": 300, "max_uses": 1}, timeout=30),
        (201, {"sdk_token": None, "expires_at": None}),
        show=("expires_at",),
    ))

    endpoint = "GET /v3/transactions/rules/library/"
    run("transaction-monitoring", endpoint, lambda: check(
        "transaction-monitoring", endpoint,
        requests.get(f"{BASE_URL}/v3/transactions/rules/library/", headers=HEADERS_KEY, timeout=30),
        (200, {}),
    ))

    endpoint = "GET /v3/transactions/rules/"
    run("transaction-monitoring", endpoint, lambda: check(
        "transaction-monitoring", endpoint,
        requests.get(f"{BASE_URL}/v3/transactions/rules/", headers=HEADERS_KEY, timeout=30),
        (200, {}),
    ))

    endpoint = "GET /v3/travel-rule/settings/"
    run("transaction-monitoring", endpoint, lambda: check(
        "transaction-monitoring", endpoint,
        requests.get(f"{BASE_URL}/v3/travel-rule/settings/", headers=HEADERS_KEY, timeout=30),
        (200, {"is_enabled": None}),
        show=("is_enabled",),
    ))

    endpoint = "GET /v3/travel-rule/vasps/"
    run("transaction-monitoring", endpoint, lambda: check(
        "transaction-monitoring", endpoint,
        requests.get(f"{BASE_URL}/v3/travel-rule/vasps/", headers=HEADERS_KEY,
                     params={"search": "test", "limit": 5}, timeout=30),
        (200, {"results": None}),
    ))

    endpoint = "POST /v1/transactions/ (no token)"
    run("transaction-monitoring", endpoint, lambda: check(
        "transaction-monitoring", endpoint,
        requests.post(f"{BASE_URL}/v1/transactions/", json={}, timeout=30),
        (401, {"detail": None}),
    ))


# ---------------------------------------------------------------------------
# Event monitoring (didit-event-monitoring)
# ---------------------------------------------------------------------------

def test_event_monitoring():
    print("\n22. Event Monitoring")
    disabled = (403, {"code": {"event_monitoring_disabled"}})
    event = {
        "event_id": f"skill-test-{int(time.time())}",
        "event_category": "auth",
        "action_type": "login",
        "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "subject": {"vendor_data": "skill-test-suite"},
    }
    endpoint = "POST /v3/events/"
    run("event-monitoring", endpoint, lambda: check(
        "event-monitoring", endpoint,
        requests.post(f"{BASE_URL}/v3/events/", headers=HEADERS_JSON, json=event, timeout=30),
        (201, {"event_uuid": None, "event_id": {event["event_id"]}, "status": None}),
        disabled,
        show=("status", "code"),
    ))

    endpoint = "GET /v3/events/"
    run("event-monitoring", endpoint, lambda: check(
        "event-monitoring", endpoint,
        requests.get(f"{BASE_URL}/v3/events/", headers=HEADERS_KEY, params={"limit": 5}, timeout=30),
        (200, {"results": None}),
    ))

    endpoint = "POST /v3/events/sdk-token/"
    token = run("event-monitoring", endpoint, lambda: check(
        "event-monitoring", endpoint,
        requests.post(f"{BASE_URL}/v3/events/sdk-token/", headers=HEADERS_JSON,
                      json={"vendor_data": "skill-test-suite", "ttl_seconds": 300, "max_uses": 2}, timeout=30),
        (201, {"monitoring_token": None, "expires_at": None}),
        disabled,
        show=("expires_at", "code"),
    )).get("monitoring_token")

    endpoint = "POST /v1/events/ (no token)"
    run("event-monitoring", endpoint, lambda: check(
        "event-monitoring", endpoint,
        requests.post(f"{BASE_URL}/v1/events/", json={}, timeout=30),
        (401, {"detail": None}),
    ))

    if token:
        device_event = {key: value for key, value in event.items() if key != "subject"}
        device_event["event_id"] = f"{event['event_id']}-device"
        endpoint = "POST /v1/events/ (X-Monitoring-Token)"
        run("event-monitoring", endpoint, lambda: check(
            "event-monitoring", endpoint,
            requests.post(f"{BASE_URL}/v1/events/", headers={"X-Monitoring-Token": token},
                          json=device_event, timeout=30),
            (201, {"event_uuid": None, "status": None}),
            show=("status",),
        ))


# ---------------------------------------------------------------------------
# Cases and fraud networks (need organization and application IDs)
# ---------------------------------------------------------------------------

def test_cases_and_networks():
    print("\n23. Cases and Fraud Networks")
    if not (ORG_ID and APP_ID):
        for name in ("GET .../cases/", "GET .../cases/statistics/", "GET .../cases/blueprints/presets/",
                     "GET .../networks/"):
            skip("cases-networks", name, "set DIDIT_ORG_ID and DIDIT_APP_ID to run")
        return

    endpoint = "GET .../cases/"
    run("case-management", endpoint, lambda: check(
        "case-management", endpoint,
        requests.get(org_path("cases/"), headers=HEADERS_KEY, params={"limit": 5}, timeout=30),
        (200, {"results": None}),
        show=("count",),
    ))

    endpoint = "GET .../cases/statistics/"
    run("case-management", endpoint, lambda: check(
        "case-management", endpoint,
        requests.get(org_path("cases/statistics/"), headers=HEADERS_KEY, timeout=30),
        (200, {}),
    ))

    endpoint = "GET .../cases/blueprints/presets/"
    run("case-management", endpoint, lambda: check(
        "case-management", endpoint,
        requests.get(org_path("cases/blueprints/presets/"), headers=HEADERS_KEY, timeout=30),
        (200, {}),
    ))

    endpoint = "GET .../networks/"
    run("fraud-networks", endpoint, lambda: check(
        "fraud-networks", endpoint,
        requests.get(org_path("networks/"), headers=HEADERS_KEY, params={"limit": 5}, timeout=30),
        (200, {"count": None, "results": None}),
        show=("count",),
    ))


# ---------------------------------------------------------------------------
# KYC end-to-end flow (didit-kyc-onboarding)
# ---------------------------------------------------------------------------

def test_kyc_flow():
    print("\n24. KYC Flow (didit-kyc-onboarding)")
    endpoint = "POST /v3/workflows/ (KYC workflow)"
    body = run("kyc-flow", endpoint, lambda: check(
        "kyc-flow", endpoint,
        requests.post(f"{BASE_URL}/v3/workflows/", headers=HEADERS_JSON, json={
            "workflow_label": "KYC Skill Test Suite",
            "features": [
                {"feature": "OCR"},
                {"feature": "LIVENESS", "config": {"face_liveness_method": "PASSIVE"}},
                {"feature": "FACE_MATCH", "config": {"face_match_score_decline_threshold": 50}},
            ],
            "max_retry_attempts": 3,
        }, timeout=30),
        (201, {"uuid": None, "features": None}),
        show=("features", "total_price"),
    ))
    workflow_id = body.get("uuid")
    if not workflow_id:
        return

    endpoint = "POST /v3/session/ (KYC session)"
    session = run("kyc-flow", endpoint, lambda: check(
        "kyc-flow", endpoint,
        requests.post(f"{BASE_URL}/v3/session/", headers=HEADERS_JSON,
                      json={"workflow_id": workflow_id, "vendor_data": "kyc-test-suite-user"}, timeout=30),
        (201, {"session_id": None, "url": None, "status": {"Not Started"}}),
        show=("status",),
    ))
    session_id = session.get("session_id")

    if session_id:
        endpoint = "GET /v3/session/{id}/decision/ (KYC)"
        run("kyc-flow", endpoint, lambda: check(
            "kyc-flow", endpoint,
            requests.get(f"{BASE_URL}/v3/session/{session_id}/decision/", headers=HEADERS_KEY, timeout=30),
            (200, {"session_id": None, "status": None}),
            show=("status",),
        ))

    endpoint = "DELETE /v3/workflows/{id}/ (KYC cleanup)"
    run("kyc-flow", endpoint, lambda: check(
        "kyc-flow", endpoint,
        requests.delete(f"{BASE_URL}/v3/workflows/{workflow_id}/", headers=HEADERS_KEY, timeout=30),
        (204, {}),
        (200, {}),
    ))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not API_KEY:
        print("ERROR: DIDIT_API_KEY environment variable not set")
        print("Usage: export DIDIT_API_KEY='your_key' && python3 tests/test_all_skills.py")
        print("Offline checks need no key: python3 tests/test_skill_structure.py")
        return 1

    print("=" * 70)
    print("Didit Skills: live API test suite")
    print(f"Base URL: {BASE_URL}")
    print(f"Auth URL: {AUTH_BASE_URL}")
    print(f"Cases and networks: {'on' if ORG_ID and APP_ID else 'skipped (no DIDIT_ORG_ID / DIDIT_APP_ID)'}")
    print("=" * 70)

    test_id_verification()
    test_passive_liveness()
    test_face_match()
    test_face_search()
    test_age_estimation()
    test_email_verification()
    test_phone_verification()
    test_aml_screening()
    test_proof_of_address()
    test_database_validation()
    test_document_ai()
    test_fraud_check()
    test_sessions()
    test_lists()
    test_auth_api()
    test_workflows()
    test_questionnaires()
    test_billing()
    test_users()
    test_webhook_destinations()
    test_transaction_monitoring()
    test_event_monitoring()
    test_cases_and_networks()
    test_kyc_flow()

    print("\n" + "=" * 70)
    skipped = sum(1 for r in results if r["skipped"])
    passed = sum(1 for r in results if r["passed"] and not r["skipped"])
    failed = sum(1 for r in results if not r["passed"])
    print(f"RESULTS: {passed} passed, {failed} failed, {skipped} skipped")
    print("=" * 70)

    if failed:
        print("\nFailed tests:")
        for r in results:
            if not r["passed"]:
                print(f"  x [{r['skill']}] {r['endpoint']} -> {r['status']} {r['detail']}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
